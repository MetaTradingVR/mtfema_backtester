"""
Indicators package for technical analysis computations
"""

from mtfema_backtester.indicators.ema import calculate_ema, detect_9ema_extension
from mtfema_backtester.indicators.bollinger import calculate_bollinger_bands, detect_bollinger_breakouts

__all__ = [
    'calculate_ema', 
    'detect_9ema_extension',
    'calculate_bollinger_bands',
    'detect_bollinger_breakouts'
]