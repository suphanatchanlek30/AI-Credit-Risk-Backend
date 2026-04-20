from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import (
    AssessmentStatusLog,
    LoanAssessment,
    PredictionLog,
    RecommendationTemplate,
    RiskFactor,
    RiskRecommendation,
    RiskResult,
    Role,
    User,
)


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


def get_prediction_log_by_id(db: Session, prediction_id: int) -> PredictionLog | None:
    stmt = select(PredictionLog).where(PredictionLog.id == prediction_id)
    return db.scalar(stmt)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _next_assessment_no(db: Session) -> str:
    count = db.scalar(select(func.count(LoanAssessment.id))) or 0
    return f"CR-{datetime.now(timezone.utc).year}-{count + 1:06d}"


def _ensure_system_user(db: Session) -> str:
    role = db.scalar(select(Role).where(Role.code == "SYSTEM"))
    if not role:
        role = Role(code="SYSTEM", name="System")
        db.add(role)
        db.flush()

    user = db.scalar(select(User).where(User.email == "system@local"))
    if not user:
        user = User(
            role_id=role.id,
            username="system",
            email="system@local",
            password_hash=hash_password("system-internal"),
            full_name="System Worker",
            status="ACTIVE",
            force_change_password=False,
        )
        db.add(user)
        db.flush()
    return user.id


def create_assessment_history_from_predict(
    db: Session,
    *,
    predictions: list[dict[str, Any]],
    model_version: str,
) -> list[str]:
    """
    Create assessment/result records from legacy /predict call.
    Returns created assessment IDs in same order as predictions.
    """
    created_ids: list[str] = []
    if not predictions:
        return created_ids

    created_by = _ensure_system_user(db)
    templates = db.scalars(select(RecommendationTemplate).where(RecommendationTemplate.is_active.is_(True))).all()
    templates_by_type_and_risk = {
        (t.recommendation_type, t.risk_level): t for t in templates
    }

    for idx, pred in enumerate(predictions):
        score = max(0.0, min(100.0, (1.0 - float(pred.get("default_probability", 1.0))) * 100.0))
        prob = float(pred.get("default_probability", 1.0))
        risk_level = str(pred.get("risk_band_en", "high")).upper()
        if risk_level not in {"LOW", "MEDIUM", "HIGH"}:
            risk_level = "HIGH"
        recommendation_type = "APPROVE" if risk_level == "LOW" else "REVIEW_MANUAL" if risk_level == "MEDIUM" else "REJECT"

        assessment = LoanAssessment(
            assessment_no=_next_assessment_no(db),
            created_by_user_id=created_by,
            status="COMPLETED",
            source_channel="API_PREDICT",
            current_step=4,
            submitted_at=_utc_now(),
            completed_at=_utc_now(),
            note="Auto-created from legacy /predict endpoint",
        )
        db.add(assessment)
        db.flush()

        result = RiskResult(
            assessment_id=assessment.id,
            result_version=1,
            model_version=model_version,
            score=round(score, 2),
            score_scale=100,
            credit_score=int(round(300 + score * 5.5)),
            score_grade="A" if score >= 85 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 45 else "E",
            default_probability=prob,
            risk_level=risk_level,
            recommendation_type=recommendation_type,
            primary_reason=str(pred.get("decision", "Auto evaluated by model")),
            calculated_by="MODEL",
        )
        db.add(result)
        db.flush()

        assessment.latest_result_id = result.id
        db.add(
            AssessmentStatusLog(
                assessment_id=assessment.id,
                from_status=None,
                to_status="COMPLETED",
                changed_by_user_id=created_by,
                reason="Legacy /predict auto-save",
            )
        )

        factor_labels = {
            "LOW": "ความเสี่ยงโดยรวมต่ำ",
            "MEDIUM": "ความเสี่ยงระดับปานกลาง",
            "HIGH": "ความเสี่ยงโดยรวมสูง",
        }
        db.add(
            RiskFactor(
                risk_result_id=result.id,
                factor_code="MODEL_DEFAULT_PROBABILITY",
                factor_label_th=factor_labels[risk_level],
                factor_label_en=f"Model probability = {prob:.4f}",
                impact_direction="NEGATIVE" if risk_level in {"MEDIUM", "HIGH"} else "POSITIVE",
                impact_score=round(abs(score - 50), 2),
                detail=f"Created from /predict with threshold-based decision ({pred.get('threshold')})",
            )
        )

        tpl = templates_by_type_and_risk.get((recommendation_type, risk_level))
        if tpl:
            db.add(
                RiskRecommendation(
                    risk_result_id=result.id,
                    recommendation_type=recommendation_type,
                    title_th=tpl.title_th,
                    description_th=tpl.description_th,
                    priority=1,
                    is_primary=True,
                )
            )
        else:
            db.add(
                RiskRecommendation(
                    risk_result_id=result.id,
                    recommendation_type=recommendation_type,
                    title_th="คำแนะนำหลัก",
                    description_th=(
                        "อนุมัติได้ภายใต้เงื่อนไขมาตรฐาน"
                        if recommendation_type == "APPROVE"
                        else "ควรตรวจสอบเอกสารหรือหลักประกันเพิ่มเติม"
                        if recommendation_type == "REVIEW_MANUAL"
                        else "ควรปฏิเสธหรือขอหลักประกันเพิ่มเติม"
                    ),
                    priority=1,
                    is_primary=True,
                )
            )

        created_ids.append(assessment.id)

    db.commit()
    return created_ids
