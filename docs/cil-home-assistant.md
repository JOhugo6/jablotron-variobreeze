**Česky** | [English](cil-home-assistant.en.md)

# Cíl integrace s Home Assistant

## Hlavní cíl

Cílem projektu je zpřístupnit v `Home Assistant` skutečný stav klapek systému `Jablotron Futura` tak, aby bylo možné:

- zobrazovat stav jednotlivých klapek po místnostech,
- ukládat historii stavů klapek v `Home Assistant`,
- porovnávat stav klapek s kvalitou vzduchu, zejména s `CO2`,
- později stavět automatizace a grafy nad historií klapek.

## Co má být vidět v Home Assistant

Pro každou klapku má být v `Home Assistant` primárně dostupná:

- aktuální poloha klapky v `%` nebo v jiné stabilní číselné škále, pokud ji tak Futura skutečně poskytuje.

Teprve jako dočasný fallback připadá v úvahu:

- stav `otevřeno / zavřeno`,
- případně i surová hodnota registru, pokud to pomůže s laděním.

Typické entity mohou vypadat například takto:

- `sensor.futura_klapka_obyvak_1_poloha`
- `binary_sensor.futura_klapka_obyvak_1_otevrena`
- `sensor.futura_klapka_obyvak_1_raw`

## Ukládání historie

Historii stavů klapek nemá řešit `Pi Zero 2`.

Historii bude ukládat samotný `Home Assistant`, protože:

- už běží v síti na `Raspberry Pi 5`,
- má vlastní interní historii a databázi,
- umí nad tím dělat grafy, statistiky a automatizace.

`Pi Zero 2` má fungovat jen jako pasivní sběrač a publisher dat.

## Cílová architektura

```text
Jablotron Futura RS485
        ->
Raspberry Pi Zero 2 W
  - pasivní odposlech RS485
  - dekódování komunikace klapek
  - převod na čitelné stavy
  - publikace do MQTT
        ->
Home Assistant na Raspberry Pi 5
  - MQTT příjem
  - ukládání historie
  - vizualizace
  - porovnání s CO2 / kvalitou vzduchu
```

## Co má Pi Zero 2 dělat

`Pi Zero 2` má:

- pasivně odposlouchávat interní `RS485 / Modbus RTU` komunikaci Futury,
- identifikovat jednotlivé klapky podle `slave_id`,
- z komunikace vyhodnocovat jejich stav nebo polohu,
- posílat výsledné hodnoty po síti do `Home Assistant`.

`Pi Zero 2` nemá:

- aktivně řídit Futuru,
- vysílat do `RS485` sběrnice,
- být hlavním úložištěm historie.

## Co má Home Assistant dělat

`Home Assistant` má:

- přijímat stavy klapek ze sítě,
- ukládat jejich historii,
- umožnit porovnání stavu klapek s `CO2`, vlhkostí nebo dalšími senzory kvality vzduchu,
- nabídnout dlouhodobé grafy a případné automatizace.

## Aktuálně potvrzený stav

Aktuálně je potvrzeno:

- pasivní odposlech `RS485` funguje,
- `19200 8N1` je správné nastavení,
- mapa `DIP -> slave_id` je odvozena a sedí na zachycenou komunikaci,
- jednotlivé klapky jsou identifikovatelné jako samostatné uzly na sběrnici,
- parser nyní spolehlivě skládá i delší `Modbus RTU` odpovědi.

Detailní reverse-engineering sběrnice, mapování `slave_id`, interpretace registrů `102` a `107` i konkrétní zachycené hodnoty jsou udržovány jen v [mapa-klapek.md](mapa-klapek.md).

Pro integrační vrstvu je aktuálně důležité jen toto:

- `FC16 / registr 102` je nejsilnější kandidát na cílovou polohu nebo požadované otevření klapky,
- `FC4 / registr 107` se chová jako stavový kód nebo reakční stav klapky,
- `registr 102` je událostní zápis, ne periodicky vysílaný stav.

## Důsledek pro Home Assistant

Pro `Home Assistant` z toho plyne:

- poslední známou cílovou polohu klapky je potřeba držet stavově v aplikaci, nečekat na to, že ji Futura bude periodicky znovu vysílat,
- `Pi Zero 2` nebo publisher do `MQTT` musí po zachycení `FC16 / registr 102` aktualizovat interní stav dané klapky,
- při restartu snifferu nebo `Home Assistant` nebude aktuální poloha známá okamžitě, pokud od té doby neproběhl nový zápis,
- proto je vhodné poslední známou hodnotu `registru 102` perzistovat mimo RAM, například:
  - v retained `MQTT` zprávách,
  - nebo v lokálním stavovém souboru na `Pi Zero 2`.

## Další praktický cíl

Nejbližší technický cíl je:

1. spolehlivě dekódovat delší odpovědi z `RS485`,
2. určit, které registry nebo hodnoty odpovídají skutečné poloze klapek,
3. převést to na stabilní datový model po místnostech,
4. publikovat tyto stavy do `MQTT`,
5. napojit `MQTT` entity do `Home Assistant`.
