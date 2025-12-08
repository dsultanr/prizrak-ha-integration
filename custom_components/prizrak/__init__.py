"""The Prizrak Monitoring integration."""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client import PrizrakClient
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .coordinator import PrizrakDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


async def _setup_www_files(hass: HomeAssistant) -> None:
    """Copy SVG files to www directory."""
    try:
        # Source: integration's www directory
        integration_path = Path(__file__).parent
        source_dir = integration_path / "www" / "prizrak"

        # Destination: HA's www directory
        www_dir = Path(hass.config.path("www"))
        dest_dir = www_dir / "prizrak"

        if not source_dir.exists():
            _LOGGER.debug("No www files found in integration directory")
            return

        # Create destination directory
        await hass.async_add_executor_job(dest_dir.mkdir, True, True)

        # Copy all SVG files
        copied_count = 0
        for svg_file in source_dir.glob("*.svg"):
            dest_file = dest_dir / svg_file.name
            try:
                # Always overwrite to ensure latest version
                await hass.async_add_executor_job(shutil.copy2, svg_file, dest_file)
                copied_count += 1
            except Exception as e:
                _LOGGER.warning(f"Failed to copy {svg_file.name}: {e}")

        if copied_count > 0:
            _LOGGER.info(f"Installed {copied_count} SVG files to www/prizrak/")

    except PermissionError:
        _LOGGER.error("Permission denied when copying SVG files. Check file permissions for /config/www/")
    except Exception as e:
        _LOGGER.warning(f"Failed to setup www files: {e}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Prizrak from a config entry."""
    # Copy SVG files on first setup
    await _setup_www_files(hass)

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    # Create coordinator
    coordinator = PrizrakDataUpdateCoordinator(hass, None)

    # Create client with coordinator callback that schedules updates in HA event loop
    def state_update_callback(device_id: int, state: dict) -> None:
        """Schedule state update in HA event loop."""
        hass.loop.call_soon_threadsafe(
            coordinator.handle_device_update, device_id, state
        )

    client = PrizrakClient(
        email,
        password,
        state_update_callback
    )

    # Store client in coordinator
    coordinator.client = client

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Start client in background
    async def start_client_task():
        """Start the client in background."""
        try:
            await client.run()
        except Exception as e:
            _LOGGER.error(f"Client error: {e}")

    # Create background task
    task = hass.async_create_task(start_client_task())

    # Store task for cleanup
    hass.data[DOMAIN][f"{entry.entry_id}_task"] = task

    # Wait for devices to be ready (with timeout)
    try:
        _LOGGER.info("Waiting for devices to be ready...")
        await asyncio.wait_for(client.devices_ready.wait(), timeout=30.0)
        _LOGGER.info("Devices are ready, setting up platforms")
    except asyncio.TimeoutError:
        _LOGGER.error("Timeout waiting for devices, setting up platforms anyway")

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop the client
    coordinator: PrizrakDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.stop()

    # Cancel the background task
    task = hass.data[DOMAIN].get(f"{entry.entry_id}_task")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop(f"{entry.entry_id}_task", None)

    return unload_ok
