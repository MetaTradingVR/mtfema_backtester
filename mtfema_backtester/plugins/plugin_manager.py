"""
Plugin manager for loading and managing plugins for the MT 9 EMA Backtester.
"""

import os
import sys
import inspect
import importlib
import importlib.util
import logging
from typing import Dict, List, Type, Any, Optional, Union, Tuple
import json
import yaml

from mtfema_backtester.plugins.base_plugin import (
    BasePlugin, 
    BaseIndicatorPlugin, 
    BaseStrategyPlugin,
    BaseVisualizationPlugin
)

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages the loading and interaction with plugins."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.indicators = {}  # type: Dict[str, BaseIndicatorPlugin]
        self.strategies = {}  # type: Dict[str, BaseStrategyPlugin]
        self.visualizations = {}  # type: Dict[str, BaseVisualizationPlugin]
        self.plugin_directories = []  # type: List[str]
        
        # Add default plugin directories
        self._add_default_directories()
    
    def _add_default_directories(self):
        """Add default plugin directories."""
        # Add built-in plugins directory
        builtin_dir = os.path.join(os.path.dirname(__file__), 'builtin')
        self.add_plugin_directory(builtin_dir)
        
        # Add user plugins directory
        user_dir = os.path.expanduser('~/.mtfema/plugins')
        self.add_plugin_directory(user_dir)
        
        # Add current directory plugins
        current_dir = os.path.join(os.getcwd(), 'plugins')
        self.add_plugin_directory(current_dir)
    
    def add_plugin_directory(self, directory: str):
        """
        Add a directory to search for plugins.
        
        Args:
            directory: Directory path to add
        """
        if os.path.isdir(directory) and directory not in self.plugin_directories:
            self.plugin_directories.append(directory)
            logger.info(f"Added plugin directory: {directory}")
    
    def discover_plugins(self):
        """
        Discover all plugins in the registered directories.
        """
        for directory in self.plugin_directories:
            if not os.path.exists(directory):
                continue
                
            self._scan_directory(directory)
    
    def _scan_directory(self, directory: str):
        """
        Scan a directory for plugin modules.
        
        Args:
            directory: Directory to scan
        """
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.py') and not filename.startswith('_'):
                    file_path = os.path.join(root, filename)
                    self._load_plugin_file(file_path)
    
    def _load_plugin_file(self, file_path: str):
        """
        Load a plugin from a file.
        
        Args:
            file_path: Path to the plugin file
        """
        try:
            # Generate a module name
            module_name = f"mtfema_plugins.{os.path.basename(file_path)[:-3]}"
            
            # Load the module spec
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load plugin spec from {file_path}")
                return
                
            # Load the module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj not in [
                    BasePlugin, BaseIndicatorPlugin, BaseStrategyPlugin, BaseVisualizationPlugin
                ]:
                    self._register_plugin(obj)
                    
        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {str(e)}")
    
    def _register_plugin(self, plugin_class: Type[BasePlugin]):
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
        """
        try:
            # Create an instance of the plugin
            plugin = plugin_class()
            
            # Determine the plugin type and register it
            if isinstance(plugin, BaseIndicatorPlugin):
                self.indicators[plugin.name] = plugin
                logger.info(f"Registered indicator plugin: {plugin.name} v{plugin.version}")
            elif isinstance(plugin, BaseStrategyPlugin):
                self.strategies[plugin.name] = plugin
                logger.info(f"Registered strategy plugin: {plugin.name} v{plugin.version}")
            elif isinstance(plugin, BaseVisualizationPlugin):
                self.visualizations[plugin.name] = plugin
                logger.info(f"Registered visualization plugin: {plugin.name} v{plugin.version}")
            else:
                logger.warning(f"Unknown plugin type: {plugin_class.__name__}")
                
        except Exception as e:
            logger.error(f"Error registering plugin {plugin_class.__name__}: {str(e)}")
    
    def get_indicator(self, name: str) -> Optional[BaseIndicatorPlugin]:
        """
        Get an indicator plugin by name.
        
        Args:
            name: Indicator name
            
        Returns:
            Indicator plugin or None if not found
        """
        return self.indicators.get(name)
    
    def get_strategy(self, name: str) -> Optional[BaseStrategyPlugin]:
        """
        Get a strategy plugin by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Strategy plugin or None if not found
        """
        return self.strategies.get(name)
    
    def get_visualization(self, name: str) -> Optional[BaseVisualizationPlugin]:
        """
        Get a visualization plugin by name.
        
        Args:
            name: Visualization name
            
        Returns:
            Visualization plugin or None if not found
        """
        return self.visualizations.get(name)
    
    def list_plugins(self) -> Dict[str, List[Dict[str, str]]]:
        """
        List all registered plugins.
        
        Returns:
            Dictionary with plugin categories and their details
        """
        result = {
            "indicators": [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "category": plugin.category
                }
                for plugin in self.indicators.values()
            ],
            "strategies": [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "timeframes": plugin.required_timeframes
                }
                for plugin in self.strategies.values()
            ],
            "visualizations": [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "libraries": plugin.supported_libraries
                }
                for plugin in self.visualizations.values()
            ]
        }
        
        return result
    
    def export_plugin_catalog(self, output_file: str, format: str = 'json'):
        """
        Export the plugin catalog to a file.
        
        Args:
            output_file: Output file path
            format: Output format ('json' or 'yaml')
        """
        catalog = self.list_plugins()
        
        try:
            with open(output_file, 'w') as f:
                if format.lower() == 'json':
                    json.dump(catalog, f, indent=2)
                elif format.lower() == 'yaml':
                    yaml.dump(catalog, f)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                    
            logger.info(f"Exported plugin catalog to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting plugin catalog: {str(e)}")
