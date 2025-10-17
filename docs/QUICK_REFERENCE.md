# CameronPAD - Quick Reference Cheat Sheet

## 🚀 Essential Commands

```powershell
# Start server
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# Stop all Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Create admin user
py create_admin.py

# Migrate old data
py migrate_all_data.py
```

## 📂 Key Files & Their Purpose

| File | Purpose |
|------|---------|
| `app_new/main.py` | Main application entry point |
| `app_new/plugins/base.py` | Base class for all plugins |
| `app_new/plugins/manager.py` | Plugin discovery & loading |
| `templates/base.html` | Navigation menu (edit here to add links) |
| `data/cameronpad_dev.db` | Active database |
| `.env` | Environment variables & API keys |

## 🔌 Plugin Structure

```
plugins/my_plugin/
├── config.yaml          # Plugin metadata
├── plugin.py            # Main plugin class
├── database.py          # Database initialization
├── services.py          # API calls & business logic (optional)
└── templates/
    └── my_plugin.html   # HTML template
```

## 🛠️ Create New Plugin (5 Steps)

1. **Create directory:** `mkdir plugins\my_plugin`
2. **Add config.yaml** with name, version, description
3. **Create plugin.py** with `get_plugin(config)` function
4. **Create templates/** directory and HTML file
5. **Restart server** - plugin auto-loads!

## 🧭 Add to Navigation Menu

Edit `templates/base.html`, find the dropdown, add:

```html
<a href="/api/v1/plugins/my_plugin/">🚀 My Plugin</a>
```

## 🗄️ Database Operations

```python
# In plugin routes:
import sqlite3

# Read
with sqlite3.connect("data/cameronpad_dev.db") as conn:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM my_table")
    results = [dict(row) for row in cur.fetchall()]

# Write
with sqlite3.connect("data/cameronpad_dev.db") as conn:
    cur = conn.cursor()
    cur.execute("INSERT INTO my_table(name) VALUES(?)", (value,))
    conn.commit()
```

## 🔑 Environment Variables

Create `.env` file with:

```bash
# Required
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
DATABASE_URL=sqlite:///./data/cameronpad_dev.db

# Stock APIs (pick one)
FINNHUB_TOKEN=your_key        # 60 req/min (recommended)
ALPHA_VANTAGE_KEY=your_key    # 5 req/min (backup)

# Intervals (seconds)
POLL_SECONDS=60        # Stock alerts
SURF_REFRESH=600       # Wave data
PREDICT_SECONDS=3600   # Predictions
```

## 🌐 Important URLs

- Home: http://127.0.0.1:8000/
- API Docs: http://127.0.0.1:8000/docs
- Plugin Base: http://127.0.0.1:8000/api/v1/plugins/{name}/

## 🐛 Quick Fixes

**Server won't start:**
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

**Plugin not loading:**
- Check `config.yaml` exists
- Verify `get_plugin()` function in `plugin.py`
- Check logs for error messages

**Database issues:**
```powershell
# View tables
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); print([r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')]); conn.close()"
```

## 📝 Plugin Template Code

```python
from app_new.plugins.base import WebPlugin, PluginMetadata
from fastapi import Request
from fastapi.templating import Jinja2Templates

class MyPlugin(WebPlugin):
    async def initialize(self):
        # Setup templates
        self.templates = Jinja2Templates(directory="plugins/my_plugin/templates")
        # Register routes
        self.register_routes()
    
    def get_metadata(self):
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My plugin"
        )
    
    def register_routes(self):
        @self._router.get("/")
        async def home(request: Request):
            return self.templates.TemplateResponse(
                "my_plugin.html",
                {"request": request}
            )
    
    async def shutdown(self):
        pass

def get_plugin(config):
    return MyPlugin(config)
```

## 🎯 Deployment Checklist

- [ ] Set production `SECRET_KEY` in `.env`
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Configure systemd service or Docker
- [ ] Set up Nginx reverse proxy
- [ ] Enable background task scheduler
- [ ] Backup database regularly

## 📚 Full Documentation

See `docs/COMPLETE_GUIDE.md` for:
- Complete architecture overview
- Detailed plugin creation tutorial
- Database schema documentation
- Deployment guides (Docker, VPS, Render)
- Troubleshooting guide
- API integration examples

---

**Current Status:**
- ✅ 8 plugins loaded
- ✅ Database migrated (1 note, 19 tabs, 24 surf spots, 1 stock)
- ✅ All CRUD operations working
- ✅ Server running on http://127.0.0.1:8000

**Quick Access:**
```
Notes:      /api/v1/plugins/notes/
Notepad:    /api/v1/plugins/notepad/
Surf:       /api/v1/plugins/surf/
Stocks:     /api/v1/plugins/stocks/
```
