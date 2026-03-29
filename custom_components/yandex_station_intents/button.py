from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Component
from .const import DOMAIN
from .entry_data import ConfigEntryData
from .export import async_export_intents

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    component: Component = hass.data[DOMAIN]
    async_add_entities([YandexIntentsExportButton(component.entry_datas[entry.entry_id])])


class YandexIntentsExportButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, entry_data: ConfigEntryData) -> None:
        self._entry_data = entry_data
        self._attr_unique_id = f"{entry_data.entry.entry_id}_export_intents"
        self._attr_name = "Export intents"

    async def async_press(self) -> None:
        out_path = await async_export_intents(self.hass, self._entry_data)
        _LOGGER.info("Интенты экспортированы в %s", out_path)
