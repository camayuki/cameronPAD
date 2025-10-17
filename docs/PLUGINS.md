# Plugin Development Guide

## 📖 Overview

CameronPAD's plugin system allows you to easily extend the application with new features. This guide walks you through creating, configuring, and deploying plugins.

## 🏗️ Plugin Architecture

### Plugin Types

CameronPAD supports several plugin types:

#### 1. WebPlugin
For plugins that provide web interfaces and API endpoints.
```python
from app_new.plugins.base import WebPlugin

class MyWebPlugin(WebPlugin):
    def register_routes(self) -> None:
        @self._router.get("/my-endpoint")
        async def my_endpoint():
            return {"message": "Hello from my plugin!"}
```

#### 2. ServicePlugin
For background services and scheduled tasks.
```python
from app_new.plugins.base import ServicePlugin

class MyServicePlugin(ServicePlugin):
    async def start_services(self) -> None:
        # Start background tasks
        self.task = asyncio.create_task(self.background_worker())
    
    async def stop_services(self) -> None:
        # Stop background tasks
        if self.task:
            self.task.cancel()
```

#### 3. DataPlugin
For plugins that manage data and database tables.
```python
from app_new.plugins.base import DataPlugin

class MyDataPlugin(DataPlugin):
    def get_models(self) -> List[Type]:
        return [MyModel, MyOtherModel]
    
    async def create_tables(self) -> None:
        # Database setup handled by migration system
        pass
```

#### 4. Combined Plugins
You can inherit from multiple plugin types:
```python
class MyFullPlugin(WebPlugin, ServicePlugin, DataPlugin):
    # Implement all required methods
    pass
```

## 🚀 Creating Your First Plugin

### Step 1: Create Plugin Directory
```bash
mkdir plugins/my_awesome_plugin
cd plugins/my_awesome_plugin
```

### Step 2: Create Plugin Class
Create `plugin.py`:
```python
"""
My Awesome Plugin - Example plugin implementation.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app_new.plugins.base import WebPlugin, ServicePlugin, PluginMetadata, PluginConfig

logger = logging.getLogger(__name__)


class MyAwesomePlugin(WebPlugin, ServicePlugin):
    """Example plugin demonstrating key features."""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.background_task: Optional[asyncio.Task] = None
        self.data_service = None
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="my_awesome_plugin",
            version="1.0.0",
            description="An awesome example plugin",
            author="Your Name",
            dependencies=[],  # List other required plugins
            api_version="1.0",
            enabled=True,
            priority=50  # Load order (lower = earlier)
        )
    
    async def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("Initializing My Awesome Plugin...")
        
        # Initialize services
        from .services import DataService
        self.data_service = DataService(self.config.settings)
        
        # Register API routes
        self.register_routes()
        
        # Create database tables
        await self.create_tables()
        
        self._initialized = True
        logger.info("My Awesome Plugin initialized successfully")
    
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        logger.info("Shutting down My Awesome Plugin...")
        
        # Stop background services
        await self.stop_services()
        
        logger.info("My Awesome Plugin shutdown completed")
    
    def register_routes(self) -> None:
        """Register API routes."""
        
        @self._router.get("/status")
        async def get_status():
            """Get plugin status."""
            return {
                "plugin": "my_awesome_plugin",
                "status": "active",
                "version": self.metadata.version,
                "settings": self.config.settings
            }
        
        @self._router.get("/data")
        async def get_data():
            """Get plugin data."""
            if self.data_service:
                return await self.data_service.get_all_data()
            return {"error": "Service not available"}
        
        @self._router.post("/data")
        async def create_data(name: str, value: str):
            """Create new data entry."""
            if self.data_service:
                result = await self.data_service.create_entry(name, value)
                return {"id": result, "message": "Data created successfully"}
            return {"error": "Service not available"}
    
    async def start_services(self) -> None:
        """Start background services."""
        if self.config.settings.get("enable_background_task", True):
            self.background_task = asyncio.create_task(
                self._background_worker()
            )
            logger.info("Started background worker")
    
    async def stop_services(self) -> None:
        """Stop background services."""
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped background worker")
    
    async def _background_worker(self) -> None:
        """Background task worker."""
        interval = self.config.settings.get("worker_interval", 60)
        
        while True:
            try:
                # Do background work
                logger.debug("Background worker running...")
                
                if self.data_service:
                    await self.data_service.cleanup_old_data()
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background worker: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """Return menu items for the web interface."""
        return [
            {
                "name": "My Plugin",
                "url": "/my-plugin",
                "icon": "star"
            },
            {
                "name": "Plugin Data",
                "url": "/my-plugin/data",
                "icon": "database"
            }
        ]
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets."""
        return [
            {
                "name": "My Plugin Status",
                "type": "status",
                "endpoint": "/api/v1/plugins/my_awesome_plugin/status",
                "refresh_interval": 30
            }
        ]
    
    def get_static_path(self) -> Optional[str]:
        """Return path to static files."""
        static_path = Path(__file__).parent / "static"
        return str(static_path) if static_path.exists() else None
    
    def get_template_path(self) -> Optional[str]:
        """Return path to templates."""
        template_path = Path(__file__).parent / "templates"
        return str(template_path) if template_path.exists() else None
    
    def get_migrations_path(self) -> Optional[str]:
        """Return path to database migrations."""
        migrations_path = Path(__file__).parent / "migrations"
        return str(migrations_path) if migrations_path.exists() else None
    
    async def health_check(self) -> Dict[str, Any]:
        """Return detailed health status."""
        base_health = await super().health_check()
        
        # Add plugin-specific health checks
        plugin_health = {
            "background_task_running": (
                self.background_task is not None and 
                not self.background_task.done()
            ),
            "data_service_available": self.data_service is not None
        }
        
        if self.data_service:
            try:
                count = await self.data_service.get_data_count()
                plugin_health["data_count"] = count
            except Exception as e:
                plugin_health["data_service_error"] = str(e)
        
        base_health["my_awesome_plugin"] = plugin_health
        return base_health
```

### Step 3: Create Data Models
Create `models.py`:
```python
"""
Data models for My Awesome Plugin.
"""
from typing import Optional
from datetime import datetime


class MyData:
    """Data model for plugin data."""
    
    def __init__(self, name: str, value: str, id: Optional[int] = None):
        self.id = id
        self.name = name
        self.value = value
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    @classmethod
    def from_db_row(cls, row):
        """Create instance from database row."""
        data = cls(
            name=row['name'],
            value=row['value'],
            id=row['id']
        )
        
        if row.get('created_at'):
            data.created_at = datetime.fromisoformat(row['created_at'])
        if row.get('updated_at'):
            data.updated_at = datetime.fromisoformat(row['updated_at'])
        
        return data
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

### Step 4: Create Services
Create `services.py`:
```python
"""
Business logic services for My Awesome Plugin.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .models import MyData

logger = logging.getLogger(__name__)


class DataService:
    """Service for managing plugin data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_items = config.get('max_items', 1000)
        self.cleanup_days = config.get('cleanup_days', 30)
    
    async def create_entry(self, name: str, value: str) -> int:
        """Create a new data entry."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        entry_id = db.execute_update("""
            INSERT INTO my_plugin_data (name, value, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (name, value))
        
        logger.info(f"Created data entry: {name}")
        return entry_id
    
    async def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all data entries."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        rows = db.execute_query("""
            SELECT * FROM my_plugin_data 
            ORDER BY created_at DESC
            LIMIT ?
        """, (self.max_items,))
        
        return [MyData.from_db_row(row).to_dict() for row in rows]
    
    async def get_data_by_id(self, data_id: int) -> Optional[MyData]:
        """Get data entry by ID."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        rows = db.execute_query("""
            SELECT * FROM my_plugin_data WHERE id = ?
        """, (data_id,))
        
        if rows:
            return MyData.from_db_row(rows[0])
        return None
    
    async def update_entry(self, data_id: int, name: str = None, value: str = None) -> bool:
        """Update data entry."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if value is not None:
            updates.append("value = ?")
            params.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(data_id)
        
        query = f"""
            UPDATE my_plugin_data 
            SET {', '.join(updates)}
            WHERE id = ?
        """
        
        affected = db.execute_update(query, tuple(params))
        return affected > 0
    
    async def delete_entry(self, data_id: int) -> bool:
        """Delete data entry."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        affected = db.execute_update("""
            DELETE FROM my_plugin_data WHERE id = ?
        """, (data_id,))
        
        return affected > 0
    
    async def get_data_count(self) -> int:
        """Get total count of data entries."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        result = db.execute_query("""
            SELECT COUNT(*) as count FROM my_plugin_data
        """)
        
        return result[0]['count'] if result else 0
    
    async def cleanup_old_data(self) -> int:
        """Clean up old data entries."""
        from app_new.core.database import get_database_manager
        
        if self.cleanup_days <= 0:
            return 0
        
        db = get_database_manager()
        
        cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
        
        affected = db.execute_update("""
            DELETE FROM my_plugin_data 
            WHERE created_at < ?
        """, (cutoff_date.isoformat(),))
        
        if affected > 0:
            logger.info(f"Cleaned up {affected} old data entries")
        
        return affected
    
    async def search_data(self, query: str) -> List[Dict[str, Any]]:
        """Search data entries."""
        from app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        search_pattern = f"%{query}%"
        rows = db.execute_query("""
            SELECT * FROM my_plugin_data 
            WHERE name LIKE ? OR value LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (search_pattern, search_pattern, self.max_items))
        
        return [MyData.from_db_row(row).to_dict() for row in rows]
```

### Step 5: Create Database Migration
Create `migrations/001_create_tables.sql`:
```sql
-- Create main data table
CREATE TABLE IF NOT EXISTS my_plugin_data (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_my_plugin_data_name ON my_plugin_data(name);
CREATE INDEX IF NOT EXISTS idx_my_plugin_data_created_at ON my_plugin_data(created_at);

-- Create settings table for plugin-specific settings
CREATE TABLE IF NOT EXISTS my_plugin_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Step 6: Create Configuration
Create `config.yaml`:
```yaml
# Plugin configuration
enabled: true
priority: 50

# Plugin settings
settings:
  # Background worker settings
  enable_background_task: true
  worker_interval: 60  # seconds
  
  # Data management settings
  max_items: 1000
  cleanup_days: 30
  
  # Feature flags
  enable_search: true
  enable_api: true
  
  # External API settings (if needed)
  api_key: ${MY_PLUGIN_API_KEY}
  api_url: "https://api.example.com"

# Plugin metadata
metadata:
  name: "my_awesome_plugin"
  version: "1.0.0"
  description: "An awesome example plugin"
  author: "Your Name"
  license: "MIT"
  homepage: "https://github.com/yourname/my-awesome-plugin"
  tags:
    - example
    - demo
    - data

# Plugin dependencies
dependencies: []

# Plugin permissions
permissions:
  - database.read
  - database.write
  - network.outbound  # If plugin makes external requests
  - filesystem.read   # If plugin reads files
```

### Step 7: Create Tests
Create `tests/test_plugin.py`:
```python
"""
Tests for My Awesome Plugin.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from plugins.my_awesome_plugin.plugin import MyAwesomePlugin
from plugins.my_awesome_plugin.services import DataService
from plugins.my_awesome_plugin.models import MyData
from app_new.plugins.base import PluginConfig


class TestMyAwesomePlugin:
    """Test My Awesome Plugin."""
    
    def test_plugin_metadata(self):
        """Test plugin metadata."""
        config = PluginConfig(enabled=True, settings={})
        plugin = MyAwesomePlugin(config)
        
        metadata = plugin.get_metadata()
        assert metadata.name == "my_awesome_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "An awesome example plugin"
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin initialization."""
        config = PluginConfig(enabled=True, settings={})
        plugin = MyAwesomePlugin(config)
        
        # Mock dependencies
        plugin.data_service = AsyncMock()
        
        await plugin.initialize()
        
        assert plugin._initialized is True
        assert plugin._router is not None
    
    @pytest.mark.asyncio
    async def test_plugin_health_check(self):
        """Test plugin health check."""
        config = PluginConfig(enabled=True, settings={})
        plugin = MyAwesomePlugin(config)
        plugin._initialized = True
        plugin.data_service = AsyncMock()
        plugin.data_service.get_data_count.return_value = 42
        
        health = await plugin.health_check()
        
        assert health["name"] == "my_awesome_plugin"
        assert health["status"] == "healthy"
        assert "my_awesome_plugin" in health
        assert health["my_awesome_plugin"]["data_count"] == 42
    
    def test_menu_items(self):
        """Test menu items generation."""
        config = PluginConfig(enabled=True, settings={})
        plugin = MyAwesomePlugin(config)
        
        menu_items = plugin.get_menu_items()
        
        assert len(menu_items) == 2
        assert menu_items[0]["name"] == "My Plugin"
        assert menu_items[0]["url"] == "/my-plugin"


class TestDataService:
    """Test Data Service."""
    
    @pytest.mark.asyncio
    async def test_create_entry(self, database_manager):
        """Test creating data entry."""
        config = {"max_items": 100}
        service = DataService(config)
        
        # Mock database
        database_manager.execute_update.return_value = 1
        
        entry_id = await service.create_entry("test", "value")
        
        assert entry_id == 1
        database_manager.execute_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_data(self, database_manager):
        """Test getting all data."""
        config = {"max_items": 100}
        service = DataService(config)
        
        # Mock database response
        database_manager.execute_query.return_value = [
            {
                'id': 1,
                'name': 'test',
                'value': 'value',
                'created_at': '2023-01-01T00:00:00',
                'updated_at': None
            }
        ]
        
        data = await service.get_all_data()
        
        assert len(data) == 1
        assert data[0]['name'] == 'test'
        assert data[0]['value'] == 'value'


class TestMyData:
    """Test data model."""
    
    def test_data_creation(self):
        """Test data model creation."""
        data = MyData("test", "value", 1)
        
        assert data.id == 1
        assert data.name == "test"
        assert data.value == "value"
    
    def test_from_db_row(self):
        """Test creating from database row."""
        row = {
            'id': 1,
            'name': 'test',
            'value': 'value',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': None
        }
        
        data = MyData.from_db_row(row)
        
        assert data.id == 1
        assert data.name == "test"
        assert data.value == "value"
        assert data.created_at is not None
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        data = MyData("test", "value", 1)
        data_dict = data.to_dict()
        
        assert data_dict['id'] == 1
        assert data_dict['name'] == "test"
        assert data_dict['value'] == "value"
```

### Step 8: Create Templates (Optional)
Create `templates/my_plugin.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>My Awesome Plugin</title>
</head>
<body>
    <h1>My Awesome Plugin</h1>
    <div id="plugin-content">
        <h2>Plugin Data</h2>
        <div id="data-list">
            <!-- Data will be loaded here -->
        </div>
        
        <h2>Add New Data</h2>
        <form id="add-data-form">
            <input type="text" id="name" placeholder="Name" required>
            <input type="text" id="value" placeholder="Value" required>
            <button type="submit">Add Data</button>
        </form>
    </div>
    
    <script>
        // Load and display data
        async function loadData() {
            const response = await fetch('/api/v1/plugins/my_awesome_plugin/data');
            const data = await response.json();
            
            const dataList = document.getElementById('data-list');
            dataList.innerHTML = data.map(item => 
                `<div>
                    <strong>${item.name}</strong>: ${item.value}
                    <small>(${item.created_at})</small>
                </div>`
            ).join('');
        }
        
        // Add new data
        document.getElementById('add-data-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('name').value;
            const value = document.getElementById('value').value;
            
            const response = await fetch('/api/v1/plugins/my_awesome_plugin/data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, value})
            });
            
            if (response.ok) {
                document.getElementById('add-data-form').reset();
                loadData();
            }
        });
        
        // Load data on page load
        loadData();
    </script>
</body>
</html>
```

## 🔧 Plugin Configuration

### Configuration Hierarchy
1. **Plugin's config.yaml** - Default settings
2. **Global plugins.yaml** - Global overrides
3. **Environment variables** - Runtime overrides

### Configuration Example
```yaml
# Global plugin configuration (config/plugins.yaml)
my_awesome_plugin:
  enabled: true
  priority: 50
  settings:
    worker_interval: 30
    max_items: 500
    api_key: ${MY_PLUGIN_API_KEY}
```

### Environment Variables
```bash
# Plugin-specific environment variables
export MY_PLUGIN_API_KEY="your-api-key"
export MY_PLUGIN_WORKER_INTERVAL="60"
```

## 🧪 Testing Your Plugin

### Running Plugin Tests
```bash
# Test specific plugin
pytest plugins/my_awesome_plugin/tests/

# Test with coverage
pytest --cov=plugins/my_awesome_plugin plugins/my_awesome_plugin/tests/

# Integration tests
pytest tests/integration/test_my_awesome_plugin.py
```

### Testing Best Practices
1. **Test plugin loading and initialization**
2. **Test all API endpoints**
3. **Test background services**
4. **Test error handling**
5. **Test configuration changes**
6. **Test database operations**

## 🚀 Plugin Deployment

### Installing Your Plugin
1. **Copy plugin directory** to `plugins/`
2. **Configure plugin** in `config/plugins.yaml`
3. **Restart application** to load plugin
4. **Verify plugin** is loaded via admin API

### Plugin Distribution
```bash
# Package plugin
tar -czf my_awesome_plugin.tar.gz plugins/my_awesome_plugin/

# Install plugin
tar -xzf my_awesome_plugin.tar.gz -C /path/to/cameronpad/
```

## 📊 Plugin Management

### Enable/Disable Plugin
```bash
# Via Admin API
curl -X POST /api/v1/admin/plugins/my_awesome_plugin/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Via Configuration
# Set enabled: false in config/plugins.yaml
```

### Monitor Plugin Health
```bash
# Check plugin health
curl /api/v1/admin/plugins/my_awesome_plugin/health

# Check all plugins
curl /api/v1/admin/plugins
```

### Update Plugin Configuration
```bash
# Update plugin settings
curl -X PUT /api/v1/admin/plugins/my_awesome_plugin/config \
  -H "Content-Type: application/json" \
  -d '{"settings": {"worker_interval": 120}}'
```

## 🔍 Debugging Plugins

### Common Issues
1. **Plugin not loading** - Check logs for import errors
2. **Database errors** - Verify migration files
3. **API endpoints not working** - Check route registration
4. **Background tasks not running** - Verify service startup

### Debug Tools
```python
# Add logging to your plugin
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Plugin Status
```bash
# Check plugin status
curl /api/v1/admin/system/status

# Get detailed plugin info
curl /api/v1/admin/plugins/my_awesome_plugin
```

## 🏆 Best Practices

### Code Quality
- Use type hints
- Follow PEP 8 style guide
- Write comprehensive tests
- Document your code
- Handle errors gracefully

### Performance
- Use async/await for I/O operations
- Cache expensive operations
- Limit database queries
- Use appropriate data structures
- Monitor resource usage

### Security
- Validate all inputs
- Use parameterized database queries
- Secure external API calls
- Handle sensitive data properly
- Follow principle of least privilege

### Maintainability
- Keep plugins focused and cohesive
- Use clear naming conventions
- Separate concerns properly
- Avoid tight coupling
- Version your plugins

## 🤝 Contributing Plugins

### Plugin Submission
1. Create comprehensive tests
2. Document configuration options
3. Include example usage
4. Follow coding standards
5. Submit pull request

### Plugin Registry
Consider publishing useful plugins to a shared registry for the community.

This guide should give you everything you need to create powerful, maintainable plugins for CameronPAD!