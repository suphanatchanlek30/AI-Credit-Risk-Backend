# Flow การทำงาน (ละเอียด) ตั้งแต่กรอกข้อมูลจนบันทึกผล

## 1. กรอกข้อมูลในฟอร์ม (Frontend)
- ผู้ใช้กรอกข้อมูลสมัครสินเชื่อ เช่น ข้อมูลส่วนตัว รายได้ อาชีพ ภาระหนี้ ฯลฯ
- เมื่อกรอกครบ กดปุ่ม "คำนวณ/ประเมิน" (Preview) หรือ "ยืนยันส่งคำขอ" (Submit)

---

## 2. เรียก API: Preview ผลประเมิน (ยังไม่บันทึก)
### Endpoint
- `POST /api/v1/assessments/calculate`

### Request ตัวอย่าง
```json
{
  "applicantProfile": {
    "dateOfBirth": "1990-01-01",
    "provinceCode": "10"
  },
  "employmentInfo": {
    "monthlyIncome": 25000,
    "jobTenureMonths": 36,
    "occupationCode": "OCC01"
  },
  "financialInfo": {
    "monthlyDebtPayment": 5000
  },
  "debtInfos": [
    { "isDefaulted": false }
  ]
}
```

### การประมวลผล
- Backend รับข้อมูล → แปลงข้อมูลสำหรับ ML → เรียก PredictionService → คำนวณ deterministic score → รวมผลลัพธ์

### Response ตัวอย่าง
```json
{
  "ok": true,
  "message": "คำนวณผลประเมินสำเร็จ",
  "data": {
    "summary": {
      "score": 68,
      "scoreScale": 100,
      "creditScore": 720,
      "scoreGrade": "B+",
      "riskLevel": "MEDIUM",
      "riskLevelLabel": "ความเสี่ยงปานกลาง",
      "defaultProbability": 0.23,
      "recommendationType": "REVIEW_MANUAL",
      "recommendationLabel": "ควรตรวจสอบเพิ่มเติม",
      "dti": 0.2
    },
    "modelPrediction": {
      "index": 0,
      "defaultProbability": 0.23,
      "decision": "ความเสี่ยงต่ำกว่าเกณฑ์",
      "decisionEn": "below_threshold",
      "riskBand": "กลาง",
      "riskBandEn": "medium",
      "threshold": 0.5,
      "modelVersion": "application_model_v1"
    },
    "scoreBreakdown": [
      { "code": "INCOME_STABILITY", "label": "รายได้มีความสม่ำเสมอ", "score": 20, "reason": "ผู้สมัครมีรายได้ประจำต่อเดือนในระดับเหมาะสม" }
    ],
    "riskFactors": [
      { "code": "HIGH_DEBT_BURDEN", "label": "ภาระหนี้ค่อนข้างสูง", "severity": "MEDIUM", "description": "ภาระหนี้ต่อรายได้อยู่ในระดับที่ควรเฝ้าระวัง" }
    ],
    "recommendations": [
      { "code": "VERIFY_INCOME", "label": "ตรวจสอบแหล่งที่มาของรายได้เพิ่มเติม", "description": "ควรขอเอกสารยืนยันรายได้เพิ่มเติมก่อนพิจารณาอนุมัติ" }
    ],
    "inputSnapshot": {
      "monthlyIncome": 25000,
      "monthlyDebtPayment": 5000,
      "occupation": "OCC01",
      "province": "10"
    }
  }
}
```

---

## 3. เรียก API: Submit (บันทึกผลจริง)
### Endpoint
- `POST /api/v1/assessments/{assessment_id}/submit`

### Request ตัวอย่าง
- ไม่ต้องมี body (ใช้ assessment_id ที่สร้างไว้แล้ว)

### การประมวลผล
- Backend ดึงข้อมูล assessment ที่กรอกไว้
- แปลงข้อมูล → เรียก PredictionService → คำนวณ deterministic score
- สร้าง RiskResult, RiskFactor, RiskRecommendation และบันทึกลงฐานข้อมูล
- อัปเดตสถานะ assessment เป็น COMPLETED

### Response ตัวอย่าง
```json
{
  "ok": true,
  "message": "บันทึกผลการประเมินสำเร็จ",
  "data": {
    "assessmentId": "a1b2c3d4",
    "assessmentNo": "20260420-0001",
    "status": "COMPLETED",
    "resultId": 101,
    "summary": {
      "score": 68,
      "creditScore": 720,
      "scoreGrade": "B+",
      "riskLevel": "MEDIUM",
      "riskLevelLabel": "ความเสี่ยงปานกลาง",
      "defaultProbability": 0.23,
      "recommendationType": "REVIEW_MANUAL",
      "recommendationLabel": "ควรตรวจสอบเพิ่มเติม"
    },
    "modelPrediction": {
      "defaultProbability": 0.23,
      "decision": "ความเสี่ยงต่ำกว่าเกณฑ์",
      "riskBand": "กลาง",
      "modelVersion": "application_model_v1"
    }
  }
}
```

---

## 4. การบันทึกข้อมูล (Persistence)
- ผลลัพธ์การประเมิน (RiskResult) จะถูกบันทึกลงฐานข้อมูล พร้อมรายละเอียดปัจจัย (RiskFactor) และคำแนะนำ (RiskRecommendation)
- อัปเดตสถานะ assessment และสร้าง log การเปลี่ยนสถานะ

---

## 5. สรุป Flow
1. กรอกข้อมูล → POST /api/v1/assessments/calculate (ดูผลประเมินเบื้องต้น)
2. ยืนยันส่งคำขอ → POST /api/v1/assessments/{assessment_id}/submit (บันทึกผลจริง)
3. ระบบประมวลผล, เรียก ML, คำนวณคะแนน, บันทึกผล, ตอบกลับข้อมูลสรุป

---

**อัปเดตล่าสุด:** 20 เมษายน 2026

---

## ตัวอย่าง Payload ที่ส่งเข้า ML Model (หลัง mapping/preprocess)

เมื่อระบบได้รับข้อมูลจากฟอร์ม จะมีการแปลงข้อมูลให้ตรงกับ input ที่โมเดลต้องการ เช่น:

### ตัวอย่างข้อมูลที่รับจากฟอร์ม (raw payload)
```json
{
  "applicantProfile": {
    "dateOfBirth": "1990-01-01",
    "provinceCode": "10"
  },
  "employmentInfo": {
    "monthlyIncome": 25000,
    "jobTenureMonths": 36,
    "occupationCode": "OCC01"
  },
  "financialInfo": {
    "monthlyDebtPayment": 5000
  },
  "debtInfos": [
    { "isDefaulted": false }
  ]
}
```

### ตัวอย่างข้อมูลที่ส่งเข้า ML Model (หลัง mapping/preprocess)
```json
{
  "monthly_income": 25000,
  "monthly_debt_payment": 5000,
  "occupation": "OCC01",
  "province": "10"
}
```

- ข้อมูลนี้จะถูกนำไป preprocess (normalize, encode ฯลฯ) ก่อนเข้าโมเดลจริง
- PredictionService จะดูแลการ mapping, alias, และ preprocessing ทั้งหมด
