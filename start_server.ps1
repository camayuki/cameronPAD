# Start CameronPAD server with UTF-8 encoding
# This prevents emoji encoding errors in Windows PowerShell

Write-Host "Starting CameronPAD Server..." -ForegroundColor Green
Write-Host "Setting UTF-8 encoding for console..." -ForegroundColor Yellow

# Set console output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Start uvicorn server
Write-Host "Launching uvicorn..." -ForegroundColor Cyan
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
