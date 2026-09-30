# 5 - Backend Inference API

## Objective
Build the FastAPI inference endpoints (Phase 3B) to serve the trained Super-UNet model to the frontend. The backend will load the PyTorch weights, ingest real-time forecast data, run the blending inference, and output GeoJSON arrays for the Leaflet maps.

## Architecture & Flow

### 1. Model Inference Flow (What happens under the hood)
- **Input Tensors**: A 7-channel grid (`128x128`) containing GFS (Rain, Temp, Wind), AI (Rain, Temp, Wind), and DEM (Topography).
- **Network execution**: The `SuperUNetBlender` evaluates the geographical features, applies the `lead_time` via the FiLM layer in the bottleneck, and predicts the trust percentage (0.0 to 1.0) for each model.
- **Output Weights**: Three independent `[2, 128, 128]` tensors representing the GFS/AI blending weights for Rain, Temperature, and Wind.
- **Final Blend**: `(GFS_Forecast * GFS_Weight) + (AI_Forecast * AI_Weight) = Blended_Forecast`.

### 2. User & System Flow (Frontend to Backend)
1. **User Request**: User opens the React frontend and requests the forecast for "Tomorrow (Day 1)".
2. **API Call**: Frontend sends a `GET /api/v1/forecast/blended?lead_time=24` request to the FastAPI server.
3. **Data Acquisition**: 
   - Backend checks if today's GFS and GraphCast `.nc`/`.grib2` grids are already cached locally. If not, it downloads them using the existing fetchers.
4. **Inference Execution**:
   - The arrays are normalized and stacked into the 7-channel PyTorch tensor.
   - The tensor and `lead_time=24` are passed through the pre-loaded `super_unet_blender_weights.pth` model.
   - The raw output tensors (Rain, Temp, Wind) are mathematically produced.
5. **Serialization**:
   - The tensors are mapped back to latitude/longitude coordinates (8 to 38 Lat, 68 to 98 Lon).
   - The grids are converted into valid GeoJSON polygon features.
6. **Frontend Rendering**:
   - The GeoJSON is returned to the React frontend.
   - Leaflet.js renders a color-coded heat map over India.
   - A sidebar flags specific districts where the U-Net detected "Extreme Events" (e.g., Cloudbursts).

## Implementation Steps
1. Create `backend/app/api/forecast.py` to house the router endpoint.
2. Create an inference service in `backend/app/services/inference_engine.py` to load the `.pth` model into memory (using a Singleton pattern to prevent reloading).
3. Build a serializer in `backend/app/utils/geojson_converter.py` to convert PyTorch/Numpy 2D arrays into GeoJSON format.
4. Attach the router to `backend/app/main.py`.
