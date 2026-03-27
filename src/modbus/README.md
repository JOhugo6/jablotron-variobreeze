**Česky** | [English](README.en.md)

# Modbus TCP

Tato složka je vyhrazená jen pro přímou práci s `Modbus TCP`.

Není určená pro `RS485` sniffing ani pro analýzu interní `Modbus RTU` komunikace.

## Účel

Modbus TCP část projektu je určená pro:

- přímé čtení registrů z Futury přes síť
- práci s veřejně dostupnou `Modbus TCP` mapou
- discovery hledání kandidátů na registry poloh
- průběžné sledování změn registrů v čase
- ověřování hypotetických registrů bez pasivního sniffingu

## Skripty

### `futura_variobreeze.py`

CLI nástroj pro čtení dat z Futury přes `Modbus TCP`.

Umí:

- načíst připojené přívodní a odtahové klapky (registry 70-73)
- číst konfigurované registry poloh s volitelným dělitelem škály
- spustit discovery režim nad zvoleným rozsahem registrů
- průběžně sledovat změny registrů a vypisovat jen rozdíly
- výstup v textovém nebo JSON formátu
- volitelně odemknout servisní registry přes access code
- pracovat s konfigurovatelným `config.json`

### Režimy spuštění

Skript má tři hlavní režimy:

#### 1. Čtení stavu klapek

Výchozí režim. Načte připojené klapky a jejich polohy z konfigurovaných registrů.

Jednorázové čtení:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once
```

Průběžné čtení s výchozím intervalem (5 sekund, konfigurovatelné v `config.json`):

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json
```

JSON výstup:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once --json
```

#### 2. Discovery režim

Prohledává zvolený rozsah registrů a hledá kandidáty, jejichž hodnoty se mění v rozsahu 0-100. Slouží k hledání neznámých registrů poloh klapek.

Doporučený postup:

1. Spusťte discovery nad vhodným rozsahem.
2. Během měření změňte stav zón nebo klapek v aplikaci Futura.
3. Sledujte registry, které se mění.

Příklad:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --discover \
  --discover-type input \
  --discover-start 900 \
  --discover-count 400 \
  --discover-samples 10 \
  --discover-interval 1
```

Parametry discovery:

| Parametr | Výchozí | Popis |
|---|---|---|
| `--discover-type` | `input` | Typ registrů: `input` nebo `holding` |
| `--discover-start` | `0` | Počáteční adresa |
| `--discover-count` | `500` | Počet registrů k prohledání |
| `--discover-samples` | `5` | Kolikrát přečíst celý rozsah |
| `--discover-interval` | `1.0` | Interval mezi vzorky v sekundách |
| `--discover-probe-count` | `2` | Kolik registrů číst v jednom dotazu (hodí se pro řídké mapy, kde ne všechny adresy odpovídají) |
| `--discover-min` | `0` | Minimální hodnota kandidáta (záporné číslo = bez filtru) |
| `--discover-max` | `100` | Maximální hodnota kandidáta (záporné číslo = bez filtru) |

Výstup je vždy JSON se seznamem kandidátních registrů seřazených podle počtu odlišných hodnot.

Pokud potřebujete odemknout servisní registry:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --access-code 12345 \
  --discover \
  --discover-start 900 \
  --discover-count 800
```

#### 3. Monitor změn

Průběžně čte zvolený rozsah registrů a vypisuje jen ty, které se od posledního čtení změnily. Vhodné pro sledování reakce registrů na změny v aplikaci Futura.

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --monitor \
  --monitor-type input \
  --monitor-start 0 \
  --monitor-count 100 \
  --monitor-interval 5
```

Parametry monitoru:

| Parametr | Výchozí | Popis |
|---|---|---|
| `--monitor-type` | `input` | Typ registrů: `input` nebo `holding` |
| `--monitor-start` | `0` | Počáteční adresa |
| `--monitor-count` | `100` | Počet registrů ke sledování |
| `--monitor-interval` | `5.0` | Interval mezi čteními v sekundách |
| `--monitor-probe-count` | `2` | Kolik registrů číst v jednom dotazu |
| `--monitor-cycles` | `0` | Počet cyklů, `0` = běží do přerušení (`Ctrl+C`) |

Pokud potřebujete odemknout servisní registry před monitorováním:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json \
  --access-code 12345 \
  --monitor \
  --monitor-start 900 \
  --monitor-count 200
```

Access code se v monitor režimu automaticky přeposílá před každým čtecím cyklem.

### Společné parametry

| Parametr | Popis |
|---|---|
| `--config` | Cesta ke konfiguračnímu JSON souboru. Výchozí: `config.example.json` vedle skriptu |
| `--once` | Načte jednou a skončí (jen v režimu čtení) |
| `--json` | Vynutí JSON výstup (jen v režimu čtení) |
| `--access-code` | Access code pro odemčení servisních registrů. Přepíše hodnotu z konfigurace |

## Závislosti

Python závislosti této části jsou v:

- [requirements.txt](requirements.txt)

Instalace:

```bash
pip install -r src/modbus/requirements.txt
```

## Konfigurace

Před prvním spuštěním zkopírujte vzorovou konfiguraci:

```bash
copy src\modbus\config.example.json src\modbus\config.json
```

Na Linuxu nebo Macu:

```bash
cp src/modbus/config.example.json src/modbus/config.json
```

Pak upravte `src/modbus/config.json` podle vaší instalace.

### Popis konfigurace

Vzorový soubor: [config.example.json](config.example.json)

#### `modbus`

| Položka | Výchozí | Popis |
|---|---|---|
| `host` | `192.168.1.50` | IP adresa Futury |
| `port` | `502` | Modbus TCP port |
| `device_id` | `1` | Modbus device ID |
| `timeout_seconds` | `3.0` | Timeout spojení v sekundách |

#### `service`

| Položka | Výchozí | Popis |
|---|---|---|
| `access_code` | `null` | Access code pro servisní registry. `null` = nepoužívat |
| `access_code_register` | `900` | Registr, do kterého se access code zapisuje |

#### `registers`

| Položka | Výchozí | Popis |
|---|---|---|
| `connected_supply_start` | `70` | Počáteční registr bitmasky připojených přívodních klapek (čte 2 registry jako uint32) |
| `connected_exhaust_start` | `72` | Počáteční registr bitmasky připojených odtahových klapek (čte 2 registry jako uint32) |
| `connected_word_order` | `low_high` | Pořadí slov v uint32: `low_high` nebo `high_low` |
| `position_source` | `input` | Typ registrů pro čtení poloh: `input` nebo `holding` |
| `position_scale_divisor` | `1.0` | Dělitel surové hodnoty polohy. Pokud Futura vrací 0-1000 místo 0-100, nastavte `10` |
| `supply_position_registers` | `{}` | Mapování čísla klapky na adresu registru polohy (přívodní) |
| `exhaust_position_registers` | `{}` | Mapování čísla klapky na adresu registru polohy (odtahové) |

Příklad mapování registrů poloh:

```json
"supply_position_registers": {
  "1": 1000,
  "2": 1001
}
```

To znamená: přívodní klapka č. 1 je v registru `1000`, klapka č. 2 v registru `1001`.

Mapování lze zadat i jako pole:

```json
"supply_position_registers": [1000, 1001]
```

V tom případě se klapky číslují automaticky od 1.

#### `poll`

| Položka | Výchozí | Popis |
|---|---|---|
| `interval_seconds` | `5.0` | Interval průběžného čtení v sekundách (bez `--once`) |

#### `output`

| Položka | Výchozí | Popis |
|---|---|---|
| `format` | `text` | Výchozí výstupní formát: `text` nebo `json`. Lze přepsat flagem `--json` |

### Poznámky ke konfiguraci

- Konfigurace se merguje přes výchozí hodnoty. Nemusíte vyplňovat všechny položky, stačí ty, které se liší od výchozích.
- `config.json` je v `.gitignore`. Do repozitáře se commituje jen `config.example.json`.
- Futura podporuje jen jedno současné Modbus TCP spojení. Pokud je připojený jiný klient, skript dostane `ConnectionResetError`.

## Poznámka k rozdělení

Praktické pravidlo je:

- `src/modbus` = přímé `Modbus TCP` nástroje
- `src/sniffer` = pasivní `RS485` sniffing a analýza zachycené interní `Modbus RTU` komunikace
