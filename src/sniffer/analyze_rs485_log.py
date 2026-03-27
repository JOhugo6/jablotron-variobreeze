#!/usr/bin/env python3
"""Summarize decoded RS-485 monitor logs and highlight per-slave register activity."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


@dataclass
class RegisterStats:
    values: Set[int] = field(default_factory=set)
    samples: int = 0
    last_value: int | None = None

    def add(self, value: int) -> None:
        self.values.add(int(value))
        self.samples += 1
        self.last_value = int(value)


@dataclass
class SlaveStats:
    requests: Set[Tuple[int, int, int]] = field(default_factory=set)
    register_stats: Dict[int, RegisterStats] = field(default_factory=lambda: defaultdict(RegisterStats))
    response_count: int = 0
    first_seen: str | None = None
    last_seen: str | None = None

    def touch(self, timestamp: str) -> None:
        if self.first_seen is None:
            self.first_seen = timestamp
        self.last_seen = timestamp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Shrnutí JSONL logu z rs485_modbus_monitor.py po slave_id a registrech."
    )
    parser.add_argument(
        "log_file",
        nargs="?",
        default="logs/rs485_frames.jsonl",
        help="Cesta k JSONL logu.",
    )
    parser.add_argument(
        "--slave",
        type=int,
        default=None,
        help="Volitelně filtr jen pro konkrétní slave_id.",
    )
    return parser.parse_args()


def summarize(log_path: Path, only_slave: int | None = None) -> Dict[str, Any]:
    slaves: Dict[int, SlaveStats] = defaultdict(SlaveStats)

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

            slave_id = record.get("slave_id")
            if not isinstance(slave_id, int):
                continue
            if only_slave is not None and slave_id != only_slave:
                continue

            timestamp = str(record.get("timestamp_utc", ""))
            stats = slaves[slave_id]
            stats.touch(timestamp)

            decoded = record.get("decoded")
            if not isinstance(decoded, dict):
                continue

            message_type = decoded.get("message_type")
            function_code = record.get("function_code")
            if not isinstance(function_code, int):
                continue

            if (
                message_type == "request"
                and isinstance(decoded.get("start_address"), int)
                and isinstance(decoded.get("register_count"), int)
            ):
                stats.requests.add(
                    (
                        function_code,
                        int(decoded["start_address"]),
                        int(decoded["register_count"]),
                    )
                )

            if message_type == "response":
                stats.response_count += 1
                register_map = record.get("register_map")
                if isinstance(register_map, list):
                    for item in register_map:
                        if not isinstance(item, dict):
                            continue
                        address = item.get("address")
                        value = item.get("value")
                        if isinstance(address, int) and isinstance(value, int):
                            stats.register_stats[address].add(value)

    summary: Dict[str, Any] = {"slaves": []}
    for slave_id in sorted(slaves):
        stats = slaves[slave_id]
        registers: List[Dict[str, Any]] = []
        for address in sorted(stats.register_stats):
            reg = stats.register_stats[address]
            distinct_values = sorted(reg.values)
            registers.append(
                {
                    "address": address,
                    "samples": reg.samples,
                    "distinct_count": len(distinct_values),
                    "distinct_values": distinct_values[:20],
                    "last_value": reg.last_value,
                    "is_candidate_variable": len(distinct_values) > 1,
                }
            )

        summary["slaves"].append(
            {
                "slave_id": slave_id,
                "first_seen": stats.first_seen,
                "last_seen": stats.last_seen,
                "response_count": stats.response_count,
                "requests": [
                    {
                        "function_code": function_code,
                        "start_address": start_address,
                        "register_count": register_count,
                    }
                    for function_code, start_address, register_count in sorted(stats.requests)
                ],
                "registers": registers,
            }
        )

    return summary


def main() -> int:
    args = parse_args()
    log_path = Path(args.log_file)
    if not log_path.exists():
        raise SystemExit(f"Soubor neexistuje: {log_path}")

    summary = summarize(log_path=log_path, only_slave=args.slave)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
