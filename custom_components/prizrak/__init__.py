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

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.DEVICE_TRACKER]


async def _setup_www_files(hass: HomeAssistant) -> None:
    """Copy visualization files (SVG, PNG) to www directory."""
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

        # Create destination directory with proper permissions
        def setup_dest_dir():
            if dest_dir.exists():
                # Fix permissions if directory already exists
                try:
                    dest_dir.chmod(0o755)
                    _LOGGER.debug("Fixed permissions for existing www/prizrak/ directory")
                except Exception as e:
                    _LOGGER.warning(f"Could not fix permissions for www/prizrak/: {e}")
            else:
                # Create with proper permissions
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_dir.chmod(0o755)

        await hass.async_add_executor_job(setup_dest_dir)

        # Copy all SVG and PNG files
        copied_count = 0
        for file in source_dir.glob("*"):
            if file.suffix in [".svg", ".png"]:
                dest_file = dest_dir / file.name
                try:
                    # Always overwrite to ensure latest version
                    def copy_with_perms():
                        shutil.copy2(file, dest_file)
                        dest_file.chmod(0o644)

                    await hass.async_add_executor_job(copy_with_perms)
                    copied_count += 1
                except Exception as e:
                    _LOGGER.warning(f"Failed to copy {file.name}: {e}")

        if copied_count > 0:
            _LOGGER.info(f"Installed {copied_count} files to www/prizrak/")

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

    # Register reconnect service
    async def handle_reconnect(call):
        """Handle reconnect service call."""
        _LOGGER.info("Reconnect service called - forcing reconnection...")
        coordinator: PrizrakDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

        # Close current WebSocket connection to trigger reconnect
        if coordinator.client.websocket:
            try:
                await coordinator.client.websocket.close()
                _LOGGER.info("WebSocket closed, will reconnect automatically")
            except Exception as e:
                _LOGGER.error(f"Error closing WebSocket: {e}")

        # Reset connection_id to force new negotiation
        coordinator.client.connection_id = None
        _LOGGER.info("Connection ID reset for clean reconnection")

    hass.services.async_register(DOMAIN, "reconnect", handle_reconnect)

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

        # Unregister service
        hass.services.async_remove(DOMAIN, "reconnect")

    return unload_ok
