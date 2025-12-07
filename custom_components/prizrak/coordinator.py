"""DataUpdateCoordinator for Prizrak integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .client import PrizrakClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PrizrakDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Prizrak data."""

    def __init__(self, hass: HomeAssistant, client: PrizrakClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # No update_interval - updates come via WebSocket
        )
        self.client = client
        self.devices: dict[int, dict[str, Any]] = {}

    @callback
    def handle_device_update(self, device_id: int, device_state: dict[str, Any]) -> None:
        """Handle device state update from WebSocket.

        Args:
            device_id: Device ID
            device_state: New device state
        """
        if device_id not in self.devices:
            self.devices[device_id] = {}

        # Merge new state with existing
        self.devices[device_id].update(device_state)

        # Add timestamp of last update (as datetime object for TIMESTAMP device_class)
        self.devices[device_id]["last_update"] = dt_util.utcnow()

        # Notify all listeners (entities) about the update
        self.async_set_updated_data(self.devices)

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Update data via library.

        This is only used as a fallback. Real updates come via WebSocket callbacks.
        """
        return self.devices
