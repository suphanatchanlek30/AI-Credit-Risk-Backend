$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

if (-not (Test-Path "artifacts\application_model_v1\model.txt")) {
  throw "ไม่พบโมเดล: artifacts\application_model_v1\model.txt (ให้ train ก่อน)"
}

function Invoke-Compose {
  param([string[]]$Args)
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
      docker compose version | Out-Null
      docker compose @Args
      return
    } catch {}
  }
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    docker-compose @Args
    return
  }
  throw "ไม่พบทั้ง docker compose และ docker-compose"
}

Invoke-Compose -Args @("up", "-d", "--build")
Write-Host "API: http://127.0.0.1:8000/docs"
Write-Host "pgAdmin: http://127.0.0.1:5050 (admin@example.com / admin1234)"
