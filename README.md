# SIH26081: Meghdrishti - Hybrid AI-NWP Super-Resolution Blending System

**Ministry of Earth Sciences Problem Statement (SIH26081)**
Meghdrishti is a production-grade Spatial Deep Learning Engine (Attention U-Net) designed to seamlessly blend traditional physical weather models (NOAA GFS) with the latest generation of Global AI Foundation Models (Huawei Pangu-Weather). 

By dynamically shifting its trust based on regional topography, lead time, and physical state variables, Meghdrishti generates a single, highly accurate $0.1^\circ$ (~10km) weather grid over India. Crucially, it employs a custom **Masked Extreme-Weighted Loss function** to explicitly preserve catastrophic weather events (cloudbursts, heatwaves, cyclones) that traditional linear statistics simply smooth away.

---

## 🧠 The Architecture (V2 Upgrade)
We abandoned simple mathematical averaging (and traditional ML) for a cutting-edge **13-Channel Super-Resolution Attention U-Net**:
- **The Inputs (13 Channels)**: We ingest 6 atmospheric variables (Precipitation, 2m Temp, 10m U-Wind, 10m V-Wind, Mean Sea Level Pressure, and Relative Humidity) from both GFS and Pangu-Weather, plus a static Topography map (DEM) of India.
- **Super-Resolution Grid**: The inputs are ingested at $0.25^\circ$ and mathematically upscaled into a dense **$320 \times 320$** tensor to perfectly map against the IMD's high-resolution $0.1^\circ$ observation datasets.
- **Spatio-Temporal Cross-Attention**: Instead of global scalars, we use a custom Cross-Attention layer that dynamically queries the spatial feature maps based on temporal embeddings (Lead Time, Seasonality). The model learns that AI predictions decay differently over the Himalayas than they do over the central plains.
- **The Output (4 Safety-Valve Heads)**: The network outputs dynamic Softmax Trust Weights for Rain, Temp, U-Wind, and V-Wind. It also includes a **Residual Bias Safety Head**, allowing the U-Net to physically inject rain into the output if both GFS and the AI completely miss a localized storm.

---

## 🛤️ Overcoming Operational Flaws (The "Why")

Building a system capable of passing the IMD's stringent validation standards required solving massive data and mathematical traps:

### 1. Eliminating "Analysis Bias" (The Perfect Initialization Trap)
* **The Problem:** If you train a blending model on AI hindcasts that were generated using ERA5 (a perfect, post-corrected reanalysis), the blending model will falsely learn that the AI is flawless. In live production, the AI gets fed noisy operational data, causing the blending model to fail catastrophically.
* **The Solution:** We explicitly generate our historical Pangu-Weather training data using noisy NOAA GDAS/ECMWF Operational Analysis initial conditions. Our training data perfectly mirrors live operational deployment noise.

### 2. The Vector Cancellation Trap
* **The Problem:** Blending wind "magnitude" is physically illegal. A +15m/s East wind and a -15m/s West wind should cancel to zero. If you blend magnitudes, the model incorrectly predicts a 15m/s storm.
* **The Solution:** We deconstruct all wind into native U-Wind (Zonal) and V-Wind (Meridional) vectors, blending them independently through the U-Net, and strictly calculating magnitude downstream.

### 3. The "Zero-Rain" Gradient Freeze
* **The Problem:** India is dry for 8 months of the year. If you feed the network thousands of dry winter days, the rain-prediction head's gradients will stagnate.
* **The Solution:** We engineered a **Masked Extreme-Weighted Loss**. The network only calculates backpropagation on pixels where rain actually fell or was predicted. 100% of the network's learning capacity is dedicated to predicting severe storms.

### 4. FP16 Mixed-Precision Underflow
* **The Problem:** Multi-task learning (Temp, Rain, Wind) requires vastly different loss scaling. Pre-multiplying a small temperature loss by 0.01 in FP16 causes the gradient to underflow to absolute zero, freezing the weights.
* **The Solution:** We execute independent, sequential `scaler.scale().backward()` passes while retaining the computation graph, guaranteeing perfect numerical stability across all output heads.

---

## 📁 Directory Structure
- `docs/` - Exhaustive architectural deep-dives, peer reviews, and implementation plans.
- `AGENTS.md` - Core instructions for AI pair-programmers.
- `backend/` - FastAPI server handling live ECMWF/NOAA data fetching and PyTorch inference.
- `frontend/` - React + TypeScript UI Dashboard (Vite) with a built-in guided tour.
- `ml_pipeline/` - PyTorch Super-UNet, Data Fetchers, Validation (EDI/ETS), and K-Fold LOSO Training loops.

---

## 🚀 Execution & Setup 

### 1. ML Pipeline (Model Training - Requires 24GB VRAM GPU)
```bash
cd ml_pipeline
uv sync
# The pipeline natively executes 3-Fold Leave-One-Season-Out (LOSO) Cross-Validation
uv run python train.py
```

### 2. Backend API
Place the trained weights at `backend/weights/super_unet_v2_Fold_1.pth`.
```bash
cd backend
uv sync
uv run dev       # Development server with auto-reload (http://127.0.0.1:8000)
```
API runs on `http://127.0.0.1:8000`. Swagger UI at `/docs`. 

### 3. Frontend Dashboard
```bash
cd frontend
bun install
bun run dev
```
Dashboard runs on `http://localhost:5173`. Click **▶ Guided Tour** for an operational walkthrough.
