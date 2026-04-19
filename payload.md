# payload.md

สเปก payload สำหรับ Frontend (ไทย+อังกฤษ) ใช้งานกับ POST /predict ได้ตรงทันที

## 1) รูปแบบ Request

- Endpoint: POST /predict
- รองรับ 2 โหมด: Single (payload object), Batch (payload array)
- threshold อยู่ในช่วง 0-1

## 2) สรุปจำนวนฟิลด์

- ฟิลด์ดิบที่โมเดลรับได้ทั้งหมด: 121
- ฟิลด์ขั้นต่ำแนะนำสำหรับหน้าเว็บ: 19
- ฟิลด์เสริมแนะนำ: 19

## 2.1) ไฟล์ตัวอย่างพร้อมใช้ (ไทย + อังกฤษ)

- อังกฤษครบทุกฟิลด์ 121 ตัว: `examples/predict_en_full.json`
- ไทยตาม alias ที่ระบบรองรับ: `examples/predict_th_mapped_full.json`
- ไฟล์เทียบไทย/อังกฤษในไฟล์เดียว: `examples/predict_full_th_en.json`
- อังกฤษแบบไม่รวม `FLAG_DOCUMENT_*`: `examples/predict_en_full_no_documents.json`
- ไทยแบบไม่รวม `FLAG_DOCUMENT_*`: `examples/predict_th_mapped_no_documents.json`

ตัวอย่างรูปแบบที่หน้าเว็บส่งได้ทันที:

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
    "วงเงินสินเชื่อ": 450000
  },
  "threshold": 0.5
}
```

## 3) รายการ Attribute ทั้งหมดที่ API รับ

| # | EN Attribute | TH Attribute | Type | ระดับการใช้งาน | ตัวเลือก (ถ้ามี) |
|---|---|---|---|---|---|
| 1 | SK_ID_CURR | รหัสลูกค้า | number | ขั้นต่ำ | - |
| 2 | NAME_CONTRACT_TYPE | ประเภทสินเชื่อ | category | ขั้นต่ำ | <code>Cash loans</code><br><code>Revolving loans</code> |
| 3 | CODE_GENDER | เพศ | category | ขั้นต่ำ | <code>F</code><br><code>M</code> |
| 4 | FLAG_OWN_CAR | มีรถยนต์ | category | ขั้นต่ำ | <code>N</code><br><code>Y</code> |
| 5 | FLAG_OWN_REALTY | มีอสังหาริมทรัพย์ | category | ขั้นต่ำ | <code>N</code><br><code>Y</code> |
| 6 | CNT_CHILDREN | จำนวนบุตร | number | ขั้นต่ำ | - |
| 7 | AMT_INCOME_TOTAL | รายได้รวม | number | ขั้นต่ำ | - |
| 8 | AMT_CREDIT | วงเงินสินเชื่อ | number | ขั้นต่ำ | - |
| 9 | AMT_ANNUITY | ค่างวดรายงวด | number | ขั้นต่ำ | - |
| 10 | AMT_GOODS_PRICE | ราคาสินค้า | number | ขั้นต่ำ | - |
| 11 | NAME_TYPE_SUITE | ผู้ติดตามตอนยื่นกู้ | category | ทางเลือก | <code>Children</code><br><code>Family</code><br><code>Group of people</code><br><code>Other_A</code><br><code>Other_B</code><br><code>Spouse, partner</code><br><code>Unaccompanied</code> |
| 12 | NAME_INCOME_TYPE | ประเภทอาชีพรายได้ | category | ขั้นต่ำ | <code>Businessman</code><br><code>Commercial associate</code><br><code>Pensioner</code><br><code>State servant</code><br><code>Student</code><br><code>Unemployed</code><br><code>Working</code> |
| 13 | NAME_EDUCATION_TYPE | ระดับการศึกษา | category | ขั้นต่ำ | <code>Academic degree</code><br><code>Higher education</code><br><code>Incomplete higher</code><br><code>Lower secondary</code><br><code>Secondary / secondary special</code> |
| 14 | NAME_FAMILY_STATUS | สถานภาพครอบครัว | category | ขั้นต่ำ | <code>Civil marriage</code><br><code>Married</code><br><code>Separated</code><br><code>Single / not married</code><br><code>Widow</code> |
| 15 | NAME_HOUSING_TYPE | ประเภทที่อยู่อาศัย | category | ขั้นต่ำ | <code>Co-op apartment</code><br><code>House / apartment</code><br><code>Municipal apartment</code><br><code>Office apartment</code><br><code>Rented apartment</code><br><code>With parents</code> |
| 16 | REGION_POPULATION_RELATIVE | สัดส่วนประชากรภูมิภาค | number | แนะนำ | - |
| 17 | DAYS_BIRTH | อายุวันเกิด | number | ขั้นต่ำ | - |
| 18 | DAYS_EMPLOYED | อายุงานวัน | number | ขั้นต่ำ | - |
| 19 | DAYS_REGISTRATION | วันเปลี่ยนทะเบียนบ้าน | number | แนะนำ | - |
| 20 | DAYS_ID_PUBLISH | วันเปลี่ยนเอกสาร | number | แนะนำ | - |
| 21 | OWN_CAR_AGE | อายุรถ | number | แนะนำ | - |
| 22 | FLAG_MOBIL | มีมือถือ | number | ทางเลือก | - |
| 23 | FLAG_EMP_PHONE | มีเบอร์ที่ทำงาน | number | ทางเลือก | - |
| 24 | FLAG_WORK_PHONE | มีโทรศัพท์บ้าน | number | ทางเลือก | - |
| 25 | FLAG_CONT_MOBILE | มีมือถือที่ติดต่อได้ | number | ทางเลือก | - |
| 26 | FLAG_PHONE | มีโทรศัพท์ | number | ทางเลือก | - |
| 27 | FLAG_EMAIL | มีอีเมล | number | ทางเลือก | - |
| 28 | OCCUPATION_TYPE | อาชีพ | category | แนะนำ | <code>Accountants</code><br><code>Cleaning staff</code><br><code>Cooking staff</code><br><code>Core staff</code><br><code>Drivers</code><br><code>High skill tech staff</code><br><code>HR staff</code><br><code>IT staff</code><br><code>Laborers</code><br><code>Low-skill Laborers</code><br><code>Managers</code><br><code>Medicine staff</code><br><code>Private service staff</code><br><code>Realty agents</code><br><code>Sales staff</code><br><code>Secretaries</code><br><code>Security staff</code><br><code>Waiters/barmen staff</code> |
| 29 | CNT_FAM_MEMBERS | จำนวนสมาชิกครอบครัว | number | ขั้นต่ำ | - |
| 30 | REGION_RATING_CLIENT | เรตติ้งภูมิภาคลูกค้า | number | แนะนำ | - |
| 31 | REGION_RATING_CLIENT_W_CITY | เรตติ้งภูมิภาคพร้อมเมือง | number | แนะนำ | - |
| 32 | WEEKDAY_APPR_PROCESS_START | วันในสัปดาห์ที่ยื่น | category | แนะนำ | <code>FRIDAY</code><br><code>MONDAY</code><br><code>SATURDAY</code><br><code>SUNDAY</code><br><code>THURSDAY</code><br><code>TUESDAY</code><br><code>WEDNESDAY</code> |
| 33 | HOUR_APPR_PROCESS_START | ชั่วโมงที่ยื่น | number | แนะนำ | - |
| 34 | REG_REGION_NOT_LIVE_REGION | ทะเบียนอยู่ภูมิภาคเดิมหรือไม่ | number | ทางเลือก | - |
| 35 | REG_REGION_NOT_WORK_REGION | ทะเบียนทำงานต่างภูมิภาคหรือไม่ | number | ทางเลือก | - |
| 36 | LIVE_REGION_NOT_WORK_REGION | อยู่จริงทำงานต่างภูมิภาคหรือไม่ | number | ทางเลือก | - |
| 37 | REG_CITY_NOT_LIVE_CITY | ทะเบียนอยู่ต่างเมืองหรือไม่ | number | ทางเลือก | - |
| 38 | REG_CITY_NOT_WORK_CITY | ทะเบียนทำงานต่างเมืองหรือไม่ | number | ทางเลือก | - |
| 39 | LIVE_CITY_NOT_WORK_CITY | อยู่จริงทำงานต่างเมืองหรือไม่ | number | ทางเลือก | - |
| 40 | ORGANIZATION_TYPE | ประเภทองค์กร | category | แนะนำ | <code>Advertising</code><br><code>Agriculture</code><br><code>Bank</code><br><code>Business Entity Type 1</code><br><code>Business Entity Type 2</code><br><code>Business Entity Type 3</code><br><code>Cleaning</code><br><code>Construction</code><br><code>Culture</code><br><code>Electricity</code><br><code>Emergency</code><br><code>Government</code><br><code>Hotel</code><br><code>Housing</code><br><code>Industry: type 1</code><br><code>Industry: type 10</code><br><code>Industry: type 11</code><br><code>Industry: type 12</code><br><code>Industry: type 13</code><br><code>Industry: type 2</code><br><code>Industry: type 3</code><br><code>Industry: type 4</code><br><code>Industry: type 5</code><br><code>Industry: type 6</code><br><code>Industry: type 7</code><br><code>Industry: type 8</code><br><code>Industry: type 9</code><br><code>Insurance</code><br><code>Kindergarten</code><br><code>Legal Services</code><br><code>Medicine</code><br><code>Military</code><br><code>Mobile</code><br><code>Other</code><br><code>Police</code><br><code>Postal</code><br><code>Realtor</code><br><code>Religion</code><br><code>Restaurant</code><br><code>School</code><br><code>Security</code><br><code>Security Ministries</code><br><code>Self-employed</code><br><code>Services</code><br><code>Telecom</code><br><code>Trade: type 1</code><br><code>Trade: type 2</code><br><code>Trade: type 3</code><br><code>Trade: type 4</code><br><code>Trade: type 5</code><br><code>Trade: type 6</code><br><code>Trade: type 7</code><br><code>Transport: type 1</code><br><code>Transport: type 2</code><br><code>Transport: type 3</code><br><code>Transport: type 4</code><br><code>University</code><br><code>XNA</code> |
| 41 | EXT_SOURCE_1 | คะแนนภายนอก1 | number | แนะนำ | - |
| 42 | EXT_SOURCE_2 | คะแนนภายนอก2 | number | ขั้นต่ำ | - |
| 43 | EXT_SOURCE_3 | คะแนนภายนอก3 | number | ขั้นต่ำ | - |
| 44 | APARTMENTS_AVG | - | number | ทางเลือก | - |
| 45 | BASEMENTAREA_AVG | - | number | ทางเลือก | - |
| 46 | YEARS_BEGINEXPLUATATION_AVG | - | number | ทางเลือก | - |
| 47 | YEARS_BUILD_AVG | - | number | ทางเลือก | - |
| 48 | COMMONAREA_AVG | - | number | ทางเลือก | - |
| 49 | ELEVATORS_AVG | - | number | ทางเลือก | - |
| 50 | ENTRANCES_AVG | - | number | ทางเลือก | - |
| 51 | FLOORSMAX_AVG | - | number | ทางเลือก | - |
| 52 | FLOORSMIN_AVG | - | number | ทางเลือก | - |
| 53 | LANDAREA_AVG | - | number | ทางเลือก | - |
| 54 | LIVINGAPARTMENTS_AVG | - | number | ทางเลือก | - |
| 55 | LIVINGAREA_AVG | - | number | ทางเลือก | - |
| 56 | NONLIVINGAPARTMENTS_AVG | - | number | ทางเลือก | - |
| 57 | NONLIVINGAREA_AVG | - | number | ทางเลือก | - |
| 58 | APARTMENTS_MODE | - | number | ทางเลือก | - |
| 59 | BASEMENTAREA_MODE | - | number | ทางเลือก | - |
| 60 | YEARS_BEGINEXPLUATATION_MODE | - | number | ทางเลือก | - |
| 61 | YEARS_BUILD_MODE | - | number | ทางเลือก | - |
| 62 | COMMONAREA_MODE | - | number | ทางเลือก | - |
| 63 | ELEVATORS_MODE | - | number | ทางเลือก | - |
| 64 | ENTRANCES_MODE | - | number | ทางเลือก | - |
| 65 | FLOORSMAX_MODE | - | number | ทางเลือก | - |
| 66 | FLOORSMIN_MODE | - | number | ทางเลือก | - |
| 67 | LANDAREA_MODE | - | number | ทางเลือก | - |
| 68 | LIVINGAPARTMENTS_MODE | - | number | ทางเลือก | - |
| 69 | LIVINGAREA_MODE | - | number | ทางเลือก | - |
| 70 | NONLIVINGAPARTMENTS_MODE | - | number | ทางเลือก | - |
| 71 | NONLIVINGAREA_MODE | - | number | ทางเลือก | - |
| 72 | APARTMENTS_MEDI | - | number | ทางเลือก | - |
| 73 | BASEMENTAREA_MEDI | - | number | ทางเลือก | - |
| 74 | YEARS_BEGINEXPLUATATION_MEDI | - | number | ทางเลือก | - |
| 75 | YEARS_BUILD_MEDI | - | number | ทางเลือก | - |
| 76 | COMMONAREA_MEDI | - | number | ทางเลือก | - |
| 77 | ELEVATORS_MEDI | - | number | ทางเลือก | - |
| 78 | ENTRANCES_MEDI | - | number | ทางเลือก | - |
| 79 | FLOORSMAX_MEDI | - | number | ทางเลือก | - |
| 80 | FLOORSMIN_MEDI | - | number | ทางเลือก | - |
| 81 | LANDAREA_MEDI | - | number | ทางเลือก | - |
| 82 | LIVINGAPARTMENTS_MEDI | - | number | ทางเลือก | - |
| 83 | LIVINGAREA_MEDI | - | number | ทางเลือก | - |
| 84 | NONLIVINGAPARTMENTS_MEDI | - | number | ทางเลือก | - |
| 85 | NONLIVINGAREA_MEDI | - | number | ทางเลือก | - |
| 86 | FONDKAPREMONT_MODE | - | category | ทางเลือก | <code>not specified</code><br><code>org spec account</code><br><code>reg oper account</code><br><code>reg oper spec account</code> |
| 87 | HOUSETYPE_MODE | - | category | ทางเลือก | <code>block of flats</code><br><code>specific housing</code><br><code>terraced house</code> |
| 88 | TOTALAREA_MODE | สัดส่วนพื้นที่รวม | number | แนะนำ | - |
| 89 | WALLSMATERIAL_MODE | - | category | ทางเลือก | <code>Block</code><br><code>Mixed</code><br><code>Monolithic</code><br><code>Others</code><br><code>Panel</code><br><code>Stone, brick</code><br><code>Wooden</code> |
| 90 | EMERGENCYSTATE_MODE | - | category | ทางเลือก | <code>No</code><br><code>Yes</code> |
| 91 | OBS_30_CNT_SOCIAL_CIRCLE | จำนวนสังคมวงใกล้ชิด30วัน | number | แนะนำ | - |
| 92 | DEF_30_CNT_SOCIAL_CIRCLE | หนี้เสียวงใกล้ชิด30วัน | number | แนะนำ | - |
| 93 | OBS_60_CNT_SOCIAL_CIRCLE | จำนวนสังคมวงใกล้ชิด60วัน | number | แนะนำ | - |
| 94 | DEF_60_CNT_SOCIAL_CIRCLE | หนี้เสียวงใกล้ชิด60วัน | number | แนะนำ | - |
| 95 | DAYS_LAST_PHONE_CHANGE | วันเปลี่ยนเบอร์ล่าสุด | number | แนะนำ | - |
| 96 | FLAG_DOCUMENT_2 | - | number | ทางเลือก | - |
| 97 | FLAG_DOCUMENT_3 | - | number | ทางเลือก | - |
| 98 | FLAG_DOCUMENT_4 | - | number | ทางเลือก | - |
| 99 | FLAG_DOCUMENT_5 | - | number | ทางเลือก | - |
| 100 | FLAG_DOCUMENT_6 | - | number | ทางเลือก | - |
| 101 | FLAG_DOCUMENT_7 | - | number | ทางเลือก | - |
| 102 | FLAG_DOCUMENT_8 | - | number | ทางเลือก | - |
| 103 | FLAG_DOCUMENT_9 | - | number | ทางเลือก | - |
| 104 | FLAG_DOCUMENT_10 | - | number | ทางเลือก | - |
| 105 | FLAG_DOCUMENT_11 | - | number | ทางเลือก | - |
| 106 | FLAG_DOCUMENT_12 | - | number | ทางเลือก | - |
| 107 | FLAG_DOCUMENT_13 | - | number | ทางเลือก | - |
| 108 | FLAG_DOCUMENT_14 | - | number | ทางเลือก | - |
| 109 | FLAG_DOCUMENT_15 | - | number | ทางเลือก | - |
| 110 | FLAG_DOCUMENT_16 | - | number | ทางเลือก | - |
| 111 | FLAG_DOCUMENT_17 | - | number | ทางเลือก | - |
| 112 | FLAG_DOCUMENT_18 | - | number | ทางเลือก | - |
| 113 | FLAG_DOCUMENT_19 | - | number | ทางเลือก | - |
| 114 | FLAG_DOCUMENT_20 | - | number | ทางเลือก | - |
| 115 | FLAG_DOCUMENT_21 | - | number | ทางเลือก | - |
| 116 | AMT_REQ_CREDIT_BUREAU_HOUR | จำนวนขอเครดิตบูโรชั่วโมง | number | ทางเลือก | - |
| 117 | AMT_REQ_CREDIT_BUREAU_DAY | จำนวนขอเครดิตบูโรวัน | number | ทางเลือก | - |
| 118 | AMT_REQ_CREDIT_BUREAU_WEEK | จำนวนขอเครดิตบูโรสัปดาห์ | number | ทางเลือก | - |
| 119 | AMT_REQ_CREDIT_BUREAU_MON | จำนวนขอเครดิตบูโรรายเดือน | number | แนะนำ | - |
| 120 | AMT_REQ_CREDIT_BUREAU_QRT | จำนวนขอเครดิตบูโรไตรมาส | number | ทางเลือก | - |
| 121 | AMT_REQ_CREDIT_BUREAU_YEAR | จำนวนขอเครดิตบูโรปีนี้ | number | แนะนำ | - |

## 4) หมายเหตุสำหรับ Frontend

1. ใช้ key ไทยได้เมื่อมีในคอลัมน์ TH Attribute
2. ถ้า TH Attribute เป็น - ให้ส่ง key อังกฤษ
3. ช่องตัวเลขควรส่งเป็น number ไม่ใช่ string
4. ช่องว่างควรส่งเป็น null
5. ไม่จำเป็นต้องส่งครบทุกฟิลด์ API จะเติมฟิลด์ที่ขาดให้ก่อน preprocess

## 5) ตัวอย่างไฟล์ payload พร้อมใช้

- examples/predict_th_minimal.json
- examples/predict_th_full.json
- examples/predict_th_batch.json
