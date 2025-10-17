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
            priority=50
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
        
        # Register routes
        self.register_routes()
        
        # Initialize stock service with API keys from environment
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
        
        @self._router.get("/", response_class=HTMLResponse)
        async def stocks_page(request: Request):
            """Render the stocks tracking page"""
            logger.info("📈 Stocks page accessed")
            
            # Default showcase symbols
            showcase_symbols = [
                "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
                "META", "TSLA", "SPY"
            ]
            
            return self.templates.TemplateResponse("stocks.html", {
                "request": request,
                "showcase_symbols": showcase_symbols,
                "current_user": {
                    "username": getattr(request.state, "username", "guest"),
                    "is_admin": getattr(request.state, "is_admin", False)
                }
            })
        
        @self._router.get("/status")
        async def get_status():
            """Get stock plugin status"""
            logger.info("📊 Stock status requested")
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
            import sqlite3
            
            logger.info("🌐 [ENDPOINT] /showcase called by frontend - starting data retrieval")
            quotes = []
            
            try:
                logger.info("🔌 [ENDPOINT] Opening database connection...")
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    
                    # First, check how many stocks are in the database
                    cur.execute("SELECT COUNT(*) as count FROM stocks WHERE enabled = 1")
                    stock_count = cur.fetchone()['count']
                    logger.info(f"📊 [ENDPOINT] Database query: {stock_count} enabled stocks found")
                    
                    # Check how many have prices
                    cur.execute("SELECT COUNT(*) as count FROM latest_prices")
                    price_count = cur.fetchone()['count']
                    logger.info(f"📊 [ENDPOINT] Database query: {price_count} stocks with prices found")
                    
                    if price_count == 0:
                        logger.warning("⚠️ [ENDPOINT] WARNING: latest_prices table is EMPTY! Service may not be running.")
                    
                    logger.info("🔍 [ENDPOINT] Executing JOIN query to fetch showcase data...")
                    cur.execute("""
                        SELECT 
                            s.symbol, s.target, s.direction, s.enabled,
                            p.price, p.high, p.low, p.ts as price_ts,
                            pr.pred_next, pr.src_days, pr.ts as pred_ts
                        FROM stocks s
                        LEFT JOIN latest_prices p ON s.symbol = p.symbol
                        LEFT JOIN predictions pr ON s.symbol = pr.symbol
                        WHERE s.enabled = 1
                        ORDER BY s.symbol
                    """)
                    quotes = [dict(row) for row in cur.fetchall()]
                    logger.info(f"✅ [ENDPOINT] Query complete: {len(quotes)} quotes retrieved")
                    
                    # Log each quote for debugging
                    for quote in quotes:
                        has_price = quote.get('price') is not None
                        has_high = quote.get('high') is not None
                        has_low = quote.get('low') is not None
                        status = "✅ HAS DATA" if has_price else "❌ NO DATA"
                        logger.info(f"� [ENDPOINT] {quote['symbol']}: {status} | Price=${quote.get('price', '--')}, High=${quote.get('high', '--')}, Low=${quote.get('low', '--')}, Timestamp={quote.get('price_ts', 'None')}")
                    
            except Exception as e:
                logger.error(f"❌ [ENDPOINT] Database error while fetching showcase quotes: {e}", exc_info=True)
            
            logger.info(f"� [ENDPOINT] Sending response to frontend: status=success, {len(quotes)} quotes")
            logger.info(f"📤 [ENDPOINT] Response summary: {sum(1 for q in quotes if q.get('price') is not None)} with prices, {sum(1 for q in quotes if q.get('price') is None)} without prices")
            return {
                "status": "success",
                "quotes": quotes
            }
        
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

