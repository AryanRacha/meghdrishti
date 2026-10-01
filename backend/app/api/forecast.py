from datetime import date as Date

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.forecast import (
    AlertsResponse,
    ForecastGrid,
    Layer,
    LayerMetadata,
    MetaResponse,
    RunInfo,
    Variable,
    VariableInfo,
)
from app.services.data_source import available_dates
from app.services.inference_engine import BlendResult, InferenceEngine
from app.services.threat_detector import detect_threats
from app.utils.geojson_converter import grid_to_geojson

router = APIRouter(prefix="/forecast", tags=["forecast"])

LEAD_TIMES = [24, 48, 72, 96, 120]
KELVIN_OFFSET = 273.15

VARIABLES: dict[Variable, VariableInfo] = {
    "rain": VariableInfo(id="rain", label="Rainfall", units="mm"),
    "temp": VariableInfo(id="temp", label="Temperature", units="°C"),
    "wind": VariableInfo(id="wind", label="Wind speed", units="m/s"),
}

DateParam = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD; defaults to latest available")
LeadTimeParam = Query(24, ge=24, le=120, description="Forecast lead time in hours")


def _resolve_date(date: str | None) -> str:
    if date is None:
        return available_dates()[-1]
    try:
        Date.fromisoformat(date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid date: {date}") from exc
    return date


def _run_info(result: BlendResult, engine: InferenceEngine) -> RunInfo:
    return RunInfo(
        date=result.date,
        lead_time=result.lead_time,
        lead_time_validated=result.lead_time in settings.TRAINED_LEAD_TIMES,
        data_source=result.source,
        weights=engine.weights_mode,
    )


def _select_grid(result: BlendResult, variable: Variable, layer: Layer) -> tuple[np.ndarray, str]:
    fields = {"blended": result.blended, "gfs": result.gfs, "ai": result.ai, "trust": result.trust}[layer]
    grid = getattr(fields, variable)
    if layer == "trust":
        return grid, "GFS weight (0-1)"
    if variable == "temp":
        return grid - KELVIN_OFFSET, VARIABLES["temp"].units
    return grid, VARIABLES[variable].units


@router.get("/meta", response_model=MetaResponse)
def forecast_meta() -> MetaResponse:
    engine = InferenceEngine.get()
    dates = available_dates()
    source = "processed" if (settings.PROCESSED_DATA_DIR / f"{dates[-1]}.pt").is_file() else "synthetic"
    return MetaResponse(
        dates=dates,
        lead_times=LEAD_TIMES,
        trained_lead_times=settings.TRAINED_LEAD_TIMES,
        variables=list(VARIABLES.values()),
        layers=["blended", "gfs", "ai", "trust"],
        bbox=[settings.LAT_SOUTH, settings.LON_WEST, settings.LAT_NORTH, settings.LON_EAST],
        data_source=source,
        weights=engine.weights_mode,
    )


@router.get("/blended", summary="Forecast layer as a GeoJSON FeatureCollection")
def forecast_blended(
    date: str | None = DateParam,
    lead_time: int = LeadTimeParam,
    variable: Variable = "rain",
    layer: Layer = "blended",
    stride: int = Query(2, ge=1, le=8, description="Block down-sampling factor"),
    min_value: float | None = Query(None, description="Drop cells below this value"),
) -> JSONResponse:
    engine = InferenceEngine.get()
    result = engine.predict(_resolve_date(date), lead_time)
    grid, units = _select_grid(result, variable, layer)

    # Block max keeps cloudburst peaks visible when down-sampling rain
    how = "max" if variable == "rain" and layer != "trust" else "mean"
    collection = grid_to_geojson(grid, stride=stride, how=how, min_value=min_value,
                                 decimals=3 if layer == "trust" else 2)

    metadata = LayerMetadata(
        **_run_info(result, engine).model_dump(),
        variable=variable,
        layer=layer,
        units=units,
        min=round(float(np.nanmin(grid)), 3),
        max=round(float(np.nanmax(grid)), 3),
        stride=stride,
        cell_count=len(collection["features"]),
    )
    # "metadata" is a GeoJSON foreign member (RFC 7946 §6.1)
    return JSONResponse({**collection, "metadata": metadata.model_dump()})


@router.get("/grid", response_model=ForecastGrid, summary="Full-resolution grid for raster rendering")
def forecast_grid(
    date: str | None = DateParam,
    lead_time: int = LeadTimeParam,
    variable: Variable = "rain",
    layer: Layer = "blended",
) -> ForecastGrid:
    engine = InferenceEngine.get()
    result = engine.predict(_resolve_date(date), lead_time)
    grid, units = _select_grid(result, variable, layer)
    rows, cols = grid.shape
    return ForecastGrid(
        metadata=LayerMetadata(
            **_run_info(result, engine).model_dump(),
            variable=variable,
            layer=layer,
            units=units,
            min=round(float(np.nanmin(grid)), 3),
            max=round(float(np.nanmax(grid)), 3),
            stride=1,
            cell_count=rows * cols,
        ),
        lat_north=settings.LAT_NORTH,
        lat_south=settings.LAT_SOUTH,
        lon_west=settings.LON_WEST,
        lon_east=settings.LON_EAST,
        rows=rows,
        cols=cols,
        values=np.round(grid.astype(np.float64), 3 if layer == "trust" else 2).ravel().tolist(),
    )


@router.get("/alerts", response_model=AlertsResponse)
def forecast_alerts(
    date: str | None = DateParam,
    lead_time: int = LeadTimeParam,
    variable: Variable = "rain",
) -> AlertsResponse:
    engine = InferenceEngine.get()
    result = engine.predict(_resolve_date(date), lead_time)
    return AlertsResponse(metadata=_run_info(result, engine), threats=detect_threats(result, variable))
