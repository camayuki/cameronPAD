"""
Surf Plugin - Wave monitoring for surf spots
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


class SurfPlugin(WebPlugin):
    """Track wave conditions at your favorite surf spots"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.templates = None
        self.update_task: Optional[asyncio.Task] = None
        self._service_running = False
        
    async def initialize(self) -> None:
        """Initialize the Surf plugin"""
        logger.info("🏄 Initializing Surf plugin...")
        
        # Initialize database tables
        from .database import init_surf_db
        init_surf_db()
        
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
            """Convert theme variables dict to CSS"""
            if not theme_vars:
                return ""
            return "\n".join([f"    {k}: {v};" for k, v in theme_vars.items()])
        
        self.templates.env.globals['get_theme_css'] = get_theme_css
        
        # Register routes
        self.register_routes()
        
        # Start background surf updates
        await self.start_surf_updates()
        
        logger.info("✅ Surf plugin initialized successfully")
        
    async def start_surf_updates(self) -> None:
        """Start background surf condition updates."""
        if self._service_running:
            logger.warning("Surf updates already running")
            return
        
        logger.info("🌊 Starting surf update service...")
        
        # Skip initial update on startup - only update on scheduled intervals
        # try:
        #     from .services import update_all_spots
        #     update_all_spots()
        #     logger.info("✅ Initial surf update complete")
        # except Exception as e:
        #     logger.error(f"❌ Initial surf update failed: {e}")
        
        # Start background update loop
        async def update_loop():
            surf_refresh = int(os.getenv('SURF_REFRESH', '300'))  # 5 minutes default
            cycle_count = 0
            
            logger.info(f"🔄 Starting surf update loop (refresh={surf_refresh}s)")
            
            while True:
                try:
                    await asyncio.sleep(surf_refresh)
                    
                    cycle_count += 1
                    logger.info(f"🌊 Starting surf update cycle #{cycle_count}")
                    
                    from .services import update_all_spots
                    update_all_spots()
                    
                    logger.info(f"✅ Surf update cycle #{cycle_count} complete")
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Surf update loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in surf update loop: {e}", exc_info=True)
                    logger.info("⚠️ Continuing loop after error...")
        
        self.update_task = asyncio.create_task(update_loop())
        self._service_running = True
        logger.info("✅ Surf update service started")
    
    async def stop_surf_updates(self) -> None:
        """Stop background surf updates."""
        if not self._service_running:
            return
        
        logger.info("⏹️ Stopping surf update service...")
        
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        self._service_running = False
        logger.info("✅ Surf update service stopped")
    
    async def shutdown(self) -> None:
        """Clean shutdown"""
        logger.info("🛑 Surf plugin shutting down")
        await self.stop_surf_updates()
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="surf",
            version="1.0.0",
            description="Wave height, period, and direction monitoring for surf spots",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100,
            requires_auth=False  # Surf plugin is public
        )
    
    def register_routes(self) -> None:
        """Register FastAPI routes for Surf plugin"""
        
        @self._router.get("/")
        async def surf_home(request: Request):
            """Render surf spots page"""
            import sqlite3
            
            # Fetch surf spots with their latest cached data
            spots = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT 
                            s.id, s.name, s.lat, s.lon, s.provider,
                            c.height_m, c.period_s, c.direction_deg, c.ts
                        FROM surf_spots s
                        LEFT JOIN surf_cache c ON s.id = c.spot_id
                        ORDER BY s.id
                    """)
                    spots = [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Failed to fetch surf spots: {e}")
            
            refresh_minutes = self.config.settings.get("refresh_interval", 300) // 60
            
            return self.templates.TemplateResponse(
                "surf.html",
                {
                    "request": request,
                    "spots": spots,
                    "refresh_minutes": refresh_minutes,
                    "user": getattr(request.state, "user", None)
                }
            )
        
        @self._router.post("/add")
        async def add_spot(
            name: str = Form(...),
            lat: float = Form(...),
            lon: float = Form(...)
        ):
            """Add a new surf spot"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO surf_spots(name, lat, lon, provider) VALUES(?, ?, ?, 'open-meteo')",
                        (name.strip(), lat, lon)
                    )
                    conn.commit()
                    logger.info(f"🏄 Added surf spot: {name} ({lat}, {lon})")
            except Exception as e:
                logger.error(f"Failed to add surf spot: {e}")
            
            return RedirectResponse("/api/v1/plugins/surf/", status_code=303)
        
        @self._router.post("/delete")
        async def delete_spot(spot_id: int = Form(...)):
            """Delete a surf spot"""
            import sqlite3
            
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM surf_spots WHERE id = ?", (spot_id,))
                    conn.commit()
                    logger.info(f"🗑️ Deleted surf spot ID: {spot_id}")
            except Exception as e:
                logger.error(f"Failed to delete surf spot: {e}")
            
            return RedirectResponse("/api/v1/plugins/surf/", status_code=303)
        
        @self._router.get("/data")
        async def get_surf_data():
            """Get current surf conditions for all spots"""
            import sqlite3
            
            spots = []
            try:
                with sqlite3.connect("data/cameronpad_dev.db") as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT 
                            s.id, s.name, s.lat, s.lon,
                            c.height_m, c.period_s, c.direction_deg, c.ts
                        FROM surf_spots s
                        LEFT JOIN surf_cache c ON s.id = c.spot_id
                        ORDER BY s.id
                    """)
                    spots = [dict(row) for row in cur.fetchall()]
            except Exception as e:
                logger.error(f"Failed to fetch surf data: {e}")
            
            return {"spots": spots}
        
        @self._router.post("/refresh")
        async def refresh_surf_data():
            """Manually refresh wave data for all spots"""
            from .services import update_all_spots
            
            try:
                update_all_spots()
                return {"status": "success", "message": "Surf data refreshed"}
            except Exception as e:
                logger.error(f"Failed to refresh surf data: {e}")
                return {"status": "error", "message": str(e)}
        
        @self._router.get("/status")
        async def status():
            """Get plugin status"""
            return {"status": "active", "plugin": "surf"}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return health status"""
        return {
            "status": "healthy",
            "plugin": "surf",
            "version": self.config.version
        }
    
    def get_menu_items(self) -> list:
        """Return menu items for this plugin"""
        return [
            {
                "label": "Surf",
                "icon": "🏄",
                "url": "/api/v1/plugins/surf/",
                "order": 40
            }
        ]


def get_plugin(config: PluginConfig) -> SurfPlugin:
    """Factory function to create plugin instance"""
    return SurfPlugin(config)
