"""Detect extreme-weather regions (rain, wind, heat) in the blended forecast and grade them."""
import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.ndimage import label

from app.core.grid import LAT_GRID, LAT_STEP, LON_GRID, LON_STEP
from app.schemas.forecast import ThreatCategory, Threat, Variable
from app.services.inference_engine import BlendResult

# IMD 24 h rainfall categories (mm)
HEAVY_MM = 64.5
VERY_HEAVY_MM = 115.6
EXTREMELY_HEAVY_MM = 204.5

# IMD surface-wind scale (km/h): strong / gale / storm-force
STRONG_WIND_KMH = 40.0
GALE_KMH = 62.0
STORM_KMH = 89.0

# Heat: IMD heatwave levels (°C), plus a relative "heat watch" for the hottest land of the day.
# The temperature field is a single 2 m snapshot, not daily Tmax, so absolute IMD
# thresholds rarely trigger; the watch flags the hottest HEAT_WATCH_PERCENTILE of land.
HEAT_WATCH_FLOOR_C = 28.0
HEAT_WATCH_PERCENTILE = 98.0
HEATWAVE_C = 40.0
SEVERE_HEATWAVE_C = 45.0
KELVIN_OFFSET = 273.15
MS_TO_KMH = 3.6

KM_PER_DEG = 111.32
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DISTRICTS_PATH = DATA_DIR / "districts.json"
DENSITY_PATH = DATA_DIR / "state_density.json"

# Cells farther than this from every district HQ are treated as outside India / sea
LAND_RADIUS_KM = 70.0


@lru_cache(maxsize=1)
def _districts() -> list[dict]:
    return json.loads(DISTRICTS_PATH.read_text(encoding="utf-8"))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


@lru_cache(maxsize=1)
def _exposure_grid() -> np.ndarray:
    """Persons per grid cell: state density (Census 2011) of the nearest district x cell area."""
    districts = _districts()
    density = json.loads(DENSITY_PATH.read_text(encoding="utf-8"))
    d_lat = np.radians([d["lat"] for d in districts])[:, None, None]
    d_lon = np.radians([d["lon"] for d in districts])[:, None, None]
    lat, lon = np.radians(LAT_GRID)[None], np.radians(LON_GRID)[None]
    a = np.sin((lat - d_lat) / 2) ** 2 + np.cos(lat) * np.cos(d_lat) * np.sin((lon - d_lon) / 2) ** 2
    dist_km = 2 * 6371.0 * np.arcsin(np.sqrt(a))  # [districts, rows, cols]

    nearest = dist_km.argmin(axis=0)
    state_density = np.array([density.get(d["state"], 0) for d in districts], dtype=np.float64)[nearest]
    on_land = dist_km.min(axis=0) <= LAND_RADIUS_KM
    return np.where(on_land, state_density * _cell_area_km2(), 0.0)


def _cell_area_km2() -> np.ndarray:
    return (LAT_STEP * KM_PER_DEG) * (LON_STEP * KM_PER_DEG) * np.cos(np.radians(LAT_GRID))


def risk_index(intensity: float, people: float) -> int:
    """0-100: 60% hazard intensity (0-1, hazard-specific scale), 40% exposure (log scale, 10M = max)."""
    exposure = min(math.log10(people + 1) / 7.0, 1.0)
    return round(100 * (0.6 * min(max(intensity, 0.0), 1.0) + 0.4 * exposure))


def nearest_district(lat: float, lon: float) -> tuple[dict, float]:
    return min(
        ((d, _haversine_km(lat, lon, d["lat"], d["lon"])) for d in _districts()),
        key=lambda pair: pair[1],
    )


@dataclass(frozen=True)
class HazardSpec:
    units: str
    convert: Callable[[np.ndarray], np.ndarray]  # model units -> display units
    levels: tuple[tuple[float, ThreatCategory], ...]  # ascending (threshold, category)
    intensity: Callable[[float], float]  # peak -> 0-1 for the risk index
    land_only: bool  # wind and heat over the open sea are not public threats


HAZARDS: dict[Variable, HazardSpec] = {
    "rain": HazardSpec(
        units="mm",
        convert=lambda g: g,
        levels=((HEAVY_MM, "heavy"), (VERY_HEAVY_MM, "very_heavy"), (EXTREMELY_HEAVY_MM, "extremely_heavy")),
        intensity=lambda peak: peak / (1.5 * EXTREMELY_HEAVY_MM),
        land_only=False,
    ),
    "wind": HazardSpec(
        units="km/h",
        convert=lambda g: g * MS_TO_KMH,
        levels=((STRONG_WIND_KMH, "strong_wind"), (GALE_KMH, "gale"), (STORM_KMH, "storm")),
        intensity=lambda peak: (peak - STRONG_WIND_KMH) / (1.25 * STORM_KMH - STRONG_WIND_KMH),
        land_only=True,
    ),
    "temp": HazardSpec(
        units="°C",
        convert=lambda g: g - KELVIN_OFFSET,
        levels=((HEAT_WATCH_FLOOR_C, "heat_watch"), (HEATWAVE_C, "heatwave"), (SEVERE_HEATWAVE_C, "severe_heatwave")),
        intensity=lambda peak: (peak - HEAT_WATCH_FLOOR_C) / (SEVERE_HEATWAVE_C + 2.0 - HEAT_WATCH_FLOOR_C),
        land_only=True,
    ),
}


def grade(spec: HazardSpec, peak: float) -> tuple[ThreatCategory, int]:
    """Highest category whose threshold the peak reaches, and its 1-based level."""
    level = max(i for i, (threshold, _) in enumerate(spec.levels) if i == 0 or peak >= threshold)
    return spec.levels[level][1], level + 1


def imd_category(mm: float) -> ThreatCategory:
    return grade(HAZARDS["rain"], mm)[0]


def detection_threshold(variable: Variable, field: np.ndarray, land: np.ndarray) -> float:
    spec = HAZARDS[variable]
    base = spec.levels[0][0]
    if variable != "temp" or not land.any():
        return base
    # Relative heat watch, capped so official heatwaves are always detected
    return min(max(base, float(np.percentile(field[land], HEAT_WATCH_PERCENTILE))), HEATWAVE_C)


def detect_threats(result: BlendResult, variable: Variable = "rain", limit: int = 20) -> list[Threat]:
    spec = HAZARDS[variable]
    field = spec.convert(getattr(result.blended, variable))
    exposure = _exposure_grid()
    land = exposure > 0

    candidate = field >= detection_threshold(variable, field, land)
    if spec.land_only:
        candidate &= land
    labels, count = label(candidate, structure=np.ones((3, 3)))

    cell_area_km2 = _cell_area_km2()
    regions = []
    for region_id in range(1, count + 1):
        mask = labels == region_id
        masked = np.where(mask, field, -np.inf)
        i, j = np.unravel_index(int(np.argmax(masked)), field.shape)
        regions.append((float(field[i, j]), mask, int(i), int(j)))

    regions.sort(key=lambda r: r[0], reverse=True)

    gfs = spec.convert(getattr(result.gfs, variable))
    ai = spec.convert(getattr(result.ai, variable))
    trust = getattr(result.trust, variable)

    threats: list[Threat] = []
    for rank, (peak, mask, i, j) in enumerate(regions[:limit], start=1):
        lat, lon = float(LAT_GRID[i, j]), float(LON_GRID[i, j])
        district, distance = nearest_district(lat, lon)
        people = float(exposure[mask].sum())
        category, level = grade(spec, peak)
        threats.append(Threat(
            id=f"{result.date}-{result.lead_time}-{variable}-{rank}",
            variable=variable,
            units=spec.units,
            district=district["district"],
            state=district["state"],
            distance_km=round(distance, 1),
            lat=round(lat, 3),
            lon=round(lon, 3),
            peak=round(peak, 1),
            mean=round(float(field[mask].mean()), 1),
            area_km2=round(float(cell_area_km2[mask].sum()), 0),
            category=category,
            level=level,
            severity_rank=rank,
            gfs_value=round(float(gfs[i, j]), 1),
            ai_value=round(float(ai[i, j]), 1),
            gfs_trust=round(float(trust[i, j]), 3),
            population_exposed=int(round(people, -2)),
            risk_index=risk_index(spec.intensity(peak), people),
        ))
    return threats
