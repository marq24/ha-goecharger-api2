"""Schedule-rule decoding, slot availability, firmware gating and field-preserving writes."""

import json
from copy import deepcopy
from datetime import time
from importlib.resources import files
from unittest.mock import AsyncMock

import pytest

from custom_components.goecharger_api2 import schedule as schedule_module
from custom_components.goecharger_api2.pygoecharger_ha.keys import CAT, Tag
from custom_components.goecharger_api2.pygoecharger_ha.const import FILTER_ALL_CONFIG
from custom_components.goecharger_api2.schedule import (
    SCHEDULE_RULE_COUNT,
    ScheduleRuleSelect,
    ScheduleRuleSwitch,
    ScheduleRuleTime,
    WEEKDAYS,
    create_schedule_rule_selects,
    create_schedule_rule_switches,
    create_schedule_rule_times,
    supports_schedule_rules,
)
from custom_components.goecharger_api2.select import async_setup_entry as async_setup_select_entry
from custom_components.goecharger_api2.switch import async_setup_entry as async_setup_switch_entry
from custom_components.goecharger_api2.time import async_setup_entry as async_setup_time_entry
from custom_components.goecharger_api2.const import DOMAIN

from .factories import make_coordinator


def _rule(control=1, **overrides):
    return {
        "enabled": True,
        "weekdays": 0b0101010,
        "control": control,
        "begin": [7, 15, 42],
        "end": [18, 30, 59],
        "other": {"keep": True},
        **overrides,
    }


def _coordinator(hass, rules):
    coordinator = make_coordinator(hass, {Tag.SCH_RULES.key: rules})
    coordinator.bridge._versions = {Tag.FWV.key: "60.4"}
    coordinator._last_update_success = True
    coordinator.async_write_key = AsyncMock()
    return coordinator


def test_firmware_gate_and_current_entity_groups(hass):
    coordinator = _coordinator(hass, [_rule()])
    assert supports_schedule_rules(coordinator)
    assert len(create_schedule_rule_switches(coordinator)) == 9
    assert len(create_schedule_rule_selects(coordinator)) == 1
    assert len(create_schedule_rule_times(coordinator)) == 2
    entities = create_schedule_rule_switches(coordinator)
    assert len({entity.entity_id for entity in entities}) == len(entities)

    coordinator.bridge._versions[Tag.FWV.key] = "59.9"
    assert not supports_schedule_rules(coordinator)
    controller = make_coordinator(hass, {}, intg_type="controller")
    controller.bridge._versions[Tag.FWV.key] = "60.4"
    assert not supports_schedule_rules(controller)
    assert Tag.SCH_RULES.key in FILTER_ALL_CONFIG.split(",")
    assert Tag.SCH_RULES.cat == CAT.CONFIG and Tag.SCH_RULES.writeable


def test_schedule_entity_ids_and_name_placeholders_are_one_based(hass):
    coordinator = _coordinator(hass, [_rule()] * SCHEDULE_RULE_COUNT)
    entity_groups = (
        create_schedule_rule_switches(coordinator),
        create_schedule_rule_selects(coordinator),
        create_schedule_rule_times(coordinator),
    )

    for entities in entity_groups:
        for entity in entities:
            index = entity.rule_index
            assert f"sch_rules_{index + 1}_" in entity.entity_id
            assert entity.entity_description.translation_placeholders == {"index": str(index + 1)}

    assert {entity.rule_index for entities in entity_groups for entity in entities} == set(range(10))


async def test_last_displayed_schedule_rule_updates_last_api_rule(hass):
    original = [_rule() for _ in range(SCHEDULE_RULE_COUNT)]
    coordinator = _coordinator(hass, original)
    last_rule = ScheduleRuleTime(coordinator, SCHEDULE_RULE_COUNT - 1, "begin")

    await last_rule.async_set_value(time(9, 5))

    written = coordinator.async_write_key.await_args.args[1]
    assert written[-1]["begin"] == [9, 5, 0]
    assert written[:-1] == original[:-1]


@pytest.mark.parametrize(
    ("firmware", "legacy_count", "rule_count"),
    [("59.9", 3, 0), ("60.0", 0, SCHEDULE_RULE_COUNT)],
)
async def test_select_setup_gates_legacy_schedule_controls(hass, firmware, legacy_count, rule_count):
    coordinator = _coordinator(hass, [_rule()] * SCHEDULE_RULE_COUNT)
    coordinator.bridge._versions[Tag.FWV.key] = firmware
    entry = coordinator._config_entry
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    added_entities = []

    await async_setup_select_entry(hass, entry, added_entities.extend)

    assert sum(entity.data_key in {Tag.SCH_WEEK.key, Tag.SCH_SATUR.key, Tag.SCH_SUND.key}
               for entity in added_entities) == legacy_count
    assert sum(isinstance(entity, ScheduleRuleSelect) for entity in added_entities) == rule_count


@pytest.mark.parametrize(
    ("setup_platform", "entity_class", "entities_per_rule"),
    [
        (async_setup_switch_entry, ScheduleRuleSwitch, 9),
        (async_setup_select_entry, ScheduleRuleSelect, 1),
        (async_setup_time_entry, ScheduleRuleTime, 2),
    ],
)
async def test_platform_setup_creates_only_existing_schedule_rules(
    hass, setup_platform, entity_class, entities_per_rule
):
    coordinator = _coordinator(hass, [_rule(), _rule(2)])
    entry = coordinator._config_entry
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    added_entities = []

    await setup_platform(hass, entry, added_entities.extend)

    rule_entities = [entity for entity in added_entities if isinstance(entity, entity_class)]
    assert len(rule_entities) == 2 * entities_per_rule
    assert {entity.rule_index for entity in rule_entities} == {0, 1}


@pytest.mark.parametrize(
    ("setup_platform", "entity_class", "entities_per_rule"),
    [
        (async_setup_switch_entry, ScheduleRuleSwitch, 9),
        (async_setup_select_entry, ScheduleRuleSelect, 1),
        (async_setup_time_entry, ScheduleRuleTime, 2),
    ],
)
async def test_schedule_rule_platforms_grow_once_and_retain_shrunk_slots(
    hass, setup_platform, entity_class, entities_per_rule
):
    coordinator = _coordinator(hass, [_rule()])
    entry = coordinator._config_entry
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    added_entities = []

    await setup_platform(hass, entry, added_entities.extend)
    initial_count = len([entity for entity in added_entities if isinstance(entity, entity_class)])
    assert initial_count == entities_per_rule

    coordinator.async_set_updated_data({Tag.SCH_RULES.key: [_rule() for _ in range(4)]})
    grown_entities = [entity for entity in added_entities if isinstance(entity, entity_class)]
    assert len(grown_entities) == 4 * entities_per_rule
    assert {entity.rule_index for entity in grown_entities} == {0, 1, 2, 3}

    coordinator.async_set_updated_data({Tag.SCH_RULES.key: [_rule() for _ in range(4)]})
    assert len([entity for entity in added_entities if isinstance(entity, entity_class)]) == 4 * entities_per_rule

    coordinator.async_set_updated_data({Tag.SCH_RULES.key: [_rule()]})
    retained_entities = [entity for entity in added_entities if isinstance(entity, entity_class)]
    assert len(retained_entities) == 4 * entities_per_rule
    assert all(entity.available for entity in retained_entities if entity.rule_index == 0)
    assert all(not entity.available for entity in retained_entities if entity.rule_index > 0)


def test_entities_for_missing_slots_are_unavailable(hass):
    coordinator = _coordinator(hass, [_rule()])
    enabled = ScheduleRuleSwitch(coordinator, 1, "enabled")
    behavior = ScheduleRuleSelect(coordinator, 1)
    start = ScheduleRuleTime(coordinator, 1, "begin")
    assert not enabled.available
    assert not behavior.available
    assert not start.available
    assert enabled.is_on is None
    assert behavior.current_option is None
    assert start.native_value is None


def test_entities_are_unavailable_when_schedule_list_is_missing(hass):
    coordinator = _coordinator(hass, [])
    assert not ScheduleRuleSwitch(coordinator, 0, "enabled").available
    assert not ScheduleRuleSelect(coordinator, 0).available
    assert not ScheduleRuleTime(coordinator, 0, "begin").available


@pytest.mark.parametrize(
    ("control", "suffix"),
    [(1, ""), (3, " (mit PV-Überschuss)")],
)
def test_enabled_switch_summary_uses_german_full_week_and_time(hass, control, suffix):
    hass.config.language = "de"
    original_rule = _rule(
        control,
        weekdays=127,
        begin=[2, 36, 0],
        end=[4, 59, 0],
    )
    original_snapshot = deepcopy(original_rule)
    coordinator = _coordinator(hass, [original_rule])

    assert ScheduleRuleSwitch(coordinator, 0, "enabled").extra_state_attributes == {
        "schedule_summary": (
            "Mo., Di., Mi., Do., Fr., Sa., So., "
            f"02:36 - 04:59{suffix}"
        )
    }
    assert coordinator.data[Tag.SCH_RULES.key][0] == original_snapshot


@pytest.mark.parametrize(
    ("weekdays", "expected_days"),
    [
        (2 | 32 | 1, "Mo., Fr., So."),
        (0, ""),
    ],
)
def test_enabled_switch_summary_handles_weekday_subsets_and_empty_days(hass, weekdays, expected_days):
    hass.config.language = "de"
    coordinator = _coordinator(
        hass,
        [_rule(weekdays=weekdays, begin=[2, 36, 0], end=[4, 59, 0])],
    )

    assert ScheduleRuleSwitch(coordinator, 0, "enabled").extra_state_attributes == {
        "schedule_summary": f"{expected_days + ', ' if expected_days else ''}02:36 - 04:59"
    }


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("en", "Mon, Tue, Wed, Thu, Fri, Sat, Sun, 02:36 - 04:59 (with PV surplus)"),
        ("fr", "lun., mar., mer., jeu., ven., sam., dim., 02:36 - 04:59 (avec Surplus PV)"),
        ("xx", "Mon, Tue, Wed, Thu, Fri, Sat, Sun, 02:36 - 04:59 (with PV surplus)"),
    ],
)
def test_enabled_switch_summary_localizes_supported_and_unknown_languages(hass, language, expected):
    hass.config.language = language
    coordinator = _coordinator(
        hass,
        [_rule(3, weekdays=127, begin=[2, 36, 0], end=[4, 59, 0])],
    )

    assert ScheduleRuleSwitch(coordinator, 0, "enabled").extra_state_attributes == {
        "schedule_summary": expected
    }


def test_summary_translation_resources_are_not_loaded_per_property_read(hass, monkeypatch):
    coordinator = _coordinator(hass, [_rule(3, weekdays=127)])
    switch = ScheduleRuleSwitch(coordinator, 0, "enabled")
    monkeypatch.setattr(
        schedule_module,
        "_load_summary_translations",
        lambda: pytest.fail("summary translation resources were reloaded"),
    )

    assert switch.extra_state_attributes["schedule_summary"].endswith("(with PV surplus)")
    assert switch.extra_state_attributes["schedule_summary"].endswith("(with PV surplus)")


def test_summary_translations_are_loaded_from_existing_language_files():
    translation_dir = files("custom_components.goecharger_api2").joinpath("translations")
    expected = {}
    for language in ("de", "en", "fr"):
        translation_path = translation_dir.joinpath(f"{language}.json")
        with translation_path.open("r", encoding="utf-8") as resource:
            common = json.load(resource)["common"]
        expected[language] = (
            tuple(
                common[f"schedule_summary_{day}"]
                for day, _ in schedule_module._SUMMARY_WEEKDAYS
            ),
            common["schedule_summary_pv_surplus"],
        )

    assert schedule_module._SUMMARY_TRANSLATIONS == expected


@pytest.mark.parametrize(
    ("control", "expected_icon"),
    [
        (1, "mdi:flash"),
        (3, "mdi:flash"),
        (2, "mdi:cancel"),
        (4, "mdi:cancel"),
    ],
)
def test_schedule_switch_icons_follow_mode_only_for_enabled_switches(hass, control, expected_icon):
    coordinator = _coordinator(hass, [_rule(control)])

    assert ScheduleRuleSwitch(coordinator, 0, "enabled").icon == expected_icon
    assert ScheduleRuleSwitch(coordinator, 0, "allow_pv_surplus").icon == "mdi:calendar-clock"


def test_enabled_switch_summary_and_icon_are_safe_for_unavailable_rules(hass):
    coordinator = _coordinator(hass, [_rule()])
    missing = ScheduleRuleSwitch(coordinator, 1, "enabled")
    assert not missing.available
    assert missing.extra_state_attributes == {"schedule_summary": None}
    assert missing.icon == "mdi:calendar-clock"


@pytest.mark.parametrize(
    "overrides",
    [
        {"weekdays": "bad"},
        {"begin": [25, 0]},
        {"end": None},
    ],
)
def test_enabled_switch_summary_is_none_for_malformed_rule_values(hass, overrides):
    coordinator = _coordinator(hass, [_rule(**overrides)])
    malformed = ScheduleRuleSwitch(coordinator, 0, "enabled")

    assert malformed.extra_state_attributes == {"schedule_summary": None}
    assert malformed.icon == "mdi:calendar-clock"


def test_enabled_switch_uses_fallback_icon_for_invalid_control(hass):
    coordinator = _coordinator(
        hass,
        [_rule("invalid", weekdays=127, begin=[2, 36, 0], end=[4, 59, 0])],
    )
    switch = ScheduleRuleSwitch(coordinator, 0, "enabled")

    assert switch.icon == "mdi:calendar-clock"
    assert switch.extra_state_attributes == {
        "schedule_summary": "Mon, Tue, Wed, Thu, Fri, Sat, Sun, 02:36 - 04:59"
    }


@pytest.mark.parametrize(("control", "behavior", "pv"), [
    (1, "allow", False),
    (2, "block", False),
    (3, "allow", True),
    (4, "block", True),
])
async def test_rules_decode_behavior_pv_and_times(hass, control, behavior, pv):
    coordinator = _coordinator(hass, [_rule(control)])
    assert ScheduleRuleSelect(coordinator, 0).current_option == behavior
    assert ScheduleRuleSwitch(coordinator, 0, "allow_pv_surplus").is_on is pv
    assert ScheduleRuleTime(coordinator, 0, "begin").native_value == time(7, 15)
    assert ScheduleRuleTime(coordinator, 0, "end").native_value == time(18, 30)


@pytest.mark.parametrize(("control", "action"), [(1, 1), (2, 2), (3, 1), (4, 2)])
@pytest.mark.parametrize("enabled", [False, True])
async def test_pv_switch_preserves_behavior_and_other_rule_data(hass, control, action, enabled):
    original = [_rule(control), _rule(2, enabled=False)]
    coordinator = _coordinator(hass, original)
    switch = ScheduleRuleSwitch(coordinator, 0, "allow_pv_surplus")
    if enabled:
        await switch.async_turn_on()
    else:
        await switch.async_turn_off()
    written = coordinator.async_write_key.await_args.args[1]
    assert len(written) == len(original)
    assert written[0]["control"] == action + (2 if enabled else 0)
    assert written[0]["other"] == original[0]["other"]
    assert written[1] == original[1]
    assert original[0]["control"] == control


@pytest.mark.parametrize(("control", "option", "expected"), [
    (1, "block", 2),
    (2, "allow", 1),
    (3, "block", 4),
    (4, "allow", 3),
])
async def test_behavior_select_preserves_pv_setting(hass, control, option, expected):
    coordinator = _coordinator(hass, [_rule(control)])
    await ScheduleRuleSelect(coordinator, 0).async_select_option(option)
    assert coordinator.async_write_key.await_args.args[1][0]["control"] == expected


@pytest.mark.parametrize(("day", "bit"), WEEKDAYS)
async def test_weekday_switch_maps_bits_and_preserves_other_weekdays(hass, day, bit):
    coordinator = _coordinator(hass, [_rule(weekdays=bit ^ 2)])
    switch = ScheduleRuleSwitch(coordinator, 0, f"weekday_{day}", bit)
    assert switch.is_on is bool((bit ^ 2) & bit)
    await switch.async_turn_on()
    assert coordinator.async_write_key.await_args.args[1][0]["weekdays"] == bit | (bit ^ 2)


async def test_enabled_and_time_writes_patch_only_the_selected_field(hass):
    original = [_rule(), _rule(4)]
    coordinator = _coordinator(hass, original)
    await ScheduleRuleSwitch(coordinator, 0, "enabled").async_turn_off()
    written = coordinator.async_write_key.await_args.args[1]
    assert written[0]["enabled"] is False
    assert written[0]["weekdays"] == original[0]["weekdays"]
    assert written[0]["begin"] == original[0]["begin"]
    assert written[1] == original[1]

    coordinator.async_write_key.reset_mock()
    await ScheduleRuleTime(coordinator, 0, "begin").async_set_value(time(9, 5, 37))
    written = coordinator.async_write_key.await_args.args[1]
    assert written[0]["begin"] == [9, 5, 0]
    assert written[0]["end"] == original[0]["end"]
    assert written[1] == original[1]
    assert original[0]["begin"] == [7, 15, 42]
