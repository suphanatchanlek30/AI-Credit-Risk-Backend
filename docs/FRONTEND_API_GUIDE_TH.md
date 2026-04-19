# Frontend Integration Guide (TH)

คู่มือนี้สรุปแบบละเอียดสำหรับทีม Frontend เพื่อเชื่อมกับ Backend (FastAPI) ที่พร้อมใช้งานแล้ว

## 1) Base URL
- Local: `http://127.0.0.1:8000`

## 2) Endpoints ที่ควรใช้จาก Frontend
1. `GET /health`  
   ใช้เช็คว่า API พร้อมตอบไหม
2. `GET /input-catalog`  
   ใช้สร้างฟอร์มแบบ dynamic จาก catalog ภาษาไทย
3. `GET /input-summary`  
   ใช้รู้จำนวนฟิลด์ทั้งหมด/ขั้นต่ำ/แนะนำ
4. `POST /predict`  
   ส่งข้อมูลเพื่อคำนวณความเสี่ยง

## 3) จำนวนฟิลด์ payload
ระบบมี endpoint บอกจำนวนจริง:
- `GET /input-summary`

ค่าที่ได้สำคัญ:
- `raw_input_field_count_from_model`: จำนวนฟิลด์ดิบที่โมเดลรองรับ (จาก artifact)
- `minimum_web_form_field_count`: จำนวนฟิลด์ขั้นต่ำที่แนะนำให้กรอก
- `recommended_extended_field_count`: ฟิลด์เสริมที่ช่วยเพิ่มความแม่น
- `catalog_field_count`: จำนวนรายการใน catalog ฟอร์ม

## 4) รูปแบบ request ที่รองรับ

### 4.1 Single payload
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

### 4.2 Batch payload
```json
{
  "threshold": 0.45,
  "payload": [
    { "รหัสลูกค้า": 920001, "เพศ": "F", "รายได้รวม": 720000, "วงเงินสินเชื่อ": 850000, "ค่างวดรายงวด": 35600, "ราคาสินค้า": 780000, "จำนวนสมาชิกครอบครัว": 3, "อายุวันเกิด": -13700, "อายุงานวัน": -4200, "คะแนนภายนอก2": 0.72, "คะแนนภายนอก3": 0.58 },
    { "รหัสลูกค้า": 920002, "เพศ": "M", "รายได้รวม": 288000, "วงเงินสินเชื่อ": 420000, "ค่างวดรายงวด": 24800, "ราคาสินค้า": 400000, "จำนวนสมาชิกครอบครัว": 4, "อายุวันเกิด": -11950, "อายุงานวัน": -1600, "คะแนนภายนอก2": 0.49, "คะแนนภายนอก3": 0.37 }
  ]
}
```

## 5) รูปแบบ response
```json
{
  "predictions": [
    {
      "index": 0,
      "default_probability": 0.022307,
      "decision": "ความเสี่ยงต่ำกว่าเกณฑ์",
      "decision_en": "below_threshold",
      "risk_band": "ต่ำ",
      "risk_band_en": "low",
      "threshold": 0.5,
      "request_id": 3
    }
  ],
  "model_version": "application_model_v1"
}
```

## 6) Frontend validation ที่ควรมี
1. `payload` ต้องไม่ว่าง
2. ถ้าเป็น single ให้เป็น object
3. ถ้าเป็น batch ให้เป็น array และ length > 0
4. `threshold` ควรอยู่ในช่วง `[0,1]`
5. ค่าตัวเลขส่งเป็น number (ไม่ใช่ string) ถ้าทำได้
6. ช่องว่าง (`""`) ควรแปลงเป็น `null`

## 7) ตัวอย่าง fetch (JavaScript)
```javascript
async function predictRisk(data) {
  const res = await fetch("http://127.0.0.1:8000/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status}: ${txt}`);
  }
  return res.json();
}
```

## 8) การ render ผลลัพธ์
- แสดง `default_probability` เป็น `%`
- แสดง `decision` หรือ `decision_en` ตาม locale
- แสดง `risk_band` สีแนะนำ:
  - `ต่ำ/low` = เขียว
  - `กลาง/medium` = ส้ม
  - `สูง/high` = แดง
- เก็บ `request_id` ไว้ใช้ audit/replay

## 9) Debug checklist
1. `GET /health` ต้องได้ `ok`
2. `GET /db-health` ต้องได้ `db_connected=true`
3. ถ้า response ไทยเพี้ยนใน terminal ให้ดูผ่าน browser/Swagger แทน
4. ถ้า error 422 ให้เช็คโครง JSON ไม่ตรง schema
