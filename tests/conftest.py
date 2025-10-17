"""
Test configuration and fixtures for CameronPAD.
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Generator, AsyncGenerator

from app_new.core.config import ConfigManager, AppConfig
from app_new.core.database import DatabaseManager, MigrationManager
from app_new.plugins.manager import PluginManager
from app_new.plugins.registry import PluginRegistry


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session")
def test_config(temp_dir: Path) -> AppConfig:
    """Create test configuration."""
    # Create test config files
    config_dir = temp_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Create test database
    db_path = temp_dir / "test.db"
    
    # Set test environment variables
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
    
    # Create config manager with test directory
    config_manager = ConfigManager(str(config_dir), "testing")
    
    # Load configuration
    config = config_manager.load_config()
    
    # Override settings for testing
    config.debug = True
    config.database.url = f"sqlite:///{db_path}"
    config.database.echo = False
    config.upload_dir = str(temp_dir / "uploads")
    config.plugins.plugins_dir = str(temp_dir / "plugins")
    config.plugins.config_dir = str(config_dir)
    
    return config


@pytest.fixture(scope="session")
async def database_manager(test_config: AppConfig) -> DatabaseManager:
    """Create and initialize test database."""
    db_manager = DatabaseManager(test_config.database.url)
    
    # Run migrations
    migration_manager = MigrationManager(db_manager)
    migration_manager.run_core_migrations()
    
    return db_manager


@pytest.fixture(scope="function")
async def clean_database(database_manager: DatabaseManager):
    """Clean database before each test."""
    # Clear all tables except migrations
    with database_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all table names except migrations
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name != 'migrations'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Clear tables
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        
        conn.commit()
    
    yield
    
    # Cleanup after test (optional)


@pytest.fixture(scope="function")
async def plugin_manager(test_config: AppConfig, temp_dir: Path) -> AsyncGenerator[PluginManager, None]:
    """Create plugin manager for testing."""
    # Create test plugins directory
    plugins_dir = temp_dir / "plugins"
    plugins_dir.mkdir(exist_ok=True)
    
    # Create test plugin structure
    await _create_test_plugin(plugins_dir / "test_plugin")
    
    # Create plugin manager
    manager = PluginManager(
        plugins_dir=str(plugins_dir),
        config_dir=str(temp_dir / "config")
    )
    
    yield manager
    
    # Cleanup
    await manager.shutdown_all_plugins()


@pytest.fixture(scope="function")
async def plugin_registry() -> PluginRegistry:
    """Create plugin registry for testing."""
    return PluginRegistry()


async def _create_test_plugin(plugin_dir: Path):
    """Create a test plugin for testing."""
    plugin_dir.mkdir(exist_ok=True)
    
    # Create plugin.py
    plugin_code = '''
"""Test plugin for testing purposes."""
from app_new.plugins.base import WebPlugin, PluginMetadata, PluginConfig
from fastapi import APIRouter

class TestPlugin(WebPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin for testing",
            author="Test",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100
        )
    
    async def initialize(self) -> None:
        self._router = APIRouter()
        
        @self._router.get("/test")
        async def test_endpoint():
            return {"message": "Test plugin endpoint"}
        
        self._initialized = True
    
    async def shutdown(self) -> None:
        pass
    
    def register_routes(self) -> None:
        pass
    
    def get_menu_items(self):
        return [{"name": "Test", "url": "/test", "icon": "test"}]
'''
    
    with open(plugin_dir / "plugin.py", "w") as f:
        f.write(plugin_code)
    
    # Create config.yaml
    config_yaml = '''
enabled: true
priority: 100
settings:
  test_setting: "test_value"
'''
    
    with open(plugin_dir / "config.yaml", "w") as f:
        f.write(config_yaml)


@pytest.fixture(scope="function")
async def test_user(database_manager: DatabaseManager) -> dict:
    """Create a test user."""
    from app_new.core.auth import get_user_manager
    
    user_manager = get_user_manager()
    user_id = user_manager.create_user(
        username="testuser",
        password="testpassword123",
        email="test@example.com",
        is_admin=False
    )
    
    return {
        "id": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "is_admin": False,
        "is_active": True
    }


@pytest.fixture(scope="function")
async def admin_user(database_manager: DatabaseManager) -> dict:
    """Create a test admin user."""
    from app_new.core.auth import get_user_manager
    
    user_manager = get_user_manager()
    user_id = user_manager.create_user(
        username="admin",
        password="adminpassword123",
        email="admin@example.com",
        is_admin=True
    )
    
    return {
        "id": user_id,
        "username": "admin",
        "email": "admin@example.com",
        "is_admin": True,
        "is_active": True
    }


@pytest.fixture(scope="function")
async def auth_token(test_user: dict) -> str:
    """Create an authentication token for test user."""
    from app_new.core.auth import get_user_manager
    
    user_manager = get_user_manager()
    return user_manager.create_access_token(test_user)


@pytest.fixture(scope="function")
async def admin_token(admin_user: dict) -> str:
    """Create an authentication token for admin user."""
    from app_new.core.auth import get_user_manager
    
    user_manager = get_user_manager()
    return user_manager.create_access_token(admin_user)


@pytest.fixture(scope="function")
async def api_key(test_user: dict) -> tuple[int, str]:
    """Create an API key for test user."""
    from app_new.core.auth import get_api_key_manager
    
    api_key_manager = get_api_key_manager()
    return api_key_manager.create_api_key(
        user_id=test_user["id"],
        key_name="test_key",
        permissions=["read", "write"]
    )


@pytest.fixture(scope="function")
async def cache_manager():
    """Create cache manager for testing."""
    from app_new.core.cache import CacheManager
    
    # Use memory backend for testing
    return CacheManager(backend="memory", max_keys=100, default_ttl=60)


# Helper functions for tests
def assert_plugin_loaded(plugin_manager: PluginManager, plugin_name: str):
    """Assert that a plugin is loaded."""
    assert plugin_name in plugin_manager.get_all_plugins()
    plugin = plugin_manager.get_plugin(plugin_name)
    assert plugin is not None
    assert plugin.is_enabled()


def assert_plugin_not_loaded(plugin_manager: PluginManager, plugin_name: str):
    """Assert that a plugin is not loaded."""
    assert plugin_name not in plugin_manager.get_all_plugins()


async def assert_database_table_exists(database_manager: DatabaseManager, table_name: str):
    """Assert that a database table exists."""
    assert database_manager.table_exists(table_name)


async def assert_database_table_empty(database_manager: DatabaseManager, table_name: str):
    """Assert that a database table is empty."""
    result = database_manager.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
    assert result[0]["count"] == 0


async def assert_cache_key_exists(cache_manager, key: str):
    """Assert that a cache key exists."""
    assert await cache_manager.exists(key)


async def assert_cache_key_not_exists(cache_manager, key: str):
    """Assert that a cache key does not exist."""
    assert not await cache_manager.exists(key)