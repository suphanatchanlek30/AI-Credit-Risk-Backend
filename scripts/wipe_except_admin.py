from app.db.session import SessionLocal
from app.db.models import (
    User, LoanAssessment, ApplicantProfile, ApplicantEmploymentInfo, ApplicantFinancialInfo, ApplicantDebtInfo,
    AssessmentStatusLog, RiskResult, RiskFactor, RiskRecommendation, RefreshToken
)
from sqlalchemy import delete

def wipe_except_admin():
    db = SessionLocal()
    try:
        # Delete all except admin user
        admin_users = db.query(User).filter(User.role_id.isnot(None), User.deleted_at.is_(None)).filter(User.username == "admin").all()
        admin_ids = [u.id for u in admin_users]
        # Delete all other users
        db.query(RefreshToken).delete()
        db.query(User).filter(~User.id.in_(admin_ids)).delete(synchronize_session=False)
        # Delete all business data
        db.query(RiskFactor).delete()
        db.query(RiskRecommendation).delete()
        db.query(RiskResult).delete()
        db.query(AssessmentStatusLog).delete()
        db.query(ApplicantDebtInfo).delete()
        db.query(ApplicantFinancialInfo).delete()
        db.query(ApplicantEmploymentInfo).delete()
        db.query(ApplicantProfile).delete()
        db.query(LoanAssessment).delete()
        db.commit()
        print("Database wiped except admin user.")
    finally:
        db.close()

if __name__ == "__main__":
    wipe_except_admin()
