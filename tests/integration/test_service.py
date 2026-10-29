"""set_pv_data: non-finite numbers must never reach the charger."""
import math
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.goecharger_api2 import service as service_module
from custom_components.goecharger_api2.service import GoeChargerApiV2Service
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag


@pytest.fixture
def svc(hass):
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.clear()
    coordinator = SimpleNamespace(
        intg_type="charger", mode="lan", name="test charger", _serial="123456", data={},
        async_write_key=AsyncMock(return_value={Tag.IDS.key: True}))
    service = GoeChargerApiV2Service(hass, SimpleNamespace(entry_id="entry"), coordinator)
    yield service, coordinator
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.clear()


def _call(**data):
    return SimpleNamespace(data=data, return_response=True)


async def test_valid_values_are_written(svc):
    service, coordinator = svc
    result = await service.set_pv_data(_call(pgrid=-500, ppv=1500, pakku=200))
    assert result["success"] == "true"
    coordinator.async_write_key.assert_awaited_once_with(
        Tag.IDS.key, {"pGrid": -500.0, "pPv": 1500.0, "pAkku": 200.0})


@pytest.mark.xfail(strict=True, reason="service.py checks pgrid with isinstance(Number) only; NaN and inf pass")
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
async def test_non_finite_grid_value_is_rejected(svc, bad):
    service, coordinator = svc
    result = await service.set_pv_data(_call(pgrid=bad, ppv=1500))
    assert "error" in result
    coordinator.async_write_key.assert_not_awaited()


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
async def test_non_finite_pv_and_battery_value_become_zero(svc, bad):
    service, coordinator = svc
    await service.set_pv_data(_call(pgrid=100, ppv=bad, pakku=bad))
    coordinator.async_write_key.assert_awaited_once_with(
        Tag.IDS.key, {"pGrid": 100.0, "pPv": 0.0, "pAkku": 0.0})
