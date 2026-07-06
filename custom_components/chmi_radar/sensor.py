from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, NAME

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ChmiRadarSensor(coordinator, entry, "rain_eta_minutes", "Odhad deště", "mdi:timer-outline", UnitOfTime.MINUTES),
        ChmiRadarSensor(coordinator, entry, "last_update", "Poslední aktualizace", "mdi:clock-outline", None),
    ])

class ChmiRadarSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, key: str, name: str, icon: str, unit: str | None) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        if key == "rain_eta_minutes":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title or NAME,
            "manufacturer": MANUFACTURER,
            "model": "Radar rain detector",
        }

    @property
    def native_value(self):
        data = self.coordinator.data
        return getattr(data, self._key, None) if data else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "raining_now": data.raining_now,
            "rain_incoming": data.rain_incoming,
            "intensity": data.intensity,
            "max_intensity_nearby": data.max_intensity_nearby,
            "motion_confidence": data.motion_confidence,
            "forecast_available": data.forecast_available,
            "forecast_note": data.forecast_note,
            "image_time": data.image_time,
            "source_url": data.url,
        }
