"""
Enhanced Configuration Management System for Multi-Timeframe 9 EMA Extension Strategy.

This module provides a robust configuration system that supports:
- YAML and JSON configuration files
- Environment variable overrides
- Type conversion and validation
- Hierarchical configuration with separate sections
- Global configuration instance with caching
"""

import os
import re
import json
import yaml
import logging
from typing import Any, Dict, Optional, Union, List, Type, TypeVar, cast
from functools import lru_cache
from pathlib import Path

T = TypeVar('T')

# Setup logger
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class ConfigManager:
    """
    Enhanced configuration manager for the Multi-Timeframe 9 EMA Extension Strategy.
    
    Provides a unified interface for accessing configuration from files and environment variables.
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None, env_prefix: str = "MTFEMA"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
            env_prefix: Prefix for environment variables
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        self._initialized = True
        self._config_file = config_file
        self._env_prefix = env_prefix
        self._config_data = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load default configuration from config.py
        try:
            from . import config as default_config
            
            # Extract all uppercase variables from the module
            for var_name in dir(default_config):
                if var_name.isupper():
                    var_value = getattr(default_config, var_name)
                    # Convert variable name from UPPERCASE_WITH_UNDERSCORES to lowercase.with.dots
                    config_key = var_name.lower().replace('_', '.')
                    self._set_nested_value(config_key, var_value)
        except ImportError:
            logger.warning("Could not import default config module")
        
        # Load configuration from file if specified
        if self._config_file:
            if not os.path.exists(self._config_file):
                logger.warning(f"Configuration file not found: {self._config_file}")
            else:
                file_ext = os.path.splitext(self._config_file)[1].lower()
                try:
                    with open(self._config_file, 'r') as f:
                        if file_ext == '.yaml' or file_ext == '.yml':
                            file_config = yaml.safe_load(f)
                        elif file_ext == '.json':
                            file_config = json.load(f)
                        else:
                            logger.warning(f"Unsupported config file type: {file_ext}")
                            file_config = {}
                        
                        # Update configuration with file values
                        self._update_config_recursive(self._config_data, file_config)
                        logger.info(f"Loaded configuration from {self._config_file}")
                except Exception as e:
                    logger.error(f"Error loading configuration file: {str(e)}")
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_pattern = re.compile(f"^{self._env_prefix}_(.+)$")
        
        for env_var, env_value in os.environ.items():
            match = env_pattern.match(env_var)
            if match:
                # Convert environment variable key to config key
                # E.g., MTFEMA_STRATEGY__EMA_PERIOD -> strategy.ema.period
                config_key = match.group(1).lower().replace('__', '.').replace('_', '.')
                
                # Try to parse the value
                try:
                    # Try to parse as JSON first
                    value = json.loads(env_value)
                except json.JSONDecodeError:
                    # If not valid JSON, use as string
                    value = env_value
                
                # Set value in config
                self._set_nested_value(config_key, value)
                logger.debug(f"Loaded configuration from environment: {config_key} = {value}")
    
    def _set_nested_value(self, key_path: str, value: Any) -> None:
        """
        Set value in nested dictionary using dot notation.
        
        Args:
            key_path: Key path in dot notation (e.g., 'strategy.ema.period')
            value: Value to set
        """
        keys = key_path.split('.')
        current = self._config_data
        
        # Traverse to the nested location
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # If the path is blocked by a non-dict value, convert it to dict
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
    
    def _update_config_recursive(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Update configuration recursively.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with updates
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively update nested dictionaries
                self._update_config_recursive(target[key], value)
            else:
                # Update or add the value
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Key in dot notation (e.g., 'strategy.ema.period')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        current = self._config_data
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return default
            current = current[k]
        
        return current
    
    def get_typed(self, key: str, expected_type: Type[T], default: Optional[T] = None) -> T:
        """
        Get configuration value with type checking.
        
        Args:
            key: Key in dot notation
            expected_type: Expected type
            default: Default value if key not found
            
        Returns:
            Configuration value of the expected type
            
        Raises:
            ConfigurationError: If value is not of expected type
        """
        value = self.get(key, default)
        
        if value is None:
            if default is not None:
                return default
            raise ConfigurationError(f"Configuration key not found: {key}")
        
        if not isinstance(value, expected_type):
            # Try to convert value to expected type
            try:
                if expected_type is bool and isinstance(value, str):
                    # Handle boolean string conversion
                    if value.lower() in ('true', 'yes', '1', 'on'):
                        return cast(T, True)
                    elif value.lower() in ('false', 'no', '0', 'off'):
                        return cast(T, False)
                
                # General conversion
                value = expected_type(value)
            except (ValueError, TypeError):
                raise ConfigurationError(
                    f"Configuration value for {key} is not of expected type {expected_type.__name__}"
                )
        
        return cast(T, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary with section configuration
        """
        return self.get(section, {})
    
    @lru_cache(maxsize=1)
    def dump(self) -> Dict[str, Any]:
        """
        Dump the entire configuration.
        
        Returns:
            Dictionary with all configuration values
        """
        return dict(self._config_data)
    
    def save_to_file(self, filename: str) -> None:
        """
        Save configuration to file.
        
        Args:
            filename: Path to save the configuration
        """
        file_ext = os.path.splitext(filename)[1].lower()
        
        try:
            with open(filename, 'w') as f:
                if file_ext == '.yaml' or file_ext == '.yml':
                    yaml.dump(self._config_data, f, default_flow_style=False)
                elif file_ext == '.json':
                    json.dump(self._config_data, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported file extension: {file_ext}")
            
            logger.info(f"Configuration saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving configuration to file: {str(e)}")
            raise

# Global instance
config = ConfigManager()

def get_config() -> ConfigManager:
    """
    Get the global configuration instance.
    
    Returns:
        ConfigManager instance
    """
    return config

def load_config_file(config_file: str) -> ConfigManager:
    """
    Load configuration from file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_file) 