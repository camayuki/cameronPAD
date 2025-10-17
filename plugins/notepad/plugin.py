"""
Notepad Plugin - Multi-tab text editor for longer notes
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class NotepadPlugin(WebPlugin):
    """Multi-tab notepad for longer notes"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        
    async def initialize(self) -> None:
        """Initialize the Notepad plugin"""
        logger.info("📓 Initializing Notepad plugin...")
        
        # Initialize database tables
        from .database import init_notepad_db
        init_notepad_db()
        
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
        
        logger.info("✅ Notepad plugin initialized successfully")
        
    async def shutdown(self) -> None:
        """Clean shutdown"""
        logger.info("🛑 Notepad plugin shutting down")
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="notepad",
            version="1.0.0",
            description="Multi-tab text editor for longer notes and code snippets",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for Notepad plugin"""
        
        @self._router.get("/")
        async def notepad_home(request: Request, tab_id: Optional[int] = None):
            """Render notepad home page"""
            import sqlite3
            
            # Fetch tabs from database
            tabs = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT id, name, content FROM pad_tabs ORDER BY id")
                    tabs = [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Failed to fetch tabs: {e}")
            
            # Select active tab
            if tab_id is None and tabs:
                tab_id = tabs[0]["id"]
            
            active_tab = next((t for t in tabs if t["id"] == tab_id), tabs[0] if tabs else None)
            
            return self.templates.TemplateResponse(
                "notepad.html",
                {
                    "request": request,
                    "tabs": tabs,
                    "active_tab": active_tab,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/save")
        async def save_content(tab_id: int = Form(...), content: str = Form(...)):
            """Save notepad content"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE pad_tabs SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (content, tab_id)
                    )
                    conn.commit()
                    logger.info(f"💾 Saved notepad tab ID: {tab_id}")
            except Exception as e:
                logger.error(f"Failed to save tab: {e}")
            
            return RedirectResponse(f"/api/v1/plugins/notepad/?tab_id={tab_id}", status_code=303)
        
        @self._router.post("/tab/add")
        async def add_tab(name: str = Form(...)):
            """Create a new tab"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO pad_tabs(name, content, updated_at) VALUES(?, '', CURRENT_TIMESTAMP)",
                        (name.strip(),)
                    )
                    conn.commit()
                    logger.info(f"➕ Created new tab: {name}")
            except Exception as e:
                logger.error(f"Failed to add tab: {e}")
            
            return RedirectResponse("/api/v1/plugins/notepad/", status_code=303)
        
        @self._router.post("/tab/rename")
        async def rename_tab(tab_id: int = Form(...), name: str = Form(...)):
            """Rename a tab"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE pad_tabs SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (name.strip(), tab_id)
                    )
                    conn.commit()
                    logger.info(f"✏️ Renamed tab ID {tab_id} to: {name}")
            except Exception as e:
                logger.error(f"Failed to rename tab: {e}")
            
            return RedirectResponse(f"/api/v1/plugins/notepad/?tab_id={tab_id}", status_code=303)
        
        @self._router.post("/tab/delete")
        async def delete_tab(tab_id: int = Form(...)):
            """Delete a tab"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM pad_tabs WHERE id = ?", (tab_id,))
                    conn.commit()
                    logger.info(f"🗑️ Deleted tab ID: {tab_id}")
            except Exception as e:
                logger.error(f"Failed to delete tab: {e}")
            
            return RedirectResponse("/api/v1/plugins/notepad/", status_code=303)
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            return {"status": "active", "plugin": "notepad"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "status": "healthy",
            "plugin": "notepad",
            "version": self.config.version
        }
    
    def get_menu_items(self) -> list:
        """Return menu items for this plugin"""
        return [
            {
                "label": "Notepad",
                "icon": "📓",
                "url": "/api/v1/plugins/notepad/",
                "order": 30
            }
        ]


def get_plugin(config: PluginConfig) -> NotepadPlugin:
    """Factory function to create plugin instance"""
    return NotepadPlugin(config)
