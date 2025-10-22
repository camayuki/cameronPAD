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
            priority=100,
            requires_auth=False  # Hello World plugin is public
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
        from fastapi.responses import JSONResponse, HTMLResponse
        
        @self._router.get("/", response_class=HTMLResponse)
        @self._router.get("", response_class=HTMLResponse)
        async def hello_page(request: Request):
            """Hello World main page."""
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Hello World Plugin</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background: #1a1a1a;
                        color: #e0e0e0;
                    }}
                    .container {{
                        background: #2a2a2a;
                        border-radius: 10px;
                        padding: 30px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                    }}
                    h1 {{ color: #4CAF50; }}
                    button {{
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                        margin: 5px;
                    }}
                    button:hover {{ background: #45a049; }}
                    .reset {{ background: #f44336; }}
                    .reset:hover {{ background: #da190b; }}
                    #result {{
                        margin-top: 20px;
                        padding: 15px;
                        background: #333;
                        border-radius: 5px;
                        min-height: 50px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>👋 Hello World Plugin</h1>
                    <p>This is an example plugin demonstrating basic plugin functionality.</p>
                    <p>Greetings sent: <strong id="count">{self.greeting_count}</strong></p>
                    
                    <input type="text" id="name" placeholder="Enter your name" value="World" />
                    <button onclick="sayHello()">Say Hello!</button>
                    <button class="reset" onclick="resetCounter()">Reset Counter</button>
                    
                    <div id="result"></div>
                </div>
                
                <script>
                    async function sayHello() {{
                        const name = document.getElementById('name').value || 'World';
                        const response = await fetch(`/api/v1/plugins/hello_world/hello?name=${{encodeURIComponent(name)}}`);
                        const data = await response.json();
                        document.getElementById('result').innerHTML = `
                            <strong>${{data.message}}</strong><br>
                            Greeting #${{data.greeting_number}}<br>
                            Plugin version: ${{data.version}}
                        `;
                        document.getElementById('count').textContent = data.greeting_number;
                    }}
                    
                    async function resetCounter() {{
                        const response = await fetch('/api/v1/plugins/hello_world/reset', {{ method: 'POST' }});
                        const data = await response.json();
                        document.getElementById('result').innerHTML = `
                            <strong>${{data.message}}</strong><br>
                            Previous count: ${{data.previous_count}}<br>
                            Current count: ${{data.current_count}}
                        `;
                        document.getElementById('count').textContent = data.current_count;
                    }}
                </script>
            </body>
            </html>
            """)
        
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
