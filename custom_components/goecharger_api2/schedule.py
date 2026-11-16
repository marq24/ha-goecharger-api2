"""Entities for the editable go-e charger schedule rules."""

import logging
import re
from datetime import time
from typing import Callable

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.const import Platform
from homeassistant.helpers.entity import EntityDescription

from . import GoeChargerBaseEntity, GoeChargerDataUpdateCoordinator
from .const import ExtSwitchEntityDescription
from .pygoecharger_ha.keys import Tag

_LOGGER = logging.getLogger(__name__)
SCHEDULE_RULE_COUNT = 10
WEEKDAYS = (
    ("sunday", 1),
    ("monday", 2),
    ("tuesday", 4),
    ("wednesday", 8),
    ("thursday", 16),
    ("friday", 32),
    ("saturday", 64),
)


def supports_schedule_rules(coordinator: GoeChargerDataUpdateCoordinator) -> bool:
    """Schedule rules are only exposed by charger firmware 60 and newer."""
    if coordinator.intg_type != "charger":
        return False
    version = coordinator.bridge._versions.get(Tag.FWV.key, "")
    match = re.match(r"\s*(\d+)", str(version))
    return match is not None and int(match.group(1)) >= 60


def schedule_rule(coordinator: GoeChargerDataUpdateCoordinator, index: int) -> dict | None:
    data = coordinator.data
    rules = data.get(Tag.SCH_RULES.key) if data is not None else None
    if not isinstance(rules, list) or index < 0 or index >= len(rules):
        return None
    rule = rules[index]
    return rule if isinstance(rule, dict) else None


def schedule_rule_count(coordinator: GoeChargerDataUpdateCoordinator) -> int:
    """Return the number of schedule slots currently exposed by the charger."""
    data = coordinator.data
    rules = data.get(Tag.SCH_RULES.key) if data is not None else None
    return min(len(rules), SCHEDULE_RULE_COUNT) if isinstance(rules, list) else 0


def add_schedule_rule_entities(coordinator, config_entry, add_entity_cb, create_entities) -> None:
    """Add current rule entities and append new slots as coordinator data grows."""
    created_count = schedule_rule_count(coordinator)
    if created_count:
        add_entity_cb(create_entities(coordinator, 0, created_count))

    def _handle_coordinator_update():
        nonlocal created_count
        current_count = schedule_rule_count(coordinator)
        if current_count <= created_count:
            return
        start_index = created_count
        created_count = current_count
        add_entity_cb(create_entities(coordinator, start_index, current_count))

    remove_listener = coordinator.async_add_listener(_handle_coordinator_update)
    config_entry.async_on_unload(remove_listener)


def _schedule_rule_range(coordinator, start_index, stop_index):
    start_index = max(0, min(start_index, SCHEDULE_RULE_COUNT))
    if stop_index is None:
        stop_index = schedule_rule_count(coordinator)
    stop_index = max(start_index, min(stop_index, SCHEDULE_RULE_COUNT))
    return start_index, stop_index


class ScheduleRuleEntity(GoeChargerBaseEntity):
    def __init__(self, coordinator, description: EntityDescription, rule_index: int, entity_type: str):
        super().__init__(entity_type, coordinator, description)
        self.rule_index = rule_index
        # Keep translation keys shared while giving each fixed slot a unique ID.
        self.entity_id = self.entity_id.replace("sch_rules_", f"sch_rules_{rule_index + 1}_", 1)

    @property
    def available(self):
        return super().available and schedule_rule(self.coordinator, self.rule_index) is not None

    async def update_rule(self, update: Callable[[dict], None]) -> None:
        rules = self.coordinator.data.get(Tag.SCH_RULES.key) if self.coordinator.data is not None else None
        if not isinstance(rules, list) or self.rule_index >= len(rules) or not isinstance(rules[self.rule_index], dict):
            raise ValueError(f"Schedule rule {self.rule_index} is unavailable")

        updated_rules = list(rules)
        updated_rule = dict(rules[self.rule_index])
        update(updated_rule)
        updated_rules[self.rule_index] = updated_rule
        await self.coordinator.async_write_key(Tag.SCH_RULES.key, updated_rules, self)


class ScheduleRuleSwitch(ScheduleRuleEntity, SwitchEntity):
    def __init__(self, coordinator, rule_index: int, field: str, bit: int | None = None):
        translation_key = f"sch_rules_{field}"
        description = ExtSwitchEntityDescription(
            key=Tag.SCH_RULES.key,
            translation_key=translation_key,
            translation_placeholders={"index": str(rule_index + 1)},
            icon="mdi:calendar-clock",
        )
        super().__init__(coordinator, description, rule_index, Platform.SWITCH)
        self.field = field
        self.bit = bit

    @property
    def is_on(self) -> bool | None:
        rule = schedule_rule(self.coordinator, self.rule_index)
        if rule is None:
            return None
        if self.field == "enabled":
            value = rule.get("enabled")
            return value if isinstance(value, bool) else None
        if self.field.startswith("weekday_"):
            try:
                return bool(int(rule.get("weekdays", 0)) & self.bit)
            except (TypeError, ValueError):
                return None
        try:
            control = int(rule["control"])
        except (KeyError, TypeError, ValueError):
            return None
        return control in (3, 4)

    async def _set_switch(self, enabled: bool) -> None:
        def update(rule):
            if self.field == "enabled":
                rule["enabled"] = enabled
            elif self.field.startswith("weekday_"):
                weekdays = int(rule.get("weekdays", 0))
                rule["weekdays"] = weekdays | self.bit if enabled else weekdays & ~self.bit
            else:
                control = int(rule["control"])
                if control not in (1, 2, 3, 4):
                    raise ValueError(f"Invalid schedule control value: {control}")
                allow = control in (1, 3)
                rule["control"] = (1 if allow else 2) + (2 if enabled else 0)

        try:
            await self.update_rule(update)
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Could not update schedule rule %s: %s", self.rule_index, err)

    async def async_turn_on(self, **kwargs):
        await self._set_switch(True)

    async def async_turn_off(self, **kwargs):
        await self._set_switch(False)


class ScheduleRuleSelect(ScheduleRuleEntity, SelectEntity):
    def __init__(self, coordinator, rule_index: int):
        description = SelectEntityDescription(
            key=Tag.SCH_RULES.key,
            translation_key="sch_rules_behavior",
            translation_placeholders={"index": str(rule_index + 1)},
            options=["allow", "block"],
            icon="mdi:calendar-clock",
        )
        super().__init__(coordinator, description, rule_index, Platform.SELECT)

    @property
    def current_option(self) -> str | None:
        rule = schedule_rule(self.coordinator, self.rule_index)
        try:
            control = int(rule["control"]) if rule is not None else 0
        except (KeyError, TypeError, ValueError):
            return None
        if control in (1, 3):
            return "allow"
        if control in (2, 4):
            return "block"
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in ("allow", "block"):
            return

        def update(rule):
            control = int(rule["control"])
            if control not in (1, 2, 3, 4):
                raise ValueError(f"Invalid schedule control value: {control}")
            pv_enabled = control in (3, 4)
            rule["control"] = (
                (3 if pv_enabled else 1) if option == "allow"
                else (4 if pv_enabled else 2)
            )

        try:
            await self.update_rule(update)
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Could not update schedule rule %s: %s", self.rule_index, err)


class ScheduleRuleTime(ScheduleRuleEntity, TimeEntity):
    def __init__(self, coordinator, rule_index: int, field: str):
        translation_field = "start" if field == "begin" else field
        description = TimeEntityDescription(
            key=Tag.SCH_RULES.key,
            translation_key=f"sch_rules_{translation_field}",
            translation_placeholders={"index": str(rule_index + 1)},
            icon="mdi:clock-outline",
        )
        super().__init__(coordinator, description, rule_index, Platform.TIME)
        self.field = field

    @property
    def native_value(self) -> time | None:
        rule = schedule_rule(self.coordinator, self.rule_index)
        value = rule.get(self.field) if rule is not None else None
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            return None
        try:
            return time(int(value[0]), int(value[1]))
        except (TypeError, ValueError, OverflowError):
            return None

    async def async_set_value(self, value: time) -> None:
        def update(rule):
            rule[self.field] = [value.hour, value.minute, 0]

        await self.update_rule(update)


def create_schedule_rule_switches(coordinator, start_index=0, stop_index=None):
    start_index, stop_index = _schedule_rule_range(coordinator, start_index, stop_index)
    entities = []
    for index in range(start_index, stop_index):
        entities.append(ScheduleRuleSwitch(coordinator, index, "enabled"))
        entities.append(ScheduleRuleSwitch(coordinator, index, "allow_pv_surplus"))
        entities.extend(
            ScheduleRuleSwitch(coordinator, index, f"weekday_{day}", bit)
            for day, bit in WEEKDAYS
        )
    return entities


def create_schedule_rule_selects(coordinator, start_index=0, stop_index=None):
    start_index, stop_index = _schedule_rule_range(coordinator, start_index, stop_index)
    return [ScheduleRuleSelect(coordinator, index) for index in range(start_index, stop_index)]


def create_schedule_rule_times(coordinator, start_index=0, stop_index=None):
    start_index, stop_index = _schedule_rule_range(coordinator, start_index, stop_index)
    return [
        ScheduleRuleTime(coordinator, index, field)
        for index in range(start_index, stop_index)
        for field in ("begin", "end")
    ]
