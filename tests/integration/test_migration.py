"""Config entry migration (async_migrate_entry).

Version 2.0 -> 2.1 deletes all devices of the entry. Home Assistant removes the entities of a deleted
device as well (assumed, not tested here), so user settings on those entities are lost once. The
test pins that the purge happens exactly once.
"""
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goecharger_api2 import async_migrate_entry
from custom_components.goecharger_api2.const import DOMAIN


def _entry(hass, version, minor, data=None, options=None):
    entry = MockConfigEntry(domain=DOMAIN, title="t", version=version, minor_version=minor,
                            data=data or {"host": "192.0.2.10", "id": "123456"}, options=options or {})
    entry.add_to_hass(hass)
    return entry


def _device(hass, entry):
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, "old-identifier")})


async def test_version_1_merges_options_into_data(hass):
    entry = _entry(hass, 1, 0, options={"scan_interval": 60})
    assert await async_migrate_entry(hass, entry) is True
    assert entry.data["scan_interval"] == 60 and entry.data["host"] == "192.0.2.10"
    assert dict(entry.options) == {}
    assert (entry.version, entry.minor_version) == (2, 1)


async def test_version_2_0_deletes_the_devices_and_moves_to_2_1(hass):
    entry = _entry(hass, 2, 0)
    device = _device(hass, entry)
    assert await async_migrate_entry(hass, entry) is True
    assert dr.async_get(hass).async_get(device.id) is None
    assert (entry.version, entry.minor_version) == (2, 1)


async def test_version_2_1_is_left_alone(hass):
    entry = _entry(hass, 2, 1)
    device = _device(hass, entry)
    assert await async_migrate_entry(hass, entry) is True
    assert dr.async_get(hass).async_get(device.id) is not None
    assert (entry.version, entry.minor_version) == (2, 1)
