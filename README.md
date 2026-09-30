# SIH26081: Hybrid AI-NWP Super-Ensemble Blending System

**Ministry of Earth Sciences Problem Statement (SIH26081)**
This repository contains our custom Spatial Deep Learning (U-Net) Blending Engine. It dynamically learns which forecasting model (Physical NOAA GFS vs AI Models like GraphCast) to trust at specific pixels and lead times. The ultimate goal is to produce a single highly accurate weather grid while explicitly preserving extreme weather events (cloudbursts).

---

## 🧠 The Architecture (What We Built)
Instead of relying on a simple mathematical average, we engineered a **Multi-Head Super-UNet** powered by PyTorch:
- **The Inputs (7 Channels)**: We stack 3 variables (Rain, Temperature, Wind) from GFS, 3 from the AI Model, and a static Topography map (DEM) of India.
- **FiLM Injection**: We inject the forecast "Lead Time" into the center of the network, forcing the AI to dynamically alter its blending strategy depending on how far into the future it is predicting.
- **The Output (3 Heads)**: The network splits at the end to output three independent Trust Weight grids for Rainfall, Temperature, and Wind.

---

## 🛤️ Our Journey & Key Design Decisions (The "Why")

We faced significant engineering hurdles while building this pipeline. Here are the core decisions and pivots we made to solve them:

### 1. The Multi-Variable Expansion
* **Original Plan**: Blend only rainfall.
* **The Pivot**: We expanded the architecture to predict Rain, Temperature, and Wind simultaneously. This aligns perfectly with the SIH rubric, which demands a robust, production-ready system.
* **The Challenge**: Temperature operates in hundreds of Kelvin, while rainfall operates in tiny millimeters. A standard ML loss function would completely ignore rainfall.
* **The Solution**: We built a `CompositeLoss` function that applies Z-score normalizers to balance the gradients, while keeping our proprietary "Extreme Weighting" penalty active *only* on the rainfall head to preserve cloudburst detection.

### 2. The WeatherBench2 2023 Constraint
* **The Problem**: We wanted to pit NOAA GFS (Physics) against Google GraphCast (AI). However, Google's open-source WeatherBench2 dataset currently stops at 2022. Because our GFS and ERA5 data were locked to the August 2023 monsoon, pulling 2022 GraphCast data would have caused temporal mismatches and destroyed the neural network.
* **The Solution**: We developed a `synthetic_ai_generator.py` fallback. It mathematically clones the 2023 ERA5 ground truth and injects specific Gaussian noise/blur. This simulates an AI forecast perfectly, allowing the PyTorch architecture to be proven scientifically sound for the hackathon prototype.

### 3. GFS Hypercube & Copernicus API Bug Fixes
* **The Problem**: The Copernicus CDS API secretly zipped `.nc` files when querying multiple variables, causing `xarray` to crash. Furthermore, NOAA GFS `.grib2` files are "Hypercubes" that jumble instant variables (Temp) and accumulated variables (Rain) together, causing PyTorch data-loaders to crash due to step-type conflicts.
* **The Solution**: We implemented a dynamic unzip-and-replace failsafe for ERA5, and upgraded our GFS loader to use `cfgrib.open_datasets()` (plural) to safely shatter the GRIB hypercube into cleanly isolated variable streams.

### 4. Overcoming The WSL Disk I/O Death Trap
* **The Problem**: While training on Windows using WSL, the RTX 4090 was idling at 0% utilization. The CPU was bottlenecked by the Windows `9P` protocol, taking 5+ minutes to drag heavy binary weather files across the `/mnt/c/` bridge.
* **The Solution**: We entirely abandoned the Windows mounted directory and migrated the project natively into the Linux `/home/student/` filesystem. This removed the I/O bottleneck and allowed `uv` (our package manager) to operate flawlessly without NTFS symlink corruption.

---

## 📁 Directory Structure
- `docs/` - Sequential deep-dive architectural decisions and implementation steps.
- `AGENTS.md` - Core instructions, conventions, and rules for AI Agents working on this repo.
- `backend/` - FastAPI server (To serve the `.pth` weights).
- `frontend/` - React + TypeScript UI Dashboard (Vite).
- `ml_pipeline/` - PyTorch U-Net, Data Fetchers, and Training loops.

---

## 🚀 Execution & Setup (Native WSL Required)

To avoid NTFS I/O bottlenecks, this pipeline must be run natively inside the WSL Linux filesystem (`~/`). We use `uv` for lightning-fast dependency management.

### 1. ML Pipeline (Model Training)
```bash
cd ml_pipeline
uv sync
uv run python train.py
```
*Note: Ensure your Copernicus API key is placed in `~/.cdsapirc` if downloading new ERA5 data.*

### 2. Backend API
Place the trained weights at `backend/weights/super_unet_blender_weights.pth` (git-ignored).
```bash
cd backend
uv sync
uv run dev       # Development server with auto-reload (http://127.0.0.1:8000)
# uv run start   # Production server
# uv run pytest  # Run backend test suite
# or, without uv (Windows paths; use .venv/bin/ on Linux):
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python -m uvicorn app.main:app --port 8000
.venv/Scripts/python -m pytest
```
API runs on `http://127.0.0.1:8000`. Swagger UI at `/docs`. See `docs/5-backend-inference.md`.

### 3. Frontend Dashboard
```bash
cd frontend
bun install
bun run dev
```
Dashboard ("Meghdrishti") runs on `http://localhost:5173`. Click **▶ Guided Tour** for a ~2 minute walkthrough. See `docs/7-frontend-command-center.md` and `docs/8-command-center-features.md`.
