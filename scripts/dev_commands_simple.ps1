# CameronPAD Development Commands
# Source this file: . .\scripts\dev_commands.ps1

function Start-CameronPAD {
    Write-Host "Starting CameronPAD..." -ForegroundColor Green
    py scripts/dev_server.py
}

function Setup-CameronPAD {
    Write-Host "Setting up development environment..." -ForegroundColor Blue
    py scripts/setup_dev.py
}

function Reset-CameronPAD {
    Write-Host "Resetting development environment..." -ForegroundColor Yellow
    
    # Remove existing data
    if (Test-Path "data/cameronpad_dev.db") {
        Remove-Item "data/cameronpad_dev.db" -Force
        Write-Host "   Removed old database" -ForegroundColor Gray
    }
    
    # Re-setup
    py scripts/setup_dev.py
}

function Test-CameronPAD {
    Write-Host "Running tests..." -ForegroundColor Cyan
    if (Test-Path "tests") {
        py -m pytest tests/ -v
    } else {
        Write-Host "   No tests directory found" -ForegroundColor Yellow
    }
}

function Install-CameronPAD {
    Write-Host "Installing dependencies..." -ForegroundColor Magenta
    
    $packages = @(
        "fastapi",
        "uvicorn[standard]", 
        "jinja2",
        "python-multipart",
        "sqlalchemy",
        "aiosqlite",
        "pydantic[email]",
        "python-dotenv",
        "bcrypt",
        "python-jose[cryptography]",
        "passlib[bcrypt]"
    )
    
    foreach ($package in $packages) {
        Write-Host "   Installing $package..." -ForegroundColor Gray
        py -m pip install $package --upgrade
    }
    
    Write-Host "All dependencies installed!" -ForegroundColor Green
}

function Show-CameronPAD-Info {
    Write-Host "CameronPAD Development Information" -ForegroundColor Blue
    Write-Host "=================================" -ForegroundColor Blue
    Write-Host "Local URL:    http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "Admin Panel:  http://127.0.0.1:8000/admin" -ForegroundColor Yellow
    Write-Host "API Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Cyan
    Write-Host "Health Check: http://127.0.0.1:8000/health" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "Default Admin:" -ForegroundColor Blue
    Write-Host "   Username: admin" -ForegroundColor Gray
    Write-Host "   Password: admin123!" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Test User:" -ForegroundColor Blue
    Write-Host "   Username: testuser" -ForegroundColor Gray
    Write-Host "   Password: test123!" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Available Commands:" -ForegroundColor Blue
    Write-Host "   Start-CameronPAD    - Start development server" -ForegroundColor Gray
    Write-Host "   Setup-CameronPAD    - Setup/reset environment" -ForegroundColor Gray
    Write-Host "   Reset-CameronPAD    - Reset database and setup" -ForegroundColor Gray
    Write-Host "   Test-CameronPAD     - Run tests" -ForegroundColor Gray
    Write-Host "   Install-CameronPAD  - Install dependencies" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Quick Start:" -ForegroundColor Green
    Write-Host "   1. Install-CameronPAD" -ForegroundColor Gray
    Write-Host "   2. Setup-CameronPAD" -ForegroundColor Gray
    Write-Host "   3. Start-CameronPAD" -ForegroundColor Gray
}

function Open-CameronPAD {
    Write-Host "Opening CameronPAD in browser..." -ForegroundColor Green
    Start-Process "http://127.0.0.1:8000"
}

function Open-CameronPAD-Admin {
    Write-Host "Opening admin panel in browser..." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8000/admin"
}

function Open-CameronPAD-Docs {
    Write-Host "Opening API docs in browser..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:8000/docs"
}

# Show info when sourced
Show-CameronPAD-Info

# Aliases for convenience
Set-Alias cameron Start-CameronPAD
Set-Alias cam Start-CameronPAD