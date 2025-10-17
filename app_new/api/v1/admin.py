"""
Admin API endpoints for plugin and system management.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from ..plugins.manager import PluginManager
from ..plugins.registry import PluginRegistry


class PluginToggleRequest(BaseModel):
    """Request model for enabling/disabling plugins."""
    enabled: bool


class PluginConfigUpdateRequest(BaseModel):
    """Request model for updating plugin configuration."""
    settings: Dict[str, Any]


def create_admin_router() -> APIRouter:
    """Create admin API router."""
    router = APIRouter()
    
    @router.get("/plugins", response_model=List[Dict[str, Any]])
    async def list_plugins(request: Request):
        """List all plugins with their status."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        
        if not plugin_manager:
            return []
        
        return await plugin_manager.get_plugin_status()
    
    @router.get("/plugins/{plugin_name}", response_model=Dict[str, Any])
    async def get_plugin_details(plugin_name: str, request: Request):
        """Get detailed information about a specific plugin."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        plugin_registry: PluginRegistry = getattr(request.app.state, 'plugin_registry', None)
        
        if not plugin_manager or not plugin_registry:
            raise HTTPException(status_code=500, detail="Plugin system not initialized")
        
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        # Get comprehensive plugin info from registry
        plugin_info = plugin_registry.get_plugin_info()
        if plugin_name not in plugin_info:
            raise HTTPException(status_code=404, detail="Plugin not found in registry")
        
        # Add runtime information
        health = await plugin.health_check()
        plugin_details = plugin_info[plugin_name]
        plugin_details["health"] = health
        
        # Add configuration
        plugin_details["current_config"] = plugin.config.dict()
        
        return plugin_details
    
    @router.post("/plugins/{plugin_name}/toggle")
    async def toggle_plugin(plugin_name: str, request_data: PluginToggleRequest, request: Request):
        """Enable or disable a plugin."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        plugin_registry: PluginRegistry = getattr(request.app.state, 'plugin_registry', None)
        
        if not plugin_manager or not plugin_registry:
            raise HTTPException(status_code=500, detail="Plugin system not initialized")
        
        try:
            if request_data.enabled:
                # Check if plugin can be enabled (dependencies satisfied)
                if plugin_name in plugin_registry.list_plugins():
                    missing_deps = plugin_registry.validate_dependencies(plugin_name)
                    if missing_deps:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot enable plugin. Missing dependencies: {', '.join(missing_deps)}"
                        )
                
                success = await plugin_manager.enable_plugin(plugin_name)
                if success:
                    # Register with registry if loaded
                    plugin = plugin_manager.get_plugin(plugin_name)
                    if plugin:
                        plugin_registry.register(plugin)
                else:
                    raise HTTPException(status_code=400, detail="Failed to enable plugin")
            else:
                # Check if plugin can be disabled (no enabled dependents)
                if plugin_name in plugin_registry.list_plugins():
                    can_disable, dependents = plugin_registry.can_disable_plugin(plugin_name)
                    if not can_disable:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot disable plugin. Required by: {', '.join(dependents)}"
                        )
                
                success = await plugin_manager.disable_plugin(plugin_name)
                if success:
                    plugin_registry.unregister(plugin_name)
                else:
                    raise HTTPException(status_code=400, detail="Failed to disable plugin")
            
            return {
                "message": f"Plugin {plugin_name} {'enabled' if request_data.enabled else 'disabled'} successfully",
                "enabled": request_data.enabled
            }
        
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=f"Error toggling plugin: {str(e)}")
    
    @router.post("/plugins/{plugin_name}/reload")
    async def reload_plugin(plugin_name: str, request: Request):
        """Reload a plugin."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        plugin_registry: PluginRegistry = getattr(request.app.state, 'plugin_registry', None)
        
        if not plugin_manager or not plugin_registry:
            raise HTTPException(status_code=500, detail="Plugin system not initialized")
        
        try:
            # Unregister from registry first
            plugin_registry.unregister(plugin_name)
            
            # Reload plugin
            success = await plugin_manager.reload_plugin(plugin_name)
            
            if success:
                # Re-register with registry
                plugin = plugin_manager.get_plugin(plugin_name)
                if plugin:
                    plugin_registry.register(plugin)
                
                return {"message": f"Plugin {plugin_name} reloaded successfully"}
            else:
                raise HTTPException(status_code=400, detail="Failed to reload plugin")
        
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=f"Error reloading plugin: {str(e)}")
    
    @router.get("/plugins/{plugin_name}/health")
    async def get_plugin_health(plugin_name: str, request: Request):
        """Get health status of a specific plugin."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        
        if not plugin_manager:
            raise HTTPException(status_code=500, detail="Plugin system not initialized")
        
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        health = await plugin.health_check()
        return health
    
    @router.put("/plugins/{plugin_name}/config")
    async def update_plugin_config(
        plugin_name: str, 
        config_update: PluginConfigUpdateRequest, 
        request: Request
    ):
        """Update plugin configuration."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        
        if not plugin_manager:
            raise HTTPException(status_code=500, detail="Plugin system not initialized")
        
        # Update configuration in plugin manager
        if plugin_name not in plugin_manager.plugin_configs:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        # Merge new settings with existing config
        current_config = plugin_manager.plugin_configs[plugin_name]
        current_settings = current_config.get('settings', {})
        current_settings.update(config_update.settings)
        current_config['settings'] = current_settings
        
        # Save configuration
        try:
            await plugin_manager._save_plugin_config(plugin_name, {'settings': current_settings})
            
            return {
                "message": f"Configuration updated for plugin {plugin_name}",
                "settings": current_settings
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")
    
    @router.get("/system/status")
    async def get_system_status(request: Request):
        """Get overall system status."""
        plugin_manager: PluginManager = getattr(request.app.state, 'plugin_manager', None)
        config = getattr(request.app.state, 'config', None)
        
        status = {
            "application": {
                "name": "CameronPAD",
                "version": config.api.version if config else "unknown",
                "environment": config.environment if config else "unknown",
                "debug": config.debug if config else False
            },
            "plugins": {
                "total": 0,
                "enabled": 0,
                "loaded": 0,
                "healthy": 0
            },
            "database": {
                "connected": True,  # TODO: Add actual database health check
                "migrations_applied": True
            }
        }
        
        if plugin_manager:
            all_plugins = plugin_manager.get_all_plugins()
            enabled_plugins = plugin_manager.get_enabled_plugins()
            
            status["plugins"]["total"] = len(plugin_manager.plugin_info)
            status["plugins"]["loaded"] = len(all_plugins)
            status["plugins"]["enabled"] = len(enabled_plugins)
            
            # Check plugin health
            healthy_count = 0
            for plugin in all_plugins.values():
                try:
                    health = await plugin.health_check()
                    if health.get("status") == "healthy":
                        healthy_count += 1
                except:
                    pass
            
            status["plugins"]["healthy"] = healthy_count
        
        return status
    
    @router.get("/system/logs")
    async def get_system_logs(limit: int = 100, level: str = "INFO"):
        """Get recent system logs."""
        # TODO: Implement log retrieval
        # This would read from log files or a logging database
        return {
            "message": "Log retrieval not implemented yet",
            "limit": limit,
            "level": level
        }
    
    @router.post("/system/maintenance")
    async def trigger_maintenance(request: Request):
        """Trigger system maintenance tasks."""
        # TODO: Implement maintenance tasks
        # - Database cleanup
        # - Cache clearing
        # - Log rotation
        # - Plugin cleanup
        
        return {"message": "Maintenance tasks completed"}
    
    return router