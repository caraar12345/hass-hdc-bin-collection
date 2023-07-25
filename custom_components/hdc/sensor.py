"""Support for bins and their collection dates from FCC/HDC API."""
from datetime import timedelta
import logging

from hdc_bin_collection import collect_data
import async_timeout

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
        async with async_timeout.timeout(30):
            data = await collect_data(session=session, uprn=uprn)

        entities = []
        bins = {}

        for bin_collection in data:
            entities.append(
                Measurement(
                    hass.data[DOMAIN][uprn],
                    str(uprn) + "_" + bin_collection["bin_type"] + "_bin",
                    uprn,
                    bin_collection["bin_type"],
                )
            )

            bins[bin_collection["bin_type"]] = bin_collection["collection_timestamp"]

        async_add_entities(entities)

        return bins

    hass.data[DOMAIN][uprn] = coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=12 * 60 * 60),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()


class Measurement(CoordinatorEntity, SensorEntity):
    """A bin and its next collection date."""

    _attr_attribution = (
        "This uses data from FCC Environment and Harborough District Council"
    )
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, key, uprn, bin_type):
        """Initialise the sensor with a bin type."""
        super().__init__(coordinator)
        self.key = key
        self._attr_unique_id = key
        self.uprn = uprn
        self.bin_type = bin_type

    @property
    def device_info(self):
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, "uprn_and_bin", self.key)},
            manufacturer="Harborough District Council",
            model=self.bin_type.title(),
            name=self.name,
            suggested_area="Outside",
        )

    @property
    def name(self):
        return f"{self.bin_type.title()} bin - {self.uprn}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        return True

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.coordinator.data[self.bin_type]

    @property
    def icon(self):
        """Set the icon to a bin rather than the default clock."""
        return "mdi:trash-can"
