"""
Tests for NOAA S3 Byte-Range Fetcher and Live Ingestion Fallbacks.
"""
import numpy as np
import pytest
from app.services.noaa_s3_fetcher import NOAAByteRangeFetcher
from app.services.operational_ai_fetcher import OperationalAIFetcher
from app.services.data_source import load_inputs

def test_operational_ai_fallback():
    fetcher = OperationalAIFetcher()
    mock_gfs = {
        "rain": np.zeros((128, 128), dtype=np.float32),
        "temp": np.full((128, 128), 295.0, dtype=np.float32),
        "wind": np.full((128, 128), 5.0, dtype=np.float32)
    }
    ai_fields = fetcher.fetch_ai_india("2026-10-01", 24, gfs_reference=mock_gfs)
    assert ai_fields is not None
    assert "rain" in ai_fields and "temp" in ai_fields and "wind" in ai_fields
    assert ai_fields["rain"].shape == (128, 128)
    assert ai_fields["temp"].shape == (128, 128)
    assert ai_fields["wind"].shape == (128, 128)

def test_load_inputs_live_or_fallback():
    # Calling load_inputs for today should return valid ForecastInputs without crashing
    inputs = load_inputs("2026-10-01", 24)
    assert inputs.gfs.rain.shape == (128, 128)
    assert inputs.ai.rain.shape == (128, 128)
    assert inputs.dem.shape == (128, 128)
    assert inputs.source in ["live_noaa_s3", "synthetic", "processed"]
