from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import *

class ChmiRadarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_LATITUDE]}_{user_input[CONF_LONGITUDE]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input.get(CONF_NAME, NAME), data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=NAME): str,
            vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): float,
            vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): float,
            vol.Required(CONF_RADIUS_KM, default=DEFAULT_RADIUS_KM): vol.Coerce(float),
            vol.Required(CONF_RAIN_THRESHOLD, default=DEFAULT_RAIN_THRESHOLD): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
            vol.Required(CONF_MAX_FORECAST_MINUTES, default=DEFAULT_MAX_FORECAST_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=120, max=3600)),
            vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
            vol.Optional(CONF_MIN_LON, default=DEFAULT_MIN_LON): vol.Coerce(float),
            vol.Optional(CONF_MAX_LON, default=DEFAULT_MAX_LON): vol.Coerce(float),
            vol.Optional(CONF_MIN_LAT, default=DEFAULT_MIN_LAT): vol.Coerce(float),
            vol.Optional(CONF_MAX_LAT, default=DEFAULT_MAX_LAT): vol.Coerce(float),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
