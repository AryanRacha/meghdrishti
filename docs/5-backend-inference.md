# 5 - Backend Inference API

## Objective
Build the FastAPI inference endpoints (Phase 3B) to serve the trained Super-UNet model to the frontend. The backend loads the PyTorch weights, ingests forecast grids, runs the blending inference, and outputs GeoJSON for the Leaflet maps.

## Verified Model Contract (from `ml_pipeline/train.py`)
The class docstring in `unet_blender.py` still describes an older 19-channel / 6-model variant. The trained checkpoint uses:

| Item | Value |
|---|---|
| Constructor | `SuperUNetBlender(n_channels=7, n_models=2, features=[32, 64, 128, 256])` |
| Input `x` | `[B, 7, 128, 128]` — GFS rain/temp/wind, AI rain/temp/wind, DEM |
| Input normalization | Per-sample, per-channel z-score: `(t - t.mean()) / (t.std() + 1e-8)` |
| Input `lead_time` | `[B, 1]`, raw hours (training only ever used `24.0`) |
| Output | 3 tensors (rain, temp, wind), each `[B, 2, 128, 128]`, softmax over dim 1 |
| Weight channel 0 / 1 | GFS trust / AI trust |
| Blend | `blended = w[0] * gfs + w[1] * ai` (raw physical units) |
| Grid orientation | Row 0 = 38°N (north), last row = 8°N; column 0 = 68°E, last column = 98°E |
| Units | Rain mm, Temp K (API converts to °C), Wind m/s |

**Lead times other than 24 h are out-of-distribution.** The API serves them but flags `lead_time_validated: false`.

## Architecture & Flow

### 1. Model Inference Flow
- **Input Tensors**: 7-channel grid (`128x128`) — GFS (Rain, Temp, Wind), AI (Rain, Temp, Wind), DEM.
- **Network execution**: `SuperUNetBlender` encodes the grid, applies `lead_time` via FiLM in the bottleneck, and predicts per-pixel trust for each model.
- **Output Weights**: Three independent `[2, 128, 128]` tensors (Rain, Temperature, Wind).
- **Final Blend**: `(GFS_Forecast * GFS_Weight) + (AI_Forecast * AI_Weight) = Blended_Forecast`.

### 2. User & System Flow
1. User opens the dashboard and selects a date, lead time, variable and layer.
2. Frontend calls `GET /api/v1/forecast/grid?...` (map raster) and `GET /api/v1/forecast/alerts?...`. External agencies use `GET /api/v1/forecast/blended` (GeoJSON).
3. **Data acquisition** (`services/data_source.py`):
   - If `ml_pipeline/data/processed/{date}.pt` exists → load it (`data_source: "processed"`).
   - Otherwise → generate a deterministic synthetic scenario (`data_source: "synthetic"`), see below.
4. **Inference** (`services/inference_engine.py`): normalize, stack, run the singleton model, blend. Results are cached per `(date, lead_time)`.
5. **Serialization** (`utils/geojson_converter.py`): grid → GeoJSON polygon cells, with `stride` down-sampling and `min_value` filtering.
6. **Threat detection** (`services/threat_detector.py`): connected regions of blended rain ≥ 64.5 mm, classified by IMD category, mapped to nearest district.

### 3. Synthetic (Mock) Mode
Used when processed tensors are absent. Seeded by `(date, lead_time)`, so identical requests return identical grids.
- **DEM**: Himalayan arc + Tibetan plateau + Western Ghats + Khasi Hills.
- **Truth rain**: monsoon trough, Western Ghats orographic band, NE India, Bay of Bengal, plus 1–2 injected Himalayan cloudburst cells (180–260 mm).
- **GFS proxy**: truth with extremes under-predicted and spatially displaced (topography weakness).
- **AI proxy**: truth blurred + Gaussian noise (same method as the project's synthetic GraphCast generator).
- Forecast degradation (blur/noise) grows with lead time.

Every response carries `data_source` and `weights` (`"trained"` / `"untrained"`) so demos are never misleading.

### 4. Weights
- Path: `backend/weights/super_unet_blender_weights.pth` (override with `WEIGHTS_PATH` env var). `*.pth` is git-ignored.
- If missing, the engine starts with random weights and reports `weights: "untrained"`.

## API Contract

| Endpoint | Description |
|---|---|
| `GET /health` | API status, model loaded, weights mode, device |
| `GET /api/v1/forecast/meta` | Available dates, lead times, variables, layers, units |
| `GET /api/v1/forecast/blended` | GeoJSON FeatureCollection for one layer (interoperability) |
| `GET /api/v1/forecast/grid` | Full 128×128 grid as a flat row-major array (row 0 = north), ~28 KB gzipped; used by the dashboard |
| `GET /api/v1/forecast/alerts` | Ranked extreme-rain threats (Threat Matrix) |

### `/blended` query parameters
| Param | Default | Values |
|---|---|---|
| `date` | latest available | `YYYY-MM-DD` |
| `lead_time` | `24` | `24`–`120` hours |
| `variable` | `rain` | `rain`, `temp`, `wind` |
| `layer` | `blended` | `blended`, `gfs`, `ai`, `trust` (GFS weight 0–1 = XAI Trust Map) |
| `stride` | `2` | `1`–`8`; block down-sampling (rain uses block max to preserve extremes, others mean) |
| `min_value` | none | drop cells below this value |

Response: GeoJSON `FeatureCollection`, each feature a cell `Polygon` with `properties.v`, plus a foreign member `metadata` (`min`, `max`, `units`, `data_source`, `weights`, `lead_time_validated`, `cell_count`).

### `/grid` response
`{ metadata, lat_north, lat_south, lon_west, lon_east, rows, cols, values: number[] }`. Same `date`, `lead_time`, `variable`, `layer` parameters as `/blended`; temperature in °C.

### `/alerts` response
`{ metadata, threats: [{ id, district, state, distance_km, lat, lon, peak_mm, mean_mm, area_km2, category, severity_rank, gfs_mm, ai_mm, gfs_trust, population_exposed, risk_index }] }`

- `population_exposed`: sum over affected grid cells of (Census 2011 state density of the nearest district × cell area). Cells > 70 km from every district HQ count as outside India / sea (`app/data/state_density.json`).
- `risk_index` (0–100): 60% rainfall intensity (saturates at 1.5 × 204.5 mm) + 40% exposure (log10 scale, 1 crore = max).

IMD 24 h rainfall categories: Heavy 64.5–115.5 mm, Very Heavy 115.6–204.4 mm, Extremely Heavy ≥ 204.5 mm.

## File Layout
```
backend/app/
  main.py                       # app + lifespan model load + router
  core/config.py                # settings (paths, bbox, device)
  ml/unet_blender.py            # vendored SuperUNetBlender (keep in sync with ml_pipeline)
  services/data_source.py       # processed .pt loader + synthetic generator
  services/inference_engine.py  # singleton model + blend + cache
  services/threat_detector.py   # IMD extreme-rain detection
  utils/geojson_converter.py    # grid -> GeoJSON
  schemas/forecast.py           # pydantic response models
  api/forecast.py               # router
  data/districts.json           # district HQ gazetteer
backend/tests/                  # pytest
```

## Running
```bash
cd backend
uv sync
uv run dev       # Development server with auto-reload (port 8000)
# uv run start   # Production server
# uv run pytest  # Pytest test suite

# Without uv:
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows; use .venv/bin/pip on Linux
.venv/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
.venv/Scripts/python -m pytest
```

## Cloud Deployment (Render Free Tier)

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Build Command** | `pip install uv && uv sync --no-dev` (or pip CPU torch command) |
| **Start Command** | `uv run start` |
| **Environment Variables** | `DEVICE=cpu`, `PYTHON_VERSION=3.11.0` |

*Note*: `app.main:start` automatically binds to `$PORT` provided by Render and runs with 1 worker to stay well within Render Free Tier's 512MB RAM cap.

