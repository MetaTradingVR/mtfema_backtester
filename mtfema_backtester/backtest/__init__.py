"""
Backtest modules for the MT 9 EMA Extension Strategy Backtester.

This package contains the core backtesting engine and performance analysis tools.
"""

from .backtest_engine import execute_backtest
from .performance_metrics import (
    calculate_performance_metrics,
    create_equity_curve,
    calculate_max_drawdown,
    calculate_longest_streak,
    calculate_reward_risk_ratio,
    calculate_sharpe_ratio,
    calculate_avg_duration,
    get_summary_statistics
)

__all__ = [
    'execute_backtest',
    'calculate_performance_metrics',
    'create_equity_curve',
    'calculate_max_drawdown',
    'calculate_longest_streak',
    'calculate_reward_risk_ratio',
    'calculate_sharpe_ratio',
    'calculate_avg_duration',
    'get_summary_statistics'
]
