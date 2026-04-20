# Frontend-Backend Master Handoff (Thai)

เอกสารนี้เป็นสรุป backend ทั้งหมดสำหรับทีม frontend: ระบบทำอะไร, endpoint ไหนใช้เมื่อไร, payload/response fields, auth flow, variables/env, business logic, และข้อควรระวังตอนเชื่อมจริง

---

## 1) ภาพรวมระบบ

- Backend framework: **FastAPI**
- Database: **PostgreSQL** (รองรับ sqlite fallback)
- Model inference: **LightGBM**
- มี API 2 ชุด:
  - **Legacy** (`/predict`, `/predictions`, `/health`, ...)
  - **v1** (`/api/v1/*`) สำหรับระบบหน้า dashboard/form/history/detail/admin

---

## 2) ตัวแปรระบบสำคัญ (Environment Variables)

อ้างอิงจาก `.env.example`

- `APP_NAME`
- `APP_ENV`
- `CORS_ALLOW_ORIGINS` (comma-separated)
- `APP_SECRET_KEY` (ใช้ sign access token)
- `ACCESS_TOKEN_MINUTES`
- `REFRESH_TOKEN_DAYS`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`
- `INITIAL_ADMIN_FULL_NAME`
- `DATABASE_URL` (local run)
- `DOCKER_DATABASE_URL` (docker internal)

Docker service vars:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST_PORT`
- `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`, `PGADMIN_HOST_PORT`
- `API_HOST_PORT`

---

## 3) Authentication / Authorization

### 3.1 Token model
- Access token: custom signed token (`Authorization: Bearer <token>`)
- Refresh token: เก็บ hash ในตาราง `refresh_tokens`

### 3.2 Role model
- `ADMIN`
- `ANALYST`
- บาง endpoint public เช่น health

### 3.3 Frontend auth flow
1. `POST /api/v1/auth/login`
2. เก็บ `accessToken` ใน memory/store
3. ส่ง Bearer token ทุก protected endpoint
4. 401 -> `POST /api/v1/auth/refresh` แล้ว retry
5. logout -> `POST /api/v1/auth/logout`

---

## 4) Response Contract (ของจริงในระบบ)

### 4.1 Success (ส่วนใหญ่ของ `/api/v1`)
```json
{
  "success": true,
  "message": "OK",
  "data": {}
}
```

### 4.2 Error (global normalized)
```json
{
  "success": false,
  "message": "AUTH_INVALID_CREDENTIALS",
  "errorCode": "UNAUTHORIZED",
  "errors": []
}
```

> หมายเหตุ: Legacy endpoint บางเส้นยังใช้ response style เดิม ไม่ได้ envelope เต็มแบบ v1

---

## 5) Endpoint Inventory ทั้งหมด

## 5.1 Legacy APIs

- `GET /health`
- `GET /db-health`
- `GET /model-info`
- `GET /input-template`
- `GET /input-catalog`
- `GET /input-summary`
- `POST /predict`
- `GET /predictions`

### Logic ย่อของ `POST /predict`
1. รับ payload ไทย/อังกฤษ (single/batch)
2. sanitize + แปลง key ไทย -> อังกฤษ
3. preprocess ตาม artifacts
4. predict default probability
5. map เป็น `decision`, `risk_band`
6. บันทึก `prediction_logs`
7. auto-create history เข้า `loan_assessments/risk_results/...` (best-effort)

---

## 5.2 v1 Auth

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

---

## 5.3 v1 System

- `GET /api/v1/health`
- `GET /api/v1/db-health`

---

## 5.4 v1 Model/Input

- `GET /api/v1/model-info`
- `GET /api/v1/input-template`
- `GET /api/v1/input-catalog`
- `GET /api/v1/input-summary`
- `POST /api/v1/predict`
- `GET /api/v1/predictions`

---

## 5.5 v1 Assessment (Form + Result + History)

- `GET /api/v1/assessments/form-options`
- `POST /api/v1/assessments`
- `PUT /api/v1/assessments/{assessment_id}`
- `POST /api/v1/assessments/calculate`
- `GET /api/v1/assessments/{assessment_id}`
- `POST /api/v1/assessments/{assessment_id}/submit`
- `GET /api/v1/assessments/{assessment_id}/result`
- `GET /api/v1/assessments/{assessment_id}/risk-factors`
- `GET /api/v1/assessments/{assessment_id}/recommendations`
- `GET /api/v1/assessments`
- `GET /api/v1/assessments/{assessment_id}/detail`
- `POST /api/v1/assessments/{assessment_id}/re-evaluate` (ADMIN)

---

## 5.6 v1 Dashboard

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/risk-distribution`
- `GET /api/v1/dashboard/recent-assessments?limit=5`
- `GET /api/v1/dashboard/key-insights`

---

## 5.7 v1 Admin

- `POST /api/v1/admin/seed`
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `PATCH /api/v1/admin/users/{user_id}/reset-password`

---

## 6) Form DTO ที่ frontend ต้องรู้

`POST/PUT /api/v1/assessments` ใช้ payload นี้:

- `applicantProfile`
  - `firstName`, `lastName`, `nationalIdHash?`, `dateOfBirth`, `maritalStatus?`, `provinceCode`, `district?`, `postalCode?`
- `employmentInfo`
  - `occupationCode`, `employmentType`, `employerName?`, `jobTenureMonths`, `monthlyIncome`, `additionalIncome`
- `financialInfo`
  - `requestedLoanAmount`, `loanTermMonths`, `loanPurposeCode`, `monthlyDebtPayment`, `existingLoanBalance`
- `debtInfos[]`
  - `debtType`, `creditorName?`, `outstandingAmount`, `monthlyPayment`, `delinquentDays`, `isDefaulted`
- `note?`

Validation หลัก:
- `monthlyIncome > 0`
- `requestedLoanAmount > 0`
- `loanTermMonths` ระหว่าง `6..120`
- debt/income fields ไม่ติดลบ

---

## 7) Data ที่ frontend ใช้ render หน้าต่างๆ

## 7.1 Dashboard
- summary cards:
  - `totalAssessments`, `lowRiskCount`, `mediumRiskCount`, `highRiskCount`
- donut:
  - `distribution[].riskLevel/count/percent`
- recent table:
  - `assessmentId`, `assessmentNo`, `applicantName`, `score`, `riskLevel`, `createdAt`
- insight cards:
  - `insights[].type/title/description`

## 7.2 History
- `GET /api/v1/assessments`:
  - `items[]: id, assessmentNo, applicantName, status, submittedAt, score, riskLevel, recommendationType`
  - `pagination`

Query รองรับ:
- `page`, `pageSize`, `search`, `riskLevel`, `status`, `dateFrom`, `dateTo`, `sortBy`, `sortOrder`

หมายเหตุ sort:
- รองรับแน่นอน: `createdAt`, `submittedAt`
- `score` มี sorting ระดับ response side ใน service

## 7.3 Detail
- ใช้ `GET /api/v1/assessments/{id}/detail` เป็นเส้นหลัก
- ถ้าจะแยก component:
  - `/result`
  - `/risk-factors`
  - `/recommendations`

---

## 8) Scoring / Risk logic (ที่ใช้ใน assessment flow)

ฟังก์ชันหลัก: `calculate_risk(...)`

ตัวแปรที่ใช้:
- `age_years`
- `monthly_income`
- `job_tenure_months`
- `monthly_debt_payment`
- `has_defaulted`

ตรรกะหลักโดยย่อ:
- คำนวณ `dti = monthly_debt_payment / monthly_income`
- เริ่มจาก base score 100
- หัก/เพิ่มคะแนนตาม DTI, รายได้, อายุงาน, อายุ, ประวัติ default
- clamp score 0..100
- map เป็น:
  - `default_probability`
  - `risk_level` (`LOW/MEDIUM/HIGH`)
  - `recommendation_type` (`APPROVE/REVIEW_MANUAL/REJECT`)
  - `score_grade`
  - `credit_score`
- สร้าง `risk_factors` และ `recommendations`

---

## 9) Mapping ไทย-อังกฤษสำหรับ `/predict`

ใช้ไฟล์:
- `config/thai_alias.json`
- `config/input_catalog_th.json`

ถ้า frontend ยิง `/predict` โดยคีย์ไทย:
- backend จะ map ไทย -> อังกฤษก่อน preprocess

เอกสารฟอร์ม model เดิม:
- `docs/FRONTEND_FORM_SPEC_TH.md`
- `payload.md`

---

## 10) Database Entities ที่ frontend ควรรู้

ตารางสำคัญ:
- Auth: `roles`, `users`, `refresh_tokens`
- Assessment: `loan_assessments`, `applicant_profiles`, `applicant_employment_infos`, `applicant_financial_infos`, `applicant_debt_infos`
- Result: `risk_results`, `risk_factors`, `risk_recommendations`
- Tracking: `assessment_status_logs`
- Model logs: `prediction_logs`
- Master/lookup: `provinces`, `occupations`, `loan_purposes`, `income_ranges`, `recommendation_templates`, `risk_rule_templates`

---

## 11) Known Gaps / Consistency Notes

1. มีทั้ง legacy และ v1 endpoints คู่ขนาน
2. success format ของ legacy ยังไม่เท่ากับ v1 ทั้งหมด
3. `/predict` และ `/api/v1/predict` มีความใกล้เคียงกันแต่ key casing ต่างกันบางส่วน (`default_probability` vs `defaultProbability`)
4. หาก frontend ใหม่ แนะนำใช้ `/api/v1/*` ก่อน

---

## 12) Frontend Integration Recipe (แนะนำจริง)

### Recipe A: ระบบหน้า dashboard/form/history/detail
- ใช้ `/api/v1/*` ทั้งหมด
- login -> dashboard -> form-options -> create/update/calculate/submit -> result/detail/history

### Recipe B: ยิงโมเดลเร็วๆ เฉพาะ prediction
- ใช้ `/api/v1/predict` (หรือ legacy `/predict`)
- ส่ง payload ขั้นต่ำ 19 ฟิลด์ขึ้นไป

---

## 13) Prompt Template ให้ทีม Frontend / AI Coding Assistant

```text
คุณคือ Senior Frontend Engineer
งาน: สร้างหน้าเว็บเชื่อม Backend Credit Risk ตามสเปกนี้

Base URL: http://127.0.0.1:8000
Auth: Bearer token จาก /api/v1/auth/login

สิ่งที่ต้องทำ:
1) ทำ Auth Store (accessToken/refreshToken)
2) ทำ API client พร้อม interceptor 401 -> refresh -> retry
3) ทำหน้า Dashboard:
   - /api/v1/dashboard/summary
   - /api/v1/dashboard/risk-distribution
   - /api/v1/dashboard/recent-assessments
   - /api/v1/dashboard/key-insights
4) ทำหน้า Assessment Form:
   - load options จาก /api/v1/assessments/form-options
   - create draft: POST /api/v1/assessments
   - update draft: PUT /api/v1/assessments/{id}
   - preview: POST /api/v1/assessments/calculate
   - submit: POST /api/v1/assessments/{id}/submit
5) ทำหน้า Result + Detail:
   - /api/v1/assessments/{id}/result
   - /api/v1/assessments/{id}/risk-factors
   - /api/v1/assessments/{id}/recommendations
   - /api/v1/assessments/{id}/detail
6) ทำหน้า History:
   - /api/v1/assessments?page=...&pageSize=...&search=...&riskLevel=...&status=...
7) รองรับ loading/error/empty state ทุกหน้า
8) ใช้ TypeScript interfaces ตาม field จาก API responses
9) แสดงวันที่เป็นโซน Asia/Bangkok ที่ UI
10) ห้าม hardcode token, ต้องใช้ environment variables
```

---

## 14) เอกสารอ้างอิงเพิ่มเติมในโปรเจกต์

- `docs/API_SPEC.md`
- `docs/FRONTEND_API_EXAMPLES_TH.md`
- `docs/FRONTEND_FORM_SPEC_TH.md`
- `docs/DATABASE_DESIGN.md`
- `docs/SEED_PLAN.md`
