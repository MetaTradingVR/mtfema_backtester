"""
Conflict resolver for the Multi-Timeframe 9 EMA Extension Strategy Backtester.

This module detects and resolves conflicts between different timeframes
to adjust trade parameters and risk accordingly.
"""

import logging
import pandas as pd
import numpy as np

from mtfema_backtester.utils.timeframe_utils import (
    get_timeframe_minutes, 
    map_timestamp_to_higher_timeframe
)

logger = logging.getLogger(__name__)

# Conflict types
class ConflictType:
    """Enum-like class for conflict types"""
    NO_CONFLICT = "NoConflict"
    DIRECT_CORRECTION = "DirectCorrection"
    TRAP_SETUP = "TrapSetup"
    CONSOLIDATION = "Consolidation"
    NO_DATA = "NoData"
    DATA_ERROR = "DataError"

def check_timeframe_conflict(timeframe_data, current_tf, higher_tf, timestamp):
    """
    Check for conflicts between current and higher timeframe.
    
    Args:
        timeframe_data: TimeframeData instance with indicator data
        current_tf: Current timeframe string
        higher_tf: Higher timeframe string
        timestamp: Timestamp to check
        
    Returns:
        str: Conflict type (see ConflictType class)
    """
    # Get extension data
    current_ext = timeframe_data.get_indicator(current_tf, "ExtensionSignal")
    higher_ext = timeframe_data.get_indicator(higher_tf, "ExtensionSignal")
    
    if current_ext is None or higher_ext is None:
        logger.warning(f"Missing extension data for conflict check: current_tf={current_tf}, higher_tf={higher_tf}")
        return ConflictType.NO_DATA
    
    # Get current values
    current_idx = timestamp
    higher_idx = map_timestamp_to_higher_timeframe(timestamp, current_tf, higher_tf)
    
    try:
        # Check if both have extensions but in opposite directions
        current_has_extension = _get_value(current_ext, current_idx, 'has_extension', False)
        higher_has_extension = _get_value(higher_ext, higher_idx, 'has_extension', False)
        
        if current_has_extension and higher_has_extension:
            current_up = _get_value(current_ext, current_idx, 'extended_up', False)
            current_down = _get_value(current_ext, current_idx, 'extended_down', False)
            higher_up = _get_value(higher_ext, higher_idx, 'extended_up', False)
            higher_down = _get_value(higher_ext, higher_idx, 'extended_down', False)
            
            if (current_up and higher_down) or (current_down and higher_up):
                logger.info(f"Direct correction conflict detected: {current_tf} vs {higher_tf}")
                return ConflictType.DIRECT_CORRECTION
        
        # Check for trap setup
        if higher_has_extension and not current_has_extension:
            # Check reclamation in lower timeframe
            reclamation = timeframe_data.get_indicator(current_tf, "Reclamation")
            if reclamation is not None:
                has_bullish_reclaim = _get_value(reclamation, current_idx, 'BullishReclaim', False)
                has_bearish_reclaim = _get_value(reclamation, current_idx, 'BearishReclaim', False)
                
                if has_bullish_reclaim or has_bearish_reclaim:
                    logger.info(f"Trap setup detected: {current_tf} reclamation against {higher_tf} extension")
                    return ConflictType.TRAP_SETUP
                
            logger.info(f"Consolidation detected: {higher_tf} extended but {current_tf} not extended")
            return ConflictType.CONSOLIDATION
        
        logger.debug(f"No conflict detected between {current_tf} and {higher_tf}")
        return ConflictType.NO_CONFLICT
        
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error checking timeframe conflict: {str(e)}")
        return ConflictType.DATA_ERROR

def adjust_risk_for_conflict(base_risk, conflict_type):
    """
    Adjust risk percentage based on conflict type.
    
    Args:
        base_risk: Base risk percentage (e.g., 0.01 for 1%)
        conflict_type: Type of conflict detected
        
    Returns:
        float: Adjusted risk percentage
    """
    if conflict_type == ConflictType.DIRECT_CORRECTION:
        # High-risk situation - reduce risk by 75%
        return base_risk * 0.25
    
    elif conflict_type == ConflictType.TRAP_SETUP:
        # Moderate-risk situation - reduce risk by 50%
        return base_risk * 0.5
    
    elif conflict_type == ConflictType.CONSOLIDATION:
        # Slightly higher risk - reduce risk by 25%
        return base_risk * 0.75
    
    elif conflict_type in [ConflictType.DATA_ERROR, ConflictType.NO_DATA]:
        # Uncertain situation - reduce risk by 50%
        return base_risk * 0.5
    
    # No conflict or unknown - use base risk
    return base_risk

def get_target_for_timeframe(timeframe_data, target_tf, signal_type):
    """
    Get the target price for a specific timeframe.
    
    Args:
        timeframe_data: TimeframeData instance
        target_tf: Target timeframe string
        signal_type: Signal type ('LONG' or 'SHORT')
        
    Returns:
        float: Target price, or None if not available
    """
    # Get 9 EMA value for target timeframe
    ema_data = timeframe_data.get_indicator(target_tf, "EMA_9")
    if ema_data is None or ema_data.empty:
        logger.warning(f"No EMA data available for target timeframe {target_tf}")
        return None
    
    # Get the latest value
    try:
        latest_ema = ema_data.iloc[-1]
        if isinstance(latest_ema, pd.Series):
            latest_ema = latest_ema.iloc[0]
        
        logger.info(f"Target for {signal_type} on {target_tf}: {latest_ema}")
        return float(latest_ema)
    
    except (IndexError, TypeError) as e:
        logger.error(f"Error getting target for timeframe {target_tf}: {str(e)}")
        return None

def _get_value(df, idx, column, default=None):
    """
    Helper function to safely get value from DataFrame.
    
    Args:
        df: DataFrame to get value from
        idx: Index to get
        column: Column name
        default: Default value if not found
        
    Returns:
        Value at df.loc[idx, column] or default if not found
    """
    try:
        if idx not in df.index or column not in df.columns:
            return default
        
        value = df.loc[idx, column]
        
        # Handle case where the value is a Series (handle MultiIndex)
        if isinstance(value, pd.Series):
            return value.iloc[0]
        
        return value
    
    except (KeyError, IndexError, TypeError) as e:
        logger.debug(f"Error getting value at {idx}, {column}: {str(e)}")
        return default 