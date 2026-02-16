# Home Assistant Integration 'go-eCharger & go-eController [via APIv2]'

![logo](https://github.com/marq24/ha-goecharger-api2/raw/main/logo.png)

Support for all go-eCharger Wallboxes & go-eController's supporting the APIv2 — __of course__ the APIv2 has to be enabled via the go-e mobile app, __before__ you can use this integration [[see instructions](#enable-http-api-v2-in-go-echarger-app)].

> [!IMPORTANT]
> __Please note__, _that this integration is not official and not supported by the go-e development team. I am not affiliated with go-e.com in any way. This integration is based on the go-e API and the go-e API documentation._


[![hacs_badge][hacsbadge]][hacs] [![hainstall][hainstallbadge]][hainstall] [![Wero][werobadge]][wero] [![Revolut][revolutbadge]][revolut] [![PayPal][paypalbadge]][paypal] [![github][ghsbadge]][ghs] [![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

## latest successfully tested go-eCharger Firmware Versions / go-eController Firmware Versions

Technically, there should be no issues using always the latest go-eCharger & go-eController firmware versions available. As long as the API will just add additional fields and not change the existing ones, this integration should work with all go-eCharger & go-eController firmware versions.

### go-eCharger Firmware Versions

List of confirmed working go-eCharger Firmware versions with this integration:
- 60.3 (60.2 had general connection issues)
- 59.4
- 57.0 & 57.1
- 56.2 - 56.11
- 055.0, 055.5, 055.7, 055.8
 
### go-eController Firmware Versions

List of confirmed working go-eController Firmware versions with this integration:
- 1.1.1

If you have any issues with this integration after you updated your go-eCharger firmware — as [reported here: #11](https://github.com/marq24/ha-goecharger-api2/issues/11) — then please be so kind and downgrade the firmware again and create an issue. TIA

## Main features
 
### go-eCharger

 - __All documented fields__ [in the official go-eCharger GitHub repository](https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md) are supported by this integration (with very few exceptions) [[see list of currently not handled API keys](#list-of-currently-not-handled-api-keys-27172)]
 - Support for 'PV surplus charging' (PV-Überschuss Laden) __without additional hardware__ — no need to pay for evcc. In order to use this feature, a small additional manual setup process is required [[details can be found below](#enable-pv-surplus-charging-via-ha-automation)]
 - For all go-eCharger (status) fields that support a numeric status code, this code is available as a separate sensor
 - Multilanguage support: a German translation included (any feedback highly appreciated!) & looking forward to other language contributions
- Hibernation-Mode: only request sensor data from wallbox when a system is in use [[details can be found below](#hibernation-mode--good-to-know)]
  
  Please note that the configuration data will be read only every 24 hours from the hardware (to save data) — but you can update the sensors any time with an 'update' button.

- Owners of a 22kW variant can __force 16A only__ for all relevant settings. (This can be enabled via the integration settings and require a restart of the integration — then with every restart the settings will be inspected and adjusted to a max of 16A if required)

### go-eController
 - This integration [supports __most documented fields__ in the official go-eCharger GitHub repository](https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md).
 - More sensors will follow up
 - Multilanguage support: a German translation included (any feedback highly appreciated!) & looking forward to other language contributions

   Please note that the configuration data will be read only every 24 hours from the hardware (to save data) — but you can update the sensors any time with an 'update' button.

> [!WARNING]
> ## Disclaimer
> Please be aware that we are developing this integration to the best of our knowledge and belief, but can't give a guarantee. Therefore, use this integration **at your own risk**.

## Requirements

### go-eCharger
- go-eCharger Wallbox running Firmware version __56.1__ (or higher)
- enabled APIv2 [[see instructions](#enable-http-api-v2-in-go-e-app)]

### go-eController
- enabled APIv2 Controller running Firmware version __1.1.1__ (or higher)
- enabled APIv2 [[see instructions](#enable-http-api-v2-in-go-e-app)]

## Installation

### Step I: Install the integration

#### Option 1: via HACS

[![Open your Home Assistant instance and adding repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=marq24&repository=ha-goecharger-api2&category=integration)

1. ~~Add a custom integration repository to HACS: [https://github.com/marq24/ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2)~~
2. ~~Once the repository is added,~~ use the search bar and type `go-e APIv2 Connect`
3. Use the 3-dots at the right of the list entry (not at the top bar!) to download/install the custom integration — the latest release version is automatically selected. Only select a different version if you have specific reasons.
4. After you press download and the process has completed, you must __Restart Home Assistant__ to install all dependencies 
5. Setup the go-eCharger custom integration as described below (see _Step II: Adding or enabling the integration_)

  <!--1. In HACS Store, search for [***marq24/ha-goecharger-api2***]-->

#### Option 2: manual steps

1. Using the tool of choice to open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `goecharger_api2`.
4. Download _all_ the files from the `custom_components/goecharger_api2/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. Setup the go-e custom integration as described below (see _Step II: Adding or enabling the integration_)

### Step II: Adding or enabling the integration

__You must have installed the integration (manually or via HACS before)!__

#### Option 1: My Home Assistant (2021.3+)

Just click the following Button to start the configuration automatically (for the rest see _Option 2: Manually step by step_):

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=goecharger_api2)

#### Option 2: Manually step by step

Use the following steps for a manual configuration by adding the custom integration using the web interface and follow instruction on screen:

- Go to `Configuration -> Integrations` and add "go-e APIv2 Connect" integration
- Select what go-e device you would like to install: `go-eCharger` or `go-eController`
- Provide the IP address (or hostname) of your go-eCharger or go-eController web server
- Provide an area/room where the wallbox/controller is located

After the integration was added, you can use the 'config' button to adjust your settings, you can additionally modify the update interval
<a id="pvsurplus"></a>

Please note that some of the available sensors are __not__ enabled by default.

## go-eCharger 

### Websocket – use local/cloud push (instead of polling)

The integration can use the (undocumented) go-eCharger Websocket API to receive the current status of your wallbox (or sending data to the wallbox). 

Using the websocket communication makes the polling interval obsolete, and you will get the latest data in HA as soon as something changes. This includes any changes in the wallbox configuration (this makes the _refresh_/_configuration sync_ button obsolete).

To enable the websocket communication, you need to provide a password for your charger. This password is used to authenticate the websocket connection and to prevent unauthorized access to your wallbox data.

Open the Integration configuration and provide the password for your go-eCharger. Once a password is available for the integration, it will use the websocket communication. This applies to the local and the cloud connection variants.

If you can't remember the password, you can set a new one via the go-eApp:

![set-password](https://github.com/marq24/ha-goecharger-api2/raw/main/res/app006.png)

### Enable PV Surplus Charging via HA automation

When you use this integration, you do not need the additional hardware (go-eController) in order to allow PV surplus charging. The only thing that is required is to add a __Home Assistant automation__ fetching the data from your grid & solar power entities and provide this data to a service of this integration.

__If you are not familiar with 'creating an automation in Home Assistant', then [you might like to start with a tutorial explaining the basics of automation in HA](https://www.home-assistant.io/getting-started/automation/).__ 

> [!NOTE]
> __only__ the `pgrid` value is __required__ — the other two fields `ppv` & `pakku` are just _optional_.

> [!NOTE]
> The goeCharger will drop the __stored data after 5 seconds__ — so if the automation is not running/sending data every five seconds (or faster) to the wallbox the 'PV Surplus Charging' is __not going to work__! 

> [!IMPORTANT]
> When you are using the Cloud/WAN connection to communicate with your go-eCharger, then the service of this integration will additionally check __if the go-eCharger is connected with a vehicle__ (API-key `car`). If this is not the case, __the data will not be submitted to the cloud__ (to reduce the load of the cloud service). 

### Do not forget this important setting

Once you have enabled the automation, you also need to:

- __Select the 'logic mode': 'Awattar [Eco]' [API-Key 'lmo']__<br/>[Logik/Modus: ECO-Modus]
- __enable the 'Use PV surplus' [API-Key 'fup']__<br/>[Mit PV-Überschuss laden]
- __enable the 'Allow Charge Pause (car compatibility)'  [API-Key 'acp']__<br/>[Ladepausen zulassen (Fahrzeug Kompatibilität)]
- double check in the _PV surplus settings_, that you have selected:
    - __Power preference: _Prefer power to grid___
    - you have a __negative Grid Target value (e.g. -500W)__

in the setting of your go-eCharger — (this can be done via the integration)

__Please note: in order to be able to enable 'Use PV surplus' in the go-eCharger Application you must also configure the "Flexibler Energietarif" [specify "Preisgrenze", "Country", "Anbieter", "Tarif" and so on] even though the "Flexibler Energietarif" switch is "OFF"__ Probably a bug in the go-echarger software?

### Service fields explained

#### pgrid [**required**]
The power in WATT you're currently consuming from the grid (positive value) or you are exporting to the grid (negative value). So when `pgrid` value is negative, the go-eCharger have the information that there is power available that can be used to charge your car.

So once the value is negative, the go-eCharger might use the available power to start  charging your car (instead of exporting power to the grid).

#### ppv [_optional_]
The power in WATT your PV system currently generating — this value must be positive.
#### pakku [_optional_]
The power in WATT your home-battery currently providing (positive — discharge — power from the battery to your home) or consuming (negative — charge — power form grid/PV to your battery).

With other words, `pAkku` is expected to be negative when the home battery is charging (consume power) and positive when it's currently discharging (provide power).

### Blueprint for PV Surplus Charging

This repository includes a ready-to-use Home Assistant blueprint that automates PV surplus charging setup.

#### Features
- Supports multiple grid measurement methods (single entity, consumption + feed-in, 3-phase)
- Automatic summation of multiple PV/battery entities
- Organized input sections with clear descriptions
- Value inversion options for different inverter conventions

#### Quick Setup
1. Import blueprint:
[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A//raw.githubusercontent.com/marq24/ha-goecharger-api2/refs/heads/main/example/blueprint/automation/go-echarger-pv-surplus-data.yaml)
2. Create automation from blueprint
3. Configure your PV entities
4. Enable ECO mode on go-eCharger

For detailed configuration instructions, see [Blueprint Documentation](example/blueprint/automation/readme.md).

#### Manual PV Setup
If you prefer manual automation setup, use this basic example:

### Example automation

Sending the information about PV Surplus is only relevant when a vehicle is connected to the wallbox. Therefore, any automation should contain the condition if there is a vehicle connected to the wallbox. This can be done via the `binary_sensor.goe_012345_car_0` sensor. (replace the `012345` with your serial number).

Please note that this example is for a for SENEC.Home System — if you are using 'my' SENEC.Home Integration, you can use the code below 1:1 — in any other case: __You must adjust/replace the sensor identifiers!!!__. So if you are not a SENEC.Home user, please replace the following:

- `sensor.senec_grid_state_power` with the entity that provides the information in WATT you're currently consuming from the grid (positive value), or you are exporting to the grid (negative value). Once the value is negative, the go-eCharger might use the available power to start charging your car.

- `sensor.senec_solar_generated_power` with the entity that provided the total power generation by your PV (in WATT)

- `sensor.senec_battery_state_power` with the entity that provided the power in WATT currently will be used to charge an additional battery (negative value) or will be consumed from the battery (positive value).

```
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

### In case when your `pgrid` (or `pakku`) value provided by the sensor needs to be inverted

In some cases (when using other solar system integrations) you might run into the situation that the pgrid sensor value is positive when you are exporting power to the grid (and negative when you import power from the grid). In this case, you need to ___invert___ the value of your grid sensor. In HA this can be done very easily via the so-called 'pipe' functionality inside templates.

Here is a simple example (just inserted a `| float * -1`) — which takes the sensor value and _convert_ it to a floating point number (from a string) and then multiply it with `-1`)
```
action:
  - service: goecharger_api2.set_pv_data
    data:
      pgrid: "{{states('sensor.other_grid_state_power')|float*-1}}"
      ...
```

### Having multiple go-eChargers in your HA installation?

When you have more than one go-eCharger in your HA installation, you must provide an additional attribute `configid` in order to let the service know which charger should be used! This configid is the ConfigEntryId of the Integration for your multiple chargers and can look like this `01J4GR20JPFQ7M888Q4C9YAR31`.

The simple way to find the corresponding ConfigEntryId's of your multiple configured go-eCharger integrations is by using the GUI of the Service, activate the optional selection field, select the charger and then switch (from GUI) to YAML-Mode mode — this will show you the configid you must use. [[See this image for details](https://raw.githubusercontent.com/marq24/ha-goecharger-api2/main/res/configid.png)]

```
action:
  - service: goecharger_api2.set_pv_data
    data:
      configid: 01J4GR20JPFQ7M888Q4C9YAR31
    ...
```

_Please note that this is __only__ required if you have multiple go-eChargers configured via this integration your HA installation._

### Finally: Verify if the wallbox receives your data from the automation

After you have your automation up and running, you might want to verify that everything is correctly connected.

When you use the Cloud/WAN connection, make sure that the wallbox is connected with a vehicle, since only then the integraion will send the pv-data will to the cloud.

#### Via Integration sensors
Search for the Integration Sensors `_pgrid`, `_ppv` & `_pakku` and check the values — or check the `pvopt_average` sensors for the current calculating average values.  

#### Via direct accessing the API (via browser)
Replace in the URLs the `[wallbox-ip]` with the ip-address or hostname of your go-eCharger.

`http://[wallbox-ip]/api/status?filter=pakku,ppv,pgrid`

Please note that the wallbox drops the stored data after 5 seconds — so if the automation is not running/sending data to the wallbox these values become 'null'.  

So you might like to check the average values (to verify if the wallbox received in the recent past some data):

`http://[wallbox-ip]/api/status?filter=pvopt_averagePAkku,pvopt_averagePGrid,pvopt_averagePPv`

### _Optional_ — Force stop charging when PV power is too low

Unfortunately, it might happen [reported by a user] that the go-eCharger __does not finish charging in ECO mode__ using the PV power (in a timely manner). If you run into the same situation, then you can ensure that charging stops when there is no longer enough PV power, by adding the following automation:

You need to adjust the entity ids: `switch.goe_012345_fup`, `sensor.goe_012345_nrg_11` and `sensor.goe_012345_pvopt_averagepgrid` (replace the `012345` with your serial number) and your preferred threshold when this automation should be executed (the `above: -200` for the `pvopt_averagepgrid` means, that as soon as the average power you export to the grid is less than 200 watt the automation will be triggered).

```
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

<a id="hibernation"></a>

### Hibernation-Mode — Good to know 

This integration will __not always fetch all sensor data from your wallbox__. For example, the configuration values — they probably do not change every 5 sec. — so to reduce the overall system load the integration, will refresh the configuration entities just every 24h — OR when you make adjustments to any of the go-eCharger settings via HA. If you want to manually sync the configuration sensors, then you can use the `button.goe_[serial]_zfocore` [^1] ['Read Configuration' button].

Additionally, to the configuration values, the number of entities that will be refreshed when no vehicle is connected (car state = 'Idle') is also drastically reduced. In this case, the integration will __only__ read the full data set __every 5 minutes__ from your wallbox.

So the integration has some _sort of hibernation-mode_ in which only the following entities will be frequently read from your wallbox (based on the configured update interval):
  
 - __car__: vehicle connection status 
 - __modelStatus__: wallbox status
 - __err__: possible error status
 - __nrg__: power values
 - __trx__: authorization required/unlocked (with Card ID)
 - __tma__: temperature values
 
and when you make use of the PV Surplus Charging fature additionally the values for: 
 - pgrid
 - ppv
 - pakku

Once the __car__ status will switch from `idle` (=1) to something different the integration will leave the hibernation-mode and update all the (none configuration) entities with the configured update interval.

<a id="enableapiv2"></a>

### List of (currently) not handled API keys (21/172)

Just as reference, here is the list of API keys that the current implementation of the integration will __not__ handle:

- atp: nextTripPlanData (debug)
- awc: awattar country (Austria=0, Germany=1)
- ccu: charge controller update progress (null if no update is in progress)
- cch: color_charging, format: #RRGGBB
- cfi: color_finished, format: #RRGGBB
- cid: color_idle, format: #RRGGBB
- cwc: color_waitcar, format: #RRGGBB
- clp: current limit presets, max. 5 entries
- del: set this to 0-9 to clear card (erases card name, energy and rfid id)
- delw: set this to 0-9 to delete sta config (erases ssid, key, ...)
- ferm: effectiveRoundingMode
- fna: friendlyName
- ido: Inverter data override
- loc: local time
- log: load_group_id
- lrn: set this to 0-9 to learn last read card id
- oct: firmware update trigger (must specify a branch from ocu)
- tof: timezone offset in minutes
- utc: utc time
- wsc: WiFi STA error count
- wsm: WiFi STA error message

## go-eController
Implementation of eController features has been provided by [@s3ppo (Harald Wiesinger)](https://github.com/s3ppo) — thank you very much! 

## go-eCharger & go-eController [COMON]

### Enable HTTP API v2 in go-e App [v4.x]
[screenshots are from the Android version]

1. Start the go-er App
2. Select '_Setting_' (lower main button bar)
3. Select '_Connection_' section as shown here:

   '![step1](https://github.com/marq24/ha-goecharger-api2/raw/main/res/app003.png)

4. Select '_API Settings_' section as shown here:

   '![step2](https://github.com/marq24/ha-goecharger-api2/raw/main/res/app004.png)
5. Toggle the '_Allow local HTTP API v2_' as shown here:

   ![step3](https://github.com/marq24/ha-goecharger-api2/raw/main/res/app005.png)

### Enable HTTP API v2 in go-e App [v3.x]
[screenshots are from the Android version]

1. Start the go-e App
2. Select '_Internet_'
3. Enable '_Advanced Settings_' as shown here:

   '![step1](https://github.com/marq24/ha-goecharger-api2/raw/main/res/app001.png)
4. Toggle the '_Access to /api/status and /api/set API_' (_Allow local HTTP API v2_) as shown here:

   ![step1](https://github.com/marq24/ha-goecharger-api2/raw/main/res/app002.png)
5. __DO not forget__ to press the save Icon!

<a id="notimplementedkeys"></a>

### Want to report an issue?

Please use the [GitHub Issues](https://github.com/marq24/ha-goecharger-api2/issues) for reporting any issues you encounter with this integration. Please be so kind before creating a new issues, check the closed ones if your problem has been already reported (& solved).

#### 1. Consider providing DEBUG Log output

To speed up the support process, you might like to already prepare and provide DEBUG log output. In the case of a technical issue, I would need this DEBUG log output to be able to help/fix the issue. There is a short [tutorial/guide 'How to provide DEBUG log' here](https://github.com/marq24/ha-senec-v3/blob/main/docs/HA_DEBUG.md) — please take the time to quickly go through it.

For this integration, you need to add:
```
logger:
  default: warning
  logs:
    custom_components.goecharger_api2: debug
```

#### 2. In case of implausible data

It will happen that the data that is displayed by this integration does not make much sense (to you) — aka 'the data is not plausible.' __Of course,__ it could be the case, that something in this integration has been messed up — but so far — in all reported issues the root cause of implausible data was/is, that the go-e device itself already provided this data [you can check this by directly requesting the attribute from the wallbox]

Each sensor of this integration has an API-Key identifier in its entity ID. You can manually request values from your wallbox by using this __API key__ via a regular web browser.

E.g., assuming the value of the sensor in question is `sensor.goe_123456_tpa` and your wallbox/controller is reachable via the IP `192.168.22.10`, then you can request/read the 'original' value via the following link (where `tpa` is the API key):

`http://192.168.22.10/api/status?filter=tpa`

so the pattern is:

`http://[device-ip]/api/status?filter=[API-KEY]`

If the plain data that will be returned in such a request is matching the data displayed by the integration, then I would kindly ask to get in contact with go-e, since in such a case the integration is just the 'messenger.'

## 

---
###### Advertisement / Werbung — alternative way to support me

### Switch to Tibber!

Be smart switch to Tibber — that's what I did in october 2023. If you want to join Tibber (become a customer), you might want to use my personal invitation link. When you use this link, Tibber will we grant you and me a bonus of 50,-€ for each of us. This bonus then can be used in the Tibber store (not for your power bill) — e.g., to buy a Tibber Bridge. If you are already a Tibber customer and have not used an invitation link yet, you can also enter one afterward in the Tibber App (up to 14 days). [[see official Tibber support article](https://support.tibber.com/en/articles/4601431-tibber-referral-bonus#h_ae8df266c0)]

Please consider [using my personal Tibber invitation link to join Tibber today](https://invite.tibber.com/6o0kqvzf) or Enter the following code: 6o0kqvzf (six, oscar, zero, kilo, quebec, victor, zulu, foxtrot) afterward in the Tibber App — TIA!

---

### References

- https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md
- https://github.com/goecharger/go-eController-API/blob/main/apikeys-en.md

[^1]: `focore` stands for: FOrce COnfiguration REquest


[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Default-blue?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

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

[hainstall]: https://my.home-assistant.io/redirect/config_flow_start/?domain=goecharger_api2
[hainstallbadge]: https://img.shields.io/badge/dynamic/json?style=for-the-badge&logo=home-assistant&logoColor=ccc&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.goecharger_api2.total
