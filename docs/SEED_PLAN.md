# SEED_PLAN.md

## Objective
ทำให้ระบบใช้งานได้ทันทีหลัง deploy ครั้งแรก:
- login ได้ทันทีด้วย admin default
- form dropdown พร้อมใช้
- dashboard มีข้อมูล
- history/result/detail แสดงผลได้ทันที

## Environment Variables
- `APP_ENV`
- `INITIAL_ADMIN_EMAIL` (default: `admin@example.com`)
- `INITIAL_ADMIN_USERNAME` (default: `admin`)
- `INITIAL_ADMIN_PASSWORD` (required in production)
- `SEED_VERSION` (example: `v1.0.0`)

## Seed Execution Order (สำคัญ)
1. `roles`
2. `users` (default admin)
3. lookup: `provinces`, `occupations`, `loan_purposes`, `income_ranges`
4. templates: `recommendation_templates`, `risk_rule_templates`
5. transactional demo: `loan_assessments` + applicant tables
6. `risk_results`, `risk_factors`, `risk_recommendations`
7. `assessment_status_logs`
8. optional legacy `prediction_logs` demo rows

## Idempotency Strategy (กัน seed ซ้ำ)
- ใช้ตาราง `system_seed_histories`
  - `id`, `seed_version`, `checksum`, `applied_at`, `applied_by`
- ก่อน seed ตรวจ `seed_version` ว่าถูก apply แล้วหรือยัง
- ทุก insert ใช้ upsert by unique keys

## Suggested Command
- CLI: `python -m app.seed.run --version v1.0.0 --with-demo true`
- API (admin): `POST /api/v1/admin/seed`

## Default Seed Data

### 1) Roles
- `ADMIN`
- `ANALYST`

### 2) Default Admin
- username: `admin`
- email: `admin@example.com`
- password: from `INITIAL_ADMIN_PASSWORD`
- role: `ADMIN`
- force change password on first login: `true`

### 3) Provinces (mock stage)
ขั้นต่ำ 10 จังหวัดแรก:
- กรุงเทพมหานคร, เชียงใหม่, ชลบุรี, ขอนแก่น, นครราชสีมา, ภูเก็ต, สงขลา, อุบลราชธานี, สุราษฎร์ธานี, นนทบุรี

### 4) Occupations (mock)
- `LABORER`, `OFFICER`, `GOVERNMENT`, `BUSINESS_OWNER`, `FREELANCE`, `DRIVER`, `ENGINEER`, `TEACHER`
- กำหนด `risk_weight` เริ่มต้น เช่น -10 ถึง +15

### 5) Loan Purposes
- `HOME_PURCHASE`, `HOME_IMPROVEMENT`, `BUSINESS`, `CAR`, `PERSONAL`, `EDUCATION`, `MEDICAL`, `DEBT_REFINANCE`

### 6) Recommendation Templates
- by `risk_level` + `recommendation_type`
  - LOW + APPROVE
  - MEDIUM + REVIEW_MANUAL
  - HIGH + REJECT_OR_ADDITIONAL_COLLATERAL

### 7) Risk Rule Templates
ตัวอย่าง rule:
- `DTI_HIGH`: if `dti >= 0.6` score -20
- `INCOME_LOW`: if `monthly_income < 15000` score -15
- `TENURE_SHORT`: if `job_tenure_months < 12` score -10
- `PAYMENT_HISTORY_GOOD`: no default in 12 months score +15

### 8) Dummy Assessments (5-10 cases)
ต้องครอบคลุมทุกกลุ่ม:
- 3 low risk
- 3 medium risk
- 2 high risk
และมีทั้ง `APPROVE`, `REVIEW_MANUAL`, `REJECT`

## Seed Validation Checklist
หลัง seed ต้องตรวจ:
1. login admin ได้
2. dashboard summary มีค่าไม่เป็นศูนย์
3. history list มีมากกว่า 5 รายการ
4. detail page เปิดได้อย่างน้อย 1 low/1 medium/1 high
5. form-options return dropdown data ครบ

## Rollback Plan
- ใช้ transaction ต่อชุด seed
- ถ้าล้มเหลว rollback batch นั้น
- เก็บ log ลง `system_seed_histories` เฉพาะสำเร็จเท่านั้น

## Production Safety
- ห้าม hardcode password ใน repo
- `INITIAL_ADMIN_PASSWORD` ต้องมาจาก secret manager / env
- บังคับเปลี่ยน password ครั้งแรก
- ปิด endpoint seed ใน production หรือจำกัด ADMIN + internal IP

## Mapping with Current Backend
ระบบปัจจุบันมี:
- FastAPI + PostgreSQL
- `prediction_logs` table และ `/health`, `/db-health`, `/predict`, `/predictions`

แผน transition:
1. เพิ่ม migration สำหรับ schema ใหม่
2. เพิ่ม seed module (`app/seed/*`)
3. เริ่มใช้ `/api/v1/*` ควบคู่กับ endpoint เดิม
4. ค่อย migrate frontend ไป endpoint ใหม่ครบชุด
