# AGENTS.md - SIH26081 Hybrid AI-NWP Blending System

## Context
This repository contains the codebase for SIH26081 (Ministry of Earth Sciences). The goal is to blend multiple weather forecast models (GFS, AI Models) into a single highly accurate forecast using a PyTorch U-Net, while explicitly preserving extreme weather events (cloudbursts).

## Tech Stack
- **Frontend**: React, TypeScript, TailwindCSS, Leaflet (Maps)
- **Backend**: FastAPI, Python 3.10+
- **ML / Data**: PyTorch, Xarray, cfgrib, NetCDF4, Boto3

## Directory Structure
- docs/ -> Contains modular documentation of implemented tasks.
- backend/ -> FastAPI server.
- frontend/ -> React UI dashboard.
- ml_pipeline/ -> PyTorch models, data fetchers, and training loops.
- data/ -> Local storage for raw and processed weather grids.

## Current Project Status
- **DONE**: Monorepo scaffolding, GFS & ERA5 data fetchers, Super-UNet model, custom loss, training loop (500 epochs).
- **DONE (Phase 3B)**: FastAPI inference API serving `backend/weights/super_unet_blender_weights.pth` (git-ignored). See `docs/5-backend-inference.md`.
- **DONE (Phase 3C/3D)**: "Meghdrishti" React/Leaflet command center. See `docs/7-frontend-command-center.md` and `docs/8-command-center-features.md`.
- **KNOWN ISSUES / NEXT STEPS**:
  1. `ml_pipeline/preprocess.py` multiplies GFS `tp` by 1000, but GFS precipitation is already kg/m² (= mm). GFS rain is 1000× too large, so the model learned to ignore GFS for rain. Fix, re-preprocess, retrain.
  2. The synthetic AI proxy (`ai_fetcher.py`) is ERA5 × 0.9 + small noise (no blur), so it leaks the target. Add blur and weaken extremes.
  3. `ml_pipeline/evaluate.py` imports a class that no longer exists (`UNetBlender`). Rewrite it to report RMSE/MAE and POD/FAR/CSI on held-out September 2023.
  4. Without `ml_pipeline/data/processed/*.pt`, the backend serves deterministic generated scenarios (`data_source: "synthetic"` in API metadata).

## Critical Rules for AI Agents (MUST FOLLOW)

1. **Workflow & Documentation**: Whenever instructed to 'plan' or 'implement' a feature, you MUST sequentially update or create a corresponding markdown file in the docs/ directory (e.g., 3-feature-name.md). Never write undocumented code.
2. **Communication Style**: Speak cleanly, strictly to the point, and professionally. NO YAPPING, no fluff, no long introductions or conclusions. Give direct technical answers and code.
3. **Code Conventions**: Follow strict, modular software engineering practices. Keep files small and focused. Use type hinting in Python, TypeScript in React, and keep everything highly readable.
4. **Data Size & OOM Prevention**: Weather grids are huge. Always crop spatial data to the Indian bounding box (Lat: 8 to 38, Lon: 68 to 98) during processing to prevent Out-Of-Memory errors.
5. **Execution Paths**: Always run bun commands inside frontend/. Always run uvicorn inside backend/. Always run python ML scripts inside ml_pipeline/.
6. **The 'Winning Edge' (Context)**: The core differentiator for SIH26081 is preserving extreme weather events. Ensure the U-Net always utilizes the Custom Extreme Weighted Loss function rather than defaulting to standard MSE.
