"""
Performance metrics for backtest analysis.

This module contains functions for calculating and analyzing trade performance metrics
from backtest results.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def calculate_performance_metrics(trades_df, initial_balance=10000.0):
    """
    Calculate comprehensive performance metrics with equity curve.
    
    Args:
        trades_df: DataFrame with trade results
        initial_balance: Initial account balance
        
    Returns:
        tuple: (metrics_dict, equity_curve_df)
    """
    if trades_df.empty:
        logger.warning("No trades available for calculating performance metrics")
        return {}, pd.DataFrame()
    
    # Create equity curve with dates
    equity_curve = create_equity_curve(trades_df, initial_balance)
    
    # Standard metrics
    metrics = {
        'total_trades': len(trades_df),
        'win_rate': (trades_df['win'] == True).mean() if 'win' in trades_df.columns else 0.0,
        'profit_factor': 0.0,
        'average_win': trades_df[trades_df['win']]['profit_pct'].mean() if 'win' in trades_df.columns and len(trades_df[trades_df['win']]) > 0 else 0.0,
        'average_loss': trades_df[~trades_df['win']]['profit_pct'].mean() if 'win' in trades_df.columns and len(trades_df[~trades_df['win']]) > 0 else 0.0,
        'total_profit': trades_df['profit'].sum(),
        'total_profit_pct': trades_df['profit_pct'].sum() if 'profit_pct' in trades_df.columns else 0.0,
    }
    
    # Add max drawdown if equity curve available
    if not equity_curve.empty:
        max_dd, max_dd_pct = calculate_max_drawdown(equity_curve)
        metrics['max_drawdown'] = max_dd
        metrics['max_drawdown_pct'] = max_dd_pct
    
    # Additional metrics
    if 'duration' in trades_df.columns:
        metrics['avg_trade_duration'] = trades_df['duration'].mean()
        metrics['avg_win_duration'] = trades_df[trades_df['win']]['duration'].mean() if len(trades_df[trades_df['win']]) > 0 else 0.0
        metrics['avg_loss_duration'] = trades_df[~trades_df['win']]['duration'].mean() if len(trades_df[~trades_df['win']]) > 0 else 0.0
    
    metrics['longest_win_streak'] = calculate_longest_streak(trades_df, 'win', True)
    metrics['longest_loss_streak'] = calculate_longest_streak(trades_df, 'win', False)
    
    # Calculate reward/risk ratio
    if 'stop_price' in trades_df.columns and 'entry_price' in trades_df.columns:
        metrics['reward_risk_ratio'] = calculate_reward_risk_ratio(trades_df)
    
    # Calculate profit factor
    gross_profit = trades_df[trades_df['profit'] > 0]['profit'].sum()
    gross_loss = abs(trades_df[trades_df['profit'] < 0]['profit'].sum())
    metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Calculate Sharpe ratio if equity curve has enough data
    if len(equity_curve) > 30:
        metrics['sharpe_ratio'] = calculate_sharpe_ratio(equity_curve)
    
    # Timeframe metrics
    if 'timeframe' in trades_df.columns:
        metrics['trades_by_timeframe'] = trades_df.groupby('timeframe').size().to_dict()
        metrics['win_rate_by_timeframe'] = trades_df.groupby('timeframe')['win'].mean().to_dict()
        metrics['profit_by_timeframe'] = trades_df.groupby('timeframe')['profit'].sum().to_dict()
    
    # Signal type metrics
    if 'type' in trades_df.columns:
        metrics['trades_by_type'] = trades_df.groupby('type').size().to_dict()
        metrics['win_rate_by_type'] = trades_df.groupby('type')['win'].mean().to_dict()
        metrics['profit_by_type'] = trades_df.groupby('type')['profit'].sum().to_dict()
    
    # Conflict type metrics
    if 'conflict_type' in trades_df.columns:
        metrics['trades_by_conflict'] = trades_df.groupby('conflict_type').size().to_dict()
        metrics['win_rate_by_conflict'] = trades_df.groupby('conflict_type')['win'].mean().to_dict()
        metrics['profit_by_conflict'] = trades_df.groupby('conflict_type')['profit'].sum().to_dict()
    
    # Progressive targeting metrics
    if 'is_progression' in trades_df.columns:
        progression_trades = trades_df[trades_df['is_progression'] == True]
        if not progression_trades.empty:
            metrics['progression_trade_count'] = len(progression_trades)
            metrics['progression_win_rate'] = progression_trades['win'].mean()
            metrics['progression_profit'] = progression_trades['profit'].sum()
    
    # Monthly/Weekly returns
    if isinstance(trades_df.index, pd.DatetimeIndex) or 'exit_time' in trades_df.columns:
        date_col = trades_df.index if isinstance(trades_df.index, pd.DatetimeIndex) else trades_df['exit_time']
        
        # Monthly returns
        monthly_returns = trades_df.groupby(pd.Grouper(key=date_col, freq='M'))['profit'].sum()
        metrics['monthly_returns'] = monthly_returns.to_dict()
        metrics['avg_monthly_return'] = monthly_returns.mean()
        
        # Weekly returns
        weekly_returns = trades_df.groupby(pd.Grouper(key=date_col, freq='W'))['profit'].sum()
        metrics['weekly_returns'] = weekly_returns.to_dict()
        metrics['avg_weekly_return'] = weekly_returns.mean()
    
    logger.info(f"Calculated {len(metrics)} performance metrics")
    return metrics, equity_curve

def create_equity_curve(trades_df, initial_balance=10000.0):
    """
    Create equity curve from trades DataFrame.
    
    Args:
        trades_df: DataFrame with trade results
        initial_balance: Initial account balance
        
    Returns:
        pd.DataFrame: Equity curve DataFrame with drawdown
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    # Sort trades by exit time
    if 'exit_time' in trades_df.columns:
        sorted_trades = trades_df.sort_values('exit_time')
        time_col = 'exit_time'
    elif isinstance(trades_df.index, pd.DatetimeIndex):
        sorted_trades = trades_df.sort_index()
        time_col = 'index'
    else:
        logger.warning("No time column available for equity curve")
        return pd.DataFrame()
    
    # Create list of equity points
    equity_points = []
    balance = initial_balance
    
    # Add initial point
    if time_col == 'exit_time':
        first_time = sorted_trades[time_col].iloc[0]
        
        # Add a point just before the first trade
        if isinstance(first_time, datetime):
            initial_time = first_time - timedelta(days=1)
        else:
            initial_time = first_time
            
        equity_points.append({
            'datetime': initial_time,
            'balance': balance,
            'drawdown': 0.0,
            'drawdown_pct': 0.0,
            'peak': balance
        })
    
    # Add each trade's contribution
    running_peak = balance
    
    for _, trade in sorted_trades.iterrows():
        # Update balance
        balance += trade['profit']
        
        # Track peak
        running_peak = max(running_peak, balance)
        
        # Calculate drawdown
        drawdown = running_peak - balance
        drawdown_pct = drawdown / running_peak if running_peak > 0 else 0.0
        
        # Get timestamp
        if time_col == 'exit_time':
            timestamp = trade[time_col]
        else:
            timestamp = trade.name
        
        # Add point
        equity_points.append({
            'datetime': timestamp,
            'balance': balance,
            'drawdown': drawdown,
            'drawdown_pct': drawdown_pct,
            'peak': running_peak
        })
    
    # Convert to DataFrame
    equity_df = pd.DataFrame(equity_points)
    
    # Set datetime as index
    if not equity_df.empty:
        equity_df.set_index('datetime', inplace=True)
    
    return equity_df

def calculate_max_drawdown(equity_curve):
    """
    Calculate maximum drawdown from equity curve.
    
    Args:
        equity_curve: Equity curve DataFrame
        
    Returns:
        tuple: (max_drawdown_amount, max_drawdown_percentage)
    """
    if 'drawdown' in equity_curve.columns:
        max_dd = equity_curve['drawdown'].max()
        max_dd_pct = equity_curve['drawdown_pct'].max()
    else:
        # Calculate max drawdown from balance
        peak = equity_curve['balance'].expanding().max()
        drawdown = (equity_curve['balance'] - peak) / peak
        max_dd = (equity_curve['balance'] - peak).min()
        max_dd_pct = drawdown.min()
    
    return float(max_dd), float(max_dd_pct)

def calculate_longest_streak(trades_df, column='win', value=True):
    """
    Calculate the longest streak of a certain value in a column.
    
    Args:
        trades_df: DataFrame with trades
        column: Column to check
        value: Value to look for streaks of
        
    Returns:
        int: Longest streak
    """
    if column not in trades_df.columns or trades_df.empty:
        return 0
    
    # Convert to series of 1s and 0s
    streak_series = (trades_df[column] == value).astype(int)
    
    # Calculate streak lengths
    streak_changes = streak_series.diff().fillna(streak_series.iloc[0]).abs()
    streak_start_indices = streak_changes[streak_changes == 1].index.tolist()
    streak_start_indices.append(trades_df.index[-1])
    
    # Calculate streak lengths
    current_streak = 0
    max_streak = 0
    
    for i in range(len(streak_series)):
        if streak_series.iloc[i] == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    return max_streak

def calculate_reward_risk_ratio(trades_df):
    """
    Calculate reward-to-risk ratio from trades.
    
    Args:
        trades_df: DataFrame with trade results
        
    Returns:
        float: Reward-to-risk ratio
    """
    if 'entry_price' not in trades_df.columns or 'stop_price' not in trades_df.columns or trades_df.empty:
        return 0.0
    
    total_reward = 0.0
    total_risk = 0.0
    
    for _, trade in trades_df.iterrows():
        # Calculate realized reward
        if trade['type'] == 'LONG':
            reward = trade['exit_price'] - trade['entry_price']
            risk = trade['entry_price'] - trade['stop_price']
        else:  # SHORT
            reward = trade['entry_price'] - trade['exit_price']
            risk = trade['stop_price'] - trade['entry_price']
        
        if risk > 0:
            total_reward += reward
            total_risk += risk
    
    return total_reward / total_risk if total_risk > 0 else 0.0

def calculate_sharpe_ratio(equity_curve, risk_free_rate=0.0, days_per_year=252):
    """
    Calculate Sharpe ratio from equity curve.
    
    Args:
        equity_curve: Equity curve DataFrame
        risk_free_rate: Annual risk-free rate
        days_per_year: Trading days per year
        
    Returns:
        float: Sharpe ratio
    """
    if equity_curve.empty or 'balance' not in equity_curve.columns:
        return 0.0
    
    # Calculate daily returns
    daily_returns = equity_curve['balance'].pct_change().dropna()
    
    if len(daily_returns) < 2:
        return 0.0
    
    # Convert annual risk-free rate to daily
    daily_risk_free = ((1 + risk_free_rate) ** (1 / days_per_year)) - 1
    
    # Calculate excess returns
    excess_returns = daily_returns - daily_risk_free
    
    # Calculate Sharpe ratio
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(days_per_year)
    
    return float(sharpe)

def calculate_avg_duration(trades_df):
    """
    Calculate average trade duration in hours.
    
    Args:
        trades_df: DataFrame with trade results
        
    Returns:
        float: Average duration in hours
    """
    if 'duration' not in trades_df.columns or trades_df.empty:
        return 0.0
    
    return trades_df['duration'].mean()

def get_summary_statistics(trades_df, metrics, initial_balance=10000.0):
    """
    Get a text summary of performance statistics.
    
    Args:
        trades_df: DataFrame with trade results
        metrics: Dictionary of performance metrics
        initial_balance: Initial account balance
        
    Returns:
        str: Formatted summary text
    """
    if trades_df.empty or not metrics:
        return "No trades available for performance summary."
    
    summary = []
    summary.append("====== Performance Summary ======")
    summary.append(f"Total trades: {metrics.get('total_trades', 0)}")
    summary.append(f"Win rate: {metrics.get('win_rate', 0):.2%}")
    summary.append(f"Profit factor: {metrics.get('profit_factor', 0):.2f}")
    summary.append(f"Total profit: ${metrics.get('total_profit', 0):.2f}")
    
    # Calculate ROI
    roi = metrics.get('total_profit', 0) / initial_balance
    summary.append(f"Return on investment: {roi:.2%}")
    
    # Add drawdown info
    if 'max_drawdown' in metrics and 'max_drawdown_pct' in metrics:
        summary.append(f"Max drawdown: ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_pct']:.2%})")
    
    # Add Sharpe ratio
    if 'sharpe_ratio' in metrics:
        summary.append(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
    
    # Add trade stats
    summary.append("\n--- Trade Statistics ---")
    summary.append(f"Average profit: {metrics.get('average_win', 0):.2%}")
    summary.append(f"Average loss: {metrics.get('average_loss', 0):.2%}")
    
    if 'reward_risk_ratio' in metrics:
        summary.append(f"Reward-to-risk ratio: {metrics['reward_risk_ratio']:.2f}")
    
    if 'avg_trade_duration' in metrics:
        summary.append(f"Average trade duration: {metrics['avg_trade_duration']:.2f} hours")
    
    summary.append(f"Longest win streak: {metrics.get('longest_win_streak', 0)}")
    summary.append(f"Longest loss streak: {metrics.get('longest_loss_streak', 0)}")
    
    # Add timeframe breakdown
    if 'trades_by_timeframe' in metrics:
        summary.append("\n--- Timeframe Breakdown ---")
        for tf, count in metrics['trades_by_timeframe'].items():
            win_rate = metrics['win_rate_by_timeframe'].get(tf, 0)
            profit = metrics['profit_by_timeframe'].get(tf, 0)
            summary.append(f"{tf}: {count} trades, Win rate: {win_rate:.2%}, Profit: ${profit:.2f}")
    
    # Add trade type breakdown
    if 'trades_by_type' in metrics:
        summary.append("\n--- Trade Type Breakdown ---")
        for type_val, count in metrics['trades_by_type'].items():
            win_rate = metrics['win_rate_by_type'].get(type_val, 0)
            profit = metrics['profit_by_type'].get(type_val, 0)
            summary.append(f"{type_val}: {count} trades, Win rate: {win_rate:.2%}, Profit: ${profit:.2f}")
    
    # Add conflict analysis if available
    if 'trades_by_conflict' in metrics:
        summary.append("\n--- Conflict Analysis ---")
        for conflict, count in metrics['trades_by_conflict'].items():
            win_rate = metrics['win_rate_by_conflict'].get(conflict, 0)
            profit = metrics['profit_by_conflict'].get(conflict, 0)
            summary.append(f"{conflict}: {count} trades, Win rate: {win_rate:.2%}, Profit: ${profit:.2f}")
    
    # Add progressive targeting stats if available
    if 'progression_trade_count' in metrics:
        summary.append("\n--- Progressive Targeting ---")
        count = metrics['progression_trade_count']
        win_rate = metrics['progression_win_rate']
        profit = metrics['progression_profit']
        summary.append(f"Progression trades: {count}, Win rate: {win_rate:.2%}, Profit: ${profit:.2f}")
    
    return "\n".join(summary) 