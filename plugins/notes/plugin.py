"""
Notes Plugin - Timestamped notes with add/delete functionality and group support
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
        
        # Initialize database tables with the correct database path
        from .database import init_notes_db
        init_notes_db("data/cameronpad_dev.db")
        
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
            
            # Get current user ID from request state
            user_id = getattr(request.state, "user_id", None)
            username = getattr(request.state, "username", None)
            is_admin = getattr(request.state, "is_admin", False)
            
            # Fetch notes from database - filtered by user's groups
            notes = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    
                    if user_id:
                        # Only show notes from groups the user belongs to
                        cur.execute("""
                            SELECT DISTINCT n.id, n.content, n.ts 
                            FROM notes n
                            INNER JOIN user_groups ug ON n.group_id = ug.group_id
                            WHERE ug.user_id = ?
                            ORDER BY n.ts DESC
                        """, (user_id,))
                        notes = [dict(row) for row in cur.fetchall()]
                        logger.info(f"📋 Loaded {len(notes)} notes for user {user_id} ({username})")
                    else:
                        # No user logged in - show no notes
                        logger.warning("⚠️ No user logged in - showing no notes")
                        notes = []
            except Exception as e:
                logger.error(f"Failed to fetch notes: {e}")
            
            return self.templates.TemplateResponse(
                "notes.html",
                {
                    "request": request,
                    "notes": notes,
                    "user": {"id": user_id, "username": username, "is_admin": is_admin} if user_id else None
                }
            )
        
        @self._router.post("/add")
        async def add_note(content: str = Form(...), request: Request = None):
            """Add a new note"""
            import sqlite3
            
            try:
                # Get current user ID from request state
                user_id = getattr(request.state, "user_id", None) if request else None
                
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    
                    # Get user's primary group (prefer Admins if they're in it)
                    group_id = None
                    if user_id:
                        cur.execute("""
                            SELECT g.id 
                            FROM user_groups ug 
                            JOIN groups g ON ug.group_id = g.id 
                            WHERE ug.user_id = ?
                            ORDER BY CASE WHEN g.name = 'Admins' THEN 0 ELSE 1 END
                            LIMIT 1
                        """, (user_id,))
                        result = cur.fetchone()
                        group_id = result[0] if result else None
                    
                    # Insert note with user_id and group_id
                    cur.execute(
                        "INSERT INTO notes(content, ts, user_id, group_id) VALUES(?, CURRENT_TIMESTAMP, ?, ?)",
                        (content.strip(), user_id, group_id)
                    )
                    conn.commit()
                    logger.info(f"📝 Added note by user {user_id} to group {group_id}: {content[:50]}...")
            except Exception as e:
                logger.error(f"Failed to add note: {e}")
            
            return RedirectResponse("/api/v1/plugins/notes/", status_code=303)
        
        @self._router.post("/delete")
        async def delete_note(note_id: int = Form(...), request: Request = None):
            """Delete a note"""
            import sqlite3
            
            # Get current user ID from request state
            user_id = getattr(request.state, "user_id", None) if request else None
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    
                    # Only allow deletion if the note belongs to a group the user is in
                    if user_id:
                        cur.execute("""
                            DELETE FROM notes 
                            WHERE id = ? 
                            AND group_id IN (
                                SELECT group_id FROM user_groups WHERE user_id = ?
                            )
                        """, (note_id, user_id))
                        
                        if cur.rowcount > 0:
                            conn.commit()
                            logger.info(f"🗑️ User {user_id} deleted note ID: {note_id}")
                        else:
                            logger.warning(f"⚠️ User {user_id} attempted to delete note {note_id} without permission")
                    else:
                        logger.warning(f"⚠️ Unauthenticated deletion attempt for note {note_id}")
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
