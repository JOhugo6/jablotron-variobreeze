[Česky](nakupni-seznam.md) | **English**

# Shopping List

## Selected Module

For passive sniffing of the Futura RS485 bus, the selected module is:

- `Waveshare TTL TO RS485 (B)`

Reason for selection:

- ready-made module, no SMD soldering required
- `galvanically isolated`
- screw terminals on both the `TTL` and `RS-485` sides
- `120R` termination can be disabled via a switch
- official documentation shows the exact interface: `VCC`, `GND`, `TXD`, `RXD`, `SGND`, `A+`, `B-`

Module wiring is described in a separate document:
- [waveshare-ttl-to-rs485-b-zapojeni.en.md](waveshare-ttl-to-rs485-b-zapojeni.en.md)

## Required Items

1. `Raspberry Pi Zero 2 W with pre-soldered GPIO header`
2. `Waveshare TTL TO RS485 (B)`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 with Raspberry Pi OS`
4. `MEAN WELL HDR-30-5`
5. `Vertical DIN rail mount for Raspberry Pi type 2`
6. `USB to micro USB data cable, 0.15m`
7. `Female/Male jumper wires 10 cm, 10 pcs`

## Mounting Accessories

These items are not specifically tied to a single shop, but they are part of the final BOM for mounting purposes:

1. `3x short wire 0.5 to 0.75 mm2` for `A+`, `B-` and optionally `SGND`
2. `2x short wire 0.5 to 0.75 mm2` for `DIN power supply +V/-V -> cut USB cable`
3. `ferrules` matching the chosen wire gauge, if using stranded wires
4. `cable ties` or other strain relief

## Only Reasonable Power Supply Alternative

If `HDR-30-5` is not available, a reasonable replacement is:

1. `MEAN WELL MDR-20-5`

For this project, however, I consider it an `alternative`, not the default choice.

## Mount Alternative: 3D Printing

A `DIN` mount for the `Pi Zero 2` can be 3D printed.

In practice this means:

- no need to buy a ready-made `Vertical DIN rail mount for Raspberry Pi type 2`
- an equivalent mount for a `TS35` rail can be printed instead

Printing recommendations:

- material: `PETG`, `ASA` or `ABS`
- not `PLA`
- at least `4` perimeters
- infill at least `40 %`

When 3D printing is a reasonable choice:

- `Pi` will be in the `SELV` section of the distribution board
- there is no high temperature inside the enclosure
- you do not mind some mechanical fine-tuning

When it is better to buy a ready-made mount:

- you want minimal installation risk
- you do not want to deal with DIN clip rigidity
- you want a finished and predictable mechanical solution

## Order Without Alternatives

The currently recommended order is:

1. `Raspberry Pi Zero 2 W with pre-soldered GPIO header`
2. `Waveshare TTL TO RS485 (B) converter`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 with Raspberry Pi OS`
4. `MEAN WELL HDR-30-5`
5. `Vertical DIN rail mount for Raspberry Pi type 2`
6. `USB to micro USB data cable, 0.15m`
7. `Female/Male jumper wires 10 cm, 10 pcs`

Why this particular setup:

- `Pi` already has a pre-soldered `GPIO header`, so no additional soldering is needed
- `Waveshare` module is ready-made and isolated
- `64GB microSD` is currently in stock and comes with `Raspberry Pi OS`
- `MEAN WELL HDR-30-5` is a higher quality `DIN 5V` power supply for distribution boards
- `Pi` can be mounted on the DIN rail right next to the converter
- `0.15 m micro-USB` cable allows short and clean power delivery
- `10 cm Female/Male` jumper wires are sufficient for a short `Pi -> module` connection

Availability status as of `March 23, 2026`:

- `Raspberry Pi Zero 2 W with pre-soldered GPIO header`: `RPishop in stock, 5+ pieces`
- `Waveshare TTL TO RS485 (B) converter`: `in stock, 5+ pieces`
- `Raspberry Pi 64GB microSDXC ...`: `RPishop in stock, 5+ pieces`
- `MEAN WELL HDR-30-5`: `in stock` at `RS Online CZ`
- `Vertical DIN rail mount for Raspberry Pi type 2`: `in stock, 5+ pieces`
- `USB to micro USB data cable, 0.15m`: `in stock, 5+ pieces`
- `Female/Male jumper wires 10 cm, 10 pcs`: `in stock, 5+ pieces`

## Recommended Purchase by Shop

### RPishop

1. `Raspberry Pi Zero 2 W with pre-soldered GPIO header`
2. `Waveshare TTL TO RS485 (B) converter`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 with Raspberry Pi OS`
4. `Vertical DIN rail mount for Raspberry Pi type 2`
5. `USB to micro USB data cable, 0.15m`
6. `Female/Male jumper wires 10 cm, 10 pcs`

### RS Online CZ

1. `MEAN WELL HDR-30-5`

This is currently my preferred purchasing option.

## If the Pi Will Be in the Distribution Board

If the `Raspberry Pi Zero 2` will indeed be in the distribution board next to the `Waveshare TTL TO RS485 (B)`, it is better to:

- not use a standard `Zero` case
- use a `DIN` mount for the Raspberry Pi instead
- place the `Pi` directly next to the `TTL/RS-485` module

This topology is better because:

- `TTL` wiring will be very short
- there will be less interference
- the entire setup will be more organized

### Practical Swap in the Cart

If you go with the `DIN` mounting approach, replace:

- `standard Zero case`

with:

- `Vertical DIN rail mount for Raspberry Pi type 2`

The standard case is no longer needed in that scenario.

## References

1. RPishop product page `Waveshare TTL TO RS485 (B) converter`: https://rpishop.cz/datove-redukce/6122-waveshare-prevodnik-ttl-na-rs485-b.html
2. RS Online CZ `MEAN WELL HDR-30-5`: https://cz.rs-online.com/web/p/napajeci-zdroje-pro-montaz-na-listu-din/1457864
