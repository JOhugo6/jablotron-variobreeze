[Česky](poznamky-z-technickeho-centra-jablotron.md) | **English**

# Notes from the Jablotron Technical Center

## Source

Summary of the `Jablotron` technical center's response regarding:

- indoor humidity,
- enthalpic moisture recovery,
- `VarioBreeze` damper positioning algorithm.

The source text comes from a technical center response provided by the project user.
This document separates information declared by the manufacturer from findings obtained through passive `RS485` sniffing.

## Humidity and Enthalpy

The technical center states:

- in cold periods, low indoor humidity is a common problem because cold outdoor air carries little moisture,
- comfortable absolute indoor humidity is approximately `7 to 10 g/m3`,
- this corresponds roughly to `40 to 60 % RH` at `20.5 °C`,
- in the specific assessed state, the indoor conditions were:
  - `24.3 °C`,
  - `37.3 % RH`,
  - `8.3 g/m3` absolute humidity,
- the outdoor conditions in the same example were:
  - `14 °C`,
  - `48.2 % RH`,
  - `5.8 g/m3` absolute humidity.

Principle of the enthalpic heat exchanger according to the response:

- if the outdoor temperature is below the indoor dew point, condensate forms in the warmer exhaust air stream,
- the damper system reverses the airflow direction after a certain period,
- some of the moisture created this way is returned to the interior,
- however, not all of it is ever returned, so the interior may gradually dry out, but more slowly than without enthalpy recovery,
- under unfavorable conditions, no condensate forms,
- when a large amount of condensate is produced, part of it drains to waste.

## Moisture Recovery Settings

According to the technical center, the settings in the application:

- `DRY` corresponds to humidity below `40 % RH`,
- `COMFORTABLE` corresponds to the range `40 to 60 % RH`,
- `HUMID` corresponds to conditions above `60 % RH`.

Purpose of this setting:

- it affects the frequency of damper flipping,
- it relates to the current indoor humidity,
- at low indoor humidity with the `HUMID` setting, dampers may flip approximately every `8 minutes`,
- in extreme cases, the interval can be as short as about `3 minutes`,
- the goal is to return moisture until the interior reaches the specified level.

## Damper Positioning Algorithm

The technical center explicitly states that damper positioning is based on the initial air analysis during installation.
According to them, the unit measures:

- total system throughput,
- throughput of individual routes,
- pressure losses required to achieve the desired flow rates.

### Exhaust Dampers

According to the response:

- exhaust dampers are fully open by default in the standard setting,
- the exception is when a damper is used in `boost` or `range hood` mode,
- for `boost`, the standard setting is exhaust through one damper at `50 m3/h`,
- if the total Futura output delivers for example `150 m3/h`, the boosted damper opens fully and the others share the remaining `100 m3/h`,
- the `range hood` mode is set to `120 m3/h` by default,
- nominal flow rates can be configured for both exhaust and supply dampers.

### Supply Dampers

According to the technical center, the following inputs factor into their positioning calculation:

- total system pressure loss,
- pressure loss of each route,
- total current airflow volume,
- request from `CO2 / TEMP / MAX` control in percent,
- nominal airflow volume of the zone.

Additional declared properties:

- at manual Futura power levels `1 to 5`, dampers are positioned in a fixed manner,
- in `AUTO` mode, the Futura power is controlled by a linear relationship between power and the maximum `CO2` in any of the zones,
- zones with higher `CO2` should be opened more than zones where ventilation is not needed,
- the relationship between damper opening and airflow is not linear but logarithmic.

## Data Visible in the Jablotron Cloud

The technical center stated that in this particular installation, they can see in the cloud:

- data from the `ALFA` in the `Living room`,
- data from one external sensor in `zone 3`.

They also stated that:

- dampers open the most overnight in `zone 7`,
- if this is a bedroom for two people, they recommend adjusting the nominal flow rates or the slope of the power-to-`CO2` dependency curve.

## Impact on This Project

For sniffing and integration into `Home Assistant`, the following from the response is mainly important:

- the actual damper position is internally controlled and depends on multiple input variables,
- according to the manufacturer, these inputs include at minimum `CO2`, `temperature`, `nominal values`, pressure losses, and total unit power,
- the damper position itself may therefore not be a simple one-dimensional value derivable from a single sensor,
- the manufacturer's response supports the sniffing conclusion that the `ALFA` in the `Living room` is a significant control input for zone 1,
- if we cannot passively find a direct position register, it is still valuable to bring into `Home Assistant`:
  - `ALFA` sensors,
  - damper status codes,
  - and temporal correlation between `CO2 / RH / temperature` and damper responses.

## Interpretation Note

The information in this file is:

- declared by the manufacturer or technical support,
- not all of it has been independently confirmed through passive sniffing yet,
- but it is important as a guide for further searching for the actual damper position.
