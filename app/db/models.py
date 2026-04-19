from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.session import DATABASE_URL

JSONType = JSONB if DATABASE_URL.startswith("postgresql") else JSON


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    translated_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, nullable=False)
    predictions: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, nullable=False)
