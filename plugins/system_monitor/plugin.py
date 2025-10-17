"""
System Monitor Plugin - Provides real-time system resource monitoring
"""
import logging
import psutil
import platform
from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter
from app_new.plugins.base import WebPlugin, PluginMetadata, PluginConfig

logger = logging.getLogger(__name__)


class SystemMonitorPlugin(WebPlugin):
    """Plugin for monitoring system resources and performance"""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.start_time = datetime.now()
        self.request_count = 0
        logger.info("🖥️ Initializing System Monitor plugin...")
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata"""
        return PluginMetadata(
            name="system_monitor",
            version="1.0.0",
            description="Real-time system monitoring and resource tracking",
            author="CameronPAD Team",
            dependencies=["psutil"],
            api_version="1.0",
            enabled=True,
            priority=90
        )
        
    async def initialize(self) -> None:
        """Initialize the plugin"""
        try:
            # Test psutil access
            psutil.cpu_percent(interval=0.1)
            psutil.virtual_memory()
            psutil.disk_usage('/')
            
            # Register routes
            self.register_routes()
            
            logger.info("✅ System Monitor plugin initialized successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize System Monitor: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Cleanup on shutdown"""
        logger.info("🛑 System Monitor plugin shutting down...")
    
    def register_routes(self) -> None:
        """Register API routes"""
        router = self._router
        
        @router.get("/info")
        async def get_system_info():
            """Get basic system information"""
            self.request_count += 1
            logger.info("📊 System info requested")
            
            return {
                "status": "success",
                "data": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                    "hostname": platform.node()
                }
            }
        
        @router.get("/cpu")
        async def get_cpu_usage():
            """Get CPU usage statistics"""
            self.request_count += 1
            logger.info("💻 CPU usage requested")
            
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            return {
                "status": "success",
                "data": {
                    "total_usage": psutil.cpu_percent(interval=0.1),
                    "per_cpu": cpu_percent,
                    "cpu_count": psutil.cpu_count(),
                    "cpu_count_logical": psutil.cpu_count(logical=True),
                    "frequency": {
                        "current": cpu_freq.current if cpu_freq else None,
                        "min": cpu_freq.min if cpu_freq else None,
                        "max": cpu_freq.max if cpu_freq else None
                    }
                }
            }
        
        @router.get("/memory")
        async def get_memory_usage():
            """Get memory usage statistics"""
            self.request_count += 1
            logger.info("🧠 Memory usage requested")
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "status": "success",
                "data": {
                    "virtual": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "free": memory.free,
                        "percent": memory.percent,
                        "total_gb": round(memory.total / (1024**3), 2),
                        "used_gb": round(memory.used / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2)
                    },
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent,
                        "total_gb": round(swap.total / (1024**3), 2),
                        "used_gb": round(swap.used / (1024**3), 2)
                    }
                }
            }
        
        @router.get("/disk")
        async def get_disk_usage():
            """Get disk usage statistics"""
            self.request_count += 1
            logger.info("💾 Disk usage requested")
            
            partitions = psutil.disk_partitions()
            disk_info = []
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2)
                    })
                except PermissionError:
                    continue
            
            return {
                "status": "success",
                "data": disk_info
            }
        
        @router.get("/network")
        async def get_network_stats():
            """Get network statistics"""
            self.request_count += 1
            logger.info("🌐 Network stats requested")
            
            net_io = psutil.net_io_counters()
            
            return {
                "status": "success",
                "data": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2)
                }
            }
        
        @router.get("/all")
        async def get_all_stats():
            """Get all system statistics in one call"""
            self.request_count += 1
            logger.info("📈 All system stats requested")
            
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            return {
                "status": "success",
                "data": {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": memory.percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "network_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "network_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
                }
            }
        
        @router.get("/metrics")
        async def get_metrics():
            """Get simplified metrics for dashboard (CPU, Memory, Disk)"""
            self.request_count += 1
            logger.info("📊 Dashboard metrics requested")
            
            try:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                return {
                    "cpu": cpu_percent,
                    "memory": memory.percent,
                    "disk": disk.percent
                }
            except Exception as e:
                logger.error(f"❌ Error fetching metrics: {e}")
                return {
                    "cpu": 0,
                    "memory": 0,
                    "disk": 0,
                    "error": str(e)
                }
        
        @router.get("/stats")
        async def get_plugin_stats():
            """Get plugin statistics"""
            logger.info("📊 Plugin stats requested")
            
            uptime = datetime.now() - self.start_time
            
            return {
                "status": "success",
                "data": {
                    "plugin_uptime": str(uptime),
                    "requests_handled": self.request_count,
                    "requests_per_minute": round(self.request_count / (uptime.total_seconds() / 60), 2) if uptime.total_seconds() > 0 else 0
                }
            }
        
        logger.info("✅ System Monitor routes registered")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get plugin health status"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Determine health based on system resources
            if cpu > 90 or memory.percent > 90:
                status = "warning"
                message = "High system resource usage detected"
            else:
                status = "healthy"
                message = "System resources normal"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "cpu_usage": f"{cpu}%",
                    "memory_usage": f"{memory.percent}%",
                    "requests_handled": self.request_count
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """Get menu items for the plugin"""
        return [
            {"label": "System Overview", "action": "view_overview"},
            {"label": "CPU Monitor", "action": "view_cpu"},
            {"label": "Memory Monitor", "action": "view_memory"},
            {"label": "Disk Monitor", "action": "view_disk"}
        ]
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Get dashboard widgets"""
        return [
            {
                "type": "stat",
                "title": "System Monitor",
                "value": "Active",
                "icon": "📊"
            }
        ]


# Plugin entry point
def get_plugin(config: PluginConfig) -> SystemMonitorPlugin:
    """Factory function to create plugin instance"""
    return SystemMonitorPlugin(config)
