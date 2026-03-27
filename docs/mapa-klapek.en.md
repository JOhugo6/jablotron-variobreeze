[Česky](mapa-klapek.md) | **English**

# Damper Map

This file is prepared for manual entry of all actually installed dampers in the system.

Fill in:

- `Room / zone`: human-readable room name
- `Type`: `supply` or `exhaust`
- `Zone`: zone number in Futura
- `Damper`: sequential damper number within the given zone
- `DIP1..DIP6`: `ON` or `OFF`
- `Note`: anything additionally useful

The columns `RS485 slave_id` and `Verified` are filled in based on the `DIP -> slave_id` match and based on passive RS485 sniffing.

## Summary

| Type | Zone | Room / zone | Damper count | Note |
|---|---:|-----------------|-------------:|---|
| supply | 1 | Living room     |            3 | confirmed by DIP table |
| supply | 2 | Library         |            1 |  |
| supply | 3 | Study           |            1 |  |
| supply | 4 | Terka           |            1 |  |
| supply | 5 | Marta           |            1 |  |
| supply | 6 | Natalka         |            1 |  |
| supply | 7 | Bedroom         |            1 |  |
| supply | 8 | -               |            0 |  |
| exhaust | 1 | Walk-in closet  |            1 |  |
| exhaust | 2 | Hallway         |            1 |  |
| exhaust | 3 | Kitchen         |            2 |  |
| exhaust | 4 | Bathroom 1F     |            1 |  |
| exhaust | 5 | Bathroom 2F     |            1 |  |
| exhaust | 6 | -               |            0 |  |
| exhaust | 7 | -               |            0 |  |
| exhaust | 8 | -               |            0 |  |

## Damper Details

| Room / zone | Type | Zone | Damper | DIP1 | DIP2 | DIP3 | DIP4 | DIP5 | DIP6 | RS485 slave_id | Verified | Note |
|-----------------|---|---:|---:|------|------|------|------|------|------|---:|---|---|
| Living room     | supply | 1 | 1 | OFF | OFF | OFF | OFF | OFF | OFF | 64 | yes | confirmed from table and matches sniffed data |
| Living room     | supply | 1 | 2 | OFF | OFF | OFF | ON  | OFF | OFF | 72 | yes | confirmed from table and matches sniffed data |
| Living room     | supply | 1 | 3 | OFF | OFF | OFF | OFF | ON  | OFF | 80 | yes | confirmed from table and matches sniffed data |
| Library         | supply | 2 | 1 | ON  | OFF | OFF | OFF | OFF | OFF | 65 | yes | matches sniffed data |
| Study           | supply | 3 | 1 | OFF | ON  | OFF | OFF | OFF | OFF | 66 | yes | matches sniffed data |
| Terka           | supply | 4 | 1 | ON  | ON  | OFF | OFF | OFF | OFF | 67 | yes | matches sniffed data |
| Marta           | supply | 5 | 1 | OFF | OFF | ON  | OFF | OFF | OFF | 68 | yes | matches sniffed data |
| Natalka         | supply | 6 | 1 | ON  | OFF | ON  | OFF | OFF | OFF | 69 | yes | matches sniffed data |
| Bedroom         | supply | 7 | 1 | OFF | ON  | ON  | OFF | OFF | OFF | 70 | yes | matches sniffed data |
| Walk-in closet  | exhaust | 1 | 1 | OFF | OFF | OFF | OFF | OFF | ON  | 96 | yes | matches sniffed data |
| Hallway         | exhaust | 2 | 1 | ON  | OFF | OFF | OFF | OFF | ON  | 97 | yes | matches sniffed data |
| Kitchen         | exhaust | 3 | 1 | OFF | ON  | OFF | OFF | OFF | ON  | 98 | yes | matches sniffed data |
| Kitchen         | exhaust | 3 | 2 | OFF | ON  | OFF | ON  | OFF | ON  | 106 | yes | matches sniffed data |
| Bathroom 1F     | exhaust | 4 | 1 | ON  | ON  | OFF | OFF | OFF | ON  | 99 | yes | matches sniffed data |
| Bathroom 2F     | exhaust | 5 | 1 | OFF | OFF | ON  | OFF | OFF | ON  | 100 | yes | matches sniffed data |

## Mapping Notes

- `slave_id 16` no longer looks like a regular damper. The current working hypothesis is that it is the `ALFA` node for zone 1 (`Living room`), which has all `DIP OFF`.
- This means that different types of peripherals on the bus probably use different address bases. For dampers the base `64` fits, for `ALFA` the base may be `16`.
- Several other devices respond via `FC4` with a single register. These are good candidates for individual dampers or peripherals.
- The number of actually installed dampers is `15` and exactly `15` active `FC4` nodes were captured on `RS485`: `64, 65, 66, 67, 68, 69, 70, 72, 80, 96, 97, 98, 99, 100, 106`.
- Current working hypothesis: `FC4` register `107` on individual dampers probably represents the binary state of the damper.
- So far it has been confirmed as a variable candidate at least on `slave_id 66` (`Study / supply / zone 3 / damper 1`), where it took values `0` and `1`.
- A longer log showed that `register 107` is more of a multi-state status than a purely binary value. Values `0`, `1`, `2` and `4` appeared on various dampers.
- In the observed window, dampers `64`, `65`, `66`, `68`, `69`, `70`, `72` changed notably, while `67`, `80`, `96`, `97`, `98`, `99`, `100`, `106` remained at value `1`.
- A targeted test by breathing on the `ALFA` in the `Living room` confirmed that `slave_id 16` very likely belongs to this `ALFA` node.
- During the same test, the probable `ALFA` register mapping appeared to be:
  - `68` = temperature in tenths of `°C`
  - `69` = relative humidity in `%`
  - `70` = `CO2` in `ppm`
- Living room dampers `64`, `72`, `80` reacted to this event by changing `register 107`, but no precise analog damper position in normal passive operation has been confirmed yet.
- In the time window of the same event, only responses to `FC4 / register 107` were captured for dampers `64`, `72`, `80`. No other register that would resemble a precise damper position in normal passive operation was captured.
- However, in the same window, a write from Futura to the living room dampers via `FC16 / register 102` was also captured.
- The written values were:
  - `33` at the beginning of the window,
  - then `32`,
  - then `31`,
  - and during a strong `CO2` increase also `100`.
- `FC16 / register 102` is therefore currently the strongest candidate for the target damper position or percentage opening request.
- An extended filter across more dampers showed that `FC16 / register 102` is used outside the living room as well.
- In the captured window, for example, the following values were observed:
  - `64`: `31`, `32`, `33`, `100`
  - `65`: `0`, `31`, `32`
  - `66`: `56`
  - `67`: `22`, `32`, `33`
  - `68`: `30`, `33`
  - `69`: `30`, `33`, `34`
  - `70`: `25`, `32`, `33`
  - `72`: `31`, `32`, `33`, `100`
  - `80`: `31`, `32`, `33`, `100`
- Current working interpretation:
  - `register 102` = target or computed damper position,
  - `register 107` = status code or damper response confirmation.
- A verification test for the `Study` (`slave 66`) in the window `2026-03-26T13:18:09+00:00` to `2026-03-26T13:31:43+00:00` captured no `FC16 / register 102`.
- In the same window, `FC4 / register 107` on `slave 66` remained unchanged at value `1`.
- In the same window, however, other supply dampers received a series of new writes to `FC16 / register 102`, typically with a gradual decrease from high values to lower ones:
  - `64`: `93 -> 90 -> 85 -> 51 -> 21 -> 24 -> 27 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `65`: `89 -> 86 -> 83 -> 80 -> 79 -> 77 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `67`: `91 -> 90 -> 87 -> 84 -> 81 -> 80 -> 77 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `68`: `94 -> 93 -> 90 -> 86 -> 83 -> 81 -> 78 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `69`: `98 -> 97 -> 93 -> 88 -> 84 -> 81 -> 51 -> 23 -> 26 -> 28 -> 32 -> 33 -> 35 -> 33 -> 31`
  - `70`: `91 -> 90 -> 88 -> 84 -> 81 -> 80 -> 77 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `72`: `98 -> 91 -> 89 -> 85 -> 51 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `80`: `98 -> 92 -> 89 -> 85 -> 51 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
- This supports the interpretation that `register 102` is a written target position that changes only when Futura recalculates.

## Derived Addressing Rule

From the observed match, the `RS485 slave_id` follows this pattern:

```text
slave_id = 64
         + DIP1*1
         + DIP2*2
         + DIP3*4
         + DIP4*8
         + DIP5*16
         + DIP6*32
```

Where:

- `OFF = 0`
- `ON = 1`

Examples:

- all `DIP OFF` -> `64`
- only `DIP4 ON` -> `72`
- only `DIP5 ON` -> `80`
- only `DIP6 ON` -> `96`
- `DIP2 + DIP4 + DIP6 ON` -> `106`
