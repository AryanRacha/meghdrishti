"""Forecast input acquisition: preprocessed .pt tensors, or a deterministic synthetic scenario."""
import zlib
from dataclasses import dataclass
from datetime import date as Date, timedelta
from typing import Literal

import numpy as np
import torch
from scipy.ndimage import gaussian_filter

from app.core.config import settings
from app.core.grid import LAT_GRID, LON_GRID

DataSource = Literal["processed", "synthetic"]

# Synthetic scenarios cover the training month (monsoon, August 2023)
SYNTHETIC_START = Date(2023, 8, 1)
SYNTHETIC_DAYS = 31

# Historically cloudburst-prone Himalayan points (lat, lon)
CLOUDBURST_HOTSPOTS: list[tuple[float, float]] = [
    (31.71, 77.07),  # Kullu / Mandi, HP
    (30.29, 78.98),  # Rudraprayag, UK
    (30.40, 79.33),  # Chamoli, UK
    (32.10, 76.27),  # Kangra, HP
    (29.58, 80.21),  # Pithoragarh, UK
    (33.24, 75.58),  # Kishtwar, J&K
]


@dataclass(frozen=True)
class ModelFields:
    rain: np.ndarray  # mm
    temp: np.ndarray  # K
    wind: np.ndarray  # m/s magnitude


@dataclass(frozen=True)
class ForecastInputs:
    gfs: ModelFields
    ai: ModelFields
    dem: np.ndarray  # m
    source: DataSource


def available_dates() -> list[str]:
    processed_dir = settings.PROCESSED_DATA_DIR
    if processed_dir.is_dir():
        dates = sorted(p.stem for p in processed_dir.glob("*.pt"))
        if dates:
            return dates
    return [(SYNTHETIC_START + timedelta(days=i)).isoformat() for i in range(SYNTHETIC_DAYS)]


def load_inputs(date: str, lead_time: int) -> ForecastInputs:
    path = settings.PROCESSED_DATA_DIR / f"{date}.pt"
    if path.is_file():
        return _load_processed(path)
    return _synthesize(date, lead_time)


def _load_processed(path) -> ForecastInputs:
    data = torch.load(path, map_location="cpu", weights_only=True)

    def fields(key: str) -> ModelFields:
        rain, temp, wind = (t.numpy().astype(np.float32) for t in data[key])
        return ModelFields(rain=rain, temp=temp, wind=wind)

    return ForecastInputs(
        gfs=fields("gfs"),
        ai=fields("ai"),
        dem=data["dem"].numpy().astype(np.float32),
        source="processed",
    )


# --------------------------------------------------------------------------- synthetic


def _seed(*parts: object) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode())


def _gauss(lat0: float, lon0: float, sig_lat: float, sig_lon: float, amp: float) -> np.ndarray:
    return amp * np.exp(-(((LAT_GRID - lat0) / sig_lat) ** 2 + ((LON_GRID - lon0) / sig_lon) ** 2) / 2)


def _smooth_noise(rng: np.random.Generator, sigma: float) -> np.ndarray:
    field = gaussian_filter(rng.normal(size=LAT_GRID.shape), sigma)
    return field / (field.std() + 1e-8)


def _synthetic_dem() -> np.ndarray:
    himalaya = [(35.5, 73.0), (34.0, 75.5), (32.5, 77.0), (30.8, 79.3), (29.0, 82.5),
                (28.2, 85.5), (27.9, 88.0), (27.8, 91.0), (28.4, 94.5)]
    ghats = [(21.0, 73.9), (18.5, 73.8), (16.0, 74.1), (13.5, 75.3), (11.0, 76.6), (9.0, 77.2)]
    dem = np.full(LAT_GRID.shape, 300.0)
    dem += _gauss(33.5, 87.0, 2.6, 8.0, 4200.0)  # Tibetan plateau
    dem += sum(_gauss(lat, lon, 0.9, 1.4, 2500.0) for lat, lon in himalaya)
    dem += sum(_gauss(lat, lon, 1.0, 0.35, 900.0) for lat, lon in ghats)
    dem += _gauss(25.5, 91.5, 0.5, 1.2, 1300.0)  # Khasi hills
    return dem.astype(np.float32)


def _synthesize(date: str, lead_time: int) -> ForecastInputs:
    scenario = np.random.default_rng(_seed("scenario", date))
    forecast = np.random.default_rng(_seed("forecast", date, lead_time))
    degradation = max(lead_time, 24) / 24.0  # 1.0 at day 1, 5.0 at day 5

    dem = _synthetic_dem()
    jitter = lambda s: scenario.normal(0.0, s)  # noqa: E731

    # --- Truth rain (mm/day) ---
    base = (
        _gauss(22.5 + jitter(1.0), 81.0 + jitter(2.0), 2.5, 6.0, 30.0)  # monsoon trough
        + _gauss(25.3, 91.7, 0.5, 0.8, 95.0 + jitter(20))  # Meghalaya
        + _gauss(26.6 + jitter(0.5), 93.5, 0.8, 1.4, 45.0)  # Assam
        + _gauss(19.0 + jitter(1.5), 88.0 + jitter(1.5), 1.6, 2.0, 42.0)  # Bay of Bengal low
        + sum(_gauss(lat, lon - 0.5, 1.2, 0.5, 70.0) for lat, lon in
              [(18.5, 73.8), (16.0, 74.1), (13.5, 75.3), (11.0, 76.6)])  # Ghats orographic
        + 12.0 * _smooth_noise(scenario, 6.0)
    )
    n_bursts = int(scenario.integers(1, 3))
    picks = scenario.choice(len(CLOUDBURST_HOTSPOTS), size=n_bursts, replace=False)
    bursts = sum(
        _gauss(*CLOUDBURST_HOTSPOTS[i], 0.28, 0.28, float(scenario.uniform(180, 260))) for i in picks
    )
    truth_rain = np.clip(base + bursts, 0.0, None)

    # --- Truth temperature (K) and wind (m/s) ---
    truth_temp = (
        303.0 - 0.35 * np.clip(LAT_GRID - 24.0, 0, None) - 0.0065 * dem - 0.04 * truth_rain
        + 0.8 * _smooth_noise(scenario, 5.0)
    )
    truth_wind = np.clip(
        4.0 + _gauss(13.0, 70.0, 3.0, 5.0, 11.0) + _gauss(18.0, 88.0, 2.5, 3.0, 7.0)
        - 0.0006 * dem + 1.2 * _smooth_noise(scenario, 5.0),
        0.3, None,
    )

    noise = lambda amp, sigma=3.0: amp * degradation * _smooth_noise(forecast, sigma)  # noqa: E731

    # GFS proxy: resolves convective extremes but with position error and a wet large-scale bias
    shift = int(forecast.integers(0, 2)) * int(degradation)
    gfs_rain = 1.15 * gaussian_filter(base, 1.0) + 0.85 * np.roll(bursts, (shift, -shift), axis=(0, 1)) + noise(4.0)
    gfs_temp = truth_temp - 0.0008 * dem + noise(0.6)
    gfs_wind = truth_wind * 1.1 + noise(0.8)

    # AI proxy: ERA5-like clone with spatial blur + Gaussian noise (see MODEL.md section 2)
    blur = 1.5 + 0.5 * degradation
    ai_rain = gaussian_filter(truth_rain, blur) + noise(5.0, 2.0)
    ai_temp = gaussian_filter(truth_temp, blur) + noise(0.4, 2.0)
    ai_wind = gaussian_filter(truth_wind, blur) + noise(0.6, 2.0)

    def pack(rain: np.ndarray, temp: np.ndarray, wind: np.ndarray) -> ModelFields:
        return ModelFields(
            rain=np.clip(rain, 0.0, None).astype(np.float32),
            temp=temp.astype(np.float32),
            wind=np.clip(wind, 0.0, None).astype(np.float32),
        )

    return ForecastInputs(
        gfs=pack(gfs_rain, gfs_temp, gfs_wind),
        ai=pack(ai_rain, ai_temp, ai_wind),
        dem=dem,
        source="synthetic",
    )
