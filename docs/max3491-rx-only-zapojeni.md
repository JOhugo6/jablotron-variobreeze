# MAX3491 RX-only zapojení

Poznámka:

- tohle je pokročilejší varianta s vlastním pájením
- aktuálně doporučená finální varianta s menším montážním rizikem je [waveshare-ttl-to-rs485-b-zapojeni.md](waveshare-ttl-to-rs485-b-zapojeni.md)

## Cíl

Tahle varianta je navržená tak, aby `Raspberry Pi Zero 2 W` fyzicky neumělo vysílat do `RS-485` sběrnice Futury. `Pi` bude pouze poslouchat data z interní komunikace `Futura <-> VarioBreeze`.

Princip:

- `MAX3491` použijeme jen jako přijímač
- výstup vysílače `Y/Z` zůstane nezapojený
- vstup vysílače `DI` zůstane nezapojený
- `DE` bude natvrdo na `GND`, takže vysílač bude trvale zakázaný
- `RE` bude natvrdo na `GND`, takže přijímač bude trvale povolený
- `TX` pin Raspberry Pi se nepřipojí vůbec

## Jednodušší alternativa bez SMD pájení

Pokud nechceš pájet `SOIC-14` čip na adaptér, existuje jednodušší varianta:

- hotový `3.3V RS-485` modul s čipem `SP3485` nebo `MAX3485`
- ideálně s vyvedenými piny `RO`, `DI`, `RE`, `DE`, `VCC`, `GND`, `A`, `B`
- nebo modul s jedním směrovým pinem typu `RSE`

Pro tuhle variantu už není potřeba pájet `MAX3491`. Prakticky jen propojíš vodiče.

### Doporučené zapojení hotového modulu

Pokud má modul samostatné piny `RE` a `DE`:

- `RO -> Pi pin 10`
- `RE -> GND`
- `DE -> GND`
- `DI -> nezapojovat`
- `VCC -> Pi pin 1 (3V3)`
- `GND -> Pi GND`
- `A -> A na Futuře`
- `B -> B na Futuře`
- `Pi pin 8 (TX) -> nezapojovat`

Pokud má modul jeden společný směrový pin `RSE`:

- `RO -> Pi pin 10`
- `RSE -> GND`
- `DI -> nezapojovat`
- `VCC -> Pi pin 1 (3V3)`
- `GND -> Pi GND`
- `A -> A na Futuře`
- `B -> B na Futuře`
- `Pi pin 8 (TX) -> nezapojovat`

### Kdy zvolit tuhle variantu

Tuhle variantu ber, pokud je pro tebe důležitější:

- menší riziko při montáži
- nulové SMD pájení
- rychlejší první zprovoznění

Varianta s `MAX3491` je pořád nejčistší `RX-only`, ale hotový modul je pro běžnou montáž obvykle rozumnější.

## Co mít kromě hlavního HW

K hlavnímu nákupnímu seznamu doporučuji přidat ještě:

1. `100 nF keramický kondenzátor`
   Použije se jako blokovací kondenzátor mezi `VCC` a `GND` přímo u `MAX3491`.
2. `Smršťovací bužírku` nebo izolační pásku
   Na mechanické zajištění odhalených vodičů.
3. `Jemný vodič` na propojky na adaptéru
   Stačí krátké kusy izolovaného vodiče.
4. `Multimetr`
   Na kontrolu zkratů a ověření, že `TX` opravdu není nikam připojený.

## Orientace čipu a adaptéru

Použij `MAX3491ECSD+` v pouzdru `SOIC-14` a `SO14 -> DIP14` adaptér.

Při pájení sleduj dva orientační znaky:

- na čipu je `tečka` nebo `zářez`, který označuje `pin 1`
- na adaptéru bývá `pin 1` označen tečkou, čtvercovou ploškou nebo číslem `1`

Čip musí být na adaptéru orientovaný tak, aby `pin 1` čipu seděl na `pin 1` adaptéru.

## Pinout MAX3491

Pohled shora na čip `MAX3491`, zářez nebo tečka nahoře:

```text
            ┌───────────────┐
   NC    1  │ o           14│  VCC
   RO    2  │             13│  VCC
   RE    3  │             12│  A
   DE    4  │             11│  B
   DI    5  │             10│  Z
   GND   6  │              9│  Y
   GND   7  │              8│  NC
            └───────────────┘
```

Význam pinů pro náš projekt:

- `2 RO`: TTL výstup přijímače, půjde do `Pi RX`
- `3 RE`: povolení přijímače, aktivní v `0`, dáme trvale na `GND`
- `4 DE`: povolení vysílače, aktivní v `1`, dáme trvale na `GND`
- `5 DI`: TTL vstup vysílače, necháme nezapojený
- `6 GND`, `7 GND`: zem
- `11 B`, `12 A`: diferenciální vstup přijímače z `RS-485` sběrnice
- `13 VCC`, `14 VCC`: napájení `3.3 V`
- `9 Y`, `10 Z`: výstup vysílače, necháme nezapojený

Tohle odpovídá oficiálnímu datasheetu `MAX3491`, Figure 3 a package drawing.

## Přesné propojky na adaptéru

Na adaptéru udělej tyto pevné propojky:

1. `pin 13 -> pin 14`
   Oba `VCC` piny spojit dohromady.
2. `pin 6 -> pin 7`
   Oba `GND` piny spojit dohromady.
3. `pin 3 -> GND`
   Nejjednodušší je propojit `pin 3` s `pin 6`.
4. `pin 4 -> GND`
   Nejjednodušší je propojit `pin 4` s `pin 7`.
5. `100 nF` kondenzátor mezi `VCC` a `GND`
   Prakticky mezi dvojici `pin 13/14` a dvojici `pin 6/7`, co nejblíž k čipu.

Nepřipojovat:

- `pin 1`
- `pin 5`
- `pin 8`
- `pin 9`
- `pin 10`

## Schéma pájení na adaptéru

Prakticky to po zapojení má vypadat takto:

```text
TOP VIEW

            ┌───────────────┐
   NC    1  │ o           14│--+-- 3V3 z Pi
   RO    2  │             13│--+
   RE    3  │--+
   DE    4  │--+              12│---- A na Futuře
   DI    5  │                  11│---- B na Futuře
   GND   6  │--+               10│---- nezapojovat
   GND   7  │--+                9│---- nezapojovat
            └───────────────┘

RO  -> Pi pin 10
RE  -> GND
DE  -> GND
DI  -> nezapojovat
GND -> Pi GND
VCC -> Pi 3V3
A/B -> RS-485 sbernice Futury

100 nF kondenzator mezi VCC a GND
Pi TX pin 8 zustava odpojeny
```

## Přesné propojení na Raspberry Pi Zero 2 W

Použij pouze tyto fyzické piny na `40pin GPIO` headeru:

```text
Raspberry Pi Zero 2 W
Pohled shora na GPIO header

  3V3  (1) (2)  5V
 GPIO2 (3) (4)  5V
 GPIO3 (5) (6)  GND
 GPIO4 (7) (8)  GPIO14 / TXD0
   GND (9) (10) GPIO15 / RXD0
```

Pro náš sniffer použij:

- `pin 1` = `3V3`
- `pin 6` nebo `pin 9` = `GND`
- `pin 10` = `GPIO15 / RXD0`

Nepoužij:

- `pin 8` = `GPIO14 / TXD0`

## Přesná tabulka propojení

| MAX3491 pin | Signál | Kam vede |
|---|---|---|
| `2` | `RO` | `Pi pin 10` |
| `3` | `RE` | `GND` |
| `4` | `DE` | `GND` |
| `5` | `DI` | nezapojovat |
| `6` | `GND` | `Pi GND` |
| `7` | `GND` | spojit s `pin 6` |
| `11` | `B` | `RS-485 B` na Futuře |
| `12` | `A` | `RS-485 A` na Futuře |
| `13` | `VCC` | `Pi pin 1` |
| `14` | `VCC` | spojit s `pin 13` |
| `9` | `Y` | nezapojovat |
| `10` | `Z` | nezapojovat |

## Jak přesně pájet

Doporučené pořadí:

1. Přichyť `MAX3491` na adaptér správnou orientací podle `pin 1`.
2. Připájej nejdřív `pin 1` a `pin 8` nebo protilehlý roh, jen aby čip seděl rovně.
3. Připájej zbytek nožiček.
4. Pod lupou zkontroluj, že mezi sousedními piny není cínový most.
5. Na spodní stranu adaptéru udělej propojky:
   - `13-14`
   - `6-7`
   - `3-6`
   - `4-7`
6. Připájej `100 nF` kondenzátor mezi `VCC` a `GND`.
7. Připájej vodiče nebo pin header pro:
   - `RO`
   - `VCC`
   - `GND`
   - `A`
   - `B`

## Kontrola multimetrem před připojením k Futuře

Než to připojíš k jednotce, ověř:

1. `pin 13` a `pin 14` jsou vodivě spojené
2. `pin 6` a `pin 7` jsou vodivě spojené
3. `pin 3` je vodivě spojený s `GND`
4. `pin 4` je vodivě spojený s `GND`
5. `pin 5` není spojený s ničím
6. `pin 9` a `pin 10` nejsou spojené s ničím
7. mezi `VCC` a `GND` není tvrdý zkrat
8. `Pi pin 8` není nikam připojený

Pokud bod `8` neplatí, není to `RX-only` varianta.

## Připojení na Futura RS-485 sběrnici

Připojuj `paralelně`, ne do série.

Správně:

- `MAX3491 pin 12 (A)` -> `A` sběrnice Futury
- `MAX3491 pin 11 (B)` -> `B` sběrnice Futury
- `MAX3491 GND` -> `GND` nebo `COM` sběrnice, ale jen pokud je na komunikační svorkovnici jasně označený

Nikdy nepřipojuj:

- `24V`
- `0V` napájení, pokud není v dokumentaci nebo na svorkovnici výslovně označené jako komunikační `GND/COM`
- žádný vodič z `Pi TX`

Pokud má Futura jen `A/B` bez samostatného `GND/COM`, začni jen s `A/B`.

## Poznámka k označení A/B

U `RS-485` bývá značení `A/B` mezi výrobci nekonzistentní.

Proto:

- nejdřív zapoj podle popisku na Futuře
- pokud po spuštění nebudou vidět validní rámce a `CRC` nebude sedět, prohoď `A` a `B`

## Co musí zůstat odpojené

Tyto věci nesmí být nikam zapojené:

- `Pi pin 8`
- `MAX3491 pin 5`
- `MAX3491 pin 9`
- `MAX3491 pin 10`

To je klíčová bezpečnostní podmínka.

## Doporučené mechanické provedení

Nejpraktičtější je:

1. `MAX3491` na `SO14 -> DIP14` adaptéru
2. z adaptéru vyvést `5` vodičů:
   - `3V3`
   - `GND`
   - `RO`
   - `A`
   - `B`
3. spoj chránit bužírkou nebo malou krabičkou

Na straně Futury je vhodné mít odbočku:

- krátkou
- mechanicky pevnou
- bez dodatečné terminace

## Softwarová část po zapojení

Po hardwarovém zapojení na Pi:

1. povolit `UART`
2. ověřit `/dev/serial0`
3. spustit [rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)

První test:

```bash
python src/sniffer/rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 127.0.0.1 \
  --listen-port 8765
```

## Reference

1. Analog Devices `MAX3483-MAX3491` datasheet, Figure 3 a package drawing: https://www.analog.com/media/en/technical-documentation/data-sheets/MAX3483-MAX3491.pdf
2. Raspberry Pi dokumentace k `UART`, `serial0`, `GPIO14/GPIO15`: https://www.raspberrypi.com/documentation/computers/configuration.html
