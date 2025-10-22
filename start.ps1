# CameronPAD Start Script for Windows
# This script starts the CameronPAD server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      Starting CameronPAD Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please run .\install.ps1 first" -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$packagesOk = $true

try {
    python -c "import fastapi" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    Write-Host "✗ FastAPI not found. Please run .\install.ps1" -ForegroundColor Red
    $packagesOk = $false
}

if (-not $packagesOk) {
    exit 1
}

Write-Host "✓ Dependencies OK" -ForegroundColor Green

# Check for .env file
if (!(Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠ Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "  Some features may not work without API keys" -ForegroundColor Gray
    Write-Host "  Run .\install.ps1 to create .env from template" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Server will start at:" -ForegroundColor White
Write-Host "  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
