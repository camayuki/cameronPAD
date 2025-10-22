"""
TradingView Plugin - Market widgets and symbol overview
"""
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata
from . import database as db

logger = logging.getLogger(__name__)


class TradingViewPlugin(WebPlugin):
    """TradingView market heatmap and symbol overview widgets"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        
    async def initialize(self) -> None:
        """Initialize the TradingView plugin"""
        logger.info("📊 Initializing TradingView plugin...")
        
        # Initialize database
        db.init_db()
        
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
            priority=100,
            requires_auth=False  # TradingView plugin is public
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for TradingView plugin"""
        
        @self._router.get("/")
        async def tradingview_home(request: Request):
            """Render TradingView page"""
            # Fetch saved charts from database
            charts = db.get_all_charts()
            symbols = self.config.settings.get("default_symbols", [])
            
            return self.templates.TemplateResponse(
                "tradingview.html",
                {
                    "request": request,
                    "symbols": symbols,
                    "charts": charts,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/charts/add")
        async def add_chart(chart_number: int = Form(...), timeframe: str = Form("D")):
            """Add a new chart"""
            db.add_chart(chart_number, timeframe)
            return JSONResponse({"success": True, "chart_number": chart_number})
        
        @self._router.post("/charts/delete")
        async def delete_chart_endpoint(chart_number: int = Form(...)):
            """Delete a chart and its notes"""
            db.delete_chart(chart_number)
            return JSONResponse({"success": True})
        
        @self._router.post("/charts/notes/save")
        async def save_notes(chart_number: int = Form(...), notes: str = Form("")):
            """Save notes for a chart"""
            db.save_chart_notes(chart_number, notes)
            return JSONResponse({"success": True})
        
        @self._router.get("/charts/notes/{chart_number}")
        async def get_notes(chart_number: int):
            """Get notes for a chart"""
            notes = db.get_chart_notes(chart_number)
            return JSONResponse({"notes": notes})
        
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
