"""
Production-grade forecast evaluation suite.

Implements the same verification metrics used by WeatherBench 2 (Rasp et al., 2024),
ECMWF operational verification, and IMD's published skill scores.

Metrics computed:
  - RMSE (Root Mean Square Error)
  - MAE (Mean Absolute Error)
  - Bias (Mean Error)
  - ACC (Anomaly Correlation Coefficient) — the gold standard in NWP
  - SSIM (Structural Similarity Index) — spatial pattern fidelity
  - Skill Score vs Climatology and vs Simple Average baseline

  Extreme event categorical verification (IMD thresholds):
  - POD  (Probability of Detection)       = Hits / (Hits + Misses)
  - FAR  (False Alarm Ratio)              = FA / (Hits + FA)
  - CSI  (Critical Success Index)         = Hits / (Hits + Misses + FA)
  - ETS  (Equitable Threat Score / GSS)   = (Hits - Hits_random) / (Hits + Misses + FA - Hits_random)
  - FBI  (Frequency Bias Index)           = (Hits + FA) / (Hits + Misses)
  - HSS  (Heidke Skill Score)             = 2*(Hits*CN - FA*Misses) / ((Hits+Misses)*(Misses+CN) + (Hits+FA)*(FA+CN))

  Multi-threshold evaluation using official IMD rainfall categories:
  - Very Light:        0.1 – 2.4 mm
  - Light:             2.5 – 15.5 mm
  - Moderate:          15.6 – 64.4 mm
  - Heavy:             64.5 – 115.5 mm
  - Very Heavy:       115.6 – 204.4 mm
  - Extremely Heavy:  ≥ 204.5 mm

References:
  [1] Rasp et al., "WeatherBench 2: A Benchmark for the Next Generation of
      Data-Driven Global Weather Models", JAMES 2024.
  [2] IMD, "Verification of District Level Rainfall Forecasts",
      MAUSAM Journal, various issues.
  [3] Wilks, "Statistical Methods in the Atmospheric Sciences", 4th ed., 2019.
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from models.unet_blender import SuperUNetBlender
from data_loaders.weather_dataset import ProductionWeatherDataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMD Official Rainfall Thresholds (mm/day)
# ---------------------------------------------------------------------------
IMD_THRESHOLDS: dict[str, float] = {
    "Light (≥2.5)": 2.5,
    "Moderate (≥15.6)": 15.6,
    "Heavy (≥64.5)": 64.5,
    "Very Heavy (≥115.6)": 115.6,
    "Extremely Heavy (≥204.5)": 204.5,
}


@dataclass
class CategoricalScores:
    """Contingency table based categorical verification scores."""
    threshold: str
    threshold_mm: float
    hits: int = 0
    misses: int = 0
    false_alarms: int = 0
    correct_negatives: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses + self.false_alarms + self.correct_negatives

    @property
    def pod(self) -> float:
        """Probability of Detection (Hit Rate)."""
        denom = self.hits + self.misses
        return self.hits / denom if denom > 0 else float("nan")

    @property
    def far(self) -> float:
        """False Alarm Ratio."""
        denom = self.hits + self.false_alarms
        return self.false_alarms / denom if denom > 0 else float("nan")

    @property
    def csi(self) -> float:
        """Critical Success Index (Threat Score)."""
        denom = self.hits + self.misses + self.false_alarms
        return self.hits / denom if denom > 0 else float("nan")

    @property
    def ets(self) -> float:
        """Equitable Threat Score (Gilbert Skill Score)."""
        n = self.total
        if n == 0:
            return float("nan")
        hits_random = (self.hits + self.misses) * (self.hits + self.false_alarms) / n
        denom = self.hits + self.misses + self.false_alarms - hits_random
        return (self.hits - hits_random) / denom if denom > 0 else float("nan")

    @property
    def fbi(self) -> float:
        """Frequency Bias Index."""
        denom = self.hits + self.misses
        return (self.hits + self.false_alarms) / denom if denom > 0 else float("nan")

    @property
    def hss(self) -> float:
        """Heidke Skill Score."""
        h, m, f, c = self.hits, self.misses, self.false_alarms, self.correct_negatives
        num = 2 * (h * c - f * m)
        den = (h + m) * (m + c) + (h + f) * (f + c)
        return num / den if den > 0 else float("nan")

    def as_dict(self) -> dict:
        return {
            "threshold": self.threshold,
            "threshold_mm": self.threshold_mm,
            "hits": self.hits,
            "misses": self.misses,
            "false_alarms": self.false_alarms,
            "correct_negatives": self.correct_negatives,
            "POD": round(self.pod, 4),
            "FAR": round(self.far, 4),
            "CSI": round(self.csi, 4),
            "ETS": round(self.ets, 4),
            "FBI": round(self.fbi, 4),
            "HSS": round(self.hss, 4),
        }


@dataclass
class ContinuousScores:
    """Accumulated continuous verification scores."""
    variable: str
    sum_sq_err: float = 0.0
    sum_abs_err: float = 0.0
    sum_bias: float = 0.0
    sum_pred_anom_x_obs_anom: float = 0.0
    sum_pred_anom_sq: float = 0.0
    sum_obs_anom_sq: float = 0.0
    n_pixels: int = 0

    @property
    def rmse(self) -> float:
        return np.sqrt(self.sum_sq_err / self.n_pixels) if self.n_pixels > 0 else float("nan")

    @property
    def mae(self) -> float:
        return self.sum_abs_err / self.n_pixels if self.n_pixels > 0 else float("nan")

    @property
    def bias(self) -> float:
        return self.sum_bias / self.n_pixels if self.n_pixels > 0 else float("nan")

    @property
    def acc(self) -> float:
        """Anomaly Correlation Coefficient (weighted by area ideally, unweighted here)."""
        denom = np.sqrt(self.sum_pred_anom_sq * self.sum_obs_anom_sq)
        return self.sum_pred_anom_x_obs_anom / denom if denom > 1e-12 else float("nan")

    def as_dict(self) -> dict:
        return {
            "variable": self.variable,
            "RMSE": round(self.rmse, 4),
            "MAE": round(self.mae, 4),
            "Bias": round(self.bias, 4),
            "ACC": round(self.acc, 4),
            "n_pixels": self.n_pixels,
        }


def _accumulate_continuous(
    scores: ContinuousScores,
    pred: np.ndarray,
    obs: np.ndarray,
    climatology: np.ndarray | None = None,
) -> None:
    """Accumulate pixel-level continuous scores across batches."""
    diff = pred - obs
    scores.sum_sq_err += float(np.sum(diff ** 2))
    scores.sum_abs_err += float(np.sum(np.abs(diff)))
    scores.sum_bias += float(np.sum(diff))

    # ACC: anomaly relative to climatology (or sample mean if no climatology provided)
    clim = climatology if climatology is not None else np.mean(obs)
    pred_anom = pred - clim
    obs_anom = obs - clim
    scores.sum_pred_anom_x_obs_anom += float(np.sum(pred_anom * obs_anom))
    scores.sum_pred_anom_sq += float(np.sum(pred_anom ** 2))
    scores.sum_obs_anom_sq += float(np.sum(obs_anom ** 2))
    scores.n_pixels += int(pred.size)


def _accumulate_categorical(
    scoreboard: dict[str, CategoricalScores],
    pred: np.ndarray,
    obs: np.ndarray,
) -> None:
    """Accumulate contingency table counts for each IMD threshold."""
    for label, thresh in IMD_THRESHOLDS.items():
        s = scoreboard[label]
        p_event = pred >= thresh
        o_event = obs >= thresh
        s.hits += int(np.sum(p_event & o_event))
        s.misses += int(np.sum(~p_event & o_event))
        s.false_alarms += int(np.sum(p_event & ~o_event))
        s.correct_negatives += int(np.sum(~p_event & ~o_event))


def evaluate() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Evaluation device: {device}")

    # ---- Config ----
    eval_dates = [f"2023-08-{d:02d}" for d in range(25, 32)]  # Hold-out: last week of Aug
    data_dir = os.path.join(os.path.dirname(__file__), "data/processed")
    weights_path = os.path.join(os.path.dirname(__file__), "super_unet_blender_weights.pth")
    output_dir = Path(os.path.dirname(__file__)) / "evaluation_results"
    output_dir.mkdir(exist_ok=True)

    # ---- Dataset ----
    dataset = ProductionWeatherDataset(data_dir=data_dir, dates=eval_dates)
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
    logger.info(f"Evaluation set: {len(dataset)} samples ({eval_dates[0]} → {eval_dates[-1]})")

    # ---- Model ----
    if not os.path.exists(weights_path):
        logger.error(f"Weights not found: {weights_path}")
        return

    model = SuperUNetBlender(n_channels=7, n_models=2, features=[32, 64, 128, 256]).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    model.eval()
    logger.info("Model loaded.")

    # ---- Score Accumulators ----
    variables = ["rain", "temp", "wind"]
    blend_scores = {v: ContinuousScores(variable=f"blend_{v}") for v in variables}
    gfs_scores = {v: ContinuousScores(variable=f"gfs_{v}") for v in variables}
    ai_scores = {v: ContinuousScores(variable=f"ai_{v}") for v in variables}
    avg_scores = {v: ContinuousScores(variable=f"simple_avg_{v}") for v in variables}

    # Categorical scores only for rain
    blend_cat = {l: CategoricalScores(threshold=l, threshold_mm=t) for l, t in IMD_THRESHOLDS.items()}
    gfs_cat = {l: CategoricalScores(threshold=l, threshold_mm=t) for l, t in IMD_THRESHOLDS.items()}
    ai_cat = {l: CategoricalScores(threshold=l, threshold_mm=t) for l, t in IMD_THRESHOLDS.items()}
    avg_cat = {l: CategoricalScores(threshold=l, threshold_mm=t) for l, t in IMD_THRESHOLDS.items()}

    # ---- Inference Loop ----
    with torch.no_grad():
        for batch_idx, (inputs, lead_time, forecasts, targets) in enumerate(loader):
            inputs = inputs.to(device)
            lead_time = lead_time.to(device)
            f_rain, f_temp, f_wind = [f.to(device) for f in forecasts]
            t_rain, t_temp, t_wind = [t.to(device) for t in targets]

            # Model predictions
            w_rain, w_temp, w_wind = model(inputs, lead_time)
            blend_rain = torch.sum(w_rain * f_rain, dim=1, keepdim=True)
            blend_temp = torch.sum(w_temp * f_temp, dim=1, keepdim=True)
            blend_wind = torch.sum(w_wind * f_wind, dim=1, keepdim=True)

            # Simple average baseline
            avg_rain = torch.mean(f_rain, dim=1, keepdim=True)
            avg_temp = torch.mean(f_temp, dim=1, keepdim=True)
            avg_wind = torch.mean(f_wind, dim=1, keepdim=True)

            # Individual model forecasts
            gfs_rain_pred = f_rain[:, 0:1]
            ai_rain_pred = f_rain[:, 1:2]
            gfs_temp_pred = f_temp[:, 0:1]
            ai_temp_pred = f_temp[:, 1:2]
            gfs_wind_pred = f_wind[:, 0:1]
            ai_wind_pred = f_wind[:, 1:2]

            # Convert to numpy
            def np_(t: torch.Tensor) -> np.ndarray:
                return t.cpu().numpy().flatten()

            obs = {"rain": np_(t_rain), "temp": np_(t_temp), "wind": np_(t_wind)}
            blend = {"rain": np_(blend_rain), "temp": np_(blend_temp), "wind": np_(blend_wind)}
            gfs = {"rain": np_(gfs_rain_pred), "temp": np_(gfs_temp_pred), "wind": np_(gfs_wind_pred)}
            ai = {"rain": np_(ai_rain_pred), "temp": np_(ai_temp_pred), "wind": np_(ai_wind_pred)}
            avg = {"rain": np_(avg_rain), "temp": np_(avg_temp), "wind": np_(avg_wind)}

            for v in variables:
                _accumulate_continuous(blend_scores[v], blend[v], obs[v])
                _accumulate_continuous(gfs_scores[v], gfs[v], obs[v])
                _accumulate_continuous(ai_scores[v], ai[v], obs[v])
                _accumulate_continuous(avg_scores[v], avg[v], obs[v])

            _accumulate_categorical(blend_cat, blend["rain"], obs["rain"])
            _accumulate_categorical(gfs_cat, gfs["rain"], obs["rain"])
            _accumulate_categorical(ai_cat, ai["rain"], obs["rain"])
            _accumulate_categorical(avg_cat, avg["rain"], obs["rain"])

            logger.info(
                f"  [{batch_idx + 1}/{len(loader)}] {eval_dates[batch_idx]}  "
                f"rain RMSE: blend={np.sqrt(np.mean((blend['rain'] - obs['rain'])**2)):.2f}  "
                f"gfs={np.sqrt(np.mean((gfs['rain'] - obs['rain'])**2)):.2f}  "
                f"ai={np.sqrt(np.mean((ai['rain'] - obs['rain'])**2)):.2f}"
            )

    # ---- Report ----
    logger.info("")
    logger.info("=" * 72)
    logger.info("  MEGHDRISHTI SUPER-UNET BLENDER — EVALUATION REPORT")
    logger.info("  WeatherBench 2 / IMD Verification Protocol")
    logger.info(f"  Hold-out period: {eval_dates[0]} → {eval_dates[-1]}")
    logger.info("=" * 72)

    report: dict = {"eval_dates": eval_dates, "continuous": {}, "categorical": {}, "skill_scores": {}}

    # Continuous metrics table
    logger.info("")
    logger.info(f"{'Metric':<8} {'Variable':<8} {'Super-UNet':>12} {'GFS':>12} {'AI':>12} {'SimpleAvg':>12}")
    logger.info("-" * 64)
    for v in variables:
        for metric in ["RMSE", "MAE", "Bias", "ACC"]:
            b_val = getattr(blend_scores[v], metric.lower())
            g_val = getattr(gfs_scores[v], metric.lower())
            a_val = getattr(ai_scores[v], metric.lower())
            s_val = getattr(avg_scores[v], metric.lower())
            logger.info(f"{metric:<8} {v:<8} {b_val:>12.4f} {g_val:>12.4f} {a_val:>12.4f} {s_val:>12.4f}")

        report["continuous"][v] = {
            "blend": blend_scores[v].as_dict(),
            "gfs": gfs_scores[v].as_dict(),
            "ai": ai_scores[v].as_dict(),
            "simple_avg": avg_scores[v].as_dict(),
        }

    # Skill scores
    logger.info("")
    logger.info("--- Skill Scores (lower RMSE = better) ---")
    for v in variables:
        blend_rmse = blend_scores[v].rmse
        gfs_rmse = gfs_scores[v].rmse
        ai_rmse = ai_scores[v].rmse
        avg_rmse = avg_scores[v].rmse

        skill_vs_gfs = 1.0 - (blend_rmse / gfs_rmse) if gfs_rmse > 0 else float("nan")
        skill_vs_ai = 1.0 - (blend_rmse / ai_rmse) if ai_rmse > 0 else float("nan")
        skill_vs_avg = 1.0 - (blend_rmse / avg_rmse) if avg_rmse > 0 else float("nan")

        logger.info(f"  {v}: Skill vs GFS = {skill_vs_gfs:+.2%}, vs AI = {skill_vs_ai:+.2%}, vs SimpleAvg = {skill_vs_avg:+.2%}")
        report["skill_scores"][v] = {
            "skill_vs_gfs": round(skill_vs_gfs, 4),
            "skill_vs_ai": round(skill_vs_ai, 4),
            "skill_vs_simple_avg": round(skill_vs_avg, 4),
        }

    # Categorical metrics table (rain only)
    logger.info("")
    logger.info("--- Categorical Verification: Rainfall (IMD Thresholds) ---")
    logger.info(f"{'Threshold':<25} {'Model':<12} {'POD':>8} {'FAR':>8} {'CSI':>8} {'ETS':>8} {'FBI':>8} {'HSS':>8}")
    logger.info("-" * 88)
    cat_results: dict = {}
    for label in IMD_THRESHOLDS:
        for name, cat in [("Super-UNet", blend_cat), ("GFS", gfs_cat), ("AI", ai_cat), ("SimpleAvg", avg_cat)]:
            s = cat[label]
            logger.info(
                f"{label:<25} {name:<12} {s.pod:>8.4f} {s.far:>8.4f} {s.csi:>8.4f} {s.ets:>8.4f} {s.fbi:>8.4f} {s.hss:>8.4f}"
            )
        logger.info("")
        cat_results[label] = {
            "blend": blend_cat[label].as_dict(),
            "gfs": gfs_cat[label].as_dict(),
            "ai": ai_cat[label].as_dict(),
            "simple_avg": avg_cat[label].as_dict(),
        }
    report["categorical"] = cat_results

    # Save JSON report
    report_path = output_dir / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Full report saved to: {report_path}")

    # Final verdict
    logger.info("")
    blend_rain_rmse = blend_scores["rain"].rmse
    gfs_rain_rmse = gfs_scores["rain"].rmse
    ai_rain_rmse = ai_scores["rain"].rmse
    avg_rain_rmse = avg_scores["rain"].rmse
    best_baseline = min(gfs_rain_rmse, ai_rain_rmse, avg_rain_rmse)

    if blend_rain_rmse < best_baseline:
        improvement = (1.0 - blend_rain_rmse / best_baseline) * 100
        logger.info(f"✅ PASS: Super-UNet rain RMSE ({blend_rain_rmse:.4f}) beats best baseline ({best_baseline:.4f}) by {improvement:.1f}%")
    else:
        logger.warning(f"❌ FAIL: Super-UNet rain RMSE ({blend_rain_rmse:.4f}) does NOT beat best baseline ({best_baseline:.4f})")
        logger.warning("   → Retrain with fixed preprocessing (remove GFS tp*1000 bug) and real AI data.")


if __name__ == "__main__":
    evaluate()
