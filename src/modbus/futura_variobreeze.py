#!/usr/bin/env python3
"""Read VarioBreeze damper data from Jablotron Futura via Modbus TCP."""

from __future__ import annotations

import argparse
import json
import math
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional

from pymodbus.client import ModbusTcpClient


RegisterType = Literal["input", "holding"]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_CONFIG: Dict[str, Any] = {
    "modbus": {
        "host": "192.168.1.50",
        "port": 502,
        "device_id": 1,
        "timeout_seconds": 3.0,
    },
    "service": {
        "access_code": None,
        "access_code_register": 900,
    },
    "registers": {
        "connected_supply_start": 70,
        "connected_exhaust_start": 72,
        "connected_word_order": "low_high",
        "position_source": "input",
        "position_scale_divisor": 1.0,
        "supply_position_registers": {},
        "exhaust_position_registers": {},
    },
    "poll": {
        "interval_seconds": 5.0,
    },
    "output": {
        "format": "text",
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def parse_int_mapping(value: Any) -> Dict[int, int]:
    if isinstance(value, list):
        return {index + 1: int(address) for index, address in enumerate(value)}
    if isinstance(value, dict):
        parsed: Dict[int, int] = {}
        for key, address in value.items():
            parsed[int(key)] = int(address)
        return parsed
    raise ValueError("Mapping must be dict or list.")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def decode_u32(registers: Iterable[int], word_order: str) -> int:
    values = list(registers)
    if len(values) != 2:
        raise ValueError("Expected exactly 2 registers for uint32.")
    lo, hi = values
    if word_order == "low_high":
        return (hi << 16) | lo
    if word_order == "high_low":
        return (lo << 16) | hi
    raise ValueError(f"Unsupported word order: {word_order}")


def bits_to_indexes(mask: int, max_bits: int = 32) -> List[int]:
    return [index + 1 for index in range(max_bits) if mask & (1 << index)]


def format_positions_text(label: str, positions: Dict[int, Optional[float]]) -> str:
    if not positions:
        return f"{label}: nejsou nakonfigurovány registry poloh."
    parts: List[str] = []
    for valve in sorted(positions):
        value = positions[valve]
        if value is None:
            parts.append(f"{valve}=N/A")
        else:
            parts.append(f"{valve}={value:.1f}%")
    return f"{label}: " + ", ".join(parts)


@dataclass
class ModbusSettings:
    host: str
    port: int
    device_id: int
    timeout_seconds: float


class FuturaClient:
    def __init__(self, settings: ModbusSettings):
        self.settings = settings
        self.client = ModbusTcpClient(
            host=settings.host,
            port=settings.port,
            timeout=settings.timeout_seconds,
        )

    def connect(self) -> None:
        if not self.client.connect():
            raise RuntimeError(
                f"Nepodařilo se připojit na {self.settings.host}:{self.settings.port}"
            )

    def close(self) -> None:
        self.client.close()

    def _read(self, register_type: RegisterType, address: int, count: int) -> List[int]:
        try:
            if register_type == "input":
                response = self.client.read_input_registers(
                    address=address,
                    count=count,
                    device_id=self.settings.device_id,
                )
            elif register_type == "holding":
                response = self.client.read_holding_registers(
                    address=address,
                    count=count,
                    device_id=self.settings.device_id,
                )
            else:
                raise ValueError(f"Unsupported register type: {register_type}")
        except ConnectionResetError as exc:
            raise RuntimeError(
                "Spojení resetoval vzdálený host (WinError 10054). "
                "Futura podporuje jen 1 Modbus socket, pravděpodobně je obsazený jiným klientem."
            ) from exc

        if response is None or response.isError():
            raise RuntimeError(
                f"Modbus chyba při čtení {register_type} registru {address} "
                f"(count={count})"
            )
        return [int(x) for x in response.registers]

    def read_register(self, register_type: RegisterType, address: int) -> int:
        return self._read(register_type, address, 1)[0]

    def read_u32(self, register_type: RegisterType, address: int, word_order: str) -> int:
        return decode_u32(self._read(register_type, address, 2), word_order)

    def write_register(self, address: int, value: int) -> None:
        try:
            response = self.client.write_register(
                address=address,
                value=value,
                device_id=self.settings.device_id,
            )
        except ConnectionResetError as exc:
            raise RuntimeError(
                "Spojení resetoval vzdálený host (WinError 10054). "
                "Futura podporuje jen 1 Modbus socket, pravděpodobně je obsazený jiným klientem."
            ) from exc
        if response is None or response.isError():
            raise RuntimeError(f"Modbus chyba při zápisu registru {address} hodnotou {value}")


def collect_snapshot(cfg: Dict[str, Any], client: FuturaClient) -> Dict[str, Any]:
    registers = cfg["registers"]
    connected_word_order = str(registers.get("connected_word_order", "low_high"))
    position_source = str(registers.get("position_source", "input"))
    divisor = float(registers.get("position_scale_divisor", 1.0))
    if math.isclose(divisor, 0.0):
        raise ValueError("position_scale_divisor nesmí být 0.")

    supply_connected_mask = client.read_u32(
        register_type="input",
        address=int(registers["connected_supply_start"]),
        word_order=connected_word_order,
    )
    exhaust_connected_mask = client.read_u32(
        register_type="input",
        address=int(registers["connected_exhaust_start"]),
        word_order=connected_word_order,
    )

    supply_connected = bits_to_indexes(supply_connected_mask)
    exhaust_connected = bits_to_indexes(exhaust_connected_mask)

    supply_map = parse_int_mapping(registers.get("supply_position_registers", {}))
    exhaust_map = parse_int_mapping(registers.get("exhaust_position_registers", {}))

    def read_positions(mapping: Dict[int, int]) -> Dict[int, Optional[float]]:
        result: Dict[int, Optional[float]] = {}
        for valve, address in sorted(mapping.items()):
            raw = client.read_register(position_source, address)
            result[valve] = raw / divisor
        return result

    supply_positions = read_positions(supply_map)
    exhaust_positions = read_positions(exhaust_map)

    return {
        "timestamp_utc": now_iso(),
        "connected": {
            "supply_mask_u32": supply_connected_mask,
            "exhaust_mask_u32": exhaust_connected_mask,
            "supply_valves": supply_connected,
            "exhaust_valves": exhaust_connected,
        },
        "positions_percent": {
            "supply": supply_positions,
            "exhaust": exhaust_positions,
        },
    }


def run_discovery(
    client: FuturaClient,
    register_type: RegisterType,
    start_address: int,
    count: int,
    samples: int,
    sample_interval: float,
    probe_count: int,
    value_min: Optional[int],
    value_max: Optional[int],
) -> Dict[str, Any]:
    if count <= 0:
        raise ValueError("count musí být > 0")
    if samples <= 0:
        raise ValueError("samples musí být > 0")
    if probe_count <= 0:
        raise ValueError("probe_count musí být > 0")

    end_address = start_address + count
    history: Dict[int, List[int]] = {address: [] for address in range(start_address, end_address)}
    successful_probes = 0

    for sample_index in range(samples):
        for address in range(start_address, end_address - probe_count + 1):
            try:
                regs = client._read(register_type, address, probe_count)
            except RuntimeError:
                continue
            successful_probes += 1
            for offset, value in enumerate(regs):
                target = address + offset
                if target in history:
                    history[target].append(value)
        if sample_index + 1 < samples:
            time.sleep(sample_interval)

    candidates: List[Dict[str, Any]] = []
    for address in range(start_address, end_address):
        values = history[address]
        unique_values = sorted(set(values))
        if not unique_values:
            continue
        min_v = min(unique_values)
        max_v = max(unique_values)
        if value_min is not None and min_v < value_min:
            continue
        if value_max is not None and max_v > value_max:
            continue
        candidates.append(
            {
                "address": address,
                "min": min_v,
                "max": max_v,
                "distinct_values": len(unique_values),
                "samples_collected": len(values),
                "values_seen": unique_values[:20],
            }
        )

    candidates.sort(
        key=lambda c: (c["distinct_values"], c["max"] - c["min"], -c["address"]),
        reverse=True,
    )

    return {
        "timestamp_utc": now_iso(),
        "scan": {
            "register_type": register_type,
            "start_address": start_address,
            "count": count,
            "samples": samples,
            "sample_interval_seconds": sample_interval,
            "probe_count": probe_count,
            "value_min": value_min,
            "value_max": value_max,
            "successful_probes": successful_probes,
        },
        "candidate_registers": candidates,
    }


def sample_sparse_registers(
    client: FuturaClient,
    register_type: RegisterType,
    start_address: int,
    count: int,
    probe_count: int,
) -> tuple[Dict[int, int], int]:
    if count <= 0:
        raise ValueError("count musí být > 0")
    if probe_count <= 0:
        raise ValueError("probe_count musí být > 0")

    end_address = start_address + count
    values: Dict[int, int] = {}
    successful_probes = 0

    for address in range(start_address, end_address - probe_count + 1):
        try:
            regs = client._read(register_type, address, probe_count)
        except RuntimeError:
            continue
        successful_probes += 1
        for offset, value in enumerate(regs):
            target = address + offset
            if target < end_address:
                values[target] = value

    return values, successful_probes


def print_monitor_snapshot(
    register_type: RegisterType,
    start_address: int,
    count: int,
    values: Dict[int, int],
    changed: Dict[int, tuple[int, int]],
    successful_probes: int,
) -> None:
    print(
        f"[{now_iso()}] monitor {register_type} {start_address}-{start_address + count - 1} "
        f"readable={len(values)} probes={successful_probes} changed={len(changed)}"
    )
    for address in sorted(changed):
        previous, current = changed[address]
        print(f"  {address}: {previous} -> {current}")
    print("")


def run_change_monitor(
    client: FuturaClient,
    register_type: RegisterType,
    start_address: int,
    count: int,
    interval_seconds: float,
    probe_count: int,
    max_cycles: int,
    access_code: Optional[int],
    access_code_register: int,
    stop_requested: Callable[[], bool],
) -> None:
    previous_values: Optional[Dict[int, int]] = None
    cycle = 0

    while not stop_requested():
        cycle += 1
        if access_code is not None:
            client.write_register(access_code_register, access_code)
        current_values, successful_probes = sample_sparse_registers(
            client=client,
            register_type=register_type,
            start_address=start_address,
            count=count,
            probe_count=probe_count,
        )
        if previous_values is None:
            changed = {address: (value, value) for address, value in current_values.items()}
        else:
            changed = {
                address: (previous_values[address], value)
                for address, value in current_values.items()
                if address in previous_values and previous_values[address] != value
            }

        print_monitor_snapshot(
            register_type=register_type,
            start_address=start_address,
            count=count,
            values=current_values,
            changed=changed,
            successful_probes=successful_probes,
        )
        previous_values = current_values

        if max_cycles > 0 and cycle >= max_cycles:
            break
        if stop_requested():
            break
        time.sleep(interval_seconds)


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Konfigurační soubor neexistuje: {path}")
    with path.open("r", encoding="utf-8") as f:
        user_cfg = json.load(f)
    return deep_merge(DEFAULT_CONFIG, user_cfg)


def print_snapshot_text(snapshot: Dict[str, Any]) -> None:
    connected = snapshot["connected"]
    positions = snapshot["positions_percent"]
    print(f"[{snapshot['timestamp_utc']}]")
    print(
        "Přívodní klapky připojené: "
        + (", ".join(str(x) for x in connected["supply_valves"]) or "žádné")
    )
    print(
        "Odtahové klapky připojené: "
        + (", ".join(str(x) for x in connected["exhaust_valves"]) or "žádné")
    )
    print(format_positions_text("Polohy přívodních klapek", positions["supply"]))
    print(format_positions_text("Polohy odtahových klapek", positions["exhaust"]))
    print("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Čte stav a polohy klapek VarioBreeze z Jablotron Futura přes Modbus TCP."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("config.example.json"),
        help="Cesta ke konfiguračnímu JSON souboru.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Načti jednou a ukonči.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Vynutí JSON výstup do stdout.",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Spustí discovery režim pro hledání registrů poloh 0-100.",
    )
    parser.add_argument("--discover-start", type=int, default=0, help="Počáteční adresa pro discovery.")
    parser.add_argument("--discover-count", type=int, default=500, help="Počet registrů pro discovery.")
    parser.add_argument("--discover-samples", type=int, default=5, help="Počet vzorků v discovery.")
    parser.add_argument(
        "--discover-interval",
        type=float,
        default=1.0,
        help="Interval mezi vzorky v discovery (sekundy).",
    )
    parser.add_argument(
        "--discover-type",
        choices=["input", "holding"],
        default="input",
        help="Typ registrů pro discovery.",
    )
    parser.add_argument(
        "--discover-probe-count",
        type=int,
        default=2,
        help="Kolik registrů číst v jednom discovery dotazu. Hodí se pro řídké mapy.",
    )
    parser.add_argument(
        "--discover-min",
        type=int,
        default=0,
        help="Minimální hodnota kandidáta. Pro vypnutí spodního filtru použijte záporné číslo.",
    )
    parser.add_argument(
        "--discover-max",
        type=int,
        default=100,
        help="Maximální hodnota kandidáta. Pro vypnutí horního filtru použijte záporné číslo.",
    )
    parser.add_argument(
        "--access-code",
        type=int,
        default=None,
        help="Volitelný access code pro servisní registry (přepíše konfiguraci).",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Průběžně sleduje změny registrů v rozsahu a vypisuje jen změny hodnot.",
    )
    parser.add_argument(
        "--monitor-start",
        type=int,
        default=0,
        help="Počáteční adresa pro monitor změn.",
    )
    parser.add_argument(
        "--monitor-count",
        type=int,
        default=100,
        help="Počet registrů pro monitor změn.",
    )
    parser.add_argument(
        "--monitor-interval",
        type=float,
        default=5.0,
        help="Interval monitoru změn v sekundách.",
    )
    parser.add_argument(
        "--monitor-type",
        choices=["input", "holding"],
        default="input",
        help="Typ registrů pro monitor změn.",
    )
    parser.add_argument(
        "--monitor-probe-count",
        type=int,
        default=2,
        help="Kolik registrů číst v jednom dotazu monitoru změn.",
    )
    parser.add_argument(
        "--monitor-cycles",
        type=int,
        default=0,
        help="Počet cyklů monitoru. 0 = běží do přerušení.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        cfg = load_config(args.config)
    except Exception as exc:
        print(f"Chyba konfigurace: {exc}", file=sys.stderr)
        return 2

    output_json = bool(args.json or str(cfg["output"].get("format", "text")).lower() == "json")

    settings = ModbusSettings(
        host=str(cfg["modbus"]["host"]),
        port=int(cfg["modbus"]["port"]),
        device_id=int(cfg["modbus"].get("device_id", 1)),
        timeout_seconds=float(cfg["modbus"].get("timeout_seconds", 3.0)),
    )

    stop = False

    def handle_sigint(_sig: int, _frame: Any) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    client = FuturaClient(settings)
    try:
        client.connect()

        access_code = args.access_code
        if access_code is None:
            access_code = cfg["service"].get("access_code")
        if access_code is not None:
            client.write_register(
                int(cfg["service"].get("access_code_register", 900)),
                int(access_code),
            )

        if args.discover:
            discover_min = None if int(args.discover_min) < 0 else int(args.discover_min)
            discover_max = None if int(args.discover_max) < 0 else int(args.discover_max)
            discovery = run_discovery(
                client=client,
                register_type=args.discover_type,  # type: ignore[arg-type]
                start_address=int(args.discover_start),
                count=int(args.discover_count),
                samples=int(args.discover_samples),
                sample_interval=float(args.discover_interval),
                probe_count=int(args.discover_probe_count),
                value_min=discover_min,
                value_max=discover_max,
            )
            print(json.dumps(discovery, ensure_ascii=False, indent=2))
            return 0

        if args.monitor:
            run_change_monitor(
                client=client,
                register_type=args.monitor_type,  # type: ignore[arg-type]
                start_address=int(args.monitor_start),
                count=int(args.monitor_count),
                interval_seconds=float(args.monitor_interval),
                probe_count=int(args.monitor_probe_count),
                max_cycles=int(args.monitor_cycles),
                access_code=None if access_code is None else int(access_code),
                access_code_register=int(cfg["service"].get("access_code_register", 900)),
                stop_requested=lambda: stop,
            )
            return 0

        interval_seconds = float(cfg["poll"].get("interval_seconds", 5.0))
        while not stop:
            snapshot = collect_snapshot(cfg, client)
            if output_json:
                print(json.dumps(snapshot, ensure_ascii=False))
            else:
                print_snapshot_text(snapshot)
            if args.once:
                break
            time.sleep(interval_seconds)

    except Exception as exc:
        print(f"Chyba: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
