"""
Target Manager for the Multi-Timeframe 9 EMA Extension Strategy.

This module implements the progressive targeting framework where each timeframe's
9 EMA becomes the target for the previous timeframe.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TargetManager:
    """
    Manages the progressive targeting framework for the Multi-Timeframe 9 EMA Extension Strategy.
    """
    
    def __init__(self, timeframe_hierarchy=None):
        """
        Initialize the TargetManager
        
        Parameters:
        -----------
        timeframe_hierarchy : list, optional
            List of timeframes in ascending order (smallest to largest)
        """
        self.timeframe_hierarchy = timeframe_hierarchy or []
        logger.info(f"TargetManager initialized with hierarchy: {self.timeframe_hierarchy}")
    
    def set_timeframe_hierarchy(self, timeframe_hierarchy):
        """
        Set the timeframe hierarchy
        
        Parameters:
        -----------
        timeframe_hierarchy : list
            List of timeframes in ascending order (smallest to largest)
        """
        self.timeframe_hierarchy = timeframe_hierarchy
        logger.info(f"Timeframe hierarchy updated: {self.timeframe_hierarchy}")
    
    def get_next_timeframe(self, current_timeframe):
        """
        Get the next timeframe in the hierarchy
        
        Parameters:
        -----------
        current_timeframe : str
            Current timeframe
            
        Returns:
        --------
        str or None
            Next timeframe or None if current is the highest
        """
        if not self.timeframe_hierarchy:
            logger.warning("Timeframe hierarchy not set, cannot determine next timeframe")
            return None
        
        try:
            idx = self.timeframe_hierarchy.index(current_timeframe)
            if idx < len(self.timeframe_hierarchy) - 1:
                return self.timeframe_hierarchy[idx + 1]
            else:
                return None
        except ValueError:
            logger.warning(f"Timeframe {current_timeframe} not found in hierarchy")
            return None
    
    def get_previous_timeframe(self, current_timeframe):
        """
        Get the previous timeframe in the hierarchy
        
        Parameters:
        -----------
        current_timeframe : str
            Current timeframe
            
        Returns:
        --------
        str or None
            Previous timeframe or None if current is the lowest
        """
        if not self.timeframe_hierarchy:
            logger.warning("Timeframe hierarchy not set, cannot determine previous timeframe")
            return None
        
        try:
            idx = self.timeframe_hierarchy.index(current_timeframe)
            if idx > 0:
                return self.timeframe_hierarchy[idx - 1]
            else:
                return None
        except ValueError:
            logger.warning(f"Timeframe {current_timeframe} not found in hierarchy")
            return None
    
    def get_target_for_timeframe(self, timeframe_data, current_timeframe, current_index, direction):
        """
        Get the target price for a given timeframe
        
        Parameters:
        -----------
        timeframe_data : TimeframeData
            Multi-timeframe data
        current_timeframe : str
            Current timeframe
        current_index : int
            Current index in the current timeframe
        direction : str
            Trade direction ('long' or 'short')
            
        Returns:
        --------
        dict
            Target information including price and timeframe
        """
        # Get next timeframe in hierarchy
        next_tf = self.get_next_timeframe(current_timeframe)
        
        # If no next timeframe, use default R multiple target
        if next_tf is None:
            logger.info(f"No higher timeframe for {current_timeframe}, using R-multiple target")
            return {
                'target_price': None,
                'target_timeframe': None,
                'target_type': 'r_multiple',
                'reason': 'No higher timeframe available'
            }
        
        # Map current index to next timeframe
        next_tf_idx = timeframe_data.map_index_between_timeframes(
            current_timeframe, current_index, next_tf
        )
        
        # Make sure we have a valid index
        if next_tf_idx < 0:
            logger.warning(f"Could not map index from {current_timeframe} to {next_tf}")
            return {
                'target_price': None,
                'target_timeframe': None,
                'target_type': 'r_multiple',
                'reason': 'Could not map timeframe index'
            }
        
        # Get the next timeframe data
        next_tf_data = timeframe_data.get_timeframe(next_tf)
        
        # Check if 9 EMA is available
        ema_col = 'EMA_9'
        if ema_col not in next_tf_data.columns:
            logger.warning(f"9 EMA not available for {next_tf}, calculating")
            try:
                import talib
                next_tf_data[ema_col] = talib.EMA(next_tf_data['Close'].values, timeperiod=9)
            except ImportError:
                import pandas_ta as ta
                next_tf_data[ema_col] = ta.ema(next_tf_data['Close'], length=9)
        
        # Get 9 EMA value for target
        target_price = next_tf_data.iloc[next_tf_idx][ema_col]
        
        logger.info(f"Target for {current_timeframe} is {next_tf} 9 EMA at {target_price:.2f}")
        
        return {
            'target_price': target_price,
            'target_timeframe': next_tf,
            'target_type': 'ema9',
            'reason': f"Next timeframe ({next_tf}) 9 EMA"
        }
    
    def calculate_progressive_targets(self, timeframe_data, current_timeframe, current_index, direction):
        """
        Calculate a sequence of progressive targets through the timeframe hierarchy
        
        Parameters:
        -----------
        timeframe_data : TimeframeData
            Multi-timeframe data
        current_timeframe : str
            Starting timeframe
        current_index : int
            Current index in the starting timeframe
        direction : str
            Trade direction ('long' or 'short')
            
        Returns:
        --------
        list
            List of target dictionaries in progression order
        """
        targets = []
        
        # Start with current timeframe
        tf = current_timeframe
        idx = current_index
        
        # Progress through the hierarchy
        while tf is not None:
            # Get target for this timeframe
            target = self.get_target_for_timeframe(
                timeframe_data, tf, idx, direction
            )
            
            # Add to target list if valid
            if target['target_price'] is not None:
                targets.append(target)
            
            # Move to next timeframe
            tf = self.get_next_timeframe(tf)
            
            # If we have a next timeframe, map the index
            if tf is not None:
                idx = timeframe_data.map_index_between_timeframes(
                    current_timeframe, current_index, tf
                )
                
                # Break if mapping failed
                if idx < 0:
                    break
        
        return targets
    
    def check_target_achievement(self, price, target, direction):
        """
        Check if a target has been achieved
        
        Parameters:
        -----------
        price : float
            Current price
        target : float
            Target price
        direction : str
            Trade direction ('long' or 'short')
            
        Returns:
        --------
        bool
            Whether the target has been achieved
        """
        if direction == 'long':
            return price >= target
        else:
            return price <= target
    
    def update_active_target(self, position, timeframe_data, current_price):
        """
        Update the active target for a position based on current price
        
        Parameters:
        -----------
        position : Position
            Current position
        timeframe_data : TimeframeData
            Multi-timeframe data
        current_price : float
            Current price
            
        Returns:
        --------
        dict
            Updated target information
        """
        # Get current target info
        current_target = position.take_profit
        current_target_tf = position.target_timeframe
        
        # Check if target has been achieved
        if self.check_target_achievement(current_price, current_target, position.direction):
            # Get next target
            next_tf = self.get_next_timeframe(current_target_tf)
            
            # If no next timeframe, position is complete
            if next_tf is None:
                return {
                    'target_achieved': True,
                    'target_updated': False,
                    'next_target': None,
                    'next_target_timeframe': None,
                    'should_close': True,
                    'reason': 'Final target achieved'
                }
            
            # Get current index for position timeframe
            current_idx = timeframe_data.get_latest_index(position.timeframe)
            
            # Get next target
            next_target = self.get_target_for_timeframe(
                timeframe_data, current_target_tf, current_idx, position.direction
            )
            
            if next_target['target_price'] is not None:
                return {
                    'target_achieved': True,
                    'target_updated': True,
                    'next_target': next_target['target_price'],
                    'next_target_timeframe': next_target['target_timeframe'],
                    'should_close': False,
                    'reason': f"Moving to next target: {next_target['target_timeframe']} 9 EMA"
                }
            else:
                # No valid next target, close position
                return {
                    'target_achieved': True,
                    'target_updated': False,
                    'next_target': None,
                    'next_target_timeframe': None,
                    'should_close': True,
                    'reason': 'Target achieved, no valid next target'
                }
        
        # Target not achieved yet
        return {
            'target_achieved': False,
            'target_updated': False,
            'next_target': None,
            'next_target_timeframe': None,
            'should_close': False,
            'reason': 'Current target not yet achieved'
        }

def get_target_for_signal(timeframe_data, signal, timeframes=None):
    """
    Get the target for a trading signal
    
    Parameters:
    -----------
    timeframe_data : TimeframeData
        Multi-timeframe data
    signal : dict
        Signal information
    timeframes : list, optional
        List of timeframes in ascending order (smallest to largest)
        
    Returns:
    --------
    dict
        Target information
    """
    # Create target manager
    manager = TargetManager()
    
    # If timeframes provided, set hierarchy
    if timeframes:
        manager.set_timeframe_hierarchy(timeframes)
    else:
        # Try to get timeframes from timeframe_data
        available_tfs = timeframe_data.get_available_timeframes()
        
        # Sort by timeframe minutes
        tf_minutes = {
            tf: timeframe_data.get_timeframe_minutes(tf) 
            for tf in available_tfs
        }
        sorted_tfs = sorted(available_tfs, key=lambda tf: tf_minutes[tf])
        
        manager.set_timeframe_hierarchy(sorted_tfs)
    
    # Get target for signal
    return manager.get_target_for_timeframe(
        timeframe_data,
        signal['timeframe'],
        signal.get('index', timeframe_data.get_latest_index(signal['timeframe'])),
        signal['direction']
    ) 