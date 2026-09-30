"""Detect extreme-rain regions in the blended forecast and classify them by IMD category."""
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.ndimage import label

from app.core.grid import LAT_GRID, LAT_STEP, LON_GRID, LON_STEP
from app.schemas.forecast import ImdCategory, Threat
from app.services.inference_engine import BlendResult

# IMD 24 h rainfall categories (mm)
HEAVY_MM = 64.5
VERY_HEAVY_MM = 115.6
EXTREMELY_HEAVY_MM = 204.5

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


def risk_index(peak_mm: float, people: float) -> int:
    """0-100: 60% rainfall intensity (saturating at 1.5x extremely-heavy), 40% exposure (log scale, 10M = max)."""
    intensity = min(peak_mm / (1.5 * EXTREMELY_HEAVY_MM), 1.0)
    exposure = min(math.log10(people + 1) / 7.0, 1.0)
    return round(100 * (0.6 * intensity + 0.4 * exposure))


def nearest_district(lat: float, lon: float) -> tuple[dict, float]:
    return min(
        ((d, _haversine_km(lat, lon, d["lat"], d["lon"])) for d in _districts()),
        key=lambda pair: pair[1],
    )


def imd_category(mm: float) -> ImdCategory:
    if mm >= EXTREMELY_HEAVY_MM:
        return "extremely_heavy"
    if mm >= VERY_HEAVY_MM:
        return "very_heavy"
    return "heavy"


def detect_threats(result: BlendResult, threshold_mm: float = HEAVY_MM, limit: int = 20) -> list[Threat]:
    rain = result.blended.rain
    labels, count = label(rain >= threshold_mm, structure=np.ones((3, 3)))

    cell_area_km2 = _cell_area_km2()
    exposure = _exposure_grid()

    regions = []
    for region_id in range(1, count + 1):
        mask = labels == region_id
        masked = np.where(mask, rain, -np.inf)
        i, j = np.unravel_index(int(np.argmax(masked)), rain.shape)
        regions.append((float(rain[i, j]), mask, int(i), int(j)))

    regions.sort(key=lambda r: r[0], reverse=True)

    threats: list[Threat] = []
    for rank, (peak, mask, i, j) in enumerate(regions[:limit], start=1):
        lat, lon = float(LAT_GRID[i, j]), float(LON_GRID[i, j])
        district, distance = nearest_district(lat, lon)
        people = float(exposure[mask].sum())
        threats.append(Threat(
            id=f"{result.date}-{result.lead_time}-{rank}",
            district=district["district"],
            state=district["state"],
            distance_km=round(distance, 1),
            lat=round(lat, 3),
            lon=round(lon, 3),
            peak_mm=round(peak, 1),
            mean_mm=round(float(rain[mask].mean()), 1),
            area_km2=round(float(cell_area_km2[mask].sum()), 0),
            category=imd_category(peak),
            severity_rank=rank,
            gfs_mm=round(float(result.gfs.rain[i, j]), 1),
            ai_mm=round(float(result.ai.rain[i, j]), 1),
            gfs_trust=round(float(result.trust.rain[i, j]), 3),
            population_exposed=int(round(people, -2)),
            risk_index=risk_index(peak, people),
        ))
    return threats
