# CameronPAD Installation Script for Windows
# This script installs dependencies and sets up the application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CameronPAD Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Check Python version
$version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([double]$version -lt 3.8) {
    Write-Host "✗ Python 3.8+ is required. Current version: $version" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installing/Updating Python packages..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

# Upgrade pip first
python -m pip install --upgrade pip

# Install requirements
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ Installation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ All packages installed successfully!" -ForegroundColor Green

# Create necessary directories
Write-Host ""
Write-Host "Creating necessary directories..." -ForegroundColor Yellow

$directories = @(
    "data",
    "data\blog_uploads",
    "data\journal_uploads",
    "logs",
    "backups"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Exists: $dir" -ForegroundColor Gray
    }
}

# Check for .env file
Write-Host ""
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "  ! .env file not found" -ForegroundColor Yellow
    Write-Host "    Creating .env from .env.example..." -ForegroundColor Gray
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  ✓ .env file created" -ForegroundColor Green
        Write-Host "    Please edit .env to configure your API keys" -ForegroundColor Cyan
    } else {
        Write-Host "  ! .env.example not found. You may need to create .env manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
}

# Check for FFmpeg (optional for video metadata)
Write-Host ""
Write-Host "Checking optional dependencies..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ FFmpeg found: Video metadata extraction enabled" -ForegroundColor Green
} catch {
    Write-Host "  ! FFmpeg not found: Video metadata will use file timestamps" -ForegroundColor Yellow
    Write-Host "    Install FFmpeg from https://ffmpeg.org for better video date detection" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review and edit .env file with your API keys" -ForegroundColor White
Write-Host "  2. Run: .\start.ps1" -ForegroundColor Yellow
Write-Host ""
