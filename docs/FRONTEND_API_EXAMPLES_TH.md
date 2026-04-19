# Frontend API Examples (พร้อมกรอกข้อมูล)

เอกสารนี้รวมตัวอย่าง Request/Response แบบกรอกข้อมูลครบ เอาไปใช้กับ Postman หรือ frontend ได้ทันที

## 1) ตั้งค่า Environment (Postman)

- `baseUrl` = `http://127.0.0.1:8000`
- `adminEmail` = `admin@example.com`
- `adminPassword` = `Admin1234!`
- `accessToken` = *(เว้นว่างก่อน)*
- `refreshToken` = *(เว้นว่างก่อน)*
- `assessmentId` = *(เว้นว่างก่อน)*

---

## 2) ลำดับทดสอบแบบครบ loop

1. `GET {{baseUrl}}/api/v1/health`
2. `POST {{baseUrl}}/api/v1/admin/seed` (ครั้งแรก)
3. `POST {{baseUrl}}/api/v1/auth/login`
4. `GET {{baseUrl}}/api/v1/auth/me`
5. `GET {{baseUrl}}/api/v1/assessments/form-options`
6. `POST {{baseUrl}}/api/v1/assessments` (create draft)
7. `POST {{baseUrl}}/api/v1/assessments/calculate`
8. `POST {{baseUrl}}/api/v1/assessments/{{assessmentId}}/submit`
9. `GET {{baseUrl}}/api/v1/assessments/{{assessmentId}}/result`
10. `GET {{baseUrl}}/api/v1/assessments?page=1&pageSize=10`

---

## 3) ตัวอย่างพร้อมใช้: Auth

### 3.1 Login
`POST {{baseUrl}}/api/v1/auth/login`

```json
{
  "usernameOrEmail": "{{adminEmail}}",
  "password": "{{adminPassword}}",
  "rememberMe": true
}
```

หลังยิงสำเร็จให้เก็บ:
- `data.accessToken` -> `{{accessToken}}`
- `data.refreshToken` -> `{{refreshToken}}`

### 3.2 Refresh
`POST {{baseUrl}}/api/v1/auth/refresh`

```json
{
  "refreshToken": "{{refreshToken}}"
}
```

### 3.3 Logout
`POST {{baseUrl}}/api/v1/auth/logout`

```json
{
  "refreshToken": "{{refreshToken}}"
}
```

---

## 4) ตัวอย่างพร้อมใช้: Assessment (กรอกข้อมูลครบ)

Header สำหรับทุกเส้นในหมวดนี้:
- `Authorization: Bearer {{accessToken}}`
- `Content-Type: application/json`

### 4.1 Create Assessment (Draft)
`POST {{baseUrl}}/api/v1/assessments`

```json
{
  "applicantProfile": {
    "firstName": "สมชาย",
    "lastName": "ใจดี",
    "nationalIdHash": "f7a2f2f39a6cbaf5f266f1f5838d6e2a8f79953f4bfa9e05f618d51a7b9fcb10",
    "dateOfBirth": "1991-04-10",
    "maritalStatus": "MARRIED",
    "provinceCode": "10",
    "district": "บางกะปิ",
    "postalCode": "10240"
  },
  "employmentInfo": {
    "occupationCode": "OFFICER",
    "employmentType": "FULL_TIME",
    "employerName": "ABC Company",
    "jobTenureMonths": 62,
    "monthlyIncome": 45000,
    "additionalIncome": 5000
  },
  "financialInfo": {
    "requestedLoanAmount": 850000,
    "loanTermMonths": 60,
    "loanPurposeCode": "HOME_PURCHASE",
    "monthlyDebtPayment": 12500,
    "existingLoanBalance": 285000
  },
  "debtInfos": [
    {
      "debtType": "PERSONAL_LOAN",
      "creditorName": "Bank A",
      "outstandingAmount": 180000,
      "monthlyPayment": 8500,
      "delinquentDays": 0,
      "isDefaulted": false
    },
    {
      "debtType": "CREDIT_CARD",
      "creditorName": "Bank B",
      "outstandingAmount": 105000,
      "monthlyPayment": 4000,
      "delinquentDays": 0,
      "isDefaulted": false
    }
  ],
  "note": "ลูกค้าต้องการวงเงินเพื่อซื้อบ้าน"
}
```

Response สำคัญ:
- `data.assessmentId` เก็บไปใส่ `{{assessmentId}}`

### 4.2 Calculate Preview
`POST {{baseUrl}}/api/v1/assessments/calculate`

ใช้ body เดียวกับ create ได้เลย

### 4.3 Update Draft
`PUT {{baseUrl}}/api/v1/assessments/{{assessmentId}}`

ใช้ body เดียวกับ create ได้เลย (แก้ค่าตามที่ต้องการ)

### 4.4 Submit
`POST {{baseUrl}}/api/v1/assessments/{{assessmentId}}/submit`

Body: none

### 4.5 Read Result
- `GET {{baseUrl}}/api/v1/assessments/{{assessmentId}}/result`
- `GET {{baseUrl}}/api/v1/assessments/{{assessmentId}}/risk-factors`
- `GET {{baseUrl}}/api/v1/assessments/{{assessmentId}}/recommendations`

### 4.6 History + Detail
- `GET {{baseUrl}}/api/v1/assessments?page=1&pageSize=10&search=&riskLevel=&status=`
- `GET {{baseUrl}}/api/v1/assessments/{{assessmentId}}/detail`

---

## 5) ตัวอย่างพร้อมใช้: Dashboard

Header:
- `Authorization: Bearer {{accessToken}}`

- `GET {{baseUrl}}/api/v1/dashboard/summary`
- `GET {{baseUrl}}/api/v1/dashboard/risk-distribution`
- `GET {{baseUrl}}/api/v1/dashboard/recent-assessments?limit=5`
- `GET {{baseUrl}}/api/v1/dashboard/key-insights`

---

## 6) ตัวอย่างพร้อมใช้: Admin

### 6.1 Seed (ครั้งแรก)
`POST {{baseUrl}}/api/v1/admin/seed`

```json
{
  "seedVersion": "v1.0.0",
  "includeDummyAssessments": true
}
```

### 6.2 List Users
`GET {{baseUrl}}/api/v1/admin/users?page=1&pageSize=20`

### 6.3 Create User
`POST {{baseUrl}}/api/v1/admin/users`

```json
{
  "fullName": "Analyst User",
  "username": "analyst1",
  "email": "analyst1@example.com",
  "role": "ANALYST",
  "password": "Analyst1234!"
}
```

### 6.4 Reset Password
`PATCH {{baseUrl}}/api/v1/admin/users/{userId}/reset-password`

```json
{
  "newPassword": "Temp1234!",
  "forceChangeOnNextLogin": true
}
```

---

## 7) Legacy Predict API (สำหรับโมเดลเดิม `/predict`)

ถ้า frontend จะยิง endpoint เดิมโดยตรง:

`POST {{baseUrl}}/predict`

```json
{
  "threshold": 0.5,
  "payload": {
    "รหัสลูกค้า": 910001,
    "ประเภทสินเชื่อ": "Cash loans",
    "เพศ": "F",
    "มีรถยนต์": "N",
    "มีอสังหาริมทรัพย์": "Y",
    "จำนวนบุตร": 1,
    "รายได้รวม": 300000,
    "วงเงินสินเชื่อ": 450000,
    "ค่างวดรายงวด": 23000,
    "ราคาสินค้า": 430000,
    "ประเภทอาชีพรายได้": "Working",
    "ระดับการศึกษา": "Higher education",
    "สถานภาพครอบครัว": "Married",
    "ประเภทที่อยู่อาศัย": "House / apartment",
    "อายุวันเกิด": -14000,
    "อายุงานวัน": -2800,
    "จำนวนสมาชิกครอบครัว": 3,
    "คะแนนภายนอก2": 0.61,
    "คะแนนภายนอก3": 0.47
  }
}
```

---

## 8) Error Cases ที่ควรทดสอบ

1. ไม่ส่ง token ใน protected API -> `401`
2. ใช้ token หมดอายุ -> `401`
3. role ไม่ถึง (เช่น analyst เรียก admin API) -> `403`
4. assessment id ไม่ถูก -> `404`
5. submit ทั้งที่ข้อมูลไม่ครบ -> `400`
6. seed version ซ้ำ -> `409`
