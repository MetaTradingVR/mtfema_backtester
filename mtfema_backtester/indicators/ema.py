"""
EMA (Exponential Moving Average) Indicator

This module provides functions for calculating EMAs and detecting extensions
from the EMA.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Try to import talib, but use pandas fallback if not available
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    logger.warning("TA-Lib not available, using pandas for EMA calculations")
    TALIB_AVAILABLE = False

def calculate_ema(data, period=9, column='Close'):
    """
    Calculate Exponential Moving Average
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    period : int
        EMA period
    column : str
        Column to use for calculation
        
    Returns:
    --------
    pandas.Series
        EMA values
    """
    if data is None or data.empty:
        logger.warning("Empty data provided for EMA calculation")
        return pd.Series()
    
    try:
        # Use TA-Lib if available (faster)
        if TALIB_AVAILABLE:
            return pd.Series(
                talib.EMA(data[column].values, timeperiod=period),
                index=data.index
            )
        else:
            # Fallback to pandas EMA
            return data[column].ewm(span=period, adjust=False).mean()
    
    except Exception as e:
        logger.error(f"Error calculating EMA: {str(e)}")
        return pd.Series()

def detect_9ema_extension(data, threshold=0.01, column='Close'):
    """
    Detect if price is extended from 9 EMA
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    threshold : float
        Extension threshold as percentage (0.01 = 1%)
    column : str
        Column to check for extension
        
    Returns:
    --------
    dict
        Extension detection results
    """
    if data is None or data.empty:
        logger.warning("Empty data provided for extension detection")
        return {
            'has_extension': False,
            'extended_up': False,
            'extended_down': False,
            'extension_percentage': 0.0
        }
    
    try:
        # Calculate 9 EMA
        ema9 = calculate_ema(data, period=9, column=column)
        
        # Get the latest values
        latest_price = data[column].iloc[-1]
        latest_ema = ema9.iloc[-1]
        
        # Calculate percentage difference
        percentage_diff = (latest_price - latest_ema) / latest_ema
        
        # Determine extension
        extended_up = percentage_diff > threshold
        extended_down = percentage_diff < -threshold
        has_extension = extended_up or extended_down
        
        return {
            'has_extension': has_extension,
            'extended_up': extended_up,
            'extended_down': extended_down,
            'extension_percentage': abs(percentage_diff) * 100.0,
            'price': latest_price,
            'ema': latest_ema,
            'percentage_diff': percentage_diff * 100.0
        }
    
    except Exception as e:
        logger.error(f"Error detecting EMA extension: {str(e)}")
        return {
            'has_extension': False,
            'extended_up': False,
            'extended_down': False,
            'extension_percentage': 0.0,
            'error': str(e)
        }