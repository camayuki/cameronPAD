"""
Soccer Plugin
"""

from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
import logging

from app_new.plugins.base import WebPlugin, PluginMetadata, PluginConfig

logger = logging.getLogger(__name__)


class SoccerPlugin(WebPlugin):
    """Soccer plugin with major leagues, teams, and tournament data"""
    
    def __init__(self, config: PluginConfig = None):
        super().__init__(config)
        self.templates = None
        self.register_routes()
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="soccer",
            version="1.0.0",
            description="Soccer leagues, teams, and tournament history",
            author="CameronPAD",
            requires_auth=False,
            icon="⚽",
            display_name="Soccer"
        )
    
    async def initialize(self) -> None:
        """Initialize the plugin"""
        logger.info("⚽ Initializing Soccer plugin...")
        
        # Setup templates with ChoiceLoader to search both plugin and main templates
        template_dir = Path(__file__).parent / "templates"
        main_template_dir = Path(__file__).parent.parent.parent / "templates"
        
        # Create a ChoiceLoader that tries plugin templates first, then main templates
        loader = ChoiceLoader([
            FileSystemLoader(str(template_dir)),
            FileSystemLoader(str(main_template_dir))
        ])
        
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.templates.env.loader = loader
        
        logger.info("✅ Soccer plugin initialized successfully!")
    
    async def shutdown(self) -> None:
        """Cleanup when plugin is disabled"""
        logger.info("⚽ Shutting down Soccer plugin...")
    
    def register_routes(self) -> None:
        """Register plugin routes"""
        
        @self._router.get("/", response_class=HTMLResponse)
        @self._router.get("", response_class=HTMLResponse)
        async def main_page(request: Request):
            """Main soccer page"""
            return self.templates.TemplateResponse(
                "soccer.html",
                {"request": request}
            )
        
        @self._router.get("/status")
        async def status():
            """Health check endpoint"""
            return {"status": "ok", "plugin": "soccer"}
