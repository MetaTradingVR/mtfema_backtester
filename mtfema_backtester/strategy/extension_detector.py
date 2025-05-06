"""
Extension Detector for the Multi-Timeframe 9 EMA Extension Strategy.

This module detects when price has extended significantly from its 9 EMA,
which is a core concept of the strategy.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def get_extension_threshold(timeframe):
    """
    Get extension threshold percentage for a given timeframe
    
    Parameters:
    -----------
    timeframe : str
        Timeframe string (e.g., '1m', '5m', '15m', '1h')
        
    Returns:
    --------
    float
        Extension threshold as percentage (0.01 = 1%)
    """
    # Default thresholds based on timeframe
    thresholds = {
        '1m': 0.0025,  # 0.25%
        '5m': 0.005,   # 0.5%
        '10m': 0.006,  # 0.6%
        '15m': 0.007,  # 0.7%
        '30m': 0.009,  # 0.9%
        '1h': 0.011,   # 1.1%
        '2h': 0.013,   # 1.3%
        '4h': 0.017,   # 1.7%
        '1d': 0.022,   # 2.2%
        '1w': 0.035,   # 3.5%
    }
    
    # Return threshold for timeframe or default value if not found
    return thresholds.get(timeframe, 0.01)  # Default 1%

def detect_extensions(data, timeframe, ema_period=9, threshold=None, column='Close'):
    """
    Detect price extensions from EMA
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns and EMA_9 if available
    timeframe : str
        Timeframe string used for appropriate threshold selection
    ema_period : int
        EMA period (default 9)
    threshold : float or None
        Extension threshold override (if None, use timeframe-based value)
    column : str
        Column to check for extension
        
    Returns:
    --------
    dict
        Extension detection results
    """
    if data is None or data.empty:
        logger.warning(f"Empty data provided for extension detection ({timeframe})")
        return {
            'has_extension': False,
            'extended_up': False,
            'extended_down': False,
            'extension_percentage': 0.0,
            'timeframe': timeframe
        }
    
    try:
        # Get threshold if not provided
        if threshold is None:
            threshold = get_extension_threshold(timeframe)
            
        # Get or calculate 9 EMA if not in dataframe    
        ema_col = f'EMA_{ema_period}'
        if ema_col not in data.columns:
            logger.warning(f"EMA_{ema_period} not in data columns, calculating")
            # Calculate EMA using pandas
            ema = data[column].ewm(span=ema_period, adjust=False).mean()
        else:
            ema = data[ema_col]
        
        # Get latest values
        latest_idx = len(data) - 1
        latest_price = data[column].iloc[latest_idx]
        latest_ema = ema.iloc[latest_idx]
        
        # Calculate percentage difference
        percentage_diff = (latest_price - latest_ema) / latest_ema
        abs_percentage = abs(percentage_diff)
        
        # Upper extension (price above EMA)
        extended_up = percentage_diff > threshold
        
        # Lower extension (price below EMA)
        extended_down = percentage_diff < -threshold
        
        # Determine if we have an extension
        has_extension = extended_up or extended_down
        
        result = {
            'has_extension': has_extension,
            'extended_up': extended_up,
            'extended_down': extended_down,
            'extension_percentage': abs_percentage * 100.0,
            'price': latest_price,
            'ema': latest_ema,
            'percentage_diff': percentage_diff * 100.0,
            'timeframe': timeframe,
            'threshold': threshold * 100.0
        }
        
        if has_extension:
            direction = 'upward' if extended_up else 'downward'
            logger.info(f"Detected {direction} extension on {timeframe}: {abs_percentage*100:.2f}% (threshold: {threshold*100:.2f}%)")
        
        return result
    
    except Exception as e:
        logger.error(f"Error detecting extensions on {timeframe}: {str(e)}")
        return {
            'has_extension': False,
            'extended_up': False, 
            'extended_down': False,
            'extension_percentage': 0.0,
            'timeframe': timeframe,
            'error': str(e)
        }

def check_extension_across_timeframes(data_dict, timeframes=None, thresholds=None):
    """
    Check for extensions across multiple timeframes
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes by timeframe
    timeframes : list or None
        List of timeframes to check (if None, use all keys in data_dict)
    thresholds : dict or None
        Dictionary of threshold overrides by timeframe
        
    Returns:
    --------
    dict
        Dictionary of extension results by timeframe
    """
    if timeframes is None:
        timeframes = list(data_dict.keys())
    
    if thresholds is None:
        thresholds = {}
    
    results = {}
    
    for tf in timeframes:
        if tf in data_dict:
            threshold = thresholds.get(tf, None)
            results[tf] = detect_extensions(data_dict[tf], tf, threshold=threshold)
    
    return results
