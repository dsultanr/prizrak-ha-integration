"""Device Tracker platform for Prizrak Monitoring."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PrizrakDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Prizrak device tracker based on a config entry."""
    coordinator: PrizrakDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create device tracker for each device
    entities = []
    for device_info in coordinator.client.devices:
        device_id = device_info['device_id']
        device_name = device_info.get('name', f"Prizrak {device_id}")
        device_model = device_info.get('model', 'Unknown')

        entities.append(
            PrizrakDeviceTracker(
                coordinator,
                device_id,
                device_name,
                device_model,
            )
        )

    async_add_entities(entities)


class PrizrakDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Representation of a Prizrak GPS tracker."""

    def __init__(
        self,
        coordinator: PrizrakDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        device_model: str,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name

        # Entity name and ID
        self._attr_name = device_name
        self._attr_unique_id = f"prizrak_{device_id}_tracker"
        self.entity_id = f"device_tracker.prizrak_{device_id}"
        self._attr_icon = "mdi:car"

        # Device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": device_name,
            "manufacturer": "Prizrak",
            "model": device_model,
            "suggested_area": "Garage",
        }

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        device_state = self.coordinator.devices.get(self._device_id, {})
        geo = device_state.get("geo", {})
        lat = geo.get("lat")

        # Validate latitude range
        if lat is not None:
            try:
                lat_float = float(lat)
                if -90 <= lat_float <= 90:
                    return lat_float
            except (ValueError, TypeError):
                pass
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        device_state = self.coordinator.devices.get(self._device_id, {})
        geo = device_state.get("geo", {})
        lon = geo.get("lon")

        # Validate longitude range
        if lon is not None:
            try:
                lon_float = float(lon)
                if -180 <= lon_float <= 180:
                    return lon_float
            except (ValueError, TypeError):
                pass
        return None

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Device tracker is available if we have valid coordinates
        return (
            self._device_id in self.coordinator.devices
            and self.latitude is not None
            and self.longitude is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        device_state = self.coordinator.devices.get(self._device_id, {})
        geo = device_state.get("geo", {})
        geo_ext = device_state.get("geo_ext", {})

        attributes = {}

        # GPS quality info
        if "gps_state" in geo:
            attributes["gps_state"] = geo["gps_state"]

        # Satellite info
        if "gnss_sat_used" in geo_ext:
            attributes["satellites"] = geo_ext["gnss_sat_used"]

        # Altitude
        if "gnss_height" in geo_ext:
            attributes["altitude"] = geo_ext["gnss_height"]

        # Speed from GPS
        if "gnss_speed" in geo_ext:
            attributes["gps_speed"] = geo_ext["gnss_speed"]

        # Azimuth/heading
        if "gnss_azimuth" in geo_ext:
            attributes["azimuth"] = geo_ext["gnss_azimuth"]

        # Vehicle speed (may differ from GPS speed)
        if "speed" in device_state:
            attributes["speed"] = device_state["speed"]

        return attributes
