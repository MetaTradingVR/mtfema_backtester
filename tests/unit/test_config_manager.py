"""
Unit tests for the configuration manager.
"""

import os
import pytest
import tempfile
import yaml
import json
from mtfema_backtester.config_manager import ConfigManager, ConfigurationError

class TestConfigManager:
    """Test suite for the ConfigManager class."""
    
    def test_singleton_pattern(self):
        """Test that ConfigManager follows the singleton pattern."""
        # Create two instances
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        # They should be the same object
        assert config1 is config2
    
    def test_get_default_values(self, test_config):
        """Test getting default values from config."""
        # Get a value that exists in the test config
        symbol = test_config.get('data.default_symbol')
        assert symbol == 'TEST'
        
        # Get a value that doesn't exist, with a default
        nonexistent = test_config.get('nonexistent_key', 'default_value')
        assert nonexistent == 'default_value'
    
    def test_get_typed_values(self, test_config):
        """Test getting typed values from config."""
        # Get an integer
        capital = test_config.get_typed('backtest.initial_capital', int)
        assert capital == 10000
        assert isinstance(capital, int)
        
        # Get a float
        commission = test_config.get_typed('backtest.commission', float)
        assert commission == 0.0
        assert isinstance(commission, float)
        
        # Get a boolean
        cache_enabled = test_config.get_typed('data.cache_enabled', bool)
        assert cache_enabled is False
        assert isinstance(cache_enabled, bool)
        
        # Get a list
        timeframes = test_config.get_typed('data.default_timeframes', list)
        assert timeframes == ['1d', '1h', '15m']
        assert isinstance(timeframes, list)
    
    def test_get_typed_with_conversion(self, test_config):
        """Test type conversion when getting typed values."""
        # Set a string value that should be converted to an integer
        test_config._set_nested_value('test.integer', '42')
        
        # Get it as an integer
        value = test_config.get_typed('test.integer', int)
        assert value == 42
        assert isinstance(value, int)
        
        # Set a string value that should be converted to a boolean
        test_config._set_nested_value('test.boolean_true', 'true')
        test_config._set_nested_value('test.boolean_false', 'false')
        
        # Get them as booleans
        true_value = test_config.get_typed('test.boolean_true', bool)
        false_value = test_config.get_typed('test.boolean_false', bool)
        
        assert true_value is True
        assert false_value is False
    
    def test_get_section(self, test_config):
        """Test getting a complete configuration section."""
        # Get the strategy section
        strategy_section = test_config.get_section('strategy')
        
        # It should be a dictionary
        assert isinstance(strategy_section, dict)
        
        # Check some values
        assert 'ema' in strategy_section
        assert strategy_section['ema']['period'] == 9
    
    def test_environment_variables(self, monkeypatch):
        """Test overriding configuration with environment variables."""
        # Create a new config manager
        with monkeypatch.context() as m:
            # Set environment variables
            m.setenv('MTFEMA_DATA__DEFAULT_SYMBOL', 'ENVTEST')
            m.setenv('MTFEMA_STRATEGY__EMA__PERIOD', '21')
            m.setenv('MTFEMA_BACKTEST__COMMISSION', '0.001')
            m.setenv('MTFEMA_DATA__CACHE_ENABLED', 'true')
            
            # Create a new config instance
            config = ConfigManager()
            
            # Check that environment variables override defaults
            assert config.get('data.default_symbol') == 'ENVTEST'
            assert config.get('strategy.ema.period') == 21
            assert config.get('backtest.commission') == 0.001
            assert config.get('data.cache_enabled') is True
    
    def test_load_yaml_config(self):
        """Test loading configuration from a YAML file."""
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
            # Write test configuration
            config_data = {
                'data': {
                    'default_symbol': 'YAML_TEST',
                    'cache_enabled': True
                },
                'custom_section': {
                    'custom_value': 'from_yaml'
                }
            }
            
            # Write YAML data
            yaml.dump(config_data, tmp, default_flow_style=False)
            yaml_path = tmp.name
        
        try:
            # Load configuration from YAML file
            config = ConfigManager(config_file=yaml_path)
            
            # Check values
            assert config.get('data.default_symbol') == 'YAML_TEST'
            assert config.get('data.cache_enabled') is True
            assert config.get('custom_section.custom_value') == 'from_yaml'
        finally:
            # Clean up
            os.unlink(yaml_path)
    
    def test_load_json_config(self):
        """Test loading configuration from a JSON file."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            # Write test configuration
            config_data = {
                'data': {
                    'default_symbol': 'JSON_TEST',
                    'cache_enabled': True
                },
                'custom_section': {
                    'custom_value': 'from_json'
                }
            }
            
            # Write JSON data
            json.dump(config_data, tmp)
            json_path = tmp.name
        
        try:
            # Load configuration from JSON file
            config = ConfigManager(config_file=json_path)
            
            # Check values
            assert config.get('data.default_symbol') == 'JSON_TEST'
            assert config.get('data.cache_enabled') is True
            assert config.get('custom_section.custom_value') == 'from_json'
        finally:
            # Clean up
            os.unlink(json_path)
    
    def test_save_config(self):
        """Test saving configuration to a file."""
        # Create a ConfigManager with some values
        config = ConfigManager()
        config._set_nested_value('test.save', 'saved_value')
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
            yaml_path = tmp.name
        
        try:
            # Save the configuration
            config.save_to_file(yaml_path)
            
            # Load it again to verify
            with open(yaml_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Check that the value was saved
            assert 'test' in loaded_config
            assert 'save' in loaded_config['test']
            assert loaded_config['test']['save'] == 'saved_value'
        finally:
            # Clean up
            os.unlink(yaml_path)
    
    def test_error_handling(self, test_config):
        """Test error handling in the config manager."""
        # Try to get a non-existent value with no default - should raise an error
        with pytest.raises(ConfigurationError):
            test_config.get_typed('nonexistent_key', int)
        
        # Try to get a value with the wrong type and no conversion
        test_config._set_nested_value('test.string', 'not_an_integer')
        
        with pytest.raises(ConfigurationError):
            test_config.get_typed('test.string', int)
            
    def test_dump_config(self, test_config):
        """Test dumping the entire configuration."""
        # Dump the config
        config_dump = test_config.dump()
        
        # It should be a dictionary
        assert isinstance(config_dump, dict)
        
        # Check some values
        assert 'data' in config_dump
        assert 'strategy' in config_dump
        assert 'backtest' in config_dump 