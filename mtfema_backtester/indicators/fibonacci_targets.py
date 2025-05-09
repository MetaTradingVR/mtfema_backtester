"""
Fibonacci Target Calculator Module

This module calculates price targets for trades using Fibonacci extension levels.
It defines specific target zones based on the Fibonacci sequence and provides methods
for profit taking and trailing stops based on these zones.
"""

import logging
import pandas as pd
import numpy as np
from mtfema_backtester.config import STRATEGY_PARAMS
from mtfema_backtester.indicators.fibonacci import FibonacciTools

logger = logging.getLogger(__name__)

class FibonacciTargetCalculator:
    """
    Calculates price targets for trades using Fibonacci extension levels.
    
    This class is designed to calculate potential take-profit levels and stop-loss levels
    using Fibonacci extensions of swing moves.
    """
    
    def __init__(self, fib_tools=None, params=None):
        """
        Initialize the Fibonacci Target Calculator.
        
        Parameters:
        -----------
        fib_tools : FibonacciTools, optional
            Fibonacci tools instance to use for calculations.
            If None, creates a new instance.
        params : dict, optional
            Strategy parameters to use.
            If None, uses STRATEGY_PARAMS.
        """
        self.params = params or STRATEGY_PARAMS
        self.fib_tools = fib_tools or FibonacciTools(
            retracement_levels=self.params['fibonacci']['levels'],
            extension_levels=self.params['fibonacci']['extension_levels'],
            pullback_zone=self.params['fibonacci']['pullback_zone']
        )
        logger.info("Fibonacci Target Calculator initialized")
    
    def calculate_targets(self, swing_high=None, swing_low=None, entry_price=None, 
                          stop_price=None, is_long=True):
        """
        Calculate Fibonacci target levels for a trade.
        
        Parameters:
        -----------
        swing_high : float
            Recent swing high price.
        swing_low : float
            Recent swing low price.
        entry_price : float
            Entry price for the trade.
        stop_price : float, optional
            Stop loss price. If provided, targets will be calculated relative to risk.
        is_long : bool, default=True
            If True, calculates targets for a long trade.
            If False, calculates targets for a short trade.
            
        Returns:
        --------
        dict
            Dictionary with target levels and relevant information.
        """
        if is_long:
            if swing_low is None or entry_price is None:
                logger.warning("Missing required parameters for long target calculation")
                return {}
                
            # For long trades
            range_size = entry_price - swing_low
            
            # Calculate extension targets from the entry
            targets = {}
            for ext_level in self.params['fibonacci']['extension_levels']:
                target_price = entry_price + (range_size * (ext_level - 1))
                targets[str(ext_level)] = target_price
                
            # If stop loss is provided, calculate reward-risk ratios
            if stop_price is not None:
                risk = entry_price - stop_price
                if risk > 0:
                    for level, price in targets.items():
                        reward = price - entry_price
                        targets[f"{level}_rr"] = reward / risk
                        
            return {
                'entry_price': entry_price,
                'swing_low': swing_low,
                'range_size': range_size,
                'targets': targets,
                'stop_price': stop_price
            }
            
        else:
            if swing_high is None or entry_price is None:
                logger.warning("Missing required parameters for short target calculation")
                return {}
                
            # For short trades
            range_size = swing_high - entry_price
            
            # Calculate extension targets from the entry
            targets = {}
            for ext_level in self.params['fibonacci']['extension_levels']:
                target_price = entry_price - (range_size * (ext_level - 1))
                targets[str(ext_level)] = target_price
                
            # If stop loss is provided, calculate reward-risk ratios
            if stop_price is not None:
                risk = stop_price - entry_price
                if risk > 0:
                    for level, price in targets.items():
                        reward = entry_price - price
                        targets[f"{level}_rr"] = reward / risk
                        
            return {
                'entry_price': entry_price,
                'swing_high': swing_high,
                'range_size': range_size,
                'targets': targets,
                'stop_price': stop_price
            }
    
    def get_optimal_targets(self, targets_data, min_rr=2.0):
        """
        Get optimal take-profit targets based on reward-risk ratio.
        
        Parameters:
        -----------
        targets_data : dict
            Target data from calculate_targets method.
        min_rr : float, default=2.0
            Minimum reward-risk ratio to consider a target valid.
            
        Returns:
        --------
        list
            List of dictionaries with optimal target levels.
        """
        if not targets_data or 'targets' not in targets_data:
            return []
            
        # Get targets that meet minimum reward-risk ratio
        optimal_targets = []
        
        for level, price in targets_data['targets'].items():
            # Skip the reward-risk entries
            if '_rr' in level:
                continue
                
            # Get the reward-risk ratio for this level
            rr_key = f"{level}_rr"
            if rr_key in targets_data['targets']:
                rr = targets_data['targets'][rr_key]
                if rr >= min_rr:
                    optimal_targets.append({
                        'level': float(level),
                        'price': price,
                        'reward_risk': rr
                    })
        
        # Sort targets by price (increasing for long, decreasing for short)
        if 'swing_low' in targets_data:  # This is a long trade
            optimal_targets.sort(key=lambda x: x['price'])
        else:
            optimal_targets.sort(key=lambda x: x['price'], reverse=True)
            
        return optimal_targets
    
    def add_targets_to_signal(self, signal, price_data, lookback=20):
        """
        Add Fibonacci targets to a trading signal.
        
        Parameters:
        -----------
        signal : dict
            Trading signal with entry price and direction.
        price_data : pandas.DataFrame
            Price data with OHLCV columns.
        lookback : int, default=20
            Number of bars to look back for swing points.
            
        Returns:
        --------
        dict
            Updated signal with Fibonacci targets.
        """
        if not signal or 'type' not in signal or 'entry_price' not in signal:
            logger.warning("Invalid signal provided for target calculation")
            return signal
        
        # Create a copy of the signal to avoid modifying the original
        updated_signal = signal.copy()
        
        # Get trade direction
        is_long = signal['type'] == 'LONG'
        
        # Get recent price data
        if isinstance(price_data.index[0], pd.Timestamp):
            # For datetime-indexed data, get data up to signal time
            signal_time = signal['datetime']
            lookback_data = price_data.loc[:signal_time].tail(lookback)
        else:
            # For integer-indexed data, use the latest data
            lookback_data = price_data.tail(lookback)
            
        # Find swing points
        if is_long:
            swing_low = lookback_data['Low'].min()
            
            # Calculate Fibonacci targets
            targets = self.calculate_targets(
                swing_low=swing_low,
                entry_price=signal['entry_price'],
                stop_price=signal.get('stop_price'),
                is_long=True
            )
            
            # Add targets to signal
            if targets:
                updated_signal['fib_targets'] = targets
                
                # Add optimal targets
                min_rr = self.params['risk_management'].get('reward_risk_ratio', 2.0)
                optimal_targets = self.get_optimal_targets(targets, min_rr)
                if optimal_targets:
                    updated_signal['optimal_targets'] = optimal_targets
        else:
            swing_high = lookback_data['High'].max()
            
            # Calculate Fibonacci targets
            targets = self.calculate_targets(
                swing_high=swing_high,
                entry_price=signal['entry_price'],
                stop_price=signal.get('stop_price'),
                is_long=False
            )
            
            # Add targets to signal
            if targets:
                updated_signal['fib_targets'] = targets
                
                # Add optimal targets
                min_rr = self.params['risk_management'].get('reward_risk_ratio', 2.0)
                optimal_targets = self.get_optimal_targets(targets, min_rr)
                if optimal_targets:
                    updated_signal['optimal_targets'] = optimal_targets
                    
        return updated_signal


def calculate_fib_targets(signal, price_data, params=None):
    """
    Calculate Fibonacci targets for a trading signal.
    
    Parameters:
    -----------
    signal : dict
        Trading signal with entry price and direction.
    price_data : pandas.DataFrame
        Price data with OHLCV columns.
    params : dict, optional
        Strategy parameters to use. If None, uses STRATEGY_PARAMS.
        
    Returns:
    --------
    dict
        Updated signal with Fibonacci targets.
    """
    calculator = FibonacciTargetCalculator(params=params)
    return calculator.add_targets_to_signal(signal, price_data) 