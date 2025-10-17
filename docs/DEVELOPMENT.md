# Local Development Setup

## 🚀 Quick Start Guide

This guide helps you run CameronPAD locally for development and testing without deploying to your Hetzner VM.

### Prerequisites
- Python 3.12 or higher
- Git (to clone the repository)
- PowerShell (Windows) or Terminal (Linux/Mac)

### Step 1: Setup Development Environment

```powershell
# Navigate to your project directory
cd d:\Repositories\CameronPAD\cameronpad

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# If requirements.txt doesn't exist, install manually:
pip install fastapi uvicorn python-multipart jinja2 python-jose[cryptography] passlib[bcrypt] sqlalchemy aiosqlite pydantic[email] python-dotenv
```

### Step 2: Configure Environment

Create a `.env.dev` file in your project root:

```env
# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database (SQLite for local development)
DATABASE_URL=sqlite+aiosqlite:///./data/cameronpad_dev.db

# Security (use simple values for development)
SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Upload settings
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=10485760

# External APIs (optional for testing)
FINNHUB_TOKEN=your-dev-token-here
ALPHA_VANTAGE_KEY=your-dev-key-here

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=./logs/cameronpad_dev.log

# Development settings
RELOAD=true
HOST=127.0.0.1
PORT=8000
```

### Step 3: Initialize Database

Create `scripts/setup_dev.py`:

```python
"""
Development setup script
Run this to initialize your local development environment
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app_new.core.database import DatabaseManager
from app_new.core.auth import SecurityManager
from app_new.core.config import ConfigManager

async def setup_development():
    """Setup development environment"""
    print("🚀 Setting up CameronPAD development environment...")
    
    # Create necessary directories
    directories = [
        "data",
        "data/uploads", 
        "logs",
        "config/environments"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Initialize configuration
    config = ConfigManager()
    await config.load_config("development")
    print("✅ Configuration loaded")
    
    # Initialize database
    db = DatabaseManager(config.database.url)
    await db.initialize_database()
    print("✅ Database initialized")
    
    # Create admin user
    security = SecurityManager(config.security.secret_key)
    admin_password = "admin123!"  # Change this!
    hashed_password = security.hash_password(admin_password)
    
    admin_user = await db.create_user(
        username="admin",
        email="admin@cameronpad.dev",
        hashed_password=hashed_password,
        full_name="Administrator",
        role="admin",
        is_active=True
    )
    
    print("✅ Admin user created")
    print(f"   Username: admin")
    print(f"   Password: {admin_password}")
    print(f"   Email: admin@cameronpad.dev")
    
    # Create test user
    test_password = "test123!"
    test_hashed = security.hash_password(test_password)
    
    test_user = await db.create_user(
        username="testuser",
        email="test@cameronpad.dev", 
        hashed_password=test_hashed,
        full_name="Test User",
        role="user",
        is_active=True
    )
    
    print("✅ Test user created")
    print(f"   Username: testuser")
    print(f"   Password: {test_password}")
    
    print("\n🎉 Development environment setup complete!")
    print(f"🌐 You can now run: python scripts/dev_server.py")

if __name__ == "__main__":
    asyncio.run(setup_development())
```

### Step 4: Development Server Script

Create `scripts/dev_server.py`:

```python
"""
Development server script
Easy way to run CameronPAD locally with auto-reload
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add the app to Python path
sys.path.append(str(Path(__file__).parent.parent))

def run_dev_server():
    """Run development server with auto-reload"""
    print("🚀 Starting CameronPAD Development Server...")
    print("🌐 Local URL: http://127.0.0.1:8000")
    print("📱 Network URL: http://localhost:8000")
    print("🔧 Admin Panel: http://127.0.0.1:8000/admin")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("⚡ Auto-reload enabled - changes will be detected automatically")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Set environment to development
    os.environ["ENVIRONMENT"] = "development"
    
    # Run the server
    uvicorn.run(
        "app_new.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app_new", "plugins", "templates"],
        env_file=".env.dev",
        log_level="debug"
    )

if __name__ == "__main__":
    run_dev_server()
```

### Step 5: PowerShell Development Commands

Create `scripts/dev_commands.ps1`:

```powershell
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
    python -m pytest tests/ -v
}

function Install-CameronPAD {
    <#
    .SYNOPSIS
    Install or update dependencies
    #>
    Write-Host "📦 Installing dependencies..." -ForegroundColor Magenta
    pip install -r requirements.txt --upgrade
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
}

# Show info when sourced
Show-CameronPAD-Info

# Aliases for convenience
Set-Alias cameron Start-CameronPAD
Set-Alias cam Start-CameronPAD
```

### Step 6: Quick Commands Reference

Create `DEV_COMMANDS.md`:

```markdown
# 🚀 CameronPAD Development Commands

## Initial Setup (Run Once)
```powershell
# 1. Setup environment
python scripts/setup_dev.py

# 2. Source development commands
. .\scripts\dev_commands.ps1
```

## Daily Development

### Start the server
```powershell
# Any of these work:
Start-CameronPAD
cameron
cam
python scripts/dev_server.py
```

### Reset environment
```powershell
Reset-CameronPAD
```

### Run tests
```powershell
Test-CameronPAD
```

## Access Points
- 🌐 **Main Site**: http://127.0.0.1:8000
- 🔧 **Admin Panel**: http://127.0.0.1:8000/admin  
- 📚 **API Docs**: http://127.0.0.1:8000/docs
- 📊 **Health Check**: http://127.0.0.1:8000/health

## Default Accounts
- **Admin**: admin / admin123!
- **Test User**: testuser / test123!

## File Watching
The development server automatically reloads when you change:
- Python files in `app_new/`
- Plugin files in `plugins/`
- Templates in `templates/`

## Database
- Development uses SQLite: `data/cameronpad_dev.db`
- View with: DB Browser for SQLite or similar tool

## Logs
- Development logs: `logs/cameronpad_dev.log`
- Console output includes debug information
```

## 🎯 Usage Instructions

### First Time Setup
1. Open PowerShell in your project directory
2. Run: `python scripts/setup_dev.py`
3. Source dev commands: `. .\scripts\dev_commands.ps1`
4. Start server: `Start-CameronPAD`

### Daily Development
1. Open PowerShell in project directory
2. Source commands: `. .\scripts\dev_commands.ps1`
3. Start server: `cameron` (or `Start-CameronPAD`)
4. Open browser to: http://127.0.0.1:8000
5. Login with admin/admin123!

### Making Changes
- Edit files in `app_new/`, `plugins/`, or `templates/`
- Server automatically reloads
- Refresh browser to see changes
- Check console for any errors

### Testing
- Run `Test-CameronPAD` to execute tests
- Check `logs/cameronpad_dev.log` for detailed logs
- Use `/docs` endpoint to test API directly

This setup provides a complete local development environment that's much easier than deploying to your Hetzner VM every time you want to test changes!