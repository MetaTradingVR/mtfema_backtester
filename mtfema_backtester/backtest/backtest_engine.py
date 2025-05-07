"""
Backtest engine for the Multi-Timeframe 9 EMA Extension Strategy Backtester.

This module handles trade simulation, execution, and tracking based on generated signals.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

from mtfema_backtester.utils.timeframe_utils import get_next_timeframe_in_hierarchy
from mtfema_backtester.strategy.conflict_resolver import (
    check_timeframe_conflict, 
    adjust_risk_for_conflict,
    get_target_for_timeframe
)

logger = logging.getLogger(__name__)

def execute_backtest(signals, timeframe_data, params):
    """
    Execute backtest with generated signals.
    
    Args:
        signals: DataFrame of trade signals
        timeframe_data: TimeframeData instance with price data
        params: Strategy parameters
        
    Returns:
        tuple: (trades_df, final_balance, equity_curve)
    """
    if signals.empty:
        logger.warning("No signals to backtest")
        return pd.DataFrame(), params.get_param('risk_management.initial_balance', 10000.0), pd.DataFrame()
    
    # Initialize tracking variables
    trades = []
    account_balance = params.get_param('risk_management.initial_balance', 10000.0)
    risk_pct = params.get_param('risk_management.account_risk_percent', 1.0) / 100.0
    equity_points = [(signals.iloc[0]['datetime'], account_balance)]
    
    # Get reference timeframe for context
    reference_tf = params.get_param('timeframes.reference_timeframe', '4h')
    
    # Track active trades
    active_trades = []
    
    # Process signals in chronological order
    signals = signals.sort_values('datetime')
    
    for idx, signal in signals.iterrows():
        # Skip signal if too many active trades
        max_trades = params.get_param('risk_management.max_concurrent_trades', 3)
        if len(active_trades) >= max_trades:
            logger.info(f"Skipping signal at {signal['datetime']} due to max trades limit ({max_trades})")
            continue
        
        # Skip signal if we already have a trade in this timeframe
        if any(t['timeframe'] == signal['timeframe'] for t in active_trades):
            logger.info(f"Skipping signal at {signal['datetime']} because we already have a trade in {signal['timeframe']}")
            continue
        
        tf = signal['timeframe']
        entry_time = signal['datetime']
        signal_type = signal['type']  # 'LONG' or 'SHORT'
        
        # Get data for this timeframe
        data = timeframe_data.get_timeframe(tf)
        if data is None or data.empty:
            logger.warning(f"No data available for timeframe {tf}")
            continue
            
        # Check reference timeframe for conflicts
        conflict_type = "None"
        adjusted_risk = risk_pct
        
        if reference_tf in timeframe_data.get_available_timeframes():
            # Check for conflicts between signal timeframe and reference timeframe
            conflict_type = check_timeframe_conflict(timeframe_data, tf, reference_tf, entry_time)
            
            # Adjust risk based on conflict
            adjusted_risk = adjust_risk_for_conflict(risk_pct, conflict_type)
            logger.info(f"Conflict check: {conflict_type}, risk adjusted from {risk_pct:.2%} to {adjusted_risk:.2%}")
        
        # Calculate position size
        risk_amount = account_balance * adjusted_risk
        risk_per_unit = abs(signal['entry_price'] - signal['stop_price'])
        if risk_per_unit <= 0:
            logger.warning(f"Invalid risk per unit: {risk_per_unit}. Skipping signal.")
            continue
            
        position_size = risk_amount / risk_per_unit
        
        # Limit position size based on max trade size parameter
        max_position_pct = params.get_param('risk_management.max_position_size_percent', 20.0) / 100.0
        max_position_size = account_balance * max_position_pct / signal['entry_price']
        position_size = min(position_size, max_position_size)
        
        # Get target timeframe and price
        target_tf = get_next_timeframe_in_hierarchy(tf)
        target_price = get_target_for_timeframe(timeframe_data, target_tf, signal_type)
        
        # If target price not available, use reward-risk ratio to set target
        if target_price is None:
            reward_risk_ratio = params.get_param('risk_management.reward_risk_ratio', 2.0)
            risk = abs(signal['entry_price'] - signal['stop_price'])
            
            if signal_type == 'LONG':
                target_price = signal['entry_price'] + (risk * reward_risk_ratio)
            else:  # SHORT
                target_price = signal['entry_price'] - (risk * reward_risk_ratio)
        
        # Create trade object
        trade = {
            'entry_time': entry_time,
            'entry_price': signal['entry_price'],
            'stop_price': signal['stop_price'],
            'target_price': target_price,
            'position_size': position_size,
            'type': signal_type,
            'timeframe': tf,
            'target_timeframe': target_tf,
            'conflict_type': conflict_type,
            'status': 'open',
            'exit_time': None,
            'exit_price': None,
            'exit_reason': None,
            'profit': 0.0,
            'profit_pct': 0.0,
            'duration': 0.0,
        }
        
        # Add to active trades
        active_trades.append(trade)
        logger.info(f"Opened {signal_type} trade on {tf} at {signal['entry_price']} with size {position_size:.2f}")
    
    # For each timeframe, get data after the last signal
    future_data = {}
    for tf in timeframe_data.get_available_timeframes():
        data = timeframe_data.get_timeframe(tf)
        if data is not None and not data.empty:
            future_data[tf] = data
    
    # Simulate trades through all available data
    for tf, data in future_data.items():
        # Skip if no active trades in this timeframe
        if not any(t['timeframe'] == tf and t['status'] == 'open' for t in active_trades):
            continue
            
        # Process each bar
        for idx, row in data.iterrows():
            # Skip bars before the first signal
            if idx < signals['datetime'].min():
                continue
                
            # Process all active trades for this timeframe
            for trade in active_trades:
                if trade['timeframe'] == tf and trade['status'] == 'open' and trade['entry_time'] < idx:
                    # Check for stop hit
                    if (trade['type'] == 'LONG' and row['Low'] <= trade['stop_price']) or \
                       (trade['type'] == 'SHORT' and row['High'] >= trade['stop_price']):
                        # Stop hit
                        close_trade(trade, idx, trade['stop_price'], 'stop_hit')
                        logger.info(f"Stop hit for {trade['type']} trade on {tf} at {trade['stop_price']}")
                        
                    # Check for target hit
                    elif (trade['type'] == 'LONG' and row['High'] >= trade['target_price']) or \
                         (trade['type'] == 'SHORT' and row['Low'] <= trade['target_price']):
                        # Target hit
                        close_trade(trade, idx, trade['target_price'], 'target_hit')
                        logger.info(f"Target hit for {trade['type']} trade on {tf} at {trade['target_price']}")
                        
                        # Check for progression to next timeframe
                        if params.get_param('strategy.use_progressive_targeting', True):
                            # Create new trade targeting the next timeframe
                            create_progression_trade(trade, idx, row['Close'], active_trades, timeframe_data, params)
    
    # Close any remaining open trades at the last available price
    for trade in active_trades:
        if trade['status'] == 'open':
            tf = trade['timeframe']
            if tf in future_data and not future_data[tf].empty:
                last_price = future_data[tf]['Close'].iloc[-1]
                last_time = future_data[tf].index[-1]
                close_trade(trade, last_time, last_price, 'end_of_data')
                logger.info(f"Closed {trade['type']} trade on {tf} at {last_price} (end of data)")
    
    # Calculate final results
    trades_df = pd.DataFrame([t for t in active_trades if t['status'] == 'closed'])
    
    # Update account balance and create equity curve
    if not trades_df.empty:
        trades_df = trades_df.sort_values('exit_time')
        
        for _, trade in trades_df.iterrows():
            # Update account balance
            account_balance += trade['profit']
            equity_points.append((trade['exit_time'], account_balance))
    
    # Create equity curve DataFrame
    equity_curve = pd.DataFrame(equity_points, columns=['datetime', 'balance'])
    equity_curve.set_index('datetime', inplace=True)
    
    return trades_df, account_balance, equity_curve

def close_trade(trade, exit_time, exit_price, reason):
    """
    Close a trade and calculate profit/loss.
    
    Args:
        trade: Trade dictionary to update
        exit_time: Exit timestamp
        exit_price: Exit price
        reason: Reason for exit
    """
    trade['exit_time'] = exit_time
    trade['exit_price'] = exit_price
    trade['exit_reason'] = reason
    trade['status'] = 'closed'
    
    # Calculate profit
    if trade['type'] == 'LONG':
        price_diff = exit_price - trade['entry_price']
    else:  # SHORT
        price_diff = trade['entry_price'] - exit_price
        
    trade['profit'] = price_diff * trade['position_size']
    trade['profit_pct'] = price_diff / trade['entry_price']
    
    # Calculate duration in hours (assuming datetime index)
    if isinstance(exit_time, datetime) and isinstance(trade['entry_time'], datetime):
        duration_seconds = (exit_time - trade['entry_time']).total_seconds()
        trade['duration'] = duration_seconds / 3600.0  # Convert to hours
    
    # Add win/loss flag
    trade['win'] = trade['profit'] > 0

def create_progression_trade(completed_trade, current_time, current_price, active_trades, timeframe_data, params):
    """
    Create a new trade targeting the next timeframe after a successful trade.
    
    Args:
        completed_trade: The successfully completed trade
        current_time: Current timestamp
        current_price: Current price
        active_trades: List of active trades
        timeframe_data: TimeframeData instance
        params: Strategy parameters
        
    Returns:
        bool: True if progression trade was created, False otherwise
    """
    # Only progress if this was a target hit
    if completed_trade['exit_reason'] != 'target_hit':
        return False
    
    # Get next timeframe in hierarchy
    current_tf = completed_trade['timeframe']
    next_tf = get_next_timeframe_in_hierarchy(current_tf)
    
    # Check if we reached the top of the hierarchy
    if next_tf == current_tf:
        logger.info(f"Reached top of timeframe hierarchy with {current_tf}")
        return False
    
    # Check if next timeframe data is available
    next_tf_data = timeframe_data.get_timeframe(next_tf)
    if next_tf_data is None or next_tf_data.empty:
        logger.warning(f"No data available for next timeframe {next_tf}")
        return False
    
    # Check if we already have a trade in the next timeframe
    if any(t['timeframe'] == next_tf and t['status'] == 'open' for t in active_trades):
        logger.info(f"Already have an open trade in the next timeframe {next_tf}")
        return False
    
    # Get target for the next timeframe
    next_target_tf = get_next_timeframe_in_hierarchy(next_tf)
    next_target_price = get_target_for_timeframe(timeframe_data, next_target_tf, completed_trade['type'])
    
    # If target not available, use reward-risk ratio
    if next_target_price is None:
        # Get reference timeframe for context
        reference_tf = params.get_param('timeframes.reference_timeframe', '4h')
        
        # Check for conflicts between next timeframe and reference
        conflict_type = "None"
        if reference_tf in timeframe_data.get_available_timeframes():
            conflict_type = check_timeframe_conflict(timeframe_data, next_tf, reference_tf, current_time)
        
        # Use a wider stop for progression trades
        stop_buffer = params.get_param('risk_management.progression_stop_buffer', 1.5)
        
        # Calculate stop based on ATR or percentage
        stop_pct = params.get_param('risk_management.default_stop_percent', 0.01) * stop_buffer
        
        if completed_trade['type'] == 'LONG':
            stop_price = current_price * (1 - stop_pct)
            
            # Calculate target using reward-risk ratio
            reward_risk_ratio = params.get_param('risk_management.reward_risk_ratio', 2.0)
            risk = current_price - stop_price
            next_target_price = current_price + (risk * reward_risk_ratio)
            
        else:  # SHORT
            stop_price = current_price * (1 + stop_pct)
            
            # Calculate target using reward-risk ratio
            reward_risk_ratio = params.get_param('risk_management.reward_risk_ratio', 2.0)
            risk = stop_price - current_price
            next_target_price = current_price - (risk * reward_risk_ratio)
    else:
        # Use a simpler stop calculation for progression trades
        stop_pct = params.get_param('risk_management.progression_stop_percent', 0.01)
        if completed_trade['type'] == 'LONG':
            stop_price = current_price * (1 - stop_pct)
        else:  # SHORT
            stop_price = current_price * (1 + stop_pct)
    
    # Calculate position size
    account_balance = params.get_param('risk_management.initial_balance', 10000.0)
    # Sum profits from previous trades
    for trade in active_trades:
        if trade['status'] == 'closed':
            account_balance += trade['profit']
    
    # Use a smaller risk for progression trades
    progression_risk_pct = params.get_param('risk_management.progression_risk_percent', 0.5) / 100.0
    risk_amount = account_balance * progression_risk_pct
    risk_per_unit = abs(current_price - stop_price)
    
    if risk_per_unit <= 0:
        logger.warning(f"Invalid risk per unit for progression trade: {risk_per_unit}")
        return False
        
    position_size = risk_amount / risk_per_unit
    
    # Create new trade
    new_trade = {
        'entry_time': current_time,
        'entry_price': current_price,
        'stop_price': stop_price,
        'target_price': next_target_price,
        'position_size': position_size,
        'type': completed_trade['type'],  # Same direction as completed trade
        'timeframe': next_tf,
        'target_timeframe': next_target_tf,
        'conflict_type': "None",  # We'll check this later
        'status': 'open',
        'exit_time': None,
        'exit_price': None,
        'exit_reason': None,
        'profit': 0.0,
        'profit_pct': 0.0,
        'duration': 0.0,
        'is_progression': True,
        'parent_timeframe': completed_trade['timeframe']
    }
    
    # Add to active trades
    active_trades.append(new_trade)
    logger.info(f"Created progression {completed_trade['type']} trade from {completed_trade['timeframe']} to {next_tf} at {current_price}")
    
    return True 