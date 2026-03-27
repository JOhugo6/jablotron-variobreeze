#!/usr/bin/env python3
"""Passive RS485 bridge for Pi Zero that derives damper state from Modbus RTU traffic."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import signal
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


if __package__ in {None, ""}:
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parents[2] if len(current_dir.parents) >= 3 else current_dir
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(project_root))

try:
    from src.sniffer.rs485_modbus_monitor import (  # noqa: E402
        build_register_map,
        buffer_needs_more_data,
        decode_modbus_frame,
        extract_valid_frames,
        now_iso,
        parity_name,
    )
except ImportError:
    from rs485_modbus_monitor import (  # type: ignore[no-redef]  # noqa: E402
        build_register_map,
        buffer_needs_more_data,
        decode_modbus_frame,
        extract_valid_frames,
        now_iso,
        parity_name,
    )


DEFAULT_CONFIG: Dict[str, Any] = {
    "serial": {
        "port": "/dev/serial0",
        "baudrate": 19200,
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "serial_timeout_seconds": 0.001,
        "frame_gap_ms": 3.0,
    },
    "http": {
        "enabled": True,
        "listen_host": "127.0.0.1",
        "listen_port": 8765,
    },
    "mqtt": {
        "enabled": False,
        "host": "127.0.0.1",
        "port": 1883,
        "username": None,
        "password": None,
        "client_id": "futura-zero",
        "topic_prefix": "futura",
        "retain": True,
        "qos": 1,
        "publish_on_change_only": True,
    },
    "storage": {
        "state_path": "state/dampers_state.json",
        "snapshot_interval_seconds": 60,
        "restore_state_on_start": True,
        "write_state_on_shutdown": True,
    },
    "debug": {
        "raw_log_enabled": False,
        "raw_log_path": "debug/raw.jsonl",
        "raw_log_rotate_bytes": 5_242_880,
        "raw_log_keep_files": 5,
        "raw_log_compress_rotated": True,
    },
    "damper_map": {
        "path": "damper-map.json",
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


def resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)


@dataclass
class DamperMapEntry:
    slave_id: int
    room: str
    zone: int
    type: str
    damper_index: int
    label: str
    enabled: bool
    notes: Optional[str] = None


class RawRecordLogger:
    def __init__(
        self,
        enabled: bool,
        path: Path,
        rotate_bytes: int,
        keep_files: int,
        compress_rotated: bool,
    ) -> None:
        self.enabled = enabled
        self.path = path
        self.rotate_bytes = max(1, int(rotate_bytes))
        self.keep_files = max(1, int(keep_files))
        self.compress_rotated = compress_rotated
        self._handle: Optional[Any] = None

    def _open(self) -> None:
        if self._handle is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self.path.open("a", encoding="utf-8")

    def _rotated_candidates(self) -> List[Path]:
        pattern = f"{self.path.stem}-*{self.path.suffix}*"
        return sorted(self.path.parent.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)

    def _prune(self) -> None:
        for stale_path in self._rotated_candidates()[self.keep_files:]:
            stale_path.unlink(missing_ok=True)

    def _rotate(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

        if not self.path.exists():
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        rotated = self.path.with_name(f"{self.path.stem}-{timestamp}{self.path.suffix}")
        self.path.replace(rotated)

        if self.compress_rotated:
            compressed = rotated.with_suffix(rotated.suffix + ".gz")
            with rotated.open("rb") as src, gzip.open(compressed, "wb") as dst:
                dst.write(src.read())
            rotated.unlink(missing_ok=True)

        self._prune()

    def write(self, record: Dict[str, Any]) -> None:
        if not self.enabled:
            return

        line = json.dumps(record, ensure_ascii=False) + "\n"
        encoded_len = len(line.encode("utf-8"))

        if self.path.exists() and self.path.stat().st_size + encoded_len > self.rotate_bytes:
            self._rotate()

        self._open()
        assert self._handle is not None
        self._handle.write(line)
        self._handle.flush()

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


class MqttPublisher:
    def __init__(self, config: Dict[str, Any], state_getter: Callable[[], List[Dict[str, Any]]]) -> None:
        self.enabled = bool(config.get("enabled", False))
        self.host = str(config.get("host", "127.0.0.1"))
        self.port = int(config.get("port", 1883))
        self.username = config.get("username")
        self.password = config.get("password")
        self.client_id = str(config.get("client_id", "futura-zero"))
        self.topic_prefix = str(config.get("topic_prefix", "futura")).rstrip("/")
        self.retain = bool(config.get("retain", True))
        self.qos = int(config.get("qos", 1))
        self.publish_on_change_only = bool(config.get("publish_on_change_only", True))
        self._state_getter = state_getter
        self._lock = threading.Lock()
        self._connected = False
        self._last_error: Optional[str] = None
        self._client: Optional[Any] = None
        self._last_published_payload_by_topic: Dict[str, str] = {}

        if not self.enabled:
            return

        try:
            import paho.mqtt.client as mqtt  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "MQTT je zapnuté, ale chybí paho-mqtt. Nainstalujte ho přes: pip install -r src/sniffer/requirements.txt"
            ) from exc

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )
        if self.username:
            client.username_pw_set(self.username, self.password)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        if hasattr(client, "on_connect_fail"):
            client.on_connect_fail = self._on_connect_fail
        self._client = client

    @property
    def connected(self) -> bool:
        with self._lock:
            return self._connected

    @property
    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def _set_connected(self, value: bool) -> None:
        with self._lock:
            self._connected = value

    def _set_last_error(self, value: Optional[str]) -> None:
        with self._lock:
            self._last_error = value

    @staticmethod
    def _reason_code_ok(reason_code: Any) -> bool:
        if reason_code is None:
            return False
        if hasattr(reason_code, "is_failure"):
            try:
                return not bool(reason_code.is_failure)
            except Exception:
                pass
        try:
            return int(reason_code) == 0
        except Exception:
            return str(reason_code).strip().lower() in {"0", "success"}

    def _on_connect(self, client: Any, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any = None) -> None:
        connected = self._reason_code_ok(reason_code)
        self._set_connected(connected)
        if connected:
            self._set_last_error(None)
            print(f"MQTT připojeno: {self.host}:{self.port} ({reason_code})", file=sys.stderr)
            self.publish_all()
            return
        message = f"Broker odmítl připojení MQTT: {reason_code}"
        self._set_last_error(message)
        print(message, file=sys.stderr)

    def _on_disconnect(self, _client: Any, _userdata: Any, _flags: Any, _reason_code: Any, _properties: Any = None) -> None:
        self._set_connected(False)
        if self.enabled:
            self._set_last_error("MQTT bylo odpojeno.")

    def _on_connect_fail(self, _client: Any, _userdata: Any) -> None:
        self._set_connected(False)
        self._set_last_error(f"Nepodařilo se navázat MQTT spojení na {self.host}:{self.port}.")
        print(self.last_error, file=sys.stderr)

    def connect(self) -> None:
        if not self.enabled or self._client is None:
            return
        try:
            self._client.connect_async(self.host, self.port, keepalive=30)
        except Exception as exc:
            self._set_connected(False)
            self._set_last_error(f"MQTT connect selhal: {exc}")
            print(self.last_error, file=sys.stderr)
            return
        self._client.loop_start()

    def publish_damper(self, damper: Dict[str, Any], force: bool = False) -> None:
        if not self.enabled or self._client is None or not self.connected:
            return
        topic = f"{self.topic_prefix}/damper/{damper['slave_id']}/state"
        payload = json.dumps(damper, ensure_ascii=False)
        if self.publish_on_change_only and not force:
            previous = self._last_published_payload_by_topic.get(topic)
            if previous == payload:
                return
        self._client.publish(topic, payload, qos=self.qos, retain=self.retain)
        self._last_published_payload_by_topic[topic] = payload

    def publish_all(self) -> None:
        if not self.enabled or self._client is None or not self.connected:
            return
        for damper in self._state_getter():
            self.publish_damper(damper, force=True)

    def close(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        self._set_connected(False)


class DamperBridgeState:
    def __init__(
        self,
        serial_config: Dict[str, Any],
        damper_entries: Iterable[DamperMapEntry],
        state_path: Path,
        snapshot_interval_seconds: float,
    ) -> None:
        self.lock = threading.RLock()
        self.serial_config = serial_config
        self.state_path = state_path
        self.snapshot_interval_seconds = max(5.0, float(snapshot_interval_seconds))
        self.started_at = now_iso()
        self.last_frame_at: Optional[str] = None
        self.frames_total = 0
        self.frames_valid_crc = 0
        self.last_frame: Optional[Dict[str, Any]] = None
        self.recent_frames: Deque[Dict[str, Any]] = deque(maxlen=100)
        self.latest_responses_by_slave: Dict[int, Dict[str, Any]] = {}
        self.pending_requests: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.dampers: Dict[int, Dict[str, Any]] = {
            entry.slave_id: {
                "slave_id": entry.slave_id,
                "room": entry.room,
                "zone": entry.zone,
                "type": entry.type,
                "damper_index": entry.damper_index,
                "label": entry.label,
                "enabled": entry.enabled,
                "notes": entry.notes,
                "target_position": None,
                "status_code": None,
                "last_target_ts": None,
                "last_status_ts": None,
                "last_seen_ts": None,
            }
            for entry in damper_entries
        }
        self.dirty = False
        self.last_snapshot_written_at: Optional[str] = None
        self._last_snapshot_monotonic = time.monotonic()
        self.mqtt_enabled = False
        self.mqtt_connected = False
        self.mqtt_last_error: Optional[str] = None

    def set_mqtt_status(self, enabled: bool, connected: bool, last_error: Optional[str] = None) -> None:
        with self.lock:
            self.mqtt_enabled = enabled
            self.mqtt_connected = connected
            self.mqtt_last_error = last_error

    def restore_snapshot(self, payload: Dict[str, Any]) -> None:
        dampers = payload.get("dampers", [])
        if not isinstance(dampers, list):
            return
        with self.lock:
            for item in dampers:
                if not isinstance(item, dict):
                    continue
                slave_id = item.get("slave_id")
                if not isinstance(slave_id, int) or slave_id not in self.dampers:
                    continue
                target = item.get("target_position")
                status = item.get("status_code")
                self.dampers[slave_id]["target_position"] = target if isinstance(target, int) else None
                self.dampers[slave_id]["status_code"] = status if isinstance(status, int) else None
                self.dampers[slave_id]["last_target_ts"] = item.get("last_target_ts")
                self.dampers[slave_id]["last_status_ts"] = item.get("last_status_ts")

    def snapshot_payload(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "saved_at": now_iso(),
                "dampers": [
                    self._public_damper_locked(slave_id)
                    for slave_id in sorted(self.dampers)
                    if self.dampers[slave_id].get("enabled", True)
                ],
            }

    def maybe_snapshot(self) -> None:
        with self.lock:
            if not self.dirty:
                return
            now_mono = time.monotonic()
            if now_mono - self._last_snapshot_monotonic < self.snapshot_interval_seconds:
                return
            payload = self.snapshot_payload()
        atomic_write_json(self.state_path, payload)
        with self.lock:
            self.dirty = False
            self.last_snapshot_written_at = payload["saved_at"]
            self._last_snapshot_monotonic = time.monotonic()

    def force_snapshot(self) -> None:
        payload = self.snapshot_payload()
        atomic_write_json(self.state_path, payload)
        with self.lock:
            self.dirty = False
            self.last_snapshot_written_at = payload["saved_at"]
            self._last_snapshot_monotonic = time.monotonic()

    def _public_damper_locked(self, slave_id: int) -> Dict[str, Any]:
        item = dict(self.dampers[slave_id])
        return {
            "slave_id": item["slave_id"],
            "room": item["room"],
            "zone": item["zone"],
            "type": item["type"],
            "damper_index": item["damper_index"],
            "label": item["label"],
            "enabled": item["enabled"],
            "notes": item["notes"],
            "target_position": item["target_position"],
            "status_code": item["status_code"],
            "last_target_ts": item["last_target_ts"],
            "last_status_ts": item["last_status_ts"],
            "last_seen_ts": item["last_seen_ts"],
        }

    def public_dampers(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [self._public_damper_locked(slave_id) for slave_id in sorted(self.dampers)]

    def public_damper(self, slave_id: int) -> Optional[Dict[str, Any]]:
        with self.lock:
            if slave_id not in self.dampers:
                return None
            return self._public_damper_locked(slave_id)

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "started_at": self.started_at,
                "last_frame_at": self.last_frame_at,
                "frames_total": self.frames_total,
                "frames_valid_crc": self.frames_valid_crc,
                "recent_frames_buffered": len(self.recent_frames),
                "latest_responses_by_slave": len(self.latest_responses_by_slave),
                "dampers_known": len(self.dampers),
                "dampers_with_target": sum(
                    1 for item in self.dampers.values() if isinstance(item.get("target_position"), int)
                ),
                "dampers_with_status": sum(
                    1 for item in self.dampers.values() if isinstance(item.get("status_code"), int)
                ),
                "dirty": self.dirty,
                "last_snapshot_written_at": self.last_snapshot_written_at,
                "mqtt": {
                    "enabled": self.mqtt_enabled,
                    "connected": self.mqtt_connected,
                    "last_error": self.mqtt_last_error,
                },
                "serial": dict(self.serial_config),
                "state_path": str(self.state_path),
            }

    def latest(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            return None if self.last_frame is None else dict(self.last_frame)

    def latest_responses(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                dict(self.latest_responses_by_slave[slave_id])
                for slave_id in sorted(self.latest_responses_by_slave)
            ]

    def record_frame(self, frame: bytes) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        record = {
            "timestamp_utc": now_iso(),
            **decode_modbus_frame(frame),
        }
        with self.lock:
            self._enrich_record_locked(record)
            self.frames_total += 1
            if record.get("valid_crc"):
                self.frames_valid_crc += 1
            self.last_frame_at = record["timestamp_utc"]
            self.last_frame = record
            self.recent_frames.append(record)
            changed_slave_ids = self._apply_damper_updates_locked(record)

        changed_dampers: List[Dict[str, Any]] = []
        for slave_id in changed_slave_ids:
            damper = self.public_damper(slave_id)
            if damper is not None:
                changed_dampers.append(damper)
        return record, changed_dampers

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

    def _apply_damper_updates_locked(self, record: Dict[str, Any]) -> List[int]:
        slave_id = record.get("slave_id")
        if not record.get("valid_crc") or not isinstance(slave_id, int) or slave_id not in self.dampers:
            return []

        decoded = record.get("decoded")
        if not isinstance(decoded, dict):
            return []

        damper = self.dampers[slave_id]
        damper["last_seen_ts"] = record["timestamp_utc"]
        changed = False

        message_type = decoded.get("message_type")
        if message_type == "write_multiple_registers_request":
            start_address = decoded.get("start_address")
            values = decoded.get("register_values")
            if start_address == 102 and isinstance(values, list) and values:
                value = int(values[0])
                if damper.get("target_position") != value:
                    damper["target_position"] = value
                    damper["last_target_ts"] = record["timestamp_utc"]
                    changed = True
        elif message_type == "write_single_register":
            register_address = decoded.get("register_address")
            register_value = decoded.get("register_value")
            if register_address == 102 and isinstance(register_value, int):
                value = int(register_value)
                if damper.get("target_position") != value:
                    damper["target_position"] = value
                    damper["last_target_ts"] = record["timestamp_utc"]
                    changed = True
        elif message_type == "response":
            register_map = record.get("register_map")
            if isinstance(register_map, list):
                for item in register_map:
                    if not isinstance(item, dict):
                        continue
                    if item.get("address") == 107 and isinstance(item.get("value"), int):
                        value = int(item["value"])
                        if damper.get("status_code") != value:
                            damper["status_code"] = value
                            damper["last_status_ts"] = record["timestamp_utc"]
                            changed = True
                        break

        if changed:
            self.dirty = True
            return [slave_id]
        return []


def build_handler(state: DamperBridgeState):
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
            if parsed.path == "/health":
                self._send_json({"ok": True, **state.stats()})
                return
            if parsed.path == "/stats":
                self._send_json(state.stats())
                return
            if parsed.path == "/latest":
                latest = state.latest()
                if latest is None:
                    self._send_json({"error": "no_frames_yet"}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json(latest)
                return
            if parsed.path == "/devices":
                self._send_json({"devices": state.latest_responses(), "stats": state.stats()})
                return
            if parsed.path == "/dampers":
                self._send_json({"dampers": state.public_dampers(), "stats": state.stats()})
                return
            if parsed.path.startswith("/dampers/"):
                raw_slave_id = parsed.path.rsplit("/", 1)[-1]
                try:
                    slave_id = int(raw_slave_id)
                except ValueError:
                    self._send_json({"error": "invalid_slave_id"}, HTTPStatus.BAD_REQUEST)
                    return
                damper = state.public_damper(slave_id)
                if damper is None:
                    self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json(damper)
                return

            self._send_json(
                {
                    "error": "not_found",
                    "available_paths": [
                        "/health",
                        "/stats",
                        "/latest",
                        "/devices",
                        "/dampers",
                        "/dampers/<slave_id>",
                    ],
                },
                HTTPStatus.NOT_FOUND,
            )

        def log_message(self, _format: str, *args: Any) -> None:
            return

    return Handler


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Soubor {path} musí obsahovat JSON objekt.")
    return data


def load_damper_map(path: Path) -> List[DamperMapEntry]:
    payload = load_json(path)
    dampers = payload.get("dampers")
    if not isinstance(dampers, list):
        raise ValueError(f"Soubor {path} musí obsahovat pole 'dampers'.")

    entries: List[DamperMapEntry] = []
    seen_slave_ids: set[int] = set()
    for item in dampers:
        if not isinstance(item, dict):
            raise ValueError(f"Neplatný záznam klapky v {path}.")
        slave_id = int(item["slave_id"])
        if slave_id in seen_slave_ids:
            raise ValueError(f"Duplicita slave_id {slave_id} v {path}.")
        seen_slave_ids.add(slave_id)
        room = str(item["room"])
        zone = int(item["zone"])
        type_name = str(item["type"])
        damper_index = int(item["damper_index"])
        label = str(item.get("label") or f"{room} {type_name} {damper_index}")
        enabled = bool(item.get("enabled", True))
        notes = item.get("notes")
        entries.append(
            DamperMapEntry(
                slave_id=slave_id,
                room=room,
                zone=zone,
                type=type_name,
                damper_index=damper_index,
                label=label,
                enabled=enabled,
                notes=None if notes is None else str(notes),
            )
        )
    return entries


def load_runtime_config(config_path: Path) -> Tuple[Dict[str, Any], Path]:
    if not config_path.exists():
        example_path = config_path.with_name("pi-zero-config.example.json")
        raise FileNotFoundError(
            f"Konfigurace {config_path} neexistuje. Vytvořte ji podle {example_path}."
        )
    payload = load_json(config_path)
    return deep_merge(DEFAULT_CONFIG, payload), config_path.parent.resolve()


def open_serial_port_from_config(serial_config: Dict[str, Any]):
    try:
        import serial  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Chybí pyserial. Nainstalujte ho přes: pip install -r src/sniffer/requirements.txt"
        ) from exc

    parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD}
    stop_bits_map = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}
    parity = str(serial_config["parity"]).upper()
    stopbits = int(serial_config["stopbits"])

    return serial.Serial(
        port=str(serial_config["port"]),
        baudrate=int(serial_config["baudrate"]),
        bytesize=int(serial_config["bytesize"]),
        parity=parity_map[parity],
        stopbits=stop_bits_map[stopbits],
        timeout=float(serial_config["serial_timeout_seconds"]),
    )


def sniff_serial(
    serial_port: Any,
    state: DamperBridgeState,
    frame_gap_seconds: float,
    raw_logger: RawRecordLogger,
    mqtt_publisher: MqttPublisher,
    stop_event: threading.Event,
) -> None:
    frame_buffer = bytearray()
    last_byte_at = time.monotonic()
    partial_frame_stale_seconds = max(0.1, frame_gap_seconds * 10)

    while not stop_event.is_set():
        chunk = serial_port.read(256)
        now_mono = time.monotonic()

        if chunk:
            frame_buffer.extend(chunk)
            for frame in extract_valid_frames(frame_buffer):
                record, changed_dampers = state.record_frame(frame)
                raw_logger.write(record)
                for damper in changed_dampers:
                    mqtt_publisher.publish_damper(damper)
                state.set_mqtt_status(mqtt_publisher.enabled, mqtt_publisher.connected, mqtt_publisher.last_error)
                state.maybe_snapshot()
            last_byte_at = now_mono
            continue

        if frame_buffer and now_mono - last_byte_at >= frame_gap_seconds:
            for frame in extract_valid_frames(frame_buffer):
                record, changed_dampers = state.record_frame(frame)
                raw_logger.write(record)
                for damper in changed_dampers:
                    mqtt_publisher.publish_damper(damper)
                state.set_mqtt_status(mqtt_publisher.enabled, mqtt_publisher.connected, mqtt_publisher.last_error)
                state.maybe_snapshot()

            if (
                frame_buffer
                and buffer_needs_more_data(bytes(frame_buffer))
                and now_mono - last_byte_at < partial_frame_stale_seconds
            ):
                continue

            if frame_buffer:
                record, changed_dampers = state.record_frame(bytes(frame_buffer))
                raw_logger.write(record)
                for damper in changed_dampers:
                    mqtt_publisher.publish_damper(damper)
                state.set_mqtt_status(mqtt_publisher.enabled, mqtt_publisher.connected, mqtt_publisher.last_error)
                state.maybe_snapshot()
                frame_buffer.clear()

        state.set_mqtt_status(mqtt_publisher.enabled, mqtt_publisher.connected, mqtt_publisher.last_error)
        state.maybe_snapshot()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produkční Pi Zero bridge pro pasivní RS485/Modbus RTU odposlech klapek."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("pi-zero-config.json"),
        help="Cesta k runtime konfiguraci bridge.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        config, config_dir = load_runtime_config(args.config.resolve())
        damper_map_path = resolve_path(config_dir, str(config["damper_map"]["path"]))
        damper_entries = load_damper_map(damper_map_path)
    except Exception as exc:
        print(f"Chyba konfigurace: {exc}", file=sys.stderr)
        return 2

    serial_cfg = config["serial"]
    http_cfg = config["http"]
    mqtt_cfg = config["mqtt"]
    storage_cfg = config["storage"]
    debug_cfg = config["debug"]

    state_path = resolve_path(config_dir, str(storage_cfg["state_path"]))
    raw_log_path = resolve_path(config_dir, str(debug_cfg["raw_log_path"]))

    serial_config = {
        "port": str(serial_cfg["port"]),
        "baudrate": int(serial_cfg["baudrate"]),
        "bytesize": int(serial_cfg["bytesize"]),
        "parity": parity_name(str(serial_cfg["parity"])),
        "stopbits": int(serial_cfg["stopbits"]),
        "frame_gap_ms": float(serial_cfg["frame_gap_ms"]),
        "serial_timeout_seconds": float(serial_cfg["serial_timeout_seconds"]),
        "state_path": str(state_path),
        "damper_map_path": str(damper_map_path),
    }
    if http_cfg.get("enabled", True):
        serial_config["listen_host"] = str(http_cfg["listen_host"])
        serial_config["listen_port"] = int(http_cfg["listen_port"])

    state = DamperBridgeState(
        serial_config=serial_config,
        damper_entries=damper_entries,
        state_path=state_path,
        snapshot_interval_seconds=float(storage_cfg["snapshot_interval_seconds"]),
    )

    if bool(storage_cfg.get("restore_state_on_start", True)) and state_path.exists():
        try:
            state.restore_snapshot(load_json(state_path))
        except Exception as exc:
            print(f"Varování: nepodařilo se načíst snapshot {state_path}: {exc}", file=sys.stderr)

    try:
        mqtt_publisher = MqttPublisher(mqtt_cfg, state.public_dampers)
    except Exception as exc:
        print(f"Chyba MQTT: {exc}", file=sys.stderr)
        return 2

    raw_logger = RawRecordLogger(
        enabled=bool(debug_cfg.get("raw_log_enabled", False)),
        path=raw_log_path,
        rotate_bytes=int(debug_cfg.get("raw_log_rotate_bytes", 5_242_880)),
        keep_files=int(debug_cfg.get("raw_log_keep_files", 5)),
        compress_rotated=bool(debug_cfg.get("raw_log_compress_rotated", True)),
    )

    stop_event = threading.Event()

    def handle_signal(_sig: int, _frame: Any) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        serial_port = open_serial_port_from_config(serial_cfg)
    except Exception as exc:
        print(f"Chyba sériového portu: {exc}", file=sys.stderr)
        return 2

    http_server: Optional[ThreadingHTTPServer] = None
    if bool(http_cfg.get("enabled", True)):
        http_server = ThreadingHTTPServer(
            (str(http_cfg["listen_host"]), int(http_cfg["listen_port"])),
            build_handler(state),
        )
        http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
        http_thread.start()

    mqtt_publisher.connect()
    state.set_mqtt_status(mqtt_publisher.enabled, mqtt_publisher.connected, mqtt_publisher.last_error)

    http_part = ""
    if http_server is not None:
        http_part = f" HTTP API: http://{http_cfg['listen_host']}:{http_cfg['listen_port']}"
    print(
        "Futura damper bridge běží."
        f"{http_part}"
        f" Snapshot: {state_path}"
        f" MQTT: {'on' if mqtt_cfg.get('enabled', False) else 'off'}"
    )

    try:
        sniff_serial(
            serial_port=serial_port,
            state=state,
            frame_gap_seconds=max(0.001, float(serial_cfg["frame_gap_ms"]) / 1000.0),
            raw_logger=raw_logger,
            mqtt_publisher=mqtt_publisher,
            stop_event=stop_event,
        )
    except Exception as exc:
        print(f"Chyba bridge: {exc}", file=sys.stderr)
        return 1
    finally:
        stop_event.set()
        try:
            if bool(storage_cfg.get("write_state_on_shutdown", True)):
                state.force_snapshot()
        except Exception as exc:
            print(f"Varování: nepodařilo se uložit snapshot: {exc}", file=sys.stderr)
        if http_server is not None:
            http_server.shutdown()
            http_server.server_close()
        mqtt_publisher.close()
        raw_logger.close()
        serial_port.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
