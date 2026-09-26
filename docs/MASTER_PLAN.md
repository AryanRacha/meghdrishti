# SIH26081: Master Implementation Plan & Architecture Blueprint

## 1. Executive Summary
A Spatial Deep Learning (U-Net) Blending Engine that dynamically learns which forecasting model (GFS vs AI Models) to trust at specific pixels, lead times, and weather regimes. The system explicitly preserves extreme rainfall peaks using a custom loss function.

## 2. Completed Phases (Architecture & ML)
- **Monorepo Setup**: FastAPI backend, React (Vite/TS) frontend, ML pipeline separated.
- **Data Pipeline**: Automated fetchers for GFS (AWS S3) and ERA5 (Copernicus CDS) implemented with xarray regridding.
- **ML Architecture**: Spatial U-Net built in PyTorch (unet_blender.py).
- **The 'Winning Edge'**: ExtremeWeightedMSELoss implemented to heavily penalize missing high-rainfall events.
- **Training Loop**: 	rain.py built with robust 	ry/except fallbacks for Windows C-library limitations.

## 3. Pending Phases (To Execute on New System)

### Phase 3A: Heavy Data Download & Model Training (Requires GPU)
1. Add Copernicus API key to ~/.cdsapirc.
2. Run data fetchers to download 1-5 years of historical Indian-bound weather grids.
3. Execute python train.py on the GPU to generate the final unet_blender_weights.pth.

### Phase 3B: Backend Inference (No GPU Required)
1. Build FastAPI endpoints (e.g., GET /api/v1/forecast/blended).
2. Write logic to load the .pth weights, run the daily forecast grids through the U-Net, and output GeoJSON arrays.

### Phase 3C: Frontend Dashboard (No GPU Required)
1. Build React UI with Leaflet.js.
2. Create map layers for Base Models and Blended Output.
3. Implement a time slider for forecast lead times (Day 1 to 5).
4. Build the Extreme Weather Alerts sidebar.
