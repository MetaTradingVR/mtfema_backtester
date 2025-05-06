"""
ZigZag indicator for identifying significant market swing points
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ZigZag:
    """
    ZigZag indicator implementation for detecting significant
    market swing points (highs and lows)
    """
    
    def __init__(self, depth=5, deviation=5.0, backstep=3):
        """
        Initialize the ZigZag indicator
        
        Parameters:
        -----------
        depth : int
            Minimum number of bars between pivot points
        deviation : float
            Minimum percentage deviation for a new pivot
        backstep : int
            Number of bars to wait before identifying a new pivot
        """
        self.depth = depth
        self.deviation = deviation / 100.0  # Convert to decimal
        self.backstep = backstep
        logger.info(f"ZigZag initialized with depth={depth}, "
                   f"deviation={deviation}%, backstep={backstep}")
    
    def calculate(self, data, high_col='High', low_col='Low'):
        """
        Calculate the ZigZag indicator to identify significant swing points
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        high_col : str
            Column name for high prices
        low_col : str
            Column name for low prices
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with ZigZag values and swing points
        """
        if data is None or len(data) < self.depth:
            logger.warning("Insufficient data for ZigZag calculation")
            return pd.DataFrame()
        
        try:
            # Extract price data
            high = data[high_col].values
            low = data[low_col].values
            
            # Initialize arrays
            zigzag = np.zeros(len(data))
            swing_high = np.zeros(len(data), dtype=bool)
            swing_low = np.zeros(len(data), dtype=bool)
            
            # Initial values
            trend = 0  # 0=undefined, 1=up, -1=down
            last_high_idx = 0
            last_low_idx = 0
            last_high_price = high[0]
            last_low_price = low[0]
            
            # Find initial trend
            for i in range(1, self.depth):
                if high[i] > last_high_price:
                    last_high_price = high[i]
                    last_high_idx = i
                if low[i] < last_low_price:
                    last_low_price = low[i]
                    last_low_idx = i
            
            if last_high_idx > last_low_idx:
                trend = 1
                zigzag[last_low_idx] = low[last_low_idx]
                swing_low[last_low_idx] = True
            else:
                trend = -1
                zigzag[last_high_idx] = high[last_high_idx]
                swing_high[last_high_idx] = True
            
            # Loop through the remaining data
            for i in range(self.depth, len(data)):
                # Uptrend: Look for higher highs or reversal
                if trend == 1:
                    # New higher high
                    if high[i] > last_high_price:
                        last_high_price = high[i]
                        last_high_idx = i
                    # Potential reversal: check if price drops enough from last high
                    elif low[i] < last_low_price or low[i] < (last_high_price * (1 - self.deviation)):
                        # Confirm reversal with backstep
                        if i >= last_high_idx + self.backstep:
                            # Mark the high point
                            zigzag[last_high_idx] = high[last_high_idx]
                            swing_high[last_high_idx] = True
                            
                            # Start new downtrend
                            trend = -1
                            last_low_price = low[i]
                            last_low_idx = i
                
                # Downtrend: Look for lower lows or reversal
                elif trend == -1:
                    # New lower low
                    if low[i] < last_low_price:
                        last_low_price = low[i]
                        last_low_idx = i
                    # Potential reversal: check if price rises enough from last low
                    elif high[i] > last_high_price or high[i] > (last_low_price * (1 + self.deviation)):
                        # Confirm reversal with backstep
                        if i >= last_low_idx + self.backstep:
                            # Mark the low point
                            zigzag[last_low_idx] = low[last_low_idx]
                            swing_low[last_low_idx] = True
                            
                            # Start new uptrend
                            trend = 1
                            last_high_price = high[i]
                            last_high_idx = i
            
            # Mark the last pivot point
            if trend == 1 and last_high_idx > 0:
                zigzag[last_high_idx] = high[last_high_idx]
                swing_high[last_high_idx] = True
            elif trend == -1 and last_low_idx > 0:
                zigzag[last_low_idx] = low[last_low_idx]
                swing_low[last_low_idx] = True
            
            # Create result DataFrame
            result = pd.DataFrame(index=data.index)
            result['ZigZag'] = zigzag
            result['SwingHigh'] = swing_high
            result['SwingLow'] = swing_low
            
            # Add swing point classification
            result['HigherHigh'] = False
            result['LowerHigh'] = False
            result['HigherLow'] = False
            result['LowerLow'] = False
            
            # Find all swing points
            swing_points = []
            
            for i in range(len(data)):
                if swing_high[i] or swing_low[i]:
                    if swing_high[i]:
                        swing_type = "high"
                        price = high[i]
                    else:
                        swing_type = "low"
                        price = low[i]
                        
                    swing_points.append({
                        'index': i,
                        'price': price,
                        'type': swing_type,
                        'time': data.index[i]
                    })
            
            # Classify swing points
            for i in range(1, len(swing_points)):
                curr = swing_points[i]
                prev = swing_points[i-1]
                
                if curr['type'] == "high" and prev['type'] == "high":
                    if curr['price'] > prev['price']:
                        result.loc[result.index[curr['index']], 'HigherHigh'] = True
                    else:
                        result.loc[result.index[curr['index']], 'LowerHigh'] = True
                
                elif curr['type'] == "low" and prev['type'] == "low":
                    if curr['price'] > prev['price']:
                        result.loc[result.index[curr['index']], 'HigherLow'] = True
                    else:
                        result.loc[result.index[curr['index']], 'LowerLow'] = True
            
            logger.info(f"ZigZag calculation found {len(swing_points)} swing points")
            return result
        
        except Exception as e:
            logger.error(f"Error calculating ZigZag: {str(e)}")
            return pd.DataFrame()
    
    def get_swing_points(self, data, zigzag_data=None, high_col='High', low_col='Low'):
        """
        Extract swing points from price data
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        zigzag_data : pandas.DataFrame, optional
            Pre-calculated ZigZag data. If None, it will be calculated.
        high_col : str
            Column name for high prices
        low_col : str
            Column name for low prices
            
        Returns:
        --------
        list
            List of SwingPoint objects with properties:
            - index: Bar index
            - price: Price level
            - type: 'high' or 'low'
            - time: Timestamp
            - is_higher_high, is_lower_high, is_higher_low, is_lower_low: Boolean flags
        """
        if zigzag_data is None:
            zigzag_data = self.calculate(data, high_col, low_col)
        
        if zigzag_data.empty:
            return []
        
        # Extract swing points
        swing_points = []
        
        for i in range(len(data)):
            if zigzag_data['SwingHigh'].iloc[i] or zigzag_data['SwingLow'].iloc[i]:
                swing_type = "high" if zigzag_data['SwingHigh'].iloc[i] else "low"
                price = data[high_col].iloc[i] if swing_type == "high" else data[low_col].iloc[i]
                
                swing_point = {
                    'index': i,
                    'price': price,
                    'type': swing_type,
                    'time': data.index[i],
                    'is_higher_high': zigzag_data['HigherHigh'].iloc[i],
                    'is_lower_high': zigzag_data['LowerHigh'].iloc[i],
                    'is_higher_low': zigzag_data['HigherLow'].iloc[i],
                    'is_lower_low': zigzag_data['LowerLow'].iloc[i]
                }
                
                swing_points.append(swing_point)
        
        return swing_points
    
    def find_most_recent_swing_high(self, swing_points, max_lookback=None):
        """
        Find the most recent swing high
        
        Parameters:
        -----------
        swing_points : list
            List of swing points
        max_lookback : int, optional
            Maximum number of swing points to look back
            
        Returns:
        --------
        dict or None
            Most recent swing high point
        """
        if not swing_points:
            return None
        
        # Sort swing points by index (most recent last)
        sorted_points = sorted(swing_points, key=lambda x: x['index'])
        
        # Limit lookback if specified
        if max_lookback is not None:
            sorted_points = sorted_points[-max_lookback:]
        
        # Find the most recent high
        for point in reversed(sorted_points):
            if point['type'] == 'high':
                return point
        
        return None
    
    def find_most_recent_swing_low(self, swing_points, max_lookback=None):
        """
        Find the most recent swing low
        
        Parameters:
        -----------
        swing_points : list
            List of swing points
        max_lookback : int, optional
            Maximum number of swing points to look back
            
        Returns:
        --------
        dict or None
            Most recent swing low point
        """
        if not swing_points:
            return None
        
        # Sort swing points by index (most recent last)
        sorted_points = sorted(swing_points, key=lambda x: x['index'])
        
        # Limit lookback if specified
        if max_lookback is not None:
            sorted_points = sorted_points[-max_lookback:]
        
        # Find the most recent low
        for point in reversed(sorted_points):
            if point['type'] == 'low':
                return point
        
        return None
