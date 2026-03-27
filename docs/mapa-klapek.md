# Mapa klapek

Tenhle soubor je pripraveny pro rucni doplneni vsech skutecne osazenych klapek v systemu.

Vyplnuj:

- `Mistnost / zona`: lidsky nazev mistnosti
- `Typ`: `privod` nebo `odtah`
- `Zona`: cislo zony ve Futuře
- `Klapka`: poradove cislo klapky v dane zone
- `DIP1..DIP6`: `ON` nebo `OFF`
- `Poznamka`: cokoliv uzitecneho navic

Sloupce `RS485 slave_id` a `Overeno` jsou doplnene podle shody `DIP -> slave_id` a podle pasivniho odposlechu `RS485`.

## Souhrn

| Typ | Zona | Mistnost / zona | Pocet klapek | Poznamka |
|---|---:|-----------------|-------------:|---|
| privod | 1 | Obyvák          |            3 | potvrzeno podle DIP tabulky |
| privod | 2 | Knihovna        |            1 |  |
| privod | 3 | Pracovna        |            1 |  |
| privod | 4 | Terka           |            1 |  |
| privod | 5 | Marťa           |            1 |  |
| privod | 6 | Natálka         |            1 |  |
| privod | 7 | Ložnice         |            1 |  |
| privod | 8 | -               |            0 |  |
| odtah | 1 | Šatna           |            1 |  |
| odtah | 2 | Předsíň         |            1 |  |
| odtah | 3 | Kuchyň          |            2 |  |
| odtah | 4 | Koupelna 1NP    |            1 |  |
| odtah | 5 | Koupelna 2NP    |            1 |  |
| odtah | 6 | -               |            0 |  |
| odtah | 7 | -               |            0 |  |
| odtah | 8 | -               |            0 |  |

## Detail klapek

| Mistnost / zona | Typ | Zona | Klapka | DIP1 | DIP2 | DIP3 | DIP4 | DIP5 | DIP6 | RS485 slave_id | Overeno | Poznamka |
|-----------------|---|---:|---:|------|------|------|------|------|------|---:|---|---|
| Obyvák          | privod | 1 | 1 | OFF | OFF | OFF | OFF | OFF | OFF | 64 | ano | potvrzeno z tabulky a shodne s odposlechem |
| Obyvák          | privod | 1 | 2 | OFF | OFF | OFF | ON  | OFF | OFF | 72 | ano | potvrzeno z tabulky a shodne s odposlechem |
| Obyvák          | privod | 1 | 3 | OFF | OFF | OFF | OFF | ON  | OFF | 80 | ano | potvrzeno z tabulky a shodne s odposlechem |
| Knihovna        | privod | 2 | 1 | ON  | OFF | OFF | OFF | OFF | OFF | 65 | ano | shodne s odposlechem |
| Pracovna        | privod | 3 | 1 | OFF | ON  | OFF | OFF | OFF | OFF | 66 | ano | shodne s odposlechem |
| Terka           | privod | 4 | 1 | ON  | ON  | OFF | OFF | OFF | OFF | 67 | ano | shodne s odposlechem |
| Marťa           | privod | 5 | 1 | OFF | OFF | ON  | OFF | OFF | OFF | 68 | ano | shodne s odposlechem |
| Natálka         | privod | 6 | 1 | ON  | OFF | ON  | OFF | OFF | OFF | 69 | ano | shodne s odposlechem |
| Ložnice         | privod | 7 | 1 | OFF | ON  | ON  | OFF | OFF | OFF | 70 | ano | shodne s odposlechem |
| Šatna           | odtah | 1 | 1 | OFF | OFF | OFF | OFF | OFF | ON  | 96 | ano | shodne s odposlechem |
| Předsíň         | odtah | 2 | 1 | ON  | OFF | OFF | OFF | OFF | ON  | 97 | ano | shodne s odposlechem |
| Kuchyň          | odtah | 3 | 1 | OFF | ON  | OFF | OFF | OFF | ON  | 98 | ano | shodne s odposlechem |
| Kuchyň          | odtah | 3 | 2 | OFF | ON  | OFF | ON  | OFF | ON  | 106 | ano | shodne s odposlechem |
| Koupelna 1NP    | odtah | 4 | 1 | ON  | ON  | OFF | OFF | OFF | ON  | 99 | ano | shodne s odposlechem |
| Koupelna 2NP    | odtah | 5 | 1 | OFF | OFF | ON  | OFF | OFF | ON  | 100 | ano | shodne s odposlechem |

## Poznámky k mapování

- `slave_id 16` uz nevypada jako bezna klapka. Aktualni pracovni hypoteza je, ze jde o `ALFA` uzel pro zonu 1 (`Obyvak`), ktery ma vsechny `DIP OFF`.
- To znamena, ze ruzne typy periferii na sběrnici pravdepodobne pouzivaji ruzne adresni zaklady. Pro klapky sedi zaklad `64`, pro `ALFA` muze byt zaklad `16`.
- Vice dalsich zarizeni odpovida pres `FC4` jednim registrem. To jsou dobri kandidati na jednotlive klapky nebo periferie.
- Pocet skutecne osazenych klapek je `15` a presne `15` aktivnich `FC4` uzlu bylo zachyceno na `RS485`: `64, 65, 66, 67, 68, 69, 70, 72, 80, 96, 97, 98, 99, 100, 106`.
- Aktualni pracovni hypoteza: `FC4` registr `107` na jednotlivych klapkach pravdepodobne reprezentuje binarni stav klapky.
- Zatim byl jako promenny kandidat potvrzen alespon na `slave_id 66` (`Pracovna / privod / zona 3 / klapka 1`), kde nabyl hodnot `0` a `1`.
- Delsi log ukazal, ze `registr 107` je spise vice-stavovy status nez ciste binarni hodnota. Na ruznych klapkach se objevily hodnoty `0`, `1`, `2` a `4`.
- Ve sledovanem okne se menily zejmena klapky `64`, `65`, `66`, `68`, `69`, `70`, `72`, zatimco `67`, `80`, `96`, `97`, `98`, `99`, `100`, `106` zustaly na hodnote `1`.
- Cileny test s dychanim na `ALFA` v `Obyvaku` potvrdil, ze `slave_id 16` velmi pravdepodobne patri tomuto `ALFA` uzlu.
- Pri tomtez testu se jako pravdepodobne mapovani `ALFA` registru ukazalo:
  - `68` = teplota v desetinach `°C`
  - `69` = relativni vlhkost v `%`
  - `70` = `CO2` v `ppm`
- Obývakove klapky `64`, `72`, `80` na tuto udalost reagovaly zmenou `registru 107`, ale zadna presna analogova poloha klapky v beznem pasivnim provozu zatim potvrzena nebyla.
- V casovem okne te same udalosti byly u klapek `64`, `72`, `80` zachyceny pouze odpovedi na `FC4 / registr 107`. Jiny registr, ktery by v tomto beznem pasivnim provozu pripominal presnou polohu klapky, zachycen nebyl.
- Nove byl ale v tomtez okne zachycen i zapis z Futury na obývakove klapky pres `FC16 / registr 102`.
- Zapsane hodnoty byly:
  - `33` na zacatku okna,
  - nasledne `32`,
  - potom `31`,
  - a pri silnem narustu `CO2` i `100`.
- `FC16 / registr 102` je tedy aktualne nejsilnejsi kandidat na cilovou pozici klapky nebo procentualni pozadavek otevreni.
- Rozsireny filtr pres vice klapek ukazal, ze `FC16 / registr 102` se pouziva i mimo obývak.
- V zachycenem okne byly pozorovany napriklad tyto hodnoty:
  - `64`: `31`, `32`, `33`, `100`
  - `65`: `0`, `31`, `32`
  - `66`: `56`
  - `67`: `22`, `32`, `33`
  - `68`: `30`, `33`
  - `69`: `30`, `33`, `34`
  - `70`: `25`, `32`, `33`
  - `72`: `31`, `32`, `33`, `100`
  - `80`: `31`, `32`, `33`, `100`
- Aktualni pracovni interpretace:
  - `registr 102` = cilova nebo vypoctena pozice klapky,
  - `registr 107` = stavovy kod nebo potvrzeni reakce klapky.
- Ověřovací test pro `Pracovnu` (`slave 66`) v okně `2026-03-26T13:18:09+00:00` až `2026-03-26T13:31:43+00:00` nezachytil žádný `FC16 / registr 102`.
- Ve stejném okně zůstal `FC4 / registr 107` na `slave 66` beze změny na hodnotě `1`.
- Ve stejnem okne ale ostatni privodni klapky dostaly radu novych zapisu na `FC16 / registr 102`, typicky s pozvolnym poklesem z vysokych hodnot do nizsich:
  - `64`: `93 -> 90 -> 85 -> 51 -> 21 -> 24 -> 27 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `65`: `89 -> 86 -> 83 -> 80 -> 79 -> 77 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `67`: `91 -> 90 -> 87 -> 84 -> 81 -> 80 -> 77 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `68`: `94 -> 93 -> 90 -> 86 -> 83 -> 81 -> 78 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `69`: `98 -> 97 -> 93 -> 88 -> 84 -> 81 -> 51 -> 23 -> 26 -> 28 -> 32 -> 33 -> 35 -> 33 -> 31`
  - `70`: `91 -> 90 -> 88 -> 84 -> 81 -> 80 -> 77 -> 50 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `72`: `98 -> 91 -> 89 -> 85 -> 51 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
  - `80`: `98 -> 92 -> 89 -> 85 -> 51 -> 21 -> 24 -> 26 -> 31 -> 30 -> 28 -> 25`
- To podporuje interpretaci, ze `registr 102` je zapisovana cilova poloha, ktera se meni jen pri prepoctu Futury.

## Odvozené pravidlo adresace

Z pozorovane shody vyplyva, ze `RS485 slave_id` odpovida tomuto vzorci:

```text
slave_id = 64
         + DIP1*1
         + DIP2*2
         + DIP3*4
         + DIP4*8
         + DIP5*16
         + DIP6*32
```

Kde:

- `OFF = 0`
- `ON = 1`

Priklady:

- vsechny `DIP OFF` -> `64`
- pouze `DIP4 ON` -> `72`
- pouze `DIP5 ON` -> `80`
- pouze `DIP6 ON` -> `96`
- `DIP2 + DIP4 + DIP6 ON` -> `106`
