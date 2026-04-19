# Frontend Form Spec (TH/EN) สำหรับ `POST /predict`

เอกสารนี้ใช้ทำฟอร์มหน้าเว็บให้ส่งเข้า API ได้ตรงทันที  
Endpoint: `POST /predict`  
Body shape:

```json
{
  "threshold": 0.5,
  "payload": {}
}
```

## 1) Required Fields (ขั้นต่ำต้องมี 19 ฟิลด์)

| TH | EN | UI Control | Type | Validation | Options |
|---|---|---|---|---|---|
| รหัสลูกค้า | SK_ID_CURR | number input | int | `>= 1` | - |
| ประเภทสินเชื่อ | NAME_CONTRACT_TYPE | select | enum | required | Cash loans, Revolving loans |
| เพศ | CODE_GENDER | select | enum | required | F, M |
| มีรถยนต์ | FLAG_OWN_CAR | select | enum | required | Y, N |
| มีอสังหาริมทรัพย์ | FLAG_OWN_REALTY | select | enum | required | Y, N |
| จำนวนบุตร | CNT_CHILDREN | number input | int | `>= 0` | - |
| รายได้รวม | AMT_INCOME_TOTAL | number input | float | `> 0` | - |
| วงเงินสินเชื่อ | AMT_CREDIT | number input | float | `> 0` | - |
| ค่างวดรายงวด | AMT_ANNUITY | number input | float | `> 0` | - |
| ราคาสินค้า | AMT_GOODS_PRICE | number input | float | `> 0` | - |
| ประเภทอาชีพรายได้ | NAME_INCOME_TYPE | select | enum | required | Working, Commercial associate, Pensioner, State servant, Businessman, Student, Unemployed |
| ระดับการศึกษา | NAME_EDUCATION_TYPE | select | enum | required | Higher education, Secondary / secondary special, Incomplete higher, Lower secondary, Academic degree |
| สถานภาพครอบครัว | NAME_FAMILY_STATUS | select | enum | required | Married, Single / not married, Civil marriage, Separated, Widow |
| ประเภทที่อยู่อาศัย | NAME_HOUSING_TYPE | select | enum | required | House / apartment, Rented apartment, With parents, Municipal apartment, Office apartment, Co-op apartment |
| อายุวันเกิด | DAYS_BIRTH | number input | int | `< 0` | - |
| อายุงานวัน | DAYS_EMPLOYED | number input | int | `<= 0` | - |
| จำนวนสมาชิกครอบครัว | CNT_FAM_MEMBERS | number input | float | `>= 1` | - |
| คะแนนภายนอก2 | EXT_SOURCE_2 | number input | float | `0 <= x <= 1` | - |
| คะแนนภายนอก3 | EXT_SOURCE_3 | number input | float | `0 <= x <= 1` | - |

## 2) Optional Recommended Fields (แนะนำเพิ่ม)

| TH | EN | UI Control | Type | Validation | Options |
|---|---|---|---|---|---|
| ผู้ติดตามตอนยื่นกู้ | NAME_TYPE_SUITE | select | enum | optional | Unaccompanied, Family, Children, Spouse, partner, Other_A, Other_B, Group of people |
| สัดส่วนประชากรภูมิภาค | REGION_POPULATION_RELATIVE | number input | float | `0 <= x <= 1` | - |
| วันเปลี่ยนทะเบียนบ้าน | DAYS_REGISTRATION | number input | float | `<= 0` | - |
| วันเปลี่ยนเอกสาร | DAYS_ID_PUBLISH | number input | int | `<= 0` | - |
| อายุรถ | OWN_CAR_AGE | number input | float | `>= 0` or `null` | - |
| มีมือถือ | FLAG_MOBIL | radio/select | int | `0 or 1` | 0, 1 |
| มีเบอร์ที่ทำงาน | FLAG_EMP_PHONE | radio/select | int | `0 or 1` | 0, 1 |
| มีโทรศัพท์บ้าน | FLAG_WORK_PHONE | radio/select | int | `0 or 1` | 0, 1 |
| มีมือถือที่ติดต่อได้ | FLAG_CONT_MOBILE | radio/select | int | `0 or 1` | 0, 1 |
| มีโทรศัพท์ | FLAG_PHONE | radio/select | int | `0 or 1` | 0, 1 |
| มีอีเมล | FLAG_EMAIL | radio/select | int | `0 or 1` | 0, 1 |
| อาชีพ | OCCUPATION_TYPE | select | enum | optional | Laborers, Sales staff, Core staff, Managers, Drivers, Accountants, Medicine staff, Security staff, Cleaning staff, Cooking staff, Private service staff, High skill tech staff, IT staff, HR staff, Secretaries, Waiters/barmen staff, Realty agents, Low-skill Laborers |
| เรตติ้งภูมิภาคลูกค้า | REGION_RATING_CLIENT | select | int | `1..3` | 1, 2, 3 |
| เรตติ้งภูมิภาคพร้อมเมือง | REGION_RATING_CLIENT_W_CITY | select | int | `1..3` | 1, 2, 3 |
| วันในสัปดาห์ที่ยื่น | WEEKDAY_APPR_PROCESS_START | select | enum | optional | MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY |
| ชั่วโมงที่ยื่น | HOUR_APPR_PROCESS_START | number input | int | `0..23` | - |
| ประเภทองค์กร | ORGANIZATION_TYPE | searchable select | enum | optional | Business Entity Type 1/2/3, Government, Self-employed, School, Trade/Industry groups, etc. |
| คะแนนภายนอก1 | EXT_SOURCE_1 | number input | float | `0 <= x <= 1` or `null` | - |
| สัดส่วนพื้นที่รวม | TOTALAREA_MODE | number input | float | `>= 0` or `null` | - |
| จำนวนสังคมวงใกล้ชิด30วัน | OBS_30_CNT_SOCIAL_CIRCLE | number input | float | `>= 0` | - |
| หนี้เสียวงใกล้ชิด30วัน | DEF_30_CNT_SOCIAL_CIRCLE | number input | float | `>= 0` | - |
| จำนวนสังคมวงใกล้ชิด60วัน | OBS_60_CNT_SOCIAL_CIRCLE | number input | float | `>= 0` | - |
| หนี้เสียวงใกล้ชิด60วัน | DEF_60_CNT_SOCIAL_CIRCLE | number input | float | `>= 0` | - |
| วันเปลี่ยนเบอร์ล่าสุด | DAYS_LAST_PHONE_CHANGE | number input | float | `<= 0` | - |
| จำนวนขอเครดิตบูโรรายเดือน | AMT_REQ_CREDIT_BUREAU_MON | number input | float | `>= 0` | - |
| จำนวนขอเครดิตบูโรปีนี้ | AMT_REQ_CREDIT_BUREAU_YEAR | number input | float | `>= 0` | - |

## 3) ฟิลด์พิเศษ

- `threshold`:
  - Type: `float`
  - Validation: `0 <= threshold <= 1`
  - Default แนะนำ: `0.5`

## 4) Rules ฝั่ง Frontend

1. ใช้คีย์ไทยหรือคีย์อังกฤษอย่างใดอย่างหนึ่งให้คงที่ทั้ง payload
2. ถ้าฟิลด์ว่าง ให้ส่ง `null` (ไม่ส่งเป็น `""`)
3. ฟิลด์ตัวเลขส่งเป็น number จริง ไม่ใช่ string
4. ฟิลด์ enum ต้องตรงตัวพิมพ์/ช่องว่างตาม options
5. ส่งขั้นต่ำ 19 ฟิลด์ก่อน แล้วค่อยเพิ่ม optional

## 5) ตัวอย่าง Payload (ขั้นต่ำ)

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

## 6) Mapping ที่เกี่ยวข้อง

- Thai alias mapping: `config/thai_alias.json`
- Catalog field examples: `config/input_catalog_th.json`
- Payload examples:
  - `examples/predict_th_minimal.json`
  - `examples/predict_th_full.json`
  - `examples/predict_th_batch.json`
