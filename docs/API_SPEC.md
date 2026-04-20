# API Spec (Frontend Friendly)

เอกสารนี้ทำให้ frontend เชื่อมได้เร็วที่สุด โดยยึดจาก backend ปัจจุบันในโปรเจกต์นี้

## 1) Base Config
- Base URL: `http://127.0.0.1:8000`
- API Prefix (ใหม่): `/api/v1`
- Content-Type: `application/json; charset=utf-8`
- Auth: Bearer Token (`Authorization: Bearer <accessToken>`)

## 2) Response Pattern

### Success
```json
{
  "success": true,
  "message": "OK",
  "data": {}
}
```

### Error
```json
{
  "detail": "AUTH_INVALID_CREDENTIALS"
}
```

หมายเหตุ: ตอนนี้บาง endpoint ใช้ `HTTPException` จึงตอบ error เป็น `detail` (FastAPI default)

## 3) Auth Flow (Frontend ใช้จริง)
1. `POST /api/v1/auth/login` -> ได้ `accessToken`, `refreshToken`
2. เก็บ `accessToken` ใน memory/state (แนะนำ), `refreshToken` ใน secure storage
3. แนบ header `Authorization: Bearer {{accessToken}}` กับทุก protected API
4. token หมดอายุ -> เรียก `POST /api/v1/auth/refresh`
5. logout -> `POST /api/v1/auth/logout`

---

## 4) Quick Start Endpoints (แนะนำลำดับเรียก)

1. `GET /api/v1/health`
2. `POST /api/v1/admin/seed` (ครั้งแรก)
3. `POST /api/v1/auth/login`
4. `GET /api/v1/auth/me`
5. `GET /api/v1/dashboard/summary`
6. `GET /api/v1/assessments/form-options`
7. `POST /api/v1/assessments`
8. `POST /api/v1/assessments/{id}/submit`
9. `GET /api/v1/assessments/{id}/result`
10. `GET /api/v1/assessments?page=1&pageSize=10`
11. `POST /api/v1/predict` (โมเดลตรงแบบ v1)

---

## 5) Auth APIs

### POST `/api/v1/auth/login`
Body:
```json
{
  "usernameOrEmail": "admin@example.com",
  "password": "Admin1234!",
  "rememberMe": true
}
```
Response 200:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "accessToken": "<token>",
    "refreshToken": "<token>",
    "expiresIn": 3600,
    "user": {
      "id": "uuid",
      "fullName": "System Admin",
      "email": "admin@example.com",
      "role": "ADMIN",
      "forceChangePassword": true
    }
  }
}
```

### POST `/api/v1/auth/refresh`
Body:
```json
{
  "refreshToken": "<token>"
}
```

### POST `/api/v1/auth/logout`
Body:
```json
{
  "refreshToken": "<token>"
}
```

### GET `/api/v1/auth/me`
Header: `Authorization: Bearer <accessToken>`

---

## 6) Dashboard APIs

### GET `/api/v1/dashboard/summary`
### GET `/api/v1/dashboard/risk-distribution`
### GET `/api/v1/dashboard/recent-assessments?limit=5`
### GET `/api/v1/dashboard/key-insights`

Header ทุกเส้น: `Authorization: Bearer <accessToken>`

---

## 7) Model / Input APIs (v1)

### GET `/api/v1/model-info`
### GET `/api/v1/input-template`
### GET `/api/v1/input-catalog`
### GET `/api/v1/input-summary`
### POST `/api/v1/predict`
### GET `/api/v1/predictions`
### GET `/api/v1/predictions/{predictionId}`

---

## 8) Assessment APIs

### GET `/api/v1/assessments/form-options`
ใช้โหลด dropdown ทั้งหมดสำหรับหน้าแบบฟอร์ม

### POST `/api/v1/assessments`
สร้าง draft ใหม่

Body ตัวอย่าง:
```json
{
  "applicantProfile": {
    "firstName": "ทดสอบ",
    "lastName": "ระบบ",
    "dateOfBirth": "1992-05-10",
    "maritalStatus": "MARRIED",
    "provinceCode": "10",
    "district": "บางกะปิ"
  },
  "employmentInfo": {
    "occupationCode": "OFFICER",
    "employmentType": "FULL_TIME",
    "jobTenureMonths": 36,
    "monthlyIncome": 42000,
    "additionalIncome": 2000
  },
  "financialInfo": {
    "requestedLoanAmount": 650000,
    "loanTermMonths": 48,
    "loanPurposeCode": "HOME_IMPROVEMENT",
    "monthlyDebtPayment": 12000,
    "existingLoanBalance": 210000
  },
  "debtInfos": [
    {
      "debtType": "PERSONAL_LOAN",
      "outstandingAmount": 210000,
      "monthlyPayment": 12000,
      "delinquentDays": 0,
      "isDefaulted": false
    }
  ]
}
```

Response สำคัญ:
```json
{
  "success": true,
  "message": "Assessment created",
  "data": {
    "assessmentId": "uuid",
    "assessmentNo": "CR-2026-000001",
    "status": "DRAFT"
  }
}
```

### POST `/api/v1/assessments/calculate`
คำนวณ preview score โดยยังไม่ submit
- ฝั่ง backend จะ “แปลงฟอร์ม” ให้เป็นฟีเจอร์ของโมเดล Home Credit แล้วค่อยยิงโมเดล
- รองรับการส่ง field โมเดลจริงเป็น key อังกฤษแทรกมาใน nested section ได้ (เช่น `CODE_GENDER`, `AMT_INCOME_TOTAL`) เพื่อให้โมเดลได้ค่าจริงมากขึ้น
- ตัวอย่าง: ส่ง `gender: "M"` ใน `applicantProfile` จะถูก map ไปเป็น `CODE_GENDER`
- ผลลัพธ์ `scoreBreakdown` / `riskFactors` / `recommendations` จะถูกสร้างจาก logic เดียวกับตอน `submit` เพื่อให้ “ผลก่อนบันทึก” และ “ผลหลังบันทึก” ตรงกัน

### PUT `/api/v1/assessments/{assessmentId}`
อัปเดต draft

### GET `/api/v1/assessments/{assessmentId}`
โหลดข้อมูลเดิมมาแก้ไข

### POST `/api/v1/assessments/{assessmentId}/submit`
ส่งประเมิน final + บันทึกผล

### GET `/api/v1/assessments/{assessmentId}/result`
ผลคะแนนหลัก

### GET `/api/v1/assessments/{assessmentId}/risk-factors`
ปัจจัยเสี่ยงที่ใช้แสดงในหน้า result/detail

### GET `/api/v1/assessments/{assessmentId}/recommendations`
คำแนะนำการตัดสินใจ

### GET `/api/v1/assessments?page=1&pageSize=20&search=&riskLevel=&status=`
หน้าประวัติ (มี pagination)

### GET `/api/v1/assessments/{assessmentId}/detail`
ข้อมูลรวมทั้งเคส

### POST `/api/v1/assessments/{assessmentId}/re-evaluate`
เฉพาะ ADMIN

---

## 9) Admin APIs

### POST `/api/v1/admin/seed`
Body:
```json
{
  "seedVersion": "v1.0.0",
  "includeDummyAssessments": true
}
```
หมายเหตุ:
- ถ้ายังไม่มี user ในระบบ เรียกได้โดยไม่ต้อง token
- ถ้ามี user แล้ว ต้องเป็น ADMIN

### GET `/api/v1/admin/users?page=1&pageSize=20`
เฉพาะ ADMIN

### POST `/api/v1/admin/users`
เฉพาะ ADMIN

### PATCH `/api/v1/admin/users/{userId}/reset-password`
เฉพาะ ADMIN

---

## 10) System APIs

### GET `/api/v1/health`
### GET `/api/v1/db-health`

---

## 11) Legacy APIs (ยังใช้ได้)

ระบบยังมี endpoint รุ่นเดิมสำหรับโมเดลเดิม:
- `GET /health`
- `GET /db-health`
- `GET /model-info`
- `GET /input-template`
- `GET /input-catalog`
- `GET /input-summary`
- `POST /predict`
- `GET /predictions`
- `GET /predictions/{predictionId}`

ถ้า frontend ใหม่ แนะนำใช้ `/api/v1/*` เป็นหลัก

---

## 12) Frontend Integration Notes

1. เก็บ `accessToken` ไว้ใน memory (state/store) และแนบ Bearer ทุกครั้ง
2. ทำ interceptor:
   - ถ้า 401 -> เรียก `/api/v1/auth/refresh` -> retry request เดิม
3. list หน้า history ใช้ `page/pageSize` รูปแบบเดียวกัน
4. ฟอร์มให้ดึง options จาก `/api/v1/assessments/form-options` ทุกครั้งตอนเข้า page
5. ถ้าใช้โมเดลตรงผ่าน `/api/v1/predict` หรือ `/predict` ให้เก็บ `requestId` จาก response แล้วใช้ `GET /api/v1/predictions/{predictionId}` หรือ `GET /predictions/{predictionId}` เพื่อโหลดรายละเอียดที่บันทึก

---

## 13) Minimal cURL Examples

### Login
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"usernameOrEmail\":\"admin@example.com\",\"password\":\"Admin1234!\",\"rememberMe\":true}"
```

### Dashboard Summary
```bash
curl "http://127.0.0.1:8000/api/v1/dashboard/summary" \
  -H "Authorization: Bearer <accessToken>"
```

### Create Assessment
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/assessments" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d "{...}"
```

---

## 14) Ready-to-Use Example Files

- `examples/api_v1_seed.json`
- `examples/api_v1_login_admin.json`
- `examples/api_v1_create_assessment_full.json`
- `examples/predict_th_minimal.json` (legacy `/predict`)
- `examples/predict_th_full.json` (legacy `/predict`)
