from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.scoring import calculate_risk
from app.core.security import hash_password
from app.db.models import (
    ApplicantDebtInfo,
    ApplicantEmploymentInfo,
    ApplicantFinancialInfo,
    ApplicantProfile,
    AssessmentStatusLog,
    IncomeRange,
    LoanAssessment,
    LoanPurpose,
    Occupation,
    Province,
    RecommendationTemplate,
    RiskFactor,
    RiskRecommendation,
    RiskResult,
    RiskRuleTemplate,
    Role,
    SystemSeedHistory,
    User,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _checksum(seed_version: str, include_dummy: bool) -> str:
    raw = json.dumps({"seedVersion": seed_version, "includeDummy": include_dummy}, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ensure_roles(db: Session) -> None:
    for code, name in [("ADMIN", "Administrator"), ("ANALYST", "Risk Analyst")]:
        row = db.scalar(select(Role).where(Role.code == code))
        if not row:
            db.add(Role(code=code, name=name))


def _ensure_admin(db: Session) -> None:
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    admin_username = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin1234!")
    admin_name = os.getenv("INITIAL_ADMIN_FULL_NAME", "System Admin")
    role = db.scalar(select(Role).where(Role.code == "ADMIN"))
    if not role:
        return
    user = db.scalar(select(User).where(User.email == admin_email))
    if user:
        return
    db.add(
        User(
            role_id=role.id,
            username=admin_username,
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name=admin_name,
            status="ACTIVE",
            force_change_password=True,
        )
    )


def _ensure_lookups(db: Session) -> None:
    provinces = [
        ("10", "กรุงเทพมหานคร", "Bangkok", "Central"),
        ("50", "เชียงใหม่", "Chiang Mai", "North"),
        ("20", "ชลบุรี", "Chonburi", "East"),
        ("40", "ขอนแก่น", "Khon Kaen", "Northeast"),
        ("30", "นครราชสีมา", "Nakhon Ratchasima", "Northeast"),
        ("83", "ภูเก็ต", "Phuket", "South"),
    ]
    for code, th, en, region in provinces:
        if not db.scalar(select(Province).where(Province.code == code)):
            db.add(Province(code=code, name_th=th, name_en=en, region=region))

    occupations = [
        ("LABORER", "แรงงานทั่วไป", "Laborer", -2),
        ("OFFICER", "พนักงานออฟฟิศ", "Officer", 2),
        ("GOVERNMENT", "ข้าราชการ", "Government Officer", 4),
        ("BUSINESS_OWNER", "เจ้าของกิจการ", "Business Owner", 3),
        ("FREELANCE", "ฟรีแลนซ์", "Freelance", -3),
    ]
    for code, th, en, weight in occupations:
        if not db.scalar(select(Occupation).where(Occupation.code == code)):
            db.add(Occupation(code=code, name_th=th, name_en=en, risk_weight=weight))

    purposes = [
        ("HOME_PURCHASE", "ซื้อบ้าน", "Home Purchase", 2),
        ("HOME_IMPROVEMENT", "ซ่อมแซมบ้าน", "Home Improvement", 1),
        ("BUSINESS", "ลงทุนธุรกิจ", "Business", 0),
        ("PERSONAL", "ใช้จ่ายส่วนบุคคล", "Personal", -2),
    ]
    for code, th, en, weight in purposes:
        if not db.scalar(select(LoanPurpose).where(LoanPurpose.code == code)):
            db.add(LoanPurpose(code=code, name_th=th, name_en=en, risk_weight=weight))

    ranges = [
        ("LOW", 0, 14999, "ต่ำกว่า 15,000 บาท", "Below 15,000"),
        ("MID", 15000, 49999, "15,000 - 49,999 บาท", "15,000 - 49,999"),
        ("HIGH", 50000, 999999999, "50,000 บาทขึ้นไป", "50,000+"),
    ]
    for code, min_income, max_income, th, en in ranges:
        if not db.scalar(select(IncomeRange).where(IncomeRange.code == code)):
            db.add(
                IncomeRange(
                    code=code,
                    min_income=min_income,
                    max_income=max_income,
                    label_th=th,
                    label_en=en,
                )
            )

    templates = [
        ("APPROVE", "LOW", "อนุมัติได้", "อนุมัติสินเชื่อภายใต้เงื่อนไขปกติ"),
        ("REVIEW_MANUAL", "MEDIUM", "พิจารณาเพิ่มเติม", "ควรขอเอกสารหรือหลักประกันเพิ่มเติม"),
        ("REJECT", "HIGH", "ยังไม่อนุมัติ", "แนะนำให้ปฏิเสธหรือขอหลักประกันเพิ่มเติม"),
    ]
    for rec_type, risk, title, desc in templates:
        row = db.scalar(
            select(RecommendationTemplate).where(
                RecommendationTemplate.recommendation_type == rec_type,
                RecommendationTemplate.risk_level == risk,
            )
        )
        if not row:
            db.add(
                RecommendationTemplate(
                    recommendation_type=rec_type,
                    risk_level=risk,
                    title_th=title,
                    description_th=desc,
                    is_active=True,
                )
            )

    rules = [
        ("DTI_HIGH", "ภาระหนี้สูง", {"field": "dti", "op": ">=", "value": 0.6}, -20, 10),
        ("LOW_INCOME", "รายได้ต่ำ", {"field": "monthlyIncome", "op": "<", "value": 15000}, -15, 20),
        ("SHORT_TENURE", "อายุงานสั้น", {"field": "jobTenureMonths", "op": "<", "value": 12}, -10, 30),
    ]
    for code, name, cond, delta, pri in rules:
        row = db.scalar(select(RiskRuleTemplate).where(RiskRuleTemplate.rule_code == code))
        if not row:
            db.add(
                RiskRuleTemplate(
                    rule_code=code,
                    rule_name=name,
                    conditions_json=cond,
                    score_delta=delta,
                    priority=pri,
                    is_active=True,
                )
            )


def _assessment_no(db: Session) -> str:
    count = db.scalar(select(func.count(LoanAssessment.id))) or 0
    return f"CR-{date.today().year}-{count + 1:06d}"


def _seed_dummy_assessments(db: Session, created_by_user_id: str, n: int = 6) -> None:
    existing = db.scalar(select(func.count(LoanAssessment.id))) or 0
    if existing >= n:
        return

    base_rows = [
        {"first": "สมชาย", "last": "ใจดี", "age": 35, "income": 45000, "debt": 12500, "tenure": 62, "defaulted": False},
        {"first": "สุภาวดี", "last": "มั่นคง", "age": 42, "income": 68000, "debt": 15000, "tenure": 96, "defaulted": False},
        {"first": "วิชิต", "last": "อ่อนใจ", "age": 27, "income": 18000, "debt": 12000, "tenure": 8, "defaulted": False},
        {"first": "สมปอง", "last": "กล้าหาญ", "age": 31, "income": 13000, "debt": 10000, "tenure": 5, "defaulted": True},
        {"first": "ธนพร", "last": "รุ่งเรือง", "age": 48, "income": 52000, "debt": 14000, "tenure": 48, "defaulted": False},
        {"first": "มนัส", "last": "พัฒนา", "age": 23, "income": 22000, "debt": 9000, "tenure": 14, "defaulted": False},
    ]

    for row in base_rows[: n - existing]:
        assessment = LoanAssessment(
            assessment_no=_assessment_no(db),
            created_by_user_id=created_by_user_id,
            status="COMPLETED",
            source_channel="WEB",
            current_step=4,
            submitted_at=_utc_now(),
            completed_at=_utc_now(),
        )
        db.add(assessment)
        db.flush()

        db.add(
            ApplicantProfile(
                assessment_id=assessment.id,
                first_name=row["first"],
                last_name=row["last"],
                date_of_birth=date(date.today().year - row["age"], 1, 1),
                age_years_snapshot=row["age"],
                marital_status="MARRIED",
                province_code="10",
                district="บางกะปิ",
            )
        )
        db.add(
            ApplicantEmploymentInfo(
                assessment_id=assessment.id,
                occupation_code="OFFICER",
                employment_type="FULL_TIME",
                job_tenure_months=row["tenure"],
                monthly_income=row["income"],
                additional_income=0,
            )
        )
        dti = row["debt"] / row["income"] if row["income"] else 1.0
        db.add(
            ApplicantFinancialInfo(
                assessment_id=assessment.id,
                requested_loan_amount=850000,
                loan_term_months=60,
                loan_purpose_code="HOME_PURCHASE",
                monthly_debt_payment=row["debt"],
                existing_loan_balance=285000,
                debt_service_ratio=dti,
                net_monthly_income=row["income"] - row["debt"],
            )
        )
        db.add(
            ApplicantDebtInfo(
                assessment_id=assessment.id,
                debt_type="PERSONAL_LOAN",
                outstanding_amount=285000,
                monthly_payment=row["debt"],
                delinquent_days=0,
                is_defaulted=row["defaulted"],
            )
        )

        out = calculate_risk(
            age_years=row["age"],
            monthly_income=row["income"],
            job_tenure_months=row["tenure"],
            monthly_debt_payment=row["debt"],
            has_defaulted=row["defaulted"],
        )
        result = RiskResult(
            assessment_id=assessment.id,
            result_version=1,
            model_version="rules_v1",
            score=out.score,
            score_scale=out.score_scale,
            credit_score=out.credit_score,
            score_grade=out.score_grade,
            default_probability=out.default_probability,
            risk_level=out.risk_level,
            recommendation_type=out.recommendation_type,
            primary_reason=out.primary_reason,
            calculated_by="MODEL",
        )
        db.add(result)
        db.flush()
        assessment.latest_result_id = result.id

        for f in out.factors:
            db.add(
                RiskFactor(
                    risk_result_id=result.id,
                    factor_code=f["code"],
                    factor_label_th=f["labelTh"],
                    impact_direction="NEGATIVE" if float(f["impact"]) < 0 else "POSITIVE",
                    impact_score=abs(float(f["impact"])),
                    detail=f["labelTh"],
                )
            )
        for r in out.recommendations:
            db.add(
                RiskRecommendation(
                    risk_result_id=result.id,
                    recommendation_type=r["type"],
                    title_th=r["titleTh"],
                    description_th=r["descriptionTh"],
                    priority=r["priority"],
                    is_primary=r["isPrimary"],
                )
            )
        db.add(
            AssessmentStatusLog(
                assessment_id=assessment.id,
                from_status="SUBMITTED",
                to_status="COMPLETED",
                changed_by_user_id=created_by_user_id,
                reason="Seeded demo result",
            )
        )


def run_seed(db: Session, *, seed_version: str, include_dummy_assessments: bool = True) -> dict[str, Any]:
    checksum = _checksum(seed_version, include_dummy_assessments)
    existing = db.scalar(select(SystemSeedHistory).where(SystemSeedHistory.seed_version == seed_version))
    if existing:
        return {"seedVersion": seed_version, "applied": False, "reason": "already_applied"}

    _ensure_roles(db)
    db.flush()
    _ensure_admin(db)
    _ensure_lookups(db)
    db.flush()

    if include_dummy_assessments:
        admin = db.scalar(select(User).where(User.email == os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")))
        if admin:
            _seed_dummy_assessments(db, created_by_user_id=admin.id)

    db.add(SystemSeedHistory(seed_version=seed_version, checksum=checksum, applied_by="system"))
    db.commit()
    return {"seedVersion": seed_version, "applied": True}
