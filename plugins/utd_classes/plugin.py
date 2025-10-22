"""UTD Classes Study Plugin - Quick reference guide for university courses."""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
import logging

from app_new.plugins.base import WebPlugin, PluginMetadata, PluginConfig

logger = logging.getLogger(__name__)


class UTDClassesPlugin(WebPlugin):
    """Plugin for studying UTD course materials."""

    def __init__(self, config: PluginConfig = None):
        """Initialize the UTD Classes plugin."""
        if config is None:
            config = PluginConfig(enabled=True)
        super().__init__(config)
        self.templates = None
        self.register_routes()

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="utd_classes",
            version="1.0.0",
            description="Study guide for UTD classes with tabbed interface",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100,
            requires_auth=False,  # Public access for quick studying
            icon="🎓",
            display_name="UTD Classes"
        )

    async def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("🎓 Initializing UTD Classes plugin...")
        
        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        main_template_dir = Path(__file__).parent.parent.parent / "templates"
        
        loader = ChoiceLoader([
            FileSystemLoader(str(template_dir)),
            FileSystemLoader(str(main_template_dir))
        ])
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.templates.env.loader = loader
        
        self._initialized = True
        logger.info("✅ UTD Classes plugin initialized successfully!")

    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        self._initialized = False

    def register_routes(self) -> None:
        """Register web routes for this plugin."""
        
        @self._router.get("/", response_class=HTMLResponse)
        @self._router.get("", response_class=HTMLResponse)
        async def main_page(request: Request):
            """Render main UTD Classes study page."""
            return self.templates.TemplateResponse(
                "utd_classes.html",
                {"request": request}
            )

        @self._router.get("/status")
        async def status():
            """Health check endpoint."""
            return {
                "status": "active",
                "plugin": "utd_classes",
                "version": "1.0.0"
            }

    def get_router(self) -> APIRouter:
        """Return the plugin's router."""
        return self._router
