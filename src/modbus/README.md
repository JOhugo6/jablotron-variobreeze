# Modbus TCP

Tato složka je vyhrazená jen pro přímou práci s `Modbus TCP`.

Není určená pro `RS485` sniffing ani pro analýzu interní `Modbus RTU` komunikace.

## Účel

Modbus TCP část projektu je určená pro:

- přímé čtení registrů z Futury přes síť
- práci s veřejně dostupnou `Modbus TCP` mapou
- discovery hledání kandidátů na registry poloh
- ověřování hypotetických registrů bez pasivního sniffingu

## Skripty

### `futura_variobreeze.py`

CLI nástroj pro čtení dat z Futury přes `Modbus TCP`.

Umí:

- načíst připojené přívodní a odtahové klapky
- číst konfigurované registry poloh
- spustit discovery režim nad zvoleným rozsahem registrů
- pracovat s konfigurovatelným `config.json`

Typické použití:

```bash
python src/modbus/futura_variobreeze.py --config src/modbus/config.json --once
```

## Závislosti

Python závislosti této části jsou v:

- [requirements.txt](requirements.txt)

Instalace:

```bash
pip install -r src/modbus/requirements.txt
```

## Konfigurace

Tato část repozitáře používá vlastní konfiguraci:

- [config.example.json](config.example.json)
- `src/modbus/config.json` jako lokální kopii vzoru pro konkrétní prostředí

To je odlišné od `Pi Zero` sniffing vrstvy, která má mít vlastní konfiguraci:

- [pi-zero-config.example.json](../sniffer/pi-zero-config.example.json)
- [damper-map.example.json](../sniffer/damper-map.example.json)

## Poznámka k rozdělení

Praktické pravidlo je:

- `src/modbus` = přímé `Modbus TCP` nástroje
- `src/sniffer` = pasivní `RS485` sniffing a analýza zachycené interní `Modbus RTU` komunikace

## Spouštění

Modbus TCP nástroj se spouští přímo z této složky přes cestu `src/modbus/futura_variobreeze.py`.
