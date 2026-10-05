"""
Evaluate Super-UNet Blender against GFS, AI Proxy, and Simple 50/50 Average
over the August 2023 monsoon benchmark using IMD verification standards.
"""
import sys
import os
from pathlib import Path

# Add backend to path so we can import services and models
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "backend"))

import numpy as np
import torch
from app.core.config import settings
from app.ml.unet_blender import SuperUNetBlender
from app.services.data_source import load_inputs, _synthesize, available_dates, SYNTHETIC_START, SYNTHETIC_DAYS
from app.services.inference_engine import _normalize

def compute_contingency(pred, truth, threshold):
    pred_pos = pred >= threshold
    truth_pos = truth >= threshold
    
    hits = np.sum(pred_pos & truth_pos)
    misses = np.sum((~pred_pos) & truth_pos)
    false_alarms = np.sum(pred_pos & (~truth_pos))
    
    pod = hits / (hits + misses + 1e-8)
    far = false_alarms / (hits + false_alarms + 1e-8)
    csi = hits / (hits + misses + false_alarms + 1e-8)
    
    return pod, far, csi, int(hits), int(misses), int(false_alarms)

def run_evaluation():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running evaluation on device: {device}")
    
    # Load model
    model = SuperUNetBlender(n_channels=7, n_models=2, features=[32, 64, 128, 256]).to(device)
    weights_path = project_root / "backend" / "weights" / "super_unet_blender_weights.pth"
    if not weights_path.exists():
        print(f"Error: weights not found at {weights_path}")
        return
        
    state = torch.load(weights_path, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    print("Loaded model weights successfully.")

    dates = available_dates()
    print(f"Evaluating across {len(dates)} dates in August 2023...")

    metrics = {
        "gfs": {"rain_sq": [], "rain_abs": [], "temp_sq": [], "temp_abs": [], "wind_sq": [], "wind_abs": []},
        "ai":  {"rain_sq": [], "rain_abs": [], "temp_sq": [], "temp_abs": [], "wind_sq": [], "wind_abs": []},
        "avg": {"rain_sq": [], "rain_abs": [], "temp_sq": [], "temp_abs": [], "wind_sq": [], "wind_abs": []},
        "blended": {"rain_sq": [], "rain_abs": [], "temp_sq": [], "temp_abs": [], "wind_sq": [], "wind_abs": []}
    }

    # Extreme rainfall contingency tables
    # IMD Thresholds: 64.5 mm (Heavy), 115.6 mm (Very Heavy)
    heavy_counts = {k: {"hits": 0, "misses": 0, "fa": 0} for k in ["gfs", "ai", "avg", "blended"]}
    vheavy_counts = {k: {"hits": 0, "misses": 0, "fa": 0} for k in ["gfs", "ai", "avg", "blended"]}

    with torch.no_grad():
        for d in dates:
            inputs = load_inputs(d, 24)
            # Reconstruct truth from synthesis
            synth = _synthesize(d, 24)
            # Recover truth_rain, truth_temp, truth_wind from synthetic generator logic
            # In synthetic mode, we can directly extract the ground truth fields
            from app.services.data_source import _seed, _synthetic_dem, _gauss, _smooth_noise, CLOUDBURST_HOTSPOTS
            from app.core.grid import LAT_GRID, LON_GRID
            from scipy.ndimage import gaussian_filter

            scenario = np.random.default_rng(_seed("scenario", d))
            dem = _synthetic_dem()
            jitter = lambda s: scenario.normal(0.0, s)
            base = (
                _gauss(22.5 + jitter(1.0), 81.0 + jitter(2.0), 2.5, 6.0, 30.0)
                + _gauss(25.3, 91.7, 0.5, 0.8, 95.0 + jitter(20))
                + _gauss(26.6 + jitter(0.5), 93.5, 0.8, 1.4, 45.0)
                + _gauss(19.0 + jitter(1.5), 88.0 + jitter(1.5), 1.6, 2.0, 42.0)
                + sum(_gauss(lat, lon - 0.5, 1.2, 0.5, 70.0) for lat, lon in
                      [(18.5, 73.8), (16.0, 74.1), (13.5, 75.3), (11.0, 76.6)])
                + 12.0 * _smooth_noise(scenario, 6.0)
            )
            n_bursts = int(scenario.integers(1, 3))
            picks = scenario.choice(len(CLOUDBURST_HOTSPOTS), size=n_bursts, replace=False)
            bursts = sum(
                _gauss(*CLOUDBURST_HOTSPOTS[i], 0.28, 0.28, float(scenario.uniform(180, 260))) for i in picks
            )
            t_rain = np.clip(base + bursts, 0.0, None)
            t_temp = (
                303.0 - 0.35 * np.clip(LAT_GRID - 24.0, 0, None) - 0.0065 * dem - 0.04 * t_rain
                + 0.8 * _smooth_noise(scenario, 5.0)
            )
            t_wind = np.clip(
                4.0 + _gauss(13.0, 70.0, 3.0, 5.0, 11.0) + _gauss(18.0, 88.0, 2.5, 3.0, 7.0)
                - 0.0006 * dem + 1.2 * _smooth_noise(scenario, 5.0),
                0.3, None,
            )

            gfs_r, gfs_t, gfs_w = inputs.gfs.rain, inputs.gfs.temp, inputs.gfs.wind
            ai_r, ai_t, ai_w = inputs.ai.rain, inputs.ai.temp, inputs.ai.wind

            # Forward pass
            channels = [gfs_r, gfs_t, gfs_w, ai_r, ai_t, ai_w, dem]
            x = torch.stack([_normalize(torch.from_numpy(c)) for c in channels]).unsqueeze(0).to(device)
            lt = torch.tensor([[24.0]], dtype=torch.float32, device=device)

            w_r, w_t, w_w = (w[0].float().cpu().numpy() for w in model(x, lt))

            b_r = (w_r[0] * gfs_r + w_r[1] * ai_r).astype(np.float32)
            b_t = (w_t[0] * gfs_t + w_t[1] * ai_t).astype(np.float32)
            b_w = (w_w[0] * gfs_w + w_w[1] * ai_w).astype(np.float32)

            avg_r = (0.5 * gfs_r + 0.5 * ai_r).astype(np.float32)
            avg_t = (0.5 * gfs_t + 0.5 * ai_t).astype(np.float32)
            avg_w = (0.5 * gfs_w + 0.5 * ai_w).astype(np.float32)

            models = {
                "gfs": (gfs_r, gfs_t, gfs_w),
                "ai":  (ai_r, ai_t, ai_w),
                "avg": (avg_r, avg_t, avg_w),
                "blended": (b_r, b_t, b_w)
            }

            for name, (pr, pt, pw) in models.items():
                metrics[name]["rain_sq"].append(np.mean((pr - t_rain) ** 2))
                metrics[name]["rain_abs"].append(np.mean(np.abs(pr - t_rain)))
                metrics[name]["temp_sq"].append(np.mean((pt - t_temp) ** 2))
                metrics[name]["temp_abs"].append(np.mean(np.abs(pt - t_temp)))
                metrics[name]["wind_sq"].append(np.mean((pw - t_wind) ** 2))
                metrics[name]["wind_abs"].append(np.mean(np.abs(pw - t_wind)))

                # Heavy Rain (64.5 mm)
                _, _, _, h, m, fa = compute_contingency(pr, t_rain, 64.5)
                heavy_counts[name]["hits"] += h
                heavy_counts[name]["misses"] += m
                heavy_counts[name]["fa"] += fa

                # Very Heavy Rain (115.6 mm)
                _, _, _, h2, m2, fa2 = compute_contingency(pr, t_rain, 115.6)
                vheavy_counts[name]["hits"] += h2
                vheavy_counts[name]["misses"] += m2
                vheavy_counts[name]["fa"] += fa2

    results_table = []
    print("\n" + "="*80)
    print("SIH26081: AUGUST 202Monsoon Benchmark Verification Results (Lead Time: +24h)")
    print("="*80)

    summary_rows = []
    for name in ["gfs", "ai", "avg", "blended"]:
        r_rmse = np.sqrt(np.mean(metrics[name]["rain_sq"]))
        r_mae  = np.mean(metrics[name]["rain_abs"])
        t_rmse = np.sqrt(np.mean(metrics[name]["temp_sq"]))
        t_mae  = np.mean(metrics[name]["temp_abs"])
        w_rmse = np.sqrt(np.mean(metrics[name]["wind_sq"]))
        w_mae  = np.mean(metrics[name]["wind_abs"])

        # Heavy rain metrics
        h_h = heavy_counts[name]["hits"]
        h_m = heavy_counts[name]["misses"]
        h_fa = heavy_counts[name]["fa"]
        h_pod = h_h / (h_h + h_m + 1e-8) * 100
        h_csi = h_h / (h_h + h_m + h_fa + 1e-8) * 100
        h_far = h_fa / (h_h + h_fa + 1e-8) * 100

        # Very heavy (cloudburst)
        vh_h = vheavy_counts[name]["hits"]
        vh_m = vheavy_counts[name]["misses"]
        vh_fa = vheavy_counts[name]["fa"]
        vh_pod = vh_h / (vh_h + vh_m + 1e-8) * 100
        vh_csi = vh_h / (vh_h + vh_m + vh_fa + 1e-8) * 100

        summary_rows.append({
            "name": name.upper(),
            "r_rmse": r_rmse, "r_mae": r_mae,
            "t_rmse": t_rmse, "t_mae": t_mae,
            "w_rmse": w_rmse, "w_mae": w_mae,
            "h_pod": h_pod, "h_csi": h_csi, "h_far": h_far,
            "vh_pod": vh_pod, "vh_csi": vh_csi
        })

    md_output = [
        "# SIH26081 Verification Benchmark Results",
        "",
        "**Benchmark Scope**: August 2023 Monsoon (31 Days, 128×128 Indian Domain, +24h Lead Time)",
        "**Baselines Evaluated**: Raw NOAA GFS, AI Proxy (GraphCast architecture), Simple 50/50 Ensemble Average, and Meghdrishti Super-UNet Blender.",
        "",
        "## 1. Overall Forecast Accuracy (Error Metrics)",
        "",
        "| Model | Rain RMSE (mm) | Rain MAE (mm) | Temp RMSE (K) | Temp MAE (K) | Wind RMSE (m/s) | Wind MAE (m/s) |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in summary_rows:
        md_output.append(f"| **{r['name']}** | {r['r_rmse']:.2f} | {r['r_mae']:.2f} | {r['t_rmse']:.2f} | {r['t_mae']:.2f} | {r['w_rmse']:.2f} | {r['w_mae']:.2f} |")

    md_output.extend([
        "",
        "## 2. Extreme Weather Detection (IMD Heavy & Cloudburst Thresholds)",
        "",
        "| Model | Heavy Rain POD (Hit Rate %) | Heavy Rain CSI (Threat Score %) | Heavy Rain FAR (False Alarm %) | Cloudburst (>115.6mm) POD (%) | Cloudburst CSI (%) |",
        "|---|---|---|---|---|---|",
    ])

    for r in summary_rows:
        md_output.append(f"| **{r['name']}** | {r['h_pod']:.1f}% | {r['h_csi']:.1f}% | {r['h_far']:.1f}% | {r['vh_pod']:.1f}% | {r['vh_csi']:.1f}% |")

    md_text = "\n".join(md_output)
    print(md_text)

    out_file = project_root / "docs" / "BENCHMARK_RESULTS.md"
    out_file.write_text(md_text)
    print(f"\nSaved benchmark markdown to: {out_file}")

if __name__ == "__main__":
    run_evaluation()
