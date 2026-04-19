param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$AdminEmail = "admin@example.com",
  [string]$AdminPassword = "Admin1234!"
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Resolve-Path "$PSScriptRoot\..")

Write-Host "==> Health"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" -Method GET | ConvertTo-Json -Depth 8

Write-Host "==> Seed (first run can call without token)"
$seedBody = @{ seedVersion = "v1.0.0"; includeDummyAssessments = $true } | ConvertTo-Json
try {
  Invoke-RestMethod -Uri "$BaseUrl/api/v1/admin/seed" -Method POST -ContentType "application/json" -Body $seedBody | ConvertTo-Json -Depth 8
} catch {
  Write-Host "Seed may already be applied. Continuing..."
}

Write-Host "==> Login"
$loginBody = @{
  usernameOrEmail = $AdminEmail
  password = $AdminPassword
  rememberMe = $true
} | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
$token = $login.data.accessToken
$refreshToken = $login.data.refreshToken
$headers = @{ Authorization = "Bearer $token" }
$headersJson = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }

Write-Host "==> Me"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" -Method GET -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> Dashboard summary"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/dashboard/summary" -Method GET -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> Form options"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/assessments/form-options" -Method GET -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> Create assessment"
$createBody = @{
  applicantProfile = @{
    firstName = "ทดสอบ"
    lastName = "ระบบ"
    dateOfBirth = "1992-05-10"
    maritalStatus = "MARRIED"
    provinceCode = "10"
    district = "บางกะปิ"
  }
  employmentInfo = @{
    occupationCode = "OFFICER"
    employmentType = "FULL_TIME"
    jobTenureMonths = 36
    monthlyIncome = 42000
    additionalIncome = 2000
  }
  financialInfo = @{
    requestedLoanAmount = 650000
    loanTermMonths = 48
    loanPurposeCode = "HOME_IMPROVEMENT"
    monthlyDebtPayment = 12000
    existingLoanBalance = 210000
  }
  debtInfos = @(
    @{
      debtType = "PERSONAL_LOAN"
      outstandingAmount = 210000
      monthlyPayment = 12000
      delinquentDays = 0
      isDefaulted = $false
    }
  )
} | ConvertTo-Json -Depth 10
$created = Invoke-RestMethod -Uri "$BaseUrl/api/v1/assessments" -Method POST -Headers $headersJson -Body $createBody
$assessmentId = $created.data.assessmentId
$assessmentNo = $created.data.assessmentNo
Write-Host "Created assessment: $assessmentNo"

Write-Host "==> Submit assessment"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/assessments/$assessmentId/submit" -Method POST -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> Result"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/assessments/$assessmentId/result" -Method GET -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> History"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/assessments?page=1&pageSize=5" -Method GET -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> Admin users"
Invoke-RestMethod -Uri "$BaseUrl/api/v1/admin/users?page=1&pageSize=5" -Method GET -Headers $headers | ConvertTo-Json -Depth 8

Write-Host "==> Refresh"
$refreshBody = @{ refreshToken = $refreshToken } | ConvertTo-Json
Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/refresh" -Method POST -ContentType "application/json" -Body $refreshBody | ConvertTo-Json -Depth 8
