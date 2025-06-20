#!/usr/bin/env python3
"""
GitBridge Plugin Loader Base Module
Phase: GBP21
Part: P21P8
Step: P21P8S2
Task: P21P8S2T1 - Plugin Loader Implementation

Load arbitration/composition/fallback strategy plugins dynamically for Phase 22.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P8 Schema]
"""

import json
import logging
import os
import sys
import importlib
import inspect
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from abc import ABC, abstractmethod
import argparse

logger = logging.getLogger(__name__)

class Plugin(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Return the plugin name."""
        pass
    
    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """Return the plugin version."""
        pass
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """Return the plugin type."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        pass

class FragmentationStrategyPlugin(Plugin):
    """Base class for fragmentation strategy plugins."""
    
    @property
    def plugin_type(self) -> str:
        return "fragmentation_strategy"
    
    @abstractmethod
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str) -> List[Any]:
        """Fragment a task into subtasks."""
        pass

class ConflictResolutionPlugin(Plugin):
    """Base class for conflict resolution plugins."""
    
    @property
    def plugin_type(self) -> str:
        return "conflict_resolution"
    
    @abstractmethod
    def resolve_conflicts(self, conflicts: List[Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between agent responses."""
        pass

class CompositionStrategyPlugin(Plugin):
    """Base class for composition strategy plugins."""
    
    @property
    def plugin_type(self) -> str:
        return "composition_strategy"
    
    @abstractmethod
    def compose_results(self, results: List[Any], strategy_config: Dict[str, Any]) -> Any:
        """Compose results into final output."""
        pass

class FallbackStrategyPlugin(Plugin):
    """Base class for fallback strategy plugins."""
    
    @property
    def plugin_type(self) -> str:
        return "fallback_strategy"
    
    @abstractmethod
    def get_fallback_plan(self, failed_agents: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback plan for failed agents."""
        pass

@dataclass
class PluginMetadata:
    """Metadata for a loaded plugin."""
    plugin_name: str
    plugin_version: str
    plugin_type: str
    plugin_class: Type[Plugin]
    plugin_module: str
    load_time: datetime
    config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    error_count: int = 0
    last_error: Optional[str] = None

class PluginManager:
    """
    Plugin manager for dynamic loading and management of plugins.
    
    Phase: GBP21
    Part: P21P8
    Step: P21P8S2
    Task: P21P8S2T1 - Core Implementation
    
    Features:
    - Dynamic plugin discovery and loading
    - Plugin validation and configuration
    - Plugin lifecycle management
    - Fallback chain support
    """
    
    def __init__(self, plugin_dir: str = "plugins", config_path: str = "plugin_config.json"):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dir: Directory containing plugin modules
            config_path: Path to plugin configuration file
        """
        self.plugin_dir = Path(plugin_dir)
        self.config_path = Path(config_path)
        self.plugins: Dict[str, PluginMetadata] = {}
        self.plugin_instances: Dict[str, Plugin] = {}
        self.fallback_chains: Dict[str, List[str]] = {}
        self._ensure_plugin_directory()
        self._load_config()
        
        logger.info(f"[P21P8S2T1] PluginManager initialized with plugin_dir: {plugin_dir}")
        
    def _ensure_plugin_directory(self):
        """Ensure plugin directory exists and create structure."""
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different plugin types
        (self.plugin_dir / "fragmentation_strategies").mkdir(exist_ok=True)
        (self.plugin_dir / "conflict_resolvers").mkdir(exist_ok=True)
        (self.plugin_dir / "composition_strategies").mkdir(exist_ok=True)
        (self.plugin_dir / "fallback_strategies").mkdir(exist_ok=True)
        
        # Create __init__.py files
        for subdir in self.plugin_dir.iterdir():
            if subdir.is_dir():
                init_file = subdir / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    
    def _load_config(self):
        """Load plugin configuration."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                self.fallback_chains = config.get('fallback_chains', {})
                logger.info(f"[P21P8S2T1] Loaded plugin config with {len(self.fallback_chains)} fallback chains")
            except Exception as e:
                logger.error(f"[P21P8S2T1] Failed to load plugin config: {e}")
                self.fallback_chains = {}
        else:
            # Create default config
            self._create_default_config()
            
    def _create_default_config(self):
        """Create default plugin configuration."""
        default_config = {
            "fallback_chains": {
                "fragmentation_strategy": ["comprehensive", "structured", "simple"],
                "conflict_resolution": ["meta_evaluator", "arbitration", "synthesis"],
                "composition_strategy": ["hierarchical", "sequential", "synthetic"],
                "fallback_strategy": ["agent_rotation", "priority_based", "random"]
            },
            "plugin_settings": {
                "auto_reload": True,
                "validation_strict": False,
                "max_plugins_per_type": 10
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"[P21P8S2T1] Created default plugin config at {self.config_path}")
        except Exception as e:
            logger.error(f"[P21P8S2T1] Failed to create default config: {e}")
            
    def load_plugins(self, plugin_dir: Optional[str] = None) -> Dict[str, PluginMetadata]:
        """
        Load plugins from directory.
        
        Args:
            plugin_dir: Optional override for plugin directory
            
        Returns:
            Dict[str, PluginMetadata]: Loaded plugin metadata
        """
        if plugin_dir:
            plugin_path = Path(plugin_dir)
        else:
            plugin_path = self.plugin_dir
            
        loaded_plugins = {}
        
        # Discover and load plugins
        for plugin_file in plugin_path.rglob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            try:
                plugin_metadata = self._load_plugin_from_file(plugin_file)
                if plugin_metadata:
                    plugin_key = f"{plugin_metadata.plugin_type}:{plugin_metadata.plugin_name}"
                    loaded_plugins[plugin_key] = plugin_metadata
                    self.plugins[plugin_key] = plugin_metadata
                    
            except Exception as e:
                logger.error(f"[P21P8S2T1] Failed to load plugin from {plugin_file}: {e}")
                
        logger.info(f"[P21P8S2T1] Loaded {len(loaded_plugins)} plugins")
        return loaded_plugins
        
    def _load_plugin_from_file(self, plugin_file: Path) -> Optional[PluginMetadata]:
        """Load a single plugin from file."""
        try:
            # Create module path
            relative_path = plugin_file.relative_to(self.plugin_dir)
            module_path = str(relative_path).replace(os.sep, ".").replace(".py", "")
            full_module_path = f"plugins.{module_path}"
            
            # Import module
            spec = importlib.util.spec_from_file_location(full_module_path, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin_classes.append(obj)
                    
            if not plugin_classes:
                logger.warning(f"[P21P8S2T1] No plugin classes found in {plugin_file}")
                return None
                
            # Load first plugin class (assuming one per file)
            plugin_class = plugin_classes[0]
            plugin_instance = plugin_class()
            
            # Create metadata
            metadata = PluginMetadata(
                plugin_name=plugin_instance.plugin_name,
                plugin_version=plugin_instance.plugin_version,
                plugin_type=plugin_instance.plugin_type,
                plugin_class=plugin_class,
                plugin_module=full_module_path,
                load_time=datetime.now(timezone.utc)
            )
            
            # Store instance
            plugin_key = f"{metadata.plugin_type}:{metadata.plugin_name}"
            self.plugin_instances[plugin_key] = plugin_instance
            
            logger.info(f"[P21P8S2T1] Loaded plugin: {plugin_key}")
            return metadata
            
        except Exception as e:
            logger.error(f"[P21P8S2T1] Failed to load plugin from {plugin_file}: {e}")
            return None
            
    def get_plugin(self, plugin_type: str, name: str) -> Optional[Plugin]:
        """
        Get a specific plugin by type and name.
        
        Args:
            plugin_type: Type of plugin to retrieve
            name: Name of the plugin
            
        Returns:
            Plugin or None if not found
        """
        plugin_key = f"{plugin_type}:{name}"
        
        # Check if plugin exists
        if plugin_key in self.plugin_instances:
            return self.plugin_instances[plugin_key]
            
        # Check fallback chain
        if plugin_type in self.fallback_chains:
            for fallback_name in self.fallback_chains[plugin_type]:
                fallback_key = f"{plugin_type}:{fallback_name}"
                if fallback_key in self.plugin_instances:
                    logger.info(f"[P21P8S2T1] Using fallback plugin: {fallback_key}")
                    return self.plugin_instances[fallback_key]
                    
        logger.warning(f"[P21P8S2T1] Plugin not found: {plugin_key}")
        return None
        
    def get_plugins_by_type(self, plugin_type: str) -> List[Plugin]:
        """Get all plugins of a specific type."""
        plugins = []
        for key, instance in self.plugin_instances.items():
            if key.startswith(f"{plugin_type}:"):
                plugins.append(instance)
        return plugins
        
    def register_plugin(self, plugin: Plugin, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a plugin programmatically.
        
        Args:
            plugin: Plugin instance to register
            config: Optional configuration for the plugin
            
        Returns:
            bool: True if registration successful
        """
        try:
            plugin_key = f"{plugin.plugin_type}:{plugin.plugin_name}"
            
            # Validate plugin
            if not self._validate_plugin(plugin):
                return False
                
            # Create metadata
            metadata = PluginMetadata(
                plugin_name=plugin.plugin_name,
                plugin_version=plugin.plugin_version,
                plugin_type=plugin.plugin_type,
                plugin_class=type(plugin),
                plugin_module="programmatic",
                load_time=datetime.now(timezone.utc),
                config=config or {}
            )
            
            # Store plugin and metadata
            self.plugin_instances[plugin_key] = plugin
            self.plugins[plugin_key] = metadata
            
            logger.info(f"[P21P8S2T1] Registered plugin: {plugin_key}")
            return True
            
        except Exception as e:
            logger.error(f"[P21P8S2T1] Failed to register plugin: {e}")
            return False
            
    def _validate_plugin(self, plugin: Plugin) -> bool:
        """Validate a plugin instance."""
        try:
            # Check required properties
            required_props = ['plugin_name', 'plugin_version', 'plugin_type']
            for prop in required_props:
                if not hasattr(plugin, prop):
                    logger.error(f"[P21P8S2T1] Plugin missing required property: {prop}")
                    return False
                    
            # Check required methods
            required_methods = ['validate_config']
            for method in required_methods:
                if not hasattr(plugin, method):
                    logger.error(f"[P21P8S2T1] Plugin missing required method: {method}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"[P21P8S2T1] Plugin validation failed: {e}")
            return False
            
    def unload_plugin(self, plugin_type: str, name: str) -> bool:
        """Unload a specific plugin."""
        plugin_key = f"{plugin_type}:{name}"
        
        if plugin_key in self.plugin_instances:
            del self.plugin_instances[plugin_key]
            
        if plugin_key in self.plugins:
            del self.plugins[plugin_key]
            
        logger.info(f"[P21P8S2T1] Unloaded plugin: {plugin_key}")
        return True
        
    def reload_plugins(self) -> Dict[str, PluginMetadata]:
        """Reload all plugins."""
        logger.info("[P21P8S2T1] Reloading all plugins")
        
        # Clear existing plugins
        self.plugin_instances.clear()
        self.plugins.clear()
        
        # Reload from directory
        return self.load_plugins()
        
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about all loaded plugins."""
        info = {
            "total_plugins": len(self.plugins),
            "plugin_types": {},
            "fallback_chains": self.fallback_chains,
            "plugins": {}
        }
        
        # Group by type
        for plugin_key, metadata in self.plugins.items():
            plugin_type = metadata.plugin_type
            if plugin_type not in info["plugin_types"]:
                info["plugin_types"][plugin_type] = 0
            info["plugin_types"][plugin_type] += 1
            
            # Plugin details
            info["plugins"][plugin_key] = {
                "name": metadata.plugin_name,
                "version": metadata.plugin_version,
                "type": metadata.plugin_type,
                "module": metadata.plugin_module,
                "load_time": metadata.load_time.isoformat(),
                "is_active": metadata.is_active,
                "error_count": metadata.error_count
            }
            
        return info
        
    def create_sample_plugins(self):
        """Create sample plugin files for testing."""
        sample_plugins = {
            "fragmentation_strategies/simple_fragmentation.py": """
from plugin_loader import FragmentationStrategyPlugin

class SimpleFragmentationPlugin(FragmentationStrategyPlugin):
    @property
    def plugin_name(self) -> str:
        return "simple"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: dict) -> bool:
        return True
    
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str):
        return [{"task_id": f"{master_task_id}_main", "description": prompt}]
""",
            "conflict_resolvers/meta_evaluator.py": """
from plugin_loader import ConflictResolutionPlugin

class MetaEvaluatorPlugin(ConflictResolutionPlugin):
    @property
    def plugin_name(self) -> str:
        return "meta_evaluator"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: dict) -> bool:
        return True
    
    def resolve_conflicts(self, conflicts: list, context: dict):
        return {"resolution_method": "meta_evaluator", "resolved": True}
""",
            "composition_strategies/hierarchical.py": """
from plugin_loader import CompositionStrategyPlugin

class HierarchicalCompositionPlugin(CompositionStrategyPlugin):
    @property
    def plugin_name(self) -> str:
        return "hierarchical"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: dict) -> bool:
        return True
    
    def compose_results(self, results: list, strategy_config: dict):
        return {"composition_method": "hierarchical", "composed": True}
"""
        }
        
        for file_path, content in sample_plugins.items():
            full_path = self.plugin_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content.strip())
                
        logger.info(f"[P21P8S2T1] Created {len(sample_plugins)} sample plugins")

def main():
    """Main function for testing plugin loader with hot-reload and dry-run support."""
    parser = argparse.ArgumentParser(description='GitBridge Plugin Loader')
    parser.add_argument('--reload-plugins', action='store_true', help='Reload plugins at runtime')
    parser.add_argument('--dry-run', action='store_true', help='Preview plugin loading without actually loading')
    args, unknown = parser.parse_known_args()
    
    manager = PluginManager()
    
    if args.reload_plugins:
        manager.reload_plugins()
        print("✅ Plugins reloaded at runtime.")
        return
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE: Previewing plugin loading")
        print("Plugin directory structure:")
        print(f"  {manager.plugin_dir}")
        print("  ├── fragmentation_strategies/")
        print("  ├── conflict_resolvers/")
        print("  ├── composition_strategies/")
        print("  └── fallback_strategies/")
        print("\nFallback chains configuration:")
        for plugin_type, fallbacks in manager.fallback_chains.items():
            print(f"  {plugin_type}: {', '.join(fallbacks)}")
        print("\nPlugin validation would check:")
        print("  - Required properties: plugin_name, plugin_version, plugin_type")
        print("  - Required methods: validate_config")
        print("  - Plugin class inheritance from base Plugin class")
        return
    
    # Create sample plugins
    manager.create_sample_plugins()
    
    # Load plugins
    loaded_plugins = manager.load_plugins()
    print(f"Loaded {len(loaded_plugins)} plugins")
    
    # Get plugin info
    info = manager.get_plugin_info()
    print(f"Plugin info: {json.dumps(info, indent=2, default=str)}")
    
    # Test getting specific plugin
    plugin = manager.get_plugin("fragmentation_strategy", "simple")
    if plugin:
        print(f"Found plugin: {plugin.plugin_name}")

if __name__ == "__main__":
    main() 