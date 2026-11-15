"""set_pv_data: non-finite numbers must never reach the charger."""
import math
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.goecharger_api2 import service as service_module
from custom_components.goecharger_api2.service import GoeChargerApiV2Service
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag


@pytest.fixture
def svc(hass):
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.clear()
    coordinator = SimpleNamespace(
        intg_type="charger", mode="lan", name="test charger", _serial="123456", data={},
        async_write_key=AsyncMock(side_effect=lambda key, value, **kwargs: {key: value}))
    service = GoeChargerApiV2Service(hass, SimpleNamespace(entry_id="entry"), coordinator)
    yield service, coordinator
    service_module._COORDINATOR_PER_CONFIG_ENTRY_ID_MAP.clear()


def _call(return_response=True, **data):
    return SimpleNamespace(data=data, return_response=return_response)


async def test_valid_values_are_written(svc):
    service, coordinator = svc
    result = await service.set_pv_data(_call(pgrid=-500, ppv=1500, pakku=200))
    assert result["success"] == "true"
    coordinator.async_write_key.assert_awaited_once_with(
        Tag.IDS.key, {"pGrid": -500.0, "pPv": 1500.0, "pAkku": 200.0}, require_ack=False)


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
        Tag.IDS.key, {"pGrid": 100.0, "pPv": 0.0, "pAkku": 0.0}, require_ack=False)


@pytest.mark.parametrize("options", [{}, {"require_ack": False}])
async def test_legacy_response_does_not_require_acknowledgement(svc, options):
    service, coordinator = svc
    reply = {"ids": True}
    coordinator.async_write_key = AsyncMock(return_value=reply)
    result = await service.set_pv_data(_call(pgrid=100, **options))
    assert result["success"] == "true" and result["response"] == reply
    assert coordinator.async_write_key.call_args.kwargs == {"require_ack": False}


@pytest.mark.parametrize("return_response", [True, False])
async def test_explicit_acknowledgement_accepts_matching_data(svc, return_response):
    service, coordinator = svc
    payload = {"pGrid": -500.0, "pPv": 1500.0, "pAkku": 200.0}
    result = await service.set_pv_data(
        _call(return_response=return_response, pgrid=-500, ppv=1500, pakku=200, require_ack=True))
    if return_response:
        assert result["success"] == "true" and result["response"] == {"ids": payload}
    else:
        assert result is None
    coordinator.async_write_key.assert_awaited_once_with(Tag.IDS.key, payload, require_ack=True)


@pytest.mark.parametrize("reply", [
    {}, None, {"err": "rejected"}, {"ids": True}, {"ids": {"pGrid": 1}},
    {"ids": {"pGrid": -500.0, "pPv": 1501.0, "pAkku": 200.0}},
])
async def test_pv_response_requires_matching_acknowledgement(svc, reply):
    service, coordinator = svc
    coordinator.async_write_key = AsyncMock(return_value=reply)
    result = await service.set_pv_data(_call(pgrid=-500, ppv=1500, pakku=200, require_ack=True))
    assert "error" in result and "success" not in result
    assert coordinator.async_write_key.call_args.kwargs == {"require_ack": True}


async def test_missing_explicit_acknowledgement_without_response_raises(svc):
    service, coordinator = svc
    coordinator.async_write_key = AsyncMock(return_value={})
    with pytest.raises(ServiceValidationError, match="did not acknowledge PV data"):
        await service.set_pv_data(_call(return_response=False, pgrid=100, require_ack=True))


async def test_explicit_acknowledgement_without_grid_power_raises(svc):
    service, coordinator = svc
    with pytest.raises(ServiceValidationError, match="No Grid Power"):
        await service.set_pv_data(_call(return_response=False, require_ack=True))
    coordinator.async_write_key.assert_not_awaited()


async def test_non_boolean_acknowledgement_option_is_rejected_before_write(svc):
    service, coordinator = svc
    with pytest.raises(ServiceValidationError, match="require_ack must be a boolean"):
        await service.set_pv_data(_call(pgrid=100, require_ack="false"))
    coordinator.async_write_key.assert_not_awaited()
