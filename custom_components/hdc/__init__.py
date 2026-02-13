"""Harborough District Council - bin collection dates integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORM: Platform = Platform.SENSOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up bin collection date sensors from a config entry."""

    _LOGGER.debug("Setting up config entry %s (UPRN: %s)", entry.entry_id, entry.data.get("uprn"))
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, [PLATFORM])
    _LOGGER.debug("Config entry %s setup complete", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload bin collection date sensors."""
    _LOGGER.debug("Unloading config entry %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [PLATFORM])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.data["uprn"], None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    _LOGGER.debug("Config entry %s unload result: %s", entry.entry_id, unload_ok)
    return unload_ok
