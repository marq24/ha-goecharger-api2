from dataclasses import dataclass
from typing import Final

from homeassistant.components.binary_sensor import BinarySensorEntityDescription, BinarySensorDeviceClass
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.number import NumberEntityDescription, NumberDeviceClass, NumberMode
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass, SensorDeviceClass
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import (
    EntityCategory, UnitOfElectricCurrent, UnitOfEnergy, UnitOfTime, CURRENCY_CENT, UnitOfPower, UnitOfTemperature,
    UnitOfFrequency, UnitOfElectricPotential, PERCENTAGE, SIGNAL_STRENGTH_DECIBELS
)

from custom_components.goecharger_api2.pygoecharger_ha.const import CT_VALUES
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag, IS_TRIGGER

# Base component constants
MANUFACTURER: Final = "go-e GmbH [Austria]"
NAME: Final = "go-e APIv2 Connect"
DOMAIN: Final = "goecharger_api2"
ISSUE_URL: Final = "https://github.com/marq24/ha-goecharger-api2/issues"

CONFIG_VERSION: Final = 2
CONFIG_MINOR_VERSION: Final = 0

STARTUP_MESSAGE: Final = f"""
-------------------------------------------------------------------
{NAME} - v%s
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

SERVICE_SET_PV_DATA: Final = "set_pv_data"
SERVICE_STOP_CHARGING: Final = "stop_charging"
CONF_11KWLIMIT: Final = "limit_to_11kw"
CONF_INTEGRATION_TYPE = "integration_type"

WAN: Final = "wan"
LAN: Final = "lan"

@dataclass(frozen=True)
class ExtBinarySensorEntityDescription(BinarySensorEntityDescription):
    idx: int | None = None
    tuple_idx: list | None = None
    icon_off: str | None = None


@dataclass(frozen=True)
class ExtButtonEntityDescription(ButtonEntityDescription):
    payload: str | None = None


@dataclass(frozen=True)
class ExtNumberEntityDescription(NumberEntityDescription):
    write_zero_as_null: bool | None = None
    handle_as_float: bool | None = None
    factor: int | None = None
    idx: int | str | None = None
    check_16a_limit: bool | None = None


@dataclass(frozen=True)
class ExtSelectEntityDescription(SelectEntityDescription):
    idx: int | str | None = None


@dataclass(frozen=True)
class ExtSensorEntityDescription(SensorEntityDescription):
    idx: int | str | None = None
    tuple_idx: list | None = None
    factor: int | None = None
    lookup: bool | None = None
    differential_base_key: str | None = None


@dataclass(frozen=True)
class ExtSwitchEntityDescription(SwitchEntityDescription):
    is_zero_or_one: bool | None = None
    icon_off: str | None = None
    idx: int | str | None = None


PLATFORMS: Final = ["binary_sensor", "button", "number", "select", "sensor", "switch"]

BINARY_SENSORS = [
    ExtBinarySensorEntityDescription(
        key=Tag.CAR_CONNECTED.key,
        idx=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:car-connected",
        icon_off="mdi:car-off",
        entity_registry_enabled_default=True
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.ESK.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:application-export",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.PHA.key,
        idx=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.PHA.key,
        idx=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.PHA.key,
        idx=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.PHA.key,
        idx=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.PHA.key,
        idx=4,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.PHA.key,
        idx=5,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.ADI.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:ev-plug-type2",
        entity_registry_enabled_default=True
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.FSP.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:numeric-1",
        entity_registry_enabled_default=True
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.TLF.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:ab-testing",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.TLS.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:ab-testing",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.CTRLS.key,
        translation_key="ctrls_0_paired", # important! 'translation_key' must be allways lower case!!!
        tuple_idx=[0, 2],
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:gamepad-square-outline",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.CTRLS.key,
        translation_key="ctrls_0_connected",  # important! 'translation_key' must be allways lower case!!!
        tuple_idx=[0, 3],
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=None,
        icon="mdi:gamepad-square",
        entity_registry_enabled_default=False
    ),
    ExtBinarySensorEntityDescription(
        key=Tag.DI1.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.OPENING, # On means open, Off means closed
        icon="mdi:electric-switch",
        icon_off="mdi:electric-switch-closed"
    ),
]
BUTTONS = [
    ExtButtonEntityDescription(
        key=Tag.RST.key,
        payload="true",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:restart",
        entity_registry_enabled_default=True
    ),
    ExtButtonEntityDescription(
        key=Tag.INTERNAL_FORCE_CONFIG_READ.key,
        payload=IS_TRIGGER,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:reload",
        entity_registry_enabled_default=True
    ),
]
NUMBER_SENSORS = [
    # ama
    ExtNumberEntityDescription(
        key=Tag.AMA.key,
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=NumberDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=True
    ),
    # amp
    ExtNumberEntityDescription(
        key=Tag.AMP.key,
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=NumberDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=True
    ),
    # ate
    ExtNumberEntityDescription(
        key=Tag.ATE.key,
        native_max_value=100000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    # att
    ExtNumberEntityDescription(
        key=Tag.ATT.key,
        factor=60,
        native_max_value=1399,  # 24h = 1400 min
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    # awp -> this is in €-CENT! - but api allow to specify 0.01 cent steps
    ExtNumberEntityDescription(
        key=Tag.AWP.key,
        handle_as_float=True,
        native_max_value=1000,
        native_min_value=-100,
        native_step=0.01,
        # mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=CURRENCY_CENT,
        device_class=None,
        icon="mdi:cash",
        entity_registry_enabled_default=True
    ),
    # cco -> only display value for the app..
    ExtNumberEntityDescription(
        key=Tag.CCO.key,
        handle_as_float=True,
        native_max_value=50,
        native_min_value=0.01,
        native_step=0.01,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        icon="mdi:gas-station-outline",
        entity_registry_enabled_default=False
    ),
    # dwo
    ExtNumberEntityDescription(
        key=Tag.DWO.key,
        write_zero_as_null=True,
        native_max_value=1000000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    # fmt
    ExtNumberEntityDescription(
        key=Tag.FMT.key,
        factor=60000,
        native_max_value=60,  # 1hr = 60min
        native_min_value=0,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    # fst
    ExtNumberEntityDescription(
        key=Tag.FST.key,
        native_max_value=32000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=False
    ),
    # lbr
    ExtNumberEntityDescription(
        key=Tag.LBR.key,  # 0...255
        native_max_value=255,
        native_min_value=0,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:brightness-6",
        entity_registry_enabled_default=False
    ),
    # lof
    ExtNumberEntityDescription(
        key=Tag.LOF.key,
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=False
    ),
    # lop
    ExtNumberEntityDescription(
        key=Tag.LOP.key,
        native_max_value=99,
        native_min_value=0,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:priority-high",
        entity_registry_enabled_default=False
    ),
    # lot -> is an object ->   "lot": {
    #     "amp": 32,
    #     "dyn": 32,
    #     "sta": 32,
    #     "ts": 3
    #   }
    ExtNumberEntityDescription(
        key=Tag.LOT.key,
        idx="amp",
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=False
    ),
    ExtNumberEntityDescription(
        key=Tag.LOT.key,
        idx="dyn",
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=False
    ),
    ExtNumberEntityDescription(
        key=Tag.LOT.key,
        idx="sta",
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=False
    ),
    ExtNumberEntityDescription(
        key=Tag.LOT.key,
        idx="ts",
        native_max_value=4000,
        native_min_value=0,
        native_step=1,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=False
    ),
    # mca
    ExtNumberEntityDescription(
        key=Tag.MCA.key,
        check_16a_limit=True,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_registry_enabled_default=True
    ),
    # mci
    ExtNumberEntityDescription(
        key=Tag.MCI.key,
        factor=60000,
        native_max_value=1400,  # 24hr = 1400min
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    # mcpd
    ExtNumberEntityDescription(
        key=Tag.MCPD.key,
        factor=60000,
        native_max_value=1400,  # 24hr = 1400min
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    # mcpea
    ExtNumberEntityDescription(
        key=Tag.MCPEA.key,
        write_zero_as_null=True,
        factor=60000,
        native_max_value=1400,  # 24hr = 1400min
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    # mptwt
    ExtNumberEntityDescription(
        key=Tag.MPTWT.key,
        factor=60000,
        native_max_value=1400,  # 24hr = 1400min
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    # mpwst
    ExtNumberEntityDescription(
        key=Tag.MPWST.key,
        factor=60000,
        native_max_value=1400,  # 24hr = 1400min
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    # pgt
    ExtNumberEntityDescription(
        key=Tag.PGT.key,
        native_max_value=5000,
        native_min_value=-5000,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=True
    ),
    # po
    ExtNumberEntityDescription(
        key=Tag.PO.key,
        native_max_value=100000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=True
    ),
    # psh
    ExtNumberEntityDescription(
        key=Tag.PSH.key,
        native_max_value=100000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=True
    ),
    # psmd
    ExtNumberEntityDescription(
        key=Tag.PSMD.key,
        factor=1000,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # random delays...
    ExtNumberEntityDescription(
        key=Tag.RDBS.key,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtNumberEntityDescription(
        key=Tag.RDES.key,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtNumberEntityDescription(
        key=Tag.RDBF.key,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtNumberEntityDescription(
        key=Tag.RDEF.key,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtNumberEntityDescription(
        key=Tag.RDRE.key,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtNumberEntityDescription(
        key=Tag.RDPL.key,
        native_max_value=84000,  # 24hr = 1400min = 84000 Sec
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # sh
    ExtNumberEntityDescription(
        key=Tag.SH.key,
        native_max_value=100000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=True
    ),
    # spl3
    ExtNumberEntityDescription(
        key=Tag.SPL3.key,
        native_max_value=64000,
        native_min_value=500,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=True
    ),
    # sumd
    ExtNumberEntityDescription(
        key=Tag.SUMD.key,
        factor=1000,
        native_max_value=3600,  # 1hr = 60min = 3600sek
        native_min_value=0,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=NumberDeviceClass.DURATION,
        icon="mdi:ab-testing",
        entity_registry_enabled_default=False
    ),
    # zfo
    ExtNumberEntityDescription(
        key=Tag.ZFO.key,
        native_max_value=100000,
        native_min_value=0,
        native_step=10,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:lightning-bolt-outline",
        entity_registry_enabled_default=True
    )
]
SELECT_SENSORS = [
    ExtSelectEntityDescription(
        key=Tag.CT.key,
        options=[el.value.lower() for el in CT_VALUES],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:ab-testing",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.BAC.key,
        options=["0", "1", "2", "3"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:button-pointer",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.FRC.key,
        options=["0", "1", "2"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:hand-front-left-outline",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.LMO.key,
        options=["3", "4", "5"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.LOTY.key,
        options=["0", "1"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:scale-balance",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.PSM.key,
        options=["0", "1", "2"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:speedometer",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.SDP.key,
        options=["0", "1", "2", "3"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:button-pointer",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.TRX.key,
        options=["null", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:shield-lock-open-outline",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.TDS.key,
        options=["0", "1", "2"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:map-clock",
        entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
        key=Tag.UST.key,
        # mode:3 not allowed (force unlock)
        # options=["0", "1", "2", "3"],
        options=["0", "1", "2"],
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:lock-open-outline",
        entity_registry_enabled_default=True
    ),
]
SENSOR_SENSORS = [
    # INDEXED Values...
    # nrg
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=0,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=1,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=2,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=3,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=4,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=5,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=6,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=7,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=8,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=9,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=10,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=11,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=12,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=13,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=14,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.NRG.key,
        idx=15,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    # tma
    ExtSensorEntityDescription(
        key=Tag.TMA.key,
        idx=0,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.TMA.key,
        idx=1,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=True
    ),

    # cdi -> object
    ExtSensorEntityDescription(
        key=Tag.CDI.key,
        idx="type",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:counter",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CDI.key,
        idx="value",
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    # atp -> object [NOT IMPLEMENTED YET]
    # TODO:HERE
    # ExtSensorEntityDescription(
    #     key=Tag.ATP.key,
    #     idx="???",
    #     entity_category=EntityCategory.DIAGNOSTIC,
    #     native_unit_of_measurement=None,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     device_class=None,
    #     icon="mdi:mdi:bug-outline",
    #     entity_registry_enabled_default=False
    # ),
    # awcp -> object
    ExtSensorEntityDescription(
        key=Tag.AWCP.key,
        idx="marketprice",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=CURRENCY_CENT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:cash",
        entity_registry_enabled_default=False
    ),
    # ccu -> object [not testable yet] - But looks like this is only the progress for
    # the update -> so we will ignore it for now!
    # TODO:HERE
    # ExtSensorEntityDescription(
    #     key=Tag.CCU.key,
    #     idx="",
    #     entity_category=EntityCategory.DIAGNOSTIC,
    #     native_unit_of_measurement=None,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     device_class=None,
    #     icon="mdi:gauge",
    #     entity_registry_enabled_default=False
    # ),

    # ccw -> object
    ExtSensorEntityDescription(
        key=Tag.CCW.key,
        idx="ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi",
        entity_registry_enabled_default=False
    ),

    # cll -> object!
    ExtSensorEntityDescription(
        key=Tag.CLL.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:list-status",
        entity_registry_enabled_default=True
    ),


    # LOOKUP-Values [always two Sensors!]
    # car
    # cus
    # err
    # modelstatus
    # ffb
    # frm
    # lck
    # pwm
    # wsms
    # wst
    ExtSensorEntityDescription(
        key=Tag.CAR.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:state-machine",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CAR.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:state-machine",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CUS.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:lock-question",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CUS.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:lock-question",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ERR.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.ERR.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.MODELSTATUS.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:state-machine",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.MODELSTATUS.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:state-machine",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.FFB.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:lock-open-check-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.FFB.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:lock-open-check-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.FRM.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:transmission-tower-export",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.FRM.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:transmission-tower-export",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.LCK.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:lock-open-alert-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LCK.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:lock-open-alert-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.PWM.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:bug-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.PWM.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:bug-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.WSMS.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi-settings",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.WSMS.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi-settings",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.WST.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.WST.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi",
        entity_registry_enabled_default=True
    ),

    # TIMES from here...

    # rbt: is the reboot time - and "looks like", that all other timestamps
    # use the rbt "as" start point [so other timestamp will need the rbt value
    # to calculate the real value]
    ExtSensorEntityDescription(
        key=Tag.RBT.key,
        factor=3600000, # time in full hours!
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),

    # fsptws
    ExtSensorEntityDescription(
        key=Tag.FSPTWS.key,
        differential_base_key=Tag.RBT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.FSPTWS.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # inva
    ExtSensorEntityDescription(
        key=Tag.INVA.key,
        differential_base_key=Tag.RBT.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.INVA.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lbp
    ExtSensorEntityDescription(
        key=Tag.LBP.key,
        differential_base_key=Tag.RBT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:button-pointer",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.LBP.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:button-pointer",
        entity_registry_enabled_default=False
    ),

    # lccfc
    ExtSensorEntityDescription(
        key=Tag.LCCFC.key,
        differential_base_key=Tag.RBT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LCCFC.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lccfi
    ExtSensorEntityDescription(
        key=Tag.LCCFI.key,
        differential_base_key=Tag.RBT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LCCFI.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lcctc
    ExtSensorEntityDescription(
        key=Tag.LCCTC.key,
        differential_base_key=Tag.RBT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LCCTC.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lfspt
    ExtSensorEntityDescription(
        key=Tag.LFSPT.key,
        differential_base_key=Tag.RBT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LFSPT.key,
        factor=60000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lpsc
    ExtSensorEntityDescription(
        key=Tag.LPSC.key,
        differential_base_key=Tag.RBT.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.LPSC.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lmsc -> last model status change
    ExtSensorEntityDescription(
        key=Tag.LMSC.key,
        differential_base_key=Tag.RBT.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    # lmsc -> last model status change
    ExtSensorEntityDescription(
        key=Tag.LMSC.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),

    # lcs -> last controller scan
    ExtSensorEntityDescription(
        key=Tag.LCS.key,
        differential_base_key=Tag.RBT.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=True
    ),
    # lcs -> last controller scan
    ExtSensorEntityDescription(
        key=Tag.LCS.key,
        factor=1000,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:timer-outline",
        entity_registry_enabled_default=False
    ),


    # So finally the normal sensor here...
    # acu
    ExtSensorEntityDescription(
        key=Tag.ACU.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    # amt
    ExtSensorEntityDescription(
        key=Tag.AMT.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=True
    ),
    # cbl
    ExtSensorEntityDescription(
        key=Tag.CBL.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=False
    ),
    # deltaa
    ExtSensorEntityDescription(
        key=Tag.DELTAA.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=False
    ),
    # deltap
    ExtSensorEntityDescription(
        key=Tag.DELTAP.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=False
    ),
    # eto
    ExtSensorEntityDescription(
        key=Tag.ETO.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    # ferm
    # NOT-AVAILABLE in MY DATA ?!
    # TODO:HERE!

    # fhz
    ExtSensorEntityDescription(
        key=Tag.FHZ.key,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        icon="mdi:current-ac",
        entity_registry_enabled_default=False
    ),
    # loa
    ExtSensorEntityDescription(
        key=Tag.LOA.key,
        name="Load balancing available current",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    # map
    ExtSensorEntityDescription(
        key=Tag.MAP.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:vector-triangle",
        entity_registry_enabled_default=True
    ),
    # mmp
    ExtSensorEntityDescription(
        key=Tag.MMP.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:bug-outline",
        entity_registry_enabled_default=True
    ),
    # nif
    ExtSensorEntityDescription(
        key=Tag.NIF.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:navigation-variant-outline",
        entity_registry_enabled_default=False
    ),
    # pakku
    ExtSensorEntityDescription(
        key=Tag.PAKKU.key,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:home-battery-outline",
        entity_registry_enabled_default=True
    ),
    # pgrid
    ExtSensorEntityDescription(
        key=Tag.PGRID.key,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:transmission-tower-export",
        entity_registry_enabled_default=True
    ),
    # pnp
    ExtSensorEntityDescription(
        key=Tag.PNP.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:counter",
        entity_registry_enabled_default=False
    ),
    # ppv
    ExtSensorEntityDescription(
        key=Tag.PPV.key,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:solar-power",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.PVOPT_AVERAGEPAKKU.key,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:home-battery-outline",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.PVOPT_AVERAGEPGRID.key,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:transmission-tower-export",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.PVOPT_AVERAGEPPV.key,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:solar-power",
        entity_registry_enabled_default=True
    ),
    # rbc
    ExtSensorEntityDescription(
        key=Tag.RBC.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=None,
        icon="mdi:counter",
        entity_registry_enabled_default=True
    ),
    # rfb
    ExtSensorEntityDescription(
        key=Tag.RFB.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    # rssi
    ExtSensorEntityDescription(
        key=Tag.RSSI.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        icon="mdi:wifi-strength-2",
        entity_registry_enabled_default=True
    ),
    # tpa
    ExtSensorEntityDescription(
        key=Tag.TPA.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        suggested_display_precision=2,
        entity_registry_enabled_default=True
    ),
    # wh
    ExtSensorEntityDescription(
        key=Tag.WH.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=True
    ),
    # wsc -> later (if at all)
    # wsm -> later (if at all)

    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[0, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[1, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[2, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[3, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[4, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[5, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[6, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[7, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[8, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CARDS.key,
        tuple_idx=[9, "energy"],
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        entity_registry_enabled_default=False
    )
]

SWITCH_SENSORS = [
    ExtSwitchEntityDescription(
        key=Tag.ACP.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True
    ),
    # require special handing: 0 and 1 (for ON/OFF -> not true/false)
    ExtSwitchEntityDescription(
        key=Tag.ACS.key,
        is_zero_or_one=True,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.ARA.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.AWE.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:cash",
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.CMSE.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:home-search-outline",
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.CWE.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.FUP.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:solar-power",
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.FZF.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True
    ),
    # hsa key is not present in my DEVICE
    # ExtSwitchEntityDescription(
    #    key=Tag.HSA.key,
    #    entity_category=EntityCategory.CONFIG,
    #    device_class=None,
    #    entity_registry_enabled_default=False
    # ),
    ExtSwitchEntityDescription(
        key=Tag.LOE.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:scale-balance",
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.LSE.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:led-off",
        icon_off="mdi:led-on",
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.NMO.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon_off="mdi:home-floor-g",
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.SU.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:ab-testing",
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.SUA.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:ab-testing",
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.UPO.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:lock-open-outline",
        entity_registry_enabled_default=False
    )
]

# NOT-IMPLEMENTED...
STRING_INPUT = [
    ExtSensorEntityDescription(
        key=Tag.LOG.key,
        name="Load-Management Group ID",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
]

OTHER = [
    ExtSensorEntityDescription(
        key=Tag.CCH.key,
        name="Color charging",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:format-color-fill",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CFI.key,
        name="Color finished",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:format-color-fill",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CID.key,
        name="Color idle",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:format-color-fill",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CLP.key,
        name="Current limit presets",
        entity_category=None,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.CWC.key,
        name="Color wait for car",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:format-color-fill",
        entity_registry_enabled_default=False
    ),

    ExtSensorEntityDescription(
        key=Tag.SCH_SATUR.key,
        name="Scheduler saturday",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.SCH_SUND.key,
        name="Scheduler sunday",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.SCH_WEEK.key,
        name="Scheduler weekday",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.TDS.key,
        name="Timezone daylight saving mode",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.TOF.key,
        name="Timezone offset in minutes",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.TSSS.key,
        name="Time server sync status",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.WIFIS.key,
        name="WiFi configurations",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.DEL.key,
        name="Delete card",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.DELW.key,
        name="Delete STA config",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LRN.key,
        name="Learn card",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.OCT.key,
        name="Firmware update trigger",
        entity_category=None,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.HOST.key,
        name="Hostname on STA interface",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.LOC.key,
        name="Local time",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.OCU.key,
        name="List of available firmware versions",
        # state=json_array_to_csv,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:numeric",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.SCAA.key,
        name="WiFi scan age",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.SCAN.key,
        name="WiFi scan result",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.TRX.key,
        name="Transaction",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:message-text-lock-outline",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.UTC.key,
        name="UTC time",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        entity_registry_enabled_default=False
    )
]

CONTROLLER_BINARY_SENSORS = [
]
CONTROLLER_BUTTONS = [
    ExtButtonEntityDescription(
        key=Tag.RST.key,
        payload="true",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        icon="mdi:restart",
        entity_registry_enabled_default=True
    ),
]
CONTROLLER_NUMBER_SENSORS = [
]
CONTROLLER_SELECT_SENSORS = [
    ExtSelectEntityDescription(
       key=Tag.IPS.key,
       idx=0,
       options=["0", "1", "2", "3"],
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       icon="mdi:sort",
       entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
       key=Tag.IPS.key,
       idx=1,
       options=["0", "1", "2", "3"],
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       icon="mdi:sort",
       entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
       key=Tag.IPS.key,
       idx=2,
       options=["0", "1", "2", "3"],
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       icon="mdi:sort",
       entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
       key=Tag.IPS.key,
       idx=3,
       options=["0", "1", "2", "3"],
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       icon="mdi:sort",
       entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
       key=Tag.IPS.key,
       idx=4,
       options=["0", "1", "2", "3"],
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       icon="mdi:sort",
       entity_registry_enabled_default=True
    ),
    ExtSelectEntityDescription(
       key=Tag.IPS.key,
       idx=5,
       options=["0", "1", "2", "3"],
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       icon="mdi:sort",
       entity_registry_enabled_default=True
    )
]
CONTROLLER_SENSOR_SENSORS = [
    ExtSensorEntityDescription(
        key=Tag.USV.key,
        tuple_idx=[0, "u1"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.USV.key+"_0_u1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.USV.key,
        tuple_idx=[0, "u2"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.USV.key+"_0_u2", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.USV.key,
        tuple_idx=[0, "u3"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.USV.key+"_0_u3", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.USV.key,
        tuple_idx=[0, "uN"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.USV.key+"_0_un", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[0, "i"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_0_i", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[0, "p"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_0_p", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[0, "f"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_0_f", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[1, "i"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_1_i", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[1, "p"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_1_p", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[1, "f"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_1_f", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[2, "i"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_2_i", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[2, "p"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_2_p", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[2, "f"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_2_f", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[3, "i"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_3_i", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[3, "p"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_3_p", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[3, "f"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_3_f", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[4, "i"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_4_i", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[4, "p"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_4_p", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[4, "f"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_4_f", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[5, "i"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_5_i", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[5, "p"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_5_p", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.ISV.key,
        tuple_idx=[5, "f"], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.ISV.key+"_5_f", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[0, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_0_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[0, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_0_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[1, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_1_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[1, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_1_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[2, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_2_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[2, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_2_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[3, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_3_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[3, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_3_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[4, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_4_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[4, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_4_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[5, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_5_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[5, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_5_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[6, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_6_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[6, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_6_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[7, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_7_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[7, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_7_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[8, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_8_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[8, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_8_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[9, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_9_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[9, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_9_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[10, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_10_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[10, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_10_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[11, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_11_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[11, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_11_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[12, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_12_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[12, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_12_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[13, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_13_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[13, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_13_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[14, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_14_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[14, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_14_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[15, 0], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_15_0", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CEC.key,
        tuple_idx=[15, 1], # when using the 'tuple_idx', a 'translation_key' must be also present!
        translation_key=Tag.CEC.key+"_15_1", # important! 'translation_key' must be allways lower case!!!
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=NumberDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=0,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=1,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=2,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=3,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=4,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=5,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=6,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=7,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=8,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=9,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=10,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=11,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=12,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=13,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=14,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCP.key,
        idx=15,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.WST.key,
        lookup=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.CCW.key,
        idx="ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:wifi",
        entity_registry_enabled_default=True
    ),
    ExtSensorEntityDescription(
        key=Tag.MECU.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:link",
        entity_registry_enabled_default=False
    ),
    ExtSensorEntityDescription(
        key=Tag.MMH.key,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        state_class=None,
        device_class=None,
        icon="mdi:link",
        entity_registry_enabled_default=False
    ),
]
CONTROLLER_SWITCH_SENSORS = [
    ExtSwitchEntityDescription(
        key=Tag.MECE.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.HAI.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
        key=Tag.WDA.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
        key=Tag.MME.key,
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=False
    ),
    ExtSwitchEntityDescription(
       key=Tag.IIM.key,
       idx=0,
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
       key=Tag.IIM.key,
       idx=1,
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
       key=Tag.IIM.key,
       idx=2,
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
       key=Tag.IIM.key,
       idx=3,
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
       key=Tag.IIM.key,
       idx=4,
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       entity_registry_enabled_default=True
    ),
    ExtSwitchEntityDescription(
       key=Tag.IIM.key,
       idx=5,
       entity_category=EntityCategory.CONFIG,
       device_class=None,
       entity_registry_enabled_default=True
    ),
]