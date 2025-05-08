"""
Strategy modules for the MT 9 EMA Extension Strategy Backtester.

This package contains the implementation of the Multi-Timeframe 9 EMA Extension
trading strategy, including signal generation, extension detection, and trade management.

The core strategy components include signal generation, conflict resolution, 
and target management.
"""

from .signal_generator import generate_signals
from .conflict_resolver import (
    check_timeframe_conflict,
    adjust_risk_for_conflict,
    get_target_for_timeframe,
    ConflictType
)

__all__ = [
    'generate_signals',
    'check_timeframe_conflict',
    'adjust_risk_for_conflict',
    'get_target_for_timeframe',
    'ConflictType'
]
