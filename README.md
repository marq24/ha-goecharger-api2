# Home Assistant Integration 'go-eCharger APIv2 Connect'

![logo](https://github.com/marq24/ha-goecharger-api2/raw/main/logo.png)

Support for all go-eCharger Wallboxes supporting the APIv2 - __of course__ the APIv2 have to be enabled via the go-eCharger mobile app, __before__ you can use this integration.

[![hacs_badge][hacsbadge]][hacs] [![BuyMeCoffee][buymecoffeebadge]][buymecoffee] [![PayPal][paypalbadge]][paypal]

## Main features
 
 - __All documented fields__ [in the official go-eCharger GitHub repository](https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md) are supported by this integration (with very few exceptions)
 - Support for 'PV surplus charging' (PV-Überschuss Laden) __without additional hardware__ - no need to pay for evcc. In order to use this feature a small additional manual setup process is required [[details can be found below](#pvsurplus)]
 - For all go-eCharger (status) fields that support a numeric status code, this code is available as separate sensor
 - Multilanguage support: a German translation included (any feedback highly appreciated!) & looking forward to other language contributions
- Hibernation-Mode: only request sensor data from wallbox when system is in use [[details can be found below](#hibernation)]
  
  Please note that the configuration data will be read only every 24hours from the hardware (to save data) - but you can update the sensors any time with an 'update' button.


## Disclaimer

Please be aware, that we are developing this integration to best of our knowledge and belief, but cant give a guarantee. Therefore, use this integration **at your own risk**.

## Installation

### via HACS

1. Add a custom integration repository to HACS: [https://github.com/marq24/ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2)
1. Install the custom integration
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "go-eCharger APIv2 Connect"
1. Setup the go-eCharger custom integration as described below

  <!--1. In HACS Store, search for [***marq24/ha-goecharger-api2***]-->

### manual steps

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `goecharger_api2`.
4. Download _all_ the files from the `custom_components/goecharger_api2/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "go-eCharger APIv2 Connect"

## Adding or enabling the integration

### My Home Assistant (2021.3+)

Just click the following Button to start the configuration automatically:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=goecharger_api2)

### Manual steps

Use the following steps for a manual configuration by adding the custom integration using the web interface and follow instruction on screen:

- Go to `Configuration -> Integrations` and add "go-eCharger APIv2 Connect" integration
- Provide the IP address (or hostname) of your go-eCharger web server
- Provide area where the wallbox is located

After the integration was added you can use the 'config' button to adjust your settings, you can additionally modify the update interval
<a id="pvsurplus"></a>

Please note, that some of the available sensors are __not__ enabled by default.


## Enable PV Surplus Charging via HA automation

When you use this integration you do not need any additional hardware (go-eController) in order to allow PV surplus charging. The only thing that is required to add a HA automation fetching the data from your grid & solar power entities.

__Once you have enabled the automation, you obviously also need to enable the 'Use PV surplus charging' setting of your go-eCharger!__

Please note, that __only__ the `pgrid` value is required - the other two fields/sensors are just _optional_.

### Example automation

Please note that this example is for a for SENEC.Home System - if you are using 'my' SENEC.Home Integration you can use the code below 1:1 - in any other case: __You must adjust/replace the sensor identifiers!!!__. So if you are not a SENEC.Home user please replace the following:

- `sensor.senec_grid_state_power` with the entity that provide the information in WATT you're currently consuming from the grid (positive value) or you are exporting to the grid (negative value). Once the value is negative the go-eCharger might use the available power to start with charging your car.
- _optional_ `sensor.senec_solar_generated_power` with the entity that provided the total power generation by your PV (in WATT)
- _optional_ `sensor.senec_battery_state_power` with the entity that provided the power in WATT currently will be used to charge an additional battery (positive value) or will be consumed from the battery (negative value).

```
alias: go-e surplus charging
description: >-
  Simple automation to update values needed by go-eChargers for using solar surplus charging.
trigger:
  - platform: time_pattern
    seconds: /5
condition: []
action:
  - service: goecharger_api2.set_pv_data
    data:
      pgrid: "{{states('sensor.senec_grid_state_power')}}"
      ppv:  "{{states('sensor.senec_solar_generated_power')}}"
      pakku: "{{states('sensor.senec_battery_state_power')}}"
mode: single
```

<a id="hibernation"></a>

### Hibernation-Mode - Good to know 

This integration will __not always fetch all sensor data from your wallbox__. For example the configuration values - they probably do not change every 5 sec. - so in order to reduce the overall system load the integration will refresh the configuration entities just every 24h - OR when you make adjustments to any of the go-eCharger settings via HA. If you want to manually sync the configuration sensors, then you can use the `button.goe_[serial]_zfocore` [^1] ['Read Configuration' button].

Additionally, to the configuration values the number of entities that will be refreshed when no vehicle is connected (car state = 'Idle'), is also drastically reduced. In this case, the integration will __only__ read the full data set __every 5 minutes__ from your wallbox.

So the integration have some _sort of hibernation-mode_ in which only the following entities will be frequently read from your wallbox (based on the configured update interval):
  
 - __car__: vehicle connection status 
 - __modelStatus__: wallbox status
 - __err__: possible error status
 - __nrg__: power values
 - __tma__: temperature values
 
and when you make use of the PV Surplus Charging fature additionally the values for: 
 - pgrid
 - ppv
 - pakku

Once the __car__ status will switch from `idle` (=1) to something different the integration will leave the hibernation-mode and update all the (none configuration) entities.

## Want to report an issue?

Please use the [GitHub Issues](https://github.com/marq24/ha-goecharger-api2/issues) for reporting any issues you encounter with this integration. Please be so kind before creating a new issues, check the closed ones, if your problem have been already reported (& solved).

In order to speed up the support process you might like already prepare and provide DEBUG log output. In the case of a technical issue, I would need this DEBUG log output to be able to help/fix the issue. There is a short [tutorial/guide 'How to provide DEBUG log' here](https://github.com/marq24/ha-senec-v3/blob/master/docs/HA_DEBUG.md) - please take the time to quickly go through it.

---

###### Advertisement / Werbung - alternative way to support me

### Switch to Tibber!

Be smart switch to Tibber - that's what I did in october 2023. If you want to join Tibber (become a customer), you might want to use my personal invitation link. When you use this link, Tibber will we grant you and me a bonus of 50,-€ for each of us. This bonus then can be used in the Tibber store (not for your power bill) - e.g. to buy a Tibber Bridge. If you are already a Tibber customer and have not used an invitation link yet, you can also enter one afterward in the Tibber App (up to 14 days). [[see official Tibber support article](https://support.tibber.com/en/articles/4601431-tibber-referral-bonus#h_ae8df266c0)]

Please consider [using my personal Tibber invitation link to join Tibber today](https://invite.tibber.com/6o0kqvzf) or Enter the following code: 6o0kqvzf (six, oscar, zero, kilo, quebec, victor, zulu, foxtrot) afterward in the Tibber App - TIA!

---

### References

- https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md

[^1]: `focore` stands for: FOrce COnfiguration REquest


[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

[buymecoffee]: https://www.buymeacoffee.com/marquardt24
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a-coffee-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[paypal]: https://paypal.me/marq24
[paypalbadge]: https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&logo=paypal&logoColor=ccc
