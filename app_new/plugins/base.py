"""
Base plugin interface and abstract classes for the CameronPAD plugin system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from fastapi import APIRouter
from pydantic import BaseModel
import yaml


class PluginMetadata(BaseModel):
    """Plugin metadata model."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = []
    api_version: str = "1.0"
    enabled: bool = True
    priority: int = 100  # Lower numbers load first
    requires_auth: bool = True  # Whether plugin requires authentication
    icon: str = "🔌"  # Icon emoji for the plugin
    display_name: Optional[str] = None  # Display name (defaults to name.title())


class PluginConfig(BaseModel):
    """Base plugin configuration model."""
    enabled: bool = True
    settings: Dict[str, Any] = {}


class BasePlugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.metadata = self.get_metadata()
        self._router: Optional[APIRouter] = None
        self._initialized = False
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin. Called once during app startup."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup plugin resources. Called during app shutdown."""
        pass
    
    def get_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this plugin."""
        return self._router
    
    def get_static_path(self) -> Optional[str]:
        """Return path to static files for this plugin."""
        return None
    
    def get_template_path(self) -> Optional[str]:
        """Return path to Jinja2 templates for this plugin."""
        return None
    
    def get_migrations_path(self) -> Optional[str]:
        """Return path to database migrations for this plugin."""
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Return plugin health status."""
        return {
            "name": self.metadata.name,
            "status": "healthy" if self._initialized else "not_initialized",
            "version": self.metadata.version
        }
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.config.enabled and self.metadata.enabled


class WebPlugin(BasePlugin):
    """Base class for plugins that provide web interfaces."""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self._router = APIRouter()
    
    @abstractmethod
    def register_routes(self) -> None:
        """Register web routes for this plugin."""
        pass
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """Return menu items for the web interface."""
        return []
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets for the admin interface."""
        return []


class ServicePlugin(BasePlugin):
    """Base class for background service plugins."""
    
    @abstractmethod
    async def start_services(self) -> None:
        """Start background services."""
        pass
    
    @abstractmethod
    async def stop_services(self) -> None:
        """Stop background services."""
        pass


class DataPlugin(BasePlugin):
    """Base class for plugins that manage data."""
    
    @abstractmethod
    def get_models(self) -> List[Type]:
        """Return SQLAlchemy models for this plugin."""
        pass
    
    @abstractmethod
    async def create_tables(self) -> None:
        """Create database tables for this plugin."""
        pass
    
    @abstractmethod
    async def migrate_data(self) -> None:
        """Perform data migrations."""
        pass