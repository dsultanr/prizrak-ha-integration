"""Binary sensor platform for Prizrak Monitoring."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BINARY_SENSOR_TYPES
from .coordinator import PrizrakDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Prizrak binary sensor based on a config entry."""
    coordinator: PrizrakDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create binary sensors for each device
    entities = []
    for device_info in coordinator.client.devices:
        device_id = device_info['device_id']

        device_name = device_info.get('name', f"Prizrak {device_id}") if device_info else f"Prizrak {device_id}"
        device_model = device_info.get('model', 'Unknown') if device_info else 'Unknown'

        for sensor_key, (name, device_class, state_key) in BINARY_SENSOR_TYPES.items():
            entities.append(
                PrizrakBinarySensor(
                    coordinator,
                    device_id,
                    device_name,
                    device_model,
                    sensor_key,
                    name,
                    device_class,
                    state_key
                )
            )

    async_add_entities(entities)


class PrizrakBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Prizrak binary sensor."""

    def __init__(
        self,
        coordinator: PrizrakDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        device_model: str,
        sensor_key: str,
        name: str,
        device_class: str,
        state_key: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_key = sensor_key
        self._state_key = state_key

        # Entity name and ID
        self._attr_name = name  # Friendly name shown in UI
        self._attr_unique_id = f"prizrak_{device_id}_{sensor_key}"
        self.entity_id = f"binary_sensor.prizrak_{device_id}_{sensor_key}"  # Force entity_id
        self._attr_device_class = device_class

        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": device_name,
            "manufacturer": "Prizrak",
            "model": device_model,
            "suggested_area": "Garage",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        device_state = self.coordinator.devices.get(self._device_id, {})

        # Handle nested keys (e.g., "geo.gps_state")
        if '.' in self._state_key:
            keys = self._state_key.split('.')
            value = device_state
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
        else:
            value = device_state.get(self._state_key)

        # Doors/locks: "Open" = ON (open)
        if value == "Open":
            return True

        # Connection: Connected = ON, Disconnected = OFF
        if self._state_key == "connection_state":
            return value == "Connected"

        # Guard: any state except SafeGuardOff = ON
        if self._state_key == "guard":
            return value not in ["SafeGuardOff", "Unknown", None, ""]

        # Alarm: anything except "Off" = ON
        if self._state_key == "alarm":
            return value not in ["Off", "Unknown", None, ""]

        # GPS: "Actual" = ON
        if self._state_key == "geo.gps_state":
            return value == "Actual"

        # Ignition: any state except engine off states = ON
        if self._state_key == "ignition_switch":
            return value not in ["EngineOffNoKey", "EngineOff", "Unknown", None, ""]

        # Parking brake: "On" = problem (ON)
        if self._state_key == "parking_brake":
            return value == "On"

        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.devices
