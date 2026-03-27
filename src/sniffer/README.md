# RS485 sniffer

Tato složka je určená pro pasivní odposlech interní komunikace Futury po `RS485`.

Na protokolové úrovni jsou odposlechnutá data dekódovaná jako `Modbus RTU`, ale tato složka není pro přímé `Modbus TCP` čtení. To patří do [../modbus](../modbus/README.md).

## Co je tady produkční a co diagnostické

### `futura_damper_bridge.py`

Produkční bridge pro `Pi Zero` pro běžný provoz.

Dělá:

- pasivní odposlech `RS485`
- dekódování `Modbus RTU` rámců
- odvozování stavu klapek z:
  - `FC16 / registr 102` jako kandidát na cílovou pozici
  - `FC4 / registr 107` jako stavový kód
- udržování stavové cache v `RAM`
- zápis malého snapshotu do `state/dampers_state.json`
- lokální HTTP API:
  - `/health`
  - `/stats`
  - `/latest`
  - `/devices`
  - `/dampers`
  - `/dampers/<slave_id>`
- volitelnou publikaci do `MQTT`

Typické použití v repozitáři:

```bash
cp src/sniffer/pi-zero-config.example.json src/sniffer/pi-zero-config.json
cp src/sniffer/damper-map.example.json src/sniffer/damper-map.json
python src/sniffer/futura_damper_bridge.py --config src/sniffer/pi-zero-config.json
```

Na `Pi Zero` lze stejný bridge provozovat i jako ploché nasazení v `~/futura`, tedy bez `src/` podsložek. V tom případě mají být v `~/futura` vedle sebe alespoň:

- `futura_damper_bridge.py`
- `rs485_modbus_monitor.py`
- `pi-zero-config.json`
- `damper-map.json`
- `requirements.txt`

Spuštění pak vypadá takto:

```bash
cd ~/futura
python futura_damper_bridge.py --config pi-zero-config.json
```

### `rs485_modbus_monitor.py`

Diagnostický monitor pro reverzní analýzu a ladění.

Je vhodný, když potřebujete:

- sledovat surové rámce
- analyzovat páry request/response
- ladit `CRC`
- hledat nové registry nebo neznámé `slave_id`

Typické použití:

```bash
python src/sniffer/rs485_modbus_monitor.py --serial-port /dev/serial0 --baudrate 19200 --parity N --stopbits 1
```

## Další skripty

### `analyze_rs485_log.py`

Shrnutí a analýza logu vytvořených diagnostickým monitorem.

### `extract_rs485_window.py`

Výřez změn registrů v konkrétním časovém okně.

### `extract_rs485_raw_window.py`

Surový výřez validních rámců ze zvoleného časového okna.

## Závislosti

Python závislosti této části jsou v:

- [requirements.txt](requirements.txt)

Instalace:

```bash
pip install -r src/sniffer/requirements.txt
```

Na `Pi Zero` v plochém nasazení tomu odpovídá:

```bash
cd ~/futura
pip install -r requirements.txt
```

## Konfigurace

Sniffer část má dva vzorové soubory:

- [pi-zero-config.example.json](pi-zero-config.example.json)
- [damper-map.example.json](damper-map.example.json)

Podrobné vysvětlení obou souborů je v:

- [../../docs/pi-zero-konfigurace.md](../../docs/pi-zero-konfigurace.md)

Včetně vysvětlení, jak poznat správný `serial.port` a kdy použít `/dev/serial0`.

V repozitáři pro lokální vývoj si vytvořte kopii:

- `src/sniffer/pi-zero-config.json`
- `src/sniffer/damper-map.json`

Tyto lokální konfigurace jsou v `.gitignore`.

Na `Pi Zero` v plochém nasazení odpovídají těmto souborům:

- `~/futura/pi-zero-config.json`
- `~/futura/damper-map.json`

### `pi-zero-config.json`

Obsahuje runtime nastavení bridge:

- `serial`
- `http`
- `mqtt`
- `storage`
- `debug`
- `damper_map`

### `damper-map.json`

Obsahuje mapu klapek pro konkrétní instalaci:

- `slave_id`
- `room`
- `zone`
- `type`
- `damper_index`
- `label`
- `enabled`

Pro aktuální známou topologii tohoto domu vycházejte z [../../docs/mapa-klapek.md](../../docs/mapa-klapek.md).

## Doporučený provozní režim na Pi Zero

Pro běžný provoz:

- používejte `futura_damper_bridge.py`
- nechte `raw_log_enabled` vypnuté
- stav držte v `RAM` a snapshotujte jen periodicky
- `MQTT` zapínejte až když máte broker a topicy připravené

Pro ladění a reverzní analýzu:

- používejte `rs485_modbus_monitor.py`
- zapínejte ho jen když potřebujete hledat nové registry nebo kontrolovat raw provoz

## Jak ověřit, že proces na Zero běží

### Když je bridge spuštěn ručně

Ověření procesu:

```bash
pgrep -af "futura_damper_bridge.py"
```

Ověření, že naslouchá HTTP API:

```bash
ss -ltnp | grep 8765
```

Ověření health endpointu:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/dampers
```

### Když je bridge spuštěn jako `systemd` služba

Stav služby:

```bash
sudo systemctl status futura-damper-bridge
```

Živé logy:

```bash
sudo journalctl -u futura-damper-bridge -f
```

### Když běží diagnostický monitor

Ověření procesu:

```bash
pgrep -af "rs485_modbus_monitor.py"
```

Stav služby:

```bash
sudo systemctl status rs485-modbus-monitor
```

Živé logy:

```bash
sudo journalctl -u rs485-modbus-monitor -f
```

Ověření API:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/stats
```

## Pravidlo rozdělení složek

- `src/sniffer` = pasivní odposlech `RS485` a analýza interní komunikace `Modbus RTU`
- `src/modbus` = přímé `Modbus TCP` nástroje
