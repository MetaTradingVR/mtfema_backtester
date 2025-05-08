"""
Strategy adapter for the MT 9 EMA Extension Strategy Backtester.

This module adapts various strategy signal formats to work with the TradeExecutor.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StrategyAdapter:
    """
    Adapter to convert strategy signals to TradeExecutor format.
    """
    
    def __init__(self, strategy_instance=None):
        """
        Initialize the strategy adapter.
        
        Args:
            strategy_instance: Optional strategy instance to connect
        """
        self.strategy = strategy_instance
        
    def convert_signals(self, original_signals, timeframe_data=None):
        """
        Convert signals from original format to TradeExecutor format.
        
        Args:
            original_signals: DataFrame or list of signal dictionaries
            timeframe_data: Optional timeframe data for target calculation
            
        Returns:
            List of signal dictionaries in TradeExecutor format
        """
        converted_signals = []
        
        # Handle DataFrame input
        if isinstance(original_signals, pd.DataFrame):
            signals_list = original_signals.to_dict('records')
        else:
            signals_list = original_signals
            
        for signal in signals_list:
            # Extract core signal properties with fallbacks
            try:
                new_signal = {
                    'entry_time': signal.get('datetime', signal.get('entry_time', datetime.now())),
                    'timeframe': signal.get('timeframe', '1d'),
                    'direction': self._normalize_direction(signal),
                    'entry_price': signal.get('entry_price', signal.get('price', 0.0)),
                    'stop_price': signal.get('stop_price', self._calculate_stop(signal)),
                    'target_price': signal.get('target_price', self._calculate_target(signal, timeframe_data)),
                    'target_timeframe': signal.get('target_timeframe', self._get_next_timeframe(signal.get('timeframe', '1d'))),
                    'risk_factor': signal.get('risk_factor', signal.get('confidence', 1.0))
                }
                
                # Add symbol if available
                if 'symbol' in signal:
                    new_signal['symbol'] = signal['symbol']
                    
                # Additional metadata that might be useful
                if 'id' in signal:
                    new_signal['original_id'] = signal['id']
                    
                if 'signal_type' in signal:
                    new_signal['signal_type'] = signal['signal_type']
                    
                converted_signals.append(new_signal)
                
            except Exception as e:
                logger.error(f"Error converting signal: {str(e)}")
                logger.debug(f"Problematic signal: {signal}")
        
        return converted_signals
    
    def _normalize_direction(self, signal):
        """Normalize direction to 'long' or 'short'."""
        direction = signal.get('direction', 
                        signal.get('type', 
                          signal.get('signal_type', 'long')))
        
        if isinstance(direction, str):
            direction = direction.lower()
            
            if direction in ['long', 'buy', '1', 'l']:
                return 'long'
            elif direction in ['short', 'sell', '-1', 's']:
                return 'short'
        
        # Convert numeric values
        if isinstance(direction, (int, float)):
            return 'long' if direction > 0 else 'short'
            
        # Default to long
        return 'long'
    
    def _calculate_stop(self, signal):
        """Calculate stop price if not provided."""
        direction = self._normalize_direction(signal)
        entry_price = signal.get('entry_price', signal.get('price', 0.0))
        
        # Default to 1% stop
        stop_percent = signal.get('stop_percent', 0.01)
        
        if direction == 'long':
            return entry_price * (1 - stop_percent)
        else:
            return entry_price * (1 + stop_percent)
    
    def _calculate_target(self, signal, timeframe_data):
        """Calculate target price based on strategy logic."""
        direction = self._normalize_direction(signal)
        entry_price = signal.get('entry_price', signal.get('price', 0.0))
        stop_price = signal.get('stop_price', self._calculate_stop(signal))
        
        # Try to use reward_risk_ratio if available
        reward_risk = signal.get('reward_risk_ratio', 2.0)
        
        risk = abs(entry_price - stop_price)
        
        if direction == 'long':
            return entry_price + (risk * reward_risk)
        else:
            return entry_price - (risk * reward_risk)
    
    def _get_next_timeframe(self, timeframe):
        """Get the next timeframe in hierarchy."""
        hierarchy = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        
        try:
            idx = hierarchy.index(timeframe)
            if idx < len(hierarchy) - 1:
                return hierarchy[idx + 1]
        except ValueError:
            pass
        
        return timeframe  # Return same timeframe if not found or at top

class MTFEMA_StrategyAdapter(StrategyAdapter):
    """
    Specialized adapter for MT 9 EMA Extension Strategy.
    """
    
    def convert_extension_signal(self, extension_data, price_data):
        """
        Convert extension detection signals to TradeExecutor format.
        
        Args:
            extension_data: Dictionary with extension data by timeframe
            price_data: Dictionary with price data by timeframe
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        for timeframe, ext_info in extension_data.items():
            if not ext_info.get('is_extended', False):
                continue
                
            # Get price data for this timeframe
            tf_price = price_data.get(timeframe, {})
            if not tf_price:
                continue
                
            # Determine direction from extension
            direction = 'long' if ext_info.get('extension_type') == 'bullish' else 'short'
            
            # Create signal
            signal = {
                'entry_time': tf_price.get('datetime', datetime.now()),
                'timeframe': timeframe,
                'direction': direction,
                'entry_price': tf_price.get('close', 0.0),
                'stop_price': self._get_extension_stop(ext_info, tf_price, direction),
                'target_price': None,  # Will be calculated
                'target_timeframe': self._get_next_timeframe(timeframe),
                'risk_factor': ext_info.get('extension_percent', 1.0) / 100.0  # Normalize to 0-1
            }
            
            # Calculate target based on EMA values
            signal['target_price'] = self._calculate_ema_target(ext_info, tf_price, direction)
            
            signals.append(signal)
            
        return signals
    
    def _get_extension_stop(self, ext_info, price_data, direction):
        """Calculate stop price based on extension data."""
        if direction == 'long':
            # For long position, use recent low or EMA level
            return min(
                price_data.get('low', 0.0),
                ext_info.get('ema_value', price_data.get('close', 0.0) * 0.99)
            )
        else:
            # For short position, use recent high or EMA level
            return max(
                price_data.get('high', 0.0),
                ext_info.get('ema_value', price_data.get('close', 0.0) * 1.01)
            )
    
    def _calculate_ema_target(self, ext_info, price_data, direction):
        """Calculate target price based on EMA values."""
        # Default to 2:1 reward-risk
        entry = price_data.get('close', 0.0)
        stop = self._get_extension_stop(ext_info, price_data, direction)
        risk = abs(entry - stop)
        
        if direction == 'long':
            return entry + (risk * 2)
        else:
            return entry - (risk * 2)
