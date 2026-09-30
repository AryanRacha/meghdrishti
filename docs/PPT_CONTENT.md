# SIH26081 — Presentation Content

**Hybrid AI-NWP Forecast Blending System for Extreme Weather** · Ministry of Earth Sciences

---

## Slide 1 — Title
**Meghdrishti (मेघदृष्टि, "Cloud Vision")**
Hybrid AI-NWP Super-Ensemble: Blending Physics and AI to Protect Lives from Extreme Weather
Team name · SIH26081 · Ministry of Earth Sciences

---

## Slide 2 — The Problem
- **Physical NWP models (GFS)** understand atmospheric physics but struggle with complex local topography (Himalaya, Western Ghats).
- **AI models (GraphCast)** are fast but tend to smooth out extreme events.
- **Simple averaging dilutes extremes** — a cloudburst predicted by one model gets averaged away.
- IMD's operational gaps: microclimate extremes, impact-based forecasting, actionable warnings, last-mile reach.

---

## Slide 3 — Our Solution
- A **Spatial U-Net** that learns a per-pixel **"Trust Map"** — how much to trust GFS vs AI at every ~26 km cell of India.
- Separate blending logic for **Rain, Temperature and Wind**.
- Blending adapts to **forecast lead time** (FiLM conditioning).
- Delivered as an **end-to-end decision-support system**: model → API → command-center dashboard → district-level alerts.

---

## Slide 4 — Data Pipeline
| Source | Role | Format |
|---|---|---|
| NOAA GFS 0.25° (AWS S3), 00Z, +24 h | Physical NWP forecast | GRIB2 |
| ERA5 Reanalysis (Copernicus CDS) | Ground truth | NetCDF |
| AI forecast proxy (GraphCast-style) | AI forecast | NetCDF |
| ERA5 geopotential → elevation | Topography (DEM) | NetCDF |

- Domain cropped to India: **8–38°N, 68–98°E**, regridded to **128 × 128** (~0.24°, ~26 km).
- Variables: rainfall, 2 m temperature, 10 m wind magnitude.
- Training period: **Monsoon, August 2023**.
- *AI proxy:* Public GraphCast data for 2023 is not yet released (WeatherBench2 stops at 2022). We generate a scientifically controlled AI proxy from ERA5 to keep timelines consistent; the pipeline accepts real GraphCast output unchanged.

---

## Slide 5 — Model Architecture: Super-UNet Blender
```
Input [7 × 128 × 128]
 GFS rain · GFS temp · GFS wind · AI rain · AI temp · AI wind · DEM
        │
 Encoder: 4 × Residual blocks (32 → 64 → 128 → 256) + MaxPool
        │
 Bottleneck: Residual block (512) + FiLM ← lead time
        │
 Decoder: 4 × Up-conv + Attention-gated skip connections
        │
 3 Output heads (Softmax over models)
 Rain weights · Temp weights · Wind weights   [2 × 128 × 128 each]
        │
 Blend = w_GFS · GFS + w_AI · AI
```
- **8.2 million parameters** (33 MB weights).
- **Residual blocks** — stable deep training.
- **FiLM layer** — changes blending strategy by lead time.
- **Attention gates** — focus skip connections on relevant regions (e.g., orographic rain zones).
- **Multi-head output** — independent trust logic per variable.

---

## Slide 6 — The Winning Edge: Extreme-Weighted Loss
- Standard MSE optimizes for the average and ignores rare cloudbursts.
- Our **Composite Loss**:
  - **Rain:** squared error × `1 + α · exp(β · (y − T) / T)` for pixels above the extreme threshold T → penalty grows **exponentially** with rainfall intensity.
  - **Temperature & Wind:** scaled MSE terms so Kelvin-scale errors don't drown out millimetre-scale rain.
- Result: the network is mathematically pushed to **preserve high-impact rainfall** rather than smooth it away.

---

## Slide 7 — Training Setup
| Item | Value |
|---|---|
| Epochs | **500** (full run) |
| Optimizer | Adam, lr = 1e-4 |
| Batch size | 16 |
| Early stopping | Patience 15 |
| Precision | Automatic Mixed Precision (AMP) |
| Hardware | NVIDIA RTX 4090 (24 GB), native WSL2 Linux |
| Input normalization | Per-channel z-score |

---

## Slide 8 — Engineering Challenges We Solved
| Challenge | Solution |
|---|---|
| GFS GRIB2 "hypercube" crashes (instant vs accumulated step types) | `cfgrib.open_datasets()` to split into isolated datasets |
| Copernicus API silently returning zipped NetCDF | Auto unzip-and-replace failsafe |
| GPU idle at 0% — WSL `/mnt/c` 9P I/O bottleneck | Migrated to native Linux filesystem + `uv` |
| 2 hours for 5 epochs (on-the-fly GRIB interpolation) | Pre-compiled `.pt` tensors → **20 seconds (360× faster)** |
| Rain on Kelvin scale drowned in the loss | Composite, scale-balanced loss |
| GFS precipitation unit mismatch vs ERA5 | Identified during validation; unit-harmonized pipeline |

---

## Slide 9 — System Architecture
```
NOAA S3 / Copernicus ─► Fetchers ─► Preprocess (.pt tensors) ─► Super-UNet (PyTorch)
                                                                      │
                                            FastAPI inference service (singleton model)
                                                                      │
                                     GeoJSON REST API  /api/v1/forecast/{blended, alerts, meta}
                                                                      │
                                     React + Leaflet Command Center  ·  External agencies (NDMA, Agri)
```
- Stateless backend → deployable on MoES Kubernetes.
- Standard **GeoJSON + REST** → any agency can consume it without rewriting their systems.

---

## Slide 10 — The Command Center (Live Demo)
- Full-screen map of India with floating glass UI.
- Toggle **GFS / AI / Blended / Trust** layers for Rain, Temperature, Wind.
- Lead-time slider (Day 1–5) and date picker.
- **XAI Trust Map** — shows where the model trusted physics vs AI.
- **Threat Matrix** — auto-detected heavy-rain regions, ranked, graded by **IMD categories** (Heavy ≥ 64.5 mm, Very Heavy ≥ 115.6 mm, Extremely Heavy ≥ 204.5 mm), mapped to the nearest district; click to fly to the hotspot.

---

## Slide 11 — Our USPs
1. **Life-saving loss function** — extreme events are prioritized over average accuracy.
2. **Explainable AI Trust Maps** — no black box; forecasters see *why*.
3. **Hybrid physics + AI blending** — per-pixel, per-variable, lead-time-aware.
4. **IMD-graded, district-level Threat Matrix** — from raw numbers to actionable hotspots.
5. **Open, interoperable API** — plug-and-play for NDMA and other agencies.

---

## Slide 12 — System Performance (Measured)
| Metric | Value |
|---|---|
| Model size | 8.2 M parameters · 33 MB |
| Inference time (full India grid, CPU) | **~0.3 s** |
| Data pipeline speed-up | **360×** (2 h → 20 s per 5 epochs) |
| API payload per map layer (gzip) | **~44 KB** |
| Spatial resolution | 128 × 128 grid, ~26 km |
| Variables blended | 3 (rain, temperature, wind) |
| Training | 500 epochs on RTX 4090 |

---

## Slide 13 — Evaluation Framework & Targets
**Protocol:** train on August 2023, test on **held-out September 2023**; compare four forecasts against ERA5.

**Target Performance (Day-1, monsoon, vs ERA5) — goals to be validated**

| Metric | Typical raw GFS (≈) | **Our target (Super-UNet blend)** |
|---|---|---|
| Rainfall RMSE | ≈ 12–15 mm/day | **≈ 10–12 mm/day (15–20% lower than GFS)** |
| Rainfall MAE | ≈ 6–8 mm/day | **15–20% lower than GFS** |
| Rainfall spatial correlation | ≈ 0.5–0.6 | **≥ 0.70** |
| 2 m Temperature RMSE | ≈ 1.8–2.5 K | **≤ 1.5 K** |
| 10 m Wind RMSE | ≈ 1.8–2.5 m/s | **≤ 1.5 m/s** |
| Heavy rain (≥ 64.5 mm) POD | ≈ 0.35–0.45 | **≥ 0.60** |
| Heavy rain FAR | ≈ 0.55–0.65 | **≤ 0.45** |
| Heavy rain CSI | ≈ 0.15–0.25 | **≥ 0.30** |
| Beats simple 50/50 average | — | **On all metrics** |

- **POD** = Probability of Detection (hits ÷ observed events) · **FAR** = False Alarm Ratio · **CSI** = Critical Success Index — the metrics that matter for disaster response.
- Headline goal: **15–20% lower rainfall error than GFS, and ~1.5× better heavy-rain detection (CSI).**
- Validation plan: train on August 2023, test on held-out September 2023; compare GFS, AI, 50/50 average, and Super-UNet.

---

## Slide 14 — Roadmap
- **Impact-based vulnerability engine:** Risk = rainfall intensity × population density → NDRF prioritization.
- **GenAI briefings (Gemini):** plain-language, local-language alerts for District Magistrates.
- **Swipe comparison** GFS vs Blended in the dashboard.
- Scale data to **June–September 2021–2023** monsoons; real GraphCast/Pangu forecasts; lead times up to Day 5.
- Operational deployment on MoES infrastructure.

---

## Slide 15 — Thank You
Team members · GitHub: `AryanRacha/sih-forecast-blending-system`

---

### Presenter notes (do not put on slides)
- Be upfront that the AI forecast is a **proxy** — judges respect transparency.
- Slide 13 numbers are **targets**. Keep the title "Target Performance" so they aren't read as achieved results. The "typical GFS" column is an approximate range; cite a source (e.g., IMD/NCMRWF verification reports) if you can, or say "approximate literature range" when asked.
- The live demo currently runs on **synthetic inputs** (badge shown in the UI) because processed tensors aren't on the demo machine; copy `ml_pipeline/data/processed/*.pt` to switch to real data.
