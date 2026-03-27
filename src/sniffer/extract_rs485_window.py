#!/usr/bin/env python3
"""Extract register changes from a time window in rs485_modbus_monitor JSONL logs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Neplatny timestamp: {value}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vyrez casoveho okna z JSONL logu a zobrazeni zmen registru."
    )
    parser.add_argument(
        "log_file",
        nargs="?",
        default="logs/rs485_frames.jsonl",
        help="Cesta k JSONL logu z rs485_modbus_monitor.py.",
    )
    parser.add_argument(
        "--from-ts",
        required=True,
        type=parse_timestamp,
        help="Zacatek okna v ISO formatu, napr. 2026-03-26T09:15:00+00:00.",
    )
    parser.add_argument(
        "--to-ts",
        required=True,
        type=parse_timestamp,
        help="Konec okna v ISO formatu, napr. 2026-03-26T09:18:00+00:00.",
    )
    parser.add_argument(
        "--slave",
        action="append",
        type=int,
        default=[],
        help="Filtr na slave_id. Lze zadat vicekrat.",
    )
    parser.add_argument(
        "--request-start",
        action="append",
        type=int,
        default=[],
        help="Filtr na correlated_request.start_address. Lze zadat vicekrat.",
    )
    parser.add_argument(
        "--address",
        action="append",
        type=int,
        default=[],
        help="Filtr na konkretni adresy registru. Lze zadat vicekrat.",
    )
    parser.add_argument(
        "--function-code",
        action="append",
        type=int,
        default=[],
        help="Filtr na konkretni Modbus function code. Lze zadat vicekrat.",
    )
    parser.add_argument(
        "--include-requests",
        action="store_true",
        help="Zahrne do vystupu i requesty a write ramce, ne jen response.",
    )
    parser.add_argument(
        "--include-unchanged",
        action="store_true",
        help="Vystupi i opakovane vzorky beze zmeny.",
    )
    return parser.parse_args()


def build_register_map(record: Dict[str, Any]) -> Dict[int, int]:
    result: Dict[int, int] = {}
    register_map = record.get("register_map")
    if not isinstance(register_map, list):
        return result

    for item in register_map:
        if not isinstance(item, dict):
            continue
        address = item.get("address")
        value = item.get("value")
        if isinstance(address, int) and isinstance(value, int):
            result[address] = value
    return result


def address_matches_request(
    decoded: Dict[str, Any],
    address_filter: set[int],
) -> bool:
    if not address_filter:
        return True

    start_address = decoded.get("start_address")
    register_count = decoded.get("register_count")
    register_address = decoded.get("register_address")

    if isinstance(register_address, int):
        return register_address in address_filter

    if isinstance(start_address, int) and isinstance(register_count, int) and register_count > 0:
        covered = range(start_address, start_address + register_count)
        return any(address in address_filter for address in covered)

    if isinstance(start_address, int):
        return start_address in address_filter

    return False


def extract_window(
    log_path: Path,
    from_ts: datetime,
    to_ts: datetime,
    slave_filter: set[int],
    request_filter: set[int],
    address_filter: set[int],
    function_filter: set[int],
    include_requests: bool,
    include_unchanged: bool,
) -> Dict[str, Any]:
    events: List[Dict[str, Any]] = []
    latest_values: Dict[Tuple[int, int], int] = {}
    matched_records = 0

    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not record.get("valid_crc"):
                continue

            decoded = record.get("decoded")
            if not isinstance(decoded, dict) or decoded.get("message_type") != "response":
                continue

            timestamp_raw = record.get("timestamp_utc")
            if not isinstance(timestamp_raw, str):
                continue
            timestamp = parse_timestamp(timestamp_raw)
            if timestamp < from_ts or timestamp > to_ts:
                continue

            slave_id = record.get("slave_id")
            if not isinstance(slave_id, int):
                continue
            if slave_filter and slave_id not in slave_filter:
                continue

            function_code = record.get("function_code")
            if function_filter and function_code not in function_filter:
                continue

            decoded = record.get("decoded")
            if not isinstance(decoded, dict):
                continue
            message_type = decoded.get("message_type")
            if message_type != "response" and not include_requests:
                continue

            correlated_request = record.get("correlated_request")
            request_start = None
            if isinstance(correlated_request, dict):
                start = correlated_request.get("start_address")
                if isinstance(start, int):
                    request_start = start
            if message_type == "response":
                if request_filter and request_start not in request_filter:
                    continue

                register_values = build_register_map(record)
                if not register_values:
                    continue
                if address_filter:
                    register_values = {
                        address: value
                        for address, value in register_values.items()
                        if address in address_filter
                    }
                    if not register_values:
                        continue

                matched_records += 1

                changed_values: Dict[int, int] = {}
                for address, value in sorted(register_values.items()):
                    key = (slave_id, address)
                    previous = latest_values.get(key)
                    latest_values[key] = value
                    if include_unchanged or previous != value:
                        changed_values[address] = value

                if not changed_values:
                    continue

                events.append(
                    {
                        "timestamp_utc": timestamp_raw,
                        "slave_id": slave_id,
                        "function_code": function_code,
                        "message_type": message_type,
                        "request_start_address": request_start,
                        "changed_registers": changed_values,
                    }
                )
                continue

            local_request_start = None
            if isinstance(decoded.get("start_address"), int):
                local_request_start = int(decoded["start_address"])
            elif isinstance(decoded.get("register_address"), int):
                local_request_start = int(decoded["register_address"])

            if request_filter and local_request_start not in request_filter:
                continue
            if not address_matches_request(decoded, address_filter):
                continue

            matched_records += 1

            event: Dict[str, Any] = {
                "timestamp_utc": timestamp_raw,
                "slave_id": slave_id,
                "function_code": function_code,
                "message_type": message_type,
            }
            if local_request_start is not None:
                event["request_start_address"] = local_request_start
            if isinstance(decoded.get("register_count"), int):
                event["register_count"] = int(decoded["register_count"])
            if isinstance(decoded.get("register_value"), int):
                event["register_value"] = int(decoded["register_value"])
            if isinstance(decoded.get("register_values"), list):
                values = [int(value) for value in decoded["register_values"] if isinstance(value, int)]
                if values:
                    event["register_values"] = values

            events.append(event)

    latest_summary = [
        {"slave_id": slave_id, "address": address, "value": value}
        for (slave_id, address), value in sorted(latest_values.items())
    ]

    return {
        "window": {
            "from_ts": from_ts.isoformat(),
            "to_ts": to_ts.isoformat(),
        },
        "filters": {
            "slave_ids": sorted(slave_filter),
            "request_start_addresses": sorted(request_filter),
            "addresses": sorted(address_filter),
            "function_codes": sorted(function_filter),
            "include_requests": include_requests,
            "include_unchanged": include_unchanged,
        },
        "matched_records": matched_records,
        "events": events,
        "latest_values": latest_summary,
    }


def main() -> int:
    args = parse_args()
    log_path = Path(args.log_file)
    if not log_path.exists():
        raise SystemExit(f"Soubor neexistuje: {log_path}")

    if args.to_ts < args.from_ts:
        raise SystemExit("--to-ts musi byt pozdeji nez --from-ts")

    result = extract_window(
        log_path=log_path,
        from_ts=args.from_ts,
        to_ts=args.to_ts,
        slave_filter=set(args.slave),
        request_filter=set(args.request_start),
        address_filter=set(args.address),
        function_filter=set(args.function_code),
        include_requests=args.include_requests,
        include_unchanged=args.include_unchanged,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
