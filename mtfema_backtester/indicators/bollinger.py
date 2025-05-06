"""
Bollinger Bands Indicator

This module provides functions for calculating Bollinger Bands and detecting
price breakouts.
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
    logger.warning("TA-Lib not available, using pandas for Bollinger Bands calculations")
    TALIB_AVAILABLE = False

def calculate_bollinger_bands(data, period=20, stdev=2, column='Close'):
    """
    Calculate Bollinger Bands
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    period : int
        Moving average period
    stdev : float
        Standard deviation multiplier
    column : str
        Column to use for calculation
        
    Returns:
    --------
    tuple
        (middle_band, upper_band, lower_band)
    """
    if data is None or data.empty:
        logger.warning("Empty data provided for Bollinger Bands calculation")
        return pd.Series(), pd.Series(), pd.Series()
    
    try:
        if TALIB_AVAILABLE:
            # Use TA-Lib if available
            upper, middle, lower = talib.BBANDS(
                data[column].values,
                timeperiod=period,
                nbdevup=stdev,
                nbdevdn=stdev,
                matype=0  # Simple Moving Average
            )
            
            # Convert to pandas Series
            middle_band = pd.Series(middle, index=data.index)
            upper_band = pd.Series(upper, index=data.index)
            lower_band = pd.Series(lower, index=data.index)
        else:
            # Calculate using pandas
            middle_band = data[column].rolling(window=period).mean()
            std_dev = data[column].rolling(window=period).std()
            upper_band = middle_band + (std_dev * stdev)
            lower_band = middle_band - (std_dev * stdev)
        
        logger.info(f"Calculated Bollinger Bands ({period}, {stdev}) successfully")
        return middle_band, upper_band, lower_band
    
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        return pd.Series(), pd.Series(), pd.Series()

def detect_bollinger_breakouts(data, upper_band, lower_band, column='Close'):
    """
    Detect price breakouts from Bollinger Bands
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    upper_band : pandas.Series
        Upper Bollinger Band
    lower_band : pandas.Series
        Lower Bollinger Band
    column : str
        Column to check for breakouts
        
    Returns:
    --------
    pd.Series
        Breakout signals (1 = upper breakout, -1 = lower breakout, 0 = none)
    """
    if data is None or data.empty:
        logger.warning("Empty data provided for breakout detection")
        return pd.Series()
    
    try:
        # Initialize signals
        signals = pd.Series(0, index=data.index)
        
        # Upper band breakouts (potentially bearish)
        signals[data[column] > upper_band] = 1
        
        # Lower band breakouts (potentially bullish)
        signals[data[column] < lower_band] = -1
        
        logger.info("Detected Bollinger Band breakouts successfully")
        return signals
    
    except Exception as e:
        logger.error(f"Error detecting Bollinger Band breakouts: {str(e)}")
        return pd.Series()

def detect_bollinger_squeeze(bb, threshold=0.1):
    """
    Detect Bollinger Band squeeze (low volatility)
    
    Parameters:
    -----------
    bb : pandas.DataFrame
        Bollinger Bands data with BB_Width column
    threshold : float
        Threshold for squeeze detection
        
    Returns:
    --------
    pandas.Series
        Series with squeeze signals
    """
    if bb is None or bb.empty or 'BB_Width' not in bb.columns:
        logger.warning("Invalid data provided for Bollinger squeeze detection")
        return pd.Series()
    
    try:
        # Calculate rolling 20-day minimum of bandwidth
        min_width = bb['BB_Width'].rolling(window=20).min()
        
        # Identify squeeze conditions
        squeeze = pd.Series(False, index=bb.index, name='BollingerSqueeze')
        squeeze[bb['BB_Width'] <= (min_width + threshold)] = True
        
        logger.info(f"Detected Bollinger squeezes with threshold {threshold}")
        return squeeze
    
    except Exception as e:
        logger.error(f"Error detecting Bollinger squeeze: {str(e)}")
        return pd.Series()
