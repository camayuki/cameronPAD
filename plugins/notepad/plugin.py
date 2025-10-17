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
        
        # Add get_theme_css function to template globals
        def get_theme_css(theme_vars):
            if not theme_vars:
                return ""
            return "\n".join([f"    {k}: {v};" for k, v in theme_vars.items()])
        self.templates.env.globals['get_theme_css'] = get_theme_css
        
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
            
            # Get current user ID from request state
            user_id = getattr(request.state, "user_id", None)
            username = getattr(request.state, "username", None)
            is_admin = getattr(request.state, "is_admin", False)
            
            # Fetch tabs from database - filtered by user's groups
            tabs = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    
                    if user_id:
                        # Only show tabs from groups the user belongs to
                        cur.execute("""
                            SELECT DISTINCT p.id, p.name, p.content 
                            FROM pad_tabs p
                            INNER JOIN user_groups ug ON p.group_id = ug.group_id
                            WHERE ug.user_id = ?
                            ORDER BY p.id
                        """, (user_id,))
                        tabs = [dict(row) for row in cur.fetchall()]
                        logger.info(f"📓 Loaded {len(tabs)} notepad tabs for user {user_id} ({username})")
                    else:
                        # No user logged in - show no tabs
                        logger.warning("⚠️ No user logged in - showing no tabs")
                        tabs = []
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
                    "user": {"id": user_id, "username": username, "is_admin": is_admin} if user_id else None
                }
            )
        
        @self._router.post("/save")
        async def save_content(tab_id: int = Form(...), content: str = Form(...), request: Request = None):
            """Save notepad content"""
            import sqlite3
            
            # Get current user
            user_id = getattr(request.state, "user_id", None) if request else None
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    
                    # Only allow saving if the tab belongs to a group the user is in
                    if user_id:
                        cur.execute("""
                            UPDATE pad_tabs 
                            SET content = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ? 
                            AND group_id IN (
                                SELECT group_id FROM user_groups WHERE user_id = ?
                            )
                        """, (content, tab_id, user_id))
                        
                        if cur.rowcount > 0:
                            conn.commit()
                            logger.info(f"💾 User {user_id} saved notepad tab ID: {tab_id}")
                        else:
                            logger.warning(f"⚠️ User {user_id} attempted to save tab {tab_id} without permission")
                    else:
                        logger.warning(f"⚠️ Unauthenticated save attempt for tab {tab_id}")
            except Exception as e:
                logger.error(f"Failed to save tab: {e}")
            
            return RedirectResponse(f"/api/v1/plugins/notepad/?tab_id={tab_id}", status_code=303)
        
        @self._router.post("/tab/add")
        async def add_tab(name: str = Form(...), request: Request = None):
            """Create a new tab"""
            import sqlite3
            
            try:
                # Get current user from request
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
                    
                    cur.execute(
                        "INSERT INTO pad_tabs(name, content, user_id, group_id, updated_at) VALUES(?, '', ?, ?, CURRENT_TIMESTAMP)",
                        (name.strip(), user_id, group_id)
                    )
                    conn.commit()
                    logger.info(f"➕ Created new tab by user {user_id} in group {group_id}: {name}")
            except Exception as e:
                logger.error(f"Failed to add tab: {e}")
            
            return RedirectResponse("/api/v1/plugins/notepad/", status_code=303)
        
        @self._router.post("/tab/rename")
        async def rename_tab(tab_id: int = Form(...), name: str = Form(...), request: Request = None):
            """Rename a tab"""
            import sqlite3
            
            # Get current user
            user_id = getattr(request.state, "user_id", None) if request else None
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    
                    # Only allow renaming if the tab belongs to a group the user is in
                    if user_id:
                        cur.execute("""
                            UPDATE pad_tabs 
                            SET name = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ? 
                            AND group_id IN (
                                SELECT group_id FROM user_groups WHERE user_id = ?
                            )
                        """, (name.strip(), tab_id, user_id))
                        
                        if cur.rowcount > 0:
                            conn.commit()
                            logger.info(f"✏️ User {user_id} renamed tab ID {tab_id} to: {name}")
                        else:
                            logger.warning(f"⚠️ User {user_id} attempted to rename tab {tab_id} without permission")
                    else:
                        logger.warning(f"⚠️ Unauthenticated rename attempt for tab {tab_id}")
            except Exception as e:
                logger.error(f"Failed to rename tab: {e}")
            
            return RedirectResponse(f"/api/v1/plugins/notepad/?tab_id={tab_id}", status_code=303)
        
        @self._router.post("/tab/delete")
        async def delete_tab(tab_id: int = Form(...), request: Request = None):
            """Delete a tab"""
            import sqlite3
            
            # Get current user
            user_id = getattr(request.state, "user_id", None) if request else None
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    
                    # Only allow deletion if the tab belongs to a group the user is in
                    if user_id:
                        cur.execute("""
                            DELETE FROM pad_tabs 
                            WHERE id = ? 
                            AND group_id IN (
                                SELECT group_id FROM user_groups WHERE user_id = ?
                            )
                        """, (tab_id, user_id))
                        
                        if cur.rowcount > 0:
                            conn.commit()
                            logger.info(f"🗑️ User {user_id} deleted tab ID: {tab_id}")
                        else:
                            logger.warning(f"⚠️ User {user_id} attempted to delete tab {tab_id} without permission")
                    else:
                        logger.warning(f"⚠️ Unauthenticated deletion attempt for tab {tab_id}")
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

