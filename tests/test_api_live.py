from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import requests


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parents[1]


def _get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=20)


def _post(path: str, payload: dict) -> requests.Response:
    return requests.post(
        f"{BASE_URL}{path}",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )


@pytest.fixture(scope="session")
def ensure_server_up() -> None:
    try:
        res = _get("/health")
        if res.status_code != 200:
            pytest.skip(f"API not ready: {res.status_code}")
    except Exception as exc:
        pytest.skip(f"API not reachable at {BASE_URL}: {exc}")


def test_health(ensure_server_up: None) -> None:
    res = _get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "ok"


def test_db_health(ensure_server_up: None) -> None:
    res = _get("/db-health")
    assert res.status_code == 200
    assert "db_connected" in res.json()


def test_model_info(ensure_server_up: None) -> None:
    res = _get("/model-info")
    assert res.status_code == 200
    data = res.json()
    assert "model_version" in data
    assert "metrics" in data


def test_input_endpoints(ensure_server_up: None) -> None:
    for path in ["/input-template", "/input-catalog", "/input-summary"]:
        res = _get(path)
        assert res.status_code == 200, f"{path} => {res.text}"


def test_predict_single_and_batch(ensure_server_up: None) -> None:
    single = json.loads((ROOT / "examples" / "predict_th_minimal.json").read_text(encoding="utf-8"))
    batch = json.loads((ROOT / "examples" / "predict_th_batch.json").read_text(encoding="utf-8"))

    res_single = _post("/predict", single)
    assert res_single.status_code == 200, res_single.text
    data_single = res_single.json()
    assert "predictions" in data_single and len(data_single["predictions"]) == 1
    assert "decision_en" in data_single["predictions"][0]
    assert "risk_band_en" in data_single["predictions"][0]

    res_batch = _post("/predict", batch)
    assert res_batch.status_code == 200, res_batch.text
    data_batch = res_batch.json()
    assert len(data_batch["predictions"]) == len(batch["payload"])


def test_prediction_logs(ensure_server_up: None) -> None:
    res = _get("/predictions?limit=3")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
