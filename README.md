# Credit Risk Backend (Refactored)

โปรเจกต์นี้ถูกจัดโครงสร้างใหม่ให้พร้อมใช้งานจริง:
- FastAPI สำหรับรับข้อมูลจากเว็บ
- โมเดล LightGBM สำหรับคำนวณความเสี่ยง
- PostgreSQL สำหรับเก็บ prediction logs
- Docker Compose สำหรับยกทั้ง stack
- ชุดทดสอบ API ทั้งแบบ PowerShell และ pytest

---

## 1) โครงสร้างโปรเจกต์ (หลังรีแฟกเตอร์)

```text
app/
  main.py                  # API routes หลัก
  db/
    session.py             # DB engine/session/create table
    models.py              # ตาราง prediction_logs
    repository.py          # บันทึก/อ่าน logs
  ml/
    preprocessing.py       # preprocess train/inference
    model_bundle.py        # save/load model + preprocess artifacts

config/
  thai_alias.json          # mapping key ภาษาไทย -> key โมเดล
  input_catalog_th.json    # catalog ฟิลด์สำหรับ frontend form

scripts/
  train_application_model.py
  setup_project.ps1
  run_api.ps1
  test_api.ps1             # ยิง endpoint ครบด้วย PowerShell
  test_api_py.ps1          # รัน pytest
  docker_up.ps1
  docker_down.ps1

examples/
  predict_th_minimal.json
  predict_th_full.json
  predict_th_batch.json

tests/
  test_api_live.py         # integration tests กับ API ที่กำลังรันอยู่

docker-compose.yml
Dockerfile
.env.example
requirements.txt
requirements-dev.txt

legacy/competition_assets/ # ไฟล์เก่าจากงานแข่งขัน (ย้ายออกจาก runtime path แล้ว)
```

---

## 2) สิ่งที่ใช้จริง vs ไม่ใช้จริง

### ใช้จริง (runtime)
- `app/`
- `config/`
- `scripts/`
- `examples/`
- `docker-compose.yml`, `Dockerfile`, `.env`
- `artifacts/application_model_v1/*` (โมเดลที่เทรนแล้ว)

### ย้ายออกแล้ว (ไม่อยู่ใน flow runtime)
- `Feature/`, `Model/`, `EDA.ipynb`, `Feature Selection.ipynb`, `only_application_pred.csv`, `README_DEPLOY_TH.md`
- ถูกย้ายไป `legacy/competition_assets/`

---

## 3) Payload รองรับกี่ฟิลด์

จาก artifact ที่เทรนล่าสุด:
- Raw input fields จากโมเดล: **121**
- Features หลัง preprocess: **132**

จาก catalog สำหรับ frontend:
- ฟิลด์ขั้นต่ำ (minimum form): **19**
- ฟิลด์แนะนำเพิ่ม (extended): **19**
- รายการฟิลด์ใน catalog: **55**

ดูแบบ runtime ได้จาก endpoint:
- `GET /input-summary`

---

## 4) API ทั้งหมด

1. `GET /health`
2. `GET /db-health`
3. `GET /model-info`
4. `GET /input-template`
5. `GET /input-catalog`
6. `GET /input-summary`
7. `POST /predict`
8. `GET /predictions?limit=20`

Swagger:
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 5) Setup ตั้งแต่ต้นจนจบ (PowerShell)

### Step 0: เข้าโฟลเดอร์
```powershell
cd C:\Projects_ai_cs271\Credit-Default-Risk-Solution-model-test
```

### Step 1: ติดตั้ง dependency
```powershell
py -m pip install -r requirements.txt
```

### Step 2: เทรนโมเดล
```powershell
py scripts/train_application_model.py
```

ต้องได้ไฟล์:
- `artifacts\application_model_v1\model.txt`
- `artifacts\application_model_v1\preprocess.json`
- `artifacts\application_model_v1\metrics.json`

### Step 3: ตั้งค่า env
```powershell
copy .env.example .env
```

### Step 4: เปิด PostgreSQL (docker)
```powershell
docker-compose up -d postgres
```
หรือ
```powershell
docker compose up -d postgres
```

### Step 5: ตั้ง DATABASE_URL ตามพอร์ตจริง
ตัวอย่างถ้า postgres map เป็น `5435`:
```powershell
$env:DATABASE_URL="postgresql+psycopg://credit_user:credit_pass@localhost:5435/credit_risk"
```

### Step 6: รัน API
```powershell
uvicorn app.main:app --reload --port 8000
```

### Step 7: เทส endpoint ครบ
เปิด PowerShell ใหม่:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_api.ps1
```

---

## 6) Run แบบ Docker ทั้งระบบ

1. train โมเดลบน host ให้เสร็จก่อน
2. รัน:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\docker_up.ps1
```
3. เทส:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_api.ps1
```
4. ปิด:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\docker_down.ps1
```

pgAdmin:
- [http://127.0.0.1:5050](http://127.0.0.1:5050)
- user: `admin@example.com`
- pass: `admin1234`

---

## 7) วิธีเทส API ทั้งหมด

## 7.1 PowerShell test script
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_api.ps1
```
ครอบคลุม:
- health, db-health, model-info
- input-template, input-catalog, input-summary
- predict single, predict batch
- prediction logs

## 7.2 pytest integration
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_api_py.ps1
```
ไฟล์เทส:
- `tests/test_api_live.py`

---

## 8) ตัวอย่าง payload สำหรับ frontend

- Minimal: [examples/predict_th_minimal.json](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/examples/predict_th_minimal.json)
- Full: [examples/predict_th_full.json](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/examples/predict_th_full.json)
- Batch: [examples/predict_th_batch.json](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/examples/predict_th_batch.json)

หมายเหตุ:
- รองรับ key ภาษาไทยผ่าน `config/thai_alias.json`
- ถ้า frontend ส่ง key อังกฤษก็ได้เหมือนกัน

---

## 9) เอกสาร frontend แบบละเอียด

ดูไฟล์:
- [docs/FRONTEND_API_GUIDE_TH.md](/C:/Projects_ai_cs271/Credit-Default-Risk-Solution-model-test/docs/FRONTEND_API_GUIDE_TH.md)

เนื้อหาในไฟล์นี้ครอบคลุม:
- flow frontend -> backend
- validation
- single/batch payload
- ตัวอย่าง fetch
- วิธี render ผล
- debug checklist

---

## 10) Output จาก `/predict` (เวอร์ชันปัจจุบัน)

แต่ละ prediction จะมี:
- `index`
- `default_probability`
- `decision` (ไทย)
- `decision_en` (อังกฤษ)
- `risk_band` (ไทย)
- `risk_band_en` (อังกฤษ)
- `threshold`
- `request_id` (id ที่บันทึกลง DB)

---

## 11) ปัญหาที่เจอบ่อย

1. `Model bundle not found`
- ให้รัน train ก่อน

2. `db_connected=false`
- เช็ก postgres container และ `DATABASE_URL`
- เช็กพอร์ต host ที่ map จริง (`docker-compose ps`)

3. ภาษาไทยเพี้ยนใน PowerShell
- เป็น encoding ของ terminal
- ดูผ่าน Swagger จะเห็นไทยปกติ

4. `docker compose` ใช้ไม่ได้
- ลอง `docker-compose`
- สคริปต์ที่ให้รองรับสองแบบแล้ว

---

## 12) API v1 (Auth + Dashboard + Assessment + Admin + Seed)

หลังอัปเดตล่าสุด มี endpoint เพิ่มภายใต้ `/api/v1` ครบตามโครงออกแบบ เช่น:
- `/api/v1/auth/*`
- `/api/v1/dashboard/*`
- `/api/v1/assessments/*`
- `/api/v1/admin/*`

### Seed ระบบครั้งแรก
```powershell
py scripts/seed_system.py --version v1.0.0 --with-demo true
```

### เทส API v1 แบบครบ flow
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_api_v1.ps1
```

เอกสารสเปก:
- `docs/API_SPEC.md`
- `docs/DATABASE_DESIGN.md`
- `docs/SEED_PLAN.md`
