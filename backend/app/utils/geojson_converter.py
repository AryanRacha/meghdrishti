"""Convert 2D model grids into GeoJSON cell polygons for Leaflet."""
from typing import Any, Literal

import numpy as np

from app.core.grid import LAT_STEP, LATS, LON_STEP, LONS

Aggregation = Literal["mean", "max"]


def downsample(grid: np.ndarray, stride: int, how: Aggregation) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Block-aggregate a grid. Returns (values, block_center_lats, block_center_lons)."""
    if stride == 1:
        return grid, LATS, LONS
    rows, cols = grid.shape[0] // stride, grid.shape[1] // stride
    blocks = grid[: rows * stride, : cols * stride].reshape(rows, stride, cols, stride)
    values = blocks.max(axis=(1, 3)) if how == "max" else blocks.mean(axis=(1, 3))
    lats = LATS[: rows * stride].reshape(rows, stride).mean(axis=1)
    lons = LONS[: cols * stride].reshape(cols, stride).mean(axis=1)
    return values, lats, lons


def grid_to_geojson(
    grid: np.ndarray,
    stride: int = 1,
    how: Aggregation = "mean",
    min_value: float | None = None,
    decimals: int = 2,
) -> dict[str, Any]:
    """Each grid cell becomes a Polygon centred on its coordinate, with properties {"v": value}."""
    values, lats, lons = downsample(grid, stride, how)
    half_lat, half_lon = LAT_STEP * stride / 2, LON_STEP * stride / 2

    features: list[dict[str, Any]] = []
    for i, lat in enumerate(lats):
        n, s = round(float(lat + half_lat), 4), round(float(lat - half_lat), 4)
        for j, lon in enumerate(lons):
            v = float(values[i, j])
            if not np.isfinite(v) or (min_value is not None and v < min_value):
                continue
            w, e = round(float(lon - half_lon), 4), round(float(lon + half_lon), 4)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]]},
                "properties": {"v": round(v, decimals)},
            })

    return {"type": "FeatureCollection", "features": features}
