import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["model_loaded"] is True


def test_meta(client: TestClient) -> None:
    body = client.get("/api/v1/forecast/meta").json()
    assert body["dates"] and 24 in body["lead_times"]
    assert body["bbox"] == [8.0, 68.0, 38.0, 98.0]


def test_blended_geojson(client: TestClient) -> None:
    res = client.get("/api/v1/forecast/blended", params={"date": "2023-08-15", "stride": 4})
    assert res.status_code == 200
    body = res.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 32 * 32
    meta = body["metadata"]
    assert meta["units"] == "mm" and meta["lead_time_validated"] is True
    assert meta["cell_count"] == len(body["features"])


def test_grid_endpoint_shape(client: TestClient) -> None:
    body = client.get("/api/v1/forecast/grid", params={"date": "2023-08-15", "variable": "wind"}).json()
    assert body["rows"] * body["cols"] == len(body["values"]) == 128 * 128
    assert body["lat_north"] > body["lat_south"] and body["metadata"]["units"] == "m/s"


def test_trust_layer_in_unit_range(client: TestClient) -> None:
    body = client.get("/api/v1/forecast/blended",
                      params={"date": "2023-08-15", "layer": "trust", "stride": 8}).json()
    values = [f["properties"]["v"] for f in body["features"]]
    assert 0.0 <= min(values) and max(values) <= 1.0


def test_temperature_is_celsius(client: TestClient) -> None:
    meta = client.get("/api/v1/forecast/blended",
                      params={"date": "2023-08-15", "variable": "temp", "stride": 8}).json()["metadata"]
    assert meta["units"] == "°C" and -40.0 < meta["min"] < meta["max"] < 50.0


def test_untrained_lead_time_is_flagged(client: TestClient) -> None:
    meta = client.get("/api/v1/forecast/blended",
                      params={"date": "2023-08-15", "lead_time": 72, "stride": 8}).json()["metadata"]
    assert meta["lead_time_validated"] is False


def test_alerts_ranked_by_peak(client: TestClient) -> None:
    body = client.get("/api/v1/forecast/alerts", params={"date": "2023-08-27"}).json()
    peaks = [t["peak"] for t in body["threats"]]
    assert peaks and peaks == sorted(peaks, reverse=True)
    assert all(p >= 64.5 for p in peaks)
    assert all(t["variable"] == "rain" and t["units"] == "mm" for t in body["threats"])
    assert all(0 <= t["risk_index"] <= 100 and t["population_exposed"] >= 0 for t in body["threats"])


@pytest.mark.parametrize(("variable", "units", "floor", "categories"), [
    ("wind", "km/h", 40.0, {"strong_wind", "gale", "storm"}),
    ("temp", "°C", 28.0, {"heat_watch", "heatwave", "severe_heatwave"}),
])
def test_wind_and_heat_alerts(client: TestClient, variable: str, units: str, floor: float,
                              categories: set[str]) -> None:
    body = client.get("/api/v1/forecast/alerts", params={"date": "2023-08-27", "variable": variable}).json()
    threats = body["threats"]
    assert threats, f"expected {variable} threats in the synthetic scenario"
    peaks = [t["peak"] for t in threats]
    assert peaks == sorted(peaks, reverse=True) and min(peaks) >= floor
    assert all(t["units"] == units and t["category"] in categories and 1 <= t["level"] <= 3 for t in threats)


@pytest.mark.parametrize("params", [
    {"variable": "snow"}, {"layer": "x"}, {"lead_time": 6}, {"stride": 0}, {"date": "15-08-2023"},
])
def test_invalid_params_rejected(client: TestClient, params: dict) -> None:
    assert client.get("/api/v1/forecast/blended", params=params).status_code == 422
