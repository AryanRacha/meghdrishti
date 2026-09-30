"""Singleton Super-UNet inference engine: loads weights once, blends GFS + AI grids."""
import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Literal

import numpy as np
import torch

from app.core.config import settings
from app.ml.unet_blender import SuperUNetBlender
from app.services.data_source import DataSource, ModelFields, load_inputs

logger = logging.getLogger(__name__)

WeightsMode = Literal["trained", "untrained"]


@dataclass(frozen=True)
class BlendResult:
    date: str
    lead_time: int
    source: DataSource
    gfs: ModelFields
    ai: ModelFields
    blended: ModelFields
    trust: ModelFields  # GFS weight in [0, 1]; AI weight = 1 - trust
    dem: np.ndarray


def _normalize(t: torch.Tensor) -> torch.Tensor:
    # Must match ProductionWeatherDataset._normalize (per-sample, per-channel z-score)
    return (t - t.mean()) / (t.std() + 1e-8)


class InferenceEngine:
    _instance: "InferenceEngine | None" = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self.device = self._resolve_device()
        self.model = SuperUNetBlender(
            n_channels=settings.N_CHANNELS, n_models=settings.N_MODELS, features=settings.FEATURES
        ).to(self.device)
        self.weights_mode: WeightsMode = self._load_weights()
        self.model.eval()
        self._cache: OrderedDict[tuple[str, int], BlendResult] = OrderedDict()
        self._lock = threading.Lock()

    @classmethod
    def get(cls) -> "InferenceEngine":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @staticmethod
    def _resolve_device() -> torch.device:
        if settings.DEVICE == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(settings.DEVICE)

    def _load_weights(self) -> WeightsMode:
        path = settings.WEIGHTS_PATH
        if not path.is_file():
            logger.warning("Weights not found at %s; serving UNTRAINED model.", path)
            return "untrained"
        state = torch.load(path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)
        logger.info("Loaded Super-UNet weights from %s on %s", path, self.device)
        return "trained"

    def predict(self, date: str, lead_time: int) -> BlendResult:
        key = (date, lead_time)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]

            result = self._run(date, lead_time)
            self._cache[key] = result
            if len(self._cache) > settings.INFERENCE_CACHE_SIZE:
                self._cache.popitem(last=False)
            return result

    @torch.inference_mode()
    def _run(self, date: str, lead_time: int) -> BlendResult:
        inputs = load_inputs(date, lead_time)
        gfs, ai = inputs.gfs, inputs.ai

        channels = [gfs.rain, gfs.temp, gfs.wind, ai.rain, ai.temp, ai.wind, inputs.dem]
        x = torch.stack([_normalize(torch.from_numpy(c)) for c in channels]).unsqueeze(0).to(self.device)
        lt = torch.tensor([[float(lead_time)]], dtype=torch.float32, device=self.device)

        w_rain, w_temp, w_wind = (w[0].float().cpu().numpy() for w in self.model(x, lt))

        def blend(w: np.ndarray, g: np.ndarray, a: np.ndarray) -> np.ndarray:
            return (w[0] * g + w[1] * a).astype(np.float32)

        return BlendResult(
            date=date,
            lead_time=lead_time,
            source=inputs.source,
            gfs=gfs,
            ai=ai,
            blended=ModelFields(
                rain=blend(w_rain, gfs.rain, ai.rain),
                temp=blend(w_temp, gfs.temp, ai.temp),
                wind=blend(w_wind, gfs.wind, ai.wind),
            ),
            trust=ModelFields(rain=w_rain[0], temp=w_temp[0], wind=w_wind[0]),
            dem=inputs.dem,
        )
