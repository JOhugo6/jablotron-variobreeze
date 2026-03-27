**Česky** | [English](poznamky-z-technickeho-centra-jablotron.en.md)

# Poznámky z technického centra Jablotronu

## Zdroj

Shrnutí odpovědi technického centra `Jablotron` k:

- vlhkosti v interiéru,
- entalpickému zpětnému zisku vlhkosti,
- algoritmu pozicování `VarioBreeze` klapek.

Zdrojový text pochází z odpovědi technického centra, kterou poskytl uživatel projektu.  
Tento dokument odděluje informace deklarované výrobcem od poznatků získaných pasivním odposlechem `RS485`.

## Vlhkost a entalpie

Technické centrum uvádí:

- v chladném období je nízká vlhkost v interiéru běžný problém, protože studený venkovní vzduch nese málo vlhkosti,
- komfortní absolutní vlhkost v interiéru je přibližně `7 až 10 g/m3`,
- to odpovídá zhruba `40 až 60 % RH` při `20,5 °C`,
- v konkrétním posuzovaném stavu bylo v interiéru:
  - `24,3 °C`,
  - `37,3 % RH`,
  - `8,3 g/m3` absolutní vlhkosti,
- venkovní stav ve stejném příkladu byl:
  - `14 °C`,
  - `48,2 % RH`,
  - `5,8 g/m3` absolutní vlhkosti.

Princip entalpického výměníku podle odpovědi:

- pokud je venkovní teplota pod rosným bodem interiéru, vytváří se v teplejším proudu odtahovaného vzduchu kondenzát,
- systém klapek po určité době obrací proudění,
- část takto vzniklé vlhkosti se vrací zpět do interiéru,
- nikdy se však nevrátí všechna, takže interiér se může postupně vysoušet, ale pomaleji než bez entalpie,
- při nevhodných podmínkách se kondenzát netvoří,
- při velkém množství kondenzátu jeho část odteče do odpadu.

## Nastavení zpětného zisku vlhkosti

Podle technického centra nastavení v aplikaci:

- `SUCHÉ` odpovídá vlhkosti do `40 % RH`,
- `KOMFORTNÍ` odpovídá rozsahu `40 až 60 % RH`,
- `VLHKÉ` odpovídá stavu nad `60 % RH`.

Smysl tohoto nastavení:

- ovlivňuje frekvenci překlápění klapek,
- vztahuje se k aktuální interiérové vlhkosti,
- při nízké interiérové vlhkosti a nastavení `VLHKÉ` mohou klapky překlápět přibližně každých `8 minut`,
- v extrémních případech může být interval až kolem `3 minut`,
- cílem je vracet vlhkost do té doby, než interiér dosáhne zadané úrovně.

## Algoritmus pozicování klapek

Technické centrum výslovně uvádí, že pozicování klapek vychází z prvotní vzduchové analýzy při instalaci.  
Jednotka si podle nich změří:

- celkovou průchodnost systému,
- průchodnost jednotlivých tras,
- tlakové ztráty potřebné pro dosažení požadovaných průtoků.

### Odtahové klapky

Podle odpovědi:

- odtahové klapky jsou v základním nastavení standardně plně otevřené,
- výjimkou je použití klapky v režimu `boost` nebo `digestoř`,
- u `boost` je standardně nastaven odtah jednou klapkou na `50 m3/h`,
- pokud celkový výkon Futury dodává například `150 m3/h`, boostovaná klapka se otevře naplno a ostatní si rozdělí zbývajících `100 m3/h`,
- režim `digestoř` je standardně nastaven na `120 m3/h`,
- u odtahových i přívodních klapek lze nastavovat nominální průtoky.

### Přívodní klapky

Podle technického centra do výpočtu jejich pozicování vstupují:

- celková tlaková ztráta systému,
- tlaková ztráta každé trasy,
- celkové aktuální vzduchové množství,
- požadavek z řízení `CO2 / TEMP / MAX` v procentech,
- nominální vzduchové množství zóny.

Další deklarované vlastnosti:

- při manuálním výkonu Futury `1 až 5` se klapky pozicují fixně,
- v režimu `AUTO` je výkon Futury řízen přímkou závislosti výkonu na maximálním `CO2` v některé ze zón,
- zóny s vyšším `CO2` mají být otevřeny více než zóny, kde není potřeba větrat,
- vztah mezi otevřením klapky a průtokem vzduchu není lineární, ale logaritmický.

## Data viditelná v Jablotron cloudu

Technické centrum uvedlo, že v tomto konkrétním zapojení v cloudu vidí:

- data z `ALFA` v `Obýváku`,
- data z jednoho externího senzoru v `zóně 3`.

Současně uvedlo, že:

- klapky se nejvíce otevírají přes noc v `zóně 7`,
- pokud je to ložnice dvou osob, doporučují upravit nominální průtoky nebo strmost přímky závislosti výkonu na `CO2`.

## Dopad na tento projekt

Pro odposlech a integraci do `Home Assistant` je z odpovědi důležité hlavně toto:

- skutečná poloha klapek je interně řízená a závisí na více vstupních veličinách,
- mezi tyto vstupy podle výrobce patří minimálně `CO2`, `teplota`, `nominály`, tlakové ztráty a celkový výkon jednotky,
- samotná poloha klapek tedy nemusí být jednoduchá jednorozměrná hodnota odvozitelná jen z jednoho senzoru,
- odpověď výrobce podporuje závěr z odposlechu, že `ALFA` v `Obýváku` je významný řídicí vstup pro zónu 1,
- pokud se nám nepodaří pasivně najít přímý registr polohy, je stále cenné do `Home Assistant` dostat:
  - senzory `ALFA`,
  - stavové kódy klapek,
  - a časovou korelaci mezi `CO2 / RH / teplotou` a reakcí klapek.

## Poznámka k interpretaci

Informace v tomto souboru jsou:

- deklarované výrobcem nebo technickou podporou,
- ne všechny jsou zatím nezávisle potvrzené pasivním odposlechem,
- ale jsou důležité jako vodítko pro další hledání skutečné polohy klapek.
