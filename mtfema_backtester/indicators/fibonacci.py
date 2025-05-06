"""
Fibonacci retracement and extension utilities for identifying key price levels
"""

import pandas as pd
import numpy as np
import logging
from mtfema_backtester.config import STRATEGY_PARAMS

logger = logging.getLogger(__name__)

class FibonacciTools:
    """
    Tools for calculating Fibonacci retracement and extension levels
    """
    
    def __init__(self, 
                 retracement_levels=None, 
                 extension_levels=None,
                 pullback_zone=None):
        """
        Initialize Fibonacci tools with levels
        
        Parameters:
        -----------
        retracement_levels : list, optional
            List of Fibonacci retracement levels (0-1)
        extension_levels : list, optional
            List of Fibonacci extension levels (>1)
        pullback_zone : list, optional
            Two-element list defining valid pullback zone [min, max]
        """
        # Use values from config if not provided
        if retracement_levels is None:
            retracement_levels = STRATEGY_PARAMS['fibonacci']['levels']
        
        if extension_levels is None:
            extension_levels = STRATEGY_PARAMS['fibonacci']['extension_levels']
            
        if pullback_zone is None:
            pullback_zone = STRATEGY_PARAMS['fibonacci']['pullback_zone']
        
        self.retracement_levels = retracement_levels
        self.extension_levels = extension_levels
        self.pullback_zone = pullback_zone
        
        logger.info(f"FibonacciTools initialized with retracement levels: {retracement_levels}, "
                   f"extension levels: {extension_levels}, pullback zone: {pullback_zone}")
    
    def calculate_retracement_levels(self, start_price, end_price):
        """
        Calculate Fibonacci retracement levels
        
        Parameters:
        -----------
        start_price : float
            Starting price level (swing high for downtrend, swing low for uptrend)
        end_price : float
            Ending price level (swing low for downtrend, swing high for uptrend)
            
        Returns:
        --------
        dict
            Dictionary with Fibonacci levels as keys and price levels as values
        """
        if start_price is None or end_price is None:
            logger.warning("Invalid prices for Fibonacci calculation")
            return {}
        
        price_range = abs(end_price - start_price)
        is_uptrend = end_price > start_price
        
        levels = {}
        
        for fib_level in self.retracement_levels:
            if is_uptrend:
                levels[fib_level] = end_price - (price_range * fib_level)
            else:
                levels[fib_level] = start_price + (price_range * fib_level)
        
        return levels
    
    def calculate_extension_levels(self, start_price, end_price, is_uptrend=None):
        """
        Calculate Fibonacci extension levels
        
        Parameters:
        -----------
        start_price : float
            Starting price level (swing point 1)
        end_price : float
            Ending price level (swing point 2)
        is_uptrend : bool, optional
            If True, calculate extensions for uptrend; if False, for downtrend
            If None, determine from prices
            
        Returns:
        --------
        dict
            Dictionary with Fibonacci extension levels as keys and prices as values
        """
        if start_price is None or end_price is None:
            logger.warning("Invalid prices for Fibonacci extension calculation")
            return {}
        
        price_range = abs(end_price - start_price)
        
        # Determine trend direction if not provided
        if is_uptrend is None:
            is_uptrend = end_price > start_price
        
        levels = {}
        
        for fib_level in self.extension_levels:
            if is_uptrend:
                # For uptrend: extend above the high
                levels[fib_level] = end_price + (price_range * (fib_level - 1))
            else:
                # For downtrend: extend below the low
                levels[fib_level] = end_price - (price_range * (fib_level - 1))
        
        return levels
    
    def calculate_levels_from_swing_points(self, swing_high, swing_low, include_extensions=True):
        """
        Calculate Fibonacci levels from swing points
        
        Parameters:
        -----------
        swing_high : dict or float
            Swing high point (can be dict with 'price' key or float price)
        swing_low : dict or float
            Swing low point (can be dict with 'price' key or float price)
        include_extensions : bool
            Whether to include extension levels
            
        Returns:
        --------
        dict
            Dictionary with separate retracement and extension levels
        """
        # Extract prices from swing points if needed
        high_price = swing_high['price'] if isinstance(swing_high, dict) else swing_high
        low_price = swing_low['price'] if isinstance(swing_low, dict) else swing_low
        
        if high_price is None or low_price is None or high_price <= low_price:
            logger.warning("Invalid swing points for Fibonacci calculation")
            return {'retracement': {}, 'extension': {}}
        
        # Calculate retracement levels (high to low)
        retracement_levels = self.calculate_retracement_levels(high_price, low_price)
        
        # Calculate extension levels if requested
        extension_levels = {}
        if include_extensions:
            extension_levels = self.calculate_extension_levels(high_price, low_price, is_uptrend=False)
        
        return {
            'retracement': retracement_levels,
            'extension': extension_levels
        }
    
    def is_in_pullback_zone(self, price, retracement_levels):
        """
        Check if a price is within the defined pullback zone
        
        Parameters:
        -----------
        price : float
            Current price to check
        retracement_levels : dict
            Dictionary of Fibonacci retracement levels
            
        Returns:
        --------
        bool
            True if price is in the pullback zone
        """
        if not retracement_levels or not self.pullback_zone or len(self.pullback_zone) != 2:
            return False
        
        # Get the upper and lower bounds of the pullback zone
        min_level, max_level = self.pullback_zone
        
        if min_level not in retracement_levels or max_level not in retracement_levels:
            return False
        
        # Get the price levels for the zone
        min_price = retracement_levels[min_level]
        max_price = retracement_levels[max_level]
        
        # Ensure correct order (min_price should be smaller)
        if min_price > max_price:
            min_price, max_price = max_price, min_price
        
        # Check if price is in the zone
        return min_price <= price <= max_price
    
    def validate_pullback(self, current_price, swing_high, swing_low, reclaim_price, is_long=True):
        """
        Validate if a pullback is in the correct Fibonacci zone
        
        Parameters:
        -----------
        current_price : float
            Current price to validate
        swing_high : float or dict
            Recent swing high price or point
        swing_low : float or dict
            Recent swing low price or point
        reclaim_price : float
            Price level where EMA was reclaimed
        is_long : bool
            True for validating long pullbacks, False for shorts
            
        Returns:
        --------
        bool
            True if the pullback is valid
        """
        # Extract prices from swing points if needed
        high_price = swing_high['price'] if isinstance(swing_high, dict) else swing_high
        low_price = swing_low['price'] if isinstance(swing_low, dict) else swing_low
        
        if is_long:
            # For longs (bullish):
            # 1. Price reclaimed EMA from below
            # 2. Then pulled back to Fibonacci zone
            # 3. But remains above the swing low
            
            # Calculate Fibonacci levels from the low to reclaim point
            levels = self.calculate_retracement_levels(low_price, reclaim_price)
            
            # Check if current price is in the pullback zone and above the low
            return (self.is_in_pullback_zone(current_price, levels) and 
                    current_price > low_price)
        else:
            # For shorts (bearish):
            # 1. Price reclaimed EMA from above
            # 2. Then pulled back to Fibonacci zone
            # 3. But remains below the swing high
            
            # Calculate Fibonacci levels from the high to reclaim point
            levels = self.calculate_retracement_levels(high_price, reclaim_price)
            
            # Check if current price is in the pullback zone and below the high
            return (self.is_in_pullback_zone(current_price, levels) and 
                    current_price < high_price)
