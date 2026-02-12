import importlib
import os
import sys
from typing import List, Dict
from core.interfaces import PluginBase
from core.logger import setup_logger

class PluginLoader:
    """
    Responsible for discovering, verifying, and loading plugins.
    """
    def __init__(self, plugin_dir="plugins", config=None):
        self.plugin_dir = plugin_dir
        self.logger = setup_logger("Jarvis.PluginLoader", config)
        self.loaded_plugins: Dict[str, PluginBase] = {}

    def discover_and_load(self) -> List[PluginBase]:
        """
        Scans the plugin directory and loads valid plugins.
        Supports:
        - plugins/my_plugin.py
        - plugins/my_plugin_pkg/ (__init__.py)
        - plugins/category/my_plugin.py
        """
        self.logger.info(f"Scanning for plugins in: {self.plugin_dir}")
        
        if not os.path.exists(self.plugin_dir):
            self.logger.warning(f"Plugin directory {self.plugin_dir} does not exist.")
            return []

        # Add project root to path
        sys.path.append(os.getcwd())

        plugins = []
        
        for root, dirs, files in os.walk(self.plugin_dir):
            # Skip __pycache__
            if "__pycache__" in root:
                continue
                
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    # Construct module path
                    # e.g. plugins/system/echo.py -> plugins.system.echo
                    
                    rel_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                    module_name = rel_path.replace(os.sep, ".")[:-3] # remove .py
                    
                    self.logger.debug(f"Found potential plugin module: {module_name}")
                    plugin = self._load_plugin_from_module_by_name(module_name)
                    if plugin:
                        plugins.append(plugin)

        return plugins

    def _load_plugin_from_module_by_name(self, full_module_name: str) -> PluginBase:
        try:
            module = importlib.import_module(full_module_name)
            return self._extract_plugin_from_module(module)
        except Exception as e:
            self.logger.error(f"Failed to load plugin module {full_module_name}: {e}")
            return None

    def _extract_plugin_from_module(self, module) -> PluginBase:
        """
        Inspects the module for a class that inherits fro PluginBase.
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
                # instantiate
                try:
                    instance = attr()
                    # Validate
                    if not instance.name():
                        self.logger.error(f"Plugin class {attr_name} has empty name. Skipping.")
                        continue
                    if not instance.patterns():
                        self.logger.error(f"Plugin class {attr_name} has no patterns. Skipping.")
                        continue
                        
                    self.logger.info(f"Successfully loaded plugin: {instance.name()}")
                    return instance
                except Exception as e:
                    self.logger.error(f"Error instantiating plugin {attr_name}: {e}")
        
        return None
