# CameronPAD Development Commands
# Source this file: . .\scripts\dev_commands.ps1

function Start-CameronPAD {
    <#
    .SYNOPSIS
    Start the CameronPAD development server
    #>
    Write-Host "🚀 Starting CameronPAD..." -ForegroundColor Green
    python scripts/dev_server.py
}

function Setup-CameronPAD {
    <#
    .SYNOPSIS
    Setup the development environment
    #>
    Write-Host "🔧 Setting up development environment..." -ForegroundColor Blue
    python scripts/setup_dev.py
}

function Reset-CameronPAD {
    <#
    .SYNOPSIS
    Reset the development database and setup
    #>
    Write-Host "🔄 Resetting development environment..." -ForegroundColor Yellow
    
    # Remove existing data
    if (Test-Path "data/cameronpad_dev.db") {
        Remove-Item "data/cameronpad_dev.db" -Force
        Write-Host "   Removed old database" -ForegroundColor Gray
    }
    
    # Re-setup
    python scripts/setup_dev.py
}

function Test-CameronPAD {
    <#
    .SYNOPSIS
    Run tests
    #>
    Write-Host "🧪 Running tests..." -ForegroundColor Cyan
    if (Test-Path "tests") {
        python -m pytest tests/ -v
    } else {
        Write-Host "   No tests directory found" -ForegroundColor Yellow
    }
}

function Install-CameronPAD {
    <#
    .SYNOPSIS
    Install or update dependencies
    #>
    Write-Host "📦 Installing dependencies..." -ForegroundColor Magenta
    
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
        pip install $package --upgrade
    }
    
    Write-Host "✅ All dependencies installed!" -ForegroundColor Green
}

function Show-CameronPAD-Info {
    <#
    .SYNOPSIS
    Show development server information
    #>
    Write-Host "🌌 CameronPAD Development Information" -ForegroundColor Blue
    Write-Host "=================================" -ForegroundColor Blue
    Write-Host "🌐 Local URL:    http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "🔧 Admin Panel:  http://127.0.0.1:8000/admin" -ForegroundColor Yellow
    Write-Host "📚 API Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Cyan
    Write-Host "📊 Health Check: http://127.0.0.1:8000/health" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "👤 Default Admin:" -ForegroundColor Blue
    Write-Host "   Username: admin" -ForegroundColor Gray
    Write-Host "   Password: admin123!" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🧪 Test User:" -ForegroundColor Blue
    Write-Host "   Username: testuser" -ForegroundColor Gray
    Write-Host "   Password: test123!" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Available Commands:" -ForegroundColor Blue
    Write-Host "   Start-CameronPAD    - Start development server" -ForegroundColor Gray
    Write-Host "   Setup-CameronPAD    - Setup/reset environment" -ForegroundColor Gray
    Write-Host "   Reset-CameronPAD    - Reset database and setup" -ForegroundColor Gray
    Write-Host "   Test-CameronPAD     - Run tests" -ForegroundColor Gray
    Write-Host "   Install-CameronPAD  - Install dependencies" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🚀 Quick Start:" -ForegroundColor Green
    Write-Host "   1. Install-CameronPAD" -ForegroundColor Gray
    Write-Host "   2. Setup-CameronPAD" -ForegroundColor Gray
    Write-Host "   3. Start-CameronPAD" -ForegroundColor Gray
}

function Open-CameronPAD {
    <#
    .SYNOPSIS
    Open CameronPAD in default browser
    #>
    Write-Host "🌐 Opening CameronPAD in browser..." -ForegroundColor Green
    Start-Process "http://127.0.0.1:8000"
}

function Open-CameronPAD-Admin {
    <#
    .SYNOPSIS
    Open CameronPAD admin panel in browser
    #>
    Write-Host "🔧 Opening admin panel in browser..." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8000/admin"
}

function Open-CameronPAD-Docs {
    <#
    .SYNOPSIS
    Open CameronPAD API documentation in browser
    #>
    Write-Host "📚 Opening API docs in browser..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:8000/docs"
}

function Get-CameronPAD-Logs {
    <#
    .SYNOPSIS
    Show recent development logs
    #>
    $logFile = "logs/cameronpad_dev.log"
    if (Test-Path $logFile) {
        Write-Host "📄 Recent CameronPAD logs:" -ForegroundColor Blue
        Get-Content $logFile -Tail 20
    } else {
        Write-Host "No log file found at $logFile" -ForegroundColor Yellow
    }
}

# Show info when sourced
Show-CameronPAD-Info

# Aliases for convenience
Set-Alias cameron Start-CameronPAD
Set-Alias cam Start-CameronPAD
Set-Alias cameron-setup Setup-CameronPAD
Set-Alias cameron-reset Reset-CameronPAD
Set-Alias cameron-install Install-CameronPAD
Set-Alias cameron-open Open-CameronPAD
Set-Alias cameron-admin Open-CameronPAD-Admin
Set-Alias cameron-docs Open-CameronPAD-Docs
Set-Alias cameron-logs Get-CameronPAD-Logs