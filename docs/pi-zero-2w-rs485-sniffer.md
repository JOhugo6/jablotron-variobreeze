# Raspberry Pi Zero 2 W RS-485 sniffer plán

## Kontext

- Veřejná `Modbus TCP` mapa Futury vrací stav připojených klapek, ale ne jejich polohy.
- Pasivní scan dostupných `input` a `holding` registrů neodhalil žádný registr, který by se choval jako skutečná poloha klapky.
- Další rozumný krok je pasivní odposlech interní `RS-485 / Modbus RTU` sběrnice mezi Futura a VarioBreeze klapkami.
- Cíl je čistě sniffer jen pro čtení, který fyzicky neumí vysílat na sběrnici.

## Finální doporučení

Aktuálně doporučená finální varianta už není `MAX3491` na adaptéru, ale hotový modul:

- `Waveshare TTL TO RS485 (B)`

Důvod:

- výrazně méně montážních chyb
- žádné `SMD` pájení
- galvanické oddělení
- šroubovací svorky
- stále jde zapojit pasivně tak, že `Pi TX` ani `modul RXD` nebudou připojené
- `Pi` může být přímo na `DIN` liště v rozvaděči
- napájení jde řešit kvalitním `DIN 5 V` zdrojem `MEAN WELL HDR-30-5`

Přesné finální zapojení je v:

- [waveshare-ttl-to-rs485-b-zapojeni.md](waveshare-ttl-to-rs485-b-zapojeni.md)

Přesná finální objednávka bez alternativ je v:

- [nakupni-seznam.md](nakupni-seznam.md)

## Doporučený HW k objednání

### Finální preferovaná varianta

1. `Raspberry Pi Zero 2 W s připájeným GPIO headerem`
2. `Waveshare TTL TO RS485 (B)`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 s Raspberry Pi OS`
4. `MEAN WELL HDR-30-5`
5. `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`
6. `Datový kabel USB - micro USB, 0,15m`
7. `Drátové propojky Female/Male 10 cm, 10 ks`

### Varianta A: doporučená

1. `Raspberry Pi Zero 2 WH`
   Důvod: má už osazený 40pin header, odpadá pájení.
2. `microSD karta 16 GB nebo 32 GB`, třída `A1` nebo lepší
3. `Napájecí zdroj 5.1 V / 2.5 A pro micro-USB`
4. `Waveshare RS485 Board (3.3V)` se SP3485 nebo ekvivalentní `3.3V` TTL-RS485 modul
   Požadavek: musí mít samostatné piny `RO`, `/RE`, `DE`, `DI`, `GND`, `A`, `B`, `VCC`.
5. `Dupont kabely`
   Doporučení: sada `female-female` a `female-male`, podle konektorů zvoleného modulu.
6. `Krabička pro Pi Zero 2 W`
7. `Krátký micro-USB kabel` pro napájení

### Varianta B: pokud koupíš opravdu Zero 2 W bez headeru

1. `Raspberry Pi Zero 2 W`
2. `2x20 40pin male header 2.54 mm`
3. `Páječka`, cín a základní vybavení pro osazení headeru
4. Vše ostatní stejně jako ve Variantě A

## Poznámka k výběru RS-485 modulu

Preferovaný modul je takový, kde lze hardware natvrdo zapojit do režimu:

- přijímač trvale povolený
- vysílač trvale zakázaný

To znamená:

- `/RE` připojit na `GND`
- `DE` připojit na `GND`
- `DI` nechat nezapojené
- používat pouze `RO`

Tím se z modulu stane čistý přijímač a nehrozí, že by Pi omylem vyslalo data na sběrnici.

## Co přesně objednat

### Minimum

1. `Raspberry Pi Zero 2 WH`
2. `Napájecí zdroj 5.1V / 2.5A micro-USB`
3. `microSD 32 GB`
4. `Waveshare RS485 Board (3.3V)` nebo jiný `SP3485/MAX3485` modul s piny `/RE` a `DE`
5. `Dupont vodiče`
6. `Krabička`

### Volitelné, ale praktické

1. `USB OTG + USB Ethernet adaptér`
   Použij jen pokud bude Wi-Fi v místě Futury slabá.
2. `WAGO / svorky / odbočné svorky`
   Jen pokud bude potřeba udělat čistou paralelní odbočku na `A/B/GND`.
3. `Galvanicky oddělený RS-485 modul`
   Je lepší, ale není nutný pro první odposlech.

## Varianta nákupu z GME

Stav ověřený k `23. březnu 2026`.

### Co na GME dává smysl

1. `RASPBERRY Pi Zero 2 W s připájeným GPIO headerem`
2. `RASPBERRY Pi Zero 2 WH`
3. `RASPBERRY Pi 64 GB microSD karta třídy A2`
4. `RASPBERRY Pi Zero krabička - oficiální`
5. `MAXIM MAX3491ECSD+`
6. `UPS-SO14 IC adaptér SOIC14/TSSOP14 na DIP14`
7. `ZYJ-W3 F-F dupont propojovací vodiče zásuvka-zásuvka, 40 žil`
8. `ZYJ-W3 M-F dupont propojovací vodiče vidlice-zásuvka, 40 žil`

### Výhoda GME

GME je zajímavější než běžné Raspberry obchody hlavně tím, že tam lze koupit:

- samotné Raspberry Pi
- dupont vodiče
- `RS-485` transceiver jako samostatný integrovaný obvod
- `SO14 -> DIP14` adaptér

To znamená, že na GME lze postavit bezpečnější `RX-only` variantu bez hotového obousměrného převodníku.

### Nevýhoda GME

Na GME jsem nenašel ideální hotový `RX-only` RS-485 přijímač jako modul.

Pro bezpečnou variantu z GME je tedy potřeba:

1. koupit `MAX3491ECSD+`
2. připájet jej na `SO14 -> DIP14` adaptér
3. ručně zapojit:
   - `VCC`
   - `GND`
   - `RO`
   - `/RE -> GND`
   - `DE -> GND`
   - `DI` nezapojené
   - `A/B` na sběrnici

### Doporučení

Pokud chcete:

- `minimum pájení`: kupte hotový obousměrný modul z jiného obchodu
- `maximum bezpečnosti`: GME varianta s `MAX3491 + adaptér` je lepší

### Praktická nákupní volba z GME

Nejrozumnější kombinace z jednoho obchodu je:

1. `RASPBERRY Pi Zero 2 W s připájeným GPIO headerem`
2. `RASPBERRY Pi 64 GB microSD karta třídy A2`
3. `RASPBERRY Pi Zero krabička - oficiální`
4. `MAXIM MAX3491ECSD+`
5. `UPS-SO14 IC adaptér SOIC14/TSSOP14 na DIP14`
6. `dupont` vodiče `F-F` a `M-F`

Napájení pro Pi je potřeba ověřit zvlášť podle aktuální nabídky `micro-USB` zdrojů. Pokud nebude na GME vhodný oficiální `5.1V / 2.5A` zdroj pro Zero, je lepší ho vzít jinde než nahrazovat nevhodným adaptérem.

### Finální varianta: co nejbezpečnější RX-only

Pokud je priorita maximální bezpečnost sběrnice, vezměte:

1. `RASPBERRY Pi Zero 2 W s připájeným GPIO headerem`
2. `RASPBERRY Pi 64 GB microSD karta třídy A2`
3. `RASPBERRY Pi Zero krabička - oficiální`
4. `MAXIM MAX3491ECSD+`
5. `UPS-SO14 IC adaptér SOIC14/TSSOP14 na DIP14`
6. `ZYJ-W3 F-F dupont propojovací vodiče zásuvka-zásuvka, 40 žil`
7. `ZYJ-W3 M-F dupont propojovací vodiče vidlice-zásuvka, 40 žil`

Tato varianta je nejlepší proto, že:

- Pi už má osazený header
- `MAX3491` použijeme jen jako přijímač
- `DE` i `/RE` lze natvrdo stáhnout do `GND`
- `TX` z Pi nepřipojíme vůbec
- `DI` necháme nezapojené

Výsledek:

- Pi umí jen poslouchat
- nemá žádnou softwarovou cestu, jak vyslat data do `RS-485`

Nevýhoda:

- je nutné připájet `MAX3491` na `SO14 -> DIP14` adaptér

Pokud nechcete pájet SMD čip, pak je bezpečnější koupit hotový modul jinde, ale z hlediska čistého `RX-only` je tato GME varianta lepší než běžný obousměrný `TTL <-> RS485` převodník.

### Jednodušší varianta s méně pájením

Pokud je priorita:

- méně montážních chyb
- méně pájení
- rychlejší zprovoznění

pak je lepší hotový `3.3V RS-485` modul s vyvedenými piny:

- `RO`
- `DI`
- `RE` a `DE`, nebo jedním společným pinem typu `RSE`
- `VCC`
- `GND`
- `A`
- `B`

Typicky:

1. `Waveshare RS485 Board (3.3V)`
2. jiný hotový modul se `SP3485` nebo `MAX3485`

Tahle varianta je horší než `MAX3491 na adaptéru` jen v tom, že uvnitř modulu pořád fyzicky existuje vysílač. Prakticky je ale velmi bezpečná, pokud:

1. `DE` nebo `RSE` stáhneš natvrdo na `GND`
2. `DI` necháš nezapojené
3. `Pi TX` vůbec nepřipojíš

Výsledek:

- žádné SMD pájení
- jen propojení vodiči
- výrazně menší riziko montážní chyby
- pořád velmi malá šance, že by modul něco vyslal do sběrnice

Tohle je nejlepší kompromis mezi bezpečností a jednoduchostí.

## Zapojení

Detailní pájecí a propojovací dokument je v:

- [max3491-rx-only-zapojeni.md](max3491-rx-only-zapojeni.md)

### Raspberry Pi GPIO

Použij `serial0` na pinech:

- `pin 1` = `3V3`
- `pin 6` = `GND`
- `pin 8` = `GPIO14 / TX`
- `pin 10` = `GPIO15 / RX`

### Zapojení Pi -> RS-485 modul

Pouze pro `RX-only` režim:

1. `Pi pin 1 (3V3)` -> `VCC` na RS-485 modulu
2. `Pi pin 6 (GND)` -> `GND` na RS-485 modulu
3. `Pi pin 10 (GPIO15 / RX / serial0 RX)` -> `RO` na RS-485 modulu
4. `Pi pin 6 (GND)` -> `/RE` na RS-485 modulu
5. `Pi pin 6 (GND)` -> `DE` na RS-485 modulu
6. `DI` na RS-485 modulu nechat nezapojené
7. `Pi pin 8 (TX)` nikam nepřipojovat

### Zapojení RS-485 modul -> Futura sběrnice

Připojit paralelně ke stávající sběrnici:

1. `A` modulu -> `A` sběrnice Futury
2. `B` modulu -> `B` sběrnice Futury
3. `GND` modulu -> `GND` sběrnice, pokud je k dispozici

### Důležité

1. `Nepřipojovat 24V` z Futury do Pi ani do RS-485 modulu.
2. `Nevkládat` sniffer do série, ale pouze paralelně.
3. `Nepřidávat další terminaci 120 ohm`, pokud ji už sběrnice má.
4. Pokud zvolený modul má terminaci přes jumper nebo DIP switch, nechat ji `OFF`.
5. Pokud po spuštění neuvidíš žádné validní rámce, zkus prohodit `A/B`.

## Instalace SW na Raspberry Pi

### 1. Nahrání systému

Na PC:

1. Nainstalovat `Raspberry Pi Imager`
2. Vybrat `Raspberry Pi OS Lite`
3. V `OS Customisation` nastavit:
   - hostname, například `futura-sniffer`
   - uživatele a heslo
   - Wi-Fi
   - `Enable SSH`

### 2. První přihlášení

Po startu Pi:

```bash
ssh <uzivatel>@futura-sniffer.local
```

Pokud `mDNS` nefunguje, přihlas se přes IP adresu z DHCP.

### 3. Základ systému

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git python3 python3-venv
```

### 4. Povolení UART

Spusť:

```bash
sudo raspi-config
```

Nastav:

1. `Interface Options` -> `Serial Port`
2. `Login shell over serial?` -> `No`
3. `Enable serial hardware?` -> `Yes`

Pak uprav:

```bash
sudo nano /boot/firmware/config.txt
```

Přidej:

```ini
enable_uart=1
dtoverlay=disable-bt
```

Potom:

```bash
sudo systemctl disable hciuart
sudo reboot
```

Po rebootu ověř:

```bash
ls -l /dev/serial0
```

Pro doporučené zapojení na `GPIO14/GPIO15` je správná volba v konfiguraci skoro vždy:

```json
"/dev/serial0"
```

`/dev/serial0` je doporučený stabilní alias na primární UART na Raspberry Pi.

Pokud chcete vidět, na co konkrétně ukazuje:

```bash
ls -l /dev/ttyAMA0 /dev/ttyS0 2>/dev/null
```

Jestli `/dev/serial0` po správném nastavení UART vůbec nevznikne, nepokračujte se změnou konfigurace naslepo. Nejdřív opravte `raspi-config`, `config.txt` a proveďte restart.

Jen pokud vědomě používáte `USB-RS485` adaptér místo GPIO UART, nastavuje se v konfiguraci jiný port, typicky:

- `/dev/ttyUSB0`
- `/dev/ttyACM0`

Takový port zjistíte takto:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

## Instalace monitoru

Pro `Pi Zero` jsou v repu dva různé nástroje:

- [../src/sniffer/rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)
  - diagnostický monitor pro reverzní analýzu
- [../src/sniffer/futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)
  - produkční bridge pro běžný provoz, stav klapek a volitelné `MQTT`

### 1. Zkopírování souborů

Na Pi nakopírujte minimálně:

- `src/sniffer/rs485_modbus_monitor.py` -> `~/futura/rs485_modbus_monitor.py`
- `src/sniffer/futura_damper_bridge.py` -> `~/futura/futura_damper_bridge.py`
- `src/sniffer/requirements.txt` -> `~/futura/requirements.txt`
- `src/sniffer/pi-zero-config.example.json` -> `~/futura/pi-zero-config.json`
- `src/sniffer/damper-map.example.json` -> `~/futura/damper-map.json`

Podrobný popis obou konfiguračních souborů je v:

- [pi-zero-konfigurace.md](pi-zero-konfigurace.md)

Například do:

```bash
mkdir -p ~/futura
```

### 2. Python prostředí

```bash
cd ~/futura
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. První ruční spuštění

Začněte tímto nastavením:

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

Pokud z linky nepotečou validní rámce, vyzkoušejte postupně:

1. `19200 8N1`
2. `9600 8N1`
3. `19200 8E1`
4. `9600 8E1`

## Produkční spuštění bridge

V běžném provozu na `Pi Zero` už nespouštějte diagnostický monitor, ale bridge:

```bash
cd ~/futura
source .venv/bin/activate
python futura_damper_bridge.py --config pi-zero-config.json
```

Bridge poskytuje lokální HTTP API:

- `http://127.0.0.1:8765/health`
- `http://127.0.0.1:8765/stats`
- `http://127.0.0.1:8765/latest`
- `http://127.0.0.1:8765/devices`
- `http://127.0.0.1:8765/dampers`
- `http://127.0.0.1:8765/dampers/<slave_id>`

`MQTT` je volitelné a zapíná se až v `~/futura/pi-zero-config.json`.

## Zpřístupnění přes TCP

### Bezpečná varianta

Nejprve nechte monitor jen na:

```bash
--listen-host 127.0.0.1
```

To je vhodné pro lokální test.

### Přístup z jiného PC v síti

Po ověření monitoru přepněte na:

```bash
--listen-host 0.0.0.0
```

Příklad:

```bash
python rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 0.0.0.0 \
  --listen-port 8765
```

Pak bude API dostupné na:

- `http://IP_RASPBERRY_PI:8765/health`
- `http://IP_RASPBERRY_PI:8765/stats`
- `http://IP_RASPBERRY_PI:8765/latest`
- `http://IP_RASPBERRY_PI:8765/frames?limit=100`

Produkční bridge místo toho vystavuje:

- `http://IP_RASPBERRY_PI:8765/health`
- `http://IP_RASPBERRY_PI:8765/stats`
- `http://IP_RASPBERRY_PI:8765/latest`
- `http://IP_RASPBERRY_PI:8765/devices`
- `http://IP_RASPBERRY_PI:8765/dampers`
- `http://IP_RASPBERRY_PI:8765/dampers/<slave_id>`

### Doporučení pro bezpečnost

Pokud bude Pi na běžné domácí LAN, stačí:

1. nepřesměrovávat port na internet
2. nepovolovat port mimo interní síť
3. ideálně omezit firewall na IP tvého PC

## Systemd služba

Po odladění ručního běhu vytvořte:

```bash
sudo nano /etc/systemd/system/rs485-modbus-monitor.service
```

Obsah:

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

Pak:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rs485-modbus-monitor
sudo systemctl status rs485-modbus-monitor
```

Pro běžný provoz na `Pi Zero` je vhodnější samostatná bridge služba:

```bash
sudo nano /etc/systemd/system/futura-damper-bridge.service
```

Obsah:

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

Pak:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now futura-damper-bridge
sudo systemctl status futura-damper-bridge
```

## Jak ověřit, že procesy na Zero běží

### Produkční bridge

Ověření procesu:

```bash
pgrep -af "futura_damper_bridge.py"
```

Stav `systemd` služby:

```bash
sudo systemctl status futura-damper-bridge
```

Živé logy:

```bash
sudo journalctl -u futura-damper-bridge -f
```

HTTP kontrola:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

Kontrola, že port opravdu naslouchá:

```bash
ss -ltnp | grep 8765
```

### Diagnostický monitor

Ověření procesu:

```bash
pgrep -af "rs485_modbus_monitor.py"
```

Stav `systemd` služby:

```bash
sudo systemctl status rs485-modbus-monitor
```

Živé logy:

```bash
sudo journalctl -u rs485-modbus-monitor -f
```

HTTP kontrola:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/stats
```

## Jak budeme pokračovat po dodání HW

1. Připojit Pi k Wi-Fi a ověřit SSH
2. Zapojit RX-only RS-485 modul
3. Ověřit, že Pi fyzicky nevysílá na sběrnici
4. Spustit monitor
5. Z jiného PC otevřít `/health` a `/dampers`
6. Zachytit několik minut provozu
7. V logu identifikovat:
   - `slave_id` jednotlivých klapek
   - funkce `0x03`, `0x04`, `0x06`, `0x10`
   - registry, které odpovídají stavu nebo poloze klapek

## Soubory v repu, které už jsou připravené

- [rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)
- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)
- [README.md](../README.md)
- [requirements.txt](../src/sniffer/requirements.txt)

## Reference

1. Raspberry Pi dokumentace: Zero 2 W a Zero 2 WH, GPIO header a konektivita
2. Raspberry Pi dokumentace: `serial0`, primární UART na GPIO14/GPIO15, `enable_uart`, `disable-bt`
3. Raspberry Pi dokumentace: Raspberry Pi Imager, přednastavení Wi-Fi a SSH
4. Raspberry Pi OS Bookworm dokumentace: doporučené použití `venv` pro Python balíčky
5. Waveshare RS485 Board (3.3V/5V) User Manual: piny `RO`, `/RE`, `DE`, `DI`, `A`, `B`, `VCC`
6. VarioBreeze datasheet: komunikace po `Modbus RTU`
