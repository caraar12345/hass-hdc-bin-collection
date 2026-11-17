"""Harborough District Council - bin collection dates integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from hdc_bin_collection import collect_data

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

PLATFORM: Platform = Platform.SENSOR
UPDATE_INTERVAL = timedelta(hours=12)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up bin collection date sensors from a config entry."""
    uprn = entry.data["uprn"]
    session = async_get_clientsession(hass=hass)
    _LOGGER.debug("Setting up config entry %s", entry.entry_id)

    async def async_update_data() -> dict:
        async with asyncio.timeout(30):
            data = await collect_data(session=session, uprn=uprn)

        # The library reports failures as a string rather than raising.
        if isinstance(data, str):
            if data == "invalid_uprn":
                raise UpdateFailed(
                    "The council's site rejected the UPRN (it redirected instead of "
                    "returning collection dates)"
                )
            raise UpdateFailed(f"Couldn't fetch bin collection dates: {data}")

        bins = {b["bin_type"]: b["collection_timestamp"] for b in data}
        _LOGGER.debug("Parsed bin data: %s", bins)
        return bins

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    # Raises ConfigEntryNotReady on failure, so HA retries the setup later.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[uprn] = coordinator
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
