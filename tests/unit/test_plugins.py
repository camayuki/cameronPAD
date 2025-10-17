"""
Tests for the plugin management system.
"""
import pytest
from pathlib import Path

from app_new.plugins.manager import PluginManager
from app_new.plugins.registry import PluginRegistry
from tests.conftest import assert_plugin_loaded, assert_plugin_not_loaded


class TestPluginManager:
    """Test plugin manager functionality."""
    
    @pytest.mark.asyncio
    async def test_plugin_discovery(self, plugin_manager: PluginManager):
        """Test plugin discovery."""
        plugins = await plugin_manager.discover_plugins()
        
        assert len(plugins) >= 1
        assert any(p.name == "test_plugin" for p in plugins)
    
    @pytest.mark.asyncio
    async def test_plugin_loading(self, plugin_manager: PluginManager):
        """Test plugin loading."""
        await plugin_manager.load_all_plugins()
        
        assert_plugin_loaded(plugin_manager, "test_plugin")
        
        plugin = plugin_manager.get_plugin("test_plugin")
        assert plugin.metadata.name == "test_plugin"
        assert plugin.metadata.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_plugin_enable_disable(self, plugin_manager: PluginManager):
        """Test enabling and disabling plugins."""
        # Load plugins first
        await plugin_manager.load_all_plugins()
        assert_plugin_loaded(plugin_manager, "test_plugin")
        
        # Disable plugin
        success = await plugin_manager.disable_plugin("test_plugin")
        assert success
        assert_plugin_not_loaded(plugin_manager, "test_plugin")
        
        # Enable plugin
        success = await plugin_manager.enable_plugin("test_plugin")
        assert success
        assert_plugin_loaded(plugin_manager, "test_plugin")
    
    @pytest.mark.asyncio
    async def test_plugin_reload(self, plugin_manager: PluginManager):
        """Test plugin reloading."""
        await plugin_manager.load_all_plugins()
        assert_plugin_loaded(plugin_manager, "test_plugin")
        
        # Reload plugin
        success = await plugin_manager.reload_plugin("test_plugin")
        assert success
        assert_plugin_loaded(plugin_manager, "test_plugin")
    
    @pytest.mark.asyncio
    async def test_plugin_health_check(self, plugin_manager: PluginManager):
        """Test plugin health checks."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        health = await plugin.health_check()
        
        assert health["name"] == "test_plugin"
        assert health["status"] == "healthy"
        assert health["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_plugin_status(self, plugin_manager: PluginManager):
        """Test getting plugin status."""
        await plugin_manager.load_all_plugins()
        
        status = await plugin_manager.get_plugin_status()
        
        assert len(status) >= 1
        test_plugin_status = next(
            (s for s in status if s["name"] == "test_plugin"), None
        )
        
        assert test_plugin_status is not None
        assert test_plugin_status["enabled"] is True
        assert test_plugin_status["loaded"] is True


class TestPluginRegistry:
    """Test plugin registry functionality."""
    
    @pytest.mark.asyncio
    async def test_plugin_registration(self, plugin_manager: PluginManager, plugin_registry: PluginRegistry):
        """Test plugin registration."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        plugin_registry.register(plugin)
        
        assert "test_plugin" in plugin_registry.list_plugins()
        assert plugin_registry.get_plugin("test_plugin") == plugin
    
    @pytest.mark.asyncio
    async def test_plugin_dependencies(self, plugin_manager: PluginManager, plugin_registry: PluginRegistry):
        """Test plugin dependency validation."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        plugin_registry.register(plugin)
        
        # Test plugin has no dependencies
        missing = plugin_registry.validate_dependencies("test_plugin")
        assert len(missing) == 0
    
    @pytest.mark.asyncio
    async def test_plugin_load_order(self, plugin_manager: PluginManager, plugin_registry: PluginRegistry):
        """Test plugin load order calculation."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        plugin_registry.register(plugin)
        
        load_order = plugin_registry.get_load_order()
        assert "test_plugin" in load_order
    
    @pytest.mark.asyncio
    async def test_plugin_info(self, plugin_manager: PluginManager, plugin_registry: PluginRegistry):
        """Test getting comprehensive plugin info."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        plugin_registry.register(plugin)
        
        info = plugin_registry.get_plugin_info()
        
        assert "test_plugin" in info
        plugin_info = info["test_plugin"]
        
        assert plugin_info["metadata"]["name"] == "test_plugin"
        assert plugin_info["status"]["loaded"] is True
        assert plugin_info["status"]["enabled"] is True


class TestPluginConfiguration:
    """Test plugin configuration management."""
    
    @pytest.mark.asyncio
    async def test_plugin_config_loading(self, plugin_manager: PluginManager):
        """Test loading plugin configuration."""
        plugins = await plugin_manager.discover_plugins()
        
        test_plugin = next(p for p in plugins if p.name == "test_plugin")
        config = plugin_manager.plugin_configs.get("test_plugin", {})
        
        assert config.get("enabled") is True
        assert config.get("priority") == 100
        assert config.get("settings", {}).get("test_setting") == "test_value"
    
    @pytest.mark.asyncio
    async def test_plugin_config_override(self, plugin_manager: PluginManager, temp_dir: Path):
        """Test global plugin configuration override."""
        # Create global plugin config
        global_config_content = """
test_plugin:
  enabled: false
  priority: 200
  settings:
    test_setting: "overridden_value"
"""
        
        config_dir = temp_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "plugins.yaml", "w") as f:
            f.write(global_config_content)
        
        # Create new plugin manager with global config
        new_manager = PluginManager(
            plugins_dir=str(temp_dir / "plugins"),
            config_dir=str(config_dir)
        )
        
        plugins = await new_manager.discover_plugins()
        config = new_manager.plugin_configs.get("test_plugin", {})
        
        assert config.get("enabled") is False
        assert config.get("priority") == 200
        assert config.get("settings", {}).get("test_setting") == "overridden_value"


class TestPluginRoutes:
    """Test plugin route registration."""
    
    @pytest.mark.asyncio
    async def test_plugin_router(self, plugin_manager: PluginManager):
        """Test plugin router creation."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        router = plugin.get_router()
        
        assert router is not None
        assert len(router.routes) > 0
    
    @pytest.mark.asyncio
    async def test_plugin_menu_items(self, plugin_manager: PluginManager):
        """Test plugin menu items."""
        await plugin_manager.load_all_plugins()
        
        plugin = plugin_manager.get_plugin("test_plugin")
        menu_items = plugin.get_menu_items()
        
        assert len(menu_items) > 0
        assert menu_items[0]["name"] == "Test"
        assert menu_items[0]["url"] == "/test"