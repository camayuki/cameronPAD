"""
Plugin manager for handling plugin discovery, loading, and lifecycle.
"""
import os
import sys
import importlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
import logging

from .base import BasePlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Information about a discovered plugin."""
    name: str
    path: Path
    config_path: Optional[Path]
    module_name: str
    enabled: bool


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""
    
    def __init__(self, plugins_dir: str, config_dir: str):
        self.plugins_dir = Path(plugins_dir)
        self.config_dir = Path(config_dir)
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        
    async def discover_plugins(self) -> List[PluginInfo]:
        """Discover all available plugins."""
        discovered = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist")
            return discovered
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('.'):
                continue
                
            plugin_file = plugin_dir / "plugin.py"
            config_file = plugin_dir / "config.yaml"
            
            if not plugin_file.exists():
                logger.warning(f"Plugin {plugin_dir.name} missing plugin.py")
                continue
            
            # Load plugin configuration
            config = {}
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f) or {}
                except Exception as e:
                    logger.error(f"Error loading config for {plugin_dir.name}: {e}")
                    continue
            
            # Check global plugin configuration
            global_config_file = self.config_dir / "plugins.yaml"
            global_config = {}
            if global_config_file.exists():
                try:
                    with open(global_config_file, 'r') as f:
                        all_plugins_config = yaml.safe_load(f) or {}
                        global_config = all_plugins_config.get(plugin_dir.name, {})
                except Exception as e:
                    logger.error(f"Error loading global plugin config: {e}")
            
            # Merge configurations (global overrides local)
            final_config = {**config, **global_config}
            enabled = final_config.get('enabled', True)
            
            plugin_info = PluginInfo(
                name=plugin_dir.name,
                path=plugin_dir,
                config_path=config_file if config_file.exists() else None,
                module_name=f"plugins.{plugin_dir.name}.plugin",
                enabled=enabled
            )
            
            discovered.append(plugin_info)
            self.plugin_info[plugin_dir.name] = plugin_info
            self.plugin_configs[plugin_dir.name] = final_config
        
        # Sort by priority (if specified in config)
        discovered.sort(key=lambda p: self.plugin_configs[p.name].get('priority', 100))
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    async def load_plugin(self, plugin_info: PluginInfo) -> Optional[BasePlugin]:
        """Load a single plugin."""
        if not plugin_info.enabled:
            logger.info(f"Plugin {plugin_info.name} is disabled")
            return None
        
        try:
            # Add plugin directory to Python path
            plugin_parent = str(plugin_info.path.parent)
            if plugin_parent not in sys.path:
                sys.path.insert(0, plugin_parent)
            
            # Import the plugin module
            module = importlib.import_module(plugin_info.module_name)
            
            # Find the plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No plugin class found in {plugin_info.module_name}")
                return None
            
            # Create plugin configuration
            config_data = self.plugin_configs.get(plugin_info.name, {})
            plugin_config = PluginConfig(**config_data)
            
            # Instantiate plugin
            plugin = plugin_class(plugin_config)
            
            # Initialize plugin
            await plugin.initialize()
            
            logger.info(f"Loaded plugin: {plugin.metadata.name} v{plugin.metadata.version}")
            return plugin
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_info.name}: {e}")
            return None
    
    async def load_all_plugins(self) -> None:
        """Load all discovered plugins."""
        plugin_infos = await self.discover_plugins()
        
        for plugin_info in plugin_infos:
            if plugin_info.enabled:
                plugin = await self.load_plugin(plugin_info)
                if plugin:
                    self.plugins[plugin_info.name] = plugin
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
    
    async def unload_plugin(self, plugin_name: str) -> None:
        """Unload a specific plugin."""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            try:
                await plugin.shutdown()
                del self.plugins[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {e}")
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin."""
        if plugin_name in self.plugins:
            await self.unload_plugin(plugin_name)
        
        if plugin_name in self.plugin_info:
            plugin_info = self.plugin_info[plugin_name]
            plugin = await self.load_plugin(plugin_info)
            if plugin:
                self.plugins[plugin_name] = plugin
                return True
        
        return False
    
    async def shutdown_all_plugins(self) -> None:
        """Shutdown all loaded plugins."""
        for plugin_name in list(self.plugins.keys()):
            await self.unload_plugin(plugin_name)
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a loaded plugin by name."""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins."""
        return self.plugins.copy()
    
    def get_enabled_plugins(self) -> Dict[str, BasePlugin]:
        """Get all enabled plugins."""
        return {name: plugin for name, plugin in self.plugins.items() 
                if plugin.is_enabled()}
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        if plugin_name in self.plugin_info:
            # Update configuration
            self.plugin_configs[plugin_name]['enabled'] = True
            self.plugin_info[plugin_name].enabled = True
            
            # Save to global config
            await self._save_plugin_config(plugin_name, {'enabled': True})
            
            # Load if not already loaded
            if plugin_name not in self.plugins:
                plugin_info = self.plugin_info[plugin_name]
                plugin = await self.load_plugin(plugin_info)
                if plugin:
                    self.plugins[plugin_name] = plugin
                    return True
            
            return plugin_name in self.plugins
        
        return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        if plugin_name in self.plugin_info:
            # Update configuration
            self.plugin_configs[plugin_name]['enabled'] = False
            self.plugin_info[plugin_name].enabled = False
            
            # Save to global config
            await self._save_plugin_config(plugin_name, {'enabled': False})
            
            # Unload if loaded
            if plugin_name in self.plugins:
                await self.unload_plugin(plugin_name)
            
            return True
        
        return False
    
    async def _save_plugin_config(self, plugin_name: str, config_update: Dict[str, Any]) -> None:
        """Save plugin configuration to global config file."""
        global_config_file = self.config_dir / "plugins.yaml"
        
        # Load existing config
        all_plugins_config = {}
        if global_config_file.exists():
            try:
                with open(global_config_file, 'r') as f:
                    all_plugins_config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Error loading global plugin config: {e}")
        
        # Update config
        if plugin_name not in all_plugins_config:
            all_plugins_config[plugin_name] = {}
        
        all_plugins_config[plugin_name].update(config_update)
        
        # Save config
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(global_config_file, 'w') as f:
                yaml.dump(all_plugins_config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving global plugin config: {e}")
    
    async def get_plugin_status(self) -> List[Dict[str, Any]]:
        """Get status of all plugins."""
        status = []
        
        for plugin_name, plugin_info in self.plugin_info.items():
            plugin = self.plugins.get(plugin_name)
            
            plugin_status = {
                "name": plugin_name,
                "enabled": plugin_info.enabled,
                "loaded": plugin is not None,
                "path": str(plugin_info.path),
                "config_path": str(plugin_info.config_path) if plugin_info.config_path else None
            }
            
            if plugin:
                health = await plugin.health_check()
                plugin_status.update({
                    "metadata": plugin.metadata.dict(),
                    "health": health
                })
            
            status.append(plugin_status)
        
        return status