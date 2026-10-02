from typing import Literal

from pydantic import BaseModel

Variable = Literal["rain", "temp", "wind"]
Layer = Literal["blended", "gfs", "ai", "trust"]
DataSource = Literal["processed", "synthetic", "live_noaa_s3"]
WeightsMode = Literal["trained", "untrained"]
ImdCategory = Literal["heavy", "very_heavy", "extremely_heavy"]
WindCategory = Literal["strong_wind", "gale", "storm"]
HeatCategory = Literal["heat_watch", "heatwave", "severe_heatwave"]
ThreatCategory = ImdCategory | WindCategory | HeatCategory


class RunInfo(BaseModel):
    date: str
    lead_time: int
    lead_time_validated: bool
    data_source: DataSource
    weights: WeightsMode


class LayerMetadata(RunInfo):
    variable: Variable
    layer: Layer
    units: str
    min: float
    max: float
    stride: int
    cell_count: int


class ForecastGrid(BaseModel):
    """Full-resolution grid for raster rendering. Row 0 = northern edge; values are row-major."""
    metadata: LayerMetadata
    lat_north: float
    lat_south: float
    lon_west: float
    lon_east: float
    rows: int
    cols: int
    values: list[float]


class Threat(BaseModel):
    id: str
    variable: Variable
    units: str  # mm (rain), km/h (wind), °C (temp)
    district: str
    state: str
    distance_km: float  # from the district HQ to the peak cell
    lat: float
    lon: float
    peak: float
    mean: float
    area_km2: float
    category: ThreatCategory
    level: int  # 1-3 within the hazard's scale (e.g. heavy / very heavy / extremely heavy)
    severity_rank: int
    gfs_value: float  # raw GFS value at the blended peak
    ai_value: float  # raw AI value at the blended peak
    gfs_trust: float  # U-Net GFS weight at the peak (XAI)
    population_exposed: int  # Census 2011 state density x affected land area
    risk_index: int  # 0-100, intensity x exposure


class AlertsResponse(BaseModel):
    metadata: RunInfo
    threats: list[Threat]


class VariableInfo(BaseModel):
    id: Variable
    label: str
    units: str


class MetaResponse(BaseModel):
    dates: list[str]
    lead_times: list[int]
    trained_lead_times: list[int]
    variables: list[VariableInfo]
    layers: list[Layer]
    bbox: list[float]  # [south, west, north, east]
    data_source: DataSource
    weights: WeightsMode


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    weights: WeightsMode
    device: str
