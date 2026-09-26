# AGENTS.md - SIH26081 Hybrid AI-NWP Blending System

## Context
This repository contains the codebase for SIH26081 (Ministry of Earth Sciences). The goal is to blend multiple weather forecast models (GFS, AI Models) into a single highly accurate forecast using a PyTorch U-Net, while explicitly preserving extreme weather events (cloudbursts).

## Tech Stack
- **Frontend**: React, TypeScript, TailwindCSS, Leaflet (Maps)
- **Backend**: FastAPI, Python 3.10+
- **ML / Data**: PyTorch, Xarray, cfgrib, NetCDF4, Boto3

## Directory Structure
- docs/ -> Contains modular documentation of implemented tasks.
- ackend/ -> FastAPI server.
- rontend/ -> React UI dashboard.
- ml_pipeline/ -> PyTorch models, data fetchers, and training loops.
- data/ -> Local storage for raw and processed weather grids.

## Current Project Status
- **DONE**: Monorepo scaffolding, FastAPI setup, GFS & ERA5 data fetchers, U-Net model, Custom Loss function, and PyTorch training loop.
- **PENDING / NEXT STEPS**: 
  1. Build the React Frontend (Map components, UI layout).
  2. Integrate backend API to serve the saved model weights (unet_blender_weights.pth) and blended .nc outputs to the frontend.

## Critical Rules for AI Agents (MUST FOLLOW)

1. **Workflow & Documentation**: Whenever instructed to 'plan' or 'implement' a feature, you MUST sequentially update or create a corresponding markdown file in the docs/ directory (e.g., 3-feature-name.md). Never write undocumented code.
2. **Communication Style**: Speak cleanly, strictly to the point, and professionally. NO YAPPING, no fluff, no long introductions or conclusions. Give direct technical answers and code.
3. **Code Conventions**: Follow strict, modular software engineering practices. Keep files small and focused. Use type hinting in Python, TypeScript in React, and keep everything highly readable.
4. **Windows Limitation**: The eccodes C-library is missing on this Windows host. DO NOT attempt to parse .grib2 files strictly in tests. Rely on the 	ry/except fallback mechanism in weather_dataset.py which mocks xarray data when the library fails.
5. **Data Size & OOM Prevention**: Weather grids are huge. Always crop spatial data to the Indian bounding box (Lat: 8 to 38, Lon: 68 to 98) during processing to prevent Out-Of-Memory errors.
6. **Execution Paths**: Always run 
pm commands inside rontend/. Always run uvicorn inside ackend/. Always run python ML scripts inside ml_pipeline/.
7. **The 'Winning Edge' (Context)**: The core differentiator for SIH26081 is preserving extreme weather events. Ensure the U-Net always utilizes the Custom Extreme Weighted Loss function rather than defaulting to standard MSE.
