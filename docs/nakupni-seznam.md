# Nákupní seznam

## Vybraný modul

Pro pasivní odposlech RS485 sběrnice Futury je vybraný modul:

- `Waveshare TTL TO RS485 (B)`

Důvod výběru:

- hotový modul bez SMD pájení
- `galvanicky izolovaný`
- šroubovací svorky na `TTL` i `RS-485` straně
- `120R` terminace jde vypnout přepínačem
- oficiální dokumentace ukazuje přesné rozhraní `VCC`, `GND`, `TXD`, `RXD`, `SGND`, `A+`, `B-`

Zapojení modulu je v samostatném dokumentu:
- [waveshare-ttl-to-rs485-b-zapojeni.md](waveshare-ttl-to-rs485-b-zapojeni.md)

## Povinné položky

1. `Raspberry Pi Zero 2 W s připájeným GPIO headerem`
2. `Waveshare TTL TO RS485 (B)`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 s Raspberry Pi OS`
4. `MEAN WELL HDR-30-5`
5. `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`
6. `Datový kabel USB - micro USB, 0,15m`
7. `Drátové propojky Female/Male 10 cm, 10 ks`

## Montážní drobnosti

Tyhle polozky nejsou specificky vazane na jeden e-shop, ale pro montaz je pocitam jako soucast finalniho BOM:

1. `3x kratky vodic 0,5 az 0,75 mm2` pro `A+`, `B-` a pripadne `SGND`
2. `2x kratky vodic 0,5 az 0,75 mm2` pro `DIN zdroj +V/-V -> ustřižený USB kabel`
3. `dutinky / ferule` podle zvoleneho prurezu, pokud pouzijes lankove vodice
4. `stahovaci pasky` nebo jine odlehceni tahu kabelu

## Jediná rozumná alternativa zdroje

Pokud by `HDR-30-5` nebyl dostupny, rozumna nahrada je:

1. `MEAN WELL MDR-20-5`

Pro tenhle projekt ho ale beru jako `alternativu`, ne jako vychozi volbu.

## Alternativa držáku: 3D tisk

`DIN` drzak pro `Pi Zero 2` jde vytisknout na `3D` tiskarne.

Prakticky to znamena:

- neni nutne kupovat hotovy `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`
- lze vytisknout ekvivalentni drzak pro `TS35` listu

Doporuceni pro tisk:

- material `PETG`, `ASA` nebo `ABS`
- ne `PLA`
- alespon `4` perimetry
- infill alespon `40 %`

Kdy je 3D tisk rozumna volba:

- `Pi` bude v `SELV` casti rozvadece
- v rozvadeci neni vysoka teplota
- nevadi ti vlastni mechanicke doladeni

Kdy je lepsi koupit hotovy drzak:

- chces co nejmensi montazni riziko
- nechces resit tuhost DIN klipu
- chces hotove a predvidatelne mechanicke reseni

## Objednávka bez alternativ

Aktualne doporucena objednavka je:

1. `Raspberry Pi Zero 2 W s připájeným GPIO headerem`
2. `Waveshare převodník TTL na RS485 (B)`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 s Raspberry Pi OS`
4. `MEAN WELL HDR-30-5`
5. `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`
6. `Datový kabel USB - micro USB, 0,15m`
7. `Drátové propojky Female/Male 10 cm, 10 ks`

Proc zrovna tahle sestava:

- `Pi` uz ma pripajeny `GPIO header`, takze odpada dalsi pajeni
- `Waveshare` modul je hotovy a izolovany
- `64GB microSD` je aktualne skladem a ma uz `Raspberry Pi OS`
- `MEAN WELL HDR-30-5` je kvalitnejsi `DIN 5V` zdroj pro rozvadece
- `Pi` muze byt na DIN liste hned vedle prevodniku
- `0,15 m micro-USB` kabel umozni kratke a ciste napajeni
- `10 cm Female/Male` propojky staci pro kratke propojeni `Pi -> modul`

Aktualni stav dostupnosti k `23. březnu 2026`:

- `Raspberry Pi Zero 2 W s připájeným GPIO headerem`: `RPishop skladem 5 a více kusů`
- `Waveshare převodník TTL na RS485 (B)`: `skladem 5 a více kusů`
- `Raspberry Pi 64GB microSDXC ...`: `RPishop skladem 5 a více kusů`
- `MEAN WELL HDR-30-5`: `skladem` na `RS Online CZ`
- `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`: `skladem 5 a více kusů`
- `Datový kabel USB - micro USB, 0,15m`: `skladem 5 a více kusů`
- `Drátové propojky Female/Male 10 cm, 10 ks`: `skladem 5 a více kusů`

## Doporučený nákup po obchodech

### RPishop

1. `Raspberry Pi Zero 2 W s připájeným GPIO headerem`
2. `Waveshare převodník TTL na RS485 (B)`
3. `Raspberry Pi 64GB microSDXC Class 10 UHS-I U1 A1 s Raspberry Pi OS`
4. `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`
5. `Datový kabel USB - micro USB, 0,15m`
6. `Drátové propojky Female/Male 10 cm, 10 ks`

### RS Online CZ

1. `MEAN WELL HDR-30-5`

Tohle je aktualne moje preferovana nakupni varianta.

## Pokud bude Pi v rozvodné skříni

Jestli bude `Raspberry Pi Zero 2` opravdu v rozvodne skrini vedle `Waveshare TTL TO RS485 (B)`, je lepsi:

- nepouzivat beznou `Zero` krabicku
- misto ni vzit `DIN` drzak pro Raspberry Pi
- dat `Pi` primo vedle `TTL/RS-485` modulu

Tahle topologie je lepsi, protoze:

- `TTL` vedeni bude velmi kratke
- bude min ruseni
- cele zapojeni bude prehlednejsi

### Praktická výměna v košíku

Pokud pujdes cestou `DIN` montaze, vymen:

- `běžnou Zero krabičku`

za:

- `Vertikální držák na DIN lištu pro Raspberry Pi typ 2`

Bezna krabicka uz v tom pripade neni potreba.

## Reference

1. RPishop produktová stránka `Waveshare převodník TTL na RS485 (B)`: https://rpishop.cz/datove-redukce/6122-waveshare-prevodnik-ttl-na-rs485-b.html
2. RS Online CZ `MEAN WELL HDR-30-5`: https://cz.rs-online.com/web/p/napajeci-zdroje-pro-montaz-na-listu-din/1457864
