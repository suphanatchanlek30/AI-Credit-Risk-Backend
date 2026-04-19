param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [int]$MaxWaitSeconds = 60
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

Write-Host "==> Waiting API ready (max $MaxWaitSeconds sec)"
$ready = $false
$deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
while ((Get-Date) -lt $deadline) {
  try {
    $h = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 5
    if ($h.status -eq "ok") {
      $ready = $true
      break
    }
  } catch {
    Start-Sleep -Seconds 2
  }
}

if (-not $ready) {
  throw "API ไม่พร้อมในเวลาที่กำหนด. ตรวจสอบ log ของ uvicorn/docker แล้วลองใหม่"
}

Write-Host "==> Health"
Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET | ConvertTo-Json -Depth 6

Write-Host "==> DB Health"
Invoke-RestMethod -Uri "$BaseUrl/db-health" -Method GET | ConvertTo-Json -Depth 6

Write-Host "==> Model Info"
Invoke-RestMethod -Uri "$BaseUrl/model-info" -Method GET | ConvertTo-Json -Depth 6

Write-Host "==> Input Template"
Invoke-RestMethod -Uri "$BaseUrl/input-template" -Method GET | ConvertTo-Json -Depth 6

Write-Host "==> Input Catalog"
Invoke-RestMethod -Uri "$BaseUrl/input-catalog" -Method GET | ConvertTo-Json -Depth 6

Write-Host "==> Input Summary"
Invoke-RestMethod -Uri "$BaseUrl/input-summary" -Method GET | ConvertTo-Json -Depth 8

Write-Host "==> Predict (example payload)"
$body = Get-Content -Raw -LiteralPath ".\examples\predict_th_full.json"
Invoke-RestMethod -Uri "$BaseUrl/predict" -Method POST -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8

Write-Host "==> Predict (batch payload)"
$batchBody = Get-Content -Raw -LiteralPath ".\examples\predict_th_batch.json"
Invoke-RestMethod -Uri "$BaseUrl/predict" -Method POST -ContentType "application/json" -Body $batchBody | ConvertTo-Json -Depth 8

Write-Host "==> Latest prediction logs"
Invoke-RestMethod -Uri "$BaseUrl/predictions?limit=5" -Method GET | ConvertTo-Json -Depth 8
