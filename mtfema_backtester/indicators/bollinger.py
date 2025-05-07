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

def calculate_bollinger_bands(data, period=20, std_dev=2, column='Close'):
    """
    Calculate Bollinger Bands
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    period : int
        Moving average period
    std_dev : float
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
                nbdevup=std_dev,
                nbdevdn=std_dev,
                matype=0  # Simple Moving Average
            )
            
            # Convert to pandas Series
            middle_band = pd.Series(middle, index=data.index)
            upper_band = pd.Series(upper, index=data.index)
            lower_band = pd.Series(lower, index=data.index)
        else:
            # Calculate using pandas
            middle_band = data[column].rolling(window=period).mean()
            std_dev_val = data[column].rolling(window=period).std()
            upper_band = middle_band + (std_dev_val * std_dev)
            lower_band = middle_band - (std_dev_val * std_dev)
        
        logger.info(f"Calculated Bollinger Bands ({period}, {std_dev}) successfully")
        return middle_band, upper_band, lower_band
    
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        return pd.Series(), pd.Series(), pd.Series()

def detect_bollinger_breakouts(data, upper_band, lower_band, symbol=None, price_col='Close'):
    """
    Detect breakouts of Bollinger Bands
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    upper_band : pandas.Series
        Upper Bollinger Band
    lower_band : pandas.Series
        Lower Bollinger Band
    symbol : str, optional
        Symbol for multi-symbol data
    price_col : str
        Column to use for price comparison
        
    Returns:
    --------
    pandas.Series
        Signal series (1 for breakout up, -1 for breakout down, 0 for no breakout)
    """
    try:
        if data is None or data.empty:
            logger.warning("Empty data provided for Bollinger Band breakout detection")
            return pd.Series()
            
        # Ensure data is 1-dimensional
        price_data = data[price_col]
        if hasattr(price_data, 'values'):
            price_values = price_data.values
            if len(price_values.shape) > 1:
                price_values = price_values.flatten()
        else:
            price_values = price_data
            
        # Ensure upper_band is 1-dimensional
        if hasattr(upper_band, 'values'):
            upper_values = upper_band.values
            if len(upper_values.shape) > 1:
                upper_values = upper_values.flatten()
        else:
            upper_values = upper_band
            
        # Ensure lower_band is 1-dimensional
        if hasattr(lower_band, 'values'):
            lower_values = lower_band.values
            if len(lower_values.shape) > 1:
                lower_values = lower_values.flatten()
        else:
            lower_values = lower_band
        
        # Check dimensions
        if len(price_values) != len(upper_values) or len(price_values) != len(lower_values):
            logger.warning(f"Dimension mismatch: Price {len(price_values)}, Upper {len(upper_values)}, Lower {len(lower_values)}")
            # Try to align by index if possible
            if hasattr(price_data, 'index') and hasattr(upper_band, 'index') and hasattr(lower_band, 'index'):
                common_index = price_data.index.intersection(upper_band.index).intersection(lower_band.index)
                price_values = price_data.loc[common_index].values
                upper_values = upper_band.loc[common_index].values
                lower_values = lower_band.loc[common_index].values
            else:
                # Truncate to the shortest length
                min_len = min(len(price_values), len(upper_values), len(lower_values))
                price_values = price_values[:min_len]
                upper_values = upper_values[:min_len]
                lower_values = lower_values[:min_len]
        
        # Create signals
        signals = np.zeros(len(price_values))
        
        # Breakout up when price > upper band
        signals[price_values > upper_values] = 1
        
        # Breakout down when price < lower band
        signals[price_values < lower_values] = -1
        
        # Create a Series with the data index
        result = pd.Series(signals, index=data.index[:len(signals)])
        return result
        
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
