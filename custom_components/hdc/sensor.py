"""Support for bins and their collection dates from FCC/HDC API."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bin Collection Sensors."""
    uprn = config_entry.data["uprn"]
    coordinator = hass.data[DOMAIN][uprn]
    async_add_entities(
        Measurement(coordinator, uprn, bin_type) for bin_type in coordinator.data
    )


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
