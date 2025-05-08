"""
Simplified test script for implementing the Trade Executor.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os
import sys
import random

# Ensure we can import from our local modules
sys.path.append('.')

# Import our own module directly
from mtfema_backtester.trading.trade_executor import TradeExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fixed_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_mock_signals(count=10, symbol="NQ"):
    """Generate mock trading signals for testing."""
    signals = []
    base_price = 18000.0
    
    for i in range(count):
        # Randomly choose long or short
        direction = random.choice(['long', 'short'])
        
        # Create entry price with some variance
        entry_price = base_price + random.uniform(-100, 100)
        
        # Define stop based on direction
        stop_price = entry_price * 0.99 if direction == 'long' else entry_price * 1.01
        
        # Define target price (2:1 reward/risk ratio)
        if direction == 'long':
            target_price = entry_price + (entry_price - stop_price) * 2
        else:
            target_price = entry_price - (stop_price - entry_price) * 2
        
        # Create a signal
        signal = {
            'entry_time': datetime.now(),
            'symbol': symbol,
            'timeframe': random.choice(['1h', '4h', '1d']),
            'direction': direction,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'target_timeframe': '1d',
            'risk_factor': random.uniform(0.8, 1.0)
        }
        
        signals.append(signal)
    
    return signals

def generate_mock_price_data():
    """Generate mock price data for different timeframes."""
    timeframes = ['1h', '4h', '1d']
    base_price = 18000.0
    
    timeframe_data = {}
    
    for tf in timeframes:
        # Create simulated price data with some variance
        timeframe_data[tf] = {
            'datetime': datetime.now(),
            'open': base_price * random.uniform(0.995, 1.005),
            'high': base_price * random.uniform(1.005, 1.015),
            'low': base_price * random.uniform(0.985, 0.995),
            'close': base_price * random.uniform(0.995, 1.005),
            'volume': random.randint(10000, 50000)
        }
    
    return timeframe_data

def run_fixed_test():
    """Run a fixed test of the TradeExecutor."""
    logger.info("Starting fixed TradeExecutor test")
    
    # Create risk settings for TradeExecutor
    risk_settings = {
        'account_risk_percent': 1.0,
        'max_concurrent_trades': 5,
        'allow_mixed_directions': True,
        'max_position_size_percent': 20.0,
        'use_trailing_stop': True,
        'trailing_stop_atr_multiple': 2.0,
        'reward_risk_ratio': 2.0,
        'use_progressive_targeting': True,
        'target_hit_stop_policy': 'breakeven',
    }
    
    # Initialize TradeExecutor
    executor = TradeExecutor(
        strategy=None,  # We don't need a strategy instance as we're directly feeding signals
        account_balance=10000.0,
        risk_settings=risk_settings
    )
    
    # Generate mock signals
    signals = generate_mock_signals(count=10)
    logger.info(f"Generated {len(signals)} test signals")
    
    # Generate mock price data
    timeframe_data = generate_mock_price_data()
    
    # Process signals with the executor
    positions = []
    for signal in signals:
        position = executor.process_signal(signal, timeframe_data)
        if position:
            positions.append(position)
            logger.info(f"Created position: {position['id']} - {position['direction']} at {position['entry_price']:.2f}")
    
    logger.info(f"Created {len(positions)} positions out of {len(signals)} signals")
    
    # Get performance metrics
    metrics = executor.get_performance_metrics()
    
    # Log metrics
    logger.info("\nPerformance Metrics:")
    logger.info(f"Final balance: ${executor.account_balance:.2f}")
    logger.info(f"Total trades: {metrics.get('trade_count', 0)}")
    logger.info(f"Win count: {metrics.get('win_count', 0)}")
    logger.info(f"Loss count: {metrics.get('loss_count', 0)}")
    
    if metrics.get('trade_count', 0) > 0:
        win_rate = (metrics.get('win_count', 0) / metrics.get('trade_count', 0)) * 100
        logger.info(f"Win rate: {win_rate:.2f}%")
    
    if metrics.get('total_loss', 0) != 0:
        profit_factor = abs(metrics.get('total_profit', 0) / metrics.get('total_loss', 1))
        logger.info(f"Profit factor: {profit_factor:.2f}")
    
    # Return all the data for inspection
    return {
        'executor': executor,
        'positions': positions,
        'metrics': metrics
    }

if __name__ == "__main__":
    test_results = run_fixed_test()
    
    # Check if we have any closed positions
    closed_positions = test_results['executor'].get_closed_positions()
    if closed_positions:
        logger.info(f"\nClosed Positions: {len(closed_positions)}")
        for pos in closed_positions:
            logger.info(f"Position {pos['id']}: {pos['direction']} - P&L: ${pos.get('profit_loss', 0):.2f}")
    else:
        logger.info("No closed positions")
