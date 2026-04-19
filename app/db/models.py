from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.session import DATABASE_URL

JSONType = JSONB if DATABASE_URL.startswith("postgresql") else JSON


def _uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)
    force_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class LoanAssessment(Base):
    __tablename__ = "loan_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    assigned_to_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False, index=True)
    source_channel: Mapped[str] = mapped_column(String(20), default="WEB", nullable=False, index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    latest_result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_assessments.id"), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    national_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    age_years_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    marital_status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    province_code: Mapped[str] = mapped_column(String(10), ForeignKey("provinces.code"), nullable=False)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class ApplicantEmploymentInfo(Base):
    __tablename__ = "applicant_employment_infos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_assessments.id"), nullable=False, unique=True)
    occupation_code: Mapped[str] = mapped_column(String(40), ForeignKey("occupations.code"), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    employer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    job_tenure_months: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_income: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False, index=True)
    additional_income: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    income_stability_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class ApplicantFinancialInfo(Base):
    __tablename__ = "applicant_financial_infos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_assessments.id"), nullable=False, unique=True)
    requested_loan_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, index=True)
    loan_term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    loan_purpose_code: Mapped[str] = mapped_column(String(40), ForeignKey("loan_purposes.code"), nullable=False)
    monthly_debt_payment: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    existing_loan_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    debt_service_ratio: Mapped[float | None] = mapped_column(Numeric(7, 4), nullable=True, index=True)
    net_monthly_income: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class ApplicantDebtInfo(Base):
    __tablename__ = "applicant_debt_infos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_assessments.id"), nullable=False, index=True)
    debt_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    creditor_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outstanding_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    monthly_payment: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    delinquent_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_defaulted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class RiskResult(Base):
    __tablename__ = "risk_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_assessments.id"), nullable=False, index=True)
    result_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, index=True)
    score_scale: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    credit_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    score_grade: Mapped[str | None] = mapped_column(String(5), nullable=True, index=True)
    default_probability: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    recommendation_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    primary_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated_by: Mapped[str] = mapped_column(String(20), default="MODEL", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)


class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    risk_result_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_results.id"), nullable=False, index=True)
    factor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    factor_label_th: Mapped[str] = mapped_column(String(200), nullable=False)
    factor_label_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    impact_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    impact_score: Mapped[float] = mapped_column(Numeric(6, 2), default=0, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class RiskRecommendation(Base):
    __tablename__ = "risk_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    risk_result_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_results.id"), nullable=False, index=True)
    recommendation_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title_th: Mapped[str] = mapped_column(String(200), nullable=False)
    description_th: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class AssessmentStatusLog(Base):
    __tablename__ = "assessment_status_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_assessments.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)


class Province(Base):
    __tablename__ = "provinces"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name_th: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class Occupation(Base):
    __tablename__ = "occupations"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name_th: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(150), nullable=True)
    risk_weight: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class LoanPurpose(Base):
    __tablename__ = "loan_purposes"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name_th: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(150), nullable=True)
    risk_weight: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)


class IncomeRange(Base):
    __tablename__ = "income_ranges"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    min_income: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    max_income: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    label_th: Mapped[str] = mapped_column(String(100), nullable=False)
    label_en: Mapped[str | None] = mapped_column(String(100), nullable=True)


class RecommendationTemplate(Base):
    __tablename__ = "recommendation_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recommendation_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    title_th: Mapped[str] = mapped_column(String(200), nullable=False)
    description_th: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RiskRuleTemplate(Base):
    __tablename__ = "risk_rule_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    rule_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(150), nullable=False)
    conditions_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    score_delta: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SystemSeedHistory(Base):
    __tablename__ = "system_seed_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    seed_version: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    applied_by: Mapped[str] = mapped_column(String(120), default="system", nullable=False)


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    translated_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, nullable=False)
    predictions: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, nullable=False)
