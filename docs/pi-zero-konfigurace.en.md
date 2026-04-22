[Česky](pi-zero-konfigurace.md) | **English**

# Pi Zero Configuration

This document describes the files:

- `~/futura/pi-zero-config.json`
- `~/futura/damper-map.json`

It is written so that a person without extensive Linux experience can configure the bridge on `Pi Zero` for dampers.

## What Is What

Two files are used:

1. `pi-zero-config.json`
   The program's control settings. Determines which serial port to read from, whether to enable the HTTP API, whether to use MQTT, where to save state, and whether to create a debug log.
2. `damper-map.json`
   Description of the specific installation. Specifies which `slave_id` belongs to which room and what kind of dampers are involved.

Without `damper-map.json`, the bridge does not know that, for example, `slave_id 66` is `Pracovna / supply / zone 3 / damper 1`.

## Where the Default Files Come From

The repository contains templates:

- [../src/sniffer/pi-zero-config.example.json](../src/sniffer/pi-zero-config.example.json)
- [../src/sniffer/damper-map.example.json](../src/sniffer/damper-map.example.json)

On `Pi Zero`, production files are created from them:

```bash
cd ~/futura
cp pi-zero-config.example.json pi-zero-config.json
cp damper-map.example.json damper-map.json
```

If you already have these files in `~/futura`, do not copy over the existing versions without a backup.

## How to Edit the Files

The easiest way is to use the `nano` editor:

```bash
nano ~/futura/pi-zero-config.json
```

Saving in `nano`:

- `Ctrl+O`
- `Enter`
- `Ctrl+X`

The same for the damper map:

```bash
nano ~/futura/damper-map.json
```

## Important Note About JSON

A `json` file:

- must not contain comments,
- must not have a trailing comma after the last item,
- `true`, `false`, and `null` must be lowercase.

Quick check whether the `JSON` is syntactically correct:

```bash
python -m json.tool ~/futura/pi-zero-config.json > /dev/null && echo OK
python -m json.tool ~/futura/damper-map.json > /dev/null && echo OK
```

If the file is broken, `python -m json.tool` will print an error and will not return `OK`.

## Minimum Safe Settings for First Start

For the first run, I recommend:

- `mqtt.enabled` leave at `false`
- `http.enabled` leave at `true`
- `http.listen_host` leave at `127.0.0.1`
- `debug.raw_log_enabled` leave at `false`
- `storage.snapshot_interval_seconds` leave at `60`

This is the safest start:

- bridge will run only locally on `Pi`,
- will not send anything to `MQTT`,
- will not unnecessarily write a large debug log,
- and can be verified via local `curl`.

## Detailed Description of `pi-zero-config.json`

The default content looks like this:

```json
{
  "serial": {
    "port": "/dev/serial0",
    "baudrate": 19200,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "serial_timeout_seconds": 0.001,
    "frame_gap_ms": 3.0
  },
  "http": {
    "enabled": true,
    "listen_host": "127.0.0.1",
    "listen_port": 8765
  },
  "mqtt": {
    "enabled": false,
    "host": "127.0.0.1",
    "port": 1883,
    "username": null,
    "password": null,
    "client_id": "futura-zero",
    "topic_prefix": "futura",
    "discovery_prefix": "homeassistant",
    "retain": true,
    "qos": 1,
    "publish_on_change_only": true
  },
  "storage": {
    "state_path": "state/dampers_state.json",
    "snapshot_interval_seconds": 60,
    "restore_state_on_start": true,
    "write_state_on_shutdown": true
  },
  "debug": {
    "raw_log_enabled": false,
    "raw_log_path": "debug/raw.jsonl",
    "raw_log_rotate_bytes": 5242880,
    "raw_log_keep_files": 5,
    "raw_log_compress_rotated": true
  },
  "damper_map": {
    "path": "damper-map.json"
  }
}
```

### Section `serial`

This is where the `RS485` serial line is configured.

#### `port`

Typical value:

```json
"/dev/serial0"
```

What it does:

- determines which UART port the bridge should open

What I recommend:

- on `Raspberry Pi Zero 2 W` leave `/dev/serial0`

When to change:

- only if you know that your UART is exposed elsewhere

#### How to Check if `/dev/serial0` Is Correct

For the recommended wiring in this project:

- if the `RS485` converter is connected to pins `GPIO14/GPIO15` on `Pi Zero`,
- and you have properly enabled UART,
- use almost always `/dev/serial0`

`/dev/serial0` is the recommended stable alias for the primary serial port on Raspberry Pi.

After reboot, check:

```bash
ls -l /dev/serial0
```

When everything is fine, you will see that `serial0` points to an actual device, typically:

- `/dev/ttyAMA0`
- or `/dev/ttyS0`

For detail, you can display both options:

```bash
ls -l /dev/ttyAMA0 /dev/ttyS0 2>/dev/null
```

Quick practical procedure:

1. if `/dev/serial0` exists, use in the configuration:

```json
"/dev/serial0"
```

2. if `/dev/serial0` does not exist, first fix the UART settings according to [pi-zero-2w-rs485-sniffer.en.md](pi-zero-2w-rs485-sniffer.en.md)
3. only if you are deliberately not using GPIO UART but a different adapter, change `port`

#### When to Change `port`

Change `port` only in these cases:

- you are not using GPIO UART on `Pi`, but a `USB-RS485` converter
- you know that your installation intentionally uses a different serial device

Typical alternatives:

- `/dev/ttyUSB0`
- `/dev/ttyUSB1`
- `/dev/ttyACM0`

When using a `USB-RS485` adapter, find its name like this:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

In that case, set the found device in the configuration, for example:

```json
"/dev/ttyUSB0"
```

#### What to Do if `/dev/serial0` Is Missing

First verify that UART is enabled:

```bash
grep -E "enable_uart=1|dtoverlay=disable-bt" /boot/firmware/config.txt
```

And that login shell is not running on the serial line:

```bash
sudo raspi-config
```

In `raspi-config`, it should be:

1. `Interface Options` -> `Serial Port`
2. `Login shell over serial?` -> `No`
3. `Enable serial hardware?` -> `Yes`

Then perform a restart:

```bash
sudo reboot
```

#### `baudrate`

Typical value:

```json
19200
```

What it does:

- determines the communication speed on the bus

What I recommend:

- leave `19200` unless you have already verified a different value during sniffing

#### `bytesize`

Typical value:

```json
8
```

What it does:

- number of data bits

What I recommend:

- leave `8`

#### `parity`

Typical value:

```json
"N"
```

Possible values:

- `"N"` = no parity
- `"E"` = even parity
- `"O"` = odd parity

What I recommend:

- leave `"N"` if `19200 8N1` has already been verified

#### `stopbits`

Typical value:

```json
1
```

What it does:

- number of stop bits for serial communication

What I recommend:

- leave `1`

#### `serial_timeout_seconds`

Typical value:

```json
0.001
```

What it does:

- how long a single read waits for bytes from the serial line

What I recommend:

- leave `0.001`

When to change:

- almost never

#### `frame_gap_ms`

Typical value:

```json
3.0
```

What it does:

- helps determine when one `Modbus RTU` frame ends and the next begins

What I recommend:

- leave `3.0`

When to change:

- only when doing deeper parser debugging

### Section `http`

This is where the bridge's local HTTP API is configured.

#### `enabled`

Typical value:

```json
true
```

What it does:

- enables or disables HTTP endpoints like `/health` and `/dampers`

What I recommend:

- leave `true`

#### `listen_host`

Typical value:

```json
"127.0.0.1"
```

What it does:

- determines from where the API can be accessed

Options:

- `"127.0.0.1"` = only from the same `Pi`
- `"0.0.0.0"` = from the entire local network

Safe first start:

- leave `"127.0.0.1"`

When to change to `"0.0.0.0"`:

- when you want to open the API from another computer on the network

#### `listen_port`

Typical value:

```json
8765
```

What it does:

- HTTP API port

What I recommend:

- leave `8765`

### Section `mqtt`

This is where the optional `MQTT` publishing is configured.

#### `enabled`

Typical value:

```json
false
```

What it does:

- enables or disables `MQTT`

What I recommend:

- for the first start, leave `false`
- enable only when you have a confirmed running broker

#### `host`

Typical value:

```json
"127.0.0.1"
```

What it does:

- address of the `MQTT` broker

Examples:

- `"127.0.0.1"` if the broker runs on the same machine
- `"192.168.1.10"` when the broker runs on another machine in the LAN

#### `port`

Typical value:

```json
1883
```

What it does:

- `MQTT` broker port

#### `username`

Typical value:

```json
null
```

What it does:

- username for `MQTT`

When to use:

- only when the broker requires authentication

#### `password`

Typical value:

```json
null
```

What it does:

- password for `MQTT`

#### `client_id`

Typical value:

```json
"futura-zero"
```

What it does:

- client identifier in `MQTT`

What I recommend:

- leave as is, or change to the name of the specific device

#### `topic_prefix`

Typical value:

```json
"futura"
```

What it does:

- prefix for all `MQTT` topics

Example:

- damper `66` will then be published under a topic like `futura/damper/66/state`

#### `discovery_prefix`

Typical value:

```json
"homeassistant"
```

What it does:

- prefix for MQTT Discovery topics, through which the bridge automatically creates entities in Home Assistant
- the bridge publishes discovery config on topics like `homeassistant/sensor/futura_damper_66_target_position/config`

When to change:

- only if you have changed the discovery prefix in the MQTT integration settings in Home Assistant
- the default value `homeassistant` matches the default Home Assistant setting

#### `retain`

Typical value:

```json
true
```

What it does:

- tells the broker to remember the last known state

What I recommend:

- leave `true`

#### `qos`

Typical value:

```json
1
```

What it does:

- `MQTT` message acknowledgment level

What I recommend:

- leave `1`

#### `publish_on_change_only`

Typical value:

```json
true
```

What it does:

- publishes only on state change, not on every repetition of the same value

What I recommend:

- leave `true`

### Section `storage`

This is where the local storage of a small state snapshot is configured.

#### `state_path`

Typical value:

```json
"state/dampers_state.json"
```

What it does:

- path to the small state file

Important:

- the relative path is always relative to the location of `pi-zero-config.json`

What I recommend:

- leave `state/dampers_state.json`

#### `snapshot_interval_seconds`

Typical value:

```json
60
```

What it does:

- how often the snapshot may be rewritten to disk when the state has changed

What I recommend:

- leave `60`

Why:

- it is gentler on the `SD` card

#### `restore_state_on_start`

Typical value:

```json
true
```

What it does:

- after starting, the bridge tries to load the last snapshot

What I recommend:

- leave `true`

#### `write_state_on_shutdown`

Typical value:

```json
true
```

What it does:

- on clean process termination, saves the last state

What I recommend:

- leave `true`

### Section `debug`

This is where the debug raw log is configured.

#### `raw_log_enabled`

Typical value:

```json
false
```

What it does:

- enables or disables the raw diagnostic frame log

What I recommend:

- in normal operation, leave `false`

When to enable:

- only during debugging or reverse analysis

#### `raw_log_path`

Typical value:

```json
"debug/raw.jsonl"
```

What it does:

- path to the debug log

#### `raw_log_rotate_bytes`

Typical value:

```json
5242880
```

What it does:

- size of a single log file in bytes

`5242880` is approximately `5 MB`.

#### `raw_log_keep_files`

Typical value:

```json
5
```

What it does:

- how many of the last rotated logs to keep

#### `raw_log_compress_rotated`

Typical value:

```json
true
```

What it does:

- old rotated logs are compressed to `gzip` after rotation

What I recommend:

- leave `true`

### Section `damper_map`

#### `path`

Typical value:

```json
"damper-map.json"
```

What it does:

- path to the damper map file

What I recommend:

- in `~/futura` leave `damper-map.json`

## Detailed Description of `damper-map.json`

Each item in the `dampers` array describes one damper.

Example:

```json
{
  "slave_id": 66,
  "room": "Pracovna",
  "label": "Pracovna privod 1",
  "enabled": true,
  "notes": null
}
```

### `slave_id`

- damper number on `RS485 / Modbus RTU`
- must match the actually mapped dampers
- for regular VarioBreeze dampers this is the primary addressing key
- if `zone`, `type`, or `damper_index` are missing, the bridge derives them from `slave_id`

For a regular damper:

```text
offset = slave_id - 64
zone = (offset & 0b111) + 1
damper_index = ((offset >> 3) & 0b11) + 1
type = "odtah" if (offset & 0b100000) else "privod"
```

This derivation only applies to regular VarioBreeze dampers, not `ALFA` or other `RS485` nodes with a different address range.

### `room`

- human-readable room name
- will be returned in the API and optionally in `MQTT`

### `zone`

- zone number in the Futura
- optional for regular dampers
- if present, it must match the value derived from `slave_id`

### `type`

Allowed values:

- `"privod"`
- `"odtah"`
- optional for regular dampers
- if present, it must match the value derived from `slave_id`

### `damper_index`

- damper order within a given room or zone
- optional for regular dampers
- if present, it must match the value derived from `slave_id`

### `label`

- human-readable damper name
- if missing, the bridge builds it from `room`, the derived `type`, and the derived `damper_index`

### `enabled`

- `true` = the damper is active, the bridge monitors it, publishes to MQTT, and creates entities for it in Home Assistant
- `false` = the record is in the map, but the bridge does not publish it to MQTT and does not create discovery entities for it in Home Assistant

This is useful when you want to keep the damper noted in the map but temporarily not publish it.

Important: if you switch a damper from `true` to `false`, the bridge will stop sending new data and will not create discovery for it on the next connection. But entities that already exist in Home Assistant will not be automatically deleted. If you want to remove them, you must delete them manually in HA in `Settings` -> `Devices & Services` -> `MQTT` -> device `Futura VarioBreeze`.

### `notes`

- optional note
- can be text or `null`

## What an Installer Typically Changes

In most installations, you will only need to change:

1. `mqtt.enabled`
2. `mqtt.host`
3. optionally `mqtt.username` and `mqtt.password`
4. `http.listen_host`, if the API should be visible from LAN
5. contents of `damper-map.json`, if it is a different installation

On the other hand, do not change without reason:

- `serial_timeout_seconds`
- `frame_gap_ms`
- `snapshot_interval_seconds`
- `raw_log_rotate_bytes`
- `raw_log_keep_files`

## Recommended Procedure for a Person Without Linux Experience

1. Copy the templates:

```bash
cd ~/futura
cp pi-zero-config.example.json pi-zero-config.json
cp damper-map.example.json damper-map.json
```

2. Open the configuration:

```bash
nano ~/futura/pi-zero-config.json
```

3. For the first start, check only:

- `serial.port` is `/dev/serial0`
- `http.enabled` is `true`
- `http.listen_host` is `127.0.0.1`
- `mqtt.enabled` is `false`

4. Open the damper map:

```bash
nano ~/futura/damper-map.json
```

5. Check that `slave_id` values match the actual installation.

6. Verify syntax:

```bash
python -m json.tool ~/futura/pi-zero-config.json > /dev/null && echo OK
python -m json.tool ~/futura/damper-map.json > /dev/null && echo OK
```

7. Start the bridge:

```bash
cd ~/futura
source .venv/bin/activate
python futura_damper_bridge.py --config pi-zero-config.json
```

8. In a second terminal, check:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

## Most Common Errors

### Bridge Reports a Configuration Error

Most often:

- comma error in `JSON`
- typo in `true/false/null`
- wrong path in `damper_map.path`

### API Does Not Respond

Most often:

- bridge is not running
- `http.enabled` is `false`
- port `8765` is used by another process

### MQTT Does Not Work

Most often:

- `mqtt.enabled` is still `false`
- wrong broker IP address
- broker requires login and `username` and `password` are not filled in

### No Damper Data Appears

Most often:

- wrong UART settings on `Pi`
- incorrectly wired `A/B`
- bridge is running, but `damper-map.json` is missing the correct `slave_id`

## Related Documents

- [Pi Zero 2 W RS485 Sniffer Deployment Plan](pi-zero-2w-rs485-sniffer.en.md)
- [Architecture Design for Pi Zero](navrh-architektury-pi-zero.en.md)
- [Damper Map and Bus Reverse Analysis](mapa-klapek.md)
