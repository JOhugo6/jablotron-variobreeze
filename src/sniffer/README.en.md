[Česky](README.md) | **English**

# RS485 Sniffer

This folder is intended for passive sniffing of Futura's internal communication over `RS485`.

At the protocol level, the captured data is decoded as `Modbus RTU`, but this folder is not for direct `Modbus TCP` reading. That belongs in [../modbus](../modbus/README.en.md).

## What is Production and What is Diagnostic

### `futura_damper_bridge.py`

Production bridge for `Pi Zero` for regular operation.

It does:

- passive `RS485` sniffing
- `Modbus RTU` frame decoding
- deriving damper state from:
  - `FC16 / register 102` as a target_position candidate
  - `FC4 / register 107` as a status_code
- maintaining a state cache in `RAM`
- writing a small snapshot to `state/dampers_state.json`
- local HTTP API:
  - `/health`
  - `/stats`
  - `/latest`
  - `/devices`
  - `/dampers`
  - `/dampers/<slave_id>`
- optional publishing to `MQTT`

Typical usage in the repository:

```bash
cp src/sniffer/pi-zero-config.example.json src/sniffer/pi-zero-config.json
cp src/sniffer/damper-map.example.json src/sniffer/damper-map.json
python src/sniffer/futura_damper_bridge.py --config src/sniffer/pi-zero-config.json
```

On `Pi Zero`, the same bridge can also be run as a flat deployment in `~/futura`, i.e., without the `src/` subdirectories. In that case, the following files should be placed side by side in `~/futura`:

- `futura_damper_bridge.py`
- `rs485_modbus_monitor.py`
- `pi-zero-config.json`
- `damper-map.json`
- `requirements.txt`

The startup then looks like this:

```bash
cd ~/futura
python futura_damper_bridge.py --config pi-zero-config.json
```

### `rs485_modbus_monitor.py`

Diagnostic monitor for reverse analysis and debugging.

It is useful when you need to:

- watch raw frames
- analyze request/response pairs
- debug `CRC`
- find new registers or unknown slave_id values

Typical usage:

```bash
python src/sniffer/rs485_modbus_monitor.py --serial-port /dev/serial0 --baudrate 19200 --parity N --stopbits 1
```

## Additional Scripts

### `analyze_rs485_log.py`

Summary and analysis of logs created by the diagnostic monitor.

### `extract_rs485_window.py`

Extract register changes within a specific time window.

### `extract_rs485_raw_window.py`

Raw extract of valid frames from a selected time window.

## Dependencies

Python dependencies for this part are in:

- [requirements.txt](requirements.txt)

Installation:

```bash
pip install -r src/sniffer/requirements.txt
```

On `Pi Zero` in a flat deployment, the equivalent is:

```bash
cd ~/futura
pip install -r requirements.txt
```

## Configuration

The sniffer part has two example files:

- [pi-zero-config.example.json](pi-zero-config.example.json)
- [damper-map.example.json](damper-map.example.json)

Detailed explanation of both files is in:

- [../../docs/pi-zero-konfigurace.en.md](../../docs/pi-zero-konfigurace.en.md)

Including an explanation of how to identify the correct `serial.port` and when to use `/dev/serial0`.

In the repository for local development, create a copy:

- `src/sniffer/pi-zero-config.json`
- `src/sniffer/damper-map.json`

These local configurations are in `.gitignore`.

On `Pi Zero` in a flat deployment, the corresponding files are:

- `~/futura/pi-zero-config.json`
- `~/futura/damper-map.json`

### `pi-zero-config.json`

Contains runtime settings for the bridge:

- `serial`
- `http`
- `mqtt`
- `storage`
- `debug`
- `damper_map`

### `damper-map.json`

Contains the damper map for a specific installation:

- `slave_id`
- `room`
- `zone`
- `type`
- `damper_index`
- `label`
- `enabled`

For the current known topology of this house, refer to [../../docs/mapa-klapek.en.md](../../docs/mapa-klapek.en.md).

## Recommended Operating Mode on Pi Zero

For regular operation:

- use `futura_damper_bridge.py`
- keep `raw_log_enabled` disabled
- keep state in `RAM` and snapshot only periodically
- enable `MQTT` only when you have the broker and topics ready
- dampers with `enabled: false` in `damper-map.json` are not published to MQTT and no entities are created for them in HA. If you disable a damper after the fact, existing entities in HA need to be deleted manually

For debugging and reverse analysis:

- use `rs485_modbus_monitor.py`
- enable it only when you need to find new registers or check raw traffic

## How to Verify the Process is Running on Zero

### When the bridge is started manually

Process verification:

```bash
pgrep -af "futura_damper_bridge.py"
```

Verify that it is listening on the HTTP API:

```bash
ss -ltnp | grep 8765
```

Verify the health endpoint:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

### When the bridge is running as a `systemd` service

Service status:

```bash
sudo systemctl status futura-damper-bridge
```

Live logs:

```bash
sudo journalctl -u futura-damper-bridge -f
```

### When the diagnostic monitor is running

Process verification:

```bash
pgrep -af "rs485_modbus_monitor.py"
```

Service status:

```bash
sudo systemctl status rs485-modbus-monitor
```

Live logs:

```bash
sudo journalctl -u rs485-modbus-monitor -f
```

API verification:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/stats
```

## Folder Separation Rule

- `src/sniffer` = passive `RS485` sniffing and analysis of internal `Modbus RTU` communication
- `src/modbus` = direct `Modbus TCP` tools
