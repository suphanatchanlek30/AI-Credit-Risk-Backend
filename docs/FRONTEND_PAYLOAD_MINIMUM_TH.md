# Frontend Payload Spec (TH/EN) - Minimum Set

เอกสารนี้สรุปเฉพาะ payload ขั้นต่ำที่คุณต้องการ (44 attributes) สำหรับยิง `POST /predict` ได้ทันที

## 1) Request Shape

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
    "ผู้ติดตามตอนยื่นกู้": "Unaccompanied",
    "ประเภทอาชีพรายได้": "Working",
    "ระดับการศึกษา": "Higher education",
    "สถานภาพครอบครัว": "Married",
    "ประเภทที่อยู่อาศัย": "House / apartment",
    "สัดส่วนประชากรภูมิภาค": 0.0188,
    "อายุวันเกิด": -14000,
    "อายุงานวัน": -3000,
    "วันเปลี่ยนทะเบียนบ้าน": -4000,
    "วันเปลี่ยนเอกสาร": -2000,
    "อายุรถ": 5,
    "มีมือถือ": 1,
    "มีเบอร์ที่ทำงาน": 1,
    "มีโทรศัพท์บ้าน": 0,
    "มีมือถือที่ติดต่อได้": 1,
    "มีโทรศัพท์": 1,
    "มีอีเมล": 0,
    "อาชีพ": "Laborers",
    "จำนวนสมาชิกครอบครัว": 3,
    "เรตติ้งภูมิภาคลูกค้า": 2,
    "เรตติ้งภูมิภาคพร้อมเมือง": 2,
    "วันในสัปดาห์ที่ยื่น": "WEDNESDAY",
    "ชั่วโมงที่ยื่น": 10,
    "ประเภทองค์กร": "Business Entity Type 3",
    "คะแนนภายนอก1": 0.72,
    "คะแนนภายนอก2": 0.63,
    "คะแนนภายนอก3": 0.51,
    "จำนวนสังคมวงใกล้ชิด30วัน": 2,
    "หนี้เสียวงใกล้ชิด30วัน": 0,
    "จำนวนสังคมวงใกล้ชิด60วัน": 2,
    "หนี้เสียวงใกล้ชิด60วัน": 0,
    "วันเปลี่ยนเบอร์ล่าสุด": -1000,
    "จำนวนขอเครดิตบูโรรายเดือน": 0,
    "จำนวนขอเครดิตบูโรปีนี้": 1
  },
  "threshold": 0.5
}
```

## 2) English Key Payload (Mapped)

```json
{
  "payload": {
    "SK_ID_CURR": 999999,
    "NAME_CONTRACT_TYPE": "Cash loans",
    "CODE_GENDER": "F",
    "FLAG_OWN_CAR": "N",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 1,
    "AMT_INCOME_TOTAL": 180000,
    "AMT_CREDIT": 450000,
    "AMT_ANNUITY": 23000,
    "AMT_GOODS_PRICE": 450000,
    "NAME_TYPE_SUITE": "Unaccompanied",
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "REGION_POPULATION_RELATIVE": 0.0188,
    "DAYS_BIRTH": -14000,
    "DAYS_EMPLOYED": -3000,
    "DAYS_REGISTRATION": -4000,
    "DAYS_ID_PUBLISH": -2000,
    "OWN_CAR_AGE": 5,
    "FLAG_MOBIL": 1,
    "FLAG_EMP_PHONE": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_CONT_MOBILE": 1,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Laborers",
    "CNT_FAM_MEMBERS": 3,
    "REGION_RATING_CLIENT": 2,
    "REGION_RATING_CLIENT_W_CITY": 2,
    "WEEKDAY_APPR_PROCESS_START": "WEDNESDAY",
    "HOUR_APPR_PROCESS_START": 10,
    "ORGANIZATION_TYPE": "Business Entity Type 3",
    "EXT_SOURCE_1": 0.72,
    "EXT_SOURCE_2": 0.63,
    "EXT_SOURCE_3": 0.51,
    "OBS_30_CNT_SOCIAL_CIRCLE": 2,
    "DEF_30_CNT_SOCIAL_CIRCLE": 0,
    "OBS_60_CNT_SOCIAL_CIRCLE": 2,
    "DEF_60_CNT_SOCIAL_CIRCLE": 0,
    "DAYS_LAST_PHONE_CHANGE": -1000,
    "AMT_REQ_CREDIT_BUREAU_MON": 0,
    "AMT_REQ_CREDIT_BUREAU_YEAR": 1
  },
  "threshold": 0.5
}
```

## 3) Value Maps (ใช้กับ UI/ผลลัพธ์)

- `0/1`: `0 = No/ไม่ใช่`, `1 = Yes/ใช่`
- `Y/N`: `Y = Yes/มี`, `N = No/ไม่มี`
- Gender: `F = Female/หญิง`, `M = Male/ชาย`
- Response decision:
  - `below_threshold = Good/ผ่านเกณฑ์`
  - `above_threshold = Bad/ความเสี่ยงสูง`
- Response risk band:
  - `low = ต่ำ`
  - `medium = ปานกลาง`
  - `high = สูง`

## 4) Attribute Catalog (ขั้นต่ำ 44 ตัว)

| # | TH | EN | Type | ตัวเลือกหลัก |
|---|---|---|---|---|
| 1 | รหัสลูกค้า | SK_ID_CURR | int | เลขจำนวนเต็ม |
| 2 | ประเภทสินเชื่อ | NAME_CONTRACT_TYPE | category | Cash loans, Revolving loans |
| 3 | เพศ | CODE_GENDER | category | F, M |
| 4 | มีรถยนต์ | FLAG_OWN_CAR | category | Y, N |
| 5 | มีอสังหาริมทรัพย์ | FLAG_OWN_REALTY | category | Y, N |
| 6 | จำนวนบุตร | CNT_CHILDREN | int | >= 0 |
| 7 | รายได้รวม | AMT_INCOME_TOTAL | float | >= 0 |
| 8 | วงเงินสินเชื่อ | AMT_CREDIT | float | > 0 |
| 9 | ค่างวดรายงวด | AMT_ANNUITY | float | > 0 |
| 10 | ราคาสินค้า | AMT_GOODS_PRICE | float | > 0 |
| 11 | ผู้ติดตามตอนยื่นกู้ | NAME_TYPE_SUITE | category | Unaccompanied, Family, Children, Spouse, partner, Other_A, Other_B, Group of people |
| 12 | ประเภทอาชีพรายได้ | NAME_INCOME_TYPE | category | Working, Commercial associate, Pensioner, State servant, Businessman, Student, Unemployed |
| 13 | ระดับการศึกษา | NAME_EDUCATION_TYPE | category | Higher education, Secondary / secondary special, Incomplete higher, Lower secondary, Academic degree |
| 14 | สถานภาพครอบครัว | NAME_FAMILY_STATUS | category | Married, Single / not married, Civil marriage, Separated, Widow |
| 15 | ประเภทที่อยู่อาศัย | NAME_HOUSING_TYPE | category | House / apartment, Rented apartment, With parents, Municipal apartment, Office apartment, Co-op apartment |
| 16 | สัดส่วนประชากรภูมิภาค | REGION_POPULATION_RELATIVE | float | 0-1 |
| 17 | อายุวันเกิด | DAYS_BIRTH | int | ติดลบ (จำนวนวันย้อนหลัง) |
| 18 | อายุงานวัน | DAYS_EMPLOYED | int | ติดลบ (จำนวนวันย้อนหลัง) |
| 19 | วันเปลี่ยนทะเบียนบ้าน | DAYS_REGISTRATION | float | ติดลบ |
| 20 | วันเปลี่ยนเอกสาร | DAYS_ID_PUBLISH | int | ติดลบ |
| 21 | อายุรถ | OWN_CAR_AGE | float | >= 0 หรือ null |
| 22 | มีมือถือ | FLAG_MOBIL | int | 0, 1 |
| 23 | มีเบอร์ที่ทำงาน | FLAG_EMP_PHONE | int | 0, 1 |
| 24 | มีโทรศัพท์บ้าน | FLAG_WORK_PHONE | int | 0, 1 |
| 25 | มีมือถือที่ติดต่อได้ | FLAG_CONT_MOBILE | int | 0, 1 |
| 26 | มีโทรศัพท์ | FLAG_PHONE | int | 0, 1 |
| 27 | มีอีเมล | FLAG_EMAIL | int | 0, 1 |
| 28 | อาชีพ | OCCUPATION_TYPE | category | Laborers, Sales staff, Core staff, Managers, Drivers, Accountants, Medicine staff, Security staff, Cleaning staff, Cooking staff, Private service staff, High skill tech staff, IT staff, HR staff, Secretaries, Waiters/barmen staff, Realty agents, Low-skill Laborers |
| 29 | จำนวนสมาชิกครอบครัว | CNT_FAM_MEMBERS | float | >= 1 |
| 30 | เรตติ้งภูมิภาคลูกค้า | REGION_RATING_CLIENT | int | 1, 2, 3 |
| 31 | เรตติ้งภูมิภาคพร้อมเมือง | REGION_RATING_CLIENT_W_CITY | int | 1, 2, 3 |
| 32 | วันในสัปดาห์ที่ยื่น | WEEKDAY_APPR_PROCESS_START | category | MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY |
| 33 | ชั่วโมงที่ยื่น | HOUR_APPR_PROCESS_START | int | 0-23 |
| 34 | ประเภทองค์กร | ORGANIZATION_TYPE | category | Business Entity Type 1/2/3, Government, Self-employed, School, Trade: type 1-7, Industry: type 1-13, Medicine, Bank, Construction, Transport: type 1-4, Housing, Military, Police, Security, Services, Telecom, Hotel, Restaurant, University, etc. |
| 35 | คะแนนภายนอก1 | EXT_SOURCE_1 | float | 0-1 หรือ null |
| 36 | คะแนนภายนอก2 | EXT_SOURCE_2 | float | 0-1 |
| 37 | คะแนนภายนอก3 | EXT_SOURCE_3 | float | 0-1 |
| 38 | จำนวนสังคมวงใกล้ชิด30วัน | OBS_30_CNT_SOCIAL_CIRCLE | float | >= 0 |
| 39 | หนี้เสียวงใกล้ชิด30วัน | DEF_30_CNT_SOCIAL_CIRCLE | float | >= 0 |
| 40 | จำนวนสังคมวงใกล้ชิด60วัน | OBS_60_CNT_SOCIAL_CIRCLE | float | >= 0 |
| 41 | หนี้เสียวงใกล้ชิด60วัน | DEF_60_CNT_SOCIAL_CIRCLE | float | >= 0 |
| 42 | วันเปลี่ยนเบอร์ล่าสุด | DAYS_LAST_PHONE_CHANGE | float | ติดลบ |
| 43 | จำนวนขอเครดิตบูโรรายเดือน | AMT_REQ_CREDIT_BUREAU_MON | float | >= 0 |
| 44 | จำนวนขอเครดิตบูโรปีนี้ | AMT_REQ_CREDIT_BUREAU_YEAR | float | >= 0 |

## 5) Frontend Validation แนะนำ

- `threshold`: 0.0 ถึง 1.0
- ฟิลด์คะแนน (`EXT_SOURCE_*`): จำกัดช่วง `0-1`
- ฟิลด์วันย้อนหลัง (`DAYS_*`): ควรเป็นค่าติดลบ
- ฟิลด์ boolean แบบตัวเลข (`FLAG_*`): รับเฉพาะ `0` หรือ `1`
- ฟิลด์ category: บังคับเลือกจากตัวเลือกในตาราง

## 6) ไฟล์อ้างอิงในโปรเจกต์

- Mapping หลัก: `config/thai_alias.json`
- Catalog (ตัวอย่าง/type): `config/input_catalog_th.json`
- ตัวอย่าง payload ไทยขั้นต่ำ: `examples/predict_th_frontend_minimum.json`
- ตัวอย่าง payload อังกฤษขั้นต่ำ: `examples/predict_en_frontend_minimum.json`
