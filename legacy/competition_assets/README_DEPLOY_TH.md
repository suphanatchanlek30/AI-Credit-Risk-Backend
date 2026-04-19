# Deploy โมเดลเป็น FastAPI (ภาษาไทย)

ไฟล์นี้เป็นแนวทางเอาโมเดลไปใช้งานจริงแบบ
- หน้าเว็บกรอกข้อมูล
- ส่ง JSON เข้า FastAPI
- API preprocess + predict
- ส่งผลความเสี่ยงกลับหน้าเว็บ

## สิ่งที่เพิ่มให้แล้ว
- [scripts/train_application_model.py](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/scripts/train_application_model.py)
- [app/main.py](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/app/main.py)
- [app/ml/preprocessing.py](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/app/ml/preprocessing.py)
- [app/ml/model_bundle.py](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/app/ml/model_bundle.py)
- [config/thai_alias.json](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/config/thai_alias.json)
- [requirements.txt](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/requirements.txt)

## ขั้นตอนรัน
1. ติดตั้ง dependency
```bash
pip install -r requirements.txt
```

2. เทรนและบันทึกโมเดล bundle
```bash
python scripts/train_application_model.py
```
หรือ
```bash
py scripts/train_application_model.py
```

3. รัน API
```bash
uvicorn app.main:app --reload --port 8000
```

4. ทดสอบ
- `GET /health`
- `GET /model-info`
- `GET /input-template`
- `POST /predict`

## ตัวอย่าง request (ส่งชื่อฟิลด์ภาษาไทยได้)
```json
{
  "payload": {
    "รหัสลูกค้า": 999999,
    "ประเภทสินเชื่อ": "Cash loans",
    "เพศ": "F",
    "มีรถยนต์": "N",
    "มีอสังหาริมทรัพย์": "Y",
    "จำนวนบุตร": 1,
    "รายได้รวม": 180000,
    "วงเงินสินเชื่อ": 450000,
    "ค่างวดรายงวด": 23000,
    "ราคาสินค้า": 450000,
    "ระดับการศึกษา": "Higher education",
    "สถานภาพครอบครัว": "Married",
    "ประเภทที่อยู่อาศัย": "House / apartment",
    "อายุวันเกิด": -14000,
    "อายุงานวัน": -3000,
    "จำนวนสมาชิกครอบครัว": 3
  }
}
```

## ตัวอย่าง response
```json
{
  "default_probability": 0.183251,
  "decision": "ความเสี่ยงต่ำกว่าเกณฑ์",
  "threshold": 0.5,
  "model_version": "application_model_v1"
}
```

## หมายเหตุสำคัญก่อนขึ้น production
- ตอนนี้ threshold ตั้งตายตัวที่ `0.5` ควรปรับจาก business target จริง
- ควรเพิ่ม input validation เฉพาะฟิลด์ที่หน้าเว็บส่งจริง (Pydantic schema แบบเจาะจง)
- ควรทำ auth/rate limit/logging สำหรับ API จริง
- ควร version model และแยก staging/prod
