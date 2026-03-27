#!/usr/bin/env python3
"""Passive RS-485 Modbus RTU sniffer with a local read-only HTTP API."""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def parity_name(value: str) -> str:
    mapping = {"N": "none", "E": "even", "O": "odd"}
    return mapping.get(value.upper(), value.lower())


def build_register_map(start_address: int, values: List[int]) -> List[Dict[str, int]]:
    return [
        {"address": start_address + index, "value": int(value)}
        for index, value in enumerate(values)
    ]


def candidate_frame_lengths(data: bytes) -> Tuple[List[int], bool]:
    if len(data) < 2:
        return [], True

    slave_id = data[0]
    function_code = data[1]

    if not 1 <= slave_id <= 247:
        return [], False

    lengths: set[int] = set()
    needs_more = False

    if function_code & 0x80:
        lengths.add(5)
        if len(data) < 5:
            needs_more = True
        return sorted(lengths), needs_more

    if function_code in {0x03, 0x04}:
        lengths.add(8)
        if len(data) < 8:
            needs_more = True
        if len(data) >= 3:
            byte_count = data[2]
            if 0 < byte_count <= 250 and byte_count % 2 == 0:
                lengths.add(byte_count + 5)
                if len(data) < byte_count + 5:
                    needs_more = True
        else:
            needs_more = True
        return sorted(lengths), needs_more

    if function_code == 0x06:
        lengths.add(8)
        if len(data) < 8:
            needs_more = True
        return sorted(lengths), needs_more

    if function_code == 0x10:
        lengths.add(8)
        if len(data) < 8:
            needs_more = True
        if len(data) >= 7:
            byte_count = data[6]
            if 0 < byte_count <= 246 and byte_count % 2 == 0:
                lengths.add(byte_count + 9)
                if len(data) < byte_count + 9:
                    needs_more = True
        else:
            needs_more = True
        return sorted(lengths), needs_more

    return [], False


def find_valid_frame(buffer: bytes) -> Tuple[Optional[int], Optional[bytes], bool]:
    earliest_partial_offset: Optional[int] = None

    for offset in range(len(buffer)):
        remaining = buffer[offset:]
        lengths, needs_more = candidate_frame_lengths(remaining)
        if not lengths:
            continue

        if needs_more and earliest_partial_offset is None:
            earliest_partial_offset = offset

        valid_candidates: List[bytes] = []
        for length in lengths:
            if len(remaining) < length:
                continue
            frame = remaining[:length]
            expected_crc = crc16_modbus(frame[:-2])
            received_crc = int.from_bytes(frame[-2:], byteorder="little", signed=False)
            if expected_crc == received_crc:
                valid_candidates.append(frame)

        if valid_candidates:
            # Prefer the longest valid frame to avoid cutting a long response too early.
            frame = max(valid_candidates, key=len)
            return offset, frame, False

    if earliest_partial_offset is not None:
        return earliest_partial_offset, None, True

    return None, None, False


def extract_valid_frames(buffer: bytearray) -> List[bytes]:
    frames: List[bytes] = []

    while buffer:
        offset, frame, needs_more = find_valid_frame(bytes(buffer))
        if frame is not None and offset is not None:
            if offset > 0:
                del buffer[:offset]
            frame_length = len(frame)
            frames.append(bytes(buffer[:frame_length]))
            del buffer[:frame_length]
            continue

        if offset is not None and needs_more:
            if offset > 0:
                del buffer[:offset]
                continue
            break

        break

    return frames


def buffer_needs_more_data(buffer: bytes) -> bool:
    offset, frame, needs_more = find_valid_frame(buffer)
    return frame is None and offset == 0 and needs_more


def decode_modbus_frame(frame: bytes) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "length_bytes": len(frame),
        "raw_hex": frame.hex(" "),
        "valid_crc": False,
    }

    if len(frame) < 4:
        result["error"] = "frame_too_short"
        return result

    payload = frame[:-2]
    received_crc = int.from_bytes(frame[-2:], byteorder="little", signed=False)
    expected_crc = crc16_modbus(payload)
    valid_crc = received_crc == expected_crc

    result.update(
        {
            "valid_crc": valid_crc,
            "crc_received": f"0x{received_crc:04x}",
            "crc_expected": f"0x{expected_crc:04x}",
            "slave_id": payload[0],
            "function_code": payload[1],
        }
    )

    function_code = payload[1]
    body = payload[2:]
    decoded: Dict[str, Any] = {}

    if function_code in {0x03, 0x04}:
        if len(payload) == 6:
            decoded = {
                "message_type": "request",
                "start_address": int.from_bytes(body[:2], "big"),
                "register_count": int.from_bytes(body[2:4], "big"),
            }
        elif len(body) >= 1 and len(body) == body[0] + 1:
            register_values = [
                int.from_bytes(body[index:index + 2], "big")
                for index in range(1, len(body), 2)
                if index + 1 < len(body)
            ]
            decoded = {
                "message_type": "response",
                "byte_count": body[0],
                "register_values": register_values,
            }
    elif function_code == 0x06 and len(payload) == 6:
        decoded = {
            "message_type": "write_single_register",
            "register_address": int.from_bytes(body[:2], "big"),
            "register_value": int.from_bytes(body[2:4], "big"),
        }
    elif function_code == 0x10:
        if len(payload) == 6:
            decoded = {
                "message_type": "write_multiple_registers_response",
                "start_address": int.from_bytes(body[:2], "big"),
                "register_count": int.from_bytes(body[2:4], "big"),
            }
        elif len(body) >= 5 and len(body) == body[4] + 5:
            values = [
                int.from_bytes(body[index:index + 2], "big")
                for index in range(5, len(body), 2)
                if index + 1 < len(body)
            ]
            decoded = {
                "message_type": "write_multiple_registers_request",
                "start_address": int.from_bytes(body[:2], "big"),
                "register_count": int.from_bytes(body[2:4], "big"),
                "byte_count": body[4],
                "register_values": values,
            }
    elif function_code & 0x80 and len(body) == 1:
        decoded = {
            "message_type": "exception",
            "exception_code": body[0],
        }

    if decoded:
        result["decoded"] = decoded

    return result


class MonitorState:
    def __init__(self, max_frames: int, serial_config: Dict[str, Any]):
        self.lock = threading.Lock()
        self.frames: Deque[Dict[str, Any]] = deque(maxlen=max_frames)
        self.serial_config = serial_config
        self.frames_total = 0
        self.frames_valid_crc = 0
        self.last_frame_at: Optional[str] = None
        self.started_at = now_iso()
        self.pending_requests: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.latest_responses_by_slave: Dict[int, Dict[str, Any]] = {}

    def record_frame(self, frame: bytes) -> Dict[str, Any]:
        decoded = decode_modbus_frame(frame)
        record = {
            "timestamp_utc": now_iso(),
            **decoded,
        }
        with self.lock:
            self._enrich_record_locked(record)
            self.frames.append(record)
            self.frames_total += 1
            if record["valid_crc"]:
                self.frames_valid_crc += 1
            self.last_frame_at = record["timestamp_utc"]
        return record

    def _enrich_record_locked(self, record: Dict[str, Any]) -> None:
        if not record.get("valid_crc"):
            return

        slave_id = record.get("slave_id")
        function_code = record.get("function_code")
        decoded = record.get("decoded")
        if not isinstance(slave_id, int) or not isinstance(function_code, int) or not isinstance(decoded, dict):
            return

        message_type = decoded.get("message_type")
        key = (slave_id, function_code)

        if (
            message_type == "request"
            and isinstance(decoded.get("start_address"), int)
            and isinstance(decoded.get("register_count"), int)
        ):
            self.pending_requests[key] = {
                "timestamp_utc": record["timestamp_utc"],
                "start_address": int(decoded["start_address"]),
                "register_count": int(decoded["register_count"]),
            }
            return

        if message_type != "response":
            return

        request = self.pending_requests.get(key)
        if request is not None:
            record["correlated_request"] = dict(request)
            register_values = decoded.get("register_values")
            if isinstance(register_values, list) and request["register_count"] == len(register_values):
                record["register_map"] = build_register_map(
                    start_address=request["start_address"],
                    values=[int(value) for value in register_values],
                )

        self.latest_responses_by_slave[slave_id] = record

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "started_at": self.started_at,
                "last_frame_at": self.last_frame_at,
                "frames_total": self.frames_total,
                "frames_valid_crc": self.frames_valid_crc,
                "frames_buffered": len(self.frames),
                "slaves_with_latest_response": len(self.latest_responses_by_slave),
                "serial": dict(self.serial_config),
            }

    def latest(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            return None if not self.frames else dict(self.frames[-1])

    def recent_frames(self, limit: int) -> list[Dict[str, Any]]:
        with self.lock:
            return [dict(frame) for frame in list(self.frames)[-limit:]]

    def latest_responses(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                dict(self.latest_responses_by_slave[slave_id])
                for slave_id in sorted(self.latest_responses_by_slave)
            ]


def build_handler(state: MonitorState):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            if parsed.path == "/health":
                self._send_json({"ok": True, **state.snapshot()})
                return
            if parsed.path == "/stats":
                self._send_json(state.snapshot())
                return
            if parsed.path == "/latest":
                latest = state.latest()
                if latest is None:
                    self._send_json({"error": "no_frames_yet"}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json(latest)
                return
            if parsed.path == "/frames":
                limit = 100
                if "limit" in query:
                    try:
                        limit = max(1, min(1000, int(query["limit"][0])))
                    except ValueError:
                        self._send_json({"error": "invalid_limit"}, HTTPStatus.BAD_REQUEST)
                        return
                self._send_json({"frames": state.recent_frames(limit), "stats": state.snapshot()})
                return
            if parsed.path == "/devices":
                self._send_json({"devices": state.latest_responses(), "stats": state.snapshot()})
                return

            self._send_json(
                {
                    "error": "not_found",
                    "available_paths": ["/health", "/stats", "/latest", "/frames?limit=100", "/devices"],
                },
                HTTPStatus.NOT_FOUND,
            )

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def open_serial_port(args: argparse.Namespace):
    try:
        import serial  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Chybí pyserial. Nainstalujte ho příkazem: py -m pip install pyserial"
        ) from exc

    parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD}
    stop_bits_map = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}

    return serial.Serial(
        port=args.serial_port,
        baudrate=args.baudrate,
        bytesize=args.bytesize,
        parity=parity_map[args.parity],
        stopbits=stop_bits_map[args.stopbits],
        timeout=args.serial_timeout,
    )


def sniff_serial(
    serial_port: Any,
    state: MonitorState,
    frame_gap_seconds: float,
    log_file: Path,
    stop_event: threading.Event,
) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    frame_buffer = bytearray()
    last_byte_at = time.monotonic()
    partial_frame_stale_seconds = max(0.1, frame_gap_seconds * 10)

    with log_file.open("a", encoding="utf-8") as handle:
        while not stop_event.is_set():
            chunk = serial_port.read(256)
            now = time.monotonic()

            if chunk:
                frame_buffer.extend(chunk)
                for frame in extract_valid_frames(frame_buffer):
                    record = state.record_frame(frame)
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    handle.flush()
                last_byte_at = now
                continue

            if frame_buffer and now - last_byte_at >= frame_gap_seconds:
                for frame in extract_valid_frames(frame_buffer):
                    record = state.record_frame(frame)
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    handle.flush()

                if (
                    frame_buffer
                    and buffer_needs_more_data(bytes(frame_buffer))
                    and now - last_byte_at < partial_frame_stale_seconds
                ):
                    continue

                if frame_buffer:
                    record = state.record_frame(bytes(frame_buffer))
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    handle.flush()
                    frame_buffer.clear()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pasivní RS-485/Modbus RTU monitor s lokálním HTTP API."
    )
    parser.add_argument("--serial-port", required=True, help="Sériový port, např. COM5.")
    parser.add_argument("--baudrate", type=int, default=19200, help="Rychlost linky.")
    parser.add_argument("--bytesize", type=int, choices=[7, 8], default=8, help="Počet datových bitů.")
    parser.add_argument("--parity", choices=["N", "E", "O"], default="N", help="Parita.")
    parser.add_argument("--stopbits", type=int, choices=[1, 2], default=1, help="Počet stop bitů.")
    parser.add_argument(
        "--serial-timeout",
        type=float,
        default=0.05,
        help="Timeout sériového čtení v sekundách.",
    )
    parser.add_argument(
        "--frame-gap-ms",
        type=float,
        default=20.0,
        help="Mezera mezi rámci v milisekundách.",
    )
    parser.add_argument(
        "--listen-host",
        default="127.0.0.1",
        help="Adresa lokálního HTTP API. Pro bezpečný provoz nechte 127.0.0.1.",
    )
    parser.add_argument("--listen-port", type=int, default=8765, help="Port HTTP API.")
    parser.add_argument(
        "--frames-buffer",
        type=int,
        default=500,
        help="Kolik posledních rámců držet v paměti pro HTTP API.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/rs485_frames.jsonl"),
        help="Kam ukládat JSONL log rámců.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    stop_event = threading.Event()

    def handle_signal(_sig: int, _frame: Any) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    serial_config = {
        "port": args.serial_port,
        "baudrate": args.baudrate,
        "bytesize": args.bytesize,
        "parity": parity_name(args.parity),
        "stopbits": args.stopbits,
        "frame_gap_ms": args.frame_gap_ms,
        "listen_host": args.listen_host,
        "listen_port": args.listen_port,
        "log_file": str(args.log_file),
    }
    state = MonitorState(max_frames=args.frames_buffer, serial_config=serial_config)

    try:
        serial_port = open_serial_port(args)
    except Exception as exc:
        print(f"Chyba sériového portu: {exc}", file=sys.stderr)
        return 2

    http_server = ThreadingHTTPServer((args.listen_host, args.listen_port), build_handler(state))
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    print(
        f"RS-485 monitor běží. HTTP API: http://{args.listen_host}:{args.listen_port} "
        f"log: {args.log_file}"
    )

    try:
        sniff_serial(
            serial_port=serial_port,
            state=state,
            frame_gap_seconds=max(0.001, args.frame_gap_ms / 1000.0),
            log_file=args.log_file,
            stop_event=stop_event,
        )
    except Exception as exc:
        print(f"Chyba monitoru: {exc}", file=sys.stderr)
        return 1
    finally:
        stop_event.set()
        http_server.shutdown()
        http_server.server_close()
        serial_port.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
