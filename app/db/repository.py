from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import PredictionLog


def create_prediction_log(
    db: Session,
    *,
    model_version: str,
    threshold: float,
    client_ip: str | None,
    request_payload: dict[str, Any] | list[dict[str, Any]],
    translated_payload: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> PredictionLog:
    row = PredictionLog(
        model_version=model_version,
        threshold=threshold,
        client_ip=client_ip,
        request_payload=request_payload if isinstance(request_payload, dict) else {"batch": request_payload},
        translated_payload=translated_payload,
        predictions=predictions,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_prediction_logs(db: Session, limit: int = 50) -> list[PredictionLog]:
    stmt = select(PredictionLog).order_by(desc(PredictionLog.id)).limit(limit)
    return list(db.scalars(stmt).all())
