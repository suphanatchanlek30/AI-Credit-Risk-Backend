$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

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

Invoke-Compose -Args @("down")
