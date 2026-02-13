"""Support for bins and their collection dates from FCC/HDC API."""
import asyncio
from datetime import timedelta
import logging

from hdc_bin_collection import collect_data

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bin Collection Sensors."""
    uprn = config_entry.data["uprn"]
    session = async_get_clientsession(hass=hass)
    _LOGGER.debug("Setting up sensor platform for UPRN %s", uprn)

    async def async_update_data():
        # DataUpdateCoordinator will handle aiohttp ClientErrors and timeouts
        _LOGGER.debug("Fetching bin collection data for UPRN %s", uprn)
        async with asyncio.timeout(30):
            data = await collect_data(session=session, uprn=uprn)

        _LOGGER.debug("Received %d bin collection(s) for UPRN %s", len(data), uprn)

        bins = {}
        for bin_collection in data:
            bins[bin_collection["bin_type"]] = bin_collection["collection_timestamp"]

        _LOGGER.debug("Parsed bin data for UPRN %s: %s", uprn, bins)
        return bins

    hass.data[DOMAIN][uprn] = coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=12 * 60 * 60),
    )

    # Fetch initial data so we have data when entities subscribe
    _LOGGER.debug("Performing first data refresh for UPRN %s", uprn)
    await coordinator.async_config_entry_first_refresh()

    # Create entities once based on the initial data
    _LOGGER.debug("Creating %d sensor entities for UPRN %s: %s", len(coordinator.data), uprn, list(coordinator.data.keys()))
    entities = [
        Measurement(coordinator, uprn, bin_type)
        for bin_type in coordinator.data
    ]
    async_add_entities(entities)
    _LOGGER.debug("Sensor platform setup complete for UPRN %s", uprn)


class Measurement(CoordinatorEntity, SensorEntity):
    """A bin and its next collection date."""

    _attr_attribution = (
        "This uses data from FCC Environment and Harborough District Council"
    )
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:trash-can"
    _attr_has_entity_name = True

    def __init__(self, coordinator, uprn, bin_type):
        """Initialise the sensor with a bin type."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{uprn}_{bin_type}_bin"
        self._attr_name = f"{bin_type.title()} bin"
        self.bin_type = bin_type
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, str(uprn))},
            manufacturer="Harborough District Council",
            name="Bin collection",
            suggested_area="Outside",
        )

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.coordinator.data.get(self.bin_type)
