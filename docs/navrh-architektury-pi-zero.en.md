[Česky](navrh-architektury-pi-zero.md) | **English**

# Architecture Design for Pi Zero RS485 Sniffer

## Purpose of This Document

This document describes the recommended solution for `Raspberry Pi Zero 2 W`, which:

- passively sniffs the internal `RS485 / Modbus RTU` communication of the Futura,
- derives damper states from it,
- minimizes writes to the `SD` card,
- and prepares a clean foundation for further integration into `Home Assistant`.

The document is intentionally focused only on `Pi Zero`.

This document belongs to the `RS485` sniffing part of the project, not to the `Modbus TCP` tool in `src/modbus`.

`ALFA` is not covered here, because its values can already be read by `Home Assistant` via a different path through `Modbus`.

## Current Implementation in the Repo

The current production base for `Pi Zero` is:

- [../src/sniffer/futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

It already supports:

- passive `RS485` sniffing,
- decoding `Modbus RTU` frames,
- keeping damper state in RAM,
- saving a small state snapshot,
- exposing a lightweight HTTP API,
- and optionally publishing state to `MQTT`.

The diagnostic monitor for reverse engineering remains separate as:

- [../src/sniffer/rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)

## Main Requirements

On `Pi Zero` we want:

- passive sniffing without transmitting to the bus,
- minimal number of writes to the `SD` card,
- robust operation after restart,
- ability to hold the last known damper state,
- ability for short-term diagnostic logging,
- simple operation as a `systemd` service.

On `Pi Zero` we do not want:

- an endless `jsonl` raw log as the primary storage,
- a database full of all raw frames,
- high write load on `SD`,
- long-term history, which `Home Assistant` should hold anyway.

## What We Already Know About the Data

From passive sniffing so far:

- `FC16 / register 102` is the strongest candidate for the target or calculated damper position,
- `FC4 / register 107` is a status code or damper reaction confirmation,
- `register 102` does not behave as a periodically read state,
- `register 102` is written event-driven, when the Futura recalculates the damper position,
- `register 107` is read periodically and is suitable as an auxiliary operational signal.

This leads to a fundamental consequence:

- the current damper state cannot be obtained by simply periodically querying the "last raw frame",
- `Pi Zero` must hold the derived damper state statefully,
- and the last known value of `register 102` needs to be persisted outside of RAM.

## Recommended Architecture

The best design for `Pi Zero` is:

```text
serial sniffer
  ->
Modbus RTU parser
  ->
state engine
  ->
in-memory cache
  ->
MQTT publisher

plus:
  - small local state snapshot
  - optional short debug log
```

In other words:

- process raw frames immediately upon receipt,
- do not store everything as the primary source of truth,
- continuously maintain a small derived state for all dampers,
- and write only a minimum to disk.

## Configuration File

Yes, `Pi Zero` should have a configuration file.

Without one, the solution would be unnecessarily tied to one specific house, one port, one broker, and one damper map.

Configuration is needed at least for:

- a different serial port,
- a different `baudrate`,
- a different `MQTT` broker,
- a different state file location,
- a different debug log mode,
- and most importantly a different damper map in a different building.

### Recommended Separation

I do not recommend having everything in one large file.

It is better to split the configuration into:

1. application runtime configuration,
2. a separate damper map.

### 1. Runtime Configuration

The runtime configuration should describe the Zero operating environment.

Typically:

- serial port,
- HTTP API,
- `MQTT`,
- snapshot persistence,
- debug log,
- paths to data files,
- reference to the damper map file.

Recommended name:

- `pi-zero-config.json`

### 2. Damper Map

The damper map should describe the specific installation.

Typically:

- `slave_id`
- room
- optionally a note or alias

For regular VarioBreeze dampers, `zone`, `type`, and `damper_index` can be derived from `slave_id`. If they are included explicitly in the map, they are mainly useful as readable redundancy and a validation guard.

Recommended name:

- `damper-map.json`

This gives us an important separation:

- when transferring to a different environment, it is often enough to change `pi-zero-config.json`,
- when the damper topology or house is different, it is enough to swap `damper-map.json`,
- the code stays the same.

### Why Not Use the Existing `config.example.json`

The repo already contains [config.example.json](../src/modbus/config.example.json), but it belongs to the older tool [futura_variobreeze.py](../src/modbus/futura_variobreeze.py) for `Modbus TCP`.

For `Pi Zero` sniffing and bridge logic, it is appropriate to use a different, separate configuration model and a different file name.

Otherwise, two different applications and two different operating modes would be mixed together.

## Component Breakdown

### 1. Serial Sniffer

The first component should handle only the lowest sniffing layer.

Its role is:

- open `serial0`,
- read bytes from the serial line,
- pass them along in a timely manner,
- and by itself not perform any application-level interpretation.

This means:

- `sniffer` = physical and byte-stream layer
- `Modbus RTU parser` = a higher protocol layer

In the implementation, both can be in a single process, but architecturally it is better to keep them separate.

In the current implementation, this is an internal part of:

- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

Sniffer responsibilities:

- read the serial line,
- pass raw bytes to the parser,
- monitor only low-level read conditions.

### 2. Modbus RTU Parser

In the current implementation, this role is fulfilled by:

- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

The diagnostic variant for detailed analysis remains:

- [rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)

Parser responsibilities:

- assemble valid frames,
- validate `CRC`,
- decode `FC3/4/6/16`,
- add `correlated_request`,
- build `register_map`,
- pass them to the internal state engine,
- optionally publish lightweight local API endpoints like `/health` and `/dampers`.

### 3. State Engine

The state engine is the main logic on `Pi Zero`.

Its tasks:

- map `slave_id` to a specific damper,
- update the target position from `FC16 / 102`,
- update the status code from `FC4 / 107`,
- hold the last known state in memory,
- publish changes to `MQTT`,
- and in a controlled manner save a small snapshot to disk.

### 4. MQTT Publisher

The MQTT publisher should send already derived state, not raw frames.

Publishing should occur:

- only on value change,
- with `retained` messages,
- with a small number of topics,
- without high-frequency unnecessary republishing.

### 5. Snapshot Writer

The snapshot writer should write only a small state file.

It should not write:

- every raw frame,
- every periodic response,
- nor all transient internal calculations.

Its only task is:

- save the last known state of all dampers,
- so that after a Zero restart, the damper positions are not lost.

### 6. Optional Debug Logger

The debug logger should be separate from normal operation.

In normal mode:

- it can be completely disabled,
- or it can write only a short rotating log.

The debug logger must not be the main data path of the system.

## Recommended In-Memory Data Model

For each damper, hold a structure like:

```json
{
  "slave_id": 66,
  "room": "Pracovna",
  "zone": 3,
  "type": "privod",
  "target_position": 56,
  "status_code": 1,
  "last_target_ts": "2026-03-26T09:17:02+00:00",
  "last_status_ts": "2026-03-26T13:18:13+00:00",
  "online": true
}
```

Required fields:

- `slave_id`
- `room`
- `zone`
- `type`
- `target_position`
- `status_code`
- `last_target_ts`
- `last_status_ts`

Optional fields:

- `online`
- `last_seen_ts`
- `source`
- `confidence`

## What to Store on Disk

### Primary Recommendation

Store on disk only:

- `state/dampers_state.json`

This should be a small snapshot of the last known state of all dampers.

Typically:

- tens to hundreds of lines,
- a few kilobytes,
- overwritten only occasionally.

### What Not to Store as Primary Storage

I do not recommend as primary storage:

- a single endless `logs/rs485_frames.jsonl`,
- SQLite with all raw frames,
- time series of all periodic readings,
- a detailed audit of every response from every damper.

Reason:

- it unnecessarily wears out the `SD`,
- data volume grows quickly,
- and it is not needed for the main purpose.

## How to Limit Writes to SD

### Rule 1: Write Only on Change

Do not write to disk or send to `MQTT` anything if the state has not changed.

This means:

- when `FC4 / 107 = 1` arrives repeatedly, do not write anything,
- when the same `FC16 / 102` appears again, do not write anything,
- only update the in-memory `last_seen_ts` if needed for health.

### Rule 2: Do Not Write Snapshot After Every Change

Do not write the snapshot to disk after every individual damper change.

Recommended approach:

- mark the state as `dirty`,
- write the snapshot at most once every `30-60 s`,
- and always on clean process shutdown.

This dramatically reduces the write load.

### Rule 3: Use Atomic File Rewrite

Save the snapshot atomically:

1. write to a temporary file,
2. perform `fsync`,
3. rename to the target file.

This minimizes the risk of corrupting the snapshot during a power failure.

### Rule 4: Keep Raw Log Only as Temporary Debug

Raw log:

- keep disabled by default,
- or keep only the last few megabytes,
- ideally with rotation,
- and optionally in `tmpfs` for a short debugging session.

## MQTT as the Main External Persistence

From the perspective of `SD` longevity, it is best if `Pi Zero` is not the main long-term storage.

Therefore the recommended model is:

- `Pi Zero` holds current state in RAM,
- on change, publishes to `MQTT`,
- `MQTT broker` runs elsewhere, ideally on `Pi 5`,
- messages are `retained`,
- and `Home Assistant` holds state and history outside of Zero.

This has several advantages:

- minimal local writes,
- after a Zero restart, state can be quickly restored from retained MQTT,
- long-term history does not reside on the Zero `SD` card.

## Do We Need a Database on Zero?

### Short Answer

Yes, it is possible. But I do not recommend it as the default design.

### When a Database Makes Sense

`SQLite` would make sense if `Pi Zero` needed to:

- operate for a long time without an MQTT broker,
- hold its own local event history,
- or provide local analytics on damper changes.

### Why It Is Not the Default Choice

For this project, it is better to:

- hold state in RAM,
- minimally write a snapshot,
- and leave history to `Home Assistant`.

The database itself is not the problem.

The problem is the usage pattern:

- if we wrote every raw frame into it, that would be bad,
- if it only stored changes and the last state, that would be technically fine.

### Recommendation

Default variant:

- no `SQLite`
- `RAM + retained MQTT + small snapshot`

Alternative variant:

- small `SQLite` only for `damper_state` and `damper_events`
- write only on change
- no raw frame history

## Recommended Directory Structure on Zero

Recommended layout:

```text
/home/pi/futura/
  rs485_modbus_monitor.py
  futura_damper_bridge.py
  requirements.txt
  pi-zero-config.json
  damper-map.json
  state/
    dampers_state.json
  debug/
    raw-0001.jsonl
    raw-0002.jsonl
```

Notes:

- root `~/futura` contains runtime scripts and configuration,
- `state/` contains the single important small persistent snapshot,
- `debug/` is optional and can be empty.

## Recommended Runtime Configuration Contents

The runtime configuration should have at least these sections:

- `serial`
- `http`
- `mqtt`
- `storage`
- `debug`
- `damper_map`

### `serial`

Defines how Zero reads `RS485`.

For example:

- `port`
- `baudrate`
- `bytesize`
- `parity`
- `stopbits`
- `serial_timeout_seconds`
- `frame_gap_ms`

### `http`

Defines the local diagnostic API.

For example:

- `enabled`
- `listen_host`
- `listen_port`

### `mqtt`

Defines publishing outside of Zero.

For example:

- `enabled`
- `host`
- `port`
- `username`
- `password`
- `client_id`
- `topic_prefix`
- `retain`
- `qos`
- `publish_on_change_only`

### `storage`

Defines local persistence.

For example:

- `state_path`
- `snapshot_interval_seconds`
- `restore_state_on_start`
- `write_state_on_shutdown`

### `debug`

Defines how raw communication will be debugged.

For example:

- `raw_log_enabled`
- `raw_log_path`
- `raw_log_rotate_bytes`
- `raw_log_keep_files`
- `raw_log_compress_rotated`

### `damper_map`

Defines where the damper map comes from.

For example:

- `path`

## Recommended Damper Map Contents

The damper map file should be a purely installation-specific description.

At minimum for each damper:

- `slave_id`
- `room`

Recommended:

- `label`
- `enabled`

Optional:

- `zone` - derivable from `slave_id` for regular dampers; if present explicitly, it should match
- `type` - derivable from `slave_id` for regular dampers; if present explicitly, it should match
- `damper_index` - derivable from `slave_id` for regular dampers; if present explicitly, it should match
- `notes`
- `dip`

This derivation applies to regular VarioBreeze dampers, not arbitrary additional `RS485` nodes with a different address space.

## Recommended Configuration Templates

Sample files are included in the repo:

- [pi-zero-config.example.json](../src/sniffer/pi-zero-config.example.json)
- [damper-map.example.json](../src/sniffer/damper-map.example.json)

A detailed practical description of individual settings is in:

- [pi-zero-konfigurace.en.md](pi-zero-konfigurace.en.md)

These files are intended to serve as the basis for:

- production `Pi Zero`,
- other future installations,
- test environments,
- and local development on a PC.

## What Must Be Configurable Without Touching the Code

Without editing Python code, it must be possible to change:

- serial port,
- line parameters,
- HTTP API host and port,
- `MQTT` host and credentials,
- snapshot path,
- debug log path,
- enabling and disabling debug mode,
- damper map,
- topic prefix,
- snapshot interval,
- and optionally disabling `MQTT` or the HTTP API.

This is the minimum level of portability between different environments.

## Recommended Operating Modes

### Mode 1: Normal Operation

In normal operation:

- raw log disabled,
- snapshot saved infrequently,
- `MQTT` publishing only on change,
- HTTP endpoints only for health and current state.

This should be the default production mode.

### Mode 2: Diagnostics

In diagnostic mode:

- enable a short rotating raw log,
- optionally increase API detail,
- rotate logs at small file sizes,
- after finishing debugging, disable debug mode again.

### Mode 3: Forensic Test

For one-off experiments:

- enable raw log for, say, `15-30 min`,
- then archive it off the Zero,
- and return Zero to normal mode.

## HTTP API on Zero

On `Pi Zero`, it makes sense to have only a small local API.

Recommended endpoints:

- `/health`
- `/dampers`
- `/dampers/<slave_id>`

### `/health`

Should return:

- whether the sniffer is running or not,
- time of the last valid frame,
- number of dampers in the state cache,
- application version,
- `MQTT` connection status.

### `/dampers`

Should return the already derived damper state, not raw frames.

For example:

```json
{
  "dampers": [
    {
      "slave_id": 66,
      "room": "Pracovna",
      "zone": 3,
      "type": "privod",
      "target_position": 56,
      "status_code": 1,
      "last_target_ts": "2026-03-26T09:17:02+00:00",
      "last_status_ts": "2026-03-26T13:18:13+00:00"
    }
  ]
}
```

A raw `/frames` endpoint does not need to be permanently enabled in production.

## Recommended Operation as systemd Services

For Zero I would recommend two options:

### Variant A: Single Process

One process handles:

- sniffer,
- parser,
- state engine,
- MQTT publish,
- HTTP health API.

Advantages:

- simpler operation,
- less IPC,
- fewer moving parts.

Disadvantages:

- larger process,
- somewhat harder to debug individual layers.

### Variant B: Two Processes

1. `futura-sniffer.service`
2. `futura-bridge.service`

Advantages:

- cleaner separation,
- easier to replace bridge logic without touching the serial part.

Disadvantages:

- more complex operation,
- typically more pressure on the middle layer or local storage.

### Recommendation

For `Pi Zero` I prefer:

- one service,
- one process,
- one state cache,
- no intermediate log as the main communication layer.

## Behavior After Restart

On application start:

1. load `damper_map`
2. load `state/dampers_state.json`, if it exists
3. restore damper state into RAM
4. connect `MQTT`
5. republish the last known state as `retained`
6. start sniffing new frames

This means:

- the last known state is available right after start,
- there is no need to wait until all dampers reposition,
- and no large historical log is read unnecessarily.

## Behavior During MQTT Outage

During an `MQTT` outage, I do not want to build a large offline queue on Zero.

Recommendation:

- keep only the current state in RAM,
- continue saving the snapshot as normal,
- after `MQTT` recovery, republish the entire current state,
- do not save every unsent change as a queue to disk.

This is significantly gentler on the `SD`.

## Recommended Sources of Truth

On Zero there will be two different "truthful" views:

### Operational Truth

The current operational truth is:

- the in-memory state cache

### Emergency Recovery

Emergency recovery is:

- `state/dampers_state.json`

### Long-Term History

Long-term history is not Zero's responsibility.

It should be held by:

- `MQTT broker` outside of Zero,
- or `Home Assistant`.

## What I Recommend Implementing First

### Phase 1

This phase is already implemented in:

- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

Current status:

- holds damper state in RAM,
- processes `FC16 / 102`,
- processes `FC4 / 107`,
- maps `slave_id -> room` via `damper-map.json`,
- exposes `/dampers`,
- and saves `state/dampers_state.json`.

### Phase 2

Add:

- `MQTT` publish on change,
- `retained` messages,
- republish after start.

### Phase 3

Add:

- optional debug mode,
- rotating raw log,
- optionally capturing only selected `slave_id` temporarily.

## Final Recommendation

The best solution for `Pi Zero` in terms of `SD` card longevity is:

- do not use an endless raw log as the main storage,
- do not store all raw frames in a database,
- hold the main state in RAM,
- write to disk only a small snapshot of the last known state,
- publish changes to `MQTT`,
- and keep the raw log only as a temporary diagnostic tool.

In brief:

```text
RAM as the primary runtime state
+ retained MQTT outside Zero as the main external persistence
+ small local snapshot as emergency recovery
+ short rotating debug log only when needed
```

This is the most sensible compromise between:

- robustness,
- simplicity,
- resource consumption,
- and `SD` card longevity.
