"""Button platform for Prizrak Monitoring."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, BUTTON_TYPES
from .coordinator import PrizrakDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Prizrak button based on a config entry."""
    coordinator: PrizrakDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create buttons for each device
    entities = []
    for device_info in coordinator.client.devices:
        device_id = device_info['device_id']

        device_name = device_info.get('name', f"Prizrak {device_id}") if device_info else f"Prizrak {device_id}"
        device_model = device_info.get('model', 'Unknown') if device_info else 'Unknown'

        for button_key, (name, command, icon) in BUTTON_TYPES.items():
            entities.append(
                PrizrakButton(
                    coordinator,
                    device_id,
                    device_name,
                    device_model,
                    button_key,
                    name,
                    command,
                    icon
                )
            )

    async_add_entities(entities)


class PrizrakButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Prizrak button."""

    def __init__(
        self,
        coordinator: PrizrakDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        device_model: str,
        button_key: str,
        name: str,
        command: str,
        icon: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._button_key = button_key
        self._command = command

        # Entity name and ID
        self._attr_name = name  # Friendly name shown in UI
        self._attr_unique_id = f"prizrak_{device_id}_{button_key}"
        self.entity_id = f"button.prizrak_{device_id}_{button_key}"  # Force entity_id
        self._attr_icon = icon

        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": device_name,
            "manufacturer": "Prizrak",
            "model": device_model,
            "suggested_area": "Garage",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info(f"Button pressed: {self._command} for device {self._device_id}")

        # Check if coordinator is available
        if not self.coordinator.client.websocket:
            _LOGGER.error(f"Cannot send command {self._command}: WebSocket not connected")
            raise HomeAssistantError(
                f"Cannot execute command: Not connected to Prizrak server. "
                f"Please check your internet connection and try again."
            )

        # Send command via client with timeout
        try:
            success = await self.coordinator.client.send_command(
                self._device_id,
                self._command,
                timeout=10.0
            )

            if success:
                _LOGGER.info(f"Command {self._command} executed successfully on device {self._device_id}")
            else:
                _LOGGER.error(f"Command {self._command} failed on device {self._device_id}")
                raise HomeAssistantError(
                    f"Command failed: Server rejected the command or device is offline. "
                    f"Please check device status and try again."
                )

        except Exception as e:
            _LOGGER.error(f"Error executing command {self._command}: {e}")
            if isinstance(e, HomeAssistantError):
                raise
            raise HomeAssistantError(
                f"Command execution error: {str(e)}"
            )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device_id in self.coordinator.devices
