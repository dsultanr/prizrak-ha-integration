"""Sensor platform for Prizrak Monitoring."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import PrizrakDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Prizrak sensor based on a config entry."""
    coordinator: PrizrakDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait a bit for initial data
    await coordinator.async_config_entry_first_refresh()

    # Create sensors for each device
    entities = []
    for device_id in coordinator.devices.keys():
        device_data = coordinator.client.devices
        device_info = None
        for dev in device_data:
            if dev['device_id'] == device_id:
                device_info = dev
                break

        device_name = device_info.get('name', f"Prizrak {device_id}") if device_info else f"Prizrak {device_id}"

        for sensor_key, (name, unit, device_class, icon, state_key) in SENSOR_TYPES.items():
            entities.append(
                PrizrakSensor(
                    coordinator,
                    device_id,
                    device_name,
                    sensor_key,
                    name,
                    unit,
                    device_class,
                    icon,
                    state_key
                )
            )

    async_add_entities(entities)


def get_nested_value(data: dict, key: str) -> Any:
    """Get value from nested dictionary using dot notation.

    Args:
        data: Dictionary to search
        key: Key in dot notation (e.g., 'geo.lat' or 'balance.value')

    Returns:
        Value if found, None otherwise
    """
    if '.' not in key:
        return data.get(key)

    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return None
    return value


class PrizrakSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Prizrak sensor."""

    def __init__(
        self,
        coordinator: PrizrakDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        sensor_key: str,
        name: str,
        unit: str | None,
        device_class: str | None,
        icon: str | None,
        state_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_key = sensor_key
        self._state_key = state_key

        self._attr_name = f"{device_name} {name}"
        self._attr_unique_id = f"prizrak_{device_id}_{sensor_key}"
        self._attr_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon

        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": device_name,
            "manufacturer": "Prizrak",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        device_state = self.coordinator.devices.get(self._device_id, {})
        return get_nested_value(device_state, self._state_key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.devices
