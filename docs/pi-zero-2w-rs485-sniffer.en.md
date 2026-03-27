[Česky](pi-zero-2w-rs485-sniffer.md) | **English**

# Raspberry Pi Zero 2 W RS-485 Sniffer Plan

## Context

- The public `Modbus TCP` map of the Futura returns the state of connected dampers, but not their positions.
- A passive scan of available `input` and `holding` registers did not reveal any register that would behave as an actual damper position.
- The next reasonable step is passive sniffing of the internal `RS-485 / Modbus RTU` bus between the Futura and VarioBreeze dampers.
- The goal is a purely read-only sniffer that is physically unable to transmit on the bus.

## Final Recommendation

The currently recommended final variant is no longer `MAX3491` on an adapter, but a ready-made module:

- `Waveshare TTL TO RS485 (B)`

Reason:

- significantly fewer assembly errors
- no `SMD` soldering
- galvanic isolation
- screw terminals
- can still be wired passively so that `Pi TX` and module `RXD` are not connected
- `Pi` can be mounted directly on a `DIN` rail in the distribution board
- power can be supplied by a quality `DIN 5 V` power supply `MEAN WELL HDR-30-5`

The exact final wiring is in:

- [waveshare-ttl-to-rs485-b-zapojeni.md](waveshare-ttl-to-rs485-b-zapojeni.md)

The exact final order list without alternatives is in:

- [nakupni-seznam.md](nakupni-seznam.md)

## Recommended HW to Order

### Final Preferred Variant

1. `Raspberry Pi Zero 2 W with pre-soldered GPIO header`
2. `Waveshare TTL TO RS485 (B)`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 with Raspberry Pi OS`
4. `MEAN WELL HDR-30-5`
5. `Vertical DIN rail mount for Raspberry Pi type 2`
6. `Data cable USB - micro USB, 0.15m`
7. `Jumper wires Female/Male 10 cm, 10 pcs`

### Variant A: Recommended

1. `Raspberry Pi Zero 2 WH`
   Reason: has a pre-soldered 40-pin header, no soldering needed.
2. `microSD card 16 GB or 32 GB`, class `A1` or better
3. `Power supply 5.1 V / 2.5 A for micro-USB`
4. `Waveshare RS485 Board (3.3V)` with SP3485 or equivalent `3.3V` TTL-RS485 module
   Requirement: must have separate pins `RO`, `/RE`, `DE`, `DI`, `GND`, `A`, `B`, `VCC`.
5. `Dupont cables`
   Recommendation: a set of `female-female` and `female-male`, depending on the chosen module's connectors.
6. `Case for Pi Zero 2 W`
7. `Short micro-USB cable` for power

### Variant B: If You Buy a Zero 2 W Without Header

1. `Raspberry Pi Zero 2 W`
2. `2x20 40pin male header 2.54 mm`
3. `Soldering iron`, solder, and basic equipment for header assembly
4. Everything else same as in Variant A

## Note on RS-485 Module Selection

The preferred module is one where the hardware can be permanently wired into the mode:

- receiver permanently enabled
- transmitter permanently disabled

This means:

- `/RE` connected to `GND`
- `DE` connected to `GND`
- `DI` left unconnected
- use only `RO`

This turns the module into a pure receiver and eliminates any risk of the Pi accidentally transmitting data to the bus.

## What Exactly to Order

### Minimum

1. `Raspberry Pi Zero 2 WH`
2. `Power supply 5.1V / 2.5A micro-USB`
3. `microSD 32 GB`
4. `Waveshare RS485 Board (3.3V)` or another `SP3485/MAX3485` module with `/RE` and `DE` pins
5. `Dupont wires`
6. `Case`

### Optional, But Practical

1. `USB OTG + USB Ethernet adapter`
   Use only if Wi-Fi at the Futura location is weak.
2. `WAGO / terminals / branch terminals`
   Only if you need to make a clean parallel tap on `A/B/GND`.
3. `Galvanically isolated RS-485 module`
   Better, but not necessary for the first sniffing attempt.

## GME Purchase Variant

Verified as of `March 23, 2026`.

### What Makes Sense at GME

1. `RASPBERRY Pi Zero 2 W with pre-soldered GPIO header`
2. `RASPBERRY Pi Zero 2 WH`
3. `RASPBERRY Pi 64 GB microSD card class A2`
4. `RASPBERRY Pi Zero case - official`
5. `MAXIM MAX3491ECSD+`
6. `UPS-SO14 IC adapter SOIC14/TSSOP14 to DIP14`
7. `ZYJ-W3 F-F dupont jumper wires socket-socket, 40 conductors`
8. `ZYJ-W3 M-F dupont jumper wires pin-socket, 40 conductors`

### GME Advantage

GME is more interesting than typical Raspberry shops mainly because you can buy there:

- the Raspberry Pi itself
- dupont wires
- `RS-485` transceiver as a standalone integrated circuit
- `SO14 -> DIP14` adapter

This means you can build a safer `RX-only` variant at GME without a ready-made bidirectional converter.

### GME Disadvantage

I did not find an ideal ready-made `RX-only` RS-485 receiver as a module on GME.

For the safe variant from GME, you therefore need to:

1. buy `MAX3491ECSD+`
2. solder it onto the `SO14 -> DIP14` adapter
3. manually wire:
   - `VCC`
   - `GND`
   - `RO`
   - `/RE -> GND`
   - `DE -> GND`
   - `DI` unconnected
   - `A/B` to the bus

### Recommendation

If you want:

- `minimum soldering`: buy a ready-made bidirectional module from another shop
- `maximum safety`: the GME variant with `MAX3491 + adapter` is better

### Practical Purchase Choice from GME

The most reasonable combination from a single shop is:

1. `RASPBERRY Pi Zero 2 W with pre-soldered GPIO header`
2. `RASPBERRY Pi 64 GB microSD card class A2`
3. `RASPBERRY Pi Zero case - official`
4. `MAXIM MAX3491ECSD+`
5. `UPS-SO14 IC adapter SOIC14/TSSOP14 to DIP14`
6. `dupont` wires `F-F` and `M-F`

The Pi power supply needs to be verified separately based on the current `micro-USB` power supply offerings. If a suitable official `5.1V / 2.5A` power supply for the Zero is not available on GME, it is better to get it elsewhere than to substitute an unsuitable adapter.

### Final Variant: Safest RX-Only

If the priority is maximum bus safety, get:

1. `RASPBERRY Pi Zero 2 W with pre-soldered GPIO header`
2. `RASPBERRY Pi 64 GB microSD card class A2`
3. `RASPBERRY Pi Zero case - official`
4. `MAXIM MAX3491ECSD+`
5. `UPS-SO14 IC adapter SOIC14/TSSOP14 to DIP14`
6. `ZYJ-W3 F-F dupont jumper wires socket-socket, 40 conductors`
7. `ZYJ-W3 M-F dupont jumper wires pin-socket, 40 conductors`

This variant is the best because:

- Pi already has a soldered header
- `MAX3491` is used only as a receiver
- `DE` and `/RE` can be permanently pulled to `GND`
- `TX` from Pi is not connected at all
- `DI` is left unconnected

Result:

- Pi can only listen
- there is no software path to transmit data to `RS-485`

Disadvantage:

- soldering the `MAX3491` onto the `SO14 -> DIP14` adapter is required

If you do not want to solder an SMD chip, it is safer to buy a ready-made module elsewhere, but from a pure `RX-only` perspective, this GME variant is better than a typical bidirectional `TTL <-> RS485` converter.

### Simpler Variant with Less Soldering

If the priority is:

- fewer assembly errors
- less soldering
- faster deployment

then a ready-made `3.3V RS-485` module with exposed pins is better:

- `RO`
- `DI`
- `RE` and `DE`, or a single combined pin like `RSE`
- `VCC`
- `GND`
- `A`
- `B`

Typically:

1. `Waveshare RS485 Board (3.3V)`
2. another ready-made module with `SP3485` or `MAX3485`

This variant is worse than `MAX3491 on adapter` only in that the transmitter physically still exists inside the module. Practically, however, it is very safe if:

1. `DE` or `RSE` is permanently pulled to `GND`
2. `DI` is left unconnected
3. `Pi TX` is not connected at all

Result:

- no SMD soldering
- just wire connections
- significantly lower risk of assembly errors
- still very low chance of the module transmitting anything to the bus

This is the best compromise between safety and simplicity.

## Wiring

The detailed soldering and wiring document is in:

- [max3491-rx-only-zapojeni.md](max3491-rx-only-zapojeni.md)

### Raspberry Pi GPIO

Use `serial0` on pins:

- `pin 1` = `3V3`
- `pin 6` = `GND`
- `pin 8` = `GPIO14 / TX`
- `pin 10` = `GPIO15 / RX`

### Wiring Pi -> RS-485 Module

For `RX-only` mode only:

1. `Pi pin 1 (3V3)` -> `VCC` on the RS-485 module
2. `Pi pin 6 (GND)` -> `GND` on the RS-485 module
3. `Pi pin 10 (GPIO15 / RX / serial0 RX)` -> `RO` on the RS-485 module
4. `Pi pin 6 (GND)` -> `/RE` on the RS-485 module
5. `Pi pin 6 (GND)` -> `DE` on the RS-485 module
6. `DI` on the RS-485 module left unconnected
7. `Pi pin 8 (TX)` not connected to anything

### Wiring RS-485 Module -> Futura Bus

Connect in parallel to the existing bus:

1. `A` of the module -> `A` of the Futura bus
2. `B` of the module -> `B` of the Futura bus
3. `GND` of the module -> `GND` of the bus, if available

### Important

1. `Do not connect 24V` from the Futura to the Pi or the RS-485 module.
2. `Do not insert` the sniffer in series, only in parallel.
3. `Do not add another 120 ohm termination` if the bus already has one.
4. If the chosen module has termination via a jumper or DIP switch, leave it `OFF`.
5. If you do not see any valid frames after startup, try swapping `A/B`.

## SW Installation on Raspberry Pi

### 1. Flashing the OS

On PC:

1. Install `Raspberry Pi Imager`
2. Select `Raspberry Pi OS Lite`
3. In `OS Customisation` set:
   - hostname, e.g. `futura-sniffer`
   - username and password
   - Wi-Fi
   - `Enable SSH`

### 2. First Login

After Pi starts:

```bash
ssh <username>@futura-sniffer.local
```

If `mDNS` does not work, log in via the IP address from DHCP.

### 3. System Basics

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git python3 python3-venv
```

### 4. Enabling UART

Run:

```bash
sudo raspi-config
```

Set:

1. `Interface Options` -> `Serial Port`
2. `Login shell over serial?` -> `No`
3. `Enable serial hardware?` -> `Yes`

Then edit:

```bash
sudo nano /boot/firmware/config.txt
```

Add:

```ini
enable_uart=1
dtoverlay=disable-bt
```

Then:

```bash
sudo systemctl disable hciuart
sudo reboot
```

After reboot, verify:

```bash
ls -l /dev/serial0
```

For the recommended wiring on `GPIO14/GPIO15`, the correct choice in the configuration is almost always:

```json
"/dev/serial0"
```

`/dev/serial0` is the recommended stable alias for the primary UART on Raspberry Pi.

If you want to see what it specifically points to:

```bash
ls -l /dev/ttyAMA0 /dev/ttyS0 2>/dev/null
```

If `/dev/serial0` does not appear after properly setting up UART, do not continue changing the configuration blindly. First fix `raspi-config`, `config.txt`, and perform a restart.

Only if you are deliberately using a `USB-RS485` adapter instead of GPIO UART, you set a different port in the configuration, typically:

- `/dev/ttyUSB0`
- `/dev/ttyACM0`

You can find such a port like this:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

## Monitor Installation

For `Pi Zero`, the repo contains two different tools:

- [../src/sniffer/rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)
  - diagnostic monitor for reverse analysis
- [../src/sniffer/futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)
  - production bridge for regular operation, damper state, and optional `MQTT`

### 1. Copying Files

Copy at least the following to the Pi:

- `src/sniffer/rs485_modbus_monitor.py` -> `~/futura/rs485_modbus_monitor.py`
- `src/sniffer/futura_damper_bridge.py` -> `~/futura/futura_damper_bridge.py`
- `src/sniffer/requirements.txt` -> `~/futura/requirements.txt`
- `src/sniffer/pi-zero-config.example.json` -> `~/futura/pi-zero-config.json`
- `src/sniffer/damper-map.example.json` -> `~/futura/damper-map.json`

A detailed description of both configuration files is in:

- [pi-zero-konfigurace.en.md](pi-zero-konfigurace.en.md)

For example into:

```bash
mkdir -p ~/futura
```

### 2. Python Environment

```bash
cd ~/futura
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. First Manual Run

Start with this setup:

```bash
cd ~/futura
source .venv/bin/activate
python rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 127.0.0.1 \
  --listen-port 8765
```

If no valid frames are coming from the line, try the following in order:

1. `19200 8N1`
2. `9600 8N1`
3. `19200 8E1`
4. `9600 8E1`

## Production Bridge Startup

In regular operation on `Pi Zero`, do not run the diagnostic monitor, but the bridge:

```bash
cd ~/futura
source .venv/bin/activate
python futura_damper_bridge.py --config pi-zero-config.json
```

The bridge provides a local HTTP API:

- `http://127.0.0.1:8765/health`
- `http://127.0.0.1:8765/stats`
- `http://127.0.0.1:8765/latest`
- `http://127.0.0.1:8765/devices`
- `http://127.0.0.1:8765/dampers`
- `http://127.0.0.1:8765/dampers/<slave_id>`

`MQTT` is optional and is enabled in `~/futura/pi-zero-config.json`.

## TCP Access

### Safe Variant

First keep the monitor only on:

```bash
--listen-host 127.0.0.1
```

This is suitable for local testing.

### Access from Another PC on the Network

After verifying the monitor, switch to:

```bash
--listen-host 0.0.0.0
```

Example:

```bash
python rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 0.0.0.0 \
  --listen-port 8765
```

Then the API will be available at:

- `http://IP_RASPBERRY_PI:8765/health`
- `http://IP_RASPBERRY_PI:8765/stats`
- `http://IP_RASPBERRY_PI:8765/latest`
- `http://IP_RASPBERRY_PI:8765/frames?limit=100`

The production bridge instead exposes:

- `http://IP_RASPBERRY_PI:8765/health`
- `http://IP_RASPBERRY_PI:8765/stats`
- `http://IP_RASPBERRY_PI:8765/latest`
- `http://IP_RASPBERRY_PI:8765/devices`
- `http://IP_RASPBERRY_PI:8765/dampers`
- `http://IP_RASPBERRY_PI:8765/dampers/<slave_id>`

### Security Recommendations

If Pi is on a regular home LAN, it is enough to:

1. not forward the port to the internet
2. not allow the port outside the internal network
3. ideally restrict the firewall to your PC's IP

## Systemd Service

After debugging the manual run, create:

```bash
sudo nano /etc/systemd/system/rs485-modbus-monitor.service
```

Contents:

```ini
[Unit]
Description=Passive RS-485 Modbus RTU monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/futura
ExecStart=/home/pi/futura/.venv/bin/python /home/pi/futura/rs485_modbus_monitor.py --serial-port /dev/serial0 --baudrate 19200 --parity N --stopbits 1 --listen-host 0.0.0.0 --listen-port 8765
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rs485-modbus-monitor
sudo systemctl status rs485-modbus-monitor
```

For regular operation on `Pi Zero`, a separate bridge service is more appropriate:

```bash
sudo nano /etc/systemd/system/futura-damper-bridge.service
```

Contents:

```ini
[Unit]
Description=Passive RS-485 damper bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/futura
ExecStart=/home/pi/futura/.venv/bin/python /home/pi/futura/futura_damper_bridge.py --config /home/pi/futura/pi-zero-config.json
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now futura-damper-bridge
sudo systemctl status futura-damper-bridge
```

## How to Verify That Processes on Zero Are Running

### Production Bridge

Process check:

```bash
pgrep -af "futura_damper_bridge.py"
```

`systemd` service status:

```bash
sudo systemctl status futura-damper-bridge
```

Live logs:

```bash
sudo journalctl -u futura-damper-bridge -f
```

HTTP check:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

Check that the port is actually listening:

```bash
ss -ltnp | grep 8765
```

### Diagnostic Monitor

Process check:

```bash
pgrep -af "rs485_modbus_monitor.py"
```

`systemd` service status:

```bash
sudo systemctl status rs485-modbus-monitor
```

Live logs:

```bash
sudo journalctl -u rs485-modbus-monitor -f
```

HTTP check:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/stats
```

## How We Will Continue After HW Delivery

1. Connect Pi to Wi-Fi and verify SSH
2. Wire the RX-only RS-485 module
3. Verify that Pi is physically not transmitting on the bus
4. Start the monitor
5. From another PC, open `/health` and `/dampers`
6. Capture a few minutes of traffic
7. In the log, identify:
   - `slave_id` of individual dampers
   - functions `0x03`, `0x04`, `0x06`, `0x10`
   - registers that correspond to damper state or position

## Files in the Repo That Are Already Prepared

- [rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)
- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)
- [README.md](../README.md)
- [requirements.txt](../src/sniffer/requirements.txt)

## References

1. Raspberry Pi documentation: Zero 2 W and Zero 2 WH, GPIO header and connectivity
2. Raspberry Pi documentation: `serial0`, primary UART on GPIO14/GPIO15, `enable_uart`, `disable-bt`
3. Raspberry Pi documentation: Raspberry Pi Imager, Wi-Fi and SSH preconfiguration
4. Raspberry Pi OS Bookworm documentation: recommended use of `venv` for Python packages
5. Waveshare RS485 Board (3.3V/5V) User Manual: pins `RO`, `/RE`, `DE`, `DI`, `A`, `B`, `VCC`
6. VarioBreeze datasheet: communication via `Modbus RTU`
