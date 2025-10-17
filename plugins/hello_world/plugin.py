"""
Hello World Plugin - Example plugin for CameronPAD.
"""
import logging
from typing import Dict, Any, List
from pathlib import Path

from app_new.plugins.base import WebPlugin, PluginMetadata, PluginConfig

logger = logging.getLogger(__name__)


class HelloWorldPlugin(WebPlugin):
    """
    A simple example plugin that demonstrates basic plugin functionality.
    
    This plugin provides:
    - A simple API endpoint
    - Menu items for the web interface
    - Dashboard widgets
    """
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.greeting_count = 0
        
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="hello_world",
            version="1.0.0",
            description="A simple example plugin that says hello",
            author="CameronPAD Team",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    async def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("🌍 Initializing Hello World plugin...")
        
        # Register API routes
        self.register_routes()
        
        self._initialized = True
        logger.info("✅ Hello World plugin initialized successfully!")
    
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        logger.info("👋 Shutting down Hello World plugin...")
        self._initialized = False
    
    def register_routes(self) -> None:
        """Register web routes for this plugin."""
        from fastapi import Request
        from fastapi.responses import JSONResponse
        
        @self._router.get("/hello")
        async def hello_endpoint(name: str = "World"):
            """Say hello to someone."""
            self.greeting_count += 1
            logger.info(f"👋 Greeting #{self.greeting_count}: Hello, {name}!")
            return JSONResponse({
                "message": f"Hello, {name}!",
                "greeting_number": self.greeting_count,
                "plugin": "hello_world",
                "version": self.metadata.version
            })
        
        @self._router.get("/status")
        async def status_endpoint():
            """Get plugin status."""
            return JSONResponse({
                "plugin": "hello_world",
                "version": self.metadata.version,
                "status": "running",
                "greetings_sent": self.greeting_count,
                "enabled": self.is_enabled()
            })
        
        @self._router.post("/reset")
        async def reset_counter():
            """Reset the greeting counter."""
            old_count = self.greeting_count
            self.greeting_count = 0
            logger.info(f"🔄 Reset greeting counter from {old_count} to 0")
            return JSONResponse({
                "message": "Counter reset",
                "previous_count": old_count,
                "current_count": self.greeting_count
            })
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """Return menu items for the web interface."""
        return [
            {
                "title": "Hello World",
                "url": "/api/v1/plugins/hello_world/hello",
                "icon": "👋",
                "description": "Try the Hello World plugin"
            }
        ]
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets."""
        return [
            {
                "title": "Hello World Status",
                "type": "info",
                "content": f"Greetings sent: {self.greeting_count}",
                "icon": "🌍"
            }
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Return plugin health status."""
        health = await super().health_check()
        health["greetings_sent"] = self.greeting_count
        health["custom_message"] = "Hello from health check!"
        return health


# Plugin factory function (required)
def create_plugin(config: PluginConfig) -> HelloWorldPlugin:
    """Create and return a plugin instance."""
    return HelloWorldPlugin(config)
