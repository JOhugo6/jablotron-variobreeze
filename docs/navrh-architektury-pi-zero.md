# Návrh architektury pro Pi Zero RS485 sniffer

## Účel dokumentu

Tento dokument popisuje doporučené řešení pro `Raspberry Pi Zero 2 W`, které:

- pasivně odposlouchává interní `RS485 / Modbus RTU` komunikaci Futury,
- odvozuje z ní stav klapek,
- minimalizuje zápisy na `SD` kartu,
- a připravuje čistý podklad pro další integraci do `Home Assistant`.

Dokument je záměrně zaměřen jen na `Pi Zero`.

Tento dokument patri ke `RS485` sniffing casti projektu, ne k `Modbus TCP` nastroji ve `src/modbus`.

`ALFA` zde neřešíme, protože její hodnoty už `Home Assistant` umí číst jinou cestou přes `Modbus`.

## Aktuální implementace v repu

Aktualni produkcni zaklad pro `Pi Zero` je:

- [../src/sniffer/futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

Ten uz dnes umi:

- pasivne sniffovat `RS485`,
- dekodovat `Modbus RTU` ramce,
- drzet stav klapek v RAM,
- ukladat maly snapshot stavu,
- vystavit lehke HTTP API,
- a volitelne publikovat stav do `MQTT`.

Diagnosticky monitor pro reverse engineering zustava oddelene jako:

- [../src/sniffer/rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)

## Hlavní požadavky

Na `Pi Zero` chceme:

- pasivní odposlech bez vysílání do sběrnice,
- minimální počet zápisů na `SD` kartu,
- robustní běh po restartu,
- schopnost držet poslední známý stav klapek,
- možnost krátkodobého diagnostického logování,
- jednoduchý provoz jako `systemd` služba.

Na `Pi Zero` naopak nechceme:

- nekonečný `jsonl` raw log jako hlavní úložiště,
- databázi plnou všech raw rámců,
- vysokou zápisovou zátěž na `SD`,
- dlouhodobou historii, kterou stejně má držet `Home Assistant`.

## Co už víme o datech

Z pasivního odposlechu zatím plyne:

- `FC16 / registr 102` je nejsilnější kandidát na cílovou nebo vypočtenou pozici klapky,
- `FC4 / registr 107` je stavový kód nebo potvrzení reakce klapky,
- `registr 102` se nechová jako periodicky čtený stav,
- `registr 102` je zapisován událostně, když Futura přepočítá polohu klapky,
- `registr 107` se čte pravidelně a je vhodný jako pomocný provozní signál.

Z toho plyne zásadní důsledek:

- aktuální stav klapky nelze získávat jen periodickým dotazem na "poslední raw rámec",
- `Pi Zero` musí držet odvozený stav klapky stavově,
- a poslední známou hodnotu `registru 102` je potřeba perzistovat mimo RAM.

## Doporučená architektura

Nejlepší návrh pro `Pi Zero` je:

```text
serial sniffer
  ->
Modbus RTU parser
  ->
state engine
  ->
in-memory cache
  ->
MQTT publisher

plus:
  - malý lokální snapshot stavu
  - volitelný krátký debug log
```

Jinými slovy:

- raw rámce zpracovávat hned při přijetí,
- neukládat všechno jako primární zdroj pravdy,
- průběžně udržovat malý odvozený stav všech klapek,
- a na disk zapisovat jen minimum.

## Konfigurační soubor

Ano, `Pi Zero` má mít konfigurační soubor.

Bez něj by řešení bylo zbytečně svázané s jedním konkrétním domem, jedním portem, jedním brokerem a jednou mapou klapek.

Konfigurace je potřeba minimálně kvůli:

- jinému sériovému portu,
- jinému `baudrate`,
- jinému `MQTT` brokeru,
- jinému umístění stavového souboru,
- jinému režimu debug logu,
- a hlavně jiné mapě klapek v jiném objektu.

### Doporučené rozdělení

Nedoporučuji mít všechno v jednom velkém souboru.

Lepší je rozdělit konfiguraci na:

1. runtime konfiguraci aplikace,
2. samostatnou mapu klapek.

### 1. Runtime konfigurace

Runtime konfigurace má popisovat provozní prostředí Zero.

Typicky:

- sériový port,
- HTTP API,
- `MQTT`,
- perzistenci snapshotu,
- debug log,
- cesty k datovým souborům,
- odkaz na soubor s mapou klapek.

Doporučený název:

- `pi-zero-config.json`

### 2. Mapa klapek

Mapa klapek má popisovat konkrétní instalaci.

Typicky:

- `slave_id`
- místnost
- typ `privod/odtah`
- číslo zóny
- pořadí klapky
- případně poznámku nebo alias

Doporučený název:

- `damper-map.json`

Tím získáme důležité oddělení:

- při přenosu do jiného prostředí často stačí změnit `pi-zero-config.json`,
- při jiné topologii klapek nebo jiném domě stačí vyměnit `damper-map.json`,
- kód zůstane stejný.

### Proč nepoužít stávající `config.example.json`

V repu už existuje [config.example.json](../src/modbus/config.example.json), ale ten patří ke staršímu nástroji [futura_variobreeze.py](../src/modbus/futura_variobreeze.py) pro `Modbus TCP`.

Pro `Pi Zero` sniffing a bridge logiku je vhodné použít jiný, oddělený konfigurační model a jiný název souboru.

Jinak by se míchaly dvě odlišné aplikace a dva odlišné provozní režimy.

## Rozdělení na komponenty

### 1. Serial sniffer

První komponenta má řešit jen nejnižší vrstvu odposlechu.

Její úloha je:

- otevřít `serial0`,
- číst bajty ze sériové linky,
- časově je předávat dál,
- a sama o sobě ještě nedělat aplikační interpretaci.

To znamená:

- `sniffer` = fyzická a byte-stream vrstva
- `Modbus RTU parser` = až vyšší protokolová vrstva

V implementaci může být oboje v jednom procesu, ale architektonicky je lepší to držet odděleně.

V aktualni implementaci je to interni cast:

- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

Úloha snifferu:

- číst sériovou linku,
- předávat syrové bajty parseru,
- hlídat jen nízkoúrovňové podmínky čtení.

### 2. Modbus RTU parser

V aktualni implementaci tuto roli plni:

- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

Diagnosticka varianta pro detailni analyzu zustava:

- [rs485_modbus_monitor.py](../src/sniffer/rs485_modbus_monitor.py)

Úloha parseru:

- sestavit validní rámce,
- validovat `CRC`,
- dekódovat `FC3/4/6/16`,
- doplnit `correlated_request`,
- vytvořit `register_map`,
- předat je dál internímu state enginu,
- volitelně publikovat lehké lokální API typu `/health` a `/dampers`.

### 3. State engine

State engine je hlavní logika na `Pi Zero`.

Má za úkol:

- mapovat `slave_id` na konkrétní klapku,
- z `FC16 / 102` aktualizovat cílovou polohu,
- z `FC4 / 107` aktualizovat stavový kód,
- držet poslední známý stav v paměti,
- publikovat změny do `MQTT`,
- a v řízeném režimu ukládat malý snapshot na disk.

### 4. MQTT publisher

MQTT publisher má posílat už odvozený stav, ne raw rámce.

Publikace má probíhat:

- pouze při změně hodnoty,
- s `retained` zprávami,
- s malým počtem topiců,
- bez vysoké frekvence zbytečných republishů.

### 5. Snapshot writer

Snapshot writer má zapisovat jen malý stavový soubor.

Nemá zapisovat:

- každý raw rámec,
- každou periodickou odpověď,
- ani všechny přechodné interní výpočty.

Jeho úkolem je jen:

- uložit poslední známý stav všech klapek,
- aby po restartu Zero nebyla poloha klapek ztracená.

### 6. Volitelný debug logger

Debug logger má být oddělený od běžného provozu.

V normálním režimu:

- může být vypnutý úplně,
- nebo může zapisovat jen krátký rotační log.

Debug logger nesmí být hlavní datová cesta systému.

## Doporučený datový model v paměti

Pro každou klapku držet strukturu typu:

```json
{
  "slave_id": 66,
  "room": "Pracovna",
  "zone": 3,
  "type": "privod",
  "target_position": 56,
  "status_code": 1,
  "last_target_ts": "2026-03-26T09:17:02+00:00",
  "last_status_ts": "2026-03-26T13:18:13+00:00",
  "online": true
}
```

Povinné položky:

- `slave_id`
- `room`
- `zone`
- `type`
- `target_position`
- `status_code`
- `last_target_ts`
- `last_status_ts`

Volitelné položky:

- `online`
- `last_seen_ts`
- `source`
- `confidence`

## Co ukládat na disk

### Primární doporučení

Na disk ukládat jen:

- `state/dampers_state.json`

To má být malý snapshot posledního známého stavu všech klapek.

Typicky:

- desítky až stovky řádků,
- jednotky kilobajtů,
- přepisovaný jen občas.

### Co neukládat jako primární storage

Nedoporučuji jako primární úložiště:

- jeden nekonečný `logs/rs485_frames.jsonl`,
- SQLite se všemi raw rámci,
- časové řady všech periodických čtení,
- detailní audit každé odpovědi každé klapky.

Důvod:

- zbytečně to opotřebovává `SD`,
- objem dat rychle roste,
- a pro hlavní účel to není potřeba.

## Jak omezit zápisy na SD

### Pravidlo 1: Zapisovat jen při změně

Na disk ani do `MQTT` neposílat nic, pokud se stav nezměnil.

To znamená:

- když přijde opakovaně `FC4 / 107 = 1`, nezapisovat nic,
- když se znovu objeví stejný `FC16 / 102`, nezapisovat nic,
- aktualizovat jen in-memory `last_seen_ts`, pokud je to potřeba pro health.

### Pravidlo 2: Snapshot nepsat po každé změně

Snapshot na disk nepsat po každé změně jednotlivé klapky.

Doporučený režim:

- označit stav jako `dirty`,
- snapshot zapisovat nejvýš jednou za `30-60 s`,
- a vždy při čistém ukončení procesu.

To dramaticky sníží zápisovou zátěž.

### Pravidlo 3: Použít atomický přepis souboru

Snapshot ukládat atomicky:

1. zapsat do dočasného souboru,
2. provést `fsync`,
3. přejmenovat na cílový soubor.

Tím se minimalizuje riziko rozbití snapshotu při výpadku napájení.

### Pravidlo 4: Raw log mít jen jako dočasný debug

Raw log:

- mít standardně vypnutý,
- nebo držet jen posledních několik megabajtů,
- ideálně rotačně,
- a volitelně v `tmpfs`, pokud jde o krátký ladicí režim.

## MQTT jako hlavní externí persistence

Z pohledu životnosti `SD` je nejlepší, když `Pi Zero` není hlavní dlouhodobé úložiště.

Proto doporučený model je:

- `Pi Zero` drží aktuální stav v RAM,
- při změně publikuje do `MQTT`,
- `MQTT broker` běží jinde, ideálně na `Pi 5`,
- zprávy jsou `retained`,
- a `Home Assistant` si stav i historii drží mimo Zero.

To má několik výhod:

- minimum lokálních zápisů,
- po restartu Zero lze stav rychle obnovit z retained MQTT,
- dlouhodobá historie neleží na `SD` kartě Zero.

## Potřebujeme na Zero databázi?

### Krátká odpověď

Ano, je to možné. Ale jako výchozí návrh ji nedoporučuji.

### Kdy databáze dává smysl

`SQLite` by dávala smysl, pokud by `Pi Zero` mělo:

- fungovat dlouho i bez MQTT brokeru,
- držet vlastní lokální historii událostí,
- nebo poskytovat lokální analytiku nad změnami klapek.

### Proč není výchozí volbou

Pro tento projekt je ale lepší:

- držet stav v RAM,
- minimálně zapisovat snapshot,
- a historii nechat na `Home Assistant`.

Databáze sama o sobě není problém.

Problém je až styl použití:

- pokud bychom do ní zapisovali každý raw rámec, je to špatně,
- pokud by uchovávala jen změny a poslední stav, bylo by to technicky v pořádku.

### Doporučení

Výchozí varianta:

- bez `SQLite`
- `RAM + retained MQTT + malý snapshot`

Alternativní varianta:

- malá `SQLite` jen pro `damper_state` a `damper_events`
- zapisovat jen při změně
- bez raw frame historie

## Návrh adresářové struktury na Zero

Doporučené rozložení:

```text
/home/pi/futura/
  rs485_modbus_monitor.py
  futura_damper_bridge.py
  requirements.txt
  pi-zero-config.json
  damper-map.json
  state/
    dampers_state.json
  debug/
    raw-0001.jsonl
    raw-0002.jsonl
```

Poznámky:

- root `~/futura` obsahuje runtime skripty a konfiguraci,
- `state/` obsahuje jediný důležitý malý perzistentní snapshot,
- `debug/` je volitelný a může být prázdný.

## Doporučený obsah runtime konfigurace

Runtime konfigurace by měla mít minimálně tyto sekce:

- `serial`
- `http`
- `mqtt`
- `storage`
- `debug`
- `damper_map`

### `serial`

Určuje, jak Zero čte `RS485`.

Například:

- `port`
- `baudrate`
- `bytesize`
- `parity`
- `stopbits`
- `serial_timeout_seconds`
- `frame_gap_ms`

### `http`

Určuje lokální diagnostické API.

Například:

- `enabled`
- `listen_host`
- `listen_port`

### `mqtt`

Určuje publikaci mimo Zero.

Například:

- `enabled`
- `host`
- `port`
- `username`
- `password`
- `client_id`
- `topic_prefix`
- `retain`
- `qos`
- `publish_on_change_only`

### `storage`

Určuje lokální perzistenci.

Například:

- `state_path`
- `snapshot_interval_seconds`
- `restore_state_on_start`
- `write_state_on_shutdown`

### `debug`

Určuje, jak se bude ladit surová komunikace.

Například:

- `raw_log_enabled`
- `raw_log_path`
- `raw_log_rotate_bytes`
- `raw_log_keep_files`
- `raw_log_compress_rotated`

### `damper_map`

Určuje, odkud se vezme mapa klapek.

Například:

- `path`

## Doporučený obsah mapy klapek

Soubor s mapou klapek má být čistě instalační popis.

Pro každou klapku:

- `slave_id`
- `room`
- `zone`
- `type`
- `damper_index`
- `label`
- `enabled`

Volitelně:

- `notes`
- `dip`

## Doporučený vzor konfigurace

Vzorové soubory jsou přiložené v repu:

- [pi-zero-config.example.json](../src/sniffer/pi-zero-config.example.json)
- [damper-map.example.json](../src/sniffer/damper-map.example.json)

Podrobny prakticky popis jednotlivych nastaveni je v:

- [pi-zero-konfigurace.md](pi-zero-konfigurace.md)

Tyto soubory mají sloužit jako základ pro:

- produkční `Pi Zero`,
- jiné budoucí instalace,
- testovací prostředí,
- i lokální vývoj na PC.

## Co musí být konfigurovatelné bez zásahu do kódu

Bez editace Python kódu musí jít změnit:

- sériový port,
- parametry linky,
- host a port HTTP API,
- host a přihlašovací údaje `MQTT`,
- cesta ke snapshotu,
- cesta k debug logu,
- zapnutí a vypnutí debug režimu,
- mapa klapek,
- prefix topiců,
- interval snapshotu,
- případně i vypnutí `MQTT` nebo HTTP API.

To je minimální úroveň přenositelnosti mezi různými prostředími.

## Doporučené režimy provozu

### Režim 1: Normální provoz

V normálním provozu:

- raw log vypnutý,
- snapshot ukládán zřídka,
- `MQTT` publikace jen při změně,
- HTTP endpointy jen pro health a aktuální stav.

To má být výchozí produkční režim.

### Režim 2: Diagnostika

V diagnostickém režimu:

- zapnout krátký rotační raw log,
- případně zvýšit detail API,
- log rotovat po malých souborech,
- po skončení ladění debug zase vypnout.

### Režim 3: Forenzní test

Pro jednorázové experimenty:

- zapnout raw log třeba na `15-30 min`,
- potom ho archivovat mimo Zero,
- a vrátit Zero do normálního režimu.

## HTTP API na Zero

Na `Pi Zero` dává smysl mít jen malé lokální API.

Doporučené endpointy:

- `/health`
- `/dampers`
- `/dampers/<slave_id>`

### `/health`

Má vracet:

- běží nebo neběží sniffer,
- čas posledního platného rámce,
- počet klapek ve stavové cache,
- verzi aplikace,
- stav `MQTT` spojení.

### `/dampers`

Má vracet už odvozený stav klapek, ne raw rámce.

Například:

```json
{
  "dampers": [
    {
      "slave_id": 66,
      "room": "Pracovna",
      "zone": 3,
      "type": "privod",
      "target_position": 56,
      "status_code": 1,
      "last_target_ts": "2026-03-26T09:17:02+00:00",
      "last_status_ts": "2026-03-26T13:18:13+00:00"
    }
  ]
}
```

Raw `/frames` endpoint v produkci není potřeba mít zapnutý trvale.

## Doporučený provoz jako systemd služby

Na Zero bych doporučil dvě možnosti:

### Varianta A: Jeden proces

Jeden proces dělá:

- sniffer,
- parser,
- state engine,
- MQTT publish,
- HTTP health API.

Výhody:

- jednodušší provoz,
- méně IPC,
- méně moving parts.

Nevýhody:

- větší proces,
- o něco těžší debug jednotlivých vrstev.

### Varianta B: Dva procesy

1. `futura-sniffer.service`
2. `futura-bridge.service`

Výhody:

- čistší oddělení,
- snazší výměna bridge logiky bez zásahu do serial části.

Nevýhody:

- komplikovanější provoz,
- typicky větší tlak na mezivrstvu nebo lokální storage.

### Doporučení

Pro `Pi Zero` preferuji:

- jednu službu,
- jeden proces,
- jedna stavová cache,
- žádný mezilog jako hlavní komunikační vrstva.

## Chování po restartu

Po startu aplikace:

1. načíst `damper_map`
2. načíst `state/dampers_state.json`, pokud existuje
3. obnovit stav klapek do RAM
4. připojit `MQTT`
5. přepublikovat poslední známý stav jako `retained`
6. začít sniffovat nové rámce

To znamená:

- už po startu je znám poslední známý stav,
- není potřeba čekat, až se všechny klapky znovu přepozicují,
- a přitom se zbytečně nečte velký historický log.

## Chování při výpadku MQTT

Při výpadku `MQTT` nechci na Zero budovat velkou offline frontu.

Doporučení:

- držet jen aktuální stav v RAM,
- snapshot ukládat dál normálně,
- po obnovení `MQTT` znovu publikovat celý aktuální stav,
- neukládat na disk každou neodeslanou změnu jako frontu.

To je výrazně šetrnější k `SD`.

## Doporučené zdroje pravdy

Na Zero budou dva různé "pravdivé" pohledy:

### Provozní pravda

Aktuální provozní pravda je:

- in-memory stavová cache

### Nouzová obnova

Nouzová obnova je:

- `state/dampers_state.json`

### Dlouhodobá historie

Dlouhodobá historie není úkol Zero.

Tu má držet:

- `MQTT broker` mimo Zero,
- nebo `Home Assistant`.

## Co doporučuji implementovat jako první

### Fáze 1

Tato faze je uz implementovana v:

- [futura_damper_bridge.py](../src/sniffer/futura_damper_bridge.py)

Aktualni stav:

- drzi stav klapek v RAM,
- zpracovava `FC16 / 102`,
- zpracovava `FC4 / 107`,
- mapuje `slave_id -> room` pres `damper-map.json`,
- vystavuje `/dampers`,
- a uklada `state/dampers_state.json`.

### Fáze 2

Přidat:

- `MQTT` publish při změně,
- `retained` zprávy,
- republish po startu.

### Fáze 3

Přidat:

- volitelný debug režim,
- rotační raw log,
- případně dočasné zachytávání jen vybraných `slave_id`.

## Výsledné doporučení

Nejlepší řešení pro `Pi Zero` z hlediska `SD` karty je:

- nepoužívat nekonečný raw log jako hlavní storage,
- neukládat všechny raw rámce do databáze,
- držet hlavní stav v RAM,
- zapisovat na disk jen malý snapshot posledního známého stavu,
- publikovat změny do `MQTT`,
- a raw log mít jen jako dočasný diagnostický nástroj.

Stručně:

```text
RAM jako primární runtime stav
+ retained MQTT mimo Zero jako hlavní externí persistence
+ malý lokální snapshot jako nouzová obnova
+ krátký rotační debug log jen když je potřeba
```

Tohle je nejrozumnější kompromis mezi:

- robustností,
- jednoduchostí,
- spotřebou zdrojů,
- a životností `SD` karty.
