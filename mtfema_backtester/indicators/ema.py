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

def detect_9ema_extension(data, ema_period=9, threshold=0.01, column='Close'):
    """
    Detect if price is extended from EMA
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    ema_period : int
        EMA period (default: 9)
    threshold : float
        Extension threshold as percentage (0.01 = 1%)
    column : str
        Column to check for extension
        
    Returns:
    --------
    tuple
        (ema_series, extension_series, signals_dict)
    """
    if data is None or len(data) == 0:
        logger.warning("Empty data provided for extension detection")
        return pd.Series(), pd.Series(), {
            'has_extension': False,
            'extended_up': False,
            'extended_down': False,
            'extension_percentage': 0.0
        }
    
    try:
        # Calculate EMA
        ema_series = calculate_ema(data, period=ema_period, column=column)
        
        # Calculate extension percentage
        extension_pct = (data[column] - ema_series) / ema_series * 100.0
        
        # Get the latest values
        latest_price = data[column].iloc[-1]
        latest_ema = ema_series.iloc[-1]
        latest_extension = extension_pct.iloc[-1]
        
        # Determine extension (convert to primitive types to avoid Series truth value ambiguity)
        latest_extension_value = latest_extension
        if isinstance(latest_extension, pd.Series):
            latest_extension_value = latest_extension.iloc[0]
        extended_up = latest_extension_value > threshold * 100
        extended_down = latest_extension_value < -threshold * 100
        has_extension = extended_up or extended_down
        
        # Convert any Series to scalar values
        latest_price_value = latest_price
        if isinstance(latest_price, pd.Series):
            latest_price_value = latest_price.iloc[0]
            
        latest_ema_value = latest_ema
        if isinstance(latest_ema, pd.Series):
            latest_ema_value = latest_ema.iloc[0]
        
        signals = {
            'has_extension': bool(has_extension),
            'extended_up': bool(extended_up),
            'extended_down': bool(extended_down),
            'extension_percentage': abs(latest_extension_value),
            'price': latest_price_value,
            'ema': latest_ema_value,
            'percentage_diff': latest_extension_value
        }
        
        return ema_series, extension_pct, signals
    
    except Exception as e:
        logger.error(f"Error detecting EMA extension: {str(e)}")
        return pd.Series(), pd.Series(), {
            'has_extension': False,
            'extended_up': False,
            'extended_down': False,
            'extension_percentage': 0.0,
            'error': str(e)
        }