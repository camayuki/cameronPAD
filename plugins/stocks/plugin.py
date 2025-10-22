"""
Stocks plugin for CameronPAD - tracks stock prices and alerts.
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from app_new.plugins.base import WebPlugin, PluginMetadata, PluginConfig
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

logger = logging.getLogger(__name__)


class StocksPlugin(WebPlugin):
    """Stock tracking and alerting plugin."""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.polling_task: Optional[asyncio.Task] = None
        self.stock_service = None
        self.templates = None
        self._service_running = False
        self._service_logs: List[Dict[str, str]] = []  # Store recent service logs
        self._max_logs = 100  # Keep last 100 log entries
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="stocks",
            version="1.0.0",
            description="Stock price tracking and alerting system",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=50,
            icon="📈",
            display_name="Stock Tracker"
        )
    
    async def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("📈 Initializing Stocks plugin...")
        
        # Initialize database tables
        from .database import init_stocks_db
        init_stocks_db()
        
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
        
        # Add get_enabled_plugins function to template globals
        def get_enabled_plugins():
            """Get list of enabled plugins for navigation"""
            # Map plugin names to icons
            plugin_icons = {
                'stocks': '📈',
                'notes': '📝',
                'journal': '📔',
                'surf': '🏄',
                'system_monitor': '🖥️',
                'hello_world': '👋',
                'notepad': '📓',
                'tradingview': '📊',
                'lol_champions': '🎮'
            }
            
            try:
                # Try to get plugin_manager from the main app
                from app_new.main import plugin_manager
                if not plugin_manager:
                    return []
                plugins_list = []
                for plugin_name, plugin in plugin_manager.get_enabled_plugins().items():
                    if hasattr(plugin, 'metadata'):
                        plugins_list.append({
                            'name': plugin.metadata.name,
                            'url': f"/api/v1/plugins/{plugin_name}/",
                            'icon': plugin_icons.get(plugin_name, '📦')
                        })
                return plugins_list
            except Exception as e:
                logger.error(f"Error getting enabled plugins: {e}", exc_info=True)
                return []
        
        self.templates.env.globals['get_enabled_plugins'] = get_enabled_plugins
        
        # Initialize stock service with API keys from environment FIRST
        from .services import StockService
        service_config = {
            'finnhub_token': os.getenv('FINNHUB_TOKEN', ''),
            'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_KEY', ''),
            'alert_cooldown_minutes': int(os.getenv('COOLDOWN_MIN', '30')),
            'alpha_min_interval': float(os.getenv('ALPHA_MIN_INTERVAL', '13.0')),
            'showcase_symbols': ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'SPY']
        }
        self.stock_service = StockService(service_config)
        logger.info("✅ Stock service initialized with API keys from environment")
        
        # Register routes (includes API routes with predictions)
        self.register_routes()
        
        # Ensure showcase symbols are in the database
        await self.stock_service.ensure_showcase_symbols()
        
        logger.info("✅ Stocks plugin initialized successfully")
    
    async def start_services(self) -> None:
        """Start background stock monitoring services."""
        if self._service_running:
            logger.warning("Stock services already running")
            self._add_service_log("WARNING", "Stock services already running")
            return
        
        logger.info("▶️ Starting stock monitoring services...")
        self._add_service_log("INFO", "▶️ Starting stock monitoring services...")
        
        # Do an initial update immediately
        try:
            logger.info("📊 Performing initial showcase update...")
            self._add_service_log("INFO", "📊 Performing initial showcase update...")
            await self.stock_service.update_showcase_prices()
            logger.info("✅ Initial showcase update complete")
            self._add_service_log("SUCCESS", "✅ Initial showcase update complete")
        except Exception as e:
            logger.error(f"❌ Initial update failed: {e}", exc_info=True)
            self._add_service_log("ERROR", f"❌ Initial update failed: {e}")
        
        # Start background tasks
        async def update_loop():
            showcase_counter = 0
            poll_seconds = int(os.getenv('POLL_SECONDS', '60'))
            showcase_refresh = int(os.getenv('SHOWCASE_REFRESH', '300'))  # 5 minutes default
            cycle_count = 0
            
            logger.info(f"🔄 [SERVICE] Starting update loop (poll={poll_seconds}s, showcase_refresh={showcase_refresh}s)")
            self._add_service_log("INFO", f"🔄 Update loop starting (poll={poll_seconds}s, showcase_refresh={showcase_refresh}s)")
            
            while True:
                try:
                    # Wait for next check
                    logger.info(f"⏱️ [SERVICE] Waiting {poll_seconds} seconds until next check...")
                    self._add_service_log("INFO", f"⏱️ Waiting {poll_seconds}s until next check...")
                    await asyncio.sleep(poll_seconds)
                    
                    cycle_count += 1
                    showcase_counter += poll_seconds
                    logger.info(f"🔄 [SERVICE] ═══════════════════════════════════════════════════")
                    logger.info(f"🔄 [SERVICE] Starting monitoring cycle #{cycle_count}")
                    logger.info(f"🔄 [SERVICE] ═══════════════════════════════════════════════════")
                    self._add_service_log("INFO", f"🔄 Monitoring cycle #{cycle_count}")
                    
                    # Update showcase prices periodically (every 5 minutes by default)
                    if showcase_counter >= showcase_refresh:
                        logger.info(f"📊 [SERVICE] Time to update showcase! (counter={showcase_counter}s >= refresh={showcase_refresh}s)")
                        logger.info("📊 [SERVICE] Starting showcase price update...")
                        self._add_service_log("INFO", "📊 Updating showcase prices...")
                        await self.stock_service.update_showcase_prices()
                        logger.info("✅ [SERVICE] Showcase prices update complete!")
                        self._add_service_log("SUCCESS", "✅ Showcase prices updated")
                        showcase_counter = 0
                    else:
                        logger.info(f"⏭️ [SERVICE] Skipping showcase update (counter={showcase_counter}s < refresh={showcase_refresh}s)")
                    
                    # Update tracked stocks and check alerts every cycle
                    logger.info("📊 [SERVICE] Updating tracked stock prices...")
                    self._add_service_log("INFO", "📊 Updating tracked stock prices...")
                    await self.stock_service.update_tracked_stocks()
                    logger.info("✅ [SERVICE] Tracked stocks updated")
                    
                    logger.info("🔔 [SERVICE] Checking alerts...")
                    self._add_service_log("INFO", "🔔 Checking alerts...")
                    await self.stock_service.check_alerts()
                    logger.info(f"✅ [SERVICE] Stock monitoring cycle #{cycle_count} complete")
                    logger.info(f"🔄 [SERVICE] ═══════════════════════════════════════════════════")
                    self._add_service_log("SUCCESS", f"✅ Monitoring cycle #{cycle_count} complete")
                    
                except asyncio.CancelledError:
                    logger.info("🛑 [SERVICE] Update loop cancelled")
                    self._add_service_log("INFO", "🛑 Update loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in stock update loop: {e}", exc_info=True)
                    self._add_service_log("ERROR", f"❌ Error in stock update loop: {e}")
                    # Continue loop even on error
                    logger.info("⚠️ Continuing loop after error...")
                    self._add_service_log("WARNING", "⚠️ Continuing loop after error...")
        
        self.polling_task = asyncio.create_task(update_loop())
        self._service_running = True
        logger.info("✅ Stock monitoring services started")
        self._add_service_log("SUCCESS", "✅ Stock monitoring services started")
        logger.info("✅ Stock monitoring services started")
    
    async def stop_services(self) -> None:
        """Stop background stock monitoring services."""
        if not self._service_running:
            logger.warning("Stock services not running")
            self._add_service_log("WARNING", "Stock services not running")
            return
        
        logger.info("⏹️ Stopping stock monitoring services...")
        self._add_service_log("INFO", "⏹️ Stopping stock monitoring services...")
        
        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        
        self._service_running = False
        logger.info("✅ Stock monitoring services stopped")
        self._add_service_log("SUCCESS", "✅ Stock monitoring services stopped")
    
    def _add_service_log(self, level: str, message: str) -> None:
        """Add a log entry to the service logs buffer."""
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        self._service_logs.append(log_entry)
        
        # Keep only the last N logs
        if len(self._service_logs) > self._max_logs:
            self._service_logs = self._service_logs[-self._max_logs:]
    
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        logger.info("🛑 Shutting down Stocks plugin...")
        self._add_service_log("INFO", "🛑 Shutting down Stocks plugin...")
        
        # Stop services if running
        if self._service_running:
            await self.stop_services()
        
        logger.info("✅ Stocks plugin shutdown completed")
        self._add_service_log("INFO", "✅ Stocks plugin shutdown completed")
    
    def register_routes(self) -> None:
        """Register web routes for this plugin."""
        
        # Import and setup API routes (includes predictions endpoint)
        from .api import setup_routes as setup_api_routes
        setup_api_routes(self._router, self.stock_service)
        logger.info("✅ Stocks API routes registered (including predictions)")
        
        @self._router.get("/", response_class=HTMLResponse)
        async def stocks_page(request: Request):
            """Render the stocks tracking page"""
            logger.info("=" * 80)
            logger.info("STOCKS PAGE ACCESSED!")
            logger.info(f"Request path: {request.url.path}")
            logger.info(f"User: {getattr(request.state, 'username', 'Unknown')}")
            logger.info(f"Templates object exists: {self.templates is not None}")
            logger.info("=" * 80)
            
            try:
                # Default showcase symbols
                showcase_symbols = [
                    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
                    "META", "TSLA", "SPY"
                ]
                
                logger.info(f"SUCCESS About to render template with {len(showcase_symbols)} symbols")
                response = self.templates.TemplateResponse("stocks.html", {
                    "request": request,
                    "showcase_symbols": showcase_symbols,
                    "current_user": {
                        "username": getattr(request.state, "username", "guest"),
                        "is_admin": getattr(request.state, "is_admin", False)
                    }
                })
                logger.info("SUCCESS Template rendered successfully!")
                return response
            except Exception as e:
                logger.error(f"ERROR rendering stocks page: {e}", exc_info=True)
                raise
        
        @self._router.get("/status")
        async def get_status():
            """Get stock plugin status"""
            logger.info("Stock status requested")
            return {
                "status": "success",
                "data": {
                    "plugin": "stocks",
                    "version": "1.0.0",
                    "polling_active": self.polling_task is not None and not self.polling_task.done() if self.polling_task else False,
                    "message": "Stock plugin is running (services not yet implemented)"
                }
            }
        
        @self._router.get("/service-status")
        async def get_service_status():
            """Get stock service status with detailed info"""
            logger.info("🔍 Service status requested")
            return {
                "status": "success",
                "data": {
                    "service_running": self._service_running,
                    "polling_active": self.polling_task is not None and not self.polling_task.done() if self.polling_task else False,
                    "has_api_keys": bool(os.getenv('FINNHUB_TOKEN') or os.getenv('ALPHA_VANTAGE_KEY')),
                    "poll_seconds": int(os.getenv('POLL_SECONDS', '60')),
                    "showcase_refresh": int(os.getenv('SHOWCASE_REFRESH', '300')),
                }
            }
        
        @self._router.post("/service-control")
        async def service_control(action: dict):
            """Control the stock service (start/stop/restart)"""
            action_type = action.get("action", "").lower()
            logger.info(f"🎮 Service control: {action_type}")
            self._add_service_log("INFO", f"🎮 Service control: {action_type}")
            
            try:
                if action_type == "start":
                    if self._service_running:
                        return {"status": "error", "message": "Service already running"}
                    await self.start_services()
                    return {"status": "success", "message": "Stock service started"}
                
                elif action_type == "stop":
                    if not self._service_running:
                        return {"status": "error", "message": "Service not running"}
                    await self.stop_services()
                    return {"status": "success", "message": "Stock service stopped"}
                
                elif action_type == "restart":
                    if self._service_running:
                        await self.stop_services()
                    await self.start_services()
                    return {"status": "success", "message": "Stock service restarted"}
                
                else:
                    return {"status": "error", "message": f"Unknown action: {action_type}"}
                    
            except Exception as e:
                logger.error(f"❌ Service control error: {e}", exc_info=True)
                self._add_service_log("ERROR", f"❌ Service control error: {e}")
                return {"status": "error", "message": str(e)}
        
        @self._router.get("/service-logs")
        async def get_service_logs(limit: int = 50):
            """Get recent service logs"""
            logger.info(f"📋 Service logs requested (limit={limit})")
            
            # Return the most recent N logs
            recent_logs = self._service_logs[-limit:] if limit > 0 else self._service_logs
            
            return {
                "status": "success",
                "logs": recent_logs,
                "total": len(self._service_logs)
            }
        
        @self._router.get("/info")
        async def get_info():
            """Get stock plugin information"""
            logger.info("ℹ️ Stock info requested")
            return {
                "status": "success",
                "data": {
                    "name": "Stocks Plugin",
                    "description": "Stock price tracking and alerting system",
                    "features": [
                        "Real-time price monitoring (coming soon)",
                        "Price alerts (coming soon)",
                        "Historical data (coming soon)",
                        "Portfolio tracking (coming soon)"
                    ],
                    "status": "in_development"
                }
            }
        
        @self._router.get("/showcase")
        async def get_showcase():
            """Get showcase stock quotes from database"""
            logger.info("=" * 80)
            logger.info("🌐 [ENDPOINT] /showcase called by frontend")
            logger.info("=" * 80)
            quotes = []
            
            try:
                # Use the stock_service method which already handles showcase data correctly
                logger.info("🔍 [ENDPOINT] Calling stock_service.get_showcase_data()...")
                quotes = await self.stock_service.get_showcase_data()
                logger.info(f"✅ [ENDPOINT] Retrieved {len(quotes)} showcase quotes")
                
                # Log each quote with ALL fields for debugging
                logger.info("📊 [ENDPOINT] DETAILED QUOTE DATA:")
                for i, quote in enumerate(quotes, 1):
                    logger.info(f"  Quote #{i}: {quote}")
                    
            except Exception as e:
                logger.error(f"❌ [ENDPOINT] Error fetching showcase quotes: {e}", exc_info=True)
            
            response = {
                "status": "success",
                "quotes": quotes
            }
            
            logger.info(f"📤 [ENDPOINT] Response structure:")
            logger.info(f"  - status: {response['status']}")
            logger.info(f"  - quotes count: {len(response['quotes'])}")
            logger.info(f"  - quotes type: {type(response['quotes'])}")
            if quotes:
                logger.info(f"  - First quote keys: {list(quotes[0].keys())}")
                logger.info(f"  - First quote: {quotes[0]}")
            logger.info("=" * 80)
            
            return response

        logger.info("✅ Stocks routes registered")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get plugin health status"""
        return {
            "status": "healthy",
            "message": "Stock plugin operational (core features in development)",
            "details": {
                "version": "1.0.0",
                "polling_active": False,
                "features_implemented": 0,
                "features_planned": 4
            }
        }
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """Return menu items for the web interface."""
        return [
            {
                "name": "Stocks",
                "url": "/stocks",
                "icon": "chart-line"
            },
            {
                "name": "Alerts",
                "url": "/stocks/alerts", 
                "icon": "bell"
            }
        ]
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets for the admin interface."""
        return [
            {
                "name": "Stock Overview",
                "type": "table",
                "endpoint": "/api/v1/plugins/stocks/showcase",
                "refresh_interval": 30
            },
            {
                "name": "Recent Alerts",
                "type": "list",
                "endpoint": "/api/v1/plugins/stocks/alerts/recent",
                "refresh_interval": 60
            }
        ]


# Plugin entry point
def get_plugin(config: PluginConfig) -> StocksPlugin:
    """Factory function to create plugin instance"""
    return StocksPlugin(config)

