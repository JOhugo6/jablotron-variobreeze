[Česky](README.md) | **English**

# Modbus TCP

This folder is dedicated exclusively to direct work with `Modbus TCP`.

It is not intended for `RS485` sniffing or for analysis of internal `Modbus RTU` communication.

## Purpose

The Modbus TCP part of the project is intended for:

- direct reading of registers from Futura over the network
- working with the publicly available `Modbus TCP` map
- discovery search for position register candidates
- continuous monitoring of register changes over time
- verifying hypothetical registers without passive sniffing

## Scripts

### `futura_variobreeze.py`

CLI tool for reading data from Futura via `Modbus TCP`.

Features:

- read connected supply and exhaust dampers (registers 70-73)
- read configured position registers with optional scale divisor
- run discovery mode over a selected register range
- continuously monitor register changes and output only differences
- output in text or JSON format
- optionally unlock service registers via access code
- work with a configurable `config.json`

### Operating Modes

The script has three main modes:

#### 1. Damper Status Reading

Default mode. Reads connected dampers and their positions from configured registers.

One-time reading:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once
```

Continuous reading with default interval (5 seconds, configurable in `config.json`):

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json
```

JSON output:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once --json
```

#### 2. Discovery Mode

Scans a selected register range and looks for candidates whose values change within the 0-100 range. Used for finding unknown damper position registers.

Recommended procedure:

1. Start discovery over an appropriate range.
2. During measurement, change the state of zones or dampers in the Futura application.
3. Watch for registers that change.

Example:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --discover \
  --discover-type input \
  --discover-start 900 \
  --discover-count 400 \
  --discover-samples 10 \
  --discover-interval 1
```

Discovery parameters:

| Parameter | Default | Description |
|---|---|---|
| `--discover-type` | `input` | Register type: `input` or `holding` |
| `--discover-start` | `0` | Start address |
| `--discover-count` | `500` | Number of registers to scan |
| `--discover-samples` | `5` | How many times to read the entire range |
| `--discover-interval` | `1.0` | Interval between samples in seconds |
| `--discover-probe-count` | `2` | How many registers to read in a single request (useful for sparse maps where not all addresses respond) |
| `--discover-min` | `0` | Minimum candidate value (negative number = no filter) |
| `--discover-max` | `100` | Maximum candidate value (negative number = no filter) |

Output is always JSON with a list of candidate registers sorted by the number of distinct values.

If you need to unlock service registers:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --access-code 12345 \
  --discover \
  --discover-start 900 \
  --discover-count 800
```

#### 3. Change Monitor

Continuously reads a selected register range and outputs only those that have changed since the last reading. Useful for observing register reactions to changes in the Futura application.

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --monitor \
  --monitor-type input \
  --monitor-start 0 \
  --monitor-count 100 \
  --monitor-interval 5
```

Monitor parameters:

| Parameter | Default | Description |
|---|---|---|
| `--monitor-type` | `input` | Register type: `input` or `holding` |
| `--monitor-start` | `0` | Start address |
| `--monitor-count` | `100` | Number of registers to monitor |
| `--monitor-interval` | `5.0` | Interval between readings in seconds |
| `--monitor-probe-count` | `2` | How many registers to read in a single request |
| `--monitor-cycles` | `0` | Number of cycles, `0` = runs until interrupted (`Ctrl+C`) |

If you need to unlock service registers before monitoring:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --access-code 12345 \
  --monitor \
  --monitor-start 900 \
  --monitor-count 200
```

The access code is automatically resent before each reading cycle in monitor mode.

### Common Parameters

| Parameter | Description |
|---|---|
| `--config` | Path to the configuration JSON file. Default: `config.example.json` next to the script |
| `--once` | Read once and exit (reading mode only) |
| `--json` | Force JSON output (reading mode only) |
| `--access-code` | Access code for unlocking service registers. Overrides the value from configuration |

## Dependencies

Python dependencies for this part are in:

- [requirements.txt](requirements.txt)

Installation:

```bash
pip install -r src/modbus/requirements.txt
```

## Configuration

Before the first run, copy the example configuration:

```bash
copy src\modbus\config.example.json src\modbus\config.json
```

On Linux or Mac:

```bash
cp src/modbus/config.example.json src/modbus/config.json
```

Then edit `src/modbus/config.json` according to your installation.

### Configuration Description

Example file: [config.example.json](config.example.json)

#### `modbus`

| Field | Default | Description |
|---|---|---|
| `host` | `192.168.1.50` | IP address of Futura |
| `port` | `502` | Modbus TCP port |
| `device_id` | `1` | Modbus device ID |
| `timeout_seconds` | `3.0` | Connection timeout in seconds |

#### `service`

| Field | Default | Description |
|---|---|---|
| `access_code` | `null` | Access code for service registers. `null` = do not use |
| `access_code_register` | `900` | Register where the access code is written |

#### `registers`

| Field | Default | Description |
|---|---|---|
| `connected_supply_start` | `70` | Start register of the connected supply damper bitmask (reads 2 registers as uint32) |
| `connected_exhaust_start` | `72` | Start register of the connected exhaust damper bitmask (reads 2 registers as uint32) |
| `connected_word_order` | `low_high` | Word order in uint32: `low_high` or `high_low` |
| `position_source` | `input` | Register type for reading positions: `input` or `holding` |
| `position_scale_divisor` | `1.0` | Divisor for the raw position value. If Futura returns 0-1000 instead of 0-100, set to `10` |
| `supply_position_registers` | `{}` | Mapping of damper number to position register address (supply) |
| `exhaust_position_registers` | `{}` | Mapping of damper number to position register address (exhaust) |

Example position register mapping:

```json
"supply_position_registers": {
  "1": 1000,
  "2": 1001
}
```

This means: supply damper #1 is in register `1000`, damper #2 in register `1001`.

The mapping can also be specified as an array:

```json
"supply_position_registers": [1000, 1001]
```

In that case, dampers are numbered automatically starting from 1.

#### `poll`

| Field | Default | Description |
|---|---|---|
| `interval_seconds` | `5.0` | Continuous reading interval in seconds (without `--once`) |

#### `output`

| Field | Default | Description |
|---|---|---|
| `format` | `text` | Default output format: `text` or `json`. Can be overridden with the `--json` flag |

### Configuration Notes

- The configuration is merged over default values. You do not need to fill in all fields, only those that differ from the defaults.
- `config.json` is in `.gitignore`. Only `config.example.json` is committed to the repository.
- Futura supports only one concurrent Modbus TCP connection. If another client is connected, the script will receive a `ConnectionResetError`.

## Folder Separation Note

The practical rule is:

- `src/modbus` = direct `Modbus TCP` tools
- `src/sniffer` = passive `RS485` sniffing and analysis of captured internal `Modbus RTU` communication
