"""
Extension Detector for the Multi-Timeframe 9 EMA Extension Strategy.
"""
Extension detector module for MT 9 EMA Backtester.

This module provides tools for detecting price extensions from the 9 EMA,
which form the foundation of the MT 9 EMA trading strategy.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from ..utils.performance_monitor import time_operation
from ..utils.strategy_logger import log_strategy_signal

logger = logging.getLogger(__name__)

class ExtensionDetector:
    """
    Detects price extensions from the EMA that are potential trading opportunities.
    
    Features:
    - Adaptive extension thresholds based on volatility
    - Extension state tracking
    - Pullback and reclamation detection
    - Multi-timeframe extension analysis
    """
    
    def __init__(self, ema_period: int = 9, use_adaptive_thresholds: bool = True):
        """
        Initialize the extension detector.
        
        Args:
            ema_period: EMA period to use (default: 9)
            use_adaptive_thresholds: Whether to use volatility-adjusted thresholds
        """
        self.ema_period = ema_period
        self.use_adaptive_thresholds = use_adaptive_thresholds
        
        # Default extension thresholds by timeframe
        self.default_thresholds = {
            '1m': 0.5,  # 0.5 ATR extension for 1-minute
            '5m': 0.6,  # 0.6 ATR extension for 5-minute
            '15m': 0.7, # 0.7 ATR extension for 15-minute
            '30m': 0.8, # 0.8 ATR extension for 30-minute
            '1h': 1.0,  # 1.0 ATR extension for 1-hour
            '4h': 1.2,  # 1.2 ATR extension for 4-hour
            '1d': 1.5,  # 1.5 ATR extension for daily
            '1w': 2.0   # 2.0 ATR extension for weekly
        }
        
        # Lookback periods for different timeframes
        self.lookback_periods = {
            '1m': 60,    # 1 hour
            '5m': 72,    # 6 hours
            '15m': 64,   # 16 hours
            '30m': 48,   # 24 hours
            '1h': 48,    # 48 hours
            '4h': 30,    # 5 days
            '1d': 20,    # 20 days
            '1w': 12     # 12 weeks
        }
        
        logger.info(f"Extension detector initialized with EMA period {ema_period}")
    
    @time_operation
    def detect_extensions(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Detect price extensions from the EMA in the data.
        
        Args:
            df: DataFrame with price data
            timeframe: Timeframe string
            
        Returns:
            DataFrame with extension indicators added
        """
        # Check required columns
        if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            logger.error(f"Required OHLC columns missing for extension detection: {df.columns}")
            return df
        
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        # Calculate the 9 EMA if not already present
        ema_col = f'EMA_{self.ema_period}'
        if ema_col not in result.columns:
            result[ema_col] = self._calculate_ema(result['close'], self.ema_period)
        
        # Calculate ATR for adaptive thresholds
        atr_period = 14  # Standard ATR period
        result['ATR'] = self._calculate_atr(result, atr_period)
        
        # Get extension threshold for this timeframe
        base_threshold = self.default_thresholds.get(timeframe, 1.0)
        
        # Detect extensions using distance from EMA
        result['distance_from_ema'] = result['close'] - result[ema_col]
        result['distance_pct'] = (result['distance_from_ema'] / result[ema_col]) * 100
        
        # Calculate normalized distance (in ATR units)
        result['distance_atr'] = result['distance_from_ema'].abs() / result['ATR']
        
        # Extension threshold in ATR units (can be adaptive based on volatility)
        if self.use_adaptive_thresholds:
            result['threshold'] = self._calculate_adaptive_threshold(result, base_threshold)
        else:
            result['threshold'] = base_threshold
        
        # Flag extensions
        result['extended_up'] = (result['distance_atr'] > result['threshold']) & (result['distance_from_ema'] > 0)
        result['extended_down'] = (result['distance_atr'] > result['threshold']) & (result['distance_from_ema'] < 0)
        result['has_extension'] = result['extended_up'] | result['extended_down']
        
        # Calculate extension percentage
        result['extension_percent'] = result['distance_atr'] / result['threshold'] * 100
        
        # Extension direction (1 for up, -1 for down, 0 for none)
        result['extension_direction'] = np.where(
            result['extended_up'], 1,
            np.where(result['extended_down'], -1, 0)
        )
        
        # Detect state changes (new extensions)
        result['new_extension_up'] = (result['extended_up'] & ~result['extended_up'].shift(1).fillna(False))
        result['new_extension_down'] = (result['extended_down'] & ~result['extended_down'].shift(1).fillna(False))
        result['new_extension'] = result['new_extension_up'] | result['new_extension_down']
        
        # Detect extension endings
        result['extension_end_up'] = (~result['extended_up'] & result['extended_up'].shift(1).fillna(False))
        result['extension_end_down'] = (~result['extended_down'] & result['extended_down'].shift(1).fillna(False))
        result['extension_end'] = result['extension_end_up'] | result['extension_end_down']
        
        # Duration of current extension (in bars)
        result['extension_duration'] = self._calculate_state_duration(result['has_extension'])
        
        # Calculate EMA slope (speed/momentum)
        result['ema_slope'] = self._calculate_slope(result[ema_col])
        
        # Log extension events
        self._log_extension_events(result, timeframe)
        
        return result
    
    @time_operation
    def detect_pullbacks(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Detect pullbacks toward the EMA after extensions.
        
        Args:
            df: DataFrame with price and extension data
            timeframe: Timeframe string
            
        Returns:
            DataFrame with pullback indicators added
        """
        # Check if extension detection has been run
        if not all(col in df.columns for col in ['has_extension', 'extension_direction', 'EMA_9']):
            logger.error("Extension detection must be run before pullback detection")
            return df
        
        # Make a copy
        result = df.copy()
        
        # Calculate pullback condition: price moving back toward EMA after extension
        ema_col = f'EMA_{self.ema_period}'
        
        # Change in distance from EMA (negative means moving toward EMA)
        result['distance_change'] = result['distance_from_ema'] - result['distance_from_ema'].shift(1)
        
        # Normalized change (as percentage of ATR)
        result['distance_change_atr'] = result['distance_change'].abs() / result['ATR']
        
        # Moving toward EMA if distance is decreasing
        result['moving_toward_ema'] = (
            (result['extended_up'] & (result['distance_change'] < 0)) | 
            (result['extended_down'] & (result['distance_change'] > 0))
        )
        
        # Pullback strength (how quickly price is returning to EMA)
        result['pullback_strength'] = result['distance_change_atr'] * result['moving_toward_ema']
        
        # Cumulative pullback from peak extension
        result['pullback_from_peak'] = self._calculate_pullback_from_peak(result)
        
        # Flag significant pullbacks (more than 30% retracement from peak extension)
        result['has_significant_pullback'] = result['pullback_from_peak'] > 0.3
        
        # New significant pullbacks
        result['new_pullback'] = (
            result['has_significant_pullback'] & 
            ~result['has_significant_pullback'].shift(1).fillna(False)
        )
        
        # Distance from EMA as percentage of recent range
        result['relative_position'] = self._calculate_relative_position(result)
        
        # Detect reclaims of EMA after extensions
        self._detect_reclaims(result)
        
        # Log pullback events
        self._log_pullback_events(result, timeframe)
        
        return result
    
    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            series: Price series
            period: EMA period
            
        Returns:
            EMA series
        """
        return series.ewm(span=period, adjust=False).mean()
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range.
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            ATR series
        """
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        return atr
    
    def _calculate_adaptive_threshold(self, df: pd.DataFrame, base_threshold: float) -> pd.Series:
        """
        Calculate adaptive threshold based on recent volatility.
        
        Args:
            df: DataFrame with OHLC and ATR data
            base_threshold: Base threshold in ATR units
            
        Returns:
            Series of adaptive thresholds
        """
        # Calculate volatility ratio (current ATR vs historical average)
        atr = df['ATR']
        avg_atr = atr.rolling(20).mean()
        volatility_ratio = atr / avg_atr.replace(0, np.nan).fillna(1)
        
        # Adjust threshold based on volatility (more volatile = higher threshold)
        adjusted_threshold = base_threshold * np.sqrt(volatility_ratio)
        
        # Ensure threshold doesn't go too low or too high
        adjusted_threshold = adjusted_threshold.clip(base_threshold * 0.7, base_threshold * 1.5)
        
        return adjusted_threshold
    
    def _calculate_state_duration(self, state_series: pd.Series) -> pd.Series:
        """
        Calculate the duration of the current state.
        
        Args:
            state_series: Boolean series indicating state
            
        Returns:
            Series with state duration (in bars)
        """
        # Initialize with zeros
        duration = pd.Series(0, index=state_series.index)
        
        # Calculate cumulative duration for each state
        count = 0
        for i, val in enumerate(state_series):
            if val:
                count += 1
            else:
                count = 0
            duration.iloc[i] = count
            
        return duration
    
    def _calculate_slope(self, series: pd.Series, period: int = 5) -> pd.Series:
        """
        Calculate the slope of a series.
        
        Args:
            series: Input series
            period: Slope calculation period
            
        Returns:
            Slope series
        """
        # Calculate difference between points 'period' bars apart
        change = series - series.shift(period)
        
        # Normalize by period to get average change per bar
        slope = change / period
        
        return slope
    
    def _calculate_pullback_from_peak(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate the pullback percentage from peak extension.
        
        Args:
            df: DataFrame with extension data
            
        Returns:
            Series with pullback percentage (0-1)
        """
        result = pd.Series(0.0, index=df.index)
        
        # Process for upward extensions
        for i in range(1, len(df)):
            if df['extended_up'].iloc[i]:
                # Find peak distance in current extension
                start_idx = i
                while start_idx > 0 and df['extended_up'].iloc[start_idx-1]:
                    start_idx -= 1
                    
                peak_idx = df['distance_from_ema'].iloc[start_idx:i+1].argmax() + start_idx
                peak_distance = df['distance_from_ema'].iloc[peak_idx]
                current_distance = df['distance_from_ema'].iloc[i]
                
                if peak_distance > 0:
                    pullback_pct = (peak_distance - current_distance) / peak_distance
                    result.iloc[i] = max(0, pullback_pct)
        
        # Process for downward extensions
        for i in range(1, len(df)):
            if df['extended_down'].iloc[i]:
                # Find peak negative distance in current extension
                start_idx = i
                while start_idx > 0 and df['extended_down'].iloc[start_idx-1]:
                    start_idx -= 1
                    
                peak_idx = df['distance_from_ema'].iloc[start_idx:i+1].argmin() + start_idx
                peak_distance = abs(df['distance_from_ema'].iloc[peak_idx])
                current_distance = abs(df['distance_from_ema'].iloc[i])
                
                if peak_distance > 0:
                    pullback_pct = (peak_distance - current_distance) / peak_distance
                    result.iloc[i] = max(0, pullback_pct)
        
        return result
    
    def _calculate_relative_position(self, df: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """
        Calculate the relative position within the recent range.
        
        Args:
            df: DataFrame with price data
            lookback: Lookback period for range calculation
            
        Returns:
            Series with relative position (0-1, 0.5 = at EMA)
        """
        ema_col = f'EMA_{self.ema_period}'
        
        # Calculate the distance from EMA as percentage of recent range
        result = pd.Series(0.5, index=df.index)  # Default at EMA
        
        for i in range(lookback, len(df)):
            recent_high = df['high'].iloc[i-lookback:i].max()
            recent_low = df['low'].iloc[i-lookback:i].min()
            recent_range = recent_high - recent_low
            
            if recent_range > 0:
                ema = df[ema_col].iloc[i]
                close = df['close'].iloc[i]
                
                # Position relative to range, centered at EMA
                if close > ema:
                    # Above EMA: scale from 0.5 (at EMA) to 1.0 (at recent high)
                    position = 0.5 + 0.5 * (close - ema) / (recent_high - ema)
                else:
                    # Below EMA: scale from 0.5 (at EMA) to 0.0 (at recent low)
                    position = 0.5 - 0.5 * (ema - close) / (ema - recent_low)
                
                result.iloc[i] = min(1.0, max(0.0, position))
        
        return result
    
    def _detect_reclaims(self, df: pd.DataFrame) -> None:
        """
        Detect reclamations of the EMA after extensions and pullbacks.
        
        Args:
            df: DataFrame with price and extension data
        """
        ema_col = f'EMA_{self.ema_period}'
        
        # Price crossing back above EMA after downward extension
        df['BullishReclaim'] = (
            (df['close'] > df[ema_col]) & 
            (df['close'].shift(1) <= df[ema_col].shift(1)) &
            df['extension_end_down'].shift(1)
        )
        
        # Price crossing back below EMA after upward extension
        df['BearishReclaim'] = (
            (df['close'] < df[ema_col]) & 
            (df['close'].shift(1) >= df[ema_col].shift(1)) &
            df['extension_end_up'].shift(1)
        )
        
        # Any reclaim
        df['has_reclaim'] = df['BullishReclaim'] | df['BearishReclaim']
    
    def _log_extension_events(self, df: pd.DataFrame, timeframe: str) -> None:
        """
        Log extension events for analysis.
        
        Args:
            df: DataFrame with extension indicators
            timeframe: Timeframe string
        """
        # Log new extension events
        for i in range(1, len(df)):
            if df['new_extension_up'].iloc[i]:
                # Log bullish extension
                extension_pct = df['extension_percent'].iloc[i]
                price = df['close'].iloc[i]
                ema = df[f'EMA_{self.ema_period}'].iloc[i]
                atr = df['ATR'].iloc[i]
                
                log_strategy_signal(
                    timeframe=timeframe,
                    direction="BULLISH",
                    reason="Price extended above EMA",
                    price=price,
                    ema=ema,
                    extension_pct=extension_pct,
                    atr=atr,
                    distance_atr=df['distance_atr'].iloc[i],
                    threshold=df['threshold'].iloc[i]
                )
                
            elif df['new_extension_down'].iloc[i]:
                # Log bearish extension
                extension_pct = df['extension_percent'].iloc[i]
                price = df['close'].iloc[i]
                ema = df[f'EMA_{self.ema_period}'].iloc[i]
                atr = df['ATR'].iloc[i]
                
                log_strategy_signal(
                    timeframe=timeframe,
                    direction="BEARISH",
                    reason="Price extended below EMA",
                    price=price,
                    ema=ema,
                    extension_pct=extension_pct,
                    atr=atr,
                    distance_atr=df['distance_atr'].iloc[i],
                    threshold=df['threshold'].iloc[i]
                )
    
    def _log_pullback_events(self, df: pd.DataFrame, timeframe: str) -> None:
        """
        Log pullback events for analysis.
        
        Args:
            df: DataFrame with pullback indicators
            timeframe: Timeframe string
        """
        # Log new significant pullbacks
        for i in range(1, len(df)):
            if df['new_pullback'].iloc[i]:
                direction = "BULLISH" if df['extended_down'].iloc[i] else "BEARISH"
                pullback_pct = df['pullback_from_peak'].iloc[i] * 100
                
                log_strategy_signal(
                    timeframe=timeframe,
                    direction=direction,
                    reason="Significant pullback from extension",
                    price=df['close'].iloc[i],
                    pullback_pct=pullback_pct,
                    relative_position=df['relative_position'].iloc[i]
                )
            
            # Log EMA reclaims
            elif df['BullishReclaim'].iloc[i]:
                log_strategy_signal(
                    timeframe=timeframe,
                    direction="BULLISH",
                    reason="Bullish EMA Reclaim",
                    price=df['close'].iloc[i],
                    ema=df[f'EMA_{self.ema_period}'].iloc[i]
                )
                
            elif df['BearishReclaim'].iloc[i]:
                log_strategy_signal(
                    timeframe=timeframe,
                    direction="BEARISH",
                    reason="Bearish EMA Reclaim",
                    price=df['close'].iloc[i],
                    ema=df[f'EMA_{self.ema_period}'].iloc[i]
                )


# Create a global instance for convenience
_extension_detector = ExtensionDetector()

def get_extension_detector() -> ExtensionDetector:
    """
    Get the global extension detector instance.
    
    Returns:
        ExtensionDetector instance
    """
    return _extension_detector
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
