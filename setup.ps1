# CameronPAD Quick Setup Script for Windows
# Run this in PowerShell

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "CameronPAD Setup Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = (python --version 2>&1) -replace 'Python ', ''
    Write-Host "✓ Found Python $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Check for .env file
Write-Host ""
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Stock Service API Keys
FINNHUB_TOKEN=your_finnhub_token_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Service Configuration
POLL_SECONDS=60
SHOWCASE_REFRESH=300
COOLDOWN_MIN=30
ALPHA_MIN_INTERVAL=13.0

# Application Configuration
SECRET_KEY=change-this-secret-key-in-production-use-random-string
DEBUG=false
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env file and add your API keys!" -ForegroundColor Yellow
    Write-Host "   Run: notepad .env"
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Create data directory
Write-Host ""
Write-Host "Creating data directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data" | Out-Null
New-Item -ItemType Directory -Force -Path "data\uploads" | Out-Null
Write-Host "✓ Data directories created" -ForegroundColor Green

# Check if admin user exists
Write-Host ""
Write-Host "Checking for admin user..." -ForegroundColor Yellow
if (Test-Path "create_admin.py") {
    Write-Host ""
    $response = Read-Host "Do you want to create an admin user now? (y/n)"
    if ($response -match "^[yY]") {
        python create_admin.py
    } else {
        Write-Host "⚠️  Remember to create an admin user later by running: python create_admin.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  create_admin.py not found - you may need to create users manually" -ForegroundColor Yellow
}

# Display completion message
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your API keys: notepad .env"
Write-Host "2. Start the application:"
Write-Host "   py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host ""
Write-Host "3. Access the application at: http://localhost:8000"
Write-Host ""
Write-Host "For production deployment, see DEPLOYMENT.md" -ForegroundColor Cyan
Write-Host ""
