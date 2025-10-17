# New Plugin Template

Copy this directory structure to create a new plugin quickly.

## Directory Structure

```
plugins/YOUR_PLUGIN_NAME/
├── config.yaml
├── plugin.py
├── database.py
└── templates/
    └── your_plugin.html
```

---

## File: `config.yaml`

```yaml
name: your_plugin_name
version: 1.0.0
description: "Brief description of what your plugin does"
author: "Your Name"
enabled: true
priority: 100  # Lower number loads first (50=high, 100=normal, 150=low)

settings:
  # Add any plugin-specific settings here
  refresh_interval: 300
  max_items: 100

dependencies: []  # List other plugins this depends on (e.g., ["stocks"])

api_version: "1.0"
```

---

## File: `database.py`

```python
"""
Database initialization for Your Plugin
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_your_plugin_db():
    """Initialize database tables for your plugin"""
    logger.info("🗄️ Initializing Your Plugin database tables...")
    
    conn = sqlite3.connect("data/cameronpad_dev.db")
    cur = conn.cursor()
    
    # Create your main table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS your_plugin_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            value REAL,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create additional tables if needed
    cur.execute("""
        CREATE TABLE IF NOT EXISTS your_plugin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES your_plugin_items(id) ON DELETE CASCADE
        )
    """)
    
    # Handle migrations (add columns to existing tables)
    try:
        cur.execute("ALTER TABLE your_plugin_items ADD COLUMN new_field TEXT")
        logger.info("Added new_field column to your_plugin_items")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()
    
    logger.info("✅ Your Plugin database tables initialized")
```

---

## File: `plugin.py`

```python
"""
Your Plugin Name - Brief description
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class YourPlugin(WebPlugin):
    """Your plugin implementation"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        # Add any instance variables you need
        self.cache = {}
        
    async def initialize(self) -> None:
        """Initialize the plugin"""
        logger.info("🚀 Initializing Your Plugin...")
        
        # 1. Initialize database tables
        from .database import init_your_plugin_db
        init_your_plugin_db()
        
        # 2. Setup templates with ChoiceLoader (searches plugin templates first, then main)
        template_dir = Path(__file__).parent / "templates"
        main_template_dir = Path(__file__).parent.parent.parent / "templates"
        
        loader = ChoiceLoader([
            FileSystemLoader(str(template_dir)),
            FileSystemLoader(str(main_template_dir))
        ])
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.templates.env.loader = loader
        
        # 3. Register routes
        self.register_routes()
        
        # 4. Do any additional initialization (load config, start background tasks, etc.)
        # self.load_config()
        # await self.start_background_tasks()
        
        logger.info("✅ Your Plugin initialized successfully")
        
    async def shutdown(self) -> None:
        """Clean shutdown - cleanup resources"""
        logger.info("🛑 Your Plugin shutting down")
        
        # Stop any background tasks
        # Cancel any pending operations
        # Close any open connections
        
        logger.info("✅ Your Plugin shutdown completed")
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="your_plugin_name",
            version="1.0.0",
            description="Brief description of your plugin",
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
                    cur.execute("""
                        SELECT id, name, description, value, status, created_at 
                        FROM your_plugin_items 
                        ORDER BY created_at DESC
                    """)
                    items = [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Failed to fetch items: {e}")
            
            return self.templates.TemplateResponse(
                "your_plugin.html",
                {
                    "request": request,
                    "items": items,
                    "plugin_name": "Your Plugin",
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/add")
        async def add_item(
            name: str = Form(...),
            description: str = Form(""),
            value: Optional[float] = Form(None)
        ):
            """Add a new item"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO your_plugin_items(name, description, value)
                        VALUES(?, ?, ?)
                    """, (name.strip(), description.strip(), value))
                    conn.commit()
                    logger.info(f"✅ Added item: {name}")
            except Exception as e:
                logger.error(f"Failed to add item: {e}")
            
            return RedirectResponse("/api/v1/plugins/your_plugin_name/", status_code=303)
        
        @self._router.post("/update/{item_id}")
        async def update_item(
            item_id: int,
            name: str = Form(...),
            description: str = Form(""),
            value: Optional[float] = Form(None),
            status: str = Form("active")
        ):
            """Update an existing item"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE your_plugin_items 
                        SET name = ?, description = ?, value = ?, status = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (name.strip(), description.strip(), value, status, item_id))
                    conn.commit()
                    logger.info(f"✅ Updated item ID: {item_id}")
            except Exception as e:
                logger.error(f"Failed to update item: {e}")
            
            return RedirectResponse("/api/v1/plugins/your_plugin_name/", status_code=303)
        
        @self._router.post("/delete/{item_id}")
        async def delete_item(item_id: int = Form(...)):
            """Delete an item"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM your_plugin_items WHERE id = ?", (item_id,))
                    conn.commit()
                    logger.info(f"🗑️ Deleted item ID: {item_id}")
            except Exception as e:
                logger.error(f"Failed to delete item: {e}")
            
            return RedirectResponse("/api/v1/plugins/your_plugin_name/", status_code=303)
        
        @self._router.get("/api/items")
        async def get_items_api():
            """Get all items as JSON (API endpoint)"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM your_plugin_items ORDER BY created_at DESC")
                    items = [dict(row) for row in cur.fetchall()]
                return {"status": "success", "items": items}
            except Exception as e:
                logger.error(f"Failed to fetch items: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            import sqlite3
            
            # Count items
            item_count = 0
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    item_count = cur.execute("SELECT COUNT(*) FROM your_plugin_items").fetchone()[0]
            except:
                pass
            
            return {
                "status": "active",
                "plugin": "your_plugin_name",
                "version": "1.0.0",
                "item_count": item_count
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status for monitoring"""
        return {
            "status": "healthy",
            "plugin": "your_plugin_name",
            "version": self.config.version
        }
    
    def get_menu_items(self) -> list:
        """Return menu items for navigation (optional)"""
        return [
            {
                "label": "Your Plugin",
                "icon": "🚀",
                "url": "/api/v1/plugins/your_plugin_name/",
                "order": 100
            }
        ]


def get_plugin(config: PluginConfig) -> YourPlugin:
    """Factory function to create plugin instance - REQUIRED"""
    return YourPlugin(config)
```

---

## File: `templates/your_plugin.html`

```html
{% extends "base.html" %}

{% block title %}Your Plugin - CameronPAD{% endblock %}

{% block content %}
<div class="container" style="max-width: 1200px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #00f3ff; text-shadow: 0 0 10px #00f3ff;">🚀 Your Plugin</h1>
    
    <!-- Add Item Form -->
    <div style="background: rgba(0, 20, 40, 0.8); border: 1px solid #00f3ff; border-radius: 10px; padding: 20px; margin: 20px 0;">
        <h2 style="color: #00f3ff;">Add New Item</h2>
        <form method="POST" action="/api/v1/plugins/your_plugin_name/add" style="display: flex; flex-direction: column; gap: 15px;">
            
            <div>
                <label for="name" style="color: #fff; display: block; margin-bottom: 5px;">Name:</label>
                <input 
                    type="text" 
                    id="name" 
                    name="name" 
                    required 
                    style="width: 100%; padding: 10px; background: rgba(0, 50, 100, 0.5); border: 1px solid #00f3ff; border-radius: 5px; color: #fff;"
                >
            </div>
            
            <div>
                <label for="description" style="color: #fff; display: block; margin-bottom: 5px;">Description:</label>
                <textarea 
                    id="description" 
                    name="description" 
                    rows="3"
                    style="width: 100%; padding: 10px; background: rgba(0, 50, 100, 0.5); border: 1px solid #00f3ff; border-radius: 5px; color: #fff;"
                ></textarea>
            </div>
            
            <div>
                <label for="value" style="color: #fff; display: block; margin-bottom: 5px;">Value (optional):</label>
                <input 
                    type="number" 
                    id="value" 
                    name="value" 
                    step="0.01"
                    style="width: 100%; padding: 10px; background: rgba(0, 50, 100, 0.5); border: 1px solid #00f3ff; border-radius: 5px; color: #fff;"
                >
            </div>
            
            <button 
                type="submit" 
                style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; padding: 12px 30px; border-radius: 5px; color: white; font-weight: bold; cursor: pointer; font-size: 16px;"
            >
                ➕ Add Item
            </button>
        </form>
    </div>
    
    <!-- Items List -->
    <div style="background: rgba(0, 20, 40, 0.8); border: 1px solid #00f3ff; border-radius: 10px; padding: 20px; margin: 20px 0;">
        <h2 style="color: #00f3ff;">Items ({{ items|length }})</h2>
        
        {% if items %}
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; color: #fff;">
                    <thead>
                        <tr style="border-bottom: 2px solid #00f3ff;">
                            <th style="padding: 10px; text-align: left;">ID</th>
                            <th style="padding: 10px; text-align: left;">Name</th>
                            <th style="padding: 10px; text-align: left;">Description</th>
                            <th style="padding: 10px; text-align: left;">Value</th>
                            <th style="padding: 10px; text-align: left;">Status</th>
                            <th style="padding: 10px; text-align: left;">Created</th>
                            <th style="padding: 10px; text-align: left;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr style="border-bottom: 1px solid rgba(0, 243, 255, 0.2);">
                            <td style="padding: 10px;">{{ item.id }}</td>
                            <td style="padding: 10px; font-weight: bold;">{{ item.name }}</td>
                            <td style="padding: 10px;">{{ item.description or '-' }}</td>
                            <td style="padding: 10px;">
                                {% if item.value %}
                                    {{ "%.2f"|format(item.value) }}
                                {% else %}
                                    -
                                {% endif %}
                            </td>
                            <td style="padding: 10px;">
                                <span style="background: {% if item.status == 'active' %}#00ff00{% else %}#ff9900{% endif %}; padding: 3px 8px; border-radius: 3px; font-size: 12px;">
                                    {{ item.status }}
                                </span>
                            </td>
                            <td style="padding: 10px; font-size: 12px;">{{ item.created_at }}</td>
                            <td style="padding: 10px;">
                                <form method="POST" action="/api/v1/plugins/your_plugin_name/delete/{{ item.id }}" style="display: inline;">
                                    <button 
                                        type="submit" 
                                        onclick="return confirm('Delete this item?')"
                                        style="background: #ff4444; border: none; padding: 5px 10px; border-radius: 3px; color: white; cursor: pointer;"
                                    >
                                        🗑️ Delete
                                    </button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <p style="color: #999; text-align: center; padding: 20px;">
                No items yet. Add one above! 👆
            </p>
        {% endif %}
    </div>
    
    <!-- Status Info -->
    <div style="background: rgba(0, 20, 40, 0.8); border: 1px solid #00f3ff; border-radius: 10px; padding: 20px; margin: 20px 0;">
        <h3 style="color: #00f3ff;">ℹ️ Plugin Info</h3>
        <p style="color: #fff;">Version: 1.0.0</p>
        <p style="color: #fff;">Status: Active</p>
        <p style="color: #fff;">Total Items: {{ items|length }}</p>
    </div>
</div>

<style>
    /* Add any custom styles here */
    .container input:focus,
    .container textarea:focus {
        outline: 2px solid #00f3ff;
        box-shadow: 0 0 10px #00f3ff;
    }
    
    .container button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 243, 255, 0.4);
    }
    
    .container table tr:hover {
        background: rgba(0, 243, 255, 0.1);
    }
</style>
{% endblock %}
```

---

## Usage Instructions

1. **Copy this template directory:**
   ```powershell
   Copy-Item -Recurse docs\PLUGIN_TEMPLATE plugins\my_new_plugin
   ```

2. **Replace placeholder text:**
   - Change `your_plugin_name` to your actual plugin name (lowercase, underscores)
   - Change `Your Plugin` to your display name
   - Update description and author
   - Change table names to match your plugin

3. **Customize database schema:**
   - Edit `database.py` to create your tables
   - Add the fields you need

4. **Implement your logic:**
   - Add routes in `register_routes()`
   - Add business logic methods to the class
   - Connect to external APIs if needed

5. **Style your template:**
   - Edit `your_plugin.html`
   - Match the space theme (dark background, cyan accents)
   - Use Jinja2 templating

6. **Test:**
   ```powershell
   py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
   ```

7. **Add to navigation menu:**
   Edit `templates/base.html` to add your plugin link

---

## Tips

- **Keep it simple:** Start with basic CRUD operations
- **Use logging:** Add `logger.info()` for important actions
- **Handle errors:** Wrap database operations in try/except
- **Test thoroughly:** Add items, update them, delete them
- **Follow conventions:** Use the same patterns as existing plugins
- **Document:** Add docstrings to your methods

---

## Next Steps

After your plugin is working:

1. Add API endpoints for external access
2. Implement background tasks if needed
3. Add services.py for external API calls
4. Create models.py for complex data structures
5. Add tests in a `tests/` directory
6. Deploy and enjoy! 🚀
