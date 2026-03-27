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
4. teprve potom pokračovat podle sekce `Co udělat dál po zapojení a instalaci systému`

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

## Co udělat dál po zapojení a instalaci systému

1. Přihlaste se na `Pi Zero` přes `SSH`.
   Pokud nevíte, jak na to, použijte na Windows program `PuTTY`.

   V `PuTTY` nastavte:

   - `Host Name (or IP address)`:
     - například `futura-sniffer.local`, pokud jste v `Raspberry Pi Imager` nastavili `hostname` na `futura-sniffer`
     - nebo přímo IP adresu, například `192.168.1.50`
     - případně i tvar `uzivatel@futura-sniffer.local` nebo `uzivatel@192.168.1.50`
   - `Port`: `22`
   - `Connection type`: `SSH`

   Pak klikněte na `Open`.

   Důležité:

   - `uzivatel` je jméno, které jste zadali při instalaci systému v `Raspberry Pi Imager`
   - pokud do pole `Host Name` zadáte jen adresu, například `192.168.1.50`, `PuTTY` se vás na uživatelské jméno zeptá po připojení
   - pokud zadáte tvar `uzivatel@192.168.1.50`, je uživatelské jméno součástí adresy

   Správný formát adresy je tedy:

   - `futura-sniffer.local`
   - `192.168.1.50`
   - `uzivatel@futura-sniffer.local`
   - `uzivatel@192.168.1.50`

   Příklad:

   - pokud jste při instalaci nastavili uživatele `zero`, použijete třeba `zero@192.168.1.50`
   - pokud jste nastavili uživatele `futura`, použijete třeba `futura@192.168.1.50`

   Pokud nevíte IP adresu `Pi Zero`, nejčastěji ji zjistíte:

   - v seznamu zařízení nebo `DHCP leases` ve vašem routeru
   - nebo zkuste v `PuTTY` rovnou `hostname.local`, například `futura-sniffer.local`
2. Otevřete [Plán nasazení Pi Zero 2 W pro RS485 sniffer](docs/pi-zero-2w-rs485-sniffer.md) a projděte sekce:
   - `Instalace SW na Raspberry Pi`
   - `Instalace monitoru`
   - `Produkční spuštění bridge`
3. Otevřete [Pi Zero konfigurace a vysvětlení nastavení](docs/pi-zero-konfigurace.md) a podle ní upravte:
   - `pi-zero-config.json`
   - `damper-map.json`
4. Spusťte na `Pi Zero` nejdřív bridge ručně a ověřte:
   - `curl http://127.0.0.1:8765/health`
   - `curl http://127.0.0.1:8765/dampers`
5. Teprve když ruční spuštění funguje, nastavte spuštění jako `systemd` službu.

Pokud chcete nejkratší možnou cestu:

- instalace a spuštění na `Pi Zero` je v [docs/pi-zero-2w-rs485-sniffer.md](docs/pi-zero-2w-rs485-sniffer.md)
- význam všech položek v `pi-zero-config.json` je v [docs/pi-zero-konfigurace.md](docs/pi-zero-konfigurace.md)
- provozní popis bridge je v [src/sniffer/README.md](src/sniffer/README.md)

## Poznámky

- Root `README` je záměrně jen stručný přehled. Detailní návody jsou v podsložkách.
- Každá část má vlastní `README.md`, `requirements.txt` a vzorové konfigurace.
- Detailní technické závěry o mapování klapek a registrech jsou udržované v [docs/mapa-klapek.md](docs/mapa-klapek.md).
- Jak ověřit běžící procesy na `Pi Zero` je popsané v [src/sniffer/README.md](src/sniffer/README.md).
- Podrobný popis `pi-zero-config.json` a `damper-map.json` je v [docs/pi-zero-konfigurace.md](docs/pi-zero-konfigurace.md).
