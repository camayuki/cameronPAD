"""
Main FastAPI application with plugin system integration.
"""
import asyncio
import logging
import os
import psutil
from contextlib import asynccontextmanager
from pathlib import Path

# Load environment variables from .env file FIRST - before any other imports that use os.getenv()
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse

from .core.config import get_config
from .core.database import initialize_database, get_migration_manager
from .plugins.manager import PluginManager
from .plugins.registry import PluginRegistry
from .api.router import create_api_router
from .api.middleware import setup_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global instances
plugin_manager: PluginManager = None
plugin_registry: PluginRegistry = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global plugin_manager, plugin_registry
    
    # Startup
    logger.info("Starting CameronPAD application...")
    
    try:
        # Load configuration
        config = get_config()
        logger.info(f"Loaded configuration for environment: {config.environment}")
        
        # Initialize database
        initialize_database(config.database.url)
        
        # Initialize plugin system
        plugin_manager = PluginManager(
            plugins_dir=config.plugins.plugins_dir,
            config_dir=config.plugins.config_dir
        )
        plugin_registry = PluginRegistry()
        
        # Load plugins
        if config.plugins.auto_load:
            await plugin_manager.load_all_plugins()
            
            # Register plugins with registry
            for plugin_name, plugin in plugin_manager.get_all_plugins().items():
                plugin_registry.register(plugin)
            
            # Run plugin migrations
            migration_manager = get_migration_manager()
            for plugin_name, plugin in plugin_manager.get_enabled_plugins().items():
                migrations_path = plugin.get_migrations_path()
                if migrations_path:
                    migration_manager.run_plugin_migrations(plugin_name, migrations_path)
        
        # Store instances in app state
        app.state.plugin_manager = plugin_manager
        app.state.plugin_registry = plugin_registry
        app.state.config = config
        
        logger.info("Application startup completed")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down CameronPAD application...")
    
    try:
        if plugin_manager:
            await plugin_manager.shutdown_all_plugins()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = get_config()
    
    # Create FastAPI app
    app = FastAPI(
        title=config.api.title,
        description=config.api.description,
        version=config.api.version,
        docs_url=config.api.docs_url if config.api.enable_docs else None,
        redoc_url=config.api.redoc_url if config.api.enable_docs else None,
        openapi_url=config.api.openapi_url if config.api.enable_docs else None,
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app, config)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for production
    if config.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with actual allowed hosts
        )
    
    # Setup static files
    setup_static_files(app)
    
    # Setup templates
    setup_templates(app)
    
    # Include API router
    api_router = create_api_router()
    app.include_router(api_router)
    
    # Setup routes
    setup_routes(app)
    
    return app


def setup_static_files(app: FastAPI) -> None:
    """Setup static file serving."""
    static_dir = Path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Mount upload directory
    config = get_config()
    upload_dir = Path(config.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


def setup_templates(app: FastAPI) -> None:
    """Setup Jinja2 templates."""
    templates_dir = Path("templates")
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
    else:
        # Fallback to app_new/templates
        templates_dir = Path("app_new/templates")
        if templates_dir.exists():
            templates = Jinja2Templates(directory=str(templates_dir))
        else:
            return
    
    # Add global template functions
    def get_theme_css(theme_vars):
        """Convert theme variables dict to CSS"""
        if not theme_vars:
            return ""
        return "\n".join([f"    {k}: {v};" for k, v in theme_vars.items()])
    
    templates.env.globals['get_theme_css'] = get_theme_css
    app.state.templates = templates


def setup_routes(app: FastAPI) -> None:
    """Setup application routes."""
    
    @app.get("/")
    async def root():
        """Root endpoint - redirect to main interface."""
        return RedirectResponse(url="/app")
    
    @app.get("/app")
    async def main_app(request: Request):
        """Main application interface."""
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            # Get enabled plugins for the interface
            plugin_manager = getattr(request.app.state, 'plugin_manager', None)
            enabled_plugins = []
            
            if plugin_manager:
                for plugin_name, plugin in plugin_manager.get_enabled_plugins().items():
                    if hasattr(plugin, 'get_menu_items'):
                        menu_items = plugin.get_menu_items()
                        if menu_items:
                            enabled_plugins.append({
                                'name': plugin_name,
                                'metadata': plugin.metadata,
                                'menu_items': menu_items
                            })
            
            # Get some basic stats for the dashboard
            # Calculate application memory usage
            try:
                process = psutil.Process(os.getpid())
                app_memory_mb = process.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
                app_memory_str = f"{app_memory_mb:.1f}MB"
            except Exception as e:
                logger.error(f"Error calculating app memory: {e}")
                app_memory_str = "N/A"
            
            stats = {
                "total_users": 1,  # TODO: Get from database
                "total_plugins": len(enabled_plugins),
                "active_plugins": len(enabled_plugins),
                "api_calls": 0,  # TODO: Track API calls
                "storage_used": app_memory_str,  # Application memory usage
                "active_sessions": 1
            }
            
            # Get current user info from request state (set by middleware)
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False)
            }
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "plugins": enabled_plugins,
                "active_plugins": enabled_plugins,  # Same as enabled_plugins for now
                "stats": stats,
                "current_user": current_user
            })
        else:
            return {"message": "CameronPAD API", "plugins_loaded": len(getattr(request.app.state, 'plugin_manager', {}).get_all_plugins())}
    
    @app.get("/health")
    async def health_check(request: Request):
        """Health check endpoint."""
        plugin_manager = getattr(request.app.state, 'plugin_manager', None)
        plugin_health = []
        
        if plugin_manager:
            for plugin_name, plugin in plugin_manager.get_enabled_plugins().items():
                health = await plugin.health_check()
                plugin_health.append(health)
        
        return {
            "status": "healthy",
            "plugins": plugin_health
        }
    
    @app.get("/plugins")
    async def plugins_page(request: Request):
        """Plugin management page."""
        logger.info(f"📦 Plugins page accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            plugin_manager = getattr(request.app.state, 'plugin_manager', None)
            all_plugins = []
            
            if plugin_manager:
                for plugin_name, plugin in plugin_manager.get_all_plugins().items():
                    all_plugins.append({
                        'name': plugin_name,
                        'metadata': plugin.metadata,
                        'enabled': plugin_name in plugin_manager.get_enabled_plugins()
                    })
            
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False)
            }
            
            return templates.TemplateResponse("plugins.html", {
                "request": request,
                "plugins": all_plugins,
                "current_user": current_user
            })
        else:
            return {"message": "Plugins page", "plugins": []}
    
    @app.get("/apps")
    async def apps_page(request: Request):
        """Applications listing page - shows all enabled plugins."""
        logger.info(f"📱 Apps page accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            plugin_manager = getattr(request.app.state, 'plugin_manager', None)
            enabled_plugins = []
            
            if plugin_manager:
                for plugin_name, plugin in plugin_manager.get_enabled_plugins().items():
                    enabled_plugins.append({
                        'name': plugin_name,
                        'metadata': plugin.metadata,
                        'enabled': True
                    })
            
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False)
            }
            
            return templates.TemplateResponse("apps.html", {
                "request": request,
                "plugins": enabled_plugins,
                "current_user": current_user
            })
        else:
            return {"message": "Apps page", "apps": []}
    
    @app.get("/plugins/{plugin_name}")
    async def plugin_detail_page(request: Request, plugin_name: str):
        """Plugin detail and control page."""
        logger.info(f"🔍 Plugin detail page for '{plugin_name}' accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            plugin_manager = getattr(request.app.state, 'plugin_manager', None)
            plugin = None
            
            if plugin_manager:
                plugin = plugin_manager.get_plugin(plugin_name)
            
            if not plugin:
                return RedirectResponse(url="/plugins")
            
            # Get plugin health status
            health = await plugin.health_check()
            
            # Get plugin routes
            router = plugin.get_router()
            routes = []
            if router:
                for route in router.routes:
                    routes.append({
                        'path': f"/api/v1/plugins/{plugin_name}{route.path}",
                        'methods': list(route.methods) if hasattr(route, 'methods') else ['GET'],
                        'name': route.name if hasattr(route, 'name') else 'unnamed'
                    })
            
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False)
            }
            
            return templates.TemplateResponse("plugin_detail.html", {
                "request": request,
                "plugin": plugin,
                "plugin_name": plugin_name,
                "health": health,
                "routes": routes,
                "current_user": current_user
            })
        else:
            return {"message": f"Plugin: {plugin_name}", "status": "active"}
    
    @app.post("/plugins/{plugin_name}/disable")
    async def disable_plugin(request: Request, plugin_name: str):
        """Disable a plugin."""
        logger.info(f"⏸️ Disabling plugin '{plugin_name}' by user: {getattr(request.state, 'username', 'Unknown')}")
        plugin_manager = getattr(request.app.state, 'plugin_manager', None)
        if plugin_manager:
            await plugin_manager.unload_plugin(plugin_name)
            logger.info(f"✅ Plugin '{plugin_name}' disabled")
        return RedirectResponse(url=f"/plugins/{plugin_name}", status_code=303)
    
    @app.get("/settings")
    async def settings_page(request: Request):
        """User settings page."""
        logger.info(f"⚙️ Settings page accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False)
            }
            
            # Get theme information
            from .core.themes import get_theme_manager
            theme_manager = get_theme_manager()
            all_themes = theme_manager.get_all_themes()
            user_id = current_user.get("id")
            current_theme = theme_manager.get_user_theme(user_id) if user_id else {"theme_id": "space"}
            
            return templates.TemplateResponse("settings.html", {
                "request": request,
                "current_user": current_user,
                "themes": all_themes,
                "current_theme": current_theme
            })
        else:
            return {"message": "Settings page"}
    
    @app.get("/profile")
    async def profile_page(request: Request):
        """User profile page."""
        logger.info(f"👤 Profile page accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            # Get user details from database
            from .core.auth import get_user_manager
            user_manager = get_user_manager()
            
            user_id = getattr(request.state, 'user_id', None)
            user_data = None
            if user_id:
                try:
                    user_data = user_manager.get_user_by_id(user_id)
                except:
                    pass
            
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False),
                "email": user_data.get('email', 'N/A') if user_data else 'N/A',
                "full_name": user_data.get('full_name', '') if user_data else '',
                "created_at": user_data.get('created_at', None) if user_data else None,
                "last_login": user_data.get('last_login', None) if user_data else None,
                "is_active": user_data.get('is_active', True) if user_data else True
            }
            
            return templates.TemplateResponse("profile.html", {
                "request": request,
                "current_user": current_user
            })
        else:
            return {"message": "Profile page"}
    
    @app.get("/services")
    async def services_page(request: Request):
        """Background services monitoring page."""
        logger.info(f"🔧 Services page accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            return templates.TemplateResponse("services.html", {
                "request": request
            })
        else:
            return {"message": "Services monitoring page"}
    
    @app.get("/admin")
    async def admin_page(request: Request):
        """Admin panel page."""
        logger.info(f"👥 Admin panel accessed by user: {getattr(request.state, 'username', 'Unknown')}")
        templates = getattr(request.app.state, 'templates', None)
        if templates:
            # Check if user is admin
            if not getattr(request.state, 'is_admin', False):
                logger.warning(f"⚠️ Non-admin user {getattr(request.state, 'username', 'Unknown')} attempted to access admin panel")
                return RedirectResponse(url="/app")
            
            current_user = {
                "id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', 'Unknown'),
                "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
                "is_admin": getattr(request.state, 'is_admin', False)
            }
            
            return templates.TemplateResponse("admin/admin_panel.html", {
                "request": request,
                "current_user": current_user
            })
        else:
            return {"message": "Admin panel"}
    
    @app.get("/docs/{filename:path}")
    async def serve_documentation(filename: str):
        """Serve markdown documentation files."""
        from fastapi.responses import FileResponse, PlainTextResponse
        import os
        
        # Security: prevent directory traversal
        filename = filename.replace("../", "").replace("..\\", "")
        
        # Try docs/ directory first
        docs_path = Path("docs") / filename
        if docs_path.exists() and docs_path.is_file():
            if filename.endswith('.md'):
                # Serve markdown as plain text so browser shows it
                with open(docs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return PlainTextResponse(content, media_type='text/markdown')
            return FileResponse(docs_path)
        
        # Try root directory for migration docs
        root_path = Path(filename)
        if root_path.exists() and root_path.is_file():
            if filename.endswith('.md'):
                with open(root_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return PlainTextResponse(content, media_type='text/markdown')
            return FileResponse(root_path)
        
        # File not found
        return {"error": "Documentation file not found", "file": filename}
    
    # Include auth router (no prefix, direct routes)
    from .api.auth import router as auth_router
    app.include_router(auth_router)
    
    # Include admin API router
    from .api.admin_new import router as admin_api_router
    app.include_router(admin_api_router)
    
    # Include theme management router
    from .api.themes import router as themes_router
    app.include_router(themes_router)
    
    # Include API router
    api_router = create_api_router()
    app.include_router(api_router, prefix="/api/v1")
    
    # Dynamic plugin route inclusion
    @app.middleware("http")
    async def include_plugin_routes(request: Request, call_next):
        """Middleware to dynamically include plugin routes."""
        # This runs after plugin loading, so we can include plugin routes
        plugin_manager = getattr(request.app.state, 'plugin_manager', None)
        
        if plugin_manager and not hasattr(app.state, 'plugin_routes_included'):
            for plugin_name, plugin in plugin_manager.get_enabled_plugins().items():
                router = plugin.get_router()
                if router:
                    app.include_router(router, prefix=f"/api/v1/plugins/{plugin_name}")
                    logger.info(f"Included routes for plugin: {plugin_name}")
            
            app.state.plugin_routes_included = True
        
        response = await call_next(request)
        return response


# Create the FastAPI app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    uvicorn.run(
        "app_new.main:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.logging.level.lower()
    )