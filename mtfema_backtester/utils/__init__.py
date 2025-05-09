"""
Utility modules for the MT 9 EMA Extension Strategy Backtester.

This package contains utility functions and helpers used across the backtester.
"""

from .timeframe_utils import (
    normalize_timeframe,
    get_timeframe_minutes,
    get_next_timeframe_in_hierarchy,
    get_previous_timeframe_in_hierarchy,
    get_all_higher_timeframes,
    map_timestamp_to_higher_timeframe,
    sort_timeframes_by_hierarchy,
    TIMEFRAME_HIERARCHY,
    TIMEFRAME_TO_MINUTES
)

# Import other utility modules if they exist
try:
    from .performance_monitor import get_performance_monitor, time_operation, TimingContext
except ImportError:
    pass

try:
    from .strategy_logger import get_strategy_logger
except ImportError:
    pass

__all__ = [
    'normalize_timeframe',
    'get_timeframe_minutes',
    'get_next_timeframe_in_hierarchy',
    'get_previous_timeframe_in_hierarchy',
    'get_all_higher_timeframes',
    'map_timestamp_to_higher_timeframe',
    'sort_timeframes_by_hierarchy',
    'TIMEFRAME_HIERARCHY',
    'TIMEFRAME_TO_MINUTES'
]

# Add other utility functions to __all__ if they were successfully imported
try:
    __all__.extend([
        'get_performance_monitor',
        'time_operation',
        'TimingContext'
    ])
except NameError:
    pass

try:
    __all__.append('get_strategy_logger')
except NameError:
    pass