"""
Journal Plugin - Daily journal with calendar view and image uploads
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date
from fastapi import Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class JournalPlugin(WebPlugin):
    """Daily journal with calendar interface and photo uploads"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        
    async def initialize(self) -> None:
        """Initialize the Journal plugin"""
        logger.info("📔 Initializing Journal plugin...")
        
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
        
        logger.info("✅ Journal plugin initialized successfully")
        
    async def shutdown(self) -> None:
        """Clean shutdown"""
        logger.info("🛑 Journal plugin shutting down")
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="journal",
            version="1.0.0",
            description="Daily journal with calendar view and image uploads",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for Journal plugin"""
        
        @self._router.get("/")
        async def journal_home(request: Request):
            """Render journal calendar page"""
            today = date.today().isoformat()
            
            return self.templates.TemplateResponse(
                "journal.html",
                {
                    "request": request,
                    "today": today,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/add")
        async def add_entry(
            entry_date: str = Form(..., alias="date"),
            title: str = Form(""),
            entry_time: str = Form("", alias="time"),
            location: str = Form(""),
            notes: str = Form(""),
            photos: Optional[List[UploadFile]] = File(None)
        ):
            """Add a new journal entry"""
            # TODO: Save entry and photos to database
            logger.info(f"📔 Adding journal entry for {entry_date}")
            return RedirectResponse("/api/v1/plugins/journal/", status_code=303)
        
        @self._router.post("/delete")
        async def delete_entry(entry_id: int = Form(...)):
            """Delete a journal entry"""
            # TODO: Delete entry and associated photos
            logger.info(f"🗑️ Deleting journal entry ID: {entry_id}")
            return RedirectResponse("/api/v1/plugins/journal/", status_code=303)
        
        @self._router.post("/image/delete")
        async def delete_image(image_id: int = Form(...)):
            """Delete a journal image"""
            # TODO: Delete image from database and filesystem
            logger.info(f"🗑️ Deleting journal image ID: {image_id}")
            return RedirectResponse("/api/v1/plugins/journal/", status_code=303)
        
        @self._router.get("/entries")
        async def get_entries(entry_date: str):
            """Get entries for a specific date"""
            # TODO: Fetch entries from database
            return {"entries": []}
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            return {"status": "active", "plugin": "journal"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "status": "healthy",
            "plugin": "journal",
            "version": self.config.version
        }
    
    def get_menu_items(self) -> list:
        """Return menu items for this plugin"""
        return [
            {
                "label": "Journal",
                "icon": "📔",
                "url": "/api/v1/plugins/journal/",
                "order": 50
            }
        ]


def get_plugin(config: PluginConfig) -> JournalPlugin:
    """Factory function to create plugin instance"""
    return JournalPlugin(config)
