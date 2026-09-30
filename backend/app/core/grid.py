"""Model grid coordinates. Row 0 is the northern edge, matching ml_pipeline/preprocess.py."""
import numpy as np

from app.core.config import settings

LATS: np.ndarray = np.linspace(settings.LAT_NORTH, settings.LAT_SOUTH, settings.GRID_SIZE)
LONS: np.ndarray = np.linspace(settings.LON_WEST, settings.LON_EAST, settings.GRID_SIZE)
LAT_STEP: float = abs(float(LATS[1] - LATS[0]))
LON_STEP: float = abs(float(LONS[1] - LONS[0]))

# 2D coordinate meshes, shape [GRID_SIZE, GRID_SIZE]
LON_GRID, LAT_GRID = np.meshgrid(LONS, LATS)
