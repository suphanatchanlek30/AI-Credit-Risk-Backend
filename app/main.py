from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.api.v1 import router as api_v1_router
from app.db.repository import create_prediction_log, list_prediction_logs
from app.db.session import create_tables, db_ping, get_db
from app.ml.model_bundle import load_bundle
from app.ml.preprocessing import preprocess_for_inference, sanitize_payload

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "application_model_v1"
THAI_ALIAS_PATH = ROOT / "config" / "thai_alias.json"
CATALOG_PATH = ROOT / "config" / "input_catalog_th.json"
DESC_PATH = ROOT / "input" / "home-credit-default-risk (1)" / "HomeCredit_columns_description.csv"

app = FastAPI(
    title="Home Credit Risk API",
    description="รับข้อมูลลูกค้า, preprocess, และพยากรณ์ความเสี่ยงผิดนัด (TARGET=1).",
    version="1.0.0",
)


def _get_cors_origins() -> list[str]:
    env_origins = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_v1_router)


class PredictRequest(BaseModel):
    payload: dict[str, Any] | list[dict[str, Any]] = Field(
        ...,
        description="ข้อมูลลูกค้า 1 รายการหรือหลายรายการ (ส่ง key อังกฤษหรือไทยก็ได้ถ้ามี mapping)",
    )
    threshold: float = Field(0.5, ge=0.0, le=1.0, description="เกณฑ์ตัดสินเสี่ยงผิดนัด")

    @field_validator("payload")
    @classmethod
    def validate_payload_not_empty(
        cls, value: dict[str, Any] | list[dict[str, Any]]
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if isinstance(value, dict) and not value:
            raise ValueError("payload ห้ามว่าง")
        if isinstance(value, list) and len(value) == 0:
            raise ValueError("payload list ห้ามว่าง")
        return value


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    predictions: list[dict[str, Any]]
    model_version: str


def _load_alias_map() -> dict[str, str]:
    if not THAI_ALIAS_PATH.exists():
        return {}
    with THAI_ALIAS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _translate_payload(payload: dict[str, Any], alias_map: dict[str, str]) -> dict[str, Any]:
    translated: dict[str, Any] = {}
    for key, value in payload.items():
        translated[alias_map.get(key, key)] = value
    return translated


def _load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {}
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.on_event("startup")
def on_startup() -> None:
    if not ARTIFACT_DIR.exists():
        raise RuntimeError(
            f"Model bundle not found at {ARTIFACT_DIR}. "
            "Run: py scripts/train_application_model.py (or python)."
        )
    app.state.model, app.state.artifacts, app.state.metrics = load_bundle(ARTIFACT_DIR)
    app.state.alias_map = _load_alias_map()
    app.state.catalog = _load_catalog()
    create_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-health")
def db_health() -> dict[str, Any]:
    return {"db_connected": db_ping()}


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    return {
        "model_version": "application_model_v1",
        "metrics": app.state.metrics,
        "num_raw_fields": len(app.state.artifacts.raw_feature_columns),
        "num_model_features": len(app.state.artifacts.feature_columns),
        "num_raw_numeric_fields": len(app.state.artifacts.raw_numeric_columns),
        "num_raw_categorical_fields": len(app.state.artifacts.raw_categorical_columns),
    }


@app.get("/input-template")
def input_template() -> dict[str, Any]:
    sample = {k: None for k in app.state.artifacts.raw_feature_columns}
    descriptions: dict[str, str] = {}
    if DESC_PATH.exists():
        desc_df = pd.read_csv(DESC_PATH)
        for _, row in desc_df.iterrows():
            col = str(row.get("Row", "")).strip()
            desc = str(row.get("Description", "")).strip()
            if col:
                descriptions[col] = desc
    return {
        "template": sample,
        "description_by_field": descriptions,
        "thai_alias_available": bool(app.state.alias_map),
    }


@app.get("/input-catalog")
def input_catalog() -> dict[str, Any]:
    if app.state.catalog:
        return app.state.catalog
    return {
        "message": "catalog not found",
        "path": str(CATALOG_PATH),
    }


@app.get("/input-summary")
def input_summary() -> dict[str, Any]:
    catalog = app.state.catalog if isinstance(app.state.catalog, dict) else {}
    minimum_fields = catalog.get("minimum_web_form_fields", [])
    extended_fields = catalog.get("recommended_extended_fields", [])
    field_catalog = catalog.get("field_catalog", [])
    return {
        "payload_modes": ["single_object", "array_of_objects"],
        "threshold_supported": True,
        "raw_input_field_count_from_model": len(app.state.artifacts.raw_feature_columns),
        "minimum_web_form_field_count": len(minimum_fields),
        "recommended_extended_field_count": len(extended_fields),
        "catalog_field_count": len(field_catalog),
        "minimum_web_form_fields": minimum_fields,
        "recommended_extended_fields": extended_fields,
    }


@app.get("/predictions")
def prediction_logs(limit: int = 20, db: Session = Depends(get_db)) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    rows = list_prediction_logs(db, limit=limit)
    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "model_version": r.model_version,
                "threshold": r.threshold,
                "client_ip": r.client_ip,
                "predictions": r.predictions,
            }
            for r in rows
        ],
    }


@app.post("/predict", response_model=PredictResponse)
def predict(
    req: PredictRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> PredictResponse:
    rows = req.payload if isinstance(req.payload, list) else [req.payload]
    translated_rows = []
    for row in rows:
        clean_payload = sanitize_payload(row)
        translated_rows.append(_translate_payload(clean_payload, app.state.alias_map))

    row_df = pd.DataFrame(translated_rows)
    X = preprocess_for_inference(row_df, app.state.artifacts)
    probs = app.state.model.predict(X)

    predictions: list[dict[str, Any]] = []
    for idx, prob in enumerate(probs):
        prob_f = float(prob)
        is_default_risk = prob_f >= req.threshold
        decision = "เสี่ยงผิดนัด" if is_default_risk else "ความเสี่ยงต่ำกว่าเกณฑ์"
        decision_en = "default_risk" if is_default_risk else "below_threshold"
        if prob_f >= 0.7:
            risk_band = "สูง"
            risk_band_en = "high"
        elif prob_f >= 0.4:
            risk_band = "กลาง"
            risk_band_en = "medium"
        else:
            risk_band = "ต่ำ"
            risk_band_en = "low"
        predictions.append(
            {
                "index": idx,
                "default_probability": round(prob_f, 6),
                "decision": decision,
                "decision_en": decision_en,
                "risk_band": risk_band,
                "risk_band_en": risk_band_en,
                "threshold": req.threshold,
            }
        )

    row = create_prediction_log(
        db,
        model_version="application_model_v1",
        threshold=req.threshold,
        client_ip=request.client.host if request.client else None,
        request_payload=req.payload,
        translated_payload=translated_rows,
        predictions=predictions,
    )
    for pred in predictions:
        pred["request_id"] = row.id

    return PredictResponse(
        predictions=predictions,
        model_version="application_model_v1",
    )
