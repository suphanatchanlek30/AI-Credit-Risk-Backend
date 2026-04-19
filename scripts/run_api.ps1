$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

if (-not (Test-Path "artifacts\application_model_v1\model.txt")) {
  throw "ไม่พบโมเดลที่ train แล้ว: artifacts\application_model_v1\model.txt"
}

uvicorn app.main:app --reload --port 8000
