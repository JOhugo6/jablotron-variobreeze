[Česky](cil-home-assistant.md) | **English**

# Home Assistant Integration Goal

## Main Goal

The goal of this project is to make the actual damper states of the `Jablotron Futura` system accessible in `Home Assistant`, so that it is possible to:

- display the state of individual dampers by room,
- store damper state history in `Home Assistant`,
- compare damper states with air quality, particularly `CO2`,
- later build automations and graphs on top of damper history.

## What Should Be Visible in Home Assistant

For each damper, the following should be primarily available in `Home Assistant`:

- the current damper position in `%` or another stable numeric scale, if the Futura actually provides it that way.

Only as a temporary fallback:

- `open / closed` state,
- optionally the raw register value, if it helps with debugging.

Typical entities might look like this:

- `sensor.futura_klapka_obyvak_1_poloha`
- `binary_sensor.futura_klapka_obyvak_1_otevrena`
- `sensor.futura_klapka_obyvak_1_raw`

## History Storage

Damper state history should not be handled by the `Pi Zero 2`.

History will be stored by `Home Assistant` itself, because:

- it is already running on the network on a `Raspberry Pi 5`,
- it has its own internal history and database,
- it can build graphs, statistics, and automations on top of that data.

The `Pi Zero 2` should function only as a passive data collector and publisher.

## Target Architecture

```text
Jablotron Futura RS485
        ->
Raspberry Pi Zero 2 W
  - passive RS485 sniffing
  - decoding damper communication
  - converting to readable states
  - publishing to MQTT
        ->
Home Assistant on Raspberry Pi 5
  - MQTT reception
  - history storage
  - visualization
  - comparison with CO2 / air quality
```

## What the Pi Zero 2 Should Do

The `Pi Zero 2` should:

- passively sniff the internal `RS485 / Modbus RTU` communication of the Futura,
- identify individual dampers by `slave_id`,
- evaluate their state or position from the communication,
- send the resulting values over the network to `Home Assistant`.

The `Pi Zero 2` should not:

- actively control the Futura,
- transmit to the `RS485` bus,
- serve as the primary history storage.

## What Home Assistant Should Do

`Home Assistant` should:

- receive damper states from the network,
- store their history,
- allow comparison of damper states with `CO2`, humidity, or other air quality sensors,
- provide long-term graphs and optional automations.

## Currently Confirmed Status

Currently confirmed:

- passive `RS485` sniffing works,
- `19200 8N1` is the correct setting,
- the `DIP -> slave_id` map has been derived and matches the captured communication,
- individual dampers are identifiable as separate nodes on the bus,
- the parser now reliably assembles longer `Modbus RTU` responses as well.

Detailed reverse engineering of the bus, `slave_id` mapping, interpretation of registers `102` and `107`, and specific captured values are maintained only in [mapa-klapek.en.md](mapa-klapek.en.md).

For the integration layer, only the following is currently important:

- `FC16 / register 102` is the strongest candidate for the target position or requested damper opening,
- `FC4 / register 107` behaves as a status code or reaction state of the damper,
- `register 102` is an event-based write, not a periodically transmitted state.

## Implications for Home Assistant

For `Home Assistant`, this means:

- the last known target damper position needs to be held statefully in the application; do not wait for the Futura to periodically retransmit it,
- the `Pi Zero 2` or the MQTT publisher must update the internal state of the given damper after capturing `FC16 / register 102`,
- after a restart of the sniffer or `Home Assistant`, the current position will not be known immediately unless a new write has occurred since then,
- therefore it is advisable to persist the last known value of `register 102` outside of RAM, for example:
  - in retained `MQTT` messages,
  - or in a local state file on the `Pi Zero 2`.

## Next Practical Goal

The nearest technical goal is:

1. reliably decode longer responses from the `RS485`,
2. determine which registers or values correspond to the actual damper positions,
3. convert them into a stable data model organized by rooms,
4. publish these states to `MQTT`,
5. connect `MQTT` entities to `Home Assistant`.
