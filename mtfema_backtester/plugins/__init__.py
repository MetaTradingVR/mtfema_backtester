"""
Plugin system for the MT 9 EMA Backtester allowing custom indicators and strategies.
"""

from mtfema_backtester.plugins.plugin_manager import PluginManager
from mtfema_backtester.plugins.base_plugin import (
    BaseIndicatorPlugin,
    BaseStrategyPlugin,
    BaseVisualizationPlugin
)

# Create a global plugin manager instance
plugin_manager = PluginManager()

__all__ = [
    'plugin_manager',
    'BaseIndicatorPlugin',
    'BaseStrategyPlugin',
    'BaseVisualizationPlugin'
]
