# 15. IMD Methodology and AI Training Data

## TOPIC 1: Available AI Weather Model Forecast Archives

### WeatherBench 2 (Google Cloud Storage)
The primary open-source archive for AI weather model hindcasts and forecasts is **WeatherBench 2**. 
- **Data Access:** Hosted publicly on Google Cloud Storage at `gs://weatherbench2/datasets` ([WeatherBench 2 Data Guide](https://weatherbench2.readthedocs.io/en/latest/data-guide.html)).
- **Format:** Zarr format, optimized for cloud-native access and distributed computing.
- **Included AI Models:**
  - **GraphCast** (Google DeepMind)
  - **Pangu-Weather** (Huawei)
  - **FourCastNet** (NVIDIA)
  - **GenCast** (Google DeepMind)
  - **NeuralGCM** (Google)
- **Variables & Resolution:** The datasets include surface variables such as `tp` (total precipitation), `t2m` (2m temperature), `10u`, and `10v` (10m wind). Spatial resolution for high-res baselines (like GraphCast and Pangu-Weather) is evaluated at 0.25°. 
- **Date Range:** The bulk of the hindcast data spans historical periods up to late 2022. 

### ECMWF AIFS
ECMWF's operational AI model (AIFS) forecasts are accessible via the ECMWF Meteorological Archival and Retrieval System (MARS) under their open data policies. Real-time open data access has been phased in, but historical AIFS hindcasts spanning decades are not provided as a standalone downloadable cloud bucket comparable to WeatherBench 2.

### Generating Hindcasts Locally (`ecmwf/ai-models`)
You can generate your own hindcasts using the `ecmwf/ai-models` pip package (which uses ERA5 initial conditions).
- **GPU Requirements:** 
  - An NVIDIA GPU is practically required. Running these on CPU takes hours per forecast.
  - **Pangu-Weather & GraphCast:** While individual model weights are around 1-2 GB, the activation memory during inference is huge. It will typically cause Out-of-Memory (OOM) errors on 12 GB VRAM GPUs (like the RTX 3060). A GPU with **at least 16 GB to 24 GB VRAM** (e.g., RTX 3090, RTX 4090, A100) is highly recommended.
- **Speed:** On a capable GPU (like an RTX 4090 or Tesla V100), generating a 24-hour forecast takes approximately 1 to 2 seconds.

### Indian AI Weather Models
Currently, there are no publicly available Indian AI weather models (from IITM Pune, NCMRWF, or IISc) that offer downloadable hindcast archives equivalent to the global models on WeatherBench 2.

---

## TOPIC 2: Model Architecture Deep Dive

Recent literature (2024-2025) on deep learning for NWP post-processing highlights the following:

1. **Vision Transformers (ViT) & Swin Transformers:** Models like Pangu-Weather utilize 3D Earth-specific transformers. While powerful globally, implementing a ViT backbone for a 128x128 regional blending task may be overly complex for a 1-2 day turnaround on a single RTX 4090.
2. **Attention U-Net / CAMT (Channel Attention Multi-task Learning):** Adding spatial and channel attention to U-Nets is highly effective for localized extreme events. **Practicality:** Very practical to implement in 1-2 days on an RTX 4090. **Improvement:** Moderate to high over vanilla U-Net by allowing the network to focus on specific severe weather phenomena ([CAMT for Precipitation](https://climatechange.ai)).
3. **Graph Neural Networks (GNNs):** GraphCast uses mesh-based GNNs to handle the Earth's spherical geometry. **Practicality:** For a small regional grid (8-38N, 68-98E) where lat/lon distortion is manageable, a GNN is overly complex to implement quickly and doesn't offer drastic improvements over CNNs for flat grid blending.
4. **Diffusion Models & Normalizing Flows:** Models like GenCast use diffusion for probabilistic generation. Recent trends in post-processing also favor Normalizing Flows to capture non-Gaussian uncertainty ([Normalizing Flows for Weather](https://arxiv.org/)). **Practicality:** Difficult to train stably in 1-2 days; inference is much slower than deterministic U-Nets.
5. **Seamless Blending Frameworks:** The current best practice is using deep U-Nets (often hybridizing ML with statistical methods) that ingest contextual auxiliary inputs (lead time, seasonality, orography) alongside the raw NWP outputs.

**Conclusion:** For a 1-2 day turnaround on an RTX 4090, upgrading the vanilla U-Net to an **Attention U-Net** with auxiliary spatial inputs (orography/elevation) is the most practical and impactful architectural change.

---

## TOPIC 3: IMD's EXACT Current Process

### MME Methodology Overview
The India Meteorological Department (IMD) and National Centre for Medium-Range Weather Forecasting (NCMRWF) use a Multi-Model Ensemble (MME) to reduce NWP uncertainties. 
- For district-level medium-range rainfall forecasts, the IMD determines grid-point weights based on the **Anomaly Correlation Coefficient (CC)** between historical model forecasts and actual observations.
- These statistical weights are then applied to the constituent models to generate a consensus forecast.

### Models in the IMD MME
The operational MME integrates outputs from:
1. **IMD GFS** (Global Forecast System) and **GEFS** (Global Ensemble Forecasting System)
2. **NCEP GFS** (USA)
3. **NCMRWF Unified Model (NCUM)** and **NEPS** (NCMRWF Ensemble Prediction System)
4. **JMA GSM** (Japan Meteorological Agency Global Spectral Model)
5. **MMCFS** (Monsoon Mission Coupled Forecasting System)

### Limitations & AI Integration
- **Limitations:** Simple ensemble means and linear weighted averages often smooth out extremes, leading to underestimation of heavy rainfall events (poor Probability of Detection / POD) and higher False Alarm Rates (FAR) for localized severe weather.
- Research published in the IMD's official journal, *MAUSAM*, acknowledges these limitations and points toward advanced statistical and machine learning post-processing methods to improve upon linear Anomaly Correlation Coefficient weighting.
