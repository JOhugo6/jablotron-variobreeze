[Česky](waveshare-ttl-to-rs485-b-zapojeni.md) | **English**

# Waveshare TTL TO RS485 (B) Wiring

## Selected Module

For this project, this is currently the most reasonable compromise between:

- bus safety
- ease of installation
- low number of wiring mistakes

Selected module:

- `Waveshare TTL TO RS485 (B)`

Reason for selection:

- ready-made module, no SMD soldering required
- `galvanically isolated`
- screw terminals on both the `TTL` and `RS-485` sides
- `120R` termination can be disabled via a switch
- official documentation shows the exact interface: `VCC`, `GND`, `TXD`, `RXD`, `SGND`, `A+`, `B-`

What to buy is described in a separate document:
- [nakupni-seznam.en.md](nakupni-seznam.en.md)

## What Is Used on the Module

Upper terminals of the module:

- `VCC`
- `GND`
- `TXD`
- `RXD`

Lower terminals of the module:

- `SGND`
- `A+`
- `B-`

Switch:

- `120R`

## Important Signal Logic

According to the official Waveshare test schematic:

- `USB-TTL RXD` is connected to `module TXD`
- `USB-TTL TXD` is connected to `module RXD`

This means:

- `module TXD` is the output from the module towards the host
- `module RXD` is the input to the module from the host

For passive sniffing, we therefore want:

- `Pi RX <- module TXD`
- `Pi TX` left completely disconnected
- `module RXD` left completely disconnected

This way the module has no data input from the Raspberry Pi.

## Exact Wiring to Raspberry Pi

Use these physical pins:

- `Pi pin 1` = `3V3`
- `Pi pin 6` = `GND`
- `Pi pin 10` = `GPIO15 / RXD0`
- `Pi pin 8` = `GPIO14 / TXD0`, this one is not used

### Exact Pi -> Module Connection Table

| Raspberry Pi | Waveshare Module | Note |
|---|---|---|
| `pin 1 (3V3)` | `VCC` | powers the TTL side of the module at `3.3 V` |
| `pin 6 (GND)` | `GND` | TTL side ground |
| `pin 10 (RXD0)` | `TXD` | data from module to Pi |
| nothing | `RXD` | do not connect |
| `pin 8 (TXD0)` | nothing | do not connect |

## Exact Wiring Module -> Futura

On the lower side of the module:

- `A+ -> A` on the Futura
- `B- -> B` on the Futura
- `SGND -> GND/COM` on the Futura only if the communication ground is clearly labeled

Safe procedure:

1. start with just `A+` and `B-`
2. if communication is not stable or you do not see valid frames, add `SGND -> GND/COM`
3. if `CRC` does not match, swap `A+` and `B-`

Never connect:

- `24V`
- power `0V`, unless it is certain that it is the communication `GND/COM`
- any wire from `Pi TX`

## Exact Module Settings

Before connecting to the Futura:

1. set the `120R` switch to `OFF`

Reason:

- the sniffer connects in parallel to an existing bus
- it must not add additional termination

## ASCII Diagram

```text
Raspberry Pi Zero 2 WH                     Waveshare TTL TO RS485 (B)                     Futura RS-485
======================                     ==========================                     ==============

pin 1  (3V3)   --------------------------> VCC
pin 6  (GND)   --------------------------> GND
pin 10 (RXD0)  <-------------------------- TXD
pin 8  (TXD0)   --- DO NOT CONNECT ---
                                           RXD --- DO NOT CONNECT ---

                                           A+  -----------------------------------------> A
                                           B-  -----------------------------------------> B
                                           SGND -------- optional -----------------------> GND / COM

                                           120R switch = OFF
```

## Pre-Power-On Checklist

Verify:

1. `Pi pin 8` is not connected to anything
2. `module RXD` is not connected to anything
3. `120R` is `OFF`
4. module `VCC` goes to `3V3`, not `5V`
5. `A+` and `B-` are not connected to `24V`
6. the module is connected `in parallel`, not in series

If points `1` and `2` are not met, this is not a passive setup.

## Recommended Assembly Procedure

1. prepare the Raspberry Pi with `UART` enabled
2. connect only `VCC`, `GND`, `TXD -> Pi RX`
3. leave `RXD` on the module disconnected
4. set `120R` to `OFF`
5. connect `A+` and `B-` to the Futura
6. start the monitor
7. only add `SGND` if needed

## How to Power the Pi in the Distribution Board

The best option is:

- `standalone DIN power supply 230 V AC -> 5 V DC`
- output at least `2.5 A`, preferably `3 A`
- short `5 V` lead to the `Pi`

Practical recommendation:

1. `MEAN WELL HDR-30-5`
2. `Pi` on a `Vertical DIN rail mount for Raspberry Pi type 2`
3. `USB to micro USB data cable, 0.15m`
4. power the `Pi` via its `micro-USB power` input, not via `GPIO`

### Why Not via GPIO 5V

Powering via `micro-USB power` is safer for the initial installation because:

- it is the standard power input of the board
- there is less risk of reverse polarity
- you avoid tinkering directly with the `5V` pins on the `GPIO`

If you want a cleaner panel solution later, you can make a short cable:

- `DIN power supply +5V`
- `DIN power supply GND`
- `micro-USB pigtail` to the `Pi`

## Exact Power Wiring Diagram

Wire the `230 V` section only according to the markings on the power supply and ideally by a qualified person.

Recommended topology:

```text
230 V AC distribution board
      |
      +---- L ------------------------------+
      |                                     |
      +---- N --------------------------+   |
                                         |   |
                              +---------------------------+
                              | DIN power supply 5 V / 4.5 A |
                              | AC IN: L, N              |
                              | DC OUT: +V, -V           |
                              +---------------------------+
                                         |   |
                                   +V ---+   +--- -V
                                         |   |
                                         |   |
                          cut end of the USB-A cable
                                         |   |
                              red -------+   +--- black
                              white ------------- do not connect
                              green ------------- do not connect
                                         |
                              micro-USB end into the Pi
```

### Exact Wiring: DIN Power Supply -> Micro-USB Cable

Use:

- `USB to micro USB data cable, 0.15m`
- cut the `USB-A` end
- strip only as much insulation as necessary

Standard USB cable wire colors:

- `red` = `+5V`
- `black` = `GND`
- `white` = `D-`
- `green` = `D+`

Before final connection, it is advisable to verify with a multimeter for continuity:

- `micro-USB pin 1` -> `red`
- `micro-USB pin 5` -> `black`

Connect:

- `DIN power supply +V` -> `red`
- `DIN power supply -V` -> `black`
- `white` -> insulate, do not connect
- `green` -> insulate, do not connect

Then:

- plug the `micro-USB` end into the `PWR IN` connector of the Raspberry Pi Zero 2

Warning:

- `Pi Zero 2` has two `micro-USB` ports
- use the `PWR IN` port for power
- do not use the data `USB` / `OTG` port

### Pre-First-Power-On Checklist

1. no short between `+V` and `-V`
2. `white` and `green` wires are individually insulated
3. `Pi` is not powered via `GPIO`
4. `Pi TX` is still not connected to the `Waveshare`
5. `Waveshare 120R` is `OFF`
6. the cable has mechanical strain relief and does not pull directly on the terminals

### Note on 5.0 V Voltage

Official Raspberry Pi power supplies for the `Zero 2 W` are typically `5.1 V`, while this `DIN` power supply outputs `5.0 V`.

My assessment:

- with a `0.15 m` cable and the low power draw of the `Zero 2 W`, this is a reasonable choice for this project
- if undervoltage or instability appears, check the actual voltage on the `Pi` and consider a different power supply or an adjustable `DIN` power supply

### What Not to Do with KNX

I would not power the `Pi` directly from the `KNX` power supply.

This also applies to the `ABB SV/S 30.640.5.1` shown in the photo.

Reason:

- the `KNX` power supply is intended for the `KNX` bus
- on the `SV/S 30.640.5.1`, the additional output `I2` is, according to the documentation, intended only for another `KNX` line in combination with a separate choke
- it is not a recommended output for powering general electronics such as `Raspberry Pi`

Therefore:

- `no` powering from `KNX bus 30 V`
- `no` powering from the `ABB I2` output for the `Pi`

### When a Second Option Makes Sense

If you already have another `SELV 24 V DC` power supply in the distribution board outside of `KNX`, then this approach is also reasonable:

1. take `24 V DC`
2. use a quality `buck converter 24 V -> 5.1 V`
3. power the `Pi` via `micro-USB`

This is viable, but for this project a standalone `DIN 5 V` power supply is simpler and cleaner.

### Mounting Recommendations

- place the `Pi` and `Waveshare` in the `SELV` section of the distribution board
- do not run `TTL` or `5 V` cables for long distances parallel to `230 V`
- if the enclosure strongly shields `Wi-Fi`, plan for a local signal test or alternative connectivity

Note on jumper wires:

- from the pack, use `3` pieces for `VCC`, `GND`, `TXD -> Pi RX`
- the `female` end goes on the `Pi` side
- the `male` end goes into the screw terminal on the module side

Note on Futura bus wires:

- for `A+`, `B-` and optionally `SGND`, I am not counting a specific product from the online shop
- use short local wires matching the actual terminal block at the Futura
- this is better resolved on-site based on actual spacing and terminal types

Practical recommendation:

- for the `Pi -> module` connection, use wires with a `female Dupont` connector on the Pi side
- on the module side, strip the wires and clamp them into the screw terminals
- for the `Futura -> module` connection, use separate wires into the lower terminals `SGND / A+ / B-`

## UTP Cable 3 m Variant

Yes, a `UTP` cable over a `3 m` distance can be used.

For this specific variant, it is a reasonable solution because:

- Waveshare specifies a transmission distance of approximately `10 m` for the `TTL` side
- our communication will be slow, typically `9600` or `19200`
- the link is `point-to-point`

Important conditions:

1. use a `dedicated` `UTP` cable solely for this connection
2. preferably `Cat5e` or `Cat6`, solid copper, not `CCA`
3. power the module from `Pi 3V3`, not from `5V`
4. leave `Pi TX` disconnected
5. leave `module RXD` disconnected

### Recommended Pair Assignment

Use 2 twisted pairs:

- pair 1: `Pi RXD0` and `GND`
- pair 2: `3V3` and `GND`

In practice:

- `white-orange` -> `Pi pin 10 (RXD0)` -> `module TXD`
- `orange` -> `GND`
- `white-blue` -> `Pi pin 1 (3V3)` -> `module VCC`
- `blue` -> `GND`

On both ends, join both `GND` wires together.

That is:

- `orange + blue` -> `Pi GND`
- `orange + blue` -> `module GND`

This improves the return path for both the signal and power.

### What Not to Use

- do not use `UTP` for the `A/B` side if the module is located directly at the Futura
- do not use an active `RJ45` network port or patch panel
- do not use `5V` to power the module when directly connected to `Pi GPIO`
- do not run `UTP` for long distances tightly parallel to `230 V`

### When It Is Better to Place the Pi Closer to the Module

If you have the option to place the `Pi` directly in the distribution board next to the module, that is even better.

Reason:

- the `TTL` link will be very short
- less interference
- fewer mechanical errors

But technically speaking, `UTP 3 m` is fine for this application.

### Recommendations for Initial Bring-Up

If there will be `3 m` of cable between the `Pi` and the module:

1. do the first test at `9600 8N1`
2. only then try `19200 8N1`
3. if operation is unstable, shorten the `TTL` wiring or use a shielded cable

## Software After Wiring

On the Raspberry Pi, use:

```bash
python src/sniffer/rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 127.0.0.1 \
  --listen-port 8765
```

If the traffic is not readable, try in sequence:

1. `19200 8N1`
2. `9600 8N1`
3. `19200 8E1`
4. `9600 8E1`

## Why I Chose This Variant

Compared to the `MAX3491` variant, this eliminates:

- SMD chip soldering
- soldering jumper wires on the adapter
- checking for fine short circuits between pins

Compared to a standard `USB-RS485` adapter, this variant is better because:

- it can be placed directly at the Futura
- it has separate power from the Pi via the TTL side
- it has screw terminals
- `Pi TX` remains physically disconnected

This is not an absolutely clean `RX-only` hardware solution like a standalone receiver, but it is much safer from a mounting perspective and more practical for this project.

## If the Target System Is Home Assistant

If the data will end up in `Home Assistant` on a `Raspberry Pi 5`, then the recommended architecture is as follows:

### 1. Standard Futura States

For everything that the Futura already supports via `Modbus TCP`, the simplest path is:

- `Futura -> Modbus TCP -> Home Assistant`

Not via `KNX`.

Reason:

- `Home Assistant` has an official `Modbus` integration
- this eliminates the additional layer of `Weinzierl KNX Modbus TCP Gateway`
- there is less complexity and fewer points of failure

### 2. Actual Damper States

If you want `Home Assistant` to also have data that the Futura does not expose via its public `Modbus TCP` -- namely the internal damper states -- the better path is:

- `RS-485 sniffer at the Futura -> MQTT -> Home Assistant`

Reason:

- the `KNX` gateway will not unlock anything beyond what `Modbus TCP` provides
- `Home Assistant` has an official `MQTT` integration and supports `MQTT discovery`
- the sniffer can run on a small `Pi Zero 2` at the Futura and simply publish data over the network to `HA`

### 3. When KNX Makes Sense

`KNX` makes sense primarily when:

- you want the same data simultaneously on the `KNX` bus
- you want to use them in `ETS` logic, visualization, or other `KNX` devices

But purely for `Home Assistant`, it is not the shortest path.

## References

1. Waveshare Wiki `TTL TO RS485 (B)`: https://www.waveshare.com/wiki/TTL_TO_RS485_(B)
