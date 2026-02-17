# PV Surplus Charging with the go-eCharger

![logo](https://github.com/marq24/ha-goecharger-api2/raw/main/logo.png)

 [![Wero][werobadge]][wero] [![Revolut][revolutbadge]][revolut] [![PayPal][paypalbadge]][paypal] [![github][ghsbadge]][ghs] [![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

## Enable PV Surplus Charging via HA automation

When you use this integration, you do not need the additional hardware (go-eController) in order to allow PV surplus charging. The only thing that is required is to add a __Home Assistant automation__ fetching the data from your grid & solar power entities and provide this data to a service of this integration.

__If you are not familiar with 'creating an automation in Home Assistant', then [you might like to start with a tutorial explaining the basics of automation in HA](https://www.home-assistant.io/getting-started/automation/).__ 

> [!NOTE]
> __only__ the `pgrid` value is __required__ — the other two fields `ppv` & `pakku` are just _optional_.

> [!NOTE]
> The goeCharger will drop the __stored data after 5 seconds__ — so if the automation is not running/sending data every five seconds (or faster) to the wallbox the 'PV Surplus Charging' is __not going to work__! 

> [!IMPORTANT]
> When you are using the Cloud/WAN connection to communicate with your go-eCharger, then the service of this integration will additionally check __if the go-eCharger is connected with a vehicle__ (API-key `car`). If this is not the case, __the data will not be submitted to the cloud__ (to reduce the load of the cloud service). 

## Do not forget this important setting

Once you have enabled the automation, you also need to:

- __Select the 'logic mode': 'Awattar [Eco]' [API-Key 'lmo']__<br/>[Logik/Modus: ECO-Modus]
- __enable the 'Use PV surplus' [API-Key 'fup']__<br/>[Mit PV-Überschuss laden]
- __enable the 'Allow Charge Pause (car compatibility)'  [API-Key 'acp']__<br/>[Ladepausen zulassen (Fahrzeug Kompatibilität)]
- double check in the _PV surplus settings_, that you have selected:
    - __Power preference: _Prefer power to grid___
    - you have a __negative Grid Target value (e.g. -500W)__

in the setting of your go-eCharger — (this can be done via the integration)

__Please note: in order to be able to enable 'Use PV surplus' in the go-eCharger Application you must also configure the "Flexibler Energietarif" [specify "Preisgrenze", "Country", "Anbieter", "Tarif" and so on] even though the "Flexibler Energietarif" switch is "OFF"__ Probably a bug in the go-echarger software?

## Service fields explained

### pgrid [**required**]
The power in WATT you're currently consuming from the grid (positive value) or you are exporting to the grid (negative value). So when `pgrid` value is negative, the go-eCharger have the information that there is power available that can be used to charge your car.

So once the value is negative, the go-eCharger might use the available power to start  charging your car (instead of exporting power to the grid).

### ppv [_optional_]
The power in WATT your PV system currently generating — this value must be positive.
### pakku [_optional_]
The power in WATT your home-battery currently providing (positive — discharge — power from the battery to your home) or consuming (negative — charge — power form grid/PV to your battery).

With other words, `pAkku` is expected to be negative when the home battery is charging (consume power) and positive when it's currently discharging (provide power).

## Blueprint for PV Surplus Charging

This repository includes a ready-to-use Home Assistant blueprint that automates PV surplus charging setup.

### Features
- Supports multiple grid measurement methods (single entity, consumption + feed-in, 3-phase)
- Automatic summation of multiple PV/battery entities
- Organized input sections with clear descriptions
- Value inversion options for different inverter conventions

### Quick Setup
1. Import blueprint:
[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A//raw.githubusercontent.com/marq24/ha-goecharger-api2/refs/heads/main/example/blueprint/automation/go-echarger-pv-surplus-data.yaml)
2. Create automation from blueprint
3. Configure your PV entities
4. Enable ECO mode on go-eCharger

For detailed configuration instructions, see [Blueprint Documentation](../example/blueprint/automation/readme.md).

### Manual PV Setup
If you prefer manual automation setup, use this basic example:

## Example automation

Sending the information about PV Surplus is only relevant when a vehicle is connected to the wallbox. Therefore, any automation should contain the condition if there is a vehicle connected to the wallbox. This can be done via the `binary_sensor.goe_012345_car_0` sensor. (replace the `012345` with your serial number).

Please note that this example is for a for SENEC.Home System — if you are using 'my' SENEC.Home Integration, you can use the code below 1:1 — in any other case: __You must adjust/replace the sensor identifiers!!!__. So if you are not a SENEC.Home user, please replace the following:

- `sensor.senec_grid_state_power` with the entity that provides the information in WATT you're currently consuming from the grid (positive value), or you are exporting to the grid (negative value). Once the value is negative, the go-eCharger might use the available power to start charging your car.

- `sensor.senec_solar_generated_power` with the entity that provided the total power generation by your PV (in WATT)

- `sensor.senec_battery_state_power` with the entity that provided the power in WATT currently will be used to charge an additional battery (negative value) or will be consumed from the battery (positive value).

```yaml
alias: go-e PV surplus charging brigde
description: >-
  Simple automation to provide your go-eChargers with the required data so that the wallbox can support PV surplus charging.
trigger:
  - platform: time_pattern
    seconds: /5
conditions:
  - condition: and
    conditions:
      - condition: template
        value_template: "{{states('binary_sensor.goe_123456_car_0')=='on'}}"
      - condition: sun
        after: sunrise
      - condition: sun
        before: sunset
action:
  - service: goecharger_api2.set_pv_data
    data:
      pgrid: "{{states('sensor.senec_grid_state_power')}}"
      ppv:  "{{states('sensor.senec_solar_generated_power')}}"
      pakku: "{{states('sensor.senec_battery_state_power')}}"
mode: single
```

## In case when your `pgrid` (or `pakku`) value provided by the sensor needs to be inverted

In some cases (when using other solar system integrations) you might run into the situation that the pgrid sensor value is positive when you are exporting power to the grid (and negative when you import power from the grid). In this case, you need to ___invert___ the value of your grid sensor. In HA this can be done very easily via the so-called 'pipe' functionality inside templates.

Here is a simple example (just inserted a `| float * -1`) — which takes the sensor value and _convert_ it to a floating point number (from a string) and then multiply it with `-1`)
```yaml
action:
  - service: goecharger_api2.set_pv_data
    data:
      pgrid: "{{states('sensor.other_grid_state_power')|float*-1}}"
      ...
```

## Having multiple go-eChargers in your HA installation?

When you have more than one go-eCharger in your HA installation, you must provide an additional attribute `configid` in order to let the service know which charger should be used! This configid is the ConfigEntryId of the Integration for your multiple chargers and can look like this `01J4GR20JPFQ7M888Q4C9YAR31`.

The simple way to find the corresponding ConfigEntryId's of your multiple configured go-eCharger integrations is by using the GUI of the Service, activate the optional selection field, select the charger and then switch (from GUI) to YAML-Mode mode — this will show you the configid you must use. [[See this image for details](https://raw.githubusercontent.com/marq24/ha-goecharger-api2/main/res/configid.png)]

```yaml
action:
  - service: goecharger_api2.set_pv_data
    data:
      configid: 01J4GR20JPFQ7M888Q4C9YAR31
    ...
```

_Please note that this is __only__ required if you have multiple go-eChargers configured via this integration your HA installation._

## Finally: Verify if the wallbox receives your data from the automation

After you have your automation up and running, you might want to verify that everything is correctly connected.

When you use the Cloud/WAN connection, make sure that the wallbox is connected with a vehicle, since only then the integraion will send the pv-data will to the cloud.

### Via Integration sensors
Search for the Integration Sensors `_pgrid`, `_ppv` & `_pakku` and check the values — or check the `pvopt_average` sensors for the current calculating average values.  

### Via direct accessing the API (via browser)
Replace in the URLs the `[wallbox-ip]` with the ip-address or hostname of your go-eCharger.

`http://[wallbox-ip]/api/status?filter=pakku,ppv,pgrid`

Please note that the wallbox drops the stored data after 5 seconds — so if the automation is not running/sending data to the wallbox these values become 'null'.  

So you might like to check the average values (to verify if the wallbox received in the recent past some data):

`http://[wallbox-ip]/api/status?filter=pvopt_averagePAkku,pvopt_averagePGrid,pvopt_averagePPv`

## _Optional_ — Force stop charging when PV power is too low

Unfortunately, it might happen [reported by a user] that the go-eCharger __does not finish charging in ECO mode__ using the PV power (in a timely manner). If you run into the same situation, then you can ensure that charging stops when there is no longer enough PV power, by adding the following automation:

You need to adjust the entity ids: `switch.goe_012345_fup`, `sensor.goe_012345_nrg_11` and `sensor.goe_012345_pvopt_averagepgrid` (replace the `012345` with your serial number) and your preferred threshold when this automation should be executed (the `above: -200` for the `pvopt_averagepgrid` means, that as soon as the average power you export to the grid is less than 200 watt the automation will be triggered).

```yaml
alias: go-e FORCE STOP of PV surplus charging
description: >-
  Simple automation to ensure that the go-eCharger will stop charging when average PV will drop below given threshold
trigger:
  - platform: time_pattern
    seconds: /5
condition:
  - condition: state
    entity_id: switch.goe_012345_fup
    state: "on"
  - condition: numeric_state
    entity_id: sensor.goe_012345_nrg_11
    above: 200    
  - condition: numeric_state
    entity_id: sensor.goe_012345_pvopt_averagepgrid
    above: -200
action:
  - service: goecharger_api2.stop_charging
mode: single
```

[ghs]: https://github.com/sponsors/marq24
[ghsbadge]: https://img.shields.io/github/sponsors/marq24?style=for-the-badge&logo=github&logoColor=ccc&link=https%3A%2F%2Fgithub.com%2Fsponsors%2Fmarq24&label=Sponsors

[buymecoffee]: https://www.buymeacoffee.com/marquardt24
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a-coffee-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[buymecoffee2]: https://buymeacoffee.com/marquardt24/membership
[buymecoffeebadge2]: https://img.shields.io/badge/coffee-subs-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[paypal]: https://paypal.me/marq24
[paypalbadge]: https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&logo=paypal&logoColor=ccc

[wero]: https://share.weropay.eu/p/1/c/6O371wjUW5
[werobadge]: https://img.shields.io/badge/_wero-me_-blue.svg?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZwogICByb2xlPSJpbWciCiAgIHZpZXdCb3g9IjAgMCA0Mi4wNDY1MDEgNDAuODg2NyIKICAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgo+CiAgPGcKICAgICBjbGlwLXBhdGg9InVybCgjY2xpcDApIgogICAgIHRyYW5zZm9ybT0idHJhbnNsYXRlKC01Ny4zODE4KSI+CiAgICA8cGF0aAogICAgICAgZD0ibSA3OC40MDUxLDMwLjM1NzQgYyAwLDAgLTAuMDE4NSwwIC0wLjAyNzgsMCAtNC4zMTg0LDAgLTcuMzQ2MiwtMi41NzY5IC04LjY0NjEsLTUuOTg4NyBIIDk5LjA2OTggQyA5OS4zMDU3LDIzLjA4NDkgOTkuNDI4MywyMS43NzExIDk5LjQyODMsMjAuNDQxIDk5LjQyODMsOS43NTY3MyA5MS43Mzc1LDAuMDEzODc4NyA3OC40MDUxLDAgdiAxMC41MjcgYyA0LjM0MzksMC4wMTE2IDcuMzQxNiwyLjU4MzcgOC42Mjc2LDUuOTg4NyBoIC0yOS4yOTcgYyAtMC4yMzM2LDEuMjgzNyAtMC4zNTM5LDIuNTk3NiAtMC4zNTM5LDMuOTI3NiAwLDEwLjY5MTMgNy43MDAyLDIwLjQ0MzQgMjAuOTk1NSwyMC40NDM0IDAuMDA5MywwIDAuMDE4NSwwIDAuMDI3OCwwIHYgLTEwLjUyNyB6IgogICAgICAgZmlsbD0iI0NDQ0NDQyIvPgogICAgPHBhdGgKICAgICAgIGQ9Im0gNzguMzc3NCw0MC44ODQ0IGMgMC40NTEsMCAwLjg5NTEsLTAuMDEzOSAxLjMzNDYsLTAuMDM0NyAyLjcwMTcsLTAuMTM2NSA1LjE1MzUsLTAuNjgwMSA3LjMzOTMsLTEuNTU2NyAyLjE4NTgsLTAuODc2NyA0LjEwNTcsLTIuMDgxOCA1LjczODcsLTMuNTM5MSAxLjYzMywtMS40NTczIDIuOTgxNSwtMy4xNjQzIDQuMDI3LC01LjA0NDkgMC45NTA2LC0xLjcwOTQgMS42NDQ1LC0zLjU1OTkgMi4wNzk0LC01LjQ5MTMgSCA4Ni42NzIgYyAtMC4yNDk4LDAuNTE1OCAtMC41NDEzLDEuMDA4NSAtMC44NzQ0LDEuNDY4OCAtMC40NTU2LDAuNjI5MSAtMC45ODk5LDEuMjAwNSAtMS41OTYsMS42OTMyIC0wLjYwNiwwLjQ5MjcgLTEuMjg2LDAuOTA5IC0yLjAzNTQsMS4yMzA2IC0wLjc0OTUsMC4zMjE1IC0xLjU2NiwwLjU0ODIgLTIuNDQ5NSwwLjY2MTUgLTAuNDMwMywwLjA1NTUgLTAuODc0NCwwLjA4NzkgLTEuMzM0NywwLjA4NzkgLTIuNzUwMiwwIC00Ljk3NzYsLTEuMDQ3OCAtNi41NjY3LC0yLjY4NzggbCAtNy45NDc2LDcuOTQ3OCBjIDMuNTM2NiwzLjIyOTIgOC40NDI2LDUuMjY0NyAxNC41MTY2LDUuMjY0NyB6IgogICAgICAgZmlsbD0idXJsKCNwYWludDApIgogICAgICAgc3R5bGU9ImZpbGw6dXJsKCNwYWludDApIiAvPgogICAgPHBhdGgKICAgICAgIGQ9Ik0gNzguMzc3NywwIEMgNjcuMTAxNiwwIDU5Ljg1MDIsNy4wMTMzNyA1Ny45MDcyLDE1LjY2OTEgSCA3MC4wOTcgYyAxLjQ1NzIsLTIuOTgxNyA0LjMyNzcsLTUuMTQyMSA4LjI4MDcsLTUuMTQyMSAzLjE1MDMsMCA1LjU5NTIsMS4zNDYyIDcuMTkzNSwzLjM4MTggTCA5My41OTA1LDUuODg5MiBDIDkwLjAwNzYsMi4zMDE1NSA4NC44NTY1LDAuMDAyMzEzMTIgNzguMzc1MywwLjAwMjMxMzEyIFoiCiAgICAgICBmaWxsPSJ1cmwoI3BhaW50MSkiCiAgICAgICBzdHlsZT0iZmlsbDp1cmwoI3BhaW50MSkiIC8+CiAgPC9nPgogIDxkZWZzPgogICAgPGxpbmVhckdyYWRpZW50CiAgICAgICBpZD0icGFpbnQwIgogICAgICAgeDE9IjkyLjc0MzY5OCIKICAgICAgIHkxPSIxOC4wMjYxOTkiCiAgICAgICB4Mj0iNzQuNzU0NTAxIgogICAgICAgeTI9IjQwLjMxMDIiCiAgICAgICBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4wMiIKICAgICAgICAgc3RvcC1jb2xvcj0iI0NDQ0NDQyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwIi8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4zOSIKICAgICAgICAgc3RvcC1jb2xvcj0iI0NDQ0NDQyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwLjY2Ii8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC42OCIKICAgICAgICAgc3RvcC1jb2xvcj0iI0NDQ0NDQyIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxsaW5lYXJHcmFkaWVudAogICAgICAgaWQ9InBhaW50MSIKICAgICAgIHgxPSI2MS4yNzA0MDEiCiAgICAgICB5MT0iMjMuMDE3Nzk5IgogICAgICAgeDI9Ijc5Ljc1NDUwMSIKICAgICAgIHkyPSI0LjUzNDI5OTkiCiAgICAgICBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4wMiIKICAgICAgICAgc3RvcC1jb2xvcj0iI0NDQ0NDQyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwIi8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4zOSIKICAgICAgICAgc3RvcC1jb2xvcj0iI0NDQ0NDQyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwLjY2Ii8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC42OCIKICAgICAgICAgc3RvcC1jb2xvcj0iI0NDQ0NDQyIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxjbGlwUGF0aAogICAgICAgaWQ9ImNsaXAwIj4KICAgICAgPHJlY3QKICAgICAgICAgd2lkdGg9IjE3Ny45MSIKICAgICAgICAgaGVpZ2h0PSI0MSIKICAgICAgICAgZmlsbD0iI2ZmZmZmZiIKICAgICAgICAgeD0iMCIKICAgICAgICAgeT0iMCIgLz4KICAgIDwvY2xpcFBhdGg+CiAgPC9kZWZzPgo8L3N2Zz4=

[revolut]: https://revolut.me/marq24
[revolutbadge]: https://img.shields.io/badge/_revolut-me_-blue.svg?style=for-the-badge&logo=revolut&logoColor=ccc