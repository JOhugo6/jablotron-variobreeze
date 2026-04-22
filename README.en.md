[Česky](README.md) | **English**

# Futura VarioBreeze

## What is this

This project reads the state of dampers in the `Jablotron Futura` HVAC unit with the `VarioBreeze` system.

Futura controls the ventilation of a house and uses VarioBreeze dampers to distribute air to individual rooms. The dampers open and close automatically based on air quality, temperature, and other conditions.

The project can:

- read publicly available Futura registers over the network (`Modbus TCP`),
- passively sniff internal communication between Futura and the dampers (`RS485 / Modbus RTU`),
- derive the target position and state of each damper from the sniffed data,
- expose damper state via a local HTTP API,
- optionally publish state to `MQTT` for integration with `Home Assistant`.

## What is in the repository

The repository is divided into two independent parts:

- `src/modbus`
  A tool for direct reading of Futura registers over the network (`Modbus TCP`).
  Runs on any PC with Python.
- `src/sniffer`
  Passive sniffing of Futura's internal RS485 bus.
  Typically runs on a `Raspberry Pi Zero 2 W` connected directly to the unit.
- `docs`
  Technical documentation, wiring, configuration, and working conclusions from reverse engineering analysis.

## Which part do you need

### Do you just want to read basic Modbus TCP registers from Futura over the network?

Use `src/modbus`. All you need is a PC with Python and a network connection to Futura.
Details are in [src/modbus/README.en.md](src/modbus/README.en.md).

### Do you want to monitor the actual state of the dampers?

Use `src/sniffer`. For this you need a `Raspberry Pi Zero 2 W` with an `RS485` converter, connected to Futura's internal bus.

The rest of this README describes this path.

---

## Step by step: RS485 sniffer on Pi Zero

The entire procedure from scratch to a working damper sniffer is described below. If you do not understand something, you do not need to know Linux or the command line beforehand. Every command is written out exactly as you should type it.

### Step 1: What you need to buy

Recommended hardware:

1. `Raspberry Pi Zero 2 W` with pre-soldered GPIO header (version `WH`)
2. `Waveshare TTL TO RS485 (B)` - galvanically isolated converter
3. `microSD` card, at least `16 GB`, class `A1` or better
4. `5V` power supply for Pi (micro-USB, at least `2.5A`)
5. short jumper wires (Female/Male, 10 cm)

If the Pi will be in a distribution cabinet, a DIN rail mount and `MEAN WELL HDR-30-5` as a power supply are recommended.

A detailed shopping list with specific products and stores is in:
- [docs/nakupni-seznam.en.md](docs/nakupni-seznam.en.md)

### Step 2: Flash the OS to the SD card

On your PC:

1. Download and install `Raspberry Pi Imager` (available for Windows, Mac, and Linux).
2. Launch `Raspberry Pi Imager`.
3. In the `Choose OS` menu, select `Raspberry Pi OS Lite (64-bit)`.
   This is the version without a graphical desktop, suitable for Pi Zero.
4. In the `Choose Storage` menu, select your microSD card.
5. Click the gear icon (`OS Customisation`) and fill in:
   - `Set hostname`: for example `futura-sniffer`
   - `Set username and password`: choose a username and password, you will need them when logging in
   - `Configure wireless LAN`: enter the name and password of your Wi-Fi network
   - `Enable SSH`: check this so you can log in to the Pi remotely
   - `Set locale settings`: set the time zone (e.g., `Europe/Prague`) and keyboard layout
6. Click `Write` and wait for the card to be written.

### Step 3: Connect the hardware

1. Insert the microSD card into the Pi Zero.
2. Connect the Pi to the Waveshare module:

```text
Raspberry Pi                  Waveshare TTL TO RS485 (B)
==========                    ==========================
pin 1  (3V3)   ------------> VCC
pin 6  (GND)   ------------> GND
pin 10 (RXD0)  <------------ TXD
pin 8  (TXD0)  DO NOT CONNECT
                              RXD   DO NOT CONNECT
```

3. Connect the Waveshare module to Futura:

```text
Waveshare                     Futura RS-485
=========                     =============
A+  ---------------------------> A
B-  ---------------------------> B
SGND --- optionally ------------> GND / COM
```

4. Set the `120R` switch on the module to `OFF`.
5. Connect power to the Pi.

#### Power supply

If you have a standard micro-USB power supply (wall adapter):

- plug it into the `PWR IN` port on the Pi Zero
- `Pi Zero 2` has two micro-USB ports, use the one labeled `PWR IN`, not the data `USB` port

If you are powering the Pi from a DIN rail power supply in the distribution cabinet (`MEAN WELL HDR-30-5` or similar):

- take a short `micro-USB` cable (e.g., `0.15 m`)
- cut off the `USB-A` end
- inside the cable you will find 4 wires: `red` (+5V), `black` (GND), `white` (D-), `green` (D+)
- verify the colors with a multimeter for continuity before connecting them
- connect `red` to the `+V` output of the DIN power supply
- connect `black` to the `-V` output of the DIN power supply
- insulate `white` and `green`, do not connect them
- plug the `micro-USB` end into the `PWR IN` port on the Pi Zero

Before powering on, check:

- there is no short between `+V` and `-V`
- `white` and `green` wires are insulated
- `Pi` is not powered through `GPIO` pins

Leave the `230 V` side wiring of the DIN power supply to a qualified person.

Important:

- `Pi pin 8 (TX)` must not be connected to anything. The Pi should only listen, not transmit.
- `module RXD` must not be connected to anything.
- The module is connected in parallel to the bus, not in series.

Detailed wiring diagram, power supply topologies, and variants are in:
- [docs/waveshare-ttl-to-rs485-b-zapojeni.en.md](docs/waveshare-ttl-to-rs485-b-zapojeni.en.md)

### Step 4: Connect to the Pi via SSH

After powering on the Pi, wait about a minute for the system to boot and connect to Wi-Fi.

You log in to the Pi remotely via `SSH`. This is a way to control the Pi from your computer over the network, as if you were sitting right in front of it. There is no monitor or keyboard connected to the Pi. Everything is done by typing commands into a text window on your PC.

#### On Windows

1. Download and install `PuTTY` (it is free).
2. Launch `PuTTY`.
3. Fill in:
   - `Host Name`: `futura-sniffer.local`
     (or the IP address of the Pi, if you know it, for example `192.168.1.50`)
   - `Port`: `22`
   - `Connection type`: `SSH`
4. Click `Open`.
5. On the first connection, a security warning will appear. Click `Accept`.
6. Enter the username and password you set in step 2.

If `futura-sniffer.local` does not work:

- You can find the Pi's IP address in your router's admin interface, in the list of connected devices or `DHCP leases`.
- Or try `hostname.local` directly, i.e., whatever you entered in `Set hostname`.

#### On Mac or Linux

Open a terminal and type:

```bash
ssh uzivatel@futura-sniffer.local
```

Replace `uzivatel` with the username you set in step 2.

### Step 5: Prepare the system on the Pi

After logging in via SSH, enter the following commands one by one. Each line is one command. Type it and press `Enter`.

System update:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git python3 python3-venv
```

What these commands do:

- `sudo` means the command runs with administrator privileges
- `apt update` downloads the current list of available packages
- `apt full-upgrade` updates all installed packages
- `apt install` installs new packages (`git`, `python3`, `python3-venv`)

### Step 6: Enable the serial port on the Pi

The Pi needs to have the serial port (`UART`) enabled, through which it reads data from the RS485 converter.

Launch the configuration tool:

```bash
sudo raspi-config
```

In the menu, set:

1. `Interface Options` -> `Serial Port`
2. `Login shell over serial?` -> `No`
3. `Enable serial hardware?` -> `Yes`

Exit `raspi-config` and select `Finish`.

Then open the configuration file:

```bash
sudo nano /boot/firmware/config.txt
```

Add two lines at the end of the file:

```ini
enable_uart=1
dtoverlay=disable-bt
```

Save (`Ctrl+O`, `Enter`) and close (`Ctrl+X`).

Then type:

```bash
sudo systemctl disable hciuart
sudo reboot
```

The Pi will restart. Wait a minute and log in again via SSH (same as in step 4).

After logging in, verify that the serial port exists:

```bash
ls -l /dev/serial0
```

If a line with `/dev/serial0` is displayed, everything is fine. If not, go back to the `raspi-config` and `config.txt` settings.

### Step 7: Copy files to the Pi

Create a project folder on the Pi:

```bash
mkdir -p ~/futura
```

`~` means the home directory of the logged-in user, for example `/home/futura` or `/home/zero`.

Now you need to get the files from this repository onto the Pi. The easiest way is to use `git`:

```bash
cd ~/futura
git clone https://github.com/JOhugo6/jablotron-variobreeze.git repo
cp repo/src/sniffer/rs485_modbus_monitor.py .
cp repo/src/sniffer/futura_damper_bridge.py .
cp repo/src/sniffer/requirements.txt .
cp repo/src/sniffer/pi-zero-config.example.json pi-zero-config.json
cp repo/src/sniffer/damper-map.example.json damper-map.json
```

Alternatively, you can transfer the files manually from your PC via `scp`. On Windows you can use `WinSCP` (a graphical file manager for SSH). You need to get at least these files onto the Pi:

- `rs485_modbus_monitor.py`
- `futura_damper_bridge.py`
- `requirements.txt`
- `pi-zero-config.example.json` (rename to `pi-zero-config.json`)
- `damper-map.example.json` (rename to `damper-map.json`)

All of them should be in the `~/futura` folder.

### Step 8: Install Python dependencies

```bash
cd ~/futura
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

What these commands do:

- `python3 -m venv .venv` creates an isolated Python environment in the `.venv` folder
- `source .venv/bin/activate` activates this environment (you will see `(.venv)` in the command prompt)
- `pip install -r requirements.txt` installs the required libraries (`pyserial`, `paho-mqtt`)

### Step 9: Edit the configuration

In the `~/futura` folder you have two configuration files:

- `pi-zero-config.json` - program settings (serial port, HTTP API, MQTT)
- `damper-map.json` - damper map for your house (which damper belongs to which room)

Open both files with the `nano` editor:

```bash
nano ~/futura/pi-zero-config.json
```

Save: `Ctrl+O`, `Enter`. Close: `Ctrl+X`.

#### What to set in `pi-zero-config.json`

You do not need to change most of the default values. Check mainly:

- `serial.port` - should be `"/dev/serial0"` if you are using GPIO UART
- `serial.baudrate` - should be `19200` (the correct value for Futura)
- `mqtt.enabled` - leave as `false` until you have an MQTT broker ready

#### What to set in `damper-map.json`

The example file contains a damper map for a specific house. If you have a different number of dampers or different rooms, edit this file according to your installation. You need to know:

- `slave_id` of each damper (derived from DIP switches on the damper)
- the room where the damper is located

For regular VarioBreeze dampers, `zone`, `type`, and `damper_index` are derived from `slave_id`. If you include them explicitly in `damper-map.json`, the bridge checks that they match the derived value.

A detailed description of all fields in both files is in:
- [docs/pi-zero-konfigurace.en.md](docs/pi-zero-konfigurace.en.md)

The DIP switch to `slave_id` mapping and the complete damper map of this house is in:
- [docs/mapa-klapek.en.md](docs/mapa-klapek.en.md)

### Step 10: First test - diagnostic monitor

First verify that the Pi can see data from the bus. The diagnostic monitor is used for this:

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

Open a second SSH window (in PuTTY, right-click the title bar -> `Duplicate Session`) and type:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/stats
```

If the response shows `frames_total` greater than `0` and `frames_valid_crc` greater than `0`, the sniffer is working.

If `frames_valid_crc` stays at `0`, try different settings one by one:

1. `--baudrate 19200 --parity N` (default, correct for Futura)
2. `--baudrate 9600 --parity N`
3. `--baudrate 19200 --parity E`
4. `--baudrate 9600 --parity E`

If nothing works, try swapping the `A+` and `B-` wires on the Waveshare module.

Stop the monitor with the keyboard shortcut `Ctrl+C`.

### Step 11: Start the production bridge

When the diagnostic monitor confirms that data is flowing from the bus, switch to the production bridge:

```bash
cd ~/futura
source .venv/bin/activate
python futura_damper_bridge.py --config pi-zero-config.json
```

In the second SSH window, verify:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

The `/dampers` response should contain a list of dampers with their state.

### Step 12: Set up automatic startup

To have the bridge run automatically after each Pi boot, set it up as a system service.

Create the service file:

```bash
sudo nano /etc/systemd/system/futura-damper-bridge.service
```

Paste this content (adjust `User` and paths according to your username):

```ini
[Unit]
Description=Passive RS-485 damper bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/futura
ExecStart=/home/YOUR_USERNAME/futura/.venv/bin/python /home/YOUR_USERNAME/futura/futura_damper_bridge.py --config /home/YOUR_USERNAME/futura/pi-zero-config.json
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Where you see `YOUR_USERNAME`, replace it with the name you set in step 2 (for example `zero` or `futura`).

Save (`Ctrl+O`, `Enter`) and close (`Ctrl+X`).

Then activate the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now futura-damper-bridge
```

Verify that it is running:

```bash
sudo systemctl status futura-damper-bridge
```

If you see `active (running)`, the bridge is running and will start automatically after each Pi restart.

To view ongoing logs:

```bash
sudo journalctl -u futura-damper-bridge -f
```

Stop the log view with the keyboard shortcut `Ctrl+C`.

### Updating software on the Pi Zero

When a new version of the scripts is released in the repository, updating on the Pi Zero looks like this:

1. Log in to the Pi Zero via SSH.
2. Download the new version of the files:

If you cloned the repo via `git` in step 7:

```bash
cd ~/futura/repo
git pull
cd ~/futura
cp repo/src/sniffer/futura_damper_bridge.py .
cp repo/src/sniffer/rs485_modbus_monitor.py .
```

If you transfer files via `WinSCP`, replace the files `futura_damper_bridge.py` and `rs485_modbus_monitor.py` in `~/futura` with the new versions.

3. If `requirements.txt` has changed (new dependency), update the Python packages:

```bash
cd ~/futura
source .venv/bin/activate
pip install -r requirements.txt
```

If `requirements.txt` has not changed, skip this step.

4. Restart the service:

```bash
sudo systemctl restart futura-damper-bridge
```

5. Verify that the bridge is running:

```bash
sudo systemctl status futura-damper-bridge
sudo journalctl -u futura-damper-bridge --no-pager -n 20
```

The configuration files `pi-zero-config.json` and `damper-map.json` are not overwritten during the update. If a new version adds new configuration fields, the bridge will use default values for them. New fields and their meaning can be found in the changelog or in [docs/pi-zero-konfigurace.en.md](docs/pi-zero-konfigurace.en.md).

---

### Step 13: Integration with Home Assistant via MQTT

This step is optional. If you want the damper state to be displayed in `Home Assistant`, you need an MQTT broker and MQTT enabled in the bridge.

#### On Home Assistant (Pi 5)

1. In `Home Assistant`, open `Settings` -> `Add-ons` -> `Add-on Store`.
2. Find `Mosquitto broker` (official add-on) and click `Install`.
3. After installation, click `Start`.
4. Create an MQTT user: `Settings` -> `People` -> `Users` -> `Add User`.
   Remember the username and password, you will need them in the next step.
5. Add the MQTT integration: `Settings` -> `Devices & Services` -> `Add Integration` -> search for `MQTT`.
   If you have the Mosquitto add-on on the same machine, Home Assistant usually finds it automatically.
   If not, fill in `host` (`127.0.0.1`), `port` (`1883`), and the login credentials.

#### On the Pi Zero

Edit `~/futura/pi-zero-config.json` and enable MQTT:

```bash
nano ~/futura/pi-zero-config.json
```

In the `mqtt` section, change:

```json
"mqtt": {
  "enabled": true,
  "host": "HOME_ASSISTANT_IP_ADDRESS",
  "port": 1883,
  "username": "mqtt_user",
  "password": "mqtt_password"
}
```

Where:

- `HOME_ASSISTANT_IP_ADDRESS` is the IP address of your Pi 5 running Home Assistant (for example `192.168.1.10`)
- `mqtt_user` and `mqtt_password` are the login credentials you created in Home Assistant

Save (`Ctrl+O`, `Enter`) and close (`Ctrl+X`).

Then restart the bridge to load the new configuration:

```bash
sudo systemctl restart futura-damper-bridge
```

Verify that the bridge is running without errors:

```bash
sudo systemctl status futura-damper-bridge
sudo journalctl -u futura-damper-bridge --no-pager -n 20
```

In the log you should see a message about a successful connection to the MQTT broker. If you see a connection error, check:

- whether the Home Assistant IP address is correct
- whether the Mosquitto add-on is running
- whether the username and password are correct
- whether the Pi Zero can see the Pi 5 on the network (try `ping HOME_ASSISTANT_IP_ADDRESS`)

#### Verification in Home Assistant

The bridge automatically publishes discovery messages for Home Assistant when connecting to MQTT. This means that entities are created in HA automatically, without manual configuration in `configuration.yaml`.

After restarting the bridge, open `Settings` -> `Devices & Services` -> `MQTT` in HA.

The following will be created in HA:

- one parent device `Futura VarioBreeze Bridge`
- a separate device for each damper (e.g., `Obyvak privod 1`, `Knihovna privod 1`, ...)

Each damper is its own device, so you can assign it to the correct room in HA: `Settings` -> `Devices & Services` -> `MQTT` -> click on the damper device -> `Area`. Room assignment is manual; the bridge does not create them automatically.

Under each damper device there are sensors:

- `Poloha` - target position of the damper in percent (`target_position`)
- `Status` - status code of the damper (`status_code`)
- `Poslední změna polohy` - when Futura last recalculated the position (`last_target_ts`)
- `Poslední aktivita` - when the damper was last seen on the bus (`last_seen_ts`)

If you do not see the entities:

- verify that the MQTT integration in HA is working: `Settings` -> `Devices & Services` -> `MQTT` -> `Configure` -> `Listen to a topic` -> enter `homeassistant/#` -> `Start listening`
- in the bridge log you should see a line `MQTT HA Discovery: publikováno X klapek`
- try restarting the bridge: `sudo systemctl restart futura-damper-bridge`

For manual inspection of raw MQTT messages, enter `futura/#` in `Listen to a topic`.

#### What the bridge sends to MQTT

For each damper, the bridge publishes a message to the topic:

```
futura/damper/<slave_id>/state
```

Example message for damper `slave_id 69` (Natalka, supply, zone 6):

```json
{
  "slave_id": 69,
  "room": "Natalka",
  "zone": 6,
  "type": "privod",
  "damper_index": 1,
  "label": "Natalka privod 1",
  "enabled": true,
  "notes": null,
  "target_position": 48,
  "status_code": 1,
  "last_target_ts": "2026-03-27T12:24:04+00:00",
  "last_status_ts": "2026-03-27T11:18:00+00:00",
  "last_seen_ts": "2026-03-27T12:24:04+00:00"
}
```

Meaning of individual fields:

| Field | Type | Description |
|---|---|---|
| `slave_id` | int | Damper address on the RS485 bus. Derived from DIP switches on the damper |
| `room` | string | Room name from `damper-map.json` |
| `zone` | int | Zone number in Futura |
| `type` | string | `privod` (supply damper) or `odtah` (exhaust damper) |
| `damper_index` | int | Sequence number of the damper in the given zone (if there are multiple dampers in a room) |
| `label` | string | Human-readable damper description from `damper-map.json` |
| `enabled` | bool | Whether the damper is marked as active in the map |
| `notes` | string/null | Optional note from `damper-map.json` |
| `target_position` | int/null | Target damper position in percent (0-100). Derived from `FC16 / register 102`, which Futura writes to the damper when it recalculates the desired opening. `null` means no position change has been captured since the bridge started |
| `status_code` | int/null | Damper status code. Derived from `FC4 / register 107`, which Futura periodically reads from the damper. Observed values are `0`, `1`, `2`, `4`. This is not a simple open/closed state but a multi-state code. `null` means no response has been captured since the bridge started |
| `last_target_ts` | string/null | Timestamp (UTC, ISO 8601) of the last captured target position write (`register 102`). Changes only when Futura recalculates the damper position, not periodically |
| `last_status_ts` | string/null | Timestamp of the last captured status code read (`register 107`) where the value changed |
| `last_seen_ts` | string/null | Timestamp of the last frame of any kind captured for this damper on the bus. Updates even when values do not change. Serves as an indicator that the damper is still active |

Important:

- `target_position` is not sent periodically. Futura writes a new target position only when it recalculates it (for example, when CO2 changes in the zone). There can be several minutes between writes.
- After a bridge restart, `target_position` and `status_code` will temporarily be `null` until Futura writes the position again or the bridge loads the last known state from a snapshot.
- Messages are `retained`, so Home Assistant sees the last known state even after its own restart.

---

## Modbus TCP on PC

This part is independent of the Pi Zero and is used for direct reading of Futura's public registers over the network.

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r src/modbus/requirements.txt
```

### Usage

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once
```

Before the first run, copy the example configuration and fill in Futura's IP address:

```bash
copy src\modbus\config.example.json src\modbus\config.json
```

Details are in [src/modbus/README.en.md](src/modbus/README.en.md).

---

## Documentation

| Document | Description |
|---|---|
| [src/modbus/README.en.md](src/modbus/README.en.md) | Modbus TCP tool, configuration, discovery |
| [src/sniffer/README.en.md](src/sniffer/README.en.md) | Sniffer, bridge, diagnostic monitor |
| [docs/pi-zero-konfigurace.en.md](docs/pi-zero-konfigurace.en.md) | Detailed description of `pi-zero-config.json` and `damper-map.json` |
| [docs/mapa-klapek.en.md](docs/mapa-klapek.en.md) | Damper map, DIP switches, slave_id, reverse engineering of registers |
| [docs/cil-home-assistant.en.md](docs/cil-home-assistant.en.md) | Goal of Home Assistant integration |
| [docs/navrh-architektury-pi-zero.en.md](docs/navrh-architektury-pi-zero.en.md) | Bridge architecture on Pi Zero |
| [docs/pi-zero-2w-rs485-sniffer.en.md](docs/pi-zero-2w-rs485-sniffer.en.md) | Deployment plan, HW variants, systemd services |
| [docs/nakupni-seznam.en.md](docs/nakupni-seznam.en.md) | Shopping list, stores, alternatives |
| [docs/waveshare-ttl-to-rs485-b-zapojeni.en.md](docs/waveshare-ttl-to-rs485-b-zapojeni.en.md) | Waveshare module wiring, power supply, mounting |
| [docs/max3491-rx-only-zapojeni.en.md](docs/max3491-rx-only-zapojeni.en.md) | Alternative RX-only wiring with MAX3491 |
| [docs/poznamky-z-technickeho-centra-jablotron.en.md](docs/poznamky-z-technickeho-centra-jablotron.en.md) | Information from Jablotron technical support |
| [docs/Registr modbus.pdf](docs/Registr%20modbus.pdf) | Official Futura Modbus map from the manufacturer |
