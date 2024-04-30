# Home Assistant Integration 'go-eCharger APIv2 Connect'

![logo](https://github.com/marq24/ha-goecharger-api2/raw/main/logo.png)

Support vor all go-eCharger Wallboxes supporting APIv2 - all Fields documented [in the official go-eCharger github repository](https://github.com/goecharger/go-eCharger-API-v2/blob/main/apikeys-en.md) are supported.

This integration also support a German translated interface and sensor names & values.

For all go-eCharger (status) fields that support a numeric status code, this code is available as separate sensor.

Please note that the configuration data will be read only every 24hours from the hardware (to save data) - but you can update the sensors any time with an 'update' button.

[![hacs_badge][hacsbadge]][hacs] [![BuyMeCoffee][buymecoffeebadge]][buymecoffee] [![PayPal][paypalbadge]][paypal]


## Disclaimer

Please be aware, that we are developing this integration to best of our knowledge and belief, but cant give a guarantee. Therefore, use this integration **at your own risk**.

### HACS

1. Add a custom integration repository to HACS: [ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2)
1. Install the custom integration
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "go-eCharger APIv2 Connect"
1. Setup the waterkotte custom integration as described below

  <!--1. In HACS Store, search for [***marq24/ha-goecharger-api2***]-->

### Manual

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

### Manual

Use the following steps for a manual configuration by adding the custom integration using the web interface and follow instruction on screen:

- Go to `Configuration -> Integrations` and add "Waterkotte" integration
- Provide the IP address (or hostname) of your Waterkotte Heatpump web server
- Select the Interface-Type of your Waterkotte (when you need to provide the user & password 'waterkotte' to login via your app/browser, then select `EcoTouch Mode`)
- Select the number of TAGs that can be fetched in a single call to your device (older devices might need to adjust this value - for my in 2022 installed Waterkotte 75 is totally fine)
- Provide area where the heatpump is located

After the integration was added you can use the 'config' button to adjust your settings and you can additionally modify the update intervall

Please note, that most of the available sensors are __not__ enabled by default.


---

###### Advertisement / Werbung - alternative way to support me

### Switch to Tibber!

Be smart switch to Tibber - that's what I did in october 2023. If you want to join Tibber (become a customer), you might want to use my personal invitation link. When you use this link, Tibber will we grant you and me a bonus of 50,-€ for each of us. This bonus then can be used in the Tibber store (not for your power bill) - e.g. to buy a Tibber Bridge. If you are already a Tibber customer and have not used an invitation link yet, you can also enter one afterward in the Tibber App (up to 14 days). [[see official Tibber support article](https://support.tibber.com/en/articles/4601431-tibber-referral-bonus#h_ae8df266c0)]

Please consider [using my personal Tibber invitation link to join Tibber today](https://invite.tibber.com/6o0kqvzf) or Enter the following code: 6o0kqvzf (six, oscar, zero, kilo, quebec, victor, zulu, foxtrot) afterward in the Tibber App - TIA!

---

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

[buymecoffee]: https://www.buymeacoffee.com/marquardt24
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a-coffee-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[paypal]: https://paypal.me/marq24
[paypalbadge]: https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&logo=paypal&logoColor=ccc
