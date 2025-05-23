"""
Pullback Validator for the Multi-Timeframe 9 EMA Extension Strategy.

This module implements the logic for validating pullbacks after EMA reclamations,
using Fibonacci retracement levels according to the strategy specification.
"""

import pandas as pd
import numpy as np
import logging

from mtfema_backtester.config import STRATEGY_PARAMS

logger = logging.getLogger(__name__)

class PullbackValidator:
    """
    Validates pullbacks after EMA reclamations using Fibonacci retracement levels.
    """
    
    def __init__(self, fibonacci_zone=None):
        """
        Initialize the PullbackValidator
        
        Parameters:
        -----------
        fibonacci_zone : tuple, optional
            Fibonacci zone (min, max) for valid pullbacks
            Default is taken from STRATEGY_PARAMS
        """
        self.fibonacci_zone = fibonacci_zone or STRATEGY_PARAMS['fibonacci']['pullback_zone']
        logger.info(f"PullbackValidator initialized with Fibonacci zone {self.fibonacci_zone}")
    
    def validate_pullback(self, data, reclamation_index, direction, ema_series):
        """
        Validate a pullback after EMA reclamation using Fibonacci retracement logic.

        Timestamp: 2025-05-06 PST
        Reference: See 'Pullback Entry Logic' in strategy_playbook.md (Section 3.3)

        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns.
        reclamation_index : int
            Index where EMA reclamation occurred.
        direction : str
            Direction of trade ('long' or 'short').
        ema_series : pandas.Series
            9 EMA values.

        Returns:
        --------
        dict
            Validation result with details:
            - valid: bool, whether pullback is valid
            - is_in_fib_zone: bool, price in 50-61.8% retracement zone
            - higher_low/lower_high: bool, structure confirmation
            - bullish_candle/bearish_candle: bool, candle confirmation
            - fib_levels: dict, key Fibonacci levels
            - current_low/current_high: float, price tested
            - swing_low/swing_high: float, reference swing
            - reclamation_ema: float, EMA at reclamation
            - pullback_ratio: float, retracement ratio

        Usage Example:
        --------------
        >>> validator = PullbackValidator()
        >>> result = validator.validate_pullback(data, reclamation_index, 'long', ema_series)
        >>> if result['valid']:
        ...     print('Valid bullish pullback detected!')

        >>> result = validator.validate_pullback(data, reclamation_index, 'short', ema_series)
        >>> if result['valid']:
        ...     print('Valid bearish pullback detected!')

        Edge Cases:
        -----------
        - Returns valid=False if insufficient data for lookback or future bar.
        - Handles division by zero if range is zero.
        - All logic branches are unit tested (see tests/strategy/test_pullback_validator.py).
        """
        is_long = direction == 'long'
        lookback_bars = 10  # Bars to look back for swing high/low
        
        # Ensure we have enough data
        if reclamation_index < lookback_bars or reclamation_index >= len(data) - 1:
            return {
                'valid': False,
                'reason': 'Insufficient data for pullback validation'
            }
        
        # Extract relevant price ranges around reclamation
        reclamation_section = data.iloc[reclamation_index-lookback_bars:reclamation_index+1]
        
        # Get EMA at reclamation
        reclamation_ema = ema_series.iloc[reclamation_index]
        
        # Get Fibonacci levels from configuration
        if len(self.fibonacci_zone) == 2:
            fib_min, fib_max = self.fibonacci_zone
        else:
            # Fallback to default values
            fib_min, fib_max = 0.382, 0.618
            logger.warning(f"Invalid fibonacci_zone format: {self.fibonacci_zone}. Using defaults: {fib_min}, {fib_max}")
        
        # Find swing points
        if is_long:
            # For long trades after bullish reclamation
            # Find recent swing low before reclamation
            swing_low = reclamation_section['Low'].min()
            swing_low_idx = reclamation_section['Low'].idxmin()
            
            # Calculate Fibonacci retracement levels (bullish case)
            range_size = reclamation_ema - swing_low
            # Use config values instead of hardcoded values
            fib_min_level = reclamation_ema - (range_size * fib_min)
            fib_max_level = reclamation_ema - (range_size * fib_max)
            
            # Check for pullback to Fibonacci zone
            current_low = data.iloc[reclamation_index+1]['Low']
            
            # Ensure correct order (min_price should be larger in bullish case)
            if fib_min_level < fib_max_level:
                fib_min_level, fib_max_level = fib_max_level, fib_min_level
            
            is_in_fib_zone = (current_low <= fib_min_level and current_low >= fib_max_level)
            higher_low = current_low > swing_low
            bullish_candle = data.iloc[reclamation_index+1]['Close'] > data.iloc[reclamation_index+1]['Open']
            
            return {
                'valid': is_in_fib_zone and higher_low and bullish_candle,
                'is_in_fib_zone': is_in_fib_zone,
                'higher_low': higher_low,
                'bullish_candle': bullish_candle,
                'fib_levels': {
                    '0.000': swing_low,
                    str(fib_min): fib_min_level,
                    str(fib_max): fib_max_level,
                    '1.000': reclamation_ema
                },
                'current_low': current_low,
                'swing_low': swing_low,
                'reclamation_ema': reclamation_ema,
                'pullback_ratio': (reclamation_ema - current_low) / range_size if range_size > 0 else 0
            }
        else:
            # For short trades after bearish reclamation
            # Find recent swing high before reclamation
            swing_high = reclamation_section['High'].max()
            swing_high_idx = reclamation_section['High'].idxmax()
            
            # Calculate Fibonacci retracement levels (bearish case)
            range_size = swing_high - reclamation_ema
            # Use config values instead of hardcoded values
            fib_min_level = reclamation_ema + (range_size * fib_min)
            fib_max_level = reclamation_ema + (range_size * fib_max)
            
            # Check for pullback to Fibonacci zone
            current_high = data.iloc[reclamation_index+1]['High']
            
            # Ensure correct order (min_price should be smaller in bearish case)
            if fib_min_level > fib_max_level:
                fib_min_level, fib_max_level = fib_max_level, fib_min_level
            
            is_in_fib_zone = (current_high >= fib_min_level and current_high <= fib_max_level)
            lower_high = current_high < swing_high
            bearish_candle = data.iloc[reclamation_index+1]['Close'] < data.iloc[reclamation_index+1]['Open']
            
            return {
                'valid': is_in_fib_zone and lower_high and bearish_candle,
                'is_in_fib_zone': is_in_fib_zone,
                'lower_high': lower_high,
                'bearish_candle': bearish_candle,
                'fib_levels': {
                    '0.000': reclamation_ema,
                    str(fib_min): fib_min_level,
                    str(fib_max): fib_max_level,
                    '1.000': swing_high
                },
                'current_high': current_high,
                'swing_high': swing_high,
                'reclamation_ema': reclamation_ema,
                'pullback_ratio': (current_high - reclamation_ema) / range_size if range_size > 0 else 0
            }
    
    def wait_for_pullback(self, data, reclamation_index, direction, ema_series, max_bars=5):
        """
        Wait for a valid pullback within a specified number of bars
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        reclamation_index : int
            Index where EMA reclamation occurred
        direction : str
            Direction of trade ('long' or 'short')
        ema_series : pandas.Series
            9 EMA values
        max_bars : int
            Maximum number of bars to wait for pullback
            
        Returns:
        --------
        dict
            Validation result with details including bar offset
        """
        is_long = direction == 'long'
        
        # Check several bars after reclamation
        for i in range(1, min(max_bars+1, len(data) - reclamation_index)):
            # Calculate the validation for this bar
            validation = self.validate_pullback(
                data, 
                reclamation_index, 
                direction, 
                ema_series
            )
            
            # If valid pullback found, return with offset
            if validation['valid']:
                validation['bar_offset'] = i
                return validation
            
            # For the next iteration, adjust reclamation index to check next bar
            reclamation_index += 1
        
        # No valid pullback found within max_bars
        return {
            'valid': False,
            'reason': f'No valid pullback within {max_bars} bars',
            'bar_offset': None
        }

def validate_pullback(data, reclamation_data, direction, ema_series=None):
    """
    Validate a pullback after EMA reclamation
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    reclamation_data : dict
        Reclamation data from reclamation_detector
    direction : str
        Direction of trade ('long' or 'short')
    ema_series : pandas.Series, optional
        9 EMA values (will be calculated if not provided)
        
    Returns:
    --------
    dict
        Validation result with details
    """
    # Create validator instance
    validator = PullbackValidator()
    
    # Get reclamation index
    reclamation_index = reclamation_data.get('reclamation_index', None)
    if reclamation_index is None:
        return {'valid': False, 'reason': 'No reclamation index provided'}
    
    # Get or calculate EMA if not provided
    if ema_series is None:
        if 'EMA_9' in data.columns:
            ema_series = data['EMA_9']
        else:
            # Try to calculate EMA
            try:
                import talib
                ema_series = pd.Series(
                    talib.EMA(data['Close'].values, timeperiod=9),
                    index=data.index
                )
            except ImportError:
                import pandas_ta as ta
                ema_series = ta.ema(data['Close'], length=9)
    
    # Validate pullback
    return validator.wait_for_pullback(
        data, 
        reclamation_index, 
        direction, 
        ema_series
    ) 