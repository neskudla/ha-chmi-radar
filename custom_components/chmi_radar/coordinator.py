from __future__ import annotations

import asyncio
import io
import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import cv2
import numpy as np
from PIL import Image

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import *

_LOGGER = logging.getLogger(__name__)
PNG_RE = re.compile(r'href="([^"]+\.png)"', re.IGNORECASE)
TIME_RE = re.compile(r"(\d{12,14})")

@dataclass
class RadarData:
    url: str | None
    image_time: str | None
    pixel_x: int | None
    pixel_y: int | None
    raining_now: bool | None
    rain_incoming: bool | None
    rain_eta_minutes: int | None
    last_update: str | None
    intensity: int | None
    max_intensity_nearby: int | None
    motion_confidence: float | None
    image_width: int | None
    image_height: int | None
    forecast_available: bool
    forecast_note: str | None = None

class ChmiRadarCoordinator(DataUpdateCoordinator[RadarData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.session = async_get_clientsession(hass)
        self.latitude = float(entry.data[CONF_LATITUDE])
        self.longitude = float(entry.data[CONF_LONGITUDE])
        self.radius_km = float(entry.data[CONF_RADIUS_KM])
        self.threshold = int(entry.data[CONF_RAIN_THRESHOLD])
        self.max_forecast_minutes = int(entry.data[CONF_MAX_FORECAST_MINUTES])
        self.base_url = str(entry.data[CONF_BASE_URL])
        self.min_lon = float(entry.data[CONF_MIN_LON])
        self.max_lon = float(entry.data[CONF_MAX_LON])
        self.min_lat = float(entry.data[CONF_MIN_LAT])
        self.max_lat = float(entry.data[CONF_MAX_LAT])
        self._previous_gray: np.ndarray | None = None
        self._previous_url: str | None = None
        interval = int(entry.data[CONF_SCAN_INTERVAL])
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=interval))

    async def _async_update_data(self) -> RadarData:
        try:
            latest_url = await self._get_latest_png_url()
            img_bytes = await self._download(latest_url)
            return await asyncio.get_running_loop().run_in_executor(None, self._process_image, latest_url, img_bytes)
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    async def _get_latest_png_url(self) -> str:
        async with self.session.get(self.base_url, timeout=30) as resp:
            resp.raise_for_status()
            html = await resp.text()
        files = PNG_RE.findall(html)
        if not files:
            raise RuntimeError("V adresáři ČHMÚ nebyl nalezen žádný PNG soubor")
        latest = sorted(files)[-1]
        return self.base_url.rstrip("/") + "/" + latest

    async def _download(self, url: str) -> bytes:
        async with self.session.get(url, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.read()

    def _process_image(self, url: str, img_bytes: bytes) -> RadarData:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        width, height = img.size
        x, y = self._latlon_to_pixel(width, height)
        radius_px = max(1, int(self._km_to_pixels(width, height, self.radius_km)))

        arr = np.array(img)
        intensity_map = self._make_intensity_map(arr)
        gray = intensity_map.astype(np.uint8)
        rain_mask = intensity_map >= self.threshold

        intensity = int(intensity_map[y, x])
        max_nearby = int(self._max_in_radius(intensity_map, x, y, radius_px))
        raining_now = bool(max_nearby >= self.threshold)

        forecast_available = False
        forecast_note = "Odhad bude dostupný po druhém načteném radarovém snímku."
        rain_incoming: bool | None = None
        rain_eta: int | None = None
        confidence: float | None = None

        if self._previous_gray is not None and self._previous_url != url and self._previous_gray.shape == gray.shape:
            forecast_available = True
            rain_incoming, rain_eta, confidence, forecast_note = self._estimate_incoming_rain(
                self._previous_gray, gray, rain_mask, x, y, radius_px
            )

        self._previous_gray = gray
        self._previous_url = url

        return RadarData(
            url=url,
            image_time=self._parse_image_time(url),
            pixel_x=x,
            pixel_y=y,
            raining_now=raining_now,
            rain_incoming=rain_incoming if not raining_now else False,
            rain_eta_minutes=0 if raining_now else rain_eta,
            last_update=datetime.now().isoformat(timespec="seconds"),
            intensity=intensity,
            max_intensity_nearby=max_nearby,
            motion_confidence=confidence,
            image_width=width,
            image_height=height,
            forecast_available=forecast_available,
            forecast_note=forecast_note,
        )

    def _make_intensity_map(self, rgba: np.ndarray) -> np.ndarray:
        rgb_max = rgba[:, :, :3].max(axis=2)
        alpha = rgba[:, :, 3]
        return np.where(alpha > 0, rgb_max, 0).astype(np.uint8)

    def _estimate_incoming_rain(
        self,
        previous_gray: np.ndarray,
        current_gray: np.ndarray,
        current_rain_mask: np.ndarray,
        home_x: int,
        home_y: int,
        radius_px: int,
    ) -> tuple[bool, int | None, float, str | None]:
        flow = cv2.calcOpticalFlowFarneback(
            previous_gray,
            current_gray,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=21,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )

        ys, xs = np.where(current_rain_mask)
        if len(xs) < 20:
            return False, None, 0.0, "Na aktuálním snímku je příliš málo srážkových pixelů pro výpočet pohybu."

        # Kvůli rychlosti pracujeme se vzorkem srážkových pixelů.
        max_points = 6000
        if len(xs) > max_points:
            idx = np.linspace(0, len(xs) - 1, max_points).astype(int)
            xs = xs[idx]
            ys = ys[idx]

        vectors = flow[ys, xs]
        magnitudes = np.linalg.norm(vectors, axis=1)
        moving = magnitudes > 0.15
        confidence = float(round(min(1.0, moving.sum() / max(1, len(magnitudes))), 3))

        if moving.sum() < 10:
            return False, None, confidence, "OpenCV nenašlo dostatečně výrazný pohyb srážek."

        for minutes in range(5, self.max_forecast_minutes + 1, 5):
            factor = minutes / 5.0
            pred_x = xs + vectors[:, 0] * factor
            pred_y = ys + vectors[:, 1] * factor
            dist2 = (pred_x - home_x) ** 2 + (pred_y - home_y) ** 2
            if np.any(dist2 <= radius_px ** 2):
                return True, minutes, confidence, None

        return False, None, confidence, None

    def _latlon_to_pixel(self, width: int, height: int) -> tuple[int, int]:
        lon_ratio = (self.longitude - self.min_lon) / (self.max_lon - self.min_lon)
        lat_ratio = (self.max_lat - self.latitude) / (self.max_lat - self.min_lat)
        x = min(width - 1, max(0, round(lon_ratio * (width - 1))))
        y = min(height - 1, max(0, round(lat_ratio * (height - 1))))
        return x, y

    def _km_to_pixels(self, width: int, height: int, km: float) -> float:
        mid_lat = math.radians(self.latitude)
        km_per_lon = 111.320 * math.cos(mid_lat)
        km_per_lat = 110.574
        px_per_km_x = width / ((self.max_lon - self.min_lon) * km_per_lon)
        px_per_km_y = height / ((self.max_lat - self.min_lat) * km_per_lat)
        return km * ((px_per_km_x + px_per_km_y) / 2)

    def _max_in_radius(self, intensity_map: np.ndarray, cx: int, cy: int, radius: int) -> int:
        h, w = intensity_map.shape
        y0, y1 = max(0, cy - radius), min(h, cy + radius + 1)
        x0, x1 = max(0, cx - radius), min(w, cx + radius + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        values = intensity_map[y0:y1, x0:x1][mask]
        return int(values.max()) if values.size else 0

    def _parse_image_time(self, url: str) -> str | None:
        match = TIME_RE.search(url)
        if not match:
            return None
        raw = match.group(1)
        fmt = "%Y%m%d%H%M%S" if len(raw) == 14 else "%Y%m%d%H%M"
        try:
            return datetime.strptime(raw, fmt).isoformat(timespec="minutes")
        except ValueError:
            return raw
