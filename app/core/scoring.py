from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreOutput:
    score: float
    score_scale: int
    credit_score: int
    score_grade: str
    risk_level: str
    recommendation_type: str
    dti: float
    default_probability: float
    primary_reason: str
    factors: list[dict]
    recommendations: list[dict]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "E"


def calculate_risk(
    *,
    age_years: int,
    monthly_income: float,
    job_tenure_months: int,
    monthly_debt_payment: float,
    has_defaulted: bool,
) -> ScoreOutput:
    income = max(0.0, float(monthly_income))
    debt_payment = max(0.0, float(monthly_debt_payment))
    dti = debt_payment / income if income > 0 else 1.0

    score = 100.0
    factors: list[dict] = []

    if dti >= 0.60:
        score -= 20
        factors.append({"code": "DTI_HIGH", "impact": -20, "labelTh": "ภาระหนี้ต่อรายได้สูง"})
    elif dti >= 0.40:
        score -= 10
        factors.append({"code": "DTI_MEDIUM", "impact": -10, "labelTh": "ภาระหนี้ต่อรายได้ระดับกลาง"})

    if income < 15000:
        score -= 15
        factors.append({"code": "LOW_INCOME", "impact": -15, "labelTh": "รายได้ต่อเดือนต่ำ"})
    elif income >= 50000:
        score += 8
        factors.append({"code": "HIGH_INCOME", "impact": 8, "labelTh": "รายได้ต่อเดือนสูง"})

    if job_tenure_months < 12:
        score -= 10
        factors.append({"code": "SHORT_TENURE", "impact": -10, "labelTh": "อายุงานสั้น"})
    elif job_tenure_months >= 36:
        score += 8
        factors.append({"code": "GOOD_TENURE", "impact": 8, "labelTh": "อายุงานมั่นคง"})

    if age_years < 21 or age_years > 70:
        score -= 10
        factors.append({"code": "AGE_EDGE", "impact": -10, "labelTh": "อายุใกล้ขอบเกณฑ์"})
    elif 25 <= age_years <= 55:
        score += 5
        factors.append({"code": "AGE_STABLE", "impact": 5, "labelTh": "ช่วงอายุมั่นคง"})

    if has_defaulted:
        score -= 25
        factors.append({"code": "DEFAULT_HISTORY", "impact": -25, "labelTh": "มีประวัติผิดนัด"})

    score = _clamp(score, 0, 100)

    default_probability = _clamp(1 - (score / 100.0), 0, 1)
    if default_probability >= 0.70:
        risk_level = "HIGH"
        recommendation_type = "REJECT"
        primary_reason = "ความเสี่ยงโดยรวมสูง"
    elif default_probability >= 0.40:
        risk_level = "MEDIUM"
        recommendation_type = "REVIEW_MANUAL"
        primary_reason = "ควรพิจารณาเพิ่มเติม"
    else:
        risk_level = "LOW"
        recommendation_type = "APPROVE"
        primary_reason = "ความเสี่ยงโดยรวมอยู่ในเกณฑ์ต่ำ"

    recommendations = [
        {
            "type": recommendation_type,
            "titleTh": "คำแนะนำหลัก",
            "descriptionTh": (
                "อนุมัติได้ภายใต้เงื่อนไขมาตรฐาน"
                if recommendation_type == "APPROVE"
                else "ควรตรวจสอบเอกสาร/หลักประกันเพิ่มเติม"
                if recommendation_type == "REVIEW_MANUAL"
                else "ควรปฏิเสธหรือขอหลักประกันเพิ่ม"
            ),
            "priority": 1,
            "isPrimary": True,
        }
    ]

    credit_score = int(round(300 + score * 5.5))
    return ScoreOutput(
        score=round(score, 2),
        score_scale=100,
        credit_score=credit_score,
        score_grade=_grade(score),
        risk_level=risk_level,
        recommendation_type=recommendation_type,
        dti=round(dti, 4),
        default_probability=round(default_probability, 6),
        primary_reason=primary_reason,
        factors=factors,
        recommendations=recommendations,
    )
