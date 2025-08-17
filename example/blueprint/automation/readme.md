# go-eCharger PV Surplus Charging Blueprint

This blueprint enables automatic PV surplus charging for go-eCharger wallboxes by transmitting solar system data (grid power, PV generation, battery status) to the charger every 5 seconds.

## Requirements

- Home Assistant 2024.6.0 or newer
- [go-eCharger API2 integration](https://github.com/marq24/ha-goecharger-api2) installed
- go-eCharger configured for PV surplus charging (ECO mode)

## Features

- **Multiple grid measurement methods**: Single entity, consumption + feed-in, or 3-phase entities
- **Flexible PV setup**: Supports multiple PV entities with automatic summation
- **Battery support**: Optional battery data transmission with configurable inversion
- **Daylight operation**: Only active during sunrise to sunset
- **User-friendly UI**: Organized input sections for easy configuration

## Installation

### Option 1: Direct Import
1. Go to **Settings** → **Automations & Scenes** → **Blueprints**
2. Click **Import Blueprint**
3. Use this URL: `https://raw.githubusercontent.com/marq24/ha-goecharger-api2/refs/heads/main/example/blueprint/automation/go-echarger-pv-surplus-data.yaml`

### Option 2: Manual Installation
1. Download `goe_pv_surplus_charging.yaml`
2. Place in `/config/blueprints/automation/`
3. Restart Home Assistant
4. Create automation from blueprint

## Configuration

### Grid Power Setup
Choose **ONE** method:

**Single Entity**: Use if you have one entity with positive (import) and negative (export) values
- Example: `sensor.meter_power_now`

**Consumption + Feed-in**: Use separate entities for consumption and feed-in
- Example: `sensor.grid_consumption` + `sensor.grid_feedin`

**3-Phase Entities**: Use individual phase entities (L1, L2, L3)
- Example: `sensor.grid_l1_power`, `sensor.grid_l2_power`, `sensor.grid_l3_power`

### PV Power
- Select all PV entities (multiple supported)
- Entities are automatically summed
- Enable inversion if your PV entities use negative values

### Battery Power
- Optional battery data transmission
- Multiple entities supported with automatic summation
- Convention: Positive = discharging, Negative = charging

## go-eCharger Setup

1. Enable **ECO mode** (Logic mode: Awattar [Eco])
2. Enable **"Use PV surplus"** (Mit PV-Überschuss laden)
3. Enable **"Allow Charge Pause"** (Ladepausen zulassen)
4. Set **Grid Target** to negative value (e.g., -500W)

## Troubleshooting

- **No data transmission**: Check entity names and availability
- **Wrong values**: Use inversion options for incorrect sign conventions
- **Charging issues**: Verify go-eCharger ECO mode settings
- **Blueprint not visible**: Ensure HA version ≥ 2024.6.0

## Support

For issues with the blueprint, please create an issue in this repository.
For go-eCharger integration issues, see the [main integration documentation](../README.md).
