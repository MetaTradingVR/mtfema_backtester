"""
Visualization modules for the MT 9 EMA Extension Strategy Backtester.

This package contains tools for creating interactive visualizations of backtest results
and strategy analysis.
"""

from .performance_dashboard import (
    create_performance_dashboard,
    create_trade_timeline,
    create_extension_signal_map,
    add_equity_curve_plot,
    add_performance_by_timeframe_plot,
    add_monthly_returns_plot,
    add_trade_results_by_direction_plot,
    add_profit_distribution_plot,
    add_timeframe_progression_plot
)

__all__ = [
    'create_performance_dashboard',
    'create_trade_timeline',
    'create_extension_signal_map',
    'add_equity_curve_plot',
    'add_performance_by_timeframe_plot',
    'add_monthly_returns_plot',
    'add_trade_results_by_direction_plot',
    'add_profit_distribution_plot',
    'add_timeframe_progression_plot'
]