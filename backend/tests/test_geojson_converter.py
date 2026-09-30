import numpy as np

from app.core.grid import LATS, LONS
from app.utils.geojson_converter import grid_to_geojson


def _bounds(feature: dict) -> tuple[float, float, float, float]:
    ring = feature["geometry"]["coordinates"][0]
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return min(lats), min(lons), max(lats), max(lons)


def test_first_feature_is_north_west_corner() -> None:
    grid = np.zeros((128, 128), dtype=np.float32)
    grid[0, 0] = 42.0
    fc = grid_to_geojson(grid)
    s, w, n, e = _bounds(fc["features"][0])
    assert fc["features"][0]["properties"]["v"] == 42.0
    assert s < LATS[0] < n and abs(n - 38.0) < 0.2
    assert w < LONS[0] < e and abs(w - 68.0) < 0.2


def test_stride_reduces_cell_count_and_max_preserves_peak() -> None:
    grid = np.zeros((128, 128), dtype=np.float32)
    grid[10, 10] = 250.0
    fc = grid_to_geojson(grid, stride=4, how="max")
    assert len(fc["features"]) == 32 * 32
    assert max(f["properties"]["v"] for f in fc["features"]) == 250.0


def test_min_value_filters_cells() -> None:
    grid = np.zeros((128, 128), dtype=np.float32)
    grid[5:7, 5:7] = 10.0
    fc = grid_to_geojson(grid, min_value=1.0)
    assert len(fc["features"]) == 4


def test_polygons_are_closed_rings() -> None:
    fc = grid_to_geojson(np.ones((128, 128), dtype=np.float32), stride=8)
    ring = fc["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1] and len(ring) == 5
