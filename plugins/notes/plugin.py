"""
Notes Plugin - Timestamped notes with add/delete functionality
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


class NotesPlugin(WebPlugin):
    """Simple timestamped notes plugin"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        
    async def initialize(self) -> None:
        """Initialize the Notes plugin"""
        logger.info("📝 Initializing Notes plugin...")
        
        # Initialize database tables
        from .database import init_notes_db
        init_notes_db()
        
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
        
        logger.info("✅ Notes plugin initialized successfully")
        
    async def shutdown(self) -> None:
        """Clean shutdown"""
        logger.info("🛑 Notes plugin shutting down")
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="notes",
            version="1.0.0",
            description="Timestamped notes with add/delete functionality",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for Notes plugin"""
        
        @self._router.get("/")
        async def notes_home(request: Request):
            """Render notes home page"""
            import sqlite3
            
            # Fetch notes from database
            notes = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT id, content, ts FROM notes ORDER BY ts DESC")
                    notes = [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Failed to fetch notes: {e}")
            
            return self.templates.TemplateResponse(
                "notes.html",
                {
                    "request": request,
                    "notes": notes,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/add")
        async def add_note(content: str = Form(...)):
            """Add a new note"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO notes(content, ts) VALUES(?, CURRENT_TIMESTAMP)",
                        (content.strip(),)
                    )
                    conn.commit()
                    logger.info(f"📝 Added note: {content[:50]}...")
            except Exception as e:
                logger.error(f"Failed to add note: {e}")
            
            return RedirectResponse("/api/v1/plugins/notes/", status_code=303)
        
        @self._router.post("/delete")
        async def delete_note(note_id: int = Form(...)):
            """Delete a note"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                    conn.commit()
                    logger.info(f"🗑️ Deleted note ID: {note_id}")
            except Exception as e:
                logger.error(f"Failed to delete note: {e}")
            
            return RedirectResponse("/api/v1/plugins/notes/", status_code=303)
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            return {"status": "active", "plugin": "notes"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "status": "healthy",
            "plugin": "notes",
            "version": self.config.version
        }
    
    def get_menu_items(self) -> list:
        """Return menu items for this plugin"""
        return [
            {
                "label": "Notes",
                "icon": "📝",
                "url": "/api/v1/plugins/notes/",
                "order": 20
            }
        ]


def get_plugin(config: PluginConfig) -> NotesPlugin:
    """Factory function to create plugin instance"""
    return NotesPlugin(config)
