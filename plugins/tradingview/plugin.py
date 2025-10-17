"""
TradingView Plugin - Market widgets and symbol overview
"""
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class TradingViewPlugin(WebPlugin):
    """TradingView market heatmap and symbol overview widgets"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        
    async def initialize(self) -> None:
        """Initialize the TradingView plugin"""
        logger.info("📊 Initializing TradingView plugin...")
        
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
        
        logger.info("✅ TradingView plugin initialized successfully")
        
    async def shutdown(self) -> None:
        """Clean shutdown"""
        logger.info("🛑 TradingView plugin shutting down")
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="tradingview",
            version="1.0.0",
            description="TradingView widgets for market heatmap and symbol overview",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for TradingView plugin"""
        
        @self._router.get("/")
        async def tradingview_home(request: Request):
            """Render TradingView page"""
            # TODO: Fetch symbols from database
            symbols = self.config.settings.get("default_symbols", [])
            
            return self.templates.TemplateResponse(
                "tradingview.html",
                {
                    "request": request,
                    "symbols": symbols,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/add")
        async def add_symbol(tv_symbol: str = Form(...), label: str = Form("")):
            """Add a symbol to the overview"""
            # TODO: Save symbol to database
            symbol = tv_symbol.strip().upper()
            lbl = (label.strip() or symbol.split(":")[-1])[:20]
            logger.info(f"📊 Adding TradingView symbol: {symbol} ({lbl})")
            return RedirectResponse("/api/v1/plugins/tradingview/", status_code=303)
        
        @self._router.post("/delete")
        async def delete_symbol(tv_symbol: str = Form(...)):
            """Remove a symbol from the overview"""
            # TODO: Delete symbol from database
            logger.info(f"🗑️ Deleting TradingView symbol: {tv_symbol}")
            return RedirectResponse("/api/v1/plugins/tradingview/", status_code=303)
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            return {"status": "active", "plugin": "tradingview"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "status": "healthy",
            "plugin": "tradingview",
            "version": self.config.version
        }
    
    def get_menu_items(self) -> list:
        """Return menu items for this plugin"""
        return [
            {
                "label": "TradingView",
                "icon": "📊",
                "url": "/api/v1/plugins/tradingview/",
                "order": 15
            }
        ]


def get_plugin(config: PluginConfig) -> TradingViewPlugin:
    """Factory function to create plugin instance"""
    return TradingViewPlugin(config)
