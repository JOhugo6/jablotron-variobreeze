[Česky](max3491-rx-only-zapojeni.md) | **English**

# MAX3491 RX-Only Wiring

Note:

- this is a more advanced variant requiring custom soldering
- the currently recommended final variant with lower assembly risk is [waveshare-ttl-to-rs485-b-zapojeni.en.md](waveshare-ttl-to-rs485-b-zapojeni.en.md)

## Goal

This variant is designed so that the `Raspberry Pi Zero 2 W` physically cannot transmit onto the Futura `RS-485` bus. The `Pi` will only listen to data from the internal `Futura <-> VarioBreeze` communication.

Principle:

- we use the `MAX3491` only as a receiver
- the transmitter output `Y/Z` remains unconnected
- the transmitter input `DI` remains unconnected
- `DE` is hardwired to `GND`, so the transmitter is permanently disabled
- `RE` is hardwired to `GND`, so the receiver is permanently enabled
- the Raspberry Pi `TX` pin is not connected at all

## Simpler Alternative Without SMD Soldering

If you do not want to solder a `SOIC-14` chip onto an adapter, there is a simpler variant:

- a ready-made `3.3V RS-485` module with a `SP3485` or `MAX3485` chip
- ideally with exposed pins `RO`, `DI`, `RE`, `DE`, `VCC`, `GND`, `A`, `B`
- or a module with a single direction pin such as `RSE`

For this variant, soldering the `MAX3491` is no longer necessary. You practically just connect wires.

### Recommended Wiring for a Ready-Made Module

If the module has separate `RE` and `DE` pins:

- `RO -> Pi pin 10`
- `RE -> GND`
- `DE -> GND`
- `DI -> do not connect`
- `VCC -> Pi pin 1 (3V3)`
- `GND -> Pi GND`
- `A -> A on Futura`
- `B -> B on Futura`
- `Pi pin 8 (TX) -> do not connect`

If the module has a single shared direction pin `RSE`:

- `RO -> Pi pin 10`
- `RSE -> GND`
- `DI -> do not connect`
- `VCC -> Pi pin 1 (3V3)`
- `GND -> Pi GND`
- `A -> A on Futura`
- `B -> B on Futura`
- `Pi pin 8 (TX) -> do not connect`

### When to Choose This Variant

Choose this variant if the following are more important to you:

- lower assembly risk
- zero SMD soldering
- faster initial setup

The `MAX3491` variant is still the cleanest `RX-only` solution, but a ready-made module is usually more practical for typical assembly.

## Additional Items Beyond the Main Hardware

In addition to the main shopping list, it is recommended to add:

1. `100 nF ceramic capacitor`
   Used as a bypass capacitor between `VCC` and `GND` directly at the `MAX3491`.
2. `Heat shrink tubing` or electrical tape
   For mechanical protection of exposed wires.
3. `Thin wire` for jumpers on the adapter
   Short pieces of insulated wire are sufficient.
4. `Multimeter`
   For checking shorts and verifying that `TX` is truly not connected anywhere.

## Chip and Adapter Orientation

Use a `MAX3491ECSD+` in `SOIC-14` package and a `SO14 -> DIP14` adapter.

When soldering, watch for two orientation marks:

- the chip has a `dot` or `notch` that indicates `pin 1`
- the adapter usually marks `pin 1` with a dot, square pad, or the number `1`

The chip must be oriented on the adapter so that `pin 1` of the chip sits on `pin 1` of the adapter.

## MAX3491 Pinout

Top view of the `MAX3491` chip, notch or dot at the top:

```text
            ┌───────────────┐
   NC    1  │ o           14│  VCC
   RO    2  │             13│  VCC
   RE    3  │             12│  A
   DE    4  │             11│  B
   DI    5  │             10│  Z
   GND   6  │              9│  Y
   GND   7  │              8│  NC
            └───────────────┘
```

Pin meanings for our project:

- `2 RO`: receiver TTL output, goes to `Pi RX`
- `3 RE`: receiver enable, active low, permanently tied to `GND`
- `4 DE`: transmitter enable, active high, permanently tied to `GND`
- `5 DI`: transmitter TTL input, left unconnected
- `6 GND`, `7 GND`: ground
- `11 B`, `12 A`: differential receiver input from the `RS-485` bus
- `13 VCC`, `14 VCC`: `3.3 V` power supply
- `9 Y`, `10 Z`: transmitter output, left unconnected

This corresponds to the official `MAX3491` datasheet, Figure 3 and package drawing.

## Exact Jumpers on the Adapter

Make the following permanent jumpers on the adapter:

1. `pin 13 -> pin 14`
   Connect both `VCC` pins together.
2. `pin 6 -> pin 7`
   Connect both `GND` pins together.
3. `pin 3 -> GND`
   The easiest way is to bridge `pin 3` to `pin 6`.
4. `pin 4 -> GND`
   The easiest way is to bridge `pin 4` to `pin 7`.
5. `100 nF` capacitor between `VCC` and `GND`
   Practically between the `pin 13/14` pair and the `pin 6/7` pair, as close to the chip as possible.

Do not connect:

- `pin 1`
- `pin 5`
- `pin 8`
- `pin 9`
- `pin 10`

## Soldering Diagram on the Adapter

After wiring, it should look like this in practice:

```text
TOP VIEW

            ┌───────────────┐
   NC    1  │ o           14│--+-- 3V3 z Pi
   RO    2  │             13│--+
   RE    3  │--+
   DE    4  │--+              12│---- A na Futuře
   DI    5  │                  11│---- B na Futuře
   GND   6  │--+               10│---- nezapojovat
   GND   7  │--+                9│---- nezapojovat
            └───────────────┘

RO  -> Pi pin 10
RE  -> GND
DE  -> GND
DI  -> nezapojovat
GND -> Pi GND
VCC -> Pi 3V3
A/B -> RS-485 sbernice Futury

100 nF kondenzator mezi VCC a GND
Pi TX pin 8 zustava odpojeny
```

## Exact Wiring to Raspberry Pi Zero 2 W

Use only these physical pins on the `40pin GPIO` header:

```text
Raspberry Pi Zero 2 W
Pohled shora na GPIO header

  3V3  (1) (2)  5V
 GPIO2 (3) (4)  5V
 GPIO3 (5) (6)  GND
 GPIO4 (7) (8)  GPIO14 / TXD0
   GND (9) (10) GPIO15 / RXD0
```

For our sniffer use:

- `pin 1` = `3V3`
- `pin 6` or `pin 9` = `GND`
- `pin 10` = `GPIO15 / RXD0`

Do not use:

- `pin 8` = `GPIO14 / TXD0`

## Exact Wiring Table

| MAX3491 pin | Signal | Connects to |
|---|---|---|
| `2` | `RO` | `Pi pin 10` |
| `3` | `RE` | `GND` |
| `4` | `DE` | `GND` |
| `5` | `DI` | do not connect |
| `6` | `GND` | `Pi GND` |
| `7` | `GND` | bridge to `pin 6` |
| `11` | `B` | `RS-485 B` on Futura |
| `12` | `A` | `RS-485 A` on Futura |
| `13` | `VCC` | `Pi pin 1` |
| `14` | `VCC` | bridge to `pin 13` |
| `9` | `Y` | do not connect |
| `10` | `Z` | do not connect |

## How to Solder

Recommended order:

1. Attach the `MAX3491` to the adapter in the correct orientation according to `pin 1`.
2. Solder `pin 1` and `pin 8` or the opposite corner first, just to hold the chip straight.
3. Solder the remaining legs.
4. Check under magnification that there are no solder bridges between adjacent pins.
5. On the bottom side of the adapter, make jumpers:
   - `13-14`
   - `6-7`
   - `3-6`
   - `4-7`
6. Solder the `100 nF` capacitor between `VCC` and `GND`.
7. Solder wires or a pin header for:
   - `RO`
   - `VCC`
   - `GND`
   - `A`
   - `B`

## Multimeter Check Before Connecting to Futura

Before connecting to the unit, verify:

1. `pin 13` and `pin 14` are conductively connected
2. `pin 6` and `pin 7` are conductively connected
3. `pin 3` is conductively connected to `GND`
4. `pin 4` is conductively connected to `GND`
5. `pin 5` is not connected to anything
6. `pin 9` and `pin 10` are not connected to anything
7. there is no hard short between `VCC` and `GND`
8. `Pi pin 8` is not connected anywhere

If point `8` does not hold, this is not the `RX-only` variant.

## Connecting to the Futura RS-485 Bus

Connect in `parallel`, not in series.

Correct:

- `MAX3491 pin 12 (A)` -> `A` on the Futura bus
- `MAX3491 pin 11 (B)` -> `B` on the Futura bus
- `MAX3491 GND` -> `GND` or `COM` on the bus, but only if it is clearly labeled on the communication terminal block

Never connect:

- `24V`
- `0V` power, unless it is explicitly labeled as communication `GND/COM` in the documentation or on the terminal block
- any wire from `Pi TX`

If Futura only has `A/B` without a separate `GND/COM`, start with just `A/B`.

## Note on A/B Labeling

With `RS-485`, the `A/B` labeling is inconsistent between manufacturers.

Therefore:

- first connect according to the labels on Futura
- if after startup no valid frames are visible and `CRC` does not match, swap `A` and `B`

## What Must Remain Disconnected

The following must not be connected anywhere:

- `Pi pin 8`
- `MAX3491 pin 5`
- `MAX3491 pin 9`
- `MAX3491 pin 10`

This is a critical safety requirement.

## Recommended Mechanical Construction

The most practical approach is:

1. `MAX3491` on a `SO14 -> DIP14` adapter
2. bring out `5` wires from the adapter:
   - `3V3`
   - `GND`
   - `RO`
   - `A`
   - `B`
3. protect the joint with heat shrink tubing or a small enclosure

On the Futura side, the tap should be:

- short
- mechanically secure
- without additional termination

## Software Part After Wiring

After hardware wiring on the Pi:

1. enable `UART`
2. verify `/dev/serial0`
3. run [rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)

First test:

```bash
python src/sniffer/rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 127.0.0.1 \
  --listen-port 8765
```

## References

1. Analog Devices `MAX3483-MAX3491` datasheet, Figure 3 and package drawing: https://www.analog.com/media/en/technical-documentation/data-sheets/MAX3483-MAX3491.pdf
2. Raspberry Pi documentation on `UART`, `serial0`, `GPIO14/GPIO15`: https://www.raspberrypi.com/documentation/computers/configuration.html
