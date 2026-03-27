# Futura VarioBreeze

## Co to je

Tento projekt čte stav klapek vzduchotechnické jednotky `Jablotron Futura` se systémem `VarioBreeze`.

Futura řídí větrání domu a přes klapky VarioBreeze rozděluje vzduch do jednotlivých místností. Klapky se otevírají a zavírají automaticky podle kvality vzduchu, teploty a dalších podmínek.

Projekt umí:

- číst veřejně dostupné registry Futury přes síť (`Modbus TCP`),
- pasivně odposlouchávat interní komunikaci mezi Futurou a klapkami (`RS485 / Modbus RTU`),
- z odposlechu odvozovat cílovou polohu a stav každé klapky,
- vystavit stav klapek přes lokální HTTP API,
- volitelně publikovat stav do `MQTT` pro napojení na `Home Assistant`.

## Co je v repozitáři

Repozitář je rozdělený na dvě samostatné části:

- `src/modbus`
  Nástroj pro přímé čtení registrů z Futury přes síť (`Modbus TCP`).
  Běží na jakémkoli PC s Pythonem.
- `src/sniffer`
  Pasivní odposlech interní RS485 sběrnice Futury.
  Běží typicky na `Raspberry Pi Zero 2 W` připojeném přímo k jednotce.
- `docs`
  Technická dokumentace, zapojení, konfigurace a pracovní závěry z reverzní analýzy.

## Kterou část potřebujete

### Chcete jen číst základní modbus TCP registry Futury přes síť?

Použijte `src/modbus`. Stačí PC s Pythonem a síťové spojení na Futuru.
Podrobnosti jsou v [src/modbus/README.md](src/modbus/README.md).

### Chcete sledovat skutečný stav klapek?

Použijte `src/sniffer`. K tomu potřebujete `Raspberry Pi Zero 2 W` s převodníkem `RS485`, připojené k interní sběrnici Futury.

Zbytek tohoto README popisuje právě tuto cestu.

---

## Krok za krokem: RS485 sniffer na Pi Zero

Celý postup od nuly do funkčního snifferu klapek je rozepsaný níže. Pokud něčemu nerozumíte, nemusíte znát Linux ani příkazovou řádku předem. Každý příkaz je vypsaný přesně tak, jak ho máte zadat.

### Krok 1: Co potřebujete koupit

Doporučený hardware:

1. `Raspberry Pi Zero 2 W` s připájeným GPIO headerem (verze `WH`)
2. `Waveshare TTL TO RS485 (B)` - galvanicky izolovaný převodník
3. `microSD` karta, alespoň `16 GB`, třída `A1` nebo lepší
4. `5V` napájecí zdroj pro Pi (micro-USB, alespoň `2.5A`)
5. krátké propojovací vodiče (Female/Male, 10 cm)

Pokud bude Pi v rozvodné skříni, doporučuje se DIN lišta držák a `MEAN WELL HDR-30-5` jako zdroj.

Podrobný nákupní seznam s konkrétními produkty a obchody je v:
- [docs/nakupni-seznam.md](docs/nakupni-seznam.md)

### Krok 2: Nahrát systém na SD kartu

Na svém PC:

1. Stáhněte a nainstalujte program `Raspberry Pi Imager` (existuje pro Windows, Mac i Linux).
2. Spusťte `Raspberry Pi Imager`.
3. V nabídce `Choose OS` vyberte `Raspberry Pi OS Lite (64-bit)`.
   Toto je verze bez grafického prostředí, vhodná pro Pi Zero.
4. V nabídce `Choose Storage` vyberte svou microSD kartu.
5. Klikněte na ikonu ozubeného kolečka (`OS Customisation`) a vyplňte:
   - `Set hostname`: například `futura-sniffer`
   - `Set username and password`: zvolte si uživatelské jméno a heslo, budete je potřebovat při přihlášení
   - `Configure wireless LAN`: vyplňte název a heslo vaší Wi-Fi sítě
   - `Enable SSH`: zaškrtněte, aby se bylo možné na Pi přihlásit vzdáleně
   - `Set locale settings`: nastavte časové pásmo (např. `Europe/Prague`) a rozložení klávesnice
6. Klikněte `Write` a počkejte, než se karta zapíše.

### Krok 3: Zapojit hardware

1. Vložte microSD kartu do Pi Zero.
2. Propojte Pi s Waveshare modulem:

```text
Raspberry Pi                  Waveshare TTL TO RS485 (B)
==========                    ==========================
pin 1  (3V3)   ------------> VCC
pin 6  (GND)   ------------> GND
pin 10 (RXD0)  <------------ TXD
pin 8  (TXD0)  NEZAPOJOVAT
                              RXD   NEZAPOJOVAT
```

3. Propojte Waveshare modul s Futurou:

```text
Waveshare                     Futura RS-485
=========                     =============
A+  ---------------------------> A
B-  ---------------------------> B
SGND --- volitelně -------------> GND / COM
```

4. Na modulu přepněte `120R` na `OFF`.
5. Zapojte napájení do Pi.

#### Napájení

Pokud máte běžný micro-USB zdroj (adaptér do zásuvky):

- zapojte ho do portu `PWR IN` na Pi Zero
- `Pi Zero 2` má dva micro-USB porty, použijte ten označený `PWR IN`, ne datový `USB`

Pokud napájíte Pi z DIN zdroje v rozvodné skříni (`MEAN WELL HDR-30-5` nebo podobný):

- vezměte krátký `micro-USB` kabel (např. `0,15 m`)
- ustřihněte `USB-A` konec
- uvnitř kabelu najdete 4 vodiče: `červený` (+5V), `černý` (GND), `bílý` (D-), `zelený` (D+)
- ověřte barvy multimetrem na kontinuitu, než je připojíte
- `červený` připojte na `+V` výstup DIN zdroje
- `černý` připojte na `-V` výstup DIN zdroje
- `bílý` a `zelený` zaizolujte, nezapojovat
- `micro-USB` konec zapojte do portu `PWR IN` na Pi Zero

Před zapnutím zkontrolujte:

- mezi `+V` a `-V` není zkrat
- `bílý` a `zelený` vodič jsou zaizolované
- `Pi` není napájené přes `GPIO` piny

Zapojení `230 V` strany DIN zdroje nechte na kvalifikované osobě.

Důležité:

- `Pi pin 8 (TX)` nesmí být nikam připojený. Pi má jen poslouchat, ne vysílat.
- `modul RXD` nesmí být nikam připojený.
- Modul se připojuje paralelně na sběrnici, ne do série.

Podrobné schéma zapojení, napájecí topologie a varianty jsou v:
- [docs/waveshare-ttl-to-rs485-b-zapojeni.md](docs/waveshare-ttl-to-rs485-b-zapojeni.md)

### Krok 4: Připojit se na Pi přes SSH

Po zapnutí Pi počkejte asi minutu, než naběhne systém a připojí se k Wi-Fi.

Na Pi se přihlásíte vzdáleně přes `SSH`. To je způsob, jak ovládat Pi z vašeho počítače přes síť, jako byste seděli přímo u něj. Na Pi není monitor ani klávesnice. Vše se dělá zadáváním příkazů do textového okna na vašem PC.

#### Na Windows

1. Stáhněte a nainstalujte program `PuTTY` (je zdarma).
2. Spusťte `PuTTY`.
3. Vyplňte:
   - `Host Name`: `futura-sniffer.local`
     (nebo IP adresu Pi, pokud znáte, například `192.168.1.50`)
   - `Port`: `22`
   - `Connection type`: `SSH`
4. Klikněte `Open`.
5. Při prvním připojení se zobrazí bezpečnostní varování. Klikněte `Accept`.
6. Zadejte uživatelské jméno a heslo, které jste nastavili v kroku 2.

Pokud `futura-sniffer.local` nefunguje:

- IP adresu Pi najdete v administraci vašeho routeru, v seznamu připojených zařízení nebo `DHCP leases`.
- Nebo zkuste přímo `hostname.local`, tedy to co jste vyplnili v `Set hostname`.

#### Na Mac nebo Linux

Otevřete terminál a zadejte:

```bash
ssh uzivatel@futura-sniffer.local
```

Místo `uzivatel` doplňte jméno, které jste nastavili v kroku 2.

### Krok 5: Připravit systém na Pi

Po přihlášení přes SSH zadávejte postupně tyto příkazy. Každý řádek je jeden příkaz. Zadejte ho a stiskněte `Enter`.

Aktualizace systému:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git python3 python3-venv
```

Co tyto příkazy dělají:

- `sudo` znamená, že příkaz běží s oprávněním správce
- `apt update` stáhne aktuální seznam dostupných balíčků
- `apt full-upgrade` aktualizuje všechny nainstalované balíčky
- `apt install` nainstaluje nové balíčky (`git`, `python3`, `python3-venv`)

### Krok 6: Povolit sériový port na Pi

Pi potřebuje mít zapnutý sériový port (`UART`), přes který čte data z RS485 převodníku.

Spusťte konfigurační nástroj:

```bash
sudo raspi-config
```

V menu nastavte:

1. `Interface Options` -> `Serial Port`
2. `Login shell over serial?` -> `No`
3. `Enable serial hardware?` -> `Yes`

Ukončete `raspi-config` a vyberte `Finish`.

Pak otevřete konfigurační soubor:

```bash
sudo nano /boot/firmware/config.txt
```

Na konec souboru přidejte dva řádky:

```ini
enable_uart=1
dtoverlay=disable-bt
```

Uložte (`Ctrl+O`, `Enter`) a zavřete (`Ctrl+X`).

Pak zadejte:

```bash
sudo systemctl disable hciuart
sudo reboot
```

Pi se restartuje. Počkejte minutu a znovu se přihlaste přes SSH (stejně jako v kroku 4).

Po přihlášení ověřte, že sériový port existuje:

```bash
ls -l /dev/serial0
```

Pokud se vypíše řádek s `/dev/serial0`, je vše v pořádku. Pokud ne, vraťte se k nastavení `raspi-config` a `config.txt`.

### Krok 7: Nakopírovat soubory na Pi

Na Pi vytvořte složku pro projekt:

```bash
mkdir -p ~/futura
```

`~` znamená domovský adresář přihlášeného uživatele, například `/home/futura` nebo `/home/zero`.

Teď potřebujete dostat soubory z tohoto repozitáře na Pi. Nejjednodušší je použít `git`:

```bash
cd ~/futura
git clone https://github.com/JOhugo6/jablotron-variobreeze.git repo
cp repo/src/sniffer/rs485_modbus_monitor.py .
cp repo/src/sniffer/futura_damper_bridge.py .
cp repo/src/sniffer/requirements.txt .
cp repo/src/sniffer/pi-zero-config.example.json pi-zero-config.json
cp repo/src/sniffer/damper-map.example.json damper-map.json
```

Alternativně můžete soubory přenést ručně z PC přes `scp`. Na Windows lze použít program `WinSCP` (grafický správce souborů pro SSH). Potřebujete na Pi dostat alespoň tyto soubory:

- `rs485_modbus_monitor.py`
- `futura_damper_bridge.py`
- `requirements.txt`
- `pi-zero-config.example.json` (přejmenovat na `pi-zero-config.json`)
- `damper-map.example.json` (přejmenovat na `damper-map.json`)

Všechny mají být ve složce `~/futura`.

### Krok 8: Nainstalovat Python závislosti

```bash
cd ~/futura
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Co tyto příkazy dělají:

- `python3 -m venv .venv` vytvoří izolované Python prostředí ve složce `.venv`
- `source .venv/bin/activate` aktivuje toto prostředí (v příkazovém řádku se objeví `(.venv)`)
- `pip install -r requirements.txt` nainstaluje potřebné knihovny (`pyserial`, `paho-mqtt`)

### Krok 9: Upravit konfiguraci

Ve složce `~/futura` máte dva konfigurační soubory:

- `pi-zero-config.json` - nastavení programu (sériový port, HTTP API, MQTT)
- `damper-map.json` - mapa klapek pro váš dům (která klapka patří do které místnosti)

Oba soubory otevřete editorem `nano`:

```bash
nano ~/futura/pi-zero-config.json
```

Uložení: `Ctrl+O`, `Enter`. Zavření: `Ctrl+X`.

#### Co nastavit v `pi-zero-config.json`

Většinu výchozích hodnot nemusíte měnit. Zkontrolujte hlavně:

- `serial.port` - měl by být `"/dev/serial0"`, pokud používáte GPIO UART
- `serial.baudrate` - měl by být `19200` (správná hodnota pro Futuru)
- `mqtt.enabled` - nechte `false`, dokud nemáte připravený MQTT broker

#### Co nastavit v `damper-map.json`

Vzorový soubor obsahuje mapu klapek pro konkrétní dům. Pokud máte jiný počet klapek nebo jiné místnosti, upravte tento soubor podle své instalace. Potřebujete znát:

- `slave_id` každé klapky (odvozuje se z DIP přepínačů na klapce)
- místnost, ve které je klapka umístěná
- jestli je přívodní (`privod`) nebo odtahová (`odtah`)

Podrobný popis všech položek obou souborů je v:
- [docs/pi-zero-konfigurace.md](docs/pi-zero-konfigurace.md)

Mapování DIP přepínačů na `slave_id` a kompletní mapa klapek tohoto domu je v:
- [docs/mapa-klapek.md](docs/mapa-klapek.md)

### Krok 10: První test - diagnostický monitor

Nejdřív ověřte, že Pi vůbec vidí data ze sběrnice. K tomu slouží diagnostický monitor:

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

Otevřete druhé SSH okno (v PuTTY klikněte pravým na záhlaví -> `Duplicate Session`) a zadejte:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/stats
```

Pokud v odpovědi vidíte `frames_total` větší než `0` a `frames_valid_crc` větší než `0`, sniffer funguje.

Pokud `frames_valid_crc` zůstává na `0`, zkuste postupně jiné nastavení:

1. `--baudrate 19200 --parity N` (výchozí, správné pro Futuru)
2. `--baudrate 9600 --parity N`
3. `--baudrate 19200 --parity E`
4. `--baudrate 9600 --parity E`

Pokud nic nefunguje, zkuste prohodit vodiče `A+` a `B-` na Waveshare modulu.

Monitor ukončíte klávesovou zkratkou `Ctrl+C`.

### Krok 11: Spustit produkční bridge

Když diagnostický monitor potvrdí, že data ze sběrnice tečou, přepněte na produkční bridge:

```bash
cd ~/futura
source .venv/bin/activate
python futura_damper_bridge.py --config pi-zero-config.json
```

V druhém SSH okně ověřte:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

Odpověď `/dampers` by měla obsahovat seznam klapek s jejich stavem.

### Krok 12: Nastavit automatické spuštění

Aby bridge běžel automaticky po každém zapnutí Pi, nastavte ho jako systémovou službu.

Vytvořte soubor služby:

```bash
sudo nano /etc/systemd/system/futura-damper-bridge.service
```

Vložte tento obsah (upravte `User` a cesty podle vašeho uživatelského jména):

```ini
[Unit]
Description=Passive RS-485 damper bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=VASE_UZIVATELSKE_JMENO
WorkingDirectory=/home/VASE_UZIVATELSKE_JMENO/futura
ExecStart=/home/VASE_UZIVATELSKE_JMENO/futura/.venv/bin/python /home/VASE_UZIVATELSKE_JMENO/futura/futura_damper_bridge.py --config /home/VASE_UZIVATELSKE_JMENO/futura/pi-zero-config.json
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Kde vidíte `VASE_UZIVATELSKE_JMENO`, nahraďte ho jménem, které jste nastavili v kroku 2 (například `zero` nebo `futura`).

Uložte (`Ctrl+O`, `Enter`) a zavřete (`Ctrl+X`).

Pak službu aktivujte:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now futura-damper-bridge
```

Ověřte, že běží:

```bash
sudo systemctl status futura-damper-bridge
```

Pokud vidíte `active (running)`, bridge běží a bude se automaticky spouštět po každém restartu Pi.

Pro zobrazení průběžných logů:

```bash
sudo journalctl -u futura-damper-bridge -f
```

Logy ukončíte klávesovou zkratkou `Ctrl+C`.

### Aktualizace softwaru na Pi Zero

Když vyjde nová verze skriptů v repozitáři, aktualizace na Pi Zero vypadá takto:

1. Přihlaste se na Pi Zero přes SSH.
2. Stáhněte novou verzi souborů:

Pokud jste v kroku 7 klonovali repo přes `git`:

```bash
cd ~/futura/repo
git pull
cd ~/futura
cp repo/src/sniffer/futura_damper_bridge.py .
cp repo/src/sniffer/rs485_modbus_monitor.py .
```

Pokud přenášíte soubory přes `WinSCP`, nahraďte v `~/futura` soubory `futura_damper_bridge.py` a `rs485_modbus_monitor.py` novými verzemi.

3. Pokud se změnil `requirements.txt` (nová závislost), aktualizujte Python balíčky:

```bash
cd ~/futura
source .venv/bin/activate
pip install -r requirements.txt
```

Pokud se `requirements.txt` nezměnil, tento krok přeskočte.

4. Restartujte službu:

```bash
sudo systemctl restart futura-damper-bridge
```

5. Ověřte, že bridge běží:

```bash
sudo systemctl status futura-damper-bridge
sudo journalctl -u futura-damper-bridge --no-pager -n 20
```

Konfigurační soubory `pi-zero-config.json` a `damper-map.json` se aktualizací nepřepisují. Pokud nová verze přidá nové konfigurační položky, bridge pro ně použije výchozí hodnoty. Nové položky a jejich význam najdete v changelogu nebo v [docs/pi-zero-konfigurace.md](docs/pi-zero-konfigurace.md).

---

### Krok 13: Napojení na Home Assistant přes MQTT

Tento krok je volitelný. Pokud chcete, aby se stav klapek zobrazoval v `Home Assistant`, potřebujete MQTT broker a zapnuté MQTT v bridge.

#### Na Home Assistant (Pi 5)

1. V `Home Assistant` otevřete `Settings` -> `Add-ons` -> `Add-on Store`.
2. Najděte `Mosquitto broker` (oficiální add-on) a klikněte `Install`.
3. Po instalaci klikněte `Start`.
4. Vytvořte MQTT uživatele: `Settings` -> `People` -> `Users` -> `Add User`.
   Zapamatujte si jméno a heslo, budete je potřebovat v dalším kroku.
5. Přidejte MQTT integraci: `Settings` -> `Devices & Services` -> `Add Integration` -> vyhledejte `MQTT`.
   Pokud máte Mosquitto add-on na stejném stroji, Home Assistant ho většinou najde automaticky.
   Pokud ne, vyplňte `host` (`127.0.0.1`), `port` (`1883`) a přihlašovací údaje.

#### Na Pi Zero

Upravte `~/futura/pi-zero-config.json` a zapněte MQTT:

```bash
nano ~/futura/pi-zero-config.json
```

V sekci `mqtt` změňte:

```json
"mqtt": {
  "enabled": true,
  "host": "IP_ADRESA_HOME_ASSISTANT",
  "port": 1883,
  "username": "mqtt_uzivatel",
  "password": "mqtt_heslo"
}
```

Kde:

- `IP_ADRESA_HOME_ASSISTANT` je IP adresa vašeho Pi 5, na kterém běží Home Assistant (například `192.168.1.10`)
- `mqtt_uzivatel` a `mqtt_heslo` jsou přihlašovací údaje, které jste vytvořili v Home Assistant

Uložte (`Ctrl+O`, `Enter`) a zavřete (`Ctrl+X`).

Pak restartujte bridge, aby se načetla nová konfigurace:

```bash
sudo systemctl restart futura-damper-bridge
```

Ověřte, že bridge běží a nemá chyby:

```bash
sudo systemctl status futura-damper-bridge
sudo journalctl -u futura-damper-bridge --no-pager -n 20
```

V logu byste měli vidět zprávu o úspěšném připojení k MQTT brokeru. Pokud vidíte chybu spojení, zkontrolujte:

- jestli je IP adresa Home Assistantu správná
- jestli je Mosquitto add-on spuštěný
- jestli jsou uživatelské jméno a heslo správné
- jestli Pi Zero vidí na síti Pi 5 (zkuste `ping IP_ADRESA_HOME_ASSISTANT`)

#### Ověření v Home Assistant

Bridge při připojení k MQTT automaticky publikuje discovery zprávy pro Home Assistant. To znamená, že entity se v HA vytvoří samy, bez ruční konfigurace v `configuration.yaml`.

Po restartu bridge otevřete v HA `Settings` -> `Devices & Services` -> `MQTT`.

V HA se vytvoří:

- jedno nadřazené zařízení `Futura VarioBreeze Bridge`
- samostatné zařízení pro každou klapku (např. `Obyvak privod 1`, `Knihovna privod 1`, ...)

Každá klapka je vlastní zařízení, takže ji můžete v HA přiřadit do správné místnosti: `Settings` -> `Devices & Services` -> `MQTT` -> klikněte na zařízení klapky -> `Area`. Přiřazení místností je ruční, bridge je nevytváří automaticky.

Pod každým zařízením klapky jsou senzory:

- `Poloha` - cílová poloha klapky v procentech (`target_position`)
- `Status` - stavový kód klapky (`status_code`)
- `Poslední změna polohy` - kdy Futura naposledy přepočítala polohu (`last_target_ts`)
- `Poslední aktivita` - kdy byla klapka naposledy vidět na sběrnici (`last_seen_ts`)

Pokud entity nevidíte:

- ověřte, že MQTT integrace v HA je funkční: `Settings` -> `Devices & Services` -> `MQTT` -> `Configure` -> `Listen to a topic` -> zadejte `homeassistant/#` -> `Start listening`
- v logu bridge byste měli vidět řádek `MQTT HA Discovery: publikováno X klapek`
- zkuste restartovat bridge: `sudo systemctl restart futura-damper-bridge`

Pro ruční kontrolu surových MQTT zpráv zadejte v `Listen to a topic` hodnotu `futura/#`.

#### Co bridge posílá do MQTT

Pro každou klapku bridge publikuje zprávu na topik:

```
futura/damper/<slave_id>/state
```

Příklad zprávy pro klapku `slave_id 69` (Natálka, přívod, zóna 6):

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

Význam jednotlivých polí:

| Pole | Typ | Popis |
|---|---|---|
| `slave_id` | int | Adresa klapky na RS485 sběrnici. Odvozená z DIP přepínačů na klapce |
| `room` | string | Název místnosti z `damper-map.json` |
| `zone` | int | Číslo zóny ve Futuře |
| `type` | string | `privod` (přívodní klapka) nebo `odtah` (odtahová klapka) |
| `damper_index` | int | Pořadové číslo klapky v dané zóně (pokud je v místnosti víc klapek) |
| `label` | string | Lidsky čitelný popis klapky z `damper-map.json` |
| `enabled` | bool | Jestli je klapka v mapě označená jako aktivní |
| `notes` | string/null | Volitelná poznámka z `damper-map.json` |
| `target_position` | int/null | Cílová poloha klapky v procentech (0-100). Odvozená z `FC16 / registr 102`, který Futura zapisuje na klapku, když přepočítá požadované otevření. `null` znamená, že od startu bridge nebyla zachycena žádná změna polohy |
| `status_code` | int/null | Stavový kód klapky. Odvozený z `FC4 / registr 107`, který Futura periodicky čte z klapky. Pozorované hodnoty jsou `0`, `1`, `2`, `4`. Nejde o prosté otevřeno/zavřeno, ale o vícestavový kód. `null` znamená, že od startu bridge nebyla zachycena žádná odpověď |
| `last_target_ts` | string/null | Časová značka (UTC, ISO 8601) posledního zachyceného zápisu cílové polohy (`registr 102`). Mění se jen když Futura přepočítá polohu klapky, ne periodicky |
| `last_status_ts` | string/null | Časová značka posledního zachyceného čtení stavového kódu (`registr 107`), při kterém se hodnota změnila |
| `last_seen_ts` | string/null | Časová značka posledního libovolného rámce zachyceného pro tuto klapku na sběrnici. Aktualizuje se i když se hodnoty nemění. Slouží jako indikátor, že klapka je stále aktivní |

Důležité:

- `target_position` se neposílá periodicky. Futura zapíše novou cílovou polohu jen když ji přepočítá (například při změně CO2 v zóně). Mezi zápisy může být i několik minut.
- Po restartu bridge bude `target_position` a `status_code` dočasně `null`, dokud Futura znovu nezapíše polohu nebo bridge nenačte poslední známý stav ze snapshotu.
- Zprávy jsou `retained`, takže Home Assistant vidí poslední známý stav i po svém restartu.

---

## Modbus TCP na PC

Tato část je nezávislá na Pi Zero a slouží k přímému čtení veřejných registrů Futury přes síť.

### Instalace

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r src/modbus/requirements.txt
```

### Použití

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once
```

Před prvním spuštěním zkopírujte vzorovou konfiguraci a vyplňte IP adresu Futury:

```bash
copy src\modbus\config.example.json src\modbus\config.json
```

Podrobnosti jsou v [src/modbus/README.md](src/modbus/README.md).

---

## Dokumentace

| Dokument | Popis |
|---|---|
| [src/modbus/README.md](src/modbus/README.md) | Modbus TCP nástroj, konfigurace, discovery |
| [src/sniffer/README.md](src/sniffer/README.md) | Sniffer, bridge, diagnostický monitor |
| [docs/pi-zero-konfigurace.md](docs/pi-zero-konfigurace.md) | Podrobný popis `pi-zero-config.json` a `damper-map.json` |
| [docs/mapa-klapek.md](docs/mapa-klapek.md) | Mapa klapek, DIP přepínače, slave_id, reverzní analýza registrů |
| [docs/cil-home-assistant.md](docs/cil-home-assistant.md) | Cíl integrace s Home Assistant |
| [docs/navrh-architektury-pi-zero.md](docs/navrh-architektury-pi-zero.md) | Architektura bridge na Pi Zero |
| [docs/pi-zero-2w-rs485-sniffer.md](docs/pi-zero-2w-rs485-sniffer.md) | Plán nasazení, HW varianty, systemd služby |
| [docs/nakupni-seznam.md](docs/nakupni-seznam.md) | Nákupní seznam, obchody, alternativy |
| [docs/waveshare-ttl-to-rs485-b-zapojeni.md](docs/waveshare-ttl-to-rs485-b-zapojeni.md) | Zapojení Waveshare modulu, napájení, montáž |
| [docs/max3491-rx-only-zapojeni.md](docs/max3491-rx-only-zapojeni.md) | Alternativní RX-only zapojení s MAX3491 |
| [docs/poznamky-z-technickeho-centra-jablotron.md](docs/poznamky-z-technickeho-centra-jablotron.md) | Informace od technické podpory Jablotronu |
| [docs/Registr modbus.pdf](docs/Registr%20modbus.pdf) | Veřejná Modbus mapa Futury od výrobce |
