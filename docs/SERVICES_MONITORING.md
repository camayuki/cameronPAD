# Services Monitoring Feature

**Created:** October 16, 2025  
**Status:** ✅ Implemented

## What Are Services in CameronPAD?

### The Architecture

CameronPAD has a **plugin-based architecture** with three types of plugins:

1. **WebPlugin** 🌐
   - Plugins that provide user interfaces
   - Examples: Notepad, Journal, Surf Browser
   - Have routes, templates, and UI components
   - Don't necessarily need background tasks

2. **ServicePlugin** ⚙️
   - Plugins that run background tasks
   - Examples: Stock price updater, data sync services
   - Run periodic jobs (schedulers)
   - May or may not have a UI

3. **Hybrid Plugins** 🔄
   - Plugins that are BOTH WebPlugin AND ServicePlugin
   - Examples: Stocks (has UI + background price fetching)
   - Most powerful and flexible type

### Services vs Apps

**Apps** = The visible plugin interfaces users interact with  
**Services** = Background tasks that run automatically

**Example:** The Stocks plugin
- **App side**: Shows stock prices, charts, alerts (UI)
- **Service side**: Fetches prices every 5 minutes, checks alerts every 60 seconds (Background)

## What Was Built

### 1. Services API (`app_new/api/services.py`)

**Endpoints:**

#### GET `/api/services/status`
Returns all background services and their status.

**Response:**
```json
{
  "services": [
    {
      "name": "Stocks Service",
      "plugin": "stocks",
      "status": "running",
      "enabled": true,
      "description": "Background services for stocks",
      "type": "scheduler"
    }
  ],
  "total": 1,
  "running": 1,
  "stopped": 0,
  "timestamp": "2025-10-16T14:30:00"
}
```

**Status values:**
- `running` - Service is actively running
- `stopped` - Service is not running
- `unknown` - Can't determine status

#### GET `/api/services/{plugin_name}/status`
Get detailed status of a specific service.

**Example:** `GET /api/services/stocks/status`

**Response:**
```json
{
  "name": "Stocks Service",
  "plugin": "stocks",
  "status": "running",
  "uptime": "N/A",
  "description": "Background services for stocks plugin"
}
```

#### POST `/api/services/{plugin_name}/action`
Control a service (start/stop/restart).

**Request Body:**
```json
{
  "action": "start"  // or "stop" or "restart"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Started stocks service"
}
```

### 2. Services UI Page (`templates/services.html`)

Beautiful monitoring dashboard showing:

**Stats Cards:**
- 📊 Total Services
- ✅ Running Services
- ❌ Stopped Services

**Service Cards:**
Each service shows:
- Service name and status indicator (pulsing dot)
- Status badge (running/stopped/unknown)
- Description
- Plugin name
- Service type (scheduler/service)
- Enabled status

**Control Buttons:**
- ▶️ Start - Start the service
- ⏹️ Stop - Stop the service
- 🔄 Restart - Restart the service

**Features:**
- Auto-refresh every 30 seconds
- Manual refresh button
- Real-time status updates
- Error handling with user-friendly messages
- Animated loading states

### 3. Settings Page Integration

Added **Quick Actions** section to Settings page with:
- 🧩 **Manage Plugins** - Configure installed plugins
- 🔧 **Services** - Monitor background services ← NEW!
- 👑 **Admin Panel** - System administration

## How It Works

### Service Detection

The system automatically detects services by checking if a plugin:

1. **Inherits from `ServicePlugin`**
   ```python
   class MyPlugin(ServicePlugin):
       async def start_services(self): ...
       async def stop_services(self): ...
   ```

2. **Has a `scheduler` attribute**
   ```python
   class MyPlugin(WebPlugin):
       def __init__(self):
           self.scheduler = BackgroundScheduler()
   ```

3. **Has a `polling_task` attribute**
   ```python
   class MyPlugin(WebPlugin):
       def __init__(self):
           self.polling_task: asyncio.Task = None
   ```

### Status Determination

**For schedulers:**
```python
if hasattr(plugin, "scheduler"):
    scheduler = getattr(plugin, "scheduler")
    status = "running" if (scheduler and scheduler.running) else "stopped"
```

**For async tasks:**
```python
if hasattr(plugin, "polling_task"):
    task = getattr(plugin, "polling_task")
    status = "running" if (task and not task.done()) else "stopped"
```

## Example: Stocks Service

The Stocks plugin will have background services like:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class StocksPlugin(WebPlugin):
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    async def initialize(self):
        # Start background tasks
        self.scheduler.add_job(
            self.check_alerts,
            'interval',
            seconds=60,
            id='check_alerts'
        )
        
        self.scheduler.add_job(
            self.update_prices,
            'interval',
            seconds=300,
            id='update_prices'
        )
        
        self.scheduler.start()
    
    async def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
    
    async def check_alerts(self):
        # Check stock price alerts
        pass
    
    async def update_prices(self):
        # Fetch latest stock prices
        pass
```

**In Services UI, this would show:**
```
┌─────────────────────────────────────────┐
│ 📈 Stocks Service                       │
│ ● RUNNING                               │
├─────────────────────────────────────────┤
│ Background services for stocks plugin   │
│                                         │
│ Plugin: stocks                          │
│ Type: scheduler                         │
│ Enabled: ✅ Yes                         │
├─────────────────────────────────────────┤
│ ▶️ Start  ⏹️ Stop  🔄 Restart          │
└─────────────────────────────────────────┘
```

## Using the Services Page

### Accessing

1. **From Dashboard:**
   - Click "Settings" in navbar
   - Click "Services" in Quick Actions

2. **Direct URL:**
   - Navigate to `/services`

### Viewing Services

The page automatically loads all services and shows:
- Real-time status with pulsing indicators
- Total count, running count, stopped count
- Each service's plugin name and type
- Whether services are enabled

### Controlling Services

Click the control buttons on any service card:

**Start:**
- Starts a stopped service
- Disabled if already running
- Calls `plugin.start_services()`

**Stop:**
- Stops a running service
- Disabled if already stopped
- Calls `plugin.stop_services()`

**Restart:**
- Stops then starts the service
- Only enabled for running services
- Useful for applying configuration changes

### Auto-Refresh

The page automatically refreshes every 30 seconds to show current status.

**Manual Refresh:**
Click the 🔄 Refresh button in the page header.

## Implementation Details

### API Integration

The Services API is registered in `app_new/api/router.py`:

```python
from .services import router as services_router

def create_api_router() -> APIRouter:
    api_router = APIRouter(prefix="/api")
    api_router.include_router(services_router, tags=["services"])
    return api_router
```

### Route Registration

The Services page route is in `app_new/main.py`:

```python
@app.get("/services")
async def services_page(request: Request):
    """Background services monitoring page."""
    templates = request.app.state.templates
    return templates.TemplateResponse("services.html", {
        "request": request
    })
```

### Security

Currently accessible to all logged-in users. Future enhancements:

```python
@app.get("/services")
async def services_page(request: Request):
    # TODO: Add admin-only check
    if not request.state.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    ...
```

## Future Enhancements

### 1. Service Logs
```python
@router.get("/{plugin_name}/logs")
async def get_service_logs(plugin_name: str):
    """Get recent logs from a service."""
    return {"logs": [...]}
```

### 2. Service Metrics
```python
@router.get("/{plugin_name}/metrics")
async def get_service_metrics(plugin_name: str):
    """Get performance metrics."""
    return {
        "uptime": 3600,
        "tasks_completed": 100,
        "errors": 2,
        "last_run": "2025-10-16T14:30:00"
    }
```

### 3. Scheduled Task Details
```python
@router.get("/{plugin_name}/schedule")
async def get_service_schedule(plugin_name: str):
    """Get scheduled tasks for a service."""
    return {
        "jobs": [
            {
                "id": "check_alerts",
                "trigger": "interval",
                "interval": 60,
                "next_run": "2025-10-16T14:31:00"
            }
        ]
    }
```

### 4. Service Configuration
```python
@router.put("/{plugin_name}/config")
async def update_service_config(plugin_name: str, config: dict):
    """Update service configuration."""
    return {"status": "success"}
```

### 5. Health Checks
```python
@router.get("/{plugin_name}/health")
async def check_service_health(plugin_name: str):
    """Check if service is healthy."""
    return {
        "healthy": True,
        "last_heartbeat": "2025-10-16T14:30:00",
        "checks": {
            "database": "ok",
            "api": "ok",
            "scheduler": "ok"
        }
    }
```

## Troubleshooting

### Service Not Showing Up

**Check if plugin has services:**
```python
# Plugin must have one of:
- isinstance(plugin, ServicePlugin)
- hasattr(plugin, "scheduler")
- hasattr(plugin, "polling_task")
```

### Status Shows "Unknown"

The system can't determine the status. Add explicit status tracking:

```python
class MyPlugin(WebPlugin):
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._service_running = False
    
    async def initialize(self):
        self.scheduler.start()
        self._service_running = True
```

### Start/Stop Not Working

Ensure your plugin implements `ServicePlugin` methods:

```python
from app_new.plugins.base import ServicePlugin

class MyPlugin(ServicePlugin, WebPlugin):
    async def start_services(self):
        if not self.scheduler.running:
            self.scheduler.start()
    
    async def stop_services(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
```

### Page Not Loading

1. Check API endpoint: `curl http://localhost:8000/api/services/status`
2. Check browser console for errors
3. Verify plugin manager is initialized

## Summary

✅ **Services API** - Monitor and control background services  
✅ **Services UI** - Beautiful dashboard with real-time status  
✅ **Settings Integration** - Quick access from Settings page  
✅ **Auto-Detection** - Automatically finds plugins with services  
✅ **Control Actions** - Start/Stop/Restart services  
✅ **Auto-Refresh** - Updates every 30 seconds  

**To Answer Your Question:**

**"Are services apps or do apps need background services to run?"**

**Answer:** 
- **Apps** and **Services** are separate but can be combined
- Some **apps DON'T need services** (e.g., Notepad - just UI)
- Some **apps DO need services** (e.g., Stocks - needs price updates)
- Some **plugins are BOTH** (e.g., Stocks - has UI AND services)
- The **Services page** shows all background services across all plugins

**In Short:**
- Apps = What users see 🖥️
- Services = What runs in background ⚙️
- Can exist independently or together 🔄
