# SIH26081: Master Implementation Plan & Architecture Blueprint

## 1. Executive Summary
A Spatial Deep Learning (U-Net) Blending Engine that dynamically learns which forecasting model (GFS vs AI Models) to trust at specific pixels, lead times, and weather regimes. The system explicitly preserves extreme rainfall peaks using a custom loss function.

## 2. Completed Phases (Architecture & ML)
- **Monorepo Setup**: FastAPI backend, React (Vite/TS) frontend, ML pipeline separated.
- **Data Pipeline**: Automated fetchers for GFS (AWS S3), ERA5 (Copernicus CDS), and GraphCast (Synthetic 2023 Generation) implemented.
- **ML Architecture**: Multi-Head Super-UNet with FiLM built in PyTorch (unet_blender.py).
- **The 'Winning Edge'**: ExtremeWeightedMSELoss implemented to heavily penalize missing high-rainfall events, balanced with Z-score normalizers.
- **Training Loop**: Completed. GPU optimized with AMP, `num_workers=0`, and `cfgrib.open_datasets()` list-shattering. `unet_blender_weights.pth` successfully generated.

## 3. Pending Phases (To Execute Next)

### Phase 3B: Backend Inference
1. Build FastAPI endpoints (e.g., GET /api/v1/forecast/blended).
2. Write logic to load the `.pth` weights, run the daily forecast grids through the U-Net, and output GeoJSON arrays.

### Phase 3C: Frontend Dashboard (No GPU Required)
1. Build React UI with Leaflet.js.
2. Create map layers for Base Models and Blended Output.
3. Implement a time slider for forecast lead times (Day 1 to 5).
4. Build the Extreme Weather Alerts sidebar.
