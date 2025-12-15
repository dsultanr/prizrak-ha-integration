"""DataUpdateCoordinator for Prizrak integration."""
from __future__ import annotations

import logging
import time
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

        # Throttling for frontend updates to prevent browser memory issues
        # Data is always up-to-date on HA server, but browser UI updates are throttled
        self.last_frontend_update: float = 0.0
        self.frontend_update_interval: float = 30.0  # seconds

    @callback
    def handle_device_update(self, device_id: int, device_state: dict[str, Any]) -> None:
        """Handle device state update from WebSocket.

        Args:
            device_id: Device ID
            device_state: New device state (partial update)
        """
        # Use client.device_states which accumulates ALL fields
        # instead of coordinator.devices which only gets partial updates
        full_device_state = self.client.device_states.get(device_id, {})

        if full_device_state:
            # Add timestamp of last update (as datetime object for TIMESTAMP device_class)
            full_device_state["last_update"] = dt_util.utcnow()

            # Convert timestamp strings to datetime objects
            time_key = "last_device_exchange_time"
            if time_key in full_device_state and isinstance(full_device_state[time_key], str):
                try:
                    full_device_state[time_key] = dt_util.parse_datetime(full_device_state[time_key])
                except (ValueError, TypeError):
                    _LOGGER.warning(f"Could not parse {time_key}: {full_device_state[time_key]}")
                    full_device_state[time_key] = None

            # ALWAYS update coordinator's cache (server-side data)
            # This ensures automations, scripts, and history have real-time data
            self.devices[device_id] = full_device_state

            # Throttle frontend updates to prevent browser memory issues
            # Only notify frontend (browser UI) if enough time has passed
            current_time = time.time()
            time_since_last_update = current_time - self.last_frontend_update

            if time_since_last_update >= self.frontend_update_interval:
                # Notify all listeners (entities) about the update → triggers browser UI redraw
                self.async_set_updated_data(self.devices)
                self.last_frontend_update = current_time
                _LOGGER.debug(
                    f"Frontend update sent (throttled: {time_since_last_update:.1f}s since last)"
                )
            else:
                # Data updated on server, but browser UI not notified yet (throttled)
                _LOGGER.debug(
                    f"Frontend update skipped (throttled: {time_since_last_update:.1f}s < {self.frontend_update_interval}s)"
                )
        else:
            _LOGGER.warning(f"Device {device_id} not found in client.device_states")

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Update data via library.

        This is only used as a fallback. Real updates come via WebSocket callbacks.
        """
        return self.devices
