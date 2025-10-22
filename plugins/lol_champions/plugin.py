"""
League of Legends Champions Plugin for CameronPAD
Pure vanilla JavaScript implementation - no React, no Babel, no CSP issues
"""

from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
import logging

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class LOLChampionsPlugin(WebPlugin):
    """League of Legends Champions browser plugin - vanilla JS version"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="League of Legends Champions",
            version="2.0.0",
            description="Browse League of Legends champions (Vanilla JS)",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100,
            requires_auth=False  # LoL Champions plugin is public
        )
    
    async def initialize(self) -> None:
        """Initialize the LoL Champions plugin"""
        logger.info("🎮 Initializing LoL Champions plugin (Vanilla JS)...")
        
        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        main_template_dir = Path(__file__).parent.parent.parent / "templates"
        
        loader = ChoiceLoader([
            FileSystemLoader(str(template_dir)),
            FileSystemLoader(str(main_template_dir))
        ])
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.templates.env.loader = loader
        
        # Add theme CSS function
        def get_theme_css(theme_vars):
            if not theme_vars:
                return ""
            return "\n".join([f"    {k}: {v};" for k, v in theme_vars.items()])
        self.templates.env.globals['get_theme_css'] = get_theme_css
        
        # Register routes
        self.register_routes()
        self._initialized = True
        
        logger.info("✅ LoL Champions plugin initialized")
    
    def register_routes(self) -> None:
        """Register web routes"""
        
        @self._router.get("", response_class=HTMLResponse)
        @self._router.get("/", response_class=HTMLResponse)
        async def champions_page(request: Request):
            """Main champions browser page"""
            logger.info("🎮 LoL Champions page accessed")
            
            user_id = getattr(request.state, 'user_id', None)
            username = getattr(request.state, 'username', 'Guest')
            is_admin = getattr(request.state, 'is_admin', False)
            
            current_user = {
                "id": user_id,
                "username": username,
                "is_admin": is_admin,
                "role": 'admin' if is_admin else 'user'
            }
            
            return self.templates.TemplateResponse("lol_champions.html", {
                "request": request,
                "current_user": current_user,
                "plugin_name": "League of Legends Champions"
            })
    
    async def shutdown(self) -> None:
        """Called when plugin shuts down"""
        logger.info("🛑 LoL Champions plugin shutting down")
    
    def get_menu_items(self):
        """Return menu items for the web interface"""
        return [
            {
                "name": "LoL Champions",
                "url": "/api/v1/plugins/lol_champions",
                "icon": "🎮"
            }
        ]
