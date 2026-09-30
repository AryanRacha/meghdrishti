from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26081 Weather API"
    API_V1_STR: str = "/api/v1"

    WEIGHTS_PATH: Path = BACKEND_DIR / "weights" / "super_unet_blender_weights.pth"
    PROCESSED_DATA_DIR: Path = REPO_DIR / "ml_pipeline" / "data" / "processed"
    DEVICE: str = "auto"  # "auto" | "cpu" | "cuda"

    # Indian bounding box (AGENTS.md rule 4) and model grid
    LAT_NORTH: float = 38.0
    LAT_SOUTH: float = 8.0
    LON_WEST: float = 68.0
    LON_EAST: float = 98.0
    GRID_SIZE: int = 128

    # Model hyper-parameters used in ml_pipeline/train.py
    N_CHANNELS: int = 7
    N_MODELS: int = 2
    FEATURES: list[int] = [32, 64, 128, 256]
    TRAINED_LEAD_TIMES: list[int] = [24]

    INFERENCE_CACHE_SIZE: int = 32

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
