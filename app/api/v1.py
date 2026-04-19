from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.scoring import calculate_risk
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import (
    ApplicantDebtInfo,
    ApplicantEmploymentInfo,
    ApplicantFinancialInfo,
    ApplicantProfile,
    AssessmentStatusLog,
    LoanAssessment,
    LoanPurpose,
    Occupation,
    Province,
    RefreshToken,
    RiskFactor,
    RiskRecommendation,
    RiskResult,
    Role,
    User,
)
from app.db.session import get_db
from app.seed.bootstrap import run_seed

router = APIRouter(prefix="/api/v1", tags=["v1"])
bearer = HTTPBearer(auto_error=False)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> tuple[User, str]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.scalar(select(User).where(User.id == str(payload.get("sub")), User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    role = db.scalar(select(Role).where(Role.id == user.role_id))
    role_code = role.code if role else "ANALYST"
    return user, role_code


def _require_role(allowed: set[str]):
    def dep(current: tuple[User, str] = Depends(_get_current_user)) -> tuple[User, str]:
        _, role = current
        if role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current

    return dep


def _get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> tuple[User, str] | None:
    if not credentials:
        return None
    return _get_current_user(credentials, db)


class LoginRequest(BaseModel):
    usernameOrEmail: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    rememberMe: bool = False


class RefreshRequest(BaseModel):
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str


class ApplicantProfilePayload(BaseModel):
    firstName: str
    lastName: str
    nationalIdHash: str | None = None
    dateOfBirth: date
    maritalStatus: str | None = None
    provinceCode: str
    district: str | None = None
    postalCode: str | None = None


class EmploymentPayload(BaseModel):
    occupationCode: str
    employmentType: str
    employerName: str | None = None
    jobTenureMonths: int = Field(ge=0)
    monthlyIncome: float = Field(gt=0)
    additionalIncome: float = Field(default=0, ge=0)


class FinancialPayload(BaseModel):
    requestedLoanAmount: float = Field(gt=0)
    loanTermMonths: int = Field(ge=6, le=120)
    loanPurposeCode: str
    monthlyDebtPayment: float = Field(ge=0)
    existingLoanBalance: float = Field(default=0, ge=0)


class DebtPayload(BaseModel):
    debtType: str
    creditorName: str | None = None
    outstandingAmount: float = Field(ge=0)
    monthlyPayment: float = Field(ge=0)
    delinquentDays: int = Field(default=0, ge=0)
    isDefaulted: bool = False


class AssessmentUpsertRequest(BaseModel):
    applicantProfile: ApplicantProfilePayload
    employmentInfo: EmploymentPayload
    financialInfo: FinancialPayload
    debtInfos: list[DebtPayload] = Field(default_factory=list)
    note: str | None = None


class SeedRequest(BaseModel):
    seedVersion: str = "v1.0.0"
    includeDummyAssessments: bool = True


def _age_years(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _assessment_no(db: Session) -> str:
    count = db.scalar(select(func.count(LoanAssessment.id))) or 0
    return f"CR-{date.today().year}-{count + 1:06d}"


def _profile_to_api(row: ApplicantProfile | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "firstName": row.first_name,
        "lastName": row.last_name,
        "dateOfBirth": row.date_of_birth.isoformat(),
        "ageYears": row.age_years_snapshot,
        "maritalStatus": row.marital_status,
        "provinceCode": row.province_code,
        "district": row.district,
        "postalCode": row.postal_code,
    }


def _employment_to_api(row: ApplicantEmploymentInfo | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "occupationCode": row.occupation_code,
        "employmentType": row.employment_type,
        "employerName": row.employer_name,
        "jobTenureMonths": row.job_tenure_months,
        "monthlyIncome": float(row.monthly_income),
        "additionalIncome": float(row.additional_income),
    }


def _financial_to_api(row: ApplicantFinancialInfo | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "requestedLoanAmount": float(row.requested_loan_amount),
        "loanTermMonths": row.loan_term_months,
        "loanPurposeCode": row.loan_purpose_code,
        "monthlyDebtPayment": float(row.monthly_debt_payment),
        "existingLoanBalance": float(row.existing_loan_balance),
        "debtServiceRatio": float(row.debt_service_ratio) if row.debt_service_ratio is not None else None,
        "netMonthlyIncome": float(row.net_monthly_income) if row.net_monthly_income is not None else None,
    }


def _upsert_assessment_data(
    db: Session,
    assessment: LoanAssessment,
    payload: AssessmentUpsertRequest,
) -> None:
    profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == assessment.id))
    age = _age_years(payload.applicantProfile.dateOfBirth)
    if not profile:
        profile = ApplicantProfile(
            assessment_id=assessment.id,
            first_name=payload.applicantProfile.firstName,
            last_name=payload.applicantProfile.lastName,
            national_id_hash=payload.applicantProfile.nationalIdHash,
            date_of_birth=payload.applicantProfile.dateOfBirth,
            age_years_snapshot=age,
            marital_status=payload.applicantProfile.maritalStatus,
            province_code=payload.applicantProfile.provinceCode,
            district=payload.applicantProfile.district,
            postal_code=payload.applicantProfile.postalCode,
        )
        db.add(profile)
    else:
        profile.first_name = payload.applicantProfile.firstName
        profile.last_name = payload.applicantProfile.lastName
        profile.national_id_hash = payload.applicantProfile.nationalIdHash
        profile.date_of_birth = payload.applicantProfile.dateOfBirth
        profile.age_years_snapshot = age
        profile.marital_status = payload.applicantProfile.maritalStatus
        profile.province_code = payload.applicantProfile.provinceCode
        profile.district = payload.applicantProfile.district
        profile.postal_code = payload.applicantProfile.postalCode
        profile.updated_at = _utc_now()

    emp = db.scalar(select(ApplicantEmploymentInfo).where(ApplicantEmploymentInfo.assessment_id == assessment.id))
    if not emp:
        emp = ApplicantEmploymentInfo(
            assessment_id=assessment.id,
            occupation_code=payload.employmentInfo.occupationCode,
            employment_type=payload.employmentInfo.employmentType,
            employer_name=payload.employmentInfo.employerName,
            job_tenure_months=payload.employmentInfo.jobTenureMonths,
            monthly_income=payload.employmentInfo.monthlyIncome,
            additional_income=payload.employmentInfo.additionalIncome,
        )
        db.add(emp)
    else:
        emp.occupation_code = payload.employmentInfo.occupationCode
        emp.employment_type = payload.employmentInfo.employmentType
        emp.employer_name = payload.employmentInfo.employerName
        emp.job_tenure_months = payload.employmentInfo.jobTenureMonths
        emp.monthly_income = payload.employmentInfo.monthlyIncome
        emp.additional_income = payload.employmentInfo.additionalIncome
        emp.updated_at = _utc_now()

    fin = db.scalar(select(ApplicantFinancialInfo).where(ApplicantFinancialInfo.assessment_id == assessment.id))
    debt_service_ratio = (
        payload.financialInfo.monthlyDebtPayment / payload.employmentInfo.monthlyIncome
        if payload.employmentInfo.monthlyIncome > 0
        else 1.0
    )
    if not fin:
        fin = ApplicantFinancialInfo(
            assessment_id=assessment.id,
            requested_loan_amount=payload.financialInfo.requestedLoanAmount,
            loan_term_months=payload.financialInfo.loanTermMonths,
            loan_purpose_code=payload.financialInfo.loanPurposeCode,
            monthly_debt_payment=payload.financialInfo.monthlyDebtPayment,
            existing_loan_balance=payload.financialInfo.existingLoanBalance,
            debt_service_ratio=debt_service_ratio,
            net_monthly_income=payload.employmentInfo.monthlyIncome - payload.financialInfo.monthlyDebtPayment,
        )
        db.add(fin)
    else:
        fin.requested_loan_amount = payload.financialInfo.requestedLoanAmount
        fin.loan_term_months = payload.financialInfo.loanTermMonths
        fin.loan_purpose_code = payload.financialInfo.loanPurposeCode
        fin.monthly_debt_payment = payload.financialInfo.monthlyDebtPayment
        fin.existing_loan_balance = payload.financialInfo.existingLoanBalance
        fin.debt_service_ratio = debt_service_ratio
        fin.net_monthly_income = payload.employmentInfo.monthlyIncome - payload.financialInfo.monthlyDebtPayment
        fin.updated_at = _utc_now()

    db.query(ApplicantDebtInfo).filter(ApplicantDebtInfo.assessment_id == assessment.id).delete()
    for d in payload.debtInfos:
        db.add(
            ApplicantDebtInfo(
                assessment_id=assessment.id,
                debt_type=d.debtType,
                creditor_name=d.creditorName,
                outstanding_amount=d.outstandingAmount,
                monthly_payment=d.monthlyPayment,
                delinquent_days=d.delinquentDays,
                is_defaulted=d.isDefaulted,
            )
        )


@router.post("/auth/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.scalar(
        select(User).where(
            and_(
                or_(User.username == req.usernameOrEmail, User.email == req.usernameOrEmail),
                User.deleted_at.is_(None),
            )
        )
    )
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="AUTH_INVALID_CREDENTIALS")
    role = db.scalar(select(Role).where(Role.id == user.role_id))
    role_code = role.code if role else "ANALYST"
    if user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="AUTH_USER_DISABLED")

    access_exp = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    access_token = create_access_token({"sub": user.id, "role": role_code}, expires_minutes=access_exp)
    refresh_token = create_refresh_token()
    refresh_days = int(os.getenv("REFRESH_TOKEN_DAYS", "14"))
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            expires_at=_utc_now() + timedelta(days=refresh_days),
        )
    )
    user.last_login_at = _utc_now()
    user.updated_at = _utc_now()
    db.commit()

    return ok(
        {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": access_exp * 60,
            "user": {
                "id": user.id,
                "fullName": user.full_name,
                "email": user.email,
                "role": role_code,
                "forceChangePassword": user.force_change_password,
            },
        },
        "Login successful",
    )


@router.post("/auth/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    token_hash = hash_token(req.refreshToken)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if not row or row.revoked_at is not None or row.expires_at < _utc_now():
        raise HTTPException(status_code=401, detail="AUTH_REFRESH_EXPIRED")
    user = db.scalar(select(User).where(User.id == row.user_id, User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(status_code=401, detail="AUTH_USER_NOT_FOUND")
    role = db.scalar(select(Role).where(Role.id == user.role_id))
    role_code = role.code if role else "ANALYST"

    row.revoked_at = _utc_now()
    access_exp = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    access_token = create_access_token({"sub": user.id, "role": role_code}, expires_minutes=access_exp)
    refresh_token = create_refresh_token()
    refresh_days = int(os.getenv("REFRESH_TOKEN_DAYS", "14"))
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            user_agent=row.user_agent,
            ip_address=row.ip_address,
            expires_at=_utc_now() + timedelta(days=refresh_days),
        )
    )
    db.commit()
    return ok({"accessToken": access_token, "refreshToken": refresh_token, "expiresIn": access_exp * 60}, "Token refreshed")


@router.post("/auth/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db), _: tuple[User, str] = Depends(_get_current_user)) -> dict[str, Any]:
    token_hash = hash_token(req.refreshToken)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if row and row.revoked_at is None:
        row.revoked_at = _utc_now()
        db.commit()
    return ok({}, "Logout successful")


@router.get("/auth/me")
def me(current: tuple[User, str] = Depends(_get_current_user)) -> dict[str, Any]:
    user, role = current
    return ok(
        {
            "id": user.id,
            "fullName": user.full_name,
            "email": user.email,
            "role": role,
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
        }
    )


@router.get("/health")
def health_v1() -> dict[str, Any]:
    return ok({"status": "ok"})


@router.get("/db-health")
def db_health_v1(db: Session = Depends(get_db)) -> dict[str, Any]:
    db.execute(select(1))
    return ok({"dbConnected": True})


@router.get("/assessments/form-options")
def form_options(db: Session = Depends(get_db), _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"}))) -> dict[str, Any]:
    provinces = db.scalars(select(Province).order_by(Province.code)).all()
    occupations = db.scalars(select(Occupation).where(Occupation.is_active.is_(True)).order_by(Occupation.code)).all()
    purposes = db.scalars(select(LoanPurpose).where(LoanPurpose.is_active.is_(True)).order_by(LoanPurpose.code)).all()
    return ok(
        {
            "provinces": [{"code": p.code, "nameTh": p.name_th, "nameEn": p.name_en} for p in provinces],
            "occupations": [{"code": o.code, "nameTh": o.name_th, "nameEn": o.name_en} for o in occupations],
            "loanPurposes": [{"code": p.code, "nameTh": p.name_th, "nameEn": p.name_en} for p in purposes],
            "employmentTypes": ["FULL_TIME", "CONTRACT", "SELF_EMPLOYED", "FREELANCE", "UNEMPLOYED"],
            "maritalStatuses": ["SINGLE", "MARRIED", "DIVORCED", "WIDOWED"],
        }
    )


@router.post("/assessments")
def create_assessment(
    req: AssessmentUpsertRequest,
    db: Session = Depends(get_db),
    current: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    user, _ = current
    assessment = LoanAssessment(
        assessment_no=_assessment_no(db),
        created_by_user_id=user.id,
        status="DRAFT",
        current_step=1,
        source_channel="WEB",
        note=req.note,
    )
    db.add(assessment)
    db.flush()
    _upsert_assessment_data(db, assessment, req)
    db.add(
        AssessmentStatusLog(
            assessment_id=assessment.id,
            from_status=None,
            to_status="DRAFT",
            changed_by_user_id=user.id,
            reason="Created draft",
        )
    )
    db.commit()
    return ok({"assessmentId": assessment.id, "assessmentNo": assessment.assessment_no, "status": assessment.status}, "Assessment created")


@router.put("/assessments/{assessment_id}")
def update_assessment(
    assessment_id: str,
    req: AssessmentUpsertRequest,
    db: Session = Depends(get_db),
    current: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    user, _ = current
    assessment = db.scalar(select(LoanAssessment).where(LoanAssessment.id == assessment_id, LoanAssessment.deleted_at.is_(None)))
    if not assessment:
        raise HTTPException(status_code=404, detail="ASSESSMENT_NOT_FOUND")
    if assessment.status not in {"DRAFT", "IN_PROGRESS"}:
        raise HTTPException(status_code=409, detail="ASSESSMENT_STATUS_LOCKED")
    _upsert_assessment_data(db, assessment, req)
    assessment.status = "IN_PROGRESS"
    assessment.current_step = min(3, assessment.current_step + 1)
    assessment.updated_at = _utc_now()
    db.add(
        AssessmentStatusLog(
            assessment_id=assessment.id,
            from_status="DRAFT",
            to_status=assessment.status,
            changed_by_user_id=user.id,
            reason="Updated draft",
        )
    )
    db.commit()
    return ok({"assessmentId": assessment.id, "status": assessment.status}, "Assessment updated")


@router.post("/assessments/calculate")
def calculate_preview(
    req: AssessmentUpsertRequest,
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    age = _age_years(req.applicantProfile.dateOfBirth)
    has_defaulted = any(d.isDefaulted for d in req.debtInfos)
    out = calculate_risk(
        age_years=age,
        monthly_income=req.employmentInfo.monthlyIncome,
        job_tenure_months=req.employmentInfo.jobTenureMonths,
        monthly_debt_payment=req.financialInfo.monthlyDebtPayment,
        has_defaulted=has_defaulted,
    )
    return ok(
        {
            "score": out.score,
            "scoreScale": out.score_scale,
            "creditScore": out.credit_score,
            "scoreGrade": out.score_grade,
            "riskLevel": out.risk_level,
            "defaultProbability": out.default_probability,
            "recommendationType": out.recommendation_type,
            "dti": out.dti,
        },
        "Calculation completed",
    )


@router.get("/assessments/{assessment_id}")
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    assessment = db.scalar(select(LoanAssessment).where(LoanAssessment.id == assessment_id, LoanAssessment.deleted_at.is_(None)))
    if not assessment:
        raise HTTPException(status_code=404, detail="ASSESSMENT_NOT_FOUND")
    profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == assessment.id))
    emp = db.scalar(select(ApplicantEmploymentInfo).where(ApplicantEmploymentInfo.assessment_id == assessment.id))
    fin = db.scalar(select(ApplicantFinancialInfo).where(ApplicantFinancialInfo.assessment_id == assessment.id))
    debts = db.scalars(select(ApplicantDebtInfo).where(ApplicantDebtInfo.assessment_id == assessment.id)).all()
    return ok(
        {
            "id": assessment.id,
            "assessmentNo": assessment.assessment_no,
            "status": assessment.status,
            "applicantProfile": _profile_to_api(profile),
            "employmentInfo": _employment_to_api(emp),
            "financialInfo": _financial_to_api(fin),
            "debtInfos": [
                {
                    "debtType": d.debt_type,
                    "creditorName": d.creditor_name,
                    "outstandingAmount": float(d.outstanding_amount),
                    "monthlyPayment": float(d.monthly_payment),
                    "delinquentDays": d.delinquent_days,
                    "isDefaulted": d.is_defaulted,
                }
                for d in debts
            ],
        }
    )


@router.post("/assessments/{assessment_id}/submit")
def submit_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    user, _ = current
    assessment = db.scalar(select(LoanAssessment).where(LoanAssessment.id == assessment_id, LoanAssessment.deleted_at.is_(None)))
    if not assessment:
        raise HTTPException(status_code=404, detail="ASSESSMENT_NOT_FOUND")

    profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == assessment.id))
    emp = db.scalar(select(ApplicantEmploymentInfo).where(ApplicantEmploymentInfo.assessment_id == assessment.id))
    fin = db.scalar(select(ApplicantFinancialInfo).where(ApplicantFinancialInfo.assessment_id == assessment.id))
    debts = db.scalars(select(ApplicantDebtInfo).where(ApplicantDebtInfo.assessment_id == assessment.id)).all()
    if not profile or not emp or not fin:
        raise HTTPException(status_code=400, detail="ASSESSMENT_INCOMPLETE")
    has_defaulted = any(d.is_defaulted for d in debts)
    out = calculate_risk(
        age_years=profile.age_years_snapshot,
        monthly_income=float(emp.monthly_income),
        job_tenure_months=emp.job_tenure_months,
        monthly_debt_payment=float(fin.monthly_debt_payment),
        has_defaulted=has_defaulted,
    )

    latest_ver = db.scalar(
        select(func.max(RiskResult.result_version)).where(RiskResult.assessment_id == assessment.id)
    )
    next_ver = int(latest_ver or 0) + 1
    result = RiskResult(
        assessment_id=assessment.id,
        result_version=next_ver,
        model_version="hybrid_v1",
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

    for f in out.factors:
        db.add(
            RiskFactor(
                risk_result_id=result.id,
                factor_code=f["code"],
                factor_label_th=f["labelTh"],
                factor_label_en=None,
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

    prev_status = assessment.status
    assessment.status = "COMPLETED"
    assessment.submitted_at = assessment.submitted_at or _utc_now()
    assessment.completed_at = _utc_now()
    assessment.latest_result_id = result.id
    assessment.updated_at = _utc_now()
    db.add(
        AssessmentStatusLog(
            assessment_id=assessment.id,
            from_status=prev_status,
            to_status="COMPLETED",
            changed_by_user_id=user.id,
            reason="Submitted and calculated result",
        )
    )
    db.commit()
    return ok(
        {
            "assessmentId": assessment.id,
            "assessmentNo": assessment.assessment_no,
            "status": assessment.status,
            "resultId": result.id,
        },
        "Assessment submitted",
    )


@router.get("/assessments/{assessment_id}/result")
def get_result(
    assessment_id: str,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    result = db.scalar(
        select(RiskResult).where(RiskResult.assessment_id == assessment_id).order_by(RiskResult.result_version.desc())
    )
    if not result:
        raise HTTPException(status_code=404, detail="RESULT_NOT_FOUND")
    return ok(
        {
            "assessmentId": assessment_id,
            "resultId": result.id,
            "score": float(result.score),
            "scoreScale": result.score_scale,
            "creditScore": result.credit_score,
            "scoreGrade": result.score_grade,
            "riskLevel": result.risk_level,
            "defaultProbability": result.default_probability,
            "recommendationType": result.recommendation_type,
            "primaryReason": result.primary_reason,
            "createdAt": result.created_at.isoformat(),
        }
    )


@router.get("/assessments/{assessment_id}/risk-factors")
def get_risk_factors(
    assessment_id: str,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    result = db.scalar(select(RiskResult).where(RiskResult.assessment_id == assessment_id).order_by(RiskResult.result_version.desc()))
    if not result:
        raise HTTPException(status_code=404, detail="RESULT_NOT_FOUND")
    rows = db.scalars(select(RiskFactor).where(RiskFactor.risk_result_id == result.id)).all()
    return ok(
        {
            "assessmentId": assessment_id,
            "riskResultId": result.id,
            "factors": [
                {
                    "code": r.factor_code,
                    "labelTh": r.factor_label_th,
                    "impactDirection": r.impact_direction,
                    "impactScore": float(r.impact_score),
                    "detail": r.detail,
                }
                for r in rows
            ],
        }
    )


@router.get("/assessments/{assessment_id}/recommendations")
def get_recommendations(
    assessment_id: str,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    result = db.scalar(select(RiskResult).where(RiskResult.assessment_id == assessment_id).order_by(RiskResult.result_version.desc()))
    if not result:
        raise HTTPException(status_code=404, detail="RESULT_NOT_FOUND")
    rows = db.scalars(select(RiskRecommendation).where(RiskRecommendation.risk_result_id == result.id)).all()
    return ok(
        {
            "assessmentId": assessment_id,
            "recommendations": [
                {
                    "type": r.recommendation_type,
                    "titleTh": r.title_th,
                    "descriptionTh": r.description_th,
                    "priority": r.priority,
                    "isPrimary": r.is_primary,
                }
                for r in rows
            ],
        }
    )


@router.get("/assessments")
def list_assessments(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    search: str | None = None,
    riskLevel: str | None = None,
    status_q: str | None = Query(None, alias="status"),
    dateFrom: date | None = None,
    dateTo: date | None = None,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    stmt = select(LoanAssessment).where(LoanAssessment.deleted_at.is_(None))
    if status_q:
        stmt = stmt.where(LoanAssessment.status == status_q)
    if dateFrom:
        stmt = stmt.where(LoanAssessment.created_at >= datetime.combine(dateFrom, datetime.min.time(), tzinfo=timezone.utc))
    if dateTo:
        stmt = stmt.where(LoanAssessment.created_at <= datetime.combine(dateTo, datetime.max.time(), tzinfo=timezone.utc))
    if search:
        stmt = stmt.where(LoanAssessment.assessment_no.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    if sortBy == "submittedAt":
        sort_col = LoanAssessment.submitted_at
    else:
        sort_col = LoanAssessment.created_at
    if sortOrder.lower() == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())
    items = db.scalars(stmt.offset((page - 1) * pageSize).limit(pageSize)).all()

    rows = []
    for a in items:
        profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == a.id))
        result = db.scalar(select(RiskResult).where(RiskResult.id == a.latest_result_id)) if a.latest_result_id else None
        if riskLevel and result and result.risk_level != riskLevel:
            continue
        rows.append(
            {
                "id": a.id,
                "assessmentNo": a.assessment_no,
                "applicantName": f"{profile.first_name} {profile.last_name}" if profile else None,
                "status": a.status,
                "submittedAt": a.submitted_at.isoformat() if a.submitted_at else None,
                "score": float(result.score) if result else None,
                "riskLevel": result.risk_level if result else None,
                "recommendationType": result.recommendation_type if result else None,
            }
        )

    total_pages = max(1, (total + pageSize - 1) // pageSize)
    return ok(
        {
            "items": rows,
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "totalItems": total,
                "totalPages": total_pages,
                "hasNext": page < total_pages,
                "hasPrev": page > 1,
            },
        }
    )


@router.get("/assessments/{assessment_id}/detail")
def assessment_detail(
    assessment_id: str,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    assessment = db.scalar(select(LoanAssessment).where(LoanAssessment.id == assessment_id, LoanAssessment.deleted_at.is_(None)))
    if not assessment:
        raise HTTPException(status_code=404, detail="ASSESSMENT_NOT_FOUND")
    profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == assessment.id))
    emp = db.scalar(select(ApplicantEmploymentInfo).where(ApplicantEmploymentInfo.assessment_id == assessment.id))
    fin = db.scalar(select(ApplicantFinancialInfo).where(ApplicantFinancialInfo.assessment_id == assessment.id))
    debts = db.scalars(select(ApplicantDebtInfo).where(ApplicantDebtInfo.assessment_id == assessment.id)).all()
    result = db.scalar(select(RiskResult).where(RiskResult.id == assessment.latest_result_id)) if assessment.latest_result_id else None
    status_logs = db.scalars(select(AssessmentStatusLog).where(AssessmentStatusLog.assessment_id == assessment.id).order_by(AssessmentStatusLog.created_at.desc())).all()
    return ok(
        {
            "assessment": {"id": assessment.id, "assessmentNo": assessment.assessment_no, "status": assessment.status},
            "applicantProfile": _profile_to_api(profile),
            "employmentInfo": _employment_to_api(emp),
            "financialInfo": _financial_to_api(fin),
            "debtInfos": [
                {
                    "debtType": d.debt_type,
                    "creditorName": d.creditor_name,
                    "outstandingAmount": float(d.outstanding_amount),
                    "monthlyPayment": float(d.monthly_payment),
                    "delinquentDays": d.delinquent_days,
                    "isDefaulted": d.is_defaulted,
                }
                for d in debts
            ],
            "result": (
                {
                    "resultId": result.id,
                    "score": float(result.score),
                    "creditScore": result.credit_score,
                    "scoreGrade": result.score_grade,
                    "defaultProbability": result.default_probability,
                    "riskLevel": result.risk_level,
                    "recommendationType": result.recommendation_type,
                    "primaryReason": result.primary_reason,
                    "createdAt": result.created_at.isoformat(),
                }
                if result
                else None
            ),
            "statusLogs": [
                {
                    "fromStatus": s.from_status,
                    "toStatus": s.to_status,
                    "reason": s.reason,
                    "createdAt": s.created_at.isoformat(),
                }
                for s in status_logs
            ],
        }
    )


@router.post("/assessments/{assessment_id}/re-evaluate")
def re_evaluate(
    assessment_id: str,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN"})),
) -> dict[str, Any]:
    assessment = db.scalar(select(LoanAssessment).where(LoanAssessment.id == assessment_id, LoanAssessment.deleted_at.is_(None)))
    if not assessment:
        raise HTTPException(status_code=404, detail="ASSESSMENT_NOT_FOUND")
    profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == assessment.id))
    emp = db.scalar(select(ApplicantEmploymentInfo).where(ApplicantEmploymentInfo.assessment_id == assessment.id))
    fin = db.scalar(select(ApplicantFinancialInfo).where(ApplicantFinancialInfo.assessment_id == assessment.id))
    debts = db.scalars(select(ApplicantDebtInfo).where(ApplicantDebtInfo.assessment_id == assessment.id)).all()
    if not profile or not emp or not fin:
        raise HTTPException(status_code=400, detail="ASSESSMENT_INCOMPLETE")
    out = calculate_risk(
        age_years=profile.age_years_snapshot,
        monthly_income=float(emp.monthly_income),
        job_tenure_months=emp.job_tenure_months,
        monthly_debt_payment=float(fin.monthly_debt_payment),
        has_defaulted=any(d.is_defaulted for d in debts),
    )
    latest_ver = db.scalar(select(func.max(RiskResult.result_version)).where(RiskResult.assessment_id == assessment.id)) or 0
    result = RiskResult(
        assessment_id=assessment.id,
        result_version=int(latest_ver) + 1,
        model_version="hybrid_v1",
        score=out.score,
        score_scale=100,
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
    assessment.status = "RE_EVALUATED"
    assessment.updated_at = _utc_now()
    db.commit()
    return ok({"assessmentId": assessment.id, "resultId": result.id}, "Assessment re-evaluated")


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    total = db.scalar(select(func.count(LoanAssessment.id)).where(LoanAssessment.deleted_at.is_(None))) or 0
    low = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == "LOW")) or 0
    med = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == "MEDIUM")) or 0
    high = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == "HIGH")) or 0
    high_percent = round((high / total) * 100, 2) if total else 0
    return ok(
        {
            "totalAssessments": total,
            "lowRiskCount": low,
            "mediumRiskCount": med,
            "highRiskCount": high,
            "highRiskPercent": high_percent,
            "changeVsPreviousPeriodPercent": 0,
        }
    )


@router.get("/dashboard/risk-distribution")
def dashboard_distribution(
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    total = db.scalar(select(func.count(RiskResult.id))) or 0
    levels = []
    for lvl in ["LOW", "MEDIUM", "HIGH"]:
        count = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == lvl)) or 0
        levels.append({"riskLevel": lvl, "count": count, "percent": round((count / total) * 100, 2) if total else 0})
    return ok({"total": total, "distribution": levels})


@router.get("/dashboard/recent-assessments")
def dashboard_recent(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    items = db.scalars(select(LoanAssessment).where(LoanAssessment.deleted_at.is_(None)).order_by(LoanAssessment.created_at.desc()).limit(limit)).all()
    data = []
    for a in items:
        profile = db.scalar(select(ApplicantProfile).where(ApplicantProfile.assessment_id == a.id))
        result = db.scalar(select(RiskResult).where(RiskResult.id == a.latest_result_id)) if a.latest_result_id else None
        data.append(
            {
                "assessmentId": a.id,
                "assessmentNo": a.assessment_no,
                "applicantName": f"{profile.first_name} {profile.last_name}" if profile else None,
                "score": float(result.score) if result else None,
                "riskLevel": result.risk_level if result else None,
                "createdAt": a.created_at.isoformat(),
            }
        )
    return ok({"items": data})


@router.get("/dashboard/key-insights")
def dashboard_insights(
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN", "ANALYST"})),
) -> dict[str, Any]:
    high = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == "HIGH")) or 0
    med = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == "MEDIUM")) or 0
    low = db.scalar(select(func.count(RiskResult.id)).where(RiskResult.risk_level == "LOW")) or 0
    return ok(
        {
            "insights": [
                {"type": "POSITIVE", "title": "กลุ่มเสี่ยงต่ำ", "description": f"มีทั้งหมด {low} เคส"},
                {"type": "WARNING", "title": "กลุ่มเสี่ยงกลาง", "description": f"มีทั้งหมด {med} เคส ควรติดตาม"},
                {"type": "ALERT", "title": "กลุ่มเสี่ยงสูง", "description": f"มีทั้งหมด {high} เคส ควรตรวจสอบเพิ่ม"},
            ]
        }
    )


@router.post("/admin/seed")
def admin_seed(
    req: SeedRequest,
    db: Session = Depends(get_db),
    current: tuple[User, str] | None = Depends(_get_current_user_optional),
) -> dict[str, Any]:
    user_count = db.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None))) or 0
    if user_count > 0:
        if not current or current[1] != "ADMIN":
            raise HTTPException(status_code=403, detail="AUTH_FORBIDDEN")
    out = run_seed(db, seed_version=req.seedVersion, include_dummy_assessments=req.includeDummyAssessments)
    if not out.get("applied"):
        raise HTTPException(status_code=409, detail="SEED_ALREADY_APPLIED")
    return ok(out, "Seed completed")


class CreateUserRequest(BaseModel):
    fullName: str
    username: str
    email: str
    role: str = Field(pattern="^(ADMIN|ANALYST)$")
    password: str = Field(min_length=8)


@router.get("/admin/users")
def admin_users(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    search: str | None = None,
    status_q: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN"})),
) -> dict[str, Any]:
    stmt = select(User).where(User.deleted_at.is_(None))
    if search:
        stmt = stmt.where(or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"), User.username.ilike(f"%{search}%")))
    if status_q:
        stmt = stmt.where(User.status == status_q)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(User.created_at.desc()).offset((page - 1) * pageSize).limit(pageSize)).all()
    rows = []
    for u in items:
        role = db.scalar(select(Role).where(Role.id == u.role_id))
        rows.append(
            {
                "id": u.id,
                "fullName": u.full_name,
                "username": u.username,
                "email": u.email,
                "role": role.code if role else None,
                "status": u.status,
                "lastLoginAt": u.last_login_at.isoformat() if u.last_login_at else None,
            }
        )
    total_pages = max(1, (total + pageSize - 1) // pageSize)
    return ok(
        {
            "items": rows,
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "totalItems": total,
                "totalPages": total_pages,
                "hasNext": page < total_pages,
                "hasPrev": page > 1,
            },
        }
    )


@router.post("/admin/users")
def create_user(
    req: CreateUserRequest,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN"})),
) -> dict[str, Any]:
    if db.scalar(select(User).where(or_(User.email == req.email, User.username == req.username), User.deleted_at.is_(None))):
        raise HTTPException(status_code=409, detail="USER_ALREADY_EXISTS")
    role = db.scalar(select(Role).where(Role.code == req.role))
    if not role:
        raise HTTPException(status_code=400, detail="ROLE_NOT_FOUND")
    row = User(
        role_id=role.id,
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.fullName,
        status="ACTIVE",
        force_change_password=True,
    )
    db.add(row)
    db.commit()
    return ok({"id": row.id}, "User created")


class ResetPasswordRequest(BaseModel):
    newPassword: str = Field(min_length=8)
    forceChangeOnNextLogin: bool = True


@router.patch("/admin/users/{user_id}/reset-password")
def reset_password(
    user_id: str,
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _: tuple[User, str] = Depends(_require_role({"ADMIN"})),
) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    user.password_hash = hash_password(req.newPassword)
    user.force_change_password = req.forceChangeOnNextLogin
    user.updated_at = _utc_now()
    db.commit()
    return ok({"id": user.id}, "Password reset successful")
