"""Coordinator.read_versions: when is a charger treated as limited to 16 A?

This is a decision table over cable limit (`cll`), 16 A adapter (`adi`), variant (`var`), device type
and the user option. The rows marked "current behaviour" pin what the code does today (since 98af3e0)
without claiming that it is the right choice for every device.
"""
import inspect
from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import GoeChargerDataUpdateCoordinator
from custom_components.goecharger_api2.pygoecharger_ha import NonNullDict

NON_CORE = "go-eCharger_V4"
CORE = "go-eCharger_Phoenix"


# The rule "cll without cableCurrentLimit -> no 16 A limit" exists since 98af3e0. Older releases limit such
# chargers, so that row is skipped there (the skip is visible in the report, it is not a silent pass).
RULE_SINCE_98AF3E0 = "will not enforce the 16A CABLE limit" in inspect.getsource(
    GoeChargerDataUpdateCoordinator.read_versions)


def _cll(**fields):
    return {"cll": fields}


CASES = [
    # id,                          device,   extra versions,                          option, expected
    ("cable_limit_32",             NON_CORE, _cll(cableCurrentLimit=32),             False,  False),
    ("cable_limit_16",             NON_CORE, _cll(cableCurrentLimit=16),             False,  True),
    ("cable_limit_6",              NON_CORE, _cll(cableCurrentLimit=6),              False,  True),
    ("variant_11kw_always_limits", NON_CORE, {"var": 11, **_cll(cableCurrentLimit=32)}, False, True),
    ("user_option_forces_limit",   NON_CORE, _cll(cableCurrentLimit=32),             True,   True),
    ("no_cll_adapter_in_use",      NON_CORE, {"adi": True},                          False,  True),
    ("no_cll_no_adapter",          NON_CORE, {"adi": False},                         False,  False),
    ("core_without_cll_is_limited", CORE,    {},                                     False,  True),
    # current behaviour since 98af3e0 (issue #176): cll present but no cableCurrentLimit -> no limit
    ("cll_without_cable_limit_non_core", NON_CORE, _cll(currentLimitMax=32),         False,  False),
    ("cll_without_cable_limit_core",     CORE,     _cll(currentLimitMax=32),         False,  False),
]


@pytest.mark.parametrize("device, extra, option, expected",
                         [c[1:] for c in CASES], ids=[c[0] for c in CASES])
async def test_limit_to_16a_decision(request, hass, device, extra, option, expected):
    if request.node.callspec.id.startswith("cll_without_cable_limit") and not RULE_SINCE_98AF3E0:
        pytest.skip("this release predates the 98af3e0 rule for cll without cableCurrentLimit")
    entry = MockConfigEntry(domain="goecharger_api2", title="t", data={
        "mode": "lan", "host": "192.0.2.10", "id": "123456", "integration_type": "charger",
        "limit_to_11kw": option})
    entry.add_to_hass(hass)
    coordinator = GoeChargerDataUpdateCoordinator(hass, entry)
    coordinator.bridge.read_versions = AsyncMock(return_value=True)
    coordinator.bridge._versions = NonNullDict({"typ": device, "fwv": "60.3", "var": 22, **extra})

    assert await coordinator.read_versions() is True
    assert coordinator.limit_to16a is expected
