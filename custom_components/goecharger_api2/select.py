import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.goecharger_api2 import GoeChargerDataUpdateCoordinator, GoeChargerBaseEntity
from custom_components.goecharger_api2.const import DOMAIN, SELECT_SENSORS, CONTROLLER_SELECT_SENSORS, \
    ExtSelectEntityDescription
from custom_components.goecharger_api2.pygoecharger_ha import INTG_TYPE
from custom_components.goecharger_api2.pygoecharger_ha.const import CT_VALUES, CT_VALUES_MAP
from custom_components.goecharger_api2.pygoecharger_ha.keys import Tag

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, add_entity_cb: AddEntitiesCallback):
    _LOGGER.debug("SELECT async_setup_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    if coordinator.intg_type == INTG_TYPE.CHARGER.value:
        for description in SELECT_SENSORS:
            if coordinator.is_valid_charger_entity(description):
                entity = GoeChargerSelect(coordinator, description)
                entities.append(entity)
    else:
        for description in CONTROLLER_SELECT_SENSORS:
            entity = GoeChargerSelect(coordinator, description)
            entities.append(entity)

    add_entity_cb(entities)


class GoeChargerSelect(GoeChargerBaseEntity, SelectEntity):
    def __init__(self, coordinator: GoeChargerDataUpdateCoordinator, description: ExtSelectEntityDescription):
        if description.key == Tag.TRX.key:
            new_options = ["null", "0"] + coordinator.available_cards_idx
            # ok we need to create a new entity description with the new options...
            # [since ExtSelectEntityDescription is frozen]
            description = ExtSelectEntityDescription (
                key = description.key,
                device_class = description.device_class,
                entity_category = description.entity_category,
                entity_registry_enabled_default = description.entity_registry_enabled_default,
                entity_registry_visible_default = description.entity_registry_visible_default,
                force_update = description.force_update,
                icon = description.icon,
                has_entity_name = description.has_entity_name,
                name = description.name,
                translation_key = description.translation_key,
                translation_placeholders = description.translation_placeholders,
                unit_of_measurement = description.unit_of_measurement,
                options = new_options,
                idx = description.idx,
            )
        super().__init__(entity_type=Platform.SELECT, coordinator=coordinator, description=description)

    @property
    def current_option(self) -> str | None:
        try:
            value = None
            if self.coordinator.data is not None:
                if self.entity_description.idx is not None:
                    if self.data_key in self.coordinator.data:
                        value = self.coordinator.data[self.data_key][self.entity_description.idx]
                    else:
                        _LOGGER.info(f"current_option: for `{self.data_key}` with index `{self.entity_description.idx}` not found in data: {len(self.coordinator.data)}")
                        return "unavailable"
                else:
                    if self.data_key in self.coordinator.data:
                        value = self.coordinator.data[self.data_key]
                    else:
                        _LOGGER.info(f"current_option: for `{self.data_key}` not found in data: {len(self.coordinator.data)}")


            if value is None or value == "":
                # special handling for tra 'transaction' API key...
                # where None means that Auth is required
                if self.data_key == Tag.TRX.key:
                    value = "null"
                elif self.data_key == Tag.CT.key:
                    value = CT_VALUES.DEFAULT.value
                else:
                    value = 'unknown'

            if isinstance(value, int):
                value = str(value)

            if self.data_key == Tag.CT.key:
                value = value.lower()

        except KeyError:
            value = "unknown"
        except TypeError:
            return None
        return value

    async def async_select_option(self, option: str) -> None:
        try:

            if self.entity_description.idx is not None:
                if self.data_key in self.coordinator.data:
                    # we have to write all values of the object... [not only the set one]
                    obj = self.coordinator.data[self.data_key]
                    if str(option) == "null":
                        obj[self.entity_description.idx] = None
                    else:
                        if self.entity_description.key in [Tag.SCH_WEEK.key, Tag.SCH_SATUR.key, Tag.SCH_SUND.key]:
                            # 1. we must post the new value as integer
                            option = int(option)
                            # 2. we must remove the 'second' object from the 'begin' & 'end' time information
                            # this is quite ridiculous!
                            for interval in obj["ranges"]:
                                if "second" in interval["begin"]:
                                    del interval["begin"]["second"]
                                if "second" in interval["end"]:
                                    del interval["end"]["second"]

                        obj[self.entity_description.idx] = option

                    await self.coordinator.async_write_key(self.data_key, obj, self)
                else:
                    _LOGGER.warning(f"async_select_option: for {self.data_key} with index not found in data: {len(self.coordinator.data)}")
                    return "unavailable"
            else:
                if str(option) == "null":
                    await self.coordinator.async_write_key(self.data_key, None, self)

                else:
                    if self.data_key == Tag.CT.key:
                        # quite a quick hack - since normally we write multiple values via a service...
                        args = {Tag.CT.key: str(CT_VALUES_MAP[option])}

                        # go-e App set
                        # ct, mca, mci, acp, su, mcpd, fmt, psm, fst, spl3, mpwst, mptwt

                        # NOT CHANGING:
                        # mci: 0, fmt: 300000, fst: 1400, spl3: 4200, mpwst: 120000, mptwt: 600000

                        # ALL: mca: 6 (except renaultZoe=10), psm: 0 (except daciaSpring=1)
                        #default,               acp: true,  su: false,  mcpd: 0,
                        #kiaSoul,               acp: true,  su: true,   mcpd: 0,
                        #renaultZoe,    mca:10, acp: true,  su: true,   mcpd: 0,
                        #MitsubishiImiev,       acp: true,  su: true,   mcpd: 0,
                        #citroenCZero,          acp: true,  su: true,   mcpd: 0,
                        #peugeotIon.            acp: true,  su: true,   mcpd: 0,

                        #ecorsa,                acp: true,  su: true,   mcpd: 0,
                        #vwID3_2,               acp: false, su: false,  mcpd: 0,
                        #vwID3_4,               acp: true,  su: true,   mcpd: 0,
                        #vwID5,                 acp: true,  su: true,   mcpd: 0,
                        #cupraBornStandard,     acp: true,  su: true,   mcpd: 0, ...
                        #cupraBornAlternative,  acp: true,  su: true,   mcpd: 120000, ...
                        #fordExplorer,          acp: true,  su: true,   mcpd: 120000, ...
                        #porscheTaycan,         acp: true,  su: true,   mcpd: 120000, ...
                        #SkodaEnyaq,            acp: true,  su: true,   mcpd: 120000, ...
                        #daciaSpring,           acp: true,  su: false,  mcpd: 0, ... psm:1
                        #mercedes,              acp: true,  su: true,   mcpd: 0,
                        #ssangyong,             acp: true,  su: false,  mcpd: 0,

                        # setting the Minimum charging current (mca)
                        if option == CT_VALUES.RENAULTZOE.value:
                            # Zoe need's 10 as value
                            args[Tag.MCA.key] = 10
                        else:
                            args[Tag.MCA.key] = 6

                        # allowChargePause (acp) false when vwID3_2, true otherwise
                        if option == CT_VALUES.VWID3_2.value:
                            args[Tag.ACP.key] = False
                        else:
                            args[Tag.ACP.key] = True

                        # simulateUnpluggingShort (su) false, when Default, vwID3_2, daciaSpring, true otherwise
                        if option in [CT_VALUES.DEFAULT.value, CT_VALUES.VWID3_2.value, CT_VALUES.DACIASPRING.value, CT_VALUES.SSANGYONG.value]:
                            args[Tag.SU.key] = False
                        else:
                            args[Tag.SU.key] = True

                        # phaseSwitchMode (psm) 1, when daciaSpring, 0 otherwise
                        if option == CT_VALUES.DACIASPRING.value:
                            args[Tag.PSM.key] = 1
                        else:
                            args[Tag.PSM.key] = 0

                        # minChargePauseDuration (mcpd)
                        if option in [CT_VALUES.CUPRABORNALTERNATIVE.value, CT_VALUES.FORDEXPLORER.value, CT_VALUES.PORSCHETAYCAN.value, CT_VALUES.SKODAENYAQ.value]:
                            args[Tag.MCPD.key] = 120000
                        else:
                            args[Tag.MCPD.key] = 0

                        # finally wringing the key...
                        await self.coordinator.async_write_multiple_keys(attr=args, key=self.data_key, value=option, entity=self)
                    else:
                        await self.coordinator.async_write_key(self.data_key, int(option), self)
        except ValueError:
            return "unavailable"
