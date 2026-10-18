# go-eCharger PV Surplus Charging Blueprint

This blueprint enables automatic PV surplus charging for go-eCharger wallboxes by transmitting solar system data (grid power, PV generation, battery status) to the charger every 5 seconds during the day. At night it sends zero values, so the charger never works with stale surplus data.

## Requirements

- Home Assistant 2024.6.0 or newer
- [go-eCharger API2 integration](https://github.com/marq24/ha-goecharger-api2) installed
- go-eCharger configured for PV surplus charging (ECO mode)
- The "car connected" entity (`binary_sensor`) of the go-eCharger API2 integration

## Features

- **Multiple grid measurement methods**: Single entity, consumption + feed-in, or 3-phase entities
- **Flexible PV setup**: Supports multiple PV entities with automatic summation
- **Battery support**: Optional battery data transmission with configurable inversion
- **Unit conversion**: Configurable multiplier for entities that report kW instead of W
- **Day and night aware**: Real values from sunrise to sunset, zero values at night (see [Data transmission](#data-transmission))
- **Only active with a connected car**: Nothing is sent while no car is plugged in (except one zero push at sunset)
- **User-friendly UI**: Organized input sections for easy configuration

## Installation

### Option 1: Direct Import
1. Go to **Settings** → **Automations & Scenes** → **Blueprints**
2. Click **Import Blueprint**
3. Use this URL: `https://raw.githubusercontent.com/marq24/ha-goecharger-api2/refs/heads/main/example/blueprint/automation/go-echarger-pv-surplus-data.yaml`

### Option 2: Manual Installation
1. Download `go-echarger-pv-surplus-data.yaml`
2. Place in `/config/blueprints/automation/`
3. Restart Home Assistant
4. Create automation from blueprint

## Configuration

### Target go-eCharger
Select the go-eCharger integration entry when more than one charger is configured.
All three transmission paths (daylight, night and sunset) use this entry.
Create one automation per charger and select its own **Car connected** entity.

Leaving this input empty preserves the service's existing default selection;
the blueprint omits `configid` rather than passing an empty ID. The service
uses its first registered charger, so select an explicit target for multiple chargers.

With an explicit target, select individual Car connected entities belonging to
that same integration entry. Mixed chargers, device/area targets and a removed
or invalid entry stop the automation with an error visible in its trace.
The blueprint does not silently fall back to another charger.

### Car Connected
Select the "car connected" entity (`binary_sensor`) of your go-eCharger from the API2 integration.
- Example: `binary_sensor.goe_123456_car_0`

### Power Unit Multiplier
The go-eCharger expects **watts**. This factor is applied to grid, PV and battery values before they are sent.
- Entities report **W**: keep the default `1`
- Entities report **kW** (e.g. FoxESS Modbus): set `1000`

The default of `1` keeps the behavior of earlier versions, so existing automations keep working unchanged.

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

## Data Transmission

| Situation | What is sent |
|---|---|
| Sunrise to sunset, car connected | Real values every 5 seconds |
| Night, car connected | Zero values every 30 seconds |
| At sunset | One immediate zero push, regardless of car connection |

### Invalid measurements

Daylight updates require finite numeric states for every used grid and PV
entity and, when enabled, every selected battery entity. `unknown`,
`unavailable`, missing entities, text, NaN and infinity skip the entire update;
they are not replaced with zero or omitted from a partial sum. A real zero is
valid. Each used state is captured once for validation and calculation.
Non-finite totals or unit conversion results also skip the update.

The existing grid method precedence remains single entity, then consumption /
feed-in, then phases. Both consumption and feed-in must be selected; phases
require exactly three distinct entities. An incomplete selected method does
not fall back to another method. Unused grid inputs are ignored.

An empty battery selection means no battery measurement and still sends zero.
Disabling battery transmission ignores any selected battery entities and also
sends zero. An enabled, selected but unavailable battery skips the update.
At least one PV entity is required. The multiplier must be finite and positive.

The failed condition is visible in the automation trace. Transmission resumes
on the next daylight tick with valid measurements and a connected car. Night
and sunset zeros remain independent of measurement validity.

**This is input validation, not a charging-stop policy.** Skipping transmission
does not issue a Stop command or clear previous `pvopt_*` averages. Ensure your
installation has an appropriate independent response to loss of measurement
data. The blueprint does not check source timestamps or freshness: an old but
numeric state passes validation. No fixed age threshold is assumed.

The go-eCharger calculates its `pvopt_*` averages from the last values it has received, no matter how old they are. Without the zero values, a car that is (re)connected at night can start charging at sunrise on the basis of the previous day's surplus, even though the PV generation has not started yet.

## go-eCharger Setup

1. Enable **ECO mode** (Logic mode: Awattar [Eco])
2. Enable **"Use PV surplus"** (Mit PV-Überschuss laden)
3. Enable **"Allow Charge Pause"** (Ladepausen zulassen)
4. Set **Grid Target** to negative value (e.g., -500W)

## Troubleshooting

- **No data transmission**: Check entity names and availability, and that the "car connected" entity reports `on`
- **Wrong values**: Use inversion options for incorrect sign conventions
- **Values are 1000 times too small**: Your entities report kW. Set the **Power Unit Multiplier** to `1000`
- **Car starts charging at sunrise before the PV generation has started**: Update to the latest version of the blueprint, which sends zero values at night
- **Charging issues**: Verify go-eCharger ECO mode settings
- **Blueprint not visible**: Ensure HA version ≥ 2024.6.0

## Changelog

### 2026-09-30
- Send zero values at sunset and every 30 seconds at night while a car is connected
- New input **Power Unit Multiplier** (default `1`, backward compatible)
- Rounding now happens after the multiplication
- The "car connected" condition works with string and list target values
- README: file name in the manual installation corrected

## Support

For issues with the blueprint, please create an issue in this repository.
For go-eCharger integration issues, see the [main integration documentation](../../../README.md).
