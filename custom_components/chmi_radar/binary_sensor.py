from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, NAME

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ChmiRadarBinarySensor(coordinator, entry, "raining_now", "Prší", "mdi:weather-pouring"),
        ChmiRadarBinarySensor(coordinator, entry, "rain_incoming", "Déšť se blíží", "mdi:weather-rainy"),
    ])

class ChmiRadarBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, key: str, name: str, icon: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title or NAME,
            "manufacturer": MANUFACTURER,
            "model": "Radar rain detector",
        }

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return getattr(data, self._key, None) if data else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "rain_eta_minutes": data.rain_eta_minutes,
            "intensity": data.intensity,
            "max_intensity_nearby": data.max_intensity_nearby,
            "motion_confidence": data.motion_confidence,
            "forecast_available": data.forecast_available,
            "forecast_note": data.forecast_note,
            "image_time": data.image_time,
            "source_url": data.url,
            "pixel_x": data.pixel_x,
            "pixel_y": data.pixel_y,
        }
