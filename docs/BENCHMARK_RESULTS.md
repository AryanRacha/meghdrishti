# SIH26081 Verification Benchmark Results

**Benchmark Scope**: August 2023 Monsoon (31 Days, 128×128 Indian Domain, +24h Lead Time)
**Baselines Evaluated**: Raw NOAA GFS, AI Proxy (GraphCast architecture), Simple 50/50 Ensemble Average, and Meghdrishti Super-UNet Blender.

## 1. Overall Forecast Accuracy (Error Metrics)

| Model | Rain RMSE (mm) | Rain MAE (mm) | Temp RMSE (K) | Temp MAE (K) | Wind RMSE (m/s) | Wind MAE (m/s) |
|---|---|---|---|---|---|---|
| **GFS** | 4.48 | 2.50 | 1.39 | 1.02 | 0.95 | 0.76 |
| **AI** | 5.69 | 3.54 | 0.63 | 0.45 | 0.61 | 0.49 |
| **AVG** | 3.86 | 2.30 | 0.71 | 0.54 | 0.56 | 0.44 |
| **BLENDED** | 5.04 | 2.74 | 0.68 | 0.51 | 0.55 | 0.43 |

## 2. Extreme Weather Detection (IMD Heavy & Cloudburst Thresholds)

| Model | Heavy Rain POD (Hit Rate %) | Heavy Rain CSI (Threat Score %) | Heavy Rain FAR (False Alarm %) | Cloudburst (>115.6mm) POD (%) | Cloudburst CSI (%) |
|---|---|---|---|---|---|
| **GFS** | 94.6% | 59.6% | 38.3% | 66.1% | 50.5% |
| **AI** | 37.6% | 35.4% | 14.5% | 2.5% | 2.5% |
| **AVG** | 77.9% | 65.0% | 20.3% | 25.5% | 25.2% |
| **BLENDED** | 38.0% | 35.7% | 14.6% | 2.5% | 2.5% |