import numpy as np

from app.services.data_source import load_inputs


def test_synthetic_inputs_are_deterministic() -> None:
    a = load_inputs("2099-01-01", 24)
    b = load_inputs("2099-01-01", 24)
    assert a.source == "synthetic"
    np.testing.assert_array_equal(a.gfs.rain, b.gfs.rain)
    np.testing.assert_array_equal(a.ai.temp, b.ai.temp)


def test_synthetic_inputs_have_model_grid_shape_and_units() -> None:
    inputs = load_inputs("2099-01-01", 48)
    for field in (inputs.gfs, inputs.ai):
        for grid in (field.rain, field.temp, field.wind):
            assert grid.shape == (128, 128) and grid.dtype == np.float32
        assert field.rain.min() >= 0.0
        assert 230.0 < field.temp.mean() < 320.0  # Kelvin
    assert inputs.dem.max() > 3000.0  # Himalaya present
