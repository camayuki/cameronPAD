# Pre-Deployment Verification Script for Windows
# Run this BEFORE transferring files to Linux

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  CameronPAD Pre-Deployment Check" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# Check 1: .env file exists
Write-Host "🔍 Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✅ .env file exists" -ForegroundColor Green
    
    # Check if it has API keys
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "FINNHUB_TOKEN=\w+") {
        Write-Host "   ✅ Finnhub token configured" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Finnhub token missing or placeholder!" -ForegroundColor Red
        $errors++
    }
    
    if ($envContent -match "ALPHA_VANTAGE_KEY=\w+") {
        Write-Host "   ✅ Alpha Vantage key configured" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Alpha Vantage key missing or placeholder" -ForegroundColor Yellow
        $warnings++
    }
    
    # Check for placeholder text
    if ($envContent -match "your_.*_here") {
        Write-Host "   ⚠️  WARNING: .env contains placeholder text" -ForegroundColor Yellow
        Write-Host "      Please update with real API keys" -ForegroundColor Yellow
        $errors++
    }
} else {
    Write-Host "   ❌ .env file NOT found!" -ForegroundColor Red
    Write-Host "      Create .env file with your API keys" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check 2: Required files exist
Write-Host "🔍 Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "app_new\main.py",
    "requirements.txt",
    "README.md",
    "DEPLOYMENT.md",
    "DEPLOY_WITH_WINSCP.md",
    "deploy_after_winscp.sh"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file NOT FOUND" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check 3: Required directories exist
Write-Host "🔍 Checking directories..." -ForegroundColor Yellow
$requiredDirs = @(
    "app_new",
    "plugins",
    "templates",
    "static",
    "data"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Host "   ✅ $dir\" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dir\ NOT FOUND" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check 4: Database exists (if applicable)
Write-Host "🔍 Checking database..." -ForegroundColor Yellow
if (Test-Path "data\cameronpad_dev.db") {
    $dbSize = (Get-Item "data\cameronpad_dev.db").Length
    Write-Host "   ✅ Database exists ($([math]::Round($dbSize/1KB, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  No database found (will be created on Linux)" -ForegroundColor Cyan
}
Write-Host ""

# Check 5: Python dependencies can be loaded
Write-Host "🔍 Testing Python imports..." -ForegroundColor Yellow
try {
    $testResult = python -c @"
try:
    import fastapi
    import uvicorn
    import aiohttp
    import dotenv
    print('OK')
except ImportError as e:
    print(f'ERROR: {e}')
"@ 2>&1

    if ($testResult -match "OK") {
        Write-Host "   ✅ Core dependencies importable" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Some dependencies may be missing" -ForegroundColor Yellow
        Write-Host "      $testResult" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   ⚠️  Could not test imports" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Check 6: Test .env loading
Write-Host "🔍 Testing .env loading..." -ForegroundColor Yellow
if (Test-Path ".env") {
    try {
        $testEnv = python -c @"
from dotenv import load_dotenv
import os
load_dotenv()
finnhub = os.getenv('FINNHUB_TOKEN', '')
alpha = os.getenv('ALPHA_VANTAGE_KEY', '')
print(f'Finnhub: {'YES' if finnhub and finnhub != 'your_finnhub_token_here' else 'NO'}')
print(f'Alpha: {'YES' if alpha and alpha != 'your_alpha_vantage_key_here' else 'NO'}')
"@ 2>&1

        Write-Host "   $testEnv" -ForegroundColor Cyan
        
        if ($testEnv -match "Finnhub: NO" -or $testEnv -match "Alpha: NO") {
            Write-Host "   ⚠️  API keys not properly configured" -ForegroundColor Yellow
            $errors++
        }
    } catch {
        Write-Host "   ⚠️  Could not test .env loading" -ForegroundColor Yellow
        Write-Host "      Error: $_" -ForegroundColor Yellow
        $warnings++
    }
}
Write-Host ""

# Check 7: Files that should NOT be transferred
Write-Host "🔍 Checking for files to exclude..." -ForegroundColor Yellow
$excludeItems = @(
    "venv",
    "__pycache__",
    "*.pyc",
    ".git"
)

$foundExcludes = @()
foreach ($item in $excludeItems) {
    if (Test-Path $item) {
        $foundExcludes += $item
    }
}

if ($foundExcludes.Count -gt 0) {
    Write-Host "   ℹ️  These will be excluded/recreated on Linux:" -ForegroundColor Cyan
    foreach ($item in $foundExcludes) {
        Write-Host "      - $item" -ForegroundColor Cyan
    }
} else {
    Write-Host "   ✅ No exclude items found" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host "   Ready for deployment to Linux" -ForegroundColor Green
} elseif ($errors -eq 0) {
    Write-Host "⚠️  $warnings warning(s) found" -ForegroundColor Yellow
    Write-Host "   Should be OK to deploy, but review warnings" -ForegroundColor Yellow
} else {
    Write-Host "❌ $errors error(s) and $warnings warning(s) found" -ForegroundColor Red
    Write-Host "   Please fix errors before deploying" -ForegroundColor Red
}
Write-Host ""

# Deployment instructions
if ($errors -eq 0) {
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Open WinSCP and connect to your Linux server" -ForegroundColor White
    Write-Host "   2. Navigate to your deployment directory on Linux" -ForegroundColor White
    Write-Host "   3. Transfer all files (except venv/, __pycache__/)" -ForegroundColor White
    Write-Host "   4. SSH into server: ssh user@server-ip" -ForegroundColor White
    Write-Host "   5. Run deployment script:" -ForegroundColor White
    Write-Host "      cd cameronpad" -ForegroundColor Gray
    Write-Host "      chmod +x deploy_after_winscp.sh" -ForegroundColor Gray
    Write-Host "      ./deploy_after_winscp.sh" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📚 Documentation:" -ForegroundColor Cyan
    Write-Host "   - DEPLOY_WITH_WINSCP.md (detailed guide)" -ForegroundColor White
    Write-Host "   - DEPLOY_CHECKLIST.md (quick checklist)" -ForegroundColor White
} else {
    Write-Host "⚠️  Fix the errors above before deploying" -ForegroundColor Yellow
}
Write-Host ""
