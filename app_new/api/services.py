"""
Services API endpoint - Monitor and manage background services.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..plugins.base import ServicePlugin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/services", tags=["services"])


class ServiceStatus(BaseModel):
    """Service status information."""
    name: str
    plugin: str
    status: str  # running, stopped, error
    uptime: str
    description: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class ServiceAction(BaseModel):
    """Service action request."""
    action: str  # start, stop, restart


@router.get("/status")
async def get_all_services(request: Request) -> Dict[str, Any]:
    """Get status of all background services."""
    try:
        plugin_manager = request.app.state.plugin_manager
        services = []
        
        # Get all plugins
        all_plugins = plugin_manager.get_all_plugins()
        logger.info(f"🔍 Checking {len(all_plugins)} plugins for services...")
        
        for plugin_name, plugin in all_plugins.items():
            # Check if plugin has background services
            has_start_stop = hasattr(plugin, "start_services") and hasattr(plugin, "stop_services")
            has_scheduler = hasattr(plugin, "scheduler")
            has_polling = hasattr(plugin, "polling_task")
            has_service_flag = hasattr(plugin, "_service_running")
            
            logger.debug(f"Plugin {plugin_name}: start_stop={has_start_stop}, scheduler={has_scheduler}, polling={has_polling}, flag={has_service_flag}")
            
            # Only include plugins that can run services
            if has_start_stop or has_scheduler or has_polling or isinstance(plugin, ServicePlugin):
                # Determine status
                service_status = "stopped"
                
                # Check status flags in order of preference
                if has_service_flag:
                    service_status = "running" if getattr(plugin, "_service_running", False) else "stopped"
                elif has_scheduler:
                    scheduler = getattr(plugin, "scheduler", None)
                    service_status = "running" if (scheduler and getattr(scheduler, "running", False)) else "stopped"
                elif has_polling:
                    task = getattr(plugin, "polling_task", None)
                    service_status = "running" if (task and not task.done()) else "stopped"
                
                # Get plugin metadata if available
                metadata = getattr(plugin, "metadata", None)
                description = f"Background services for {plugin_name}"
                if metadata:
                    description = getattr(metadata, "description", description)
                
                logger.info(f"✅ Found service: {plugin_name} (status={service_status}, has_start_stop={has_start_stop})")
                
                services.append({
                    "name": plugin_name.title() + " Service",
                    "plugin": plugin_name,
                    "status": service_status,
                    "enabled": True,  # If loaded, it's enabled
                    "description": description,
                    "has_scheduler": has_scheduler,
                    "has_start_stop": has_start_stop,
                    "type": "scheduler" if has_scheduler else "background_task"
                })
        
        return {
            "services": services,
            "total": len(services),
            "running": sum(1 for s in services if s["status"] == "running"),
            "stopped": sum(1 for s in services if s["status"] == "stopped"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}/status")
async def get_service_status(plugin_name: str, request: Request) -> ServiceStatus:
    """Get status of a specific service."""
    try:
        plugin_manager = request.app.state.plugin_manager
        plugin = plugin_manager.get_plugin(plugin_name)
        
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
        
        # Check if it's a service plugin
        is_service = isinstance(plugin, ServicePlugin) or hasattr(plugin, "scheduler") or hasattr(plugin, "polling_task")
        
        if not is_service:
            raise HTTPException(status_code=400, detail=f"Plugin {plugin_name} has no background services")
        
        # Determine status
        status = "unknown"
        if hasattr(plugin, "scheduler"):
            scheduler = getattr(plugin, "scheduler")
            status = "running" if (scheduler and getattr(scheduler, "running", False)) else "stopped"
        elif hasattr(plugin, "polling_task"):
            task = getattr(plugin, "polling_task")
            status = "running" if (task and not task.done()) else "stopped"
        
        return ServiceStatus(
            name=f"{plugin_name.title()} Service",
            plugin=plugin_name,
            status=status,
            uptime="N/A",  # TODO: Track actual uptime
            description=f"Background services for {plugin_name} plugin"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service status for {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_name}/action")
async def control_service(plugin_name: str, action: ServiceAction, request: Request) -> Dict[str, Any]:
    """Control a background service (start/stop/restart)."""
    try:
        plugin_manager = request.app.state.plugin_manager
        plugin = plugin_manager.get_plugin(plugin_name)
        
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
        
        # Check if plugin has start/stop methods
        has_start_stop = hasattr(plugin, "start_services") and hasattr(plugin, "stop_services")
        
        if not has_start_stop:
            raise HTTPException(
                status_code=400, 
                detail=f"Plugin {plugin_name} does not support start/stop control"
            )
        
        # Execute action
        if action.action == "start":
            await plugin.start_services()
            logger.info(f"✅ Started {plugin_name} service")
            return {"status": "success", "message": f"Started {plugin_name} service"}
        
        elif action.action == "stop":
            await plugin.stop_services()
            logger.info(f"⏹️ Stopped {plugin_name} service")
            return {"status": "success", "message": f"Stopped {plugin_name} service"}
        
        elif action.action == "restart":
            await plugin.stop_services()
            await plugin.start_services()
            logger.info(f"🔄 Restarted {plugin_name} service")
            return {"status": "success", "message": f"Restarted {plugin_name} service"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error controlling service {plugin_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
