**Česky** | [English](pi-zero-konfigurace.en.md)

# Pi Zero konfigurace

Tento dokument popisuje soubory:

- `~/futura/pi-zero-config.json`
- `~/futura/damper-map.json`

Je napsaný tak, aby podle něj dokázal člověk bez větších linuxových zkušeností nakonfigurovat bridge na `Pi Zero` pro klapky.

## Co je co

Používají se dva soubory:

1. `pi-zero-config.json`
   Řídicí nastavení programu. Určuje, na jakém sériovém portu má číst, jestli má zapnout HTTP API, jestli má použít MQTT, kam má ukládat stav a jestli má vytvářet ladicí log.
2. `damper-map.json`
   Popis konkrétní instalace. Říká, která `slave_id` patří ke které místnosti a o jaké klapky jde.

Bez `damper-map.json` bridge neví, že třeba `slave_id 66` je `Pracovna / přívod / zóna 3 / klapka 1`.

## Kde se vezmou výchozí soubory

V repozitáři jsou vzory:

- [../src/sniffer/pi-zero-config.example.json](../src/sniffer/pi-zero-config.example.json)
- [../src/sniffer/damper-map.example.json](../src/sniffer/damper-map.example.json)

Na `Pi Zero` se z nich vytvoří produkční soubory:

```bash
cd ~/futura
cp pi-zero-config.example.json pi-zero-config.json
cp damper-map.example.json damper-map.json
```

Pokud už tyto soubory v `~/futura` máte, znovu je nekopírujte přes existující verzi bez zálohy.

## Jak soubor upravovat

Nejjednodušší je použít editor `nano`:

```bash
nano ~/futura/pi-zero-config.json
```

Uložení v `nano`:

- `Ctrl+O`
- `Enter`
- `Ctrl+X`

Stejně tak pro mapu klapek:

```bash
nano ~/futura/damper-map.json
```

## Důležitá poznámka k JSON

Soubor `json`:

- nesmí obsahovat komentáře,
- za poslední položkou nesmí být navíc čárka,
- `true`, `false` a `null` musí být malými písmeny.

Rychlá kontrola, jestli je `JSON` syntakticky v pořádku:

```bash
python -m json.tool ~/futura/pi-zero-config.json > /dev/null && echo OK
python -m json.tool ~/futura/damper-map.json > /dev/null && echo OK
```

Když je soubor rozbitý, `python -m json.tool` vypíše chybu a nevrátí `OK`.

## Minimální bezpečné nastavení pro první start

Pro první spuštění doporučuji:

- `mqtt.enabled` nechat na `false`
- `http.enabled` nechat na `true`
- `http.listen_host` nechat na `127.0.0.1`
- `debug.raw_log_enabled` nechat na `false`
- `storage.snapshot_interval_seconds` nechat na `60`

To je nejbezpečnější start:

- bridge poběží jen lokálně na `Pi`,
- nebude nic posílat do `MQTT`,
- nebude zbytečně zapisovat velký debug log,
- a půjde ověřit přes lokální `curl`.

## Podrobný popis `pi-zero-config.json`

Výchozí obsah vypadá takto:

```json
{
  "serial": {
    "port": "/dev/serial0",
    "baudrate": 19200,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "serial_timeout_seconds": 0.001,
    "frame_gap_ms": 3.0
  },
  "http": {
    "enabled": true,
    "listen_host": "127.0.0.1",
    "listen_port": 8765
  },
  "mqtt": {
    "enabled": false,
    "host": "127.0.0.1",
    "port": 1883,
    "username": null,
    "password": null,
    "client_id": "futura-zero",
    "topic_prefix": "futura",
    "discovery_prefix": "homeassistant",
    "retain": true,
    "qos": 1,
    "publish_on_change_only": true
  },
  "storage": {
    "state_path": "state/dampers_state.json",
    "snapshot_interval_seconds": 60,
    "restore_state_on_start": true,
    "write_state_on_shutdown": true
  },
  "debug": {
    "raw_log_enabled": false,
    "raw_log_path": "debug/raw.jsonl",
    "raw_log_rotate_bytes": 5242880,
    "raw_log_keep_files": 5,
    "raw_log_compress_rotated": true
  },
  "damper_map": {
    "path": "damper-map.json"
  }
}
```

### Sekce `serial`

Tady se nastavuje sériová linka `RS485`.

#### `port`

Typická hodnota:

```json
"/dev/serial0"
```

Co to dělá:

- určuje, jaký UART port má bridge otevřít

Co doporučuji:

- na `Raspberry Pi Zero 2 W` nechte `/dev/serial0`

Kdy měnit:

- jen pokud víte, že máte UART vystavený jinam

#### Jak zjistit, jestli je `/dev/serial0` správně

Pro doporučené zapojení v tomto projektu platí:

- pokud je `RS485` převodník připojený na piny `GPIO14/GPIO15` na `Pi Zero`,
- a máte správně povolený UART,
- používejte skoro vždy `/dev/serial0`

`/dev/serial0` je na Raspberry Pi doporučený stabilní alias na primární sériový port.

Po rebootu zkontrolujte:

```bash
ls -l /dev/serial0
```

Když je vše v pořádku, uvidíte, že `serial0` ukazuje na skutečné zařízení, typicky:

- `/dev/ttyAMA0`
- nebo `/dev/ttyS0`

Pro detail můžete zobrazit obě možnosti:

```bash
ls -l /dev/ttyAMA0 /dev/ttyS0 2>/dev/null
```

Rychlý praktický postup:

1. pokud existuje `/dev/serial0`, použijte v konfiguraci:

```json
"/dev/serial0"
```

2. pokud `/dev/serial0` neexistuje, nejdřív opravte nastavení UART podle [pi-zero-2w-rs485-sniffer.md](pi-zero-2w-rs485-sniffer.md)
3. teprve pokud vědomě nepoužíváte GPIO UART, ale jiný adaptér, změňte `port`

#### Kdy se `port` mění

`port` změňte jen v těchto případech:

- nepoužíváte GPIO UART na `Pi`, ale `USB-RS485` převodník
- víte, že vaše instalace záměrně používá jiné sériové zařízení

Typické alternativy:

- `/dev/ttyUSB0`
- `/dev/ttyUSB1`
- `/dev/ttyACM0`

Když použijete `USB-RS485` adaptér, zjistíte jeho jméno takto:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

V tom případě do konfigurace nastavte nalezené zařízení, například:

```json
"/dev/ttyUSB0"
```

#### Co dělat, když `/dev/serial0` chybí

Nejdřív ověřte, že je UART povolený:

```bash
grep -E "enable_uart=1|dtoverlay=disable-bt" /boot/firmware/config.txt
```

A že login shell neběží na sériové lince:

```bash
sudo raspi-config
```

V `raspi-config` má být:

1. `Interface Options` -> `Serial Port`
2. `Login shell over serial?` -> `No`
3. `Enable serial hardware?` -> `Yes`

Pak proveďte restart:

```bash
sudo reboot
```

#### `baudrate`

Typická hodnota:

```json
19200
```

Co to dělá:

- určuje rychlost komunikace na sběrnici

Co doporučuji:

- nechat `19200`, pokud jste už při odposlechu neověřili jinou hodnotu

#### `bytesize`

Typická hodnota:

```json
8
```

Co to dělá:

- počet datových bitů

Co doporučuji:

- nechat `8`

#### `parity`

Typická hodnota:

```json
"N"
```

Možné hodnoty:

- `"N"` = bez parity
- `"E"` = sudá parita
- `"O"` = lichá parita

Co doporučuji:

- nechat `"N"`, pokud už bylo ověřeno `19200 8N1`

#### `stopbits`

Typická hodnota:

```json
1
```

Co to dělá:

- počet stop bitů sériové komunikace

Co doporučuji:

- nechat `1`

#### `serial_timeout_seconds`

Typická hodnota:

```json
0.001
```

Co to dělá:

- jak dlouho čeká jedno čtení na bajty ze sériové linky

Co doporučuji:

- nechat `0.001`

Kdy měnit:

- skoro nikdy

#### `frame_gap_ms`

Typická hodnota:

```json
3.0
```

Co to dělá:

- pomáhá určit, kdy končí jeden `Modbus RTU` rámec a začíná další

Co doporučuji:

- nechat `3.0`

Kdy měnit:

- jen když děláte hlubší ladění parseru

### Sekce `http`

Tady se nastavuje lokální HTTP API bridge.

#### `enabled`

Typická hodnota:

```json
true
```

Co to dělá:

- zapíná nebo vypíná HTTP endpointy jako `/health` a `/dampers`

Co doporučuji:

- nechat `true`

#### `listen_host`

Typická hodnota:

```json
"127.0.0.1"
```

Co to dělá:

- určuje, odkud půjde na API přistupovat

Možnosti:

- `"127.0.0.1"` = jen ze stejného `Pi`
- `"0.0.0.0"` = z celé lokální sítě

Bezpečný první start:

- nechat `"127.0.0.1"`

Kdy změnit na `"0.0.0.0"`:

- až když chcete API otevřít z jiného počítače v síti

#### `listen_port`

Typická hodnota:

```json
8765
```

Co to dělá:

- port HTTP API

Co doporučuji:

- nechat `8765`

### Sekce `mqtt`

Tady se nastavuje volitelná publikace do `MQTT`.

#### `enabled`

Typická hodnota:

```json
false
```

Co to dělá:

- zapíná nebo vypíná `MQTT`

Co doporučuji:

- pro první start nechat `false`
- zapnout až když máte potvrzený běžící broker

#### `host`

Typická hodnota:

```json
"127.0.0.1"
```

Co to dělá:

- adresa `MQTT` brokeru

Příklady:

- `"127.0.0.1"` kdyby broker běžel na stejném stroji
- `"192.168.1.10"` když broker běží na jiném stroji v LAN

#### `port`

Typická hodnota:

```json
1883
```

Co to dělá:

- port `MQTT` brokeru

#### `username`

Typická hodnota:

```json
null
```

Co to dělá:

- uživatelské jméno pro `MQTT`

Kdy použít:

- jen když broker vyžaduje přihlášení

#### `password`

Typická hodnota:

```json
null
```

Co to dělá:

- heslo pro `MQTT`

#### `client_id`

Typická hodnota:

```json
"futura-zero"
```

Co to dělá:

- identifikátor klienta v `MQTT`

Co doporučuji:

- nechat takto, nebo změnit na jméno konkrétního zařízení

#### `topic_prefix`

Typická hodnota:

```json
"futura"
```

Co to dělá:

- prefix všech `MQTT` topiců

Příklad:

- klapka `66` se pak bude publikovat pod topic podobný `futura/damper/66/state`

#### `discovery_prefix`

Typická hodnota:

```json
"homeassistant"
```

Co to dělá:

- prefix pro MQTT Discovery topiky, přes které bridge automaticky vytváří entity v Home Assistant
- bridge publikuje discovery config na topiky typu `homeassistant/sensor/futura_damper_66_target_position/config`

Kdy měnit:

- jen pokud máte v Home Assistant změněný discovery prefix v nastavení MQTT integrace
- výchozí hodnota `homeassistant` odpovídá výchozímu nastavení Home Assistant

#### `retain`

Typická hodnota:

```json
true
```

Co to dělá:

- říká brokeru, aby si pamatoval poslední známý stav

Co doporučuji:

- nechat `true`

#### `qos`

Typická hodnota:

```json
1
```

Co to dělá:

- úroveň potvrzení `MQTT` zprávy

Co doporučuji:

- nechat `1`

#### `publish_on_change_only`

Typická hodnota:

```json
true
```

Co to dělá:

- publikuje jen při změně stavu, ne při každém opakování stejné hodnoty

Co doporučuji:

- nechat `true`

### Sekce `storage`

Tady se nastavuje lokální uložení malého snapshotu stavu.

#### `state_path`

Typická hodnota:

```json
"state/dampers_state.json"
```

Co to dělá:

- cesta k malému stavovému souboru

Důležité:

- relativní cesta je vždy vzhledem k umístění `pi-zero-config.json`

Co doporučuji:

- nechat `state/dampers_state.json`

#### `snapshot_interval_seconds`

Typická hodnota:

```json
60
```

Co to dělá:

- jak často se smí přepsat snapshot na disk, když je stav změněný

Co doporučuji:

- nechat `60`

Proč:

- je to šetrnější k `SD` kartě

#### `restore_state_on_start`

Typická hodnota:

```json
true
```

Co to dělá:

- po startu bridge zkusí načíst poslední snapshot

Co doporučuji:

- nechat `true`

#### `write_state_on_shutdown`

Typická hodnota:

```json
true
```

Co to dělá:

- při korektním ukončení procesu uloží poslední stav

Co doporučuji:

- nechat `true`

### Sekce `debug`

Tady se nastavuje ladicí raw log.

#### `raw_log_enabled`

Typická hodnota:

```json
false
```

Co to dělá:

- zapíná nebo vypíná surový diagnostický log rámců

Co doporučuji:

- v běžném provozu nechat `false`

Kdy zapnout:

- jen při ladění nebo reverzní analýze

#### `raw_log_path`

Typická hodnota:

```json
"debug/raw.jsonl"
```

Co to dělá:

- cesta k debug logu

#### `raw_log_rotate_bytes`

Typická hodnota:

```json
5242880
```

Co to dělá:

- velikost jednoho log souboru v bajtech

`5242880` je zhruba `5 MB`.

#### `raw_log_keep_files`

Typická hodnota:

```json
5
```

Co to dělá:

- kolik posledních otočených logů se má nechat

#### `raw_log_compress_rotated`

Typická hodnota:

```json
true
```

Co to dělá:

- staré rotované logy se po otočení komprimují do `gzip`

Co doporučuji:

- nechat `true`

### Sekce `damper_map`

#### `path`

Typická hodnota:

```json
"damper-map.json"
```

Co to dělá:

- cesta k souboru s mapou klapek

Co doporučuji:

- v `~/futura` nechat `damper-map.json`

## Podrobný popis `damper-map.json`

Každá položka v poli `dampers` popisuje jednu klapku.

Příklad:

```json
{
  "slave_id": 66,
  "room": "Pracovna",
  "label": "Pracovna privod 1",
  "enabled": true,
  "notes": null
}
```

### `slave_id`

- číslo klapky na `RS485 / Modbus RTU`
- musí odpovídat skutečně zmapovaným klapkám
- pro běžné klapky VarioBreeze je to primární adresní klíč
- pokud `zone`, `type` nebo `damper_index` chybí, bridge je odvodí z `slave_id`

Pro běžnou klapku platí:

```text
offset = slave_id - 64
zone = (offset & 0b111) + 1
damper_index = ((offset >> 3) & 0b11) + 1
type = "odtah" if (offset & 0b100000) else "privod"
```

Tohle odvozování platí jen pro běžné klapky VarioBreeze, ne pro `ALFA` nebo jiné `RS485` uzly s jiným adresním rozsahem.

### `room`

- lidský název místnosti
- bude se vracet v API a v případném `MQTT`

### `zone`

- číslo zóny ve Futuře
- pro běžné klapky volitelné
- pokud je uvedené, musí odpovídat hodnotě odvozené ze `slave_id`

### `type`

Povolené hodnoty:

- `"privod"`
- `"odtah"`
- pro běžné klapky volitelné
- pokud je uvedené, musí odpovídat hodnotě odvozené ze `slave_id`

### `damper_index`

- pořadí klapky v rámci dané místnosti nebo zóny
- pro běžné klapky volitelné
- pokud je uvedené, musí odpovídat hodnotě odvozené ze `slave_id`

### `label`

- čitelný název klapky
- pokud chybí, bridge ho sestaví z `room`, odvozeného `type` a odvozeného `damper_index`

### `enabled`

- `true` = klapka je aktivní, bridge ji sleduje, publikuje do MQTT a vytváří pro ni entity v Home Assistant
- `false` = záznam je v mapě, ale bridge ho nepublikuje do MQTT a nevytváří pro něj discovery entity v Home Assistant

To je užitečné, když si chcete klapku v mapě nechat poznamenanou, ale dočasně ji nepublikovat.

Důležité: pokud klapku přepnete z `true` na `false`, bridge přestane posílat nová data a nevytvoří pro ni discovery při dalším připojení. Ale entity, které už v Home Assistant existují, se automaticky nesmažou. Pokud je chcete odstranit, musíte je smazat ručně v HA v `Settings` -> `Devices & Services` -> `MQTT` -> zařízení `Futura VarioBreeze`.

### `notes`

- volitelná poznámka
- může být text nebo `null`

## Co instalatér obvykle mění

Ve většině instalací bude potřeba změnit jen:

1. `mqtt.enabled`
2. `mqtt.host`
3. pripadne `mqtt.username` a `mqtt.password`
4. `http.listen_host`, pokud má být API vidět z LAN
5. obsah `damper-map.json`, pokud jde o jinou instalaci

Naopak bezdůvodně neměňte:

- `serial_timeout_seconds`
- `frame_gap_ms`
- `snapshot_interval_seconds`
- `raw_log_rotate_bytes`
- `raw_log_keep_files`

## Doporučený postup pro člověka bez linux zkušeností

1. Zkopírovat vzory:

```bash
cd ~/futura
cp pi-zero-config.example.json pi-zero-config.json
cp damper-map.example.json damper-map.json
```

2. Otevřít konfiguraci:

```bash
nano ~/futura/pi-zero-config.json
```

3. Pro první start zkontrolovat jen:

- `serial.port` je `/dev/serial0`
- `http.enabled` je `true`
- `http.listen_host` je `127.0.0.1`
- `mqtt.enabled` je `false`

4. Otevřít mapu klapek:

```bash
nano ~/futura/damper-map.json
```

5. Zkontrolovat, že `slave_id` odpovídají skutečné instalaci.

6. Ověřit syntaxi:

```bash
python -m json.tool ~/futura/pi-zero-config.json > /dev/null && echo OK
python -m json.tool ~/futura/damper-map.json > /dev/null && echo OK
```

7. Spustit bridge:

```bash
cd ~/futura
source .venv/bin/activate
python futura_damper_bridge.py --config pi-zero-config.json
```

8. V druhém terminálu zkontrolovat:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

## Nejběžnější chyby

### Bridge hlásí chybu konfigurace

Nejčastěji:

- chyba carky v `JSON`
- překlep v `true/false/null`
- špatná cesta v `damper_map.path`

### API neodpovídá

Nejčastěji:

- bridge neni spusteny
- `http.enabled` je `false`
- port `8765` používá jiný proces

### MQTT nefunguje

Nejčastěji:

- `mqtt.enabled` je stale `false`
- špatná IP adresa brokeru
- broker vyzaduje login a neni vyplnene `username` a `password`

### Neobjevují se data o klapkách

Nejčastěji:

- špatné nastavení UART na `Pi`
- špatně zapojené `A/B`
- bridge běží, ale v `damper-map.json` chybí správné `slave_id`

## Související dokumenty

- [Plán nasazení Pi Zero 2 W pro RS485 sniffer](pi-zero-2w-rs485-sniffer.md)
- [Navrh architektury pro Pi Zero](navrh-architektury-pi-zero.md)
- [Mapa klapek a reverzní analýza sběrnice](mapa-klapek.md)
