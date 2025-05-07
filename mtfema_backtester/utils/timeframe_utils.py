"""
Timeframe utilities for the MT 9 EMA Extension Strategy Backtester.

This module contains functions for managing timeframes, including normalization,
conversion, and timeframe hierarchy management.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Standard timeframe hierarchy from smallest to largest
TIMEFRAME_HIERARCHY = [
    "1m", "5m", "10m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"
]

# Mapping between timeframe strings and minutes
TIMEFRAME_TO_MINUTES = {
    "1m": 1,
    "5m": 5,
    "10m": 10,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "1d": 1440,  # 24 * 60
    "1w": 10080,  # 7 * 24 * 60
    "1M": 43200,  # 30 * 24 * 60 (approximate)
}

def normalize_timeframe(tf):
    """
    Convert various timeframe formats to standard format.
    
    Args:
        tf: Timeframe string (e.g., '1', 'd', '15m', 'hourly')
        
    Returns:
        str: Normalized timeframe string
    """
    # Common timeframe mappings
    mappings = {
        # Days
        '1': '1d', 'd': '1d', 'day': '1d', 'daily': '1d', '1day': '1d', 'D': '1d',
        # Hours
        'h': '1h', 'hour': '1h', '1hour': '1h', '60m': '1h', '60min': '1h', 'H': '1h',
        # Minutes
        'm': '1m', 'min': '1m', 'minute': '1m', '1minute': '1m', 'M': '1m',
        # Weeks
        'w': '1w', 'week': '1w', '1week': '1w', 'weekly': '1w', 'W': '1w',
        # Months
        'mo': '1M', 'month': '1M', '1month': '1M', 'monthly': '1M', 'MO': '1M'
    }
    
    # Check if already in standard format
    if tf in TIMEFRAME_HIERARCHY:
        return tf
    
    # Try direct mapping
    if tf.lower() in mappings:
        return mappings[tf.lower()]
    
    # Try to parse more complex formats
    match = re.match(r'(\d+)([a-zA-Z]+)', tf)
    if match:
        value, unit = match.groups()
        unit = unit.lower()
        if unit in ['m', 'min', 'minute', 'minutes']:
            return f"{value}m"
        elif unit in ['h', 'hr', 'hour', 'hours']:
            return f"{value}h"
        elif unit in ['d', 'day', 'days']:
            return f"{value}d"
        elif unit in ['w', 'week', 'weeks']:
            return f"{value}w"
        elif unit in ['mo', 'month', 'months']:
            return f"{value}M"
    
    # Return original with warning
    logger.warning(f"Unrecognized timeframe format: {tf}, using as-is")
    return tf

def get_timeframe_minutes(timeframe):
    """
    Convert timeframe string to minutes.
    
    Args:
        timeframe: Timeframe string (e.g., '1d', '1h', '15m')
        
    Returns:
        int: Number of minutes in the timeframe
    """
    # Normalize the timeframe first
    normalized_tf = normalize_timeframe(timeframe)
    
    # Check if it's in our standard mapping
    if normalized_tf in TIMEFRAME_TO_MINUTES:
        return TIMEFRAME_TO_MINUTES[normalized_tf]
    
    # Try to parse it
    if normalized_tf.endswith('m'):
        try:
            return int(normalized_tf[:-1])
        except ValueError:
            logger.warning(f"Invalid minute timeframe format: {normalized_tf}")
            return 1440  # Default to daily
        
    elif normalized_tf.endswith('h'):
        try:
            return int(normalized_tf[:-1]) * 60
        except ValueError:
            logger.warning(f"Invalid hour timeframe format: {normalized_tf}")
            return 1440  # Default to daily
        
    elif normalized_tf.endswith('d'):
        try:
            return int(normalized_tf[:-1]) * 1440
        except ValueError:
            logger.warning(f"Invalid day timeframe format: {normalized_tf}")
            return 1440  # Default to daily
        
    elif normalized_tf.endswith('w'):
        try:
            return int(normalized_tf[:-1]) * 1440 * 7
        except ValueError:
            logger.warning(f"Invalid week timeframe format: {normalized_tf}")
            return 1440 * 7  # Default to weekly
        
    elif normalized_tf.endswith('M'):
        try:
            return int(normalized_tf[:-1]) * 1440 * 30
        except ValueError:
            logger.warning(f"Invalid month timeframe format: {normalized_tf}")
            return 1440 * 30  # Default to monthly
    
    logger.warning(f"Unknown timeframe format: {normalized_tf}, defaulting to daily")
    return 1440  # Default to daily

def get_next_timeframe_in_hierarchy(current_tf):
    """
    Get the next timeframe in the hierarchy.
    
    Args:
        current_tf: Current timeframe string
        
    Returns:
        str: Next timeframe in hierarchy, or current if at the top
    """
    # Normalize the timeframe
    normalized_tf = normalize_timeframe(current_tf)
    
    try:
        current_idx = TIMEFRAME_HIERARCHY.index(normalized_tf)
        if current_idx < len(TIMEFRAME_HIERARCHY) - 1:
            return TIMEFRAME_HIERARCHY[current_idx + 1]
        return normalized_tf  # Return the same if at the top
    except ValueError:
        # If not found in hierarchy, try to find the closest one by minutes
        current_minutes = get_timeframe_minutes(current_tf)
        
        # Find the next timeframe with higher minutes
        for tf in TIMEFRAME_HIERARCHY:
            tf_minutes = TIMEFRAME_TO_MINUTES[tf]
            if tf_minutes > current_minutes:
                return tf
        
        # If not found, return the highest timeframe
        return TIMEFRAME_HIERARCHY[-1]

def get_previous_timeframe_in_hierarchy(current_tf):
    """
    Get the previous timeframe in the hierarchy.
    
    Args:
        current_tf: Current timeframe string
        
    Returns:
        str: Previous timeframe in hierarchy, or current if at the bottom
    """
    # Normalize the timeframe
    normalized_tf = normalize_timeframe(current_tf)
    
    try:
        current_idx = TIMEFRAME_HIERARCHY.index(normalized_tf)
        if current_idx > 0:
            return TIMEFRAME_HIERARCHY[current_idx - 1]
        return normalized_tf  # Return the same if at the bottom
    except ValueError:
        # If not found in hierarchy, try to find the closest one by minutes
        current_minutes = get_timeframe_minutes(current_tf)
        
        # Find the previous timeframe with lower minutes
        for tf in reversed(TIMEFRAME_HIERARCHY):
            tf_minutes = TIMEFRAME_TO_MINUTES[tf]
            if tf_minutes < current_minutes:
                return tf
        
        # If not found, return the lowest timeframe
        return TIMEFRAME_HIERARCHY[0]

def get_all_higher_timeframes(current_tf):
    """
    Get all timeframes higher than the current one in the hierarchy.
    
    Args:
        current_tf: Current timeframe string
        
    Returns:
        list: List of higher timeframes
    """
    # Normalize the timeframe
    normalized_tf = normalize_timeframe(current_tf)
    
    try:
        current_idx = TIMEFRAME_HIERARCHY.index(normalized_tf)
        if current_idx < len(TIMEFRAME_HIERARCHY) - 1:
            return TIMEFRAME_HIERARCHY[current_idx + 1:]
        return []  # Return empty list if at the top
    except ValueError:
        # If not found in hierarchy, try to find the closest one by minutes
        current_minutes = get_timeframe_minutes(current_tf)
        
        # Find all timeframes with higher minutes
        higher_tfs = []
        for tf in TIMEFRAME_HIERARCHY:
            tf_minutes = TIMEFRAME_TO_MINUTES[tf]
            if tf_minutes > current_minutes:
                higher_tfs.append(tf)
        
        return higher_tfs

def map_timestamp_to_higher_timeframe(timestamp, source_tf, target_tf):
    """
    Map a timestamp from a lower timeframe to the corresponding timestamp in a higher timeframe.
    
    Args:
        timestamp: Timestamp to map
        source_tf: Source timeframe
        target_tf: Target timeframe
        
    Returns:
        timestamp: Corresponding timestamp in the target timeframe
    """
    # This is a placeholder - in practice, this would depend on the data's timestamp format
    # and might require resampling or other operations. The actual implementation would
    # need to be adapted to the specific data structure.
    
    # The general logic is:
    # 1. Determine the period start for the target timeframe that contains the source timestamp
    # 2. Return that period start as the corresponding timestamp
    
    logger.warning("map_timestamp_to_higher_timeframe is not fully implemented")
    return timestamp  # Placeholder

def sort_timeframes_by_hierarchy(timeframes):
    """
    Sort a list of timeframes according to the standard hierarchy.
    
    Args:
        timeframes: List of timeframe strings
        
    Returns:
        list: Sorted list of timeframe strings
    """
    # Create a mapping from timeframe to its position in hierarchy
    tf_positions = {tf: i for i, tf in enumerate(TIMEFRAME_HIERARCHY)}
    
    # Define a key function for sorting
    def sort_key(tf):
        normalized_tf = normalize_timeframe(tf)
        return tf_positions.get(normalized_tf, float('inf'))
    
    # Sort the timeframes
    return sorted(timeframes, key=sort_key) 