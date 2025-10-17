# CameronPAD - Complete Developer & Deployment Guide

> **Last Updated:** October 16, 2025  
> **Version:** 2.0 (Plugin Architecture)  
> **Author:** Cameron

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Architecture](#project-architecture)
3. [File Structure & What Each File Does](#file-structure--what-each-file-does)
4. [Plugin System](#plugin-system)
5. [How to Create a New Plugin](#how-to-create-a-new-plugin)
6. [How to Add Plugin to Navigation Menu](#how-to-add-plugin-to-navigation-menu)
7. [Database Management](#database-management)
8. [API Keys & Environment Variables](#api-keys--environment-variables)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Development Server
```powershell
# Install dependencies
pip install -r requirements.txt

# Run development server
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# Access at: http://127.0.0.1:8000
```

### Production Server
```powershell
# Run with Gunicorn (recommended for production)
gunicorn app_new.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Project Architecture

### High-Level Overview

```
CameronPAD
├── Frontend: HTML + JavaScript (vanilla)
├── Backend: FastAPI (Python async web framework)
├── Database: SQLite (cameronpad_dev.db)
├── Plugins: Modular plugin system
└── Authentication: JWT tokens with bcrypt password hashing
```

### Architecture Diagram

```
┌─────────────────────────────────────────────┐
│           Browser / Client                   │
└──────────────┬──────────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────────────┐
│         FastAPI Application                  │
│  ┌────────────────────────────────────────┐ │
│  │     Middleware Stack                   │ │
│  │  - CORS                                │ │
│  │  - Authentication (JWT)                │ │
│  │  - Static Files                        │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │     Core Routes                        │ │
│  │  - /auth (login, register)             │ │
│  │  - / (home page)                       │ │
│  │  - /dashboard                          │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │     Plugin System                      │ │
│  │  - Dynamic plugin loading              │ │
│  │  - Route registration                  │ │
│  │  - /api/v1/plugins/{name}/             │ │
│  └────────────────────────────────────────┘ │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│     SQLite Database (cameronpad_dev.db)     │
│  - users                                     │
│  - sessions                                  │
│  - notes, pad_tabs                           │
│  - surf_spots, surf_cache                    │
│  - stocks, alerts, latest_prices             │
│  - predictions, journal_entries              │
└──────────────────────────────────────────────┘
```

---

## File Structure & What Each File Does

### Root Directory

```
cameronpad/
├── app/                          # Original app (legacy - DO NOT USE)
│   └── main.py                   # Old monolithic app (reference only)
│
├── app_new/                      # NEW PLUGIN-BASED APP (USE THIS)
│   ├── __init__.py               # Package marker
│   ├── main.py                   # 🔥 MAIN APPLICATION ENTRY POINT
│   │                             # - Creates FastAPI app
│   │                             # - Loads plugins
│   │                             # - Registers routes
│   │                             # - Handles startup/shutdown
│   │
│   ├── core/                     # Core application modules
│   │   ├── config.py             # Configuration management (env vars)
│   │   ├── database.py           # Database connection & migrations
│   │   ├── auth.py               # JWT authentication logic
│   │   └── security.py           # Password hashing, token generation
│   │
│   ├── plugins/                  # 🔥 PLUGIN SYSTEM
│   │   ├── base.py               # WebPlugin base class (inherit from this)
│   │   ├── manager.py            # PluginManager - discovers & loads plugins
│   │   └── registry.py           # Plugin registry (tracks loaded plugins)
│   │
│   ├── routes/                   # Core API routes
│   │   ├── auth.py               # /auth/login, /auth/register
│   │   └── main.py               # /, /dashboard
│   │
│   └── models/                   # SQLAlchemy ORM models
│       ├── user.py               # User model
│       └── session.py            # Session model
│
├── plugins/                      # 🔥 PLUGIN IMPLEMENTATIONS
│   ├── stocks/                   # Stock tracking plugin
│   │   ├── __init__.py
│   │   ├── config.yaml           # Plugin metadata & settings
│   │   ├── plugin.py             # Main plugin class (StocksPlugin)
│   │   ├── database.py           # Database initialization
│   │   ├── services.py           # API calls, business logic
│   │   └── templates/            # HTML templates
│   │       └── stocks.html
│   │
│   ├── notes/                    # Notes plugin
│   │   ├── plugin.py             # NotesPlugin (CRUD operations)
│   │   ├── database.py           # Creates 'notes' table
│   │   └── templates/
│   │       └── notes.html
│   │
│   ├── notepad/                  # Multi-tab notepad plugin
│   │   ├── plugin.py             # NotepadPlugin (tab management)
│   │   ├── database.py           # Creates 'pad_tabs' table
│   │   └── templates/
│   │       └── notepad.html
│   │
│   ├── surf/                     # Surf spot tracking plugin
│   │   ├── plugin.py             # SurfPlugin (spot CRUD)
│   │   ├── database.py           # Creates 'surf_spots', 'surf_cache'
│   │   ├── services.py           # Open-Meteo Marine API integration
│   │   └── templates/
│   │       └── surf.html
│   │
│   ├── journal/                  # Journal with image upload
│   │   ├── plugin.py
│   │   └── templates/
│   │       └── journal.html
│   │
│   ├── tradingview/              # TradingView widgets
│   │   ├── plugin.py
│   │   └── templates/
│   │       └── tradingview.html
│   │
│   ├── system_monitor/           # System metrics (CPU, RAM, disk)
│   │   ├── plugin.py
│   │   └── templates/
│   │       └── system_monitor.html
│   │
│   └── hello_world/              # Demo plugin (template)
│       ├── plugin.py
│       └── templates/
│           └── hello_world.html
│
├── templates/                    # 🔥 SHARED TEMPLATES
│   ├── base.html                 # Base template with navigation menu
│   ├── index.html                # Home page
│   ├── dashboard.html            # User dashboard
│   ├── login.html                # Login page
│   └── register.html             # Registration page
│
├── static/                       # Static assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── data/                         # 🔥 DATABASE FILES
│   ├── app.db                    # Original database (legacy)
│   ├── cameronpad_dev.db         # NEW DATABASE (active)
│   └── uploads/                  # User uploaded files
│
├── docs/                         # Documentation
│   └── COMPLETE_GUIDE.md         # This file!
│
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker setup
├── Dockerfile                    # Docker image
├── .env                          # Environment variables (create this!)
├── migrate_all_data.py           # Data migration script
└── create_admin.py               # Admin user creation script
```

---

## Plugin System

### How Plugins Work

1. **Discovery:** `PluginManager` scans `plugins/` directory for subdirectories containing `config.yaml`
2. **Loading:** Each plugin's `plugin.py` must have a `get_plugin(config)` function
3. **Registration:** Plugin routes are mounted at `/api/v1/plugins/{plugin_name}/`
4. **Initialization:** `initialize()` method called on startup, `shutdown()` on exit

### Plugin Lifecycle

```python
# 1. Application starts
app = FastAPI()

# 2. PluginManager initialized
plugin_manager = PluginManager(plugins_dir="plugins")

# 3. Plugins discovered
await plugin_manager.discover_plugins()
# → Finds: stocks, notes, notepad, surf, journal, tradingview, system_monitor, hello_world

# 4. Plugins loaded
await plugin_manager.load_plugins()
# → Calls get_plugin(config) for each plugin
# → Calls plugin.initialize() for each plugin

# 5. Routes registered
for name, plugin in plugin_manager.get_all_plugins().items():
    app.include_router(
        plugin.router,
        prefix=f"/api/v1/plugins/{name}",
        tags=[name]
    )

# 6. Application ready
# → http://127.0.0.1:8000/api/v1/plugins/notes/
# → http://127.0.0.1:8000/api/v1/plugins/stocks/
# etc.

# 7. On shutdown
await plugin_manager.unload_plugins()
# → Calls plugin.shutdown() for each plugin
```

### Plugin Base Class

All plugins inherit from `WebPlugin` in `app_new/plugins/base.py`:

```python
class WebPlugin(ABC):
    def __init__(self, config: PluginConfig):
        self.config = config
        self._router = APIRouter()  # Each plugin has its own router
    
    @abstractmethod
    async def initialize(self) -> None:
        """Called on plugin load - setup database, templates, routes"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Called on plugin unload - cleanup resources"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin name, version, description, etc."""
        pass
    
    @abstractmethod
    def register_routes(self) -> None:
        """Register FastAPI routes on self._router"""
        pass
    
    @property
    def router(self) -> APIRouter:
        """Returns the router for FastAPI to mount"""
        return self._router
```

---

## How to Create a New Plugin

### Step 1: Create Plugin Directory

```powershell
# Create plugin directory structure
mkdir plugins\my_plugin
mkdir plugins\my_plugin\templates
```

### Step 2: Create `config.yaml`

**File:** `plugins/my_plugin/config.yaml`

```yaml
name: my_plugin
version: 1.0.0
description: "My awesome plugin"
author: "Your Name"
enabled: true
priority: 100  # Lower number = loads first

# Optional settings
settings:
  refresh_interval: 300
  max_items: 100
  api_key: ""  # Can be overridden by environment variable

# Optional dependencies (other plugins required)
dependencies: []

# API version compatibility
api_version: "1.0"
```

### Step 3: Create Database Initialization (Optional)

**File:** `plugins/my_plugin/database.py`

```python
"""
Database initialization for My Plugin
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_my_plugin_db():
    """Initialize database tables for my plugin"""
    conn = sqlite3.connect("data/cameronpad_dev.db")
    cur = conn.cursor()
    
    # Create your table(s)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS my_plugin_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ My Plugin database tables initialized")
```

### Step 4: Create Plugin Class

**File:** `plugins/my_plugin/plugin.py`

```python
"""
My Plugin - Does something awesome
"""
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class MyPlugin(WebPlugin):
    """My awesome plugin implementation"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        
    async def initialize(self) -> None:
        """Initialize the plugin"""
        logger.info("🚀 Initializing My Plugin...")
        
        # Initialize database tables
        from .database import init_my_plugin_db
        init_my_plugin_db()
        
        # Setup templates with both main and plugin template directories
        template_dir = Path(__file__).parent / "templates"
        main_template_dir = Path(__file__).parent.parent.parent / "templates"
        
        # Use ChoiceLoader to search in plugin templates first, then main templates
        loader = ChoiceLoader([
            FileSystemLoader(str(template_dir)),
            FileSystemLoader(str(main_template_dir))
        ])
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.templates.env.loader = loader
        
        # Register routes
        self.register_routes()
        
        logger.info("✅ My Plugin initialized successfully")
        
    async def shutdown(self) -> None:
        """Clean shutdown"""
        logger.info("🛑 My Plugin shutting down")
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My awesome plugin",
            author="Your Name",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for this plugin"""
        
        @self._router.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Render plugin home page"""
            import sqlite3
            
            # Fetch data from database
            items = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT id, name, value, created_at FROM my_plugin_data ORDER BY created_at DESC")
                    items = [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Failed to fetch items: {e}")
            
            return self.templates.TemplateResponse(
                "my_plugin.html",
                {
                    "request": request,
                    "items": items,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/add")
        async def add_item(name: str = Form(...), value: str = Form(...)):
            """Add a new item"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO my_plugin_data(name, value) VALUES(?, ?)",
                        (name, value)
                    )
                    conn.commit()
                    logger.info(f"✅ Added item: {name}")
            except Exception as e:
                logger.error(f"Failed to add item: {e}")
            
            return RedirectResponse("/api/v1/plugins/my_plugin/", status_code=303)
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            return {"status": "active", "plugin": "my_plugin"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "status": "healthy",
            "plugin": "my_plugin",
            "version": self.config.version
        }


def get_plugin(config: PluginConfig) -> MyPlugin:
    """Factory function to create plugin instance"""
    return MyPlugin(config)
```

### Step 5: Create HTML Template

**File:** `plugins/my_plugin/templates/my_plugin.html`

```html
{% extends "base.html" %}

{% block title %}My Plugin - CameronPAD{% endblock %}

{% block content %}
<div class="container">
    <h1>🚀 My Plugin</h1>
    
    <!-- Add Item Form -->
    <div class="card">
        <h2>Add New Item</h2>
        <form method="POST" action="/api/v1/plugins/my_plugin/add">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="value">Value:</label>
                <input type="text" id="value" name="value" required>
            </div>
            <button type="submit" class="btn btn-primary">Add Item</button>
        </form>
    </div>
    
    <!-- Items List -->
    <div class="card">
        <h2>Items</h2>
        {% if items %}
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Value</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>{{ item.id }}</td>
                        <td>{{ item.name }}</td>
                        <td>{{ item.value }}</td>
                        <td>{{ item.created_at }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p>No items yet. Add one above!</p>
        {% endif %}
    </div>
</div>
{% endblock %}
```

### Step 6: Test Your Plugin

```powershell
# Restart server
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# Check logs for initialization
# Should see: "✅ My Plugin initialized successfully"

# Visit your plugin
# http://127.0.0.1:8000/api/v1/plugins/my_plugin/
```

---

## How to Add Plugin to Navigation Menu

### Method 1: Edit `base.html` Directly

**File:** `templates/base.html`

Find the navigation menu dropdown (around line 60-90):

```html
<div class="dropdown">
    <button class="dropbtn">Apps ▼</button>
    <div class="dropdown-content">
        <a href="/api/v1/plugins/stocks/">📈 Stocks</a>
        <a href="/api/v1/plugins/surf/">🏄 Surf</a>
        <a href="/api/v1/plugins/journal/">📔 Journal</a>
        <a href="/api/v1/plugins/notes/">📝 Notes</a>
        <a href="/api/v1/plugins/notepad/">📓 Notepad</a>
        <a href="/api/v1/plugins/tradingview/">📊 TradingView</a>
        <a href="/api/v1/plugins/system_monitor/">🖥️ System Monitor</a>
        
        <!-- ADD YOUR PLUGIN HERE -->
        <a href="/api/v1/plugins/my_plugin/">🚀 My Plugin</a>
    </div>
</div>
```

### Method 2: Dynamic Menu (Advanced)

Modify `app_new/main.py` to inject plugin menu items into templates:

```python
# In app_new/main.py startup event
@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Collect menu items from all plugins
    menu_items = []
    for name, plugin in plugin_manager.get_all_plugins().items():
        if hasattr(plugin, 'get_menu_items'):
            items = plugin.get_menu_items()
            menu_items.extend(items)
    
    # Store in app state
    app.state.plugin_menu_items = menu_items
```

Then add to your plugin:

```python
def get_menu_items(self) -> list:
    """Return menu items for this plugin"""
    return [
        {
            "label": "My Plugin",
            "icon": "🚀",
            "url": "/api/v1/plugins/my_plugin/",
            "order": 100
        }
    ]
```

### Restart Server

```powershell
# Stop current server (Ctrl+C)
# Restart
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
```

Your plugin should now appear in the Apps menu!

---

## Database Management

### Database Location

- **Development:** `data/cameronpad_dev.db`
- **Production:** Configure in `.env` file

### Database Schema

The application uses SQLite with the following core tables:

#### Core Tables (managed by app_new/core/database.py)
- `users` - User accounts
- `sessions` - Active user sessions

#### Plugin Tables (managed by individual plugins)
- `notes` - Timestamped notes
- `pad_tabs` - Notepad tabs with content
- `surf_spots` - Surf locations with coordinates
- `surf_cache` - Cached wave data
- `stocks` - Stock symbols to track
- `alerts` - Triggered stock alerts
- `latest_prices` - Current stock prices
- `predictions` - Price predictions
- `journal_entries` - Journal posts
- `journal_images` - Uploaded images

### Database Migrations

Each plugin manages its own tables via `database.py`:

```python
# Example: plugins/my_plugin/database.py
def init_my_plugin_db():
    conn = sqlite3.connect("data/cameronpad_dev.db")
    cur = conn.cursor()
    
    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS my_table (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    
    # Add column if not exists (migration)
    try:
        cur.execute("ALTER TABLE my_table ADD COLUMN new_column TEXT")
    except:
        pass  # Column already exists
    
    conn.commit()
    conn.close()
```

### Viewing Database

```powershell
# Install DB Browser for SQLite: https://sqlitebrowser.org/

# Or use command line:
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); print([row[0] for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')]); conn.close()"
```

### Backup Database

```powershell
# Copy database file
Copy-Item data\cameronpad_dev.db data\cameronpad_dev.backup.db

# Or use SQLite backup command
py -c "import sqlite3; src = sqlite3.connect('data/cameronpad_dev.db'); dst = sqlite3.connect('data/backup.db'); src.backup(dst); dst.close(); src.close()"
```

---

## API Keys & Environment Variables

### Create `.env` File

**File:** `.env` (create in root directory)

```bash
# Application Settings
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-this-in-production
DATABASE_URL=sqlite:///./data/cameronpad_dev.db

# JWT Settings
JWT_SECRET=your-jwt-secret-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stock APIs (choose one or both)
FINNHUB_TOKEN=your_finnhub_api_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key

# Polling Intervals (seconds)
POLL_SECONDS=60          # Stock alert checking
SHOWCASE_REFRESH=300     # Price updates
PREDICT_SECONDS=3600     # Price predictions
SURF_REFRESH=600         # Wave data updates

# Notifications (optional)
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_FROM=your_phone_number
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# CORS Settings (for production)
ALLOWED_ORIGINS=https://cameronpad.com,https://www.cameronpad.com
```

### How to Get API Keys

#### Finnhub (Stock Data - Recommended)
1. Visit: https://finnhub.io/register
2. Free tier: 60 requests/minute
3. Copy API key to `FINNHUB_TOKEN`

#### Alpha Vantage (Stock Data - Backup)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Free tier: 5 requests/minute, 500/day
3. Copy API key to `ALPHA_VANTAGE_KEY`

#### Twilio (SMS Notifications)
1. Visit: https://www.twilio.com/try-twilio
2. Get Account SID, Auth Token, and phone number
3. Set `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM`

#### Telegram (Bot Notifications)
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Copy token to `TELEGRAM_BOT_TOKEN`

#### Discord (Webhook Notifications)
1. Create webhook in Discord server settings
2. Copy webhook URL to `DISCORD_WEBHOOK_URL`

### Loading Environment Variables

The app automatically loads `.env` file on startup via `app_new/core/config.py`:

```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file
```

Access in code:

```python
import os
api_key = os.getenv("FINNHUB_TOKEN")
```

---

## Deployment Guide

### Option 1: Deploy with Docker (Recommended)

```powershell
# Build Docker image
docker build -t cameronpad:latest .

# Run container
docker run -d -p 8000:8000 --name cameronpad -v ${PWD}/data:/app/data cameronpad:latest

# Or use docker-compose
docker-compose up -d
```

### Option 2: Deploy to VPS (Hetzner, DigitalOcean, etc.)

```bash
# On server (Ubuntu/Debian)

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# 3. Clone repository
git clone https://github.com/yourusername/cameronpad.git
cd cameronpad

# 4. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create .env file
nano .env
# (paste your environment variables)

# 7. Create systemd service
sudo nano /etc/systemd/system/cameronpad.service
```

**Service file content:**

```ini
[Unit]
Description=CameronPAD FastAPI Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/cameronpad
Environment="PATH=/path/to/cameronpad/venv/bin"
ExecStart=/path/to/cameronpad/venv/bin/gunicorn app_new.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 8. Start service
sudo systemctl daemon-reload
sudo systemctl enable cameronpad
sudo systemctl start cameronpad

# 9. Check status
sudo systemctl status cameronpad

# 10. Setup Nginx reverse proxy
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/cameronpad
```

**Nginx config:**

```nginx
server {
    listen 80;
    server_name cameronpad.com www.cameronpad.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cameronpad /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 11. Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d cameronpad.com -d www.cameronpad.com
```

### Option 3: Deploy to Render.com (Easy)

1. Create account at https://render.com
2. Connect GitHub repository
3. Create new Web Service
4. Set environment variables in dashboard
5. Deploy!

### Background Tasks (Important!)

For production, you need to run background tasks for:
- Stock price polling
- Wave data updates
- Price predictions
- Alert checking

**Option A:** Use APScheduler (built-in)
```python
# Add to app_new/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    # Update surf data every 10 minutes
    scheduler.add_job(
        update_surf_data,
        'interval',
        seconds=600,
        id='surf_update'
    )
    scheduler.start()
```

**Option B:** Use systemd timers or cron jobs

---

## Troubleshooting

### Server won't start

```powershell
# Check for port conflicts
netstat -ano | findstr :8000

# Kill process using port 8000
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Check Python version (need 3.8+)
python --version
```

### Plugin not loading

```powershell
# Check logs for errors
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# Verify config.yaml exists
Test-Path plugins\my_plugin\config.yaml

# Verify get_plugin() function exists
Get-Content plugins\my_plugin\plugin.py | Select-String "def get_plugin"
```

### Database errors

```powershell
# Check database file exists
Test-Path data\cameronpad_dev.db

# Verify table structure
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); print([row for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')]); conn.close()"

# Reset database (CAUTION: deletes all data)
Remove-Item data\cameronpad_dev.db
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
```

### Template not found

```powershell
# Verify ChoiceLoader is configured in plugin.py:
# loader = ChoiceLoader([
#     FileSystemLoader(str(template_dir)),
#     FileSystemLoader(str(main_template_dir))
# ])

# Check template file exists
Test-Path plugins\my_plugin\templates\my_plugin.html
```

### CORS errors in browser

Add to `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Migration issues

```powershell
# Re-run migration
py migrate_all_data.py

# Or migrate specific data
py -c "from migrate_all_data import migrate_pad_tabs; migrate_pad_tabs()"
```

---

## Important Commands Reference

```powershell
# Start development server
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# Start production server
gunicorn app_new.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Create admin user
py create_admin.py

# Migrate data from old app
py migrate_all_data.py

# Install dependencies
pip install -r requirements.txt

# Update dependencies
pip freeze > requirements.txt

# Check database
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); [print(row) for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')]; conn.close()"

# Kill all Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

---

## Key URLs

- **Home:** http://127.0.0.1:8000/
- **Dashboard:** http://127.0.0.1:8000/dashboard
- **API Docs:** http://127.0.0.1:8000/docs (FastAPI auto-generated)
- **Plugin Base:** http://127.0.0.1:8000/api/v1/plugins/

### Plugin URLs

- Stocks: http://127.0.0.1:8000/api/v1/plugins/stocks/
- Notes: http://127.0.0.1:8000/api/v1/plugins/notes/
- Notepad: http://127.0.0.1:8000/api/v1/plugins/notepad/
- Surf: http://127.0.0.1:8000/api/v1/plugins/surf/
- Journal: http://127.0.0.1:8000/api/v1/plugins/journal/
- TradingView: http://127.0.0.1:8000/api/v1/plugins/tradingview/
- System Monitor: http://127.0.0.1:8000/api/v1/plugins/system_monitor/

---

## Support & Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Jinja2 Docs:** https://jinja.palletsprojects.com/
- **SQLite Docs:** https://www.sqlite.org/docs.html
- **Finnhub API:** https://finnhub.io/docs/api
- **Open-Meteo Marine:** https://open-meteo.com/en/docs/marine-weather-api

---

## Version History

- **v2.0** (Oct 2025) - Plugin architecture, modular design
- **v1.0** (2024) - Monolithic Flask app (legacy)

---

**Remember:** This is YOUR application. Customize it, extend it, make it your own! 🚀

**Have fun building!** 🎉
