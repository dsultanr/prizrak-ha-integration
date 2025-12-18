"""DataUpdateCoordinator for Prizrak integration."""
from __future__ import annotations

import asyncio
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
        self.throttling_enabled: bool = True
        self.throttling_disable_task: Any | None = None

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

            # Check if throttling is enabled and enough time has passed
            should_update = not self.throttling_enabled or time_since_last_update >= self.frontend_update_interval

            if should_update:
                # Notify all listeners (entities) about the update → triggers browser UI redraw
                self.async_set_updated_data(self.devices)
                self.last_frontend_update = current_time
                throttle_status = "disabled" if not self.throttling_enabled else f"throttled: {time_since_last_update:.1f}s since last"
                _LOGGER.debug(f"Frontend update sent ({throttle_status})")
            else:
                # Data updated on server, but browser UI not notified yet (throttled)
                _LOGGER.debug(
                    f"Frontend update skipped (throttled: {time_since_last_update:.1f}s < {self.frontend_update_interval}s)"
                )
        else:
            _LOGGER.warning(f"Device {device_id} not found in client.device_states")

    def disable_throttling_temporarily(self, duration: float = 30.0) -> None:
        """Temporarily disable frontend update throttling.

        Used after sending commands (Guard, Autolaunch) to show immediate feedback.
        Throttling is re-enabled after specified duration.

        Args:
            duration: How long to disable throttling (seconds)
        """
        # Cancel previous task if exists
        if self.throttling_disable_task and not self.throttling_disable_task.done():
            self.throttling_disable_task.cancel()

        # Disable throttling
        self.throttling_enabled = False
        _LOGGER.info(f"Throttling disabled for {duration}s (command sent)")

        # Schedule re-enable
        async def re_enable_throttling():
            await asyncio.sleep(duration)
            self.throttling_enabled = True
            _LOGGER.info("Throttling re-enabled")

        self.throttling_disable_task = self.hass.async_create_task(re_enable_throttling())

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Update data via library.

        This is only used as a fallback. Real updates come via WebSocket callbacks.
        """
        return self.devices
