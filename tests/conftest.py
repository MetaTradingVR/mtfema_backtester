"""
Test fixtures for the Multi-Timeframe 9 EMA Extension Strategy.

This module provides pytest fixtures that can be used across different test modules.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import json
import yaml

# Add project root to Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from mtfema_backtester.config_manager import ConfigManager

@pytest.fixture
def sample_price_data():
    """
    Create a sample price dataframe for testing.
    
    Returns:
        pd.DataFrame: DataFrame with OHLCV data
    """
    # Create date range
    dates = pd.date_range(start='2023-01-01', end='2023-01-30', freq='1D')
    
    # Create a simple test dataframe
    np.random.seed(42)  # For reproducibility
    data = pd.DataFrame({
        'Open': np.random.normal(100, 5, len(dates)),
        'High': np.random.normal(102, 5, len(dates)),
        'Low': np.random.normal(98, 5, len(dates)),
        'Close': np.random.normal(101, 5, len(dates)),
        'Volume': np.random.normal(1000000, 200000, len(dates))
    }, index=dates)
    
    # Make sure High is the highest and Low is the lowest
    for i in range(len(data)):
        data.loc[data.index[i], 'High'] = max(
            data.loc[data.index[i], 'Open'],
            data.loc[data.index[i], 'Close'],
            data.loc[data.index[i], 'High']
        ) + abs(np.random.normal(0, 0.5))
        
        data.loc[data.index[i], 'Low'] = min(
            data.loc[data.index[i], 'Open'],
            data.loc[data.index[i], 'Close'],
            data.loc[data.index[i], 'Low']
        ) - abs(np.random.normal(0, 0.5))
    
    return data

@pytest.fixture
def multi_timeframe_data():
    """
    Create sample data for multiple timeframes.
    
    Returns:
        dict: Dictionary of dataframes by timeframe
    """
    # Daily data
    daily_data = sample_price_data()
    
    # Create hourly data (24x more points)
    hourly_dates = pd.date_range(start='2023-01-01', end='2023-01-30', freq='1H')
    hourly_data = pd.DataFrame({
        'Open': np.random.normal(100, 2, len(hourly_dates)),
        'High': np.random.normal(101, 2, len(hourly_dates)),
        'Low': np.random.normal(99, 2, len(hourly_dates)),
        'Close': np.random.normal(100.5, 2, len(hourly_dates)),
        'Volume': np.random.normal(50000, 10000, len(hourly_dates))
    }, index=hourly_dates)
    
    # Make sure High is the highest and Low is the lowest for hourly data too
    for i in range(len(hourly_data)):
        hourly_data.loc[hourly_data.index[i], 'High'] = max(
            hourly_data.loc[hourly_data.index[i], 'Open'],
            hourly_data.loc[hourly_data.index[i], 'Close'],
            hourly_data.loc[hourly_data.index[i], 'High']
        ) + abs(np.random.normal(0, 0.2))
        
        hourly_data.loc[hourly_data.index[i], 'Low'] = min(
            hourly_data.loc[hourly_data.index[i], 'Open'],
            hourly_data.loc[hourly_data.index[i], 'Close'],
            hourly_data.loc[hourly_data.index[i], 'Low']
        ) - abs(np.random.normal(0, 0.2))
    
    # Create 15min data (4x more points than hourly)
    min15_dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='15min')
    min15_data = pd.DataFrame({
        'Open': np.random.normal(100, 1, len(min15_dates)),
        'High': np.random.normal(100.5, 1, len(min15_dates)),
        'Low': np.random.normal(99.5, 1, len(min15_dates)),
        'Close': np.random.normal(100, 1, len(min15_dates)),
        'Volume': np.random.normal(10000, 2000, len(min15_dates))
    }, index=min15_dates)
    
    # Make sure High is the highest and Low is the lowest for 15min data too
    for i in range(len(min15_data)):
        min15_data.loc[min15_data.index[i], 'High'] = max(
            min15_data.loc[min15_data.index[i], 'Open'],
            min15_data.loc[min15_data.index[i], 'Close'],
            min15_data.loc[min15_data.index[i], 'High']
        ) + abs(np.random.normal(0, 0.1))
        
        min15_data.loc[min15_data.index[i], 'Low'] = min(
            min15_data.loc[min15_data.index[i], 'Open'],
            min15_data.loc[min15_data.index[i], 'Close'],
            min15_data.loc[min15_data.index[i], 'Low']
        ) - abs(np.random.normal(0, 0.1))
    
    # Return as dictionary
    return {
        '1d': daily_data,
        '1h': hourly_data,
        '15m': min15_data
    }

@pytest.fixture
def timeframe_data(multi_timeframe_data):
    """
    Create a TimeframeData object if available, otherwise return the dict.
    
    Returns:
        TimeframeData or dict: TimeframeData object or dictionary of dataframes
    """
    try:
        from mtfema_backtester.data.timeframe_data import TimeframeData
        return TimeframeData(multi_timeframe_data)
    except ImportError:
        return multi_timeframe_data

@pytest.fixture
def temp_config_file():
    """
    Create a temporary configuration file for testing.
    
    Returns:
        str: Path to the temporary configuration file
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        # Write test configuration
        config_data = {
            'data': {
                'default_symbol': 'TEST',
                'default_timeframes': ['1d', '1h', '15m'],
                'cache_enabled': False
            },
            'strategy': {
                'ema': {
                    'period': 9,
                    'extension_thresholds': {
                        '1d': 1.0,
                        '1h': 0.5,
                        '15m': 0.3
                    }
                }
            },
            'backtest': {
                'initial_capital': 10000,
                'commission': 0.0,
                'slippage': 0.0
            }
        }
        
        # Write YAML data
        yaml.dump(config_data, tmp, default_flow_style=False)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up
    os.unlink(tmp_path)

@pytest.fixture
def test_config(temp_config_file):
    """
    Create a test configuration manager with the temporary config file.
    
    Returns:
        ConfigManager: Test configuration manager
    """
    return ConfigManager(config_file=temp_config_file)

@pytest.fixture
def reset_config():
    """
    Reset the global configuration manager after the test.
    """
    # Store original instance
    original_instance = ConfigManager._instance
    
    # Yield control to the test
    yield
    
    # Restore original instance
    ConfigManager._instance = original_instance 