"""
ZigZag and Fibonacci retracement indicator implementations for MT 9 EMA Backtester.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable, Type
from mtfema_backtester.utils.indicators import Indicator

class ZigZag(Indicator):
    """
    ZigZag indicator for identifying significant market turning points.
    
    This indicator filters out minor price movements and highlights significant
    trends by connecting swing highs and swing lows.
    """
    
    def __init__(self, 
                 deviation: float = 5.0, 
                 depth: int = 12,
                 name: str = None):
        """
        Initialize the ZigZag indicator.
        
        Args:
            deviation: Minimum percentage price movement to register a new pivot point
            depth: Minimum number of bars between pivot points
            name: Optional custom name for this indicator
        """
        params = {
            'deviation': deviation,
            'depth': depth
        }
        super().__init__(name or "ZigZag", params)
        self.required_columns = ['high', 'low']
        
    def _validate_params(self) -> None:
        """
        Validate ZigZag parameters.
        """
        if self.params['deviation'] <= 0:
            raise ValueError("Deviation must be greater than 0")
        if self.params['depth'] < 1:
            raise ValueError("Depth must be at least 1")
    
    def _calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate the ZigZag indicator.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with ZigZag line and pivot points
        """
        deviation = self.params['deviation'] / 100.0  # Convert percentage to decimal
        depth = self.params['depth']
        
        # Initialize arrays
        highs = data['high'].values
        lows = data['low'].values
        dates = data.index
        n = len(data)
        
        # Arrays to track turning points
        zigzag = np.zeros(n)
        direction = np.zeros(n)  # 1 for uptrend, -1 for downtrend
        
        # Find initial direction
        if n <= depth:
            return {'line': pd.Series(zigzag, index=data.index)}
        
        # Initialize with a starting point
        last_high_idx = 0
        last_low_idx = 0
        last_high = highs[0]
        last_low = lows[0]
        
        # Set initial trend direction (1 for up, -1 for down)
        if highs[depth] > highs[0]:
            direction[0] = 1
            zigzag[0] = lows[0]
        else:
            direction[0] = -1
            zigzag[0] = highs[0]
        
        # Identify turning points
        for i in range(1, n):
            # Update potential high and low points
            if highs[i] > last_high:
                last_high = highs[i]
                last_high_idx = i
            if lows[i] < last_low:
                last_low = lows[i]
                last_low_idx = i
            
            # Check for trend reversal - Down to Up
            if direction[i-1] == -1:  # Coming from a downtrend
                if highs[i] > last_high * (1 + deviation) and i - last_low_idx >= depth:
                    # Confirmed reversal to uptrend
                    direction[i] = 1
                    zigzag[last_low_idx] = last_low
                    # Reset tracking variables
                    last_high = highs[i]
                    last_high_idx = i
                else:
                    direction[i] = direction[i-1]
            
            # Check for trend reversal - Up to Down
            elif direction[i-1] == 1:  # Coming from an uptrend
                if lows[i] < last_low * (1 - deviation) and i - last_high_idx >= depth:
                    # Confirmed reversal to downtrend
                    direction[i] = -1
                    zigzag[last_high_idx] = last_high
                    # Reset tracking variables
                    last_low = lows[i]
                    last_low_idx = i
                else:
                    direction[i] = direction[i-1]
            else:
                direction[i] = direction[i-1]
        
        # Clean up zigzag line (connecting the dots)
        pivots = np.where(zigzag != 0)[0]
        if len(pivots) < 2:
            return {'line': pd.Series(zigzag, index=data.index)}
        
        # Connect pivot points with straight lines
        for i in range(len(pivots)-1):
            start_idx = pivots[i]
            end_idx = pivots[i+1]
            start_val = zigzag[start_idx]
            end_val = zigzag[end_idx]
            
            # Linear interpolation between pivot points
            if end_idx > start_idx + 1:
                slope = (end_val - start_val) / (end_idx - start_idx)
                for j in range(start_idx + 1, end_idx):
                    zigzag[j] = start_val + slope * (j - start_idx)
        
        # Create pivot point series for easy plotting
        pivot_points = pd.Series(index=data.index, dtype=float)
        pivot_points[pivots] = zigzag[pivots]
        
        # Create direction series
        trend_direction = pd.Series(direction, index=data.index)
        
        return {
            'line': pd.Series(zigzag, index=data.index),
            'pivots': pivot_points,
            'direction': trend_direction
        }


class FibRetracement(Indicator):
    """
    Fibonacci Retracement indicator.
    
    Calculates Fibonacci retracement levels between significant swing highs and lows.
    Typically used with ZigZag indicator to identify potential support/resistance levels.
    """
    
    def __init__(self, 
                 levels: List[float] = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0],
                 extension_levels: List[float] = [1.272, 1.618, 2.618],
                 use_zigzag: bool = True,
                 zigzag_deviation: float = 5.0,
                 zigzag_depth: int = 12,
                 lookback_periods: int = 2,  # Number of swing points to use
                 name: str = None):
        """
        Initialize the Fibonacci Retracement indicator.
        
        Args:
            levels: List of Fibonacci retracement levels to calculate
            extension_levels: List of Fibonacci extension levels to calculate
            use_zigzag: Whether to use ZigZag to find swing points
            zigzag_deviation: Deviation parameter for ZigZag if used
            zigzag_depth: Depth parameter for ZigZag if used
            lookback_periods: Number of swing periods to consider
            name: Optional custom name for this indicator
        """
        params = {
            'levels': levels,
            'extension_levels': extension_levels,
            'use_zigzag': use_zigzag,
            'zigzag_deviation': zigzag_deviation,
            'zigzag_depth': zigzag_depth,
            'lookback_periods': lookback_periods
        }
        super().__init__(name or "FibRetracement", params)
        self.required_columns = ['high', 'low', 'close']
    
    def _validate_params(self) -> None:
        """
        Validate Fibonacci Retracement parameters.
        """
        if not all(0 <= level <= 1 for level in self.params['levels']):
            raise ValueError("Retracement levels must be between 0 and 1")
    
    def _calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate Fibonacci retracement and extension levels.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with retracement and extension levels
        """
        # Get parameters
        levels = self.params['levels']
        extension_levels = self.params['extension_levels']
        use_zigzag = self.params['use_zigzag']
        zigzag_deviation = self.params['zigzag_deviation']
        zigzag_depth = self.params['zigzag_depth']
        lookback_periods = self.params['lookback_periods']
        
        n = len(data)
        if n < zigzag_depth * 2:
            # Not enough data for meaningful analysis
            empty_series = pd.Series(index=data.index, dtype=float)
            return {f'level_{level:.3f}': empty_series for level in levels}
        
        # Find swing highs and lows using ZigZag if requested
        if use_zigzag:
            # Create ZigZag indicator
            zigzag = ZigZag(deviation=zigzag_deviation, depth=zigzag_depth)
            zigzag_result = zigzag.calculate(data)
            
            # Extract pivot points
            pivot_points = zigzag_result['pivots'].dropna()
            if len(pivot_points) < 2:
                # Not enough pivot points for analysis
                empty_series = pd.Series(index=data.index, dtype=float)
                return {f'level_{level:.3f}': empty_series for level in levels}
            
            # Get latest swing points based on lookback_periods
            pivot_indices = pivot_points.index[-lookback_periods-1:] 
            if len(pivot_indices) < 2:
                # Not enough pivot points for analysis
                empty_series = pd.Series(index=data.index, dtype=float)
                return {f'level_{level:.3f}': empty_series for level in levels}
            
            # Get swing high and low values
            swing_values = pivot_points[pivot_indices].values
            
            # Determine if currently in uptrend or downtrend
            current_direction = 1 if swing_values[-1] > swing_values[-2] else -1
            
            # High and low points for retracement calculation
            if current_direction == 1:  # Uptrend, from low to high
                low_value = swing_values[-2]
                high_value = swing_values[-1]
            else:  # Downtrend, from high to low
                high_value = swing_values[-2]
                low_value = swing_values[-1]
        else:
            # Use simple high/low method for finding swing points
            lookback = min(n, 100)  # Limit lookback to prevent excessive computation
            high_value = data['high'][-lookback:].max()
            low_value = data['low'][-lookback:].min()
            
            # Determine direction based on recent prices
            current_direction = 1 if data['close'].iloc[-1] > data['close'].iloc[-lookback//2] else -1
        
        # Price range for calculations
        price_range = high_value - low_value
        
        # Calculate retracement levels
        retracement_levels = {}
        for level in levels:
            if current_direction == 1:  # Uptrend retracements (move down from high)
                level_price = high_value - (price_range * level)
            else:  # Downtrend retracements (move up from low)
                level_price = low_value + (price_range * level)
            
            # Create a series with the level value for all dates since the last pivot
            level_series = pd.Series(index=data.index, dtype=float)
            if use_zigzag and len(pivot_indices) >= 2:
                start_idx = data.index.get_loc(pivot_indices[-2])
                level_series.iloc[start_idx:] = level_price
            else:
                level_series.iloc[-lookback:] = level_price
            
            retracement_levels[f'level_{level:.3f}'] = level_series
        
        # Calculate extension levels
        extension_level_results = {}
        for ext_level in extension_levels:
            if current_direction == 1:  # Uptrend extensions (move up beyond high)
                ext_price = high_value + (price_range * ext_level)
            else:  # Downtrend extensions (move down beyond low)
                ext_price = low_value - (price_range * ext_level)
            
            # Create a series with the extension level value
            ext_level_series = pd.Series(index=data.index, dtype=float)
            if use_zigzag and len(pivot_indices) >= 2:
                start_idx = data.index.get_loc(pivot_indices[-2])
                ext_level_series.iloc[start_idx:] = ext_price
            else:
                ext_level_series.iloc[-lookback:] = ext_price
            
            extension_level_results[f'extension_{ext_level:.3f}'] = ext_level_series
        
        # Return combined results
        result = {}
        result.update(retracement_levels)
        result.update(extension_level_results)
        
        # Add swing points for reference
        if use_zigzag:
            result['swing_high'] = pd.Series(index=data.index, dtype=float)
            result['swing_low'] = pd.Series(index=data.index, dtype=float)
            
            for idx, val in pivot_points.items():
                if zigzag_result['direction'][idx] == 1:  # Direction changing to up, so this is a low
                    result['swing_low'][idx] = val
                elif zigzag_result['direction'][idx] == -1:  # Direction changing to down, so this is a high
                    result['swing_high'][idx] = val
        
        return result
