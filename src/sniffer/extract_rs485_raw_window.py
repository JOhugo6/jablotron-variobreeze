#!/usr/bin/env python3
"""Extract raw RS-485 frames from a time window for selected slave IDs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Neplatny timestamp: {value}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vyrez surovych RS-485 ramcu z JSONL logu v zadanem casovem okne."
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
        help="Zacatek okna v ISO formatu, napr. 2026-03-26T09:12:00+00:00.",
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
        "--function-code",
        action="append",
        type=int,
        default=[],
        help="Volitelny filtr na konkretni Modbus function code. Lze zadat vicekrat.",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Zahrne i ramce s neplatnym CRC.",
    )
    return parser.parse_args()


def extract_raw_window(
    log_path: Path,
    from_ts: datetime,
    to_ts: datetime,
    slave_filter: set[int],
    function_filter: set[int],
    include_invalid: bool,
) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    by_function_code: Counter[str] = Counter()
    by_slave: Counter[str] = Counter()

    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not include_invalid and not record.get("valid_crc"):
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

            by_slave[str(slave_id)] += 1
            by_function_code[str(function_code)] += 1

            item: Dict[str, Any] = {
                "timestamp_utc": timestamp_raw,
                "slave_id": slave_id,
                "function_code": function_code,
                "length_bytes": record.get("length_bytes"),
                "valid_crc": record.get("valid_crc"),
                "raw_hex": record.get("raw_hex"),
            }

            if "decoded" in record:
                item["decoded"] = record["decoded"]
            if "correlated_request" in record:
                item["correlated_request"] = record["correlated_request"]
            if "register_map" in record:
                item["register_map"] = record["register_map"]
            if "crc_received" in record:
                item["crc_received"] = record["crc_received"]
            if "crc_expected" in record:
                item["crc_expected"] = record["crc_expected"]

            records.append(item)

    return {
        "window": {
            "from_ts": from_ts.isoformat(),
            "to_ts": to_ts.isoformat(),
        },
        "filters": {
            "slave_ids": sorted(slave_filter),
            "function_codes": sorted(function_filter),
            "include_invalid": include_invalid,
        },
        "matched_records": len(records),
        "counts": {
            "by_slave": dict(sorted(by_slave.items(), key=lambda item: int(item[0]))),
            "by_function_code": dict(sorted(by_function_code.items(), key=lambda item: int(item[0]))),
        },
        "records": records,
    }


def main() -> int:
    args = parse_args()
    log_path = Path(args.log_file)
    if not log_path.exists():
        raise SystemExit(f"Soubor neexistuje: {log_path}")
    if args.to_ts < args.from_ts:
        raise SystemExit("--to-ts musi byt pozdeji nez --from-ts")

    result = extract_raw_window(
        log_path=log_path,
        from_ts=args.from_ts,
        to_ts=args.to_ts,
        slave_filter=set(args.slave),
        function_filter=set(args.function_code),
        include_invalid=args.include_invalid,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
