# Futura VarioBreeze

Repozitář je rozdělený na dvě samostatné části:

- `src/modbus`
  Přímé nástroje pro `Modbus TCP`.
- `src/sniffer`
  Pasivní odposlech interní `RS485` komunikace Futury, která je na protokolové úrovni dekódovaná jako `Modbus RTU`.

## Rozcestník

- [Modbus TCP část](src/modbus/README.md)
- [RS485 sniffer část](src/sniffer/README.md)
- [Mapa klapek a reverzní analýza sběrnice](docs/mapa-klapek.md)
- [Cíl integrace s Home Assistant](docs/cil-home-assistant.md)
- [Návrh architektury pro Pi Zero](docs/navrh-architektury-pi-zero.md)
- [Plán nasazení Pi Zero 2 W pro RS485 sniffer](docs/pi-zero-2w-rs485-sniffer.md)
- [Pi Zero konfigurace a vysvětlení nastavení](docs/pi-zero-konfigurace.md)
- [Veřejná Modbus mapa Futury](docs/Registr%20modbus.pdf)

## Struktura repozitáře

- `src/modbus`
  Skripty, konfigurace a závislosti pro `Modbus TCP`.
- `src/sniffer`
  Skripty, konfigurace a závislosti pro pasivní odposlech `RS485`.
- `docs`
  Technická dokumentace, zapojení a pracovní závěry.

## RS485 sniffer: HW a zapojení

Pro pasivní odposlech interní `RS485` sběrnice Futury je aktuálně doporučená tato varianta:

- `Raspberry Pi Zero 2 W` nebo `Zero 2 WH`
- `Waveshare TTL TO RS485 (B)`
- `microSD` karta s `Raspberry Pi OS Lite (64-bit)`
- stabilní `5V` napájení pro Pi
- krátké propojky mezi Pi a převodníkem

Doporučený systém pro `Pi Zero`:

- `Raspberry Pi OS Lite (64-bit)`
- nahraný přes `Raspberry Pi Imager`

Při přípravě karty v `Raspberry Pi Imager` použijte předvolby systému:

- nastavte `hostname`, například `futura-sniffer`
- vytvořte uživatele a heslo
- vyplňte `Wi-Fi` síť a heslo, pokud nebude `Pi` připojené kabelem
- zapněte `SSH`
- nastavte časové pásmo a rozložení klávesnice

První praktický postup je:

1. nahrát `Raspberry Pi OS Lite (64-bit)` na `microSD`
2. při zápisu vyplnit uvedené předvolby
3. vložit kartu do `Pi Zero` a zapnout ho
4. přihlásit se přes `SSH`
5. teprve potom řešit `UART`, zapojení převodníku a spuštění snifferu

Základní princip zapojení je pasivní:

- `Pi pin 1 (3V3)` -> `VCC`
- `Pi pin 6 (GND)` -> `GND`
- `Pi pin 10 (RXD0)` <- `TXD` z modulu
- `Pi pin 8 (TXD0)` nezapojovat
- `modul RXD` nezapojovat
- `A+` -> `A` na Futuře
- `B-` -> `B` na Futuře
- `SGND` jen volitelně, pokud je na Futuře jasně označená komunikační zem
- `120R` na modulu nechat `OFF`

Tato varianta je určená jen pro čtení. `Pi` má pouze poslouchat, ne vysílat do sběrnice.

Pro produkční běh na `Pi Zero` je připraven [src/sniffer/futura_damper_bridge.py](src/sniffer/futura_damper_bridge.py). Diagnostický [src/sniffer/rs485_modbus_monitor.py](src/sniffer/rs485_modbus_monitor.py) zůstává pro reverzní analýzu a ladění. Na Zero se počítá s plochým nasazením v `~/futura`.

Podrobné návody:

- [Plán nasazení Pi Zero 2 W pro RS485 sniffer](docs/pi-zero-2w-rs485-sniffer.md)
- [Pi Zero konfigurace a vysvětlení nastavení](docs/pi-zero-konfigurace.md)
- [Waveshare TTL TO RS485 (B) zapojení](docs/waveshare-ttl-to-rs485-b-zapojeni.md)
- [MAX3491 RX-only alternativa](docs/max3491-rx-only-zapojeni.md)

## Poznámky

- Root `README` je záměrně jen stručný přehled. Detailní návody jsou v podsložkách.
- Každá část má vlastní `README.md`, `requirements.txt` a vzorové konfigurace.
- Detailní technické závěry o mapování klapek a registrech jsou udržované v [docs/mapa-klapek.md](docs/mapa-klapek.md).
- Jak ověřit běžící procesy na `Pi Zero` je popsané v [src/sniffer/README.md](src/sniffer/README.md).
- Podrobný popis `pi-zero-config.json` a `damper-map.json` je v [docs/pi-zero-konfigurace.md](docs/pi-zero-konfigurace.md).
