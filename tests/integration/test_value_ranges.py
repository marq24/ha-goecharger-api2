"""Value ranges and option sets of the entities against the documentation.

Sources (go-eCharger-API-v2, official repository):
- key table (`API_KEYS_FIRMWARE/apikeys-en.md`): option sets with their meaning and `lbr` 0-255
- Modbus profile (`modbus-en.md`): amp/ama as whole amps 6 to 32 ("AMPERE_VOLATILE", "AMPERE_EEPROM"),
  `frc` and `psm` "only accepts values 0, 1, 2", `dwo` any number of Wh or "null" for no limit

Only numbers and option values are stored here, not the descriptions. The comparison is against what
the entity description offers; Home Assistant itself rejects values outside min/max before the
integration is called, so these limits are what a user can actually send.
"""
import pytest

from custom_components.goecharger_api2 import const as entity_const

# key -> (min, max) documented
NUMBER_RANGES = {"amp": (6, 32), "ama": (6, 32), "lbr": (0, 255)}
# key -> the set of values the charger accepts according to the documentation
OPTION_SETS = {
    "frc": {"0", "1", "2"},   # Neutral, Off, On
    "psm": {"0", "1", "2"},   # Modbus: "only accepts values 0, 1, 2"
    "ust": {"0", "1", "2"},   # Normal, AutoUnlock, AlwaysLock
    "tds": {"0", "1", "2"},   # None, EuropeanSummerTime, UsDaylightTime
    "lmo": {"3", "4", "5"},   # Default, Awattar, AutomaticStop
    "bac": {"0", "1", "2", "3"},  # AlwaysLock .. NeverLock
}


def _description(list_name, key):
    matches = [d for d in getattr(entity_const, list_name) if d.key == key]
    assert len(matches) == 1, f"{key}: expected one description in {list_name}, found {len(matches)}"
    return matches[0]


@pytest.mark.parametrize("key, bounds", NUMBER_RANGES.items(), ids=NUMBER_RANGES)
def test_number_range_equals_documentation(key, bounds):
    d = _description("NUMBER_SENSORS", key)
    assert (d.native_min_value, d.native_max_value) == bounds


@pytest.mark.parametrize("key", NUMBER_RANGES)
def test_number_step_is_a_whole_unit(key):
    assert _description("NUMBER_SENSORS", key).native_step == 1


@pytest.mark.parametrize("key, values", OPTION_SETS.items(), ids=OPTION_SETS)
def test_select_options_equal_documentation(key, values):
    d = _description("SELECT_SENSORS", key)
    assert set(d.options) == values and len(d.options) == len(values), "no duplicates, no missing or extra option"


def test_energy_limit_stays_inside_what_the_api_accepts():
    # documented: any number of Wh (null = no limit); the integration offers 0 to 1,000,000 Wh in steps of 10
    d = _description("NUMBER_SENSORS", "dwo")
    assert 0 <= d.native_min_value < d.native_max_value and d.native_step > 0
    assert d.native_min_value >= 0, "a negative energy limit is not meaningful"
