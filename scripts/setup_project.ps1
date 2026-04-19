param(
  [switch]$SkipTrain = $false,
  [switch]$StartDb = $false
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

Write-Host "==> Installing dependencies"
if (Get-Command py -ErrorAction SilentlyContinue) {
  py -m pip install -r requirements.txt
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  python -m pip install -r requirements.txt
} else {
  throw "Python ไม่พร้อมใช้งาน (ไม่พบคำสั่ง py/python)"
}

if (-not $SkipTrain) {
  Write-Host "==> Training model bundle"
  if (Get-Command py -ErrorAction SilentlyContinue) {
    py scripts/train_application_model.py
  } else {
    python scripts/train_application_model.py
  }
}

if ($StartDb) {
  Write-Host "==> Starting PostgreSQL via docker compose"
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
      docker compose version | Out-Null
      docker compose up -d postgres
    } catch {
      if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        docker-compose up -d postgres
      } else {
        throw "ไม่พบทั้ง docker compose และ docker-compose"
      }
    }
  } elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    docker-compose up -d postgres
  } else {
    throw "ไม่พบทั้ง docker compose และ docker-compose"
  }
}

Write-Host "==> Done. You can run API with: uvicorn app.main:app --reload --port 8000"
