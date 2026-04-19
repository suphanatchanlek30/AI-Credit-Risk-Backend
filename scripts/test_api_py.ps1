param(
  [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

if (Get-Command py -ErrorAction SilentlyContinue) {
  py -m pip install -r requirements-dev.txt
  $env:API_BASE_URL = $BaseUrl
  py -m pytest -q tests\test_api_live.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  python -m pip install -r requirements-dev.txt
  $env:API_BASE_URL = $BaseUrl
  python -m pytest -q tests\test_api_live.py
} else {
  throw "ไม่พบคำสั่ง py/python"
}
