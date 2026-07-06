DOMAIN = "chmi_radar"
NAME = "ČHMÚ Radar"
MANUFACTURER = "ČHMÚ OpenData"

DEFAULT_SCAN_INTERVAL = 300
DEFAULT_RADIUS_KM = 2.0
DEFAULT_RAIN_THRESHOLD = 25
DEFAULT_MAX_FORECAST_MINUTES = 60
DEFAULT_BASE_URL = "https://opendata.chmi.cz/meteorology/weather/radar/composite/maxz/png/"

# Přibližný bounding box pro radarový PNG kompozit ČHMÚ.
# Pokud poloha nesedí přesně, lze hranice upravit v nastavení integrace.
DEFAULT_MIN_LON = 11.0
DEFAULT_MAX_LON = 19.2
DEFAULT_MIN_LAT = 48.0
DEFAULT_MAX_LAT = 51.4

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_RADIUS_KM = "radius_km"
CONF_RAIN_THRESHOLD = "rain_threshold"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_BASE_URL = "base_url"
CONF_MIN_LON = "min_lon"
CONF_MAX_LON = "max_lon"
CONF_MIN_LAT = "min_lat"
CONF_MAX_LAT = "max_lat"
CONF_MAX_FORECAST_MINUTES = "max_forecast_minutes"
