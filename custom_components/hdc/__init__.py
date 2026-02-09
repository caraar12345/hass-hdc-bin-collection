"""Harborough District Council - bin collection dates integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORM: Platform = Platform.SENSOR


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up bin collection date sensors from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, [PLATFORM])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload bin collection date sensors."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [PLATFORM])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.data["uprn"], None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok
