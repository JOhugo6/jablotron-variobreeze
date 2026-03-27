# Waveshare TTL TO RS485 (B) zapojení

## Vybraný modul

Pro tenhle projekt je to aktuálně nejrozumnější kompromis mezi:

- bezpečností sběrnice
- jednoduchostí montáže
- malým počtem chyb při zapojení

Vybraný modul:

- `Waveshare TTL TO RS485 (B)`

Důvod výběru:

- hotový modul bez SMD pájení
- `galvanicky izolovaný`
- šroubovací svorky na `TTL` i `RS-485` straně
- `120R` terminace jde vypnout přepínačem
- oficiální dokumentace ukazuje přesné rozhraní `VCC`, `GND`, `TXD`, `RXD`, `SGND`, `A+`, `B-`

Co koupit je v samostatném dokumentu:
- [nakupni-seznam.md](nakupni-seznam.md)

## Co se na modulu použije

Horní svorky modulu:

- `VCC`
- `GND`
- `TXD`
- `RXD`

Spodní svorky modulu:

- `SGND`
- `A+`
- `B-`

Přepínač:

- `120R`

## Důležitá logika signálů

Podle oficiálního testovacího schématu Waveshare:

- `USB-TTL RXD` je připojené na `modul TXD`
- `USB-TTL TXD` je připojené na `modul RXD`

Z toho plyne:

- `modul TXD` je výstup z modulu směrem do hosta
- `modul RXD` je vstup do modulu od hosta

Pro pasivní odposlech tedy chceme:

- `Pi RX <- modul TXD`
- `Pi TX` nechat úplně odpojené
- `modul RXD` nechat úplně odpojené

Tím modul nemá žádný datový vstup z Raspberry Pi.

## Přesné zapojení na Raspberry Pi

Použij tyto fyzické piny:

- `Pi pin 1` = `3V3`
- `Pi pin 6` = `GND`
- `Pi pin 10` = `GPIO15 / RXD0`
- `Pi pin 8` = `GPIO14 / TXD0`, ten se nepoužije

### Přesná tabulka propojení Pi -> modul

| Raspberry Pi | Modul Waveshare | Poznámka |
|---|---|---|
| `pin 1 (3V3)` | `VCC` | napájení TTL strany modulu na `3.3 V` |
| `pin 6 (GND)` | `GND` | zem TTL strany modulu |
| `pin 10 (RXD0)` | `TXD` | data z modulu do Pi |
| nic | `RXD` | nezapojovat |
| `pin 8 (TXD0)` | nic | nezapojovat |

## Přesné zapojení modul -> Futura

Na spodní straně modulu:

- `A+ -> A` na Futuře
- `B- -> B` na Futuře
- `SGND -> GND/COM` na Futuře pouze pokud je komunikační zem jasně označená

Bezpečný postup:

1. začni jen s `A+` a `B-`
2. pokud nebude komunikace stabilní nebo neuvidíš validní rámce, přidej `SGND -> GND/COM`
3. pokud nebude sedět `CRC`, prohoď `A+` a `B-`

Nikdy nepřipojuj:

- `24V`
- napájecí `0V`, pokud není jisté, že jde o komunikační `GND/COM`
- žádný vodič z `Pi TX`

## Přesné nastavení modulu

Před připojením k Futuře:

1. přepínač `120R` nastav na `OFF`

Důvod:

- sniffer se připojuje paralelně na už existující sběrnici
- nesmí přidat další terminaci

## ASCII schéma

```text
Raspberry Pi Zero 2 WH                     Waveshare TTL TO RS485 (B)                     Futura RS-485
======================                     ==========================                     ==============

pin 1  (3V3)   --------------------------> VCC
pin 6  (GND)   --------------------------> GND
pin 10 (RXD0)  <-------------------------- TXD
pin 8  (TXD0)   --- NEZAPOJOVAT ---
                                           RXD --- NEZAPOJOVAT ---

                                           A+  -----------------------------------------> A
                                           B-  -----------------------------------------> B
                                           SGND -------- optional -----------------------> GND / COM

                                           120R switch = OFF
```

## Kontrola před zapnutím

Zkontroluj:

1. `Pi pin 8` není nikam připojený
2. `modul RXD` není nikam připojený
3. `120R` je `OFF`
4. `VCC` modulu jde na `3V3`, ne na `5V`
5. `A+` a `B-` nejdou na `24V`
6. modul je připojený `paralelně`, ne do série

Pokud body `1` a `2` neplatí, není to pasivní varianta.

## Doporučený postup montáže

1. připrav Raspberry Pi s povoleným `UART`
2. propoj jen `VCC`, `GND`, `TXD -> Pi RX`
3. nechej `RXD` na modulu volný
4. nastav `120R` na `OFF`
5. připoj `A+` a `B-` na Futuru
6. spusť monitor
7. teprve pokud bude potřeba, doplň `SGND`

## Jak napájet Pi v rozvodné skříni

Nejlepsi varianta je:

- `samostatny DIN zdroj 230 V AC -> 5 V DC`
- vystup alespon `2.5 A`, lepe `3 A`
- kratky privod `5 V` do `Pi`

Prakticky doporucuji:

1. `MEAN WELL HDR-30-5`
2. `Pi` na `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`
3. `Datový kabel USB - micro USB, 0,15m`
4. napajeni vest do `Pi` pres jeho `micro-USB power` vstup, ne pres `GPIO`

### Proč ne přes GPIO 5V

Napajeni pres `micro-USB power` je pro prvni instalaci bezpecnejsi, protoze:

- je to standardni napajeci vstup desky
- je mensi riziko prepolovani
- vyhnes se bastleni primo na `5V` pinech `GPIO`

Pokud budes chtit cistejsi panelove reseni, lze pozdeji udelat kratky kabel:

- `DIN zdroj +5V`
- `DIN zdroj GND`
- `micro-USB pigtail` do `Pi`

## Přesné napájecí schéma

`230 V` cast zapojuj jen podle znaceni na zdroji a idealne kvalifikovanou osobou.

Doporucena topologie:

```text
230 V AC rozvaděč
      |
      +---- L ------------------------------+
      |                                     |
      +---- N --------------------------+   |
                                         |   |
                              +---------------------------+
                              | DIN zdroj 5 V / 4.5 A    |
                              | AC IN: L, N              |
                              | DC OUT: +V, -V           |
                              +---------------------------+
                                         |   |
                                   +V ---+   +--- -V
                                         |   |
                                         |   |
                          ustrižený konec USB-A kabelu
                                         |   |
                              cerveny ---+   +--- cerny
                              bily ------------- nezapojovat
                              zeleny ----------- nezapojovat
                                         |
                              micro-USB konec do Pi
```

### Přesné zapojení DIN zdroj -> Micro-USB kabel

Pouzij:

- `Datový kabel USB - micro USB, 0,15m`
- odstrihni `USB-A` konec
- odizoluj jen tolik, kolik je nutne

Standardni barvy v USB kabelu:

- `cerveny` = `+5V`
- `cerny` = `GND`
- `bily` = `D-`
- `zeleny` = `D+`

Pred definitivnim zapojenim je vhodne to overit multimetrem na kontinuitu:

- `micro-USB pin 1` -> `cerveny`
- `micro-USB pin 5` -> `cerny`

Zapoj:

- `DIN zdroj +V` -> `cerveny`
- `DIN zdroj -V` -> `cerny`
- `bily` -> izolovat, nezapojovat
- `zeleny` -> izolovat, nezapojovat

Pak:

- `micro-USB` konec zapojit do `PWR IN` konektoru Raspberry Pi Zero 2

Pozor:

- `Pi Zero 2` ma dva `micro-USB` porty
- pro napajeni pouzij port `PWR IN`
- nepouzivej datovy `USB` / `OTG` port

### Kontrola před prvním zapnutím

1. mezi `+V` a `-V` neni zkrat
2. `bily` a `zeleny` vodic jsou samostatne zaizolovane
3. `Pi` neni napajene pres `GPIO`
4. `Pi TX` stale neni pripojeny k `Waveshare`
5. `Waveshare 120R` je `OFF`
6. kabel je mechanicky odlehcen a nema tah primo do svorek

### Poznámka k napětí 5.0 V

Oficialni Raspberry Pi zdroje pro `Zero 2 W` byvaji `5.1 V`, zatimco tenhle `DIN` zdroj ma `5.0 V`.

Moje inference:

- s `0,15 m` kabelem a malym odberem `Zero 2 W` je to pro tenhle projekt rozumna volba
- kdyby se objevilo podnapeti nebo nestabilita, je potreba zkontrolovat skutecne napeti na `Pi` a pripadne zvolit jiny zdroj nebo upravitelny `DIN` zdroj

### Co nedělat s KNX

`Pi` bych nenapajel primo z `KNX` zdroje.

To plati i pro `ABB SV/S 30.640.5.1` na fotce.

Duvod:

- `KNX` zdroj je urceny pro sbernici `KNX`
- u `SV/S 30.640.5.1` je dodatecny vystup `I2` podle dokumentace urceny jen pro dalsi `KNX` linku v kombinaci se samostatnou tlumivkou
- neni to doporuceny vystup pro napajeni obecne elektroniky typu `Raspberry Pi`

Takze:

- `ne` napajeni z `KNX bus 30 V`
- `ne` napajeni z `ABB I2` vystupu pro `Pi`

### Kdy je druhá rozumná varianta

Pokud uz v rozvodne skrini mas jiny `SELV 24 V DC` zdroj mimo `KNX`, pak je rozumna i tato cesta:

1. vzit `24 V DC`
2. pouzit kvalitni `buck converter 24 V -> 5.1 V`
3. napajet `Pi` pres `micro-USB`

To je pouzitelne, ale pro tenhle projekt je jednodussi a cistsi samostatny `DIN 5 V` zdroj.

### Doporučení k montáži

- `Pi` a `Waveshare` dej do `SELV` casti rozvadece
- neved `TTL` ani `5 V` kabely dlouze soubezne s `230 V`
- pokud skrin silne stini `Wi-Fi`, pocitej radeji s lokalnim testem signalu nebo s jinou konektivitou

Poznamka k propojkam:

- z baleni pouzij `3` kusy pro `VCC`, `GND`, `TXD -> Pi RX`
- na strane `Pi` prijde `female`
- na strane modulu prijde `male` konec do sroubovaci svorky

Poznamka k vodičům na sběrnici Futury:

- pro `A+`, `B-` a pripadne `SGND` nepocitam specialni produkt z e-shopu
- pouzij kratke mistni vodiče podle skutecne svorkovnice u Futury
- tohle je lepsi resit az na miste podle realne roztece a typu svorek

Praktické doporučení:

- pro propojení `Pi -> modul` použij vodiče s `female Dupont` na straně Pi
- na straně modulu vodiče odizoluj a upni do šroubovacích svorek
- pro `Futura -> modul` použij samostatné vodiče do spodních svorek `SGND / A+ / B-`

## Varianta s UTP kabelem 3 m

Ano, `UTP` kabel na vzdálenost `3 m` použít lze.

Pro tuhle konkrétní variantu je to rozumné řešení, protože:

- Waveshare uvádí pro `TTL` stranu přenosovou vzdálenost přibližně `10 m`
- naše komunikace bude pomalá, typicky `9600` nebo `19200`
- spojení je `point-to-point`

Důležité podmínky:

1. použij `samostatný` `UTP` kabel jen pro tenhle spoj
2. ideálně `Cat5e` nebo `Cat6`, měděný, ne `CCA`
3. modul napájej z `Pi 3V3`, ne z `5V`
4. `Pi TX` nechej odpojený
5. `modul RXD` nechej odpojený

### Doporučené rozdělení párů

Použij 2 kroucené páry:

- pár 1: `Pi RXD0` a `GND`
- pár 2: `3V3` a `GND`

Prakticky:

- `bílo-oranžový` -> `Pi pin 10 (RXD0)` -> `modul TXD`
- `oranžový` -> `GND`
- `bílo-modrý` -> `Pi pin 1 (3V3)` -> `modul VCC`
- `modrý` -> `GND`

Na obou koncích spoj oba `GND` vodiče dohromady.

Tedy:

- `oranžový + modrý` -> `Pi GND`
- `oranžový + modrý` -> `modul GND`

To zlepší návratovou cestu signálu i napájení.

### Co nepoužívat

- nepoužívat `UTP` pro `A/B` stranu, pokud máš modul přímo u Futury
- nepoužívat aktivní `RJ45` síťový port nebo patch panel
- nepoužívat `5V` napájení modulu při přímém spojení s `Pi GPIO`
- netáhnout `UTP` dlouhé metry těsně souběžně s `230 V`

### Kdy je lepší dát Pi blíž k modulu

Pokud budeš mít možnost umístit `Pi` přímo do rozvodné skříně vedle modulu, je to ještě lepší.

Důvod:

- `TTL` spoj bude velmi krátký
- méně rušení
- méně mechanických chyb

Ale čistě technicky je `UTP 3 m` pro tuhle aplikaci v pořádku.

### Doporučení pro první oživení

Pokud bude mezi `Pi` a modulem opravdu `3 m` kabelu:

1. první test udělej na `9600 8N1`
2. teprve potom zkus `19200 8N1`
3. pokud bude provoz nestabilní, zkrať `TTL` vedení nebo použij stíněný kabel

## Software po zapojení

Na Raspberry Pi pak použij:

```bash
python src/sniffer/rs485_modbus_monitor.py \
  --serial-port /dev/serial0 \
  --baudrate 19200 \
  --parity N \
  --stopbits 1 \
  --listen-host 127.0.0.1 \
  --listen-port 8765
```

Pokud nebude provoz čitelný, zkus postupně:

1. `19200 8N1`
2. `9600 8N1`
3. `19200 8E1`
4. `9600 8E1`

## Proč jsem vybral tuhle variantu

Oproti `MAX3491` variantě odpadá:

- SMD pájení čipu
- pájení propojek na adaptéru
- kontrola jemných zkratů mezi piny

Oproti běžnému `USB-RS485` adaptéru je tahle varianta lepší v tom, že:

- lze ji umístit přímo u Futury
- má oddělené napájení od Pi přes TTL stranu
- má šroubovací svorky
- `Pi TX` zůstane fyzicky odpojené

To není absolutně čistý `RX-only` hardware jako u samostatného přijímače, ale je to montážně mnohem bezpečnější a pro tenhle projekt rozumnější.

## Pokud je cílový systém Home Assistant

Pokud budou data končit v `Home Assistant` na `Raspberry Pi 5`, pak je doporučená architektura tato:

### 1. Běžné stavy Futury

Pro vse, co uz Futura umi pres `Modbus TCP`, je nejjednodussi jit:

- `Futura -> Modbus TCP -> Home Assistant`

Ne pres `KNX`.

Duvod:

- `Home Assistant` ma oficialni `Modbus` integraci
- odpada dalsi vrstva `Weinzierl KNX Modbus TCP Gateway`
- je mensi slozitost i mensi pocet mist, kde muze vzniknout chyba

### 2. Skutečné stavy klapek

Pokud chces v `Home Assistant` mit i to, co Futura pres verejny `Modbus TCP` nevystavuje, tedy pravdepodobne interni stavy klapek, je lepsi jit:

- `RS-485 sniffer u Futury -> MQTT -> Home Assistant`

Duvod:

- `KNX` gateway ti neodemkne nic navic oproti `Modbus TCP`
- `Home Assistant` ma oficialni `MQTT` integraci a umi `MQTT discovery`
- sniffer muze bezet na malem `Pi Zero 2` u Futury a jen publikovat data po siti do `HA`

### 3. Kdy má KNX smysl

`KNX` ma smysl hlavne tehdy, pokud:

- uz chces stejna data zaroven i na `KNX` sbernici
- chces je pouzit v `ETS` logice, vizualizaci nebo dalsich `KNX` prvcich

Ale ciste pro `Home Assistant` to neni nejkratsi cesta.

## Reference

1. Waveshare Wiki `TTL TO RS485 (B)`: https://www.waveshare.com/wiki/TTL_TO_RS485_(B)
