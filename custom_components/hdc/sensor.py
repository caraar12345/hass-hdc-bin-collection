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

    async def async_update_data():
        # DataUpdateCoordinator will handle aiohttp ClientErrors and timeouts
        async with asyncio.timeout(30):
            data = await collect_data(session=session, uprn=uprn)

        bins = {}
        for bin_collection in data:
            bins[bin_collection["bin_type"]] = bin_collection["collection_timestamp"]

        return bins

    hass.data[DOMAIN][uprn] = coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=12 * 60 * 60),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Create entities once based on the initial data
    entities = [
        Measurement(coordinator, uprn, bin_type)
        for bin_type in coordinator.data
    ]
    async_add_entities(entities)


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
