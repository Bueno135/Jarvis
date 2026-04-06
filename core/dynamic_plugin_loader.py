"""
Dynamic plugin system for Jarvis.
Supports hot-loading, hot-unloading, and plugin dependencies.
"""
import os
import sys
import importlib
import inspect
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.interfaces import PluginBase, CommandContext, CommandResult
from core.logger import setup_logger
from core.exceptions import PluginError
from core.cache import cache_result, get_cache_instance

class PluginEvent:
    """Plugin lifecycle event."""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    UPDATED = "updated"

class PluginDependency:
    """Plugin dependency definition."""
    def __init__(self, name: str, version: str = ">=1.0.0", optional: bool = False):
        self.name = name
        self.version = version
        self.optional = optional

class PluginMetadata:
    """Plugin metadata container."""
    def __init__(self, name: str, version: str, description: str = "",
                 author: str = "", dependencies: List[PluginDependency] = None,
                 tags: List[str] = None, hot_reloadable: bool = True):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.hot_reloadable = hot_reloadable
        self.loaded_at = None
        self.file_path = None

class PluginRegistry:
    """Registry for managing loaded plugins."""
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        self.event_listeners: Dict[str, List[Callable]] = {}
        
    def register(self, plugin: PluginBase, metadata: PluginMetadata):
        """Register a plugin with its metadata."""
        self.plugins[metadata.name] = plugin
        self.metadata[metadata.name] = metadata
        metadata.loaded_at = time.time()
        
        # Update dependency graph
        self.dependency_graph[metadata.name] = {dep.name for dep in metadata.dependencies}
        
        # Update reverse dependencies
        for dep in metadata.dependencies:
            if dep.name not in self.reverse_dependencies:
                self.reverse_dependencies[dep.name] = set()
            self.reverse_dependencies[dep.name].add(metadata.name)
    
    def unregister(self, name: str):
        """Unregister a plugin."""
        if name in self.plugins:
            del self.plugins[name]
        if name in self.metadata:
            del self.metadata[name]
        
        # Clean up dependency graph
        if name in self.dependency_graph:
            del self.dependency_graph[name]
        
        # Clean up reverse dependencies
        for dep_name, dependents in self.reverse_dependencies.items():
            dependents.discard(name)
            if not dependents:
                del self.reverse_dependencies[dep_name]
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get plugin by name."""
        return self.plugins.get(name)
    
    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name."""
        return self.metadata.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self.plugins.keys())
    
    def get_dependents(self, name: str) -> Set[str]:
        """Get all plugins that depend on the given plugin."""
        return self.reverse_dependencies.get(name, set())
    
    def add_event_listener(self, event: str, callback: Callable):
        """Add event listener for plugin events."""
        if event not in self.event_listeners:
            self.event_listeners[event] = []
        self.event_listeners[event].append(callback)
    
    def emit_event(self, event: str, plugin_name: str, **kwargs):
        """Emit plugin event."""
        listeners = self.event_listeners.get(event, [])
        for listener in listeners:
            try:
                listener(plugin_name, **kwargs)
            except Exception as e:
                print(f"Error in event listener: {e}")

class PluginFileWatcher(FileSystemEventHandler):
    """File system watcher for plugin hot-reloading."""
    
    def __init__(self, dynamic_loader: 'DynamicPluginLoader'):
        super().__init__()
        self.dynamic_loader = dynamic_loader
        self.logger = setup_logger("Jarvis.PluginWatcher", {})
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix != '.py' or file_path.name.startswith('__'):
            return
            
        self.logger.info(f"Plugin file modified: {file_path}")
        
        # Find which plugin this file belongs to
        plugin_name = self.dynamic_loader._find_plugin_for_file(file_path)
        if plugin_name:
            metadata = self.dynamic_loader.registry.get_metadata(plugin_name)
            if metadata and metadata.hot_reloadable:
                self.dynamic_loader.reload_plugin(plugin_name)

class DynamicPluginLoader:
    """Dynamic plugin loader with hot-reloading support."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = setup_logger("Jarvis.DynamicPluginLoader", self.config)
        self.registry = PluginRegistry()
        self.plugins_path = Path(self.config.get("plugins_dir", "plugins"))
        self.observer = None
        self.watching = False
        
        # Plugin loading cache
        self.cache = get_cache_instance()
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Start file watcher if enabled
        if self.config.get("hot_reload", True):
            self._start_file_watcher()
    
    def _start_file_watcher(self):
        """Start file system watcher for hot-reloading."""
        if not self.plugins_path.exists():
            self.logger.warning(f"Plugins directory not found: {self.plugins_path}")
            return
        
        self.observer = Observer()
        handler = PluginFileWatcher(self)
        self.observer.schedule(handler, str(self.plugins_path), recursive=True)
        self.observer.start()
        self.watching = True
        self.logger.info("Plugin file watcher started")
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """Discover all available plugins."""
        plugins = []
        
        if not self.plugins_path.exists():
            self.logger.warning(f"Plugins directory not found: {self.plugins_path}")
            return plugins
        
        for plugin_dir in self.plugins_path.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("__"):
                metadata = self._load_plugin_metadata(plugin_dir)
                if metadata:
                    plugins.append(metadata)
        
        self.logger.info(f"Discovered {len(plugins)} plugins")
        return plugins
    
    def _load_plugin_metadata(self, plugin_dir: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from directory."""
        try:
            # Look for plugin files
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                module_name = f"plugins.{plugin_dir.name}.{py_file.stem}"
                module = importlib.import_module(module_name)
                
                # Find PluginBase classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginBase) and obj != PluginBase:
                        # Extract metadata from class
                        metadata = self._extract_metadata(obj, plugin_dir, py_file)
                        return metadata
                        
        except Exception as e:
            self.logger.error(f"Failed to load metadata from {plugin_dir}: {e}")
            
        return None
    
    def _extract_metadata(self, plugin_class: type, plugin_dir: Path, file_path: Path) -> PluginMetadata:
        """Extract metadata from plugin class."""
        # Create instance to get basic info
        try:
            instance = plugin_class()
            name = instance.name()
            patterns = instance.patterns()
        except Exception as e:
            self.logger.error(f"Failed to instantiate plugin class: {e}")
            name = plugin_class.__name__
            patterns = []
        
        # Try to get additional metadata from class attributes
        version = getattr(plugin_class, "__version__", "1.0.0")
        description = getattr(plugin_class, "__description__", f"Plugin: {name}")
        author = getattr(plugin_class, "__author__", "Unknown")
        tags = getattr(plugin_class, "__tags__", [])
        dependencies = getattr(plugin_class, "__dependencies__", [])
        hot_reloadable = getattr(plugin_class, "__hot_reloadable__", True)
        
        # Convert dependencies to PluginDependency objects
        deps = []
        for dep in dependencies:
            if isinstance(dep, str):
                deps.append(PluginDependency(dep))
            elif isinstance(dep, dict):
                deps.append(PluginDependency(
                    dep.get("name", ""),
                    dep.get("version", ">=1.0.0"),
                    dep.get("optional", False)
                ))
            elif isinstance(dep, PluginDependency):
                deps.append(dep)
        
        return PluginMetadata(
            name=name,
            version=version,
            description=description,
            author=author,
            dependencies=deps,
            tags=tags,
            hot_reloadable=hot_reloadable
        )
    
    def load_plugin(self, name: str) -> bool:
        """Load a specific plugin by name."""
        with self.lock:
            # Check if already loaded
            if name in self.registry.plugins:
                self.logger.warning(f"Plugin {name} already loaded")
                return True
            
            # Find plugin metadata
            metadata = None
            for plugin_meta in self.discover_plugins():
                if plugin_meta.name == name:
                    metadata = plugin_meta
                    break
            
            if not metadata:
                self.logger.error(f"Plugin {name} not found")
                return False
            
            # Check dependencies
            if not self._check_dependencies(metadata):
                return False
            
            # Load the plugin
            try:
                plugin = self._load_plugin_instance(metadata)
                if plugin:
                    self.registry.register(plugin, metadata)
                    self.registry.emit_event(PluginEvent.LOADED, name, metadata=metadata)
                    self.logger.info(f"Plugin {name} loaded successfully")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to load plugin {name}: {e}")
                self.registry.emit_event(PluginEvent.ERROR, name, error=str(e))
                return False
            
            return False
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a specific plugin by name."""
        with self.lock:
            if name not in self.registry.plugins:
                self.logger.warning(f"Plugin {name} not loaded")
                return False
            
            # Check if other plugins depend on this one
            dependents = self.registry.get_dependents(name)
            if dependents:
                self.logger.error(f"Cannot unload {name}: required by {dependents}")
                return False
            
            metadata = self.registry.get_metadata(name)
            plugin = self.registry.get_plugin(name)
            
            try:
                # Call cleanup if available
                if hasattr(plugin, 'cleanup'):
                    plugin.cleanup()
                
                # Remove from registry
                self.registry.unregister(name)
                self.registry.emit_event(PluginEvent.UNLOADED, name, metadata=metadata)
                self.logger.info(f"Plugin {name} unloaded successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to unload plugin {name}: {e}")
                self.registry.emit_event(PluginEvent.ERROR, name, error=str(e))
                return False
    
    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin."""
        with self.lock:
            metadata = self.registry.get_metadata(name)
            if not metadata:
                self.logger.error(f"Plugin {name} not found")
                return False
            
            if not metadata.hot_reloadable:
                self.logger.warning(f"Plugin {name} is not hot-reloadable")
                return False
            
            self.logger.info(f"Reloading plugin {name}")
            
            # Unload and reload
            if self.unload_plugin(name):
                return self.load_plugin(name)
            
            return False
    
    def _check_dependencies(self, metadata: PluginMetadata) -> bool:
        """Check if all dependencies are satisfied."""
        for dep in metadata.dependencies:
            if dep.name in self.registry.plugins:
                continue
            
            if dep.optional:
                self.logger.warning(f"Optional dependency {dep.name} not loaded for {metadata.name}")
                continue
            
            # Try to load dependency
            if not self.load_plugin(dep.name):
                self.logger.error(f"Required dependency {dep.name} not found for {metadata.name}")
                return False
        
        return True
    
    def _load_plugin_instance(self, metadata: PluginMetadata) -> Optional[PluginBase]:
        """Load plugin instance from file."""
        # Find the plugin file
        plugin_file = None
        for py_file in metadata.file_path.parent.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            module_name = f"plugins.{metadata.file_path.parent.name}.{py_file.stem}"
            
            try:
                # Reload the module to get latest changes
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                
                module = importlib.import_module(module_name)
                
                # Find PluginBase classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginBase) and obj != PluginBase:
                        instance = obj()
                        if instance.name() == metadata.name:
                            return instance
                            
            except Exception as e:
                self.logger.error(f"Failed to load plugin instance from {module_name}: {e}")
        
        return None
    
    def _find_plugin_for_file(self, file_path: Path) -> Optional[str]:
        """Find which plugin a file belongs to."""
        for name, metadata in self.registry.metadata.items():
            if metadata.file_path and metadata.file_path.parent == file_path.parent:
                return name
        return None
    
    def load_all_plugins(self) -> int:
        """Load all discovered plugins."""
        plugins = self.discover_plugins()
        loaded_count = 0
        
        for metadata in plugins:
            if self.load_plugin(metadata.name):
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count}/{len(plugins)} plugins")
        return loaded_count
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin."""
        metadata = self.registry.get_metadata(name)
        plugin = self.registry.get_plugin(name)
        
        if not metadata:
            return None
        
        info = {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "tags": metadata.tags,
            "dependencies": [dep.name for dep in metadata.dependencies],
            "hot_reloadable": metadata.hot_reloadable,
            "loaded_at": metadata.loaded_at,
            "loaded": plugin is not None,
            "patterns": plugin.patterns() if plugin else []
        }
        
        if plugin:
            info.update({
                "help": getattr(plugin, 'get_help', lambda: "No help available")(),
                "class_name": plugin.__class__.__name__
            })
        
        return info
    
    def list_plugins_info(self) -> List[Dict[str, Any]]:
        """Get information about all plugins."""
        return [self.get_plugin_info(name) for name in self.registry.list_plugins()]
    
    def shutdown(self):
        """Shutdown the dynamic plugin loader."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.watching = False
            self.logger.info("Plugin file watcher stopped")
        
        # Unload all plugins
        for name in list(self.registry.list_plugins()):
            self.unload_plugin(name)

# Cache plugin loading results
@cache_result(ttl=300, tags=["plugin"])
def cached_plugin_load(plugin_name: str) -> Dict[str, Any]:
    """Cached plugin loading for performance."""
    # This would be implemented by the DynamicPluginLoader
    return {"name": plugin_name, "cached": True}
