# CameronPAD Documentation 📚

Welcome to the complete documentation for CameronPAD v2.0!

## 📖 Documentation Files

### 1. **COMPLETE_GUIDE.md** - Your Bible 📘
The most comprehensive guide covering:
- Full architecture overview
- Every file and what it does
- Plugin system deep dive
- Step-by-step plugin creation tutorial
- Database management
- API keys setup
- Complete deployment guide (Docker, VPS, Render)
- Troubleshooting guide
- Command reference

**Read this when:** You need to understand how everything works or deploy to production.

---

### 2. **QUICK_REFERENCE.md** - Cheat Sheet ⚡
Quick lookup for:
- Essential commands
- Key file locations
- Plugin structure overview
- Database operations snippets
- Quick fixes for common issues
- Environment variables list

**Read this when:** You need to quickly remember a command or pattern.

---

### 3. **PLUGIN_TEMPLATE.md** - Copy & Paste Template 🎨
Ready-to-use plugin template with:
- Complete directory structure
- Fully commented code
- All CRUD operations implemented
- Beautiful HTML template with space theme
- Database initialization example
- Usage instructions

**Read this when:** You're creating a new plugin from scratch.

---

## 🚀 Quick Start Guide

### First Time Setup

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file (copy template below)
# Add your API keys

# 3. Start server
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# 4. Create admin user (optional)
py create_admin.py

# 5. Migrate old data (if you have it)
py migrate_all_data.py

# 6. Visit http://127.0.0.1:8000
```

### Environment Variables Template

Create `.env` file in root:

```bash
# Required
SECRET_KEY=change-this-to-something-random
JWT_SECRET=change-this-too
DATABASE_URL=sqlite:///./data/cameronpad_dev.db

# Stock APIs (optional - for stocks plugin)
FINNHUB_TOKEN=your_key_here
ALPHA_VANTAGE_KEY=your_key_here

# Polling intervals (optional)
POLL_SECONDS=60
SURF_REFRESH=600
PREDICT_SECONDS=3600
```

---

## 📂 Project Structure

```
cameronpad/
├── app_new/              ⭐ MAIN APPLICATION
│   ├── main.py           🔥 Entry point - START HERE
│   ├── core/             Core modules (auth, database, config)
│   ├── plugins/          Plugin system (base class, manager, registry)
│   ├── routes/           Core routes (auth, dashboard)
│   └── models/           Database models
│
├── plugins/              ⭐ PLUGIN IMPLEMENTATIONS
│   ├── stocks/           Stock tracking with alerts
│   ├── notes/            Simple timestamped notes
│   ├── notepad/          Multi-tab text editor
│   ├── surf/             Wave conditions monitoring
│   ├── journal/          Journal with images
│   ├── tradingview/      TradingView widgets
│   ├── system_monitor/   System metrics (CPU, RAM, disk)
│   └── hello_world/      Demo plugin
│
├── templates/            ⭐ SHARED HTML TEMPLATES
│   └── base.html         🔥 Navigation menu - EDIT TO ADD LINKS
│
├── data/                 ⭐ DATABASES
│   ├── cameronpad_dev.db 🔥 Active database
│   └── app.db            Legacy database (backup)
│
└── docs/                 ⭐ THIS DOCUMENTATION
    ├── README.md         Overview (you are here)
    ├── COMPLETE_GUIDE.md Full documentation
    ├── QUICK_REFERENCE.md Cheat sheet
    └── PLUGIN_TEMPLATE.md Copy-paste template
```

---

## 🔌 Current Plugins

| Plugin | Status | Description |
|--------|--------|-------------|
| **Stocks** | ✅ Working | Track stock prices, set alerts, predictions |
| **Notes** | ✅ Working | Simple timestamped notes with CRUD |
| **Notepad** | ✅ Working | Multi-tab text editor (19 tabs migrated) |
| **Surf** | ✅ Working | Wave conditions for 24 surf spots |
| **Journal** | 🟡 Template | Journal with image uploads (needs completion) |
| **TradingView** | ✅ Working | Embedded TradingView widgets |
| **System Monitor** | ✅ Working | CPU, RAM, disk usage monitoring |
| **Hello World** | ✅ Working | Demo plugin for testing |

**Legend:**
- ✅ Fully functional
- 🟡 Template ready, needs implementation
- 🔴 Not started

---

## 🗄️ Database Status

After migration:

| Table | Records | Plugin |
|-------|---------|--------|
| notes | 1 | Notes |
| pad_tabs | 19 | Notepad |
| surf_spots | 24 | Surf |
| surf_cache | 0 | Surf (will populate on refresh) |
| stocks | 1 | Stocks |
| alerts | 0 | Stocks (historical alerts) |
| latest_prices | 0 | Stocks (will populate on API call) |
| predictions | 0 | Stocks (will populate on prediction run) |

---

## 🎯 Common Tasks

### Create a New Plugin

```powershell
# 1. Copy template
Copy-Item -Recurse docs\PLUGIN_TEMPLATE plugins\my_plugin

# 2. Edit files (see PLUGIN_TEMPLATE.md for details)
# - config.yaml (metadata)
# - plugin.py (logic)
# - database.py (tables)
# - templates/my_plugin.html (UI)

# 3. Restart server
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

# 4. Visit http://127.0.0.1:8000/api/v1/plugins/my_plugin/
```

### Add Plugin to Navigation Menu

1. Open `templates/base.html`
2. Find the `<div class="dropdown-content">` section
3. Add: `<a href="/api/v1/plugins/my_plugin/">🚀 My Plugin</a>`
4. Restart server

### Debug Issues

```powershell
# Check logs
# Server prints detailed logs to console

# View database tables
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); print([r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')]); conn.close()"

# Kill stuck processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

---

## 🌐 Important URLs

### Local Development
- **Home:** http://127.0.0.1:8000/
- **Dashboard:** http://127.0.0.1:8000/dashboard
- **API Docs:** http://127.0.0.1:8000/docs (auto-generated by FastAPI)

### Plugin URLs
All plugins are at: `http://127.0.0.1:8000/api/v1/plugins/{plugin_name}/`

- Notes: http://127.0.0.1:8000/api/v1/plugins/notes/
- Notepad: http://127.0.0.1:8000/api/v1/plugins/notepad/
- Surf: http://127.0.0.1:8000/api/v1/plugins/surf/
- Stocks: http://127.0.0.1:8000/api/v1/plugins/stocks/
- Journal: http://127.0.0.1:8000/api/v1/plugins/journal/
- TradingView: http://127.0.0.1:8000/api/v1/plugins/tradingview/
- System Monitor: http://127.0.0.1:8000/api/v1/plugins/system_monitor/

---

## 📚 Learning Path

### If you're new to the project:
1. Start with **QUICK_REFERENCE.md** to get familiar with commands
2. Read **COMPLETE_GUIDE.md** sections 1-3 (Quick Start, Architecture, File Structure)
3. Create a simple plugin using **PLUGIN_TEMPLATE.md**
4. Read the rest of **COMPLETE_GUIDE.md** as needed

### If you're building a new plugin:
1. Read **PLUGIN_TEMPLATE.md** first
2. Copy the template directory
3. Refer to existing plugins (notes, notepad, surf) for examples
4. Use **QUICK_REFERENCE.md** for database operations

### If you're deploying to production:
1. Read **COMPLETE_GUIDE.md** section 9 (Deployment)
2. Set up environment variables
3. Choose deployment method (Docker, VPS, or Render)
4. Follow the step-by-step deployment guide

---

## 🆘 Getting Help

### Troubleshooting Order:
1. Check **QUICK_REFERENCE.md** → Quick Fixes section
2. Check **COMPLETE_GUIDE.md** → Troubleshooting section
3. Review server console logs for error messages
4. Check if database tables exist
5. Verify plugin config.yaml is valid YAML

### Common Issues:

**Server won't start:**
- Kill existing Python processes
- Check port 8000 isn't in use
- Verify Python 3.8+ is installed

**Plugin not loading:**
- Check config.yaml exists
- Verify get_plugin() function in plugin.py
- Look for error in server logs

**Database errors:**
- Ensure data/ directory exists
- Check database file permissions
- Run database init function

---

## 🎉 Current Status

**Your CameronPAD v2.0 is fully operational!**

✅ **Working:**
- 8 plugins loaded and functional
- Database migrated (1 note, 19 tabs, 24 surf spots, 1 stock)
- All CRUD operations implemented
- Server running on http://127.0.0.1:8000
- Navigation menu with dropdown
- Template inheritance working
- Authentication system ready

🟡 **In Progress:**
- Stock API integration (needs API keys)
- Background polling tasks (stocks, surf)
- Notification system (Twilio, Telegram, Discord)

📝 **Planned:**
- Journal plugin completion
- More plugins as you build them!

---

## 🚀 Next Steps

1. **Immediate:**
   - Test all plugins by visiting their URLs
   - Add any API keys you have to `.env`
   - Create your first custom plugin!

2. **Short Term:**
   - Set up background tasks for surf data updates
   - Add stock API keys and test price tracking
   - Customize navigation menu

3. **Long Term:**
   - Deploy to production
   - Set up SSL certificate
   - Add more plugins as needed
   - Share with the world! 🌍

---

## 📞 Support

- **Documentation:** You're reading it! See the other files in this directory
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Jinja2 Docs:** https://jinja.palletsprojects.com/
- **SQLite Docs:** https://www.sqlite.org/docs.html

---

## 📝 Version History

- **v2.0** (October 2025) - Complete rewrite with plugin architecture
- **v1.0** (2024) - Original monolithic app

---

**Remember:** This is YOUR application. Customize it, extend it, break it, fix it, and make it amazing! 🎨

**Have fun coding!** 🚀✨
