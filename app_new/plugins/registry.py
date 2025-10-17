"""
Plugin registry for managing plugin metadata and relationships.
"""
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import logging

from .base import BasePlugin, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class PluginDependency:
    """Represents a plugin dependency."""
    name: str
    version: Optional[str] = None
    required: bool = True


class PluginRegistry:
    """Registry for managing plugin metadata and dependencies."""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.dependencies: Dict[str, List[PluginDependency]] = {}
        self.dependents: Dict[str, Set[str]] = {}  # What depends on this plugin
    
    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin in the registry."""
        name = plugin.metadata.name
        
        self.plugins[name] = plugin
        self.metadata[name] = plugin.metadata
        
        # Parse dependencies
        deps = []
        for dep_str in plugin.metadata.dependencies:
            if ':' in dep_str:
                dep_name, version = dep_str.split(':', 1)
                deps.append(PluginDependency(dep_name, version))
            else:
                deps.append(PluginDependency(dep_str))
        
        self.dependencies[name] = deps
        
        # Update dependents mapping
        for dep in deps:
            if dep.name not in self.dependents:
                self.dependents[dep.name] = set()
            self.dependents[dep.name].add(name)
        
        logger.info(f"Registered plugin: {name}")
    
    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin from the registry."""
        if plugin_name in self.plugins:
            # Remove from dependents
            for dep in self.dependencies.get(plugin_name, []):
                if dep.name in self.dependents:
                    self.dependents[dep.name].discard(plugin_name)
            
            # Clean up
            del self.plugins[plugin_name]
            del self.metadata[plugin_name]
            if plugin_name in self.dependencies:
                del self.dependencies[plugin_name]
            if plugin_name in self.dependents:
                del self.dependents[plugin_name]
            
            logger.info(f"Unregistered plugin: {plugin_name}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a registered plugin by name."""
        return self.plugins.get(name)
    
    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name."""
        return self.metadata.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self.plugins.keys())
    
    def get_dependencies(self, plugin_name: str) -> List[PluginDependency]:
        """Get dependencies for a plugin."""
        return self.dependencies.get(plugin_name, [])
    
    def get_dependents(self, plugin_name: str) -> Set[str]:
        """Get plugins that depend on this plugin."""
        return self.dependents.get(plugin_name, set())
    
    def validate_dependencies(self, plugin_name: str) -> List[str]:
        """Validate dependencies for a plugin. Returns list of missing dependencies."""
        missing = []
        
        for dep in self.dependencies.get(plugin_name, []):
            if dep.name not in self.plugins:
                if dep.required:
                    missing.append(dep.name)
            elif dep.version:
                # Check version compatibility
                dep_plugin = self.plugins[dep.name]
                if not self._is_version_compatible(dep_plugin.metadata.version, dep.version):
                    missing.append(f"{dep.name} (version {dep.version} required, got {dep_plugin.metadata.version})")
        
        return missing
    
    def _is_version_compatible(self, actual_version: str, required_version: str) -> bool:
        """Check if actual version satisfies required version."""
        # Simple version comparison - in production, use proper semantic versioning
        try:
            actual_parts = [int(x) for x in actual_version.split('.')]
            required_parts = [int(x) for x in required_version.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(actual_parts), len(required_parts))
            actual_parts.extend([0] * (max_len - len(actual_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            return actual_parts >= required_parts
        except (ValueError, AttributeError):
            return True  # If we can't parse, assume compatible
    
    def get_load_order(self) -> List[str]:
        """Get the correct order to load plugins based on dependencies."""
        loaded = set()
        order = []
        
        def visit(plugin_name: str, visiting: Set[str]) -> None:
            if plugin_name in loaded:
                return
            
            if plugin_name in visiting:
                raise ValueError(f"Circular dependency detected involving {plugin_name}")
            
            if plugin_name not in self.plugins:
                # Missing dependency - will be caught by validation
                return
            
            visiting.add(plugin_name)
            
            # Load dependencies first
            for dep in self.dependencies.get(plugin_name, []):
                if dep.required:
                    visit(dep.name, visiting)
            
            visiting.remove(plugin_name)
            loaded.add(plugin_name)
            order.append(plugin_name)
        
        # Visit all plugins
        for plugin_name in self.plugins:
            if plugin_name not in loaded:
                visit(plugin_name, set())
        
        return order
    
    def get_unload_order(self) -> List[str]:
        """Get the correct order to unload plugins (reverse of load order)."""
        return list(reversed(self.get_load_order()))
    
    def can_disable_plugin(self, plugin_name: str) -> Tuple[bool, List[str]]:
        """Check if a plugin can be safely disabled."""
        dependents = self.get_dependents(plugin_name)
        enabled_dependents = []
        
        for dependent in dependents:
            dependent_plugin = self.plugins.get(dependent)
            if dependent_plugin and dependent_plugin.is_enabled():
                # Check if this is a required dependency
                for dep in self.dependencies.get(dependent, []):
                    if dep.name == plugin_name and dep.required:
                        enabled_dependents.append(dependent)
                        break
        
        can_disable = len(enabled_dependents) == 0
        return can_disable, enabled_dependents
    
    def get_plugin_info(self) -> Dict[str, Dict]:
        """Get comprehensive information about all plugins."""
        info = {}
        
        for name, plugin in self.plugins.items():
            metadata = self.metadata[name]
            dependencies = self.dependencies.get(name, [])
            dependents = self.dependents.get(name, set())
            
            missing_deps = self.validate_dependencies(name)
            can_disable, blocking_dependents = self.can_disable_plugin(name)
            
            info[name] = {
                "metadata": {
                    "name": metadata.name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "author": metadata.author,
                    "api_version": metadata.api_version,
                    "enabled": metadata.enabled,
                    "priority": metadata.priority
                },
                "status": {
                    "loaded": True,
                    "enabled": plugin.is_enabled(),
                    "can_disable": can_disable,
                    "blocking_dependents": list(blocking_dependents)
                },
                "dependencies": [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "required": dep.required,
                        "satisfied": dep.name in self.plugins
                    }
                    for dep in dependencies
                ],
                "dependents": list(dependents),
                "missing_dependencies": missing_deps
            }
        
        return info