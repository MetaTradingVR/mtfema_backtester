"""
Test script for implementing the Trade Executor with MT 9 EMA Strategy.

This script integrates the new TradeExecutor with the existing signal generation
and backtest engine components.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os

from mtfema_backtester.trading.trade_executor import TradeExecutor
from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.strategy.signal_generator import generate_signals
from mtfema_backtester.backtest.backtest_engine import execute_backtest
from mtfema_backtester.backtest.performance_metrics import calculate_performance_metrics
from mtfema_backtester.utils.performance_monitor import PerformanceMonitor
from mtfema_backtester.visualization.performance_dashboard import create_performance_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_executor_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_trade_executor_test():
    """Run a test of the TradeExecutor with the existing signal generator."""
    logger.info("Starting Trade Executor test")
    
    # Create performance monitor
    monitor = PerformanceMonitor('trade_executor_test')
    
    # Define strategy parameters
    strategy_params = {
        'ema_period': 9,
        'timeframes': {
            '1h': {'extension_threshold': 1.0},
            '4h': {'extension_threshold': 1.2},
            '1d': {'extension_threshold': 1.5}
        },
        'risk_management': {
            'account_risk_percent': 1.0,
            'max_concurrent_trades': 3,
            'default_stop_percent': 1.0,
            'lookback_bars': 5,
            'initial_balance': 10000.0
        },
        'indicators': {
            'use_paperfeet_confirmation': True
        }
    }
    
    # Create risk settings for TradeExecutor
    risk_settings = {
        'account_risk_percent': 1.0,
        'max_concurrent_trades': 3,
        'allow_mixed_directions': False,
        'max_position_size_percent': 20.0,
        'use_trailing_stop': True,
        'trailing_stop_atr_multiple': 2.0,
        'reward_risk_ratio': 2.0,
        'use_progressive_targeting': True,
        'target_hit_stop_policy': 'breakeven',
    }
    
    # Define output directory
    output_dir = 'output/trade_executor_test'
    os.makedirs(output_dir, exist_ok=True)
    
    # Look for test data
    symbol = 'NQ'
    csv_path = f'data/{symbol.lower()}_test_data.csv'
    h5_path = f'data/{symbol.lower()}_data.h5'
    
    logger.info("Loading test data")
    
    try:
        # Initialize TimeframeData
        tf_data = TimeframeData()
        
        # Try to load from CSV first, then H5 if CSV doesn't exist
        if os.path.exists(csv_path):
            logger.info(f"Loading data from {csv_path}")
            tf_data.load_from_csv(csv_path)
        elif os.path.exists(h5_path):
            logger.info(f"Loading data from {h5_path}")
            tf_data.load_from_h5(h5_path)
        else:
            logger.error(f"No data found at {csv_path} or {h5_path}")
            return
            
        # Calculate indicators
        logger.info("Calculating indicators")
        with monitor.measure_performance('indicator_calculation'):
            tf_data.calculate_indicators(ema_period=strategy_params['ema_period'])
        
        # Generate signals
        logger.info("Generating trading signals")
        with monitor.measure_performance('signal_generation'):
            signals = generate_signals(tf_data, strategy_params)
        
        if signals.empty:
            logger.warning("No signals generated")
            return
            
        logger.info(f"Generated {len(signals)} signals")
        
        # Initialize TradeExecutor 
        logger.info("Initializing TradeExecutor for signal processing")
        
        # We can implement a simple wrapper to adapt our signal format to TradeExecutor
        # This demonstrates how to integrate the new TradeExecutor with existing code
        executor = TradeExecutor(
            strategy=None,  # We don't need a strategy instance as we're using our signal generator
            account_balance=strategy_params['risk_management']['initial_balance'],
            risk_settings=risk_settings
        )
        
        # Execute backtest with the generated signals
        logger.info("Running backtest with signals")
        with monitor.measure_performance('backtest'):
            # Option 1: Use existing backtest engine (for comparison)
            trades, final_balance, equity_curve = execute_backtest(signals, tf_data, strategy_params)
            logger.info(f"Backtest engine results: Final balance: ${final_balance:.2f}, Trade count: {len(trades)}")
            
            # Option 2: Use the TradeExecutor directly
            logger.info("Running backtest with TradeExecutor")
            
            # Get historical data in the format TradeExecutor needs
            timeframe_data = {}
            for tf in tf_data.timeframes:
                df = tf_data.get_dataframe(tf)
                if df is not None and not df.empty:
                    # Get the latest data point for each timeframe
                    timeframe_data[tf] = df.iloc[-1].to_dict()
            
            # Process signals with the executor
            executor_trades = []
            for signal in signals.to_dict('records'):
                # Convert signal format to what TradeExecutor expects
                adapted_signal = {
                    'entry_time': signal['datetime'],
                    'timeframe': signal['timeframe'],
                    'direction': signal['type'],
                    'entry_price': signal['entry_price'],
                    'stop_price': signal['stop_price'],
                    'target_price': signal['entry_price'] * (1.02 if signal['type'] == 'long' else 0.98),  # Simple 2% target
                    'target_timeframe': signal['timeframe'],  # We'll keep it in same timeframe for simplicity
                    'risk_factor': 1.0
                }
                
                # Process the signal through the executor
                position = executor.process_signal(adapted_signal, timeframe_data)
                if position:
                    executor_trades.append(position)
        
        # Calculate performance metrics for backtest engine results
        logger.info("Calculating performance metrics for backtest engine")
        with monitor.measure_performance('metrics_calculation_backtest'):
            backtest_metrics = calculate_performance_metrics(trades, equity_curve)
        
        # Log backtest engine metrics
        logger.info("Backtest engine performance:")
        logger.info(f"Final balance: ${backtest_metrics['final_balance']:.2f}")
        logger.info(f"Total return: {backtest_metrics['total_return_pct']:.2f}%")
        logger.info(f"Win rate: {backtest_metrics['win_rate']:.2f}%")
        logger.info(f"Profit factor: {backtest_metrics['profit_factor']:.2f}")
        
        # Calculate and log TradeExecutor metrics
        logger.info("\nTradeExecutor performance:")
        executor_metrics = executor.get_performance_metrics()
        
        logger.info(f"Final balance: ${executor.account_balance:.2f}")
        logger.info(f"Total trades: {executor_metrics['trade_count']}")
        logger.info(f"Win count: {executor_metrics['win_count']}")
        logger.info(f"Loss count: {executor_metrics['loss_count']}")
        if executor_metrics['trade_count'] > 0:
            win_rate = (executor_metrics['win_count'] / executor_metrics['trade_count']) * 100
            logger.info(f"Win rate: {win_rate:.2f}%")
        
        if executor_metrics['total_loss'] != 0:
            profit_factor = abs(executor_metrics['total_profit'] / executor_metrics['total_loss'])
            logger.info(f"Profit factor: {profit_factor:.2f}")
            
        # Create performance dashboard for backtest engine results
        logger.info("\nCreating performance dashboards")
        backtest_dashboard_path = Path(output_dir) / 'backtest_engine_dashboard.html'
        
        with monitor.measure_performance('dashboard_creation_backtest'):
            backtest_dashboard = create_performance_dashboard(
                trades_df=trades, 
                timeframe_data=tf_data,
                metrics=backtest_metrics,
                equity_curve=equity_curve,
                params=strategy_params
            )
            
            # Save dashboard to HTML
            with open(str(backtest_dashboard_path), 'w') as f:
                f.write(backtest_dashboard.to_html())
            logger.info(f"Backtest dashboard saved to {backtest_dashboard_path}")
            
        # Create simplified dashboard for TradeExecutor results
        executor_dashboard_path = Path(output_dir) / 'trade_executor_dashboard.html'
        
        # Convert executor positions to pandas DataFrame for visualization
        if executor.closed_positions:
            # Create a DataFrame from closed positions
            executor_trades_df = pd.DataFrame(executor.closed_positions)
            
            # Convert equity curve to DataFrame
            executor_equity_curve = pd.DataFrame(executor.get_equity_curve(), 
                                              columns=['datetime', 'balance'])
            
            with monitor.measure_performance('dashboard_creation_executor'):
                executor_dashboard = create_performance_dashboard(
                    trades_df=executor_trades_df,
                    timeframe_data=tf_data,
                    metrics=executor_metrics,
                    equity_curve=executor_equity_curve,
                    params=strategy_params
                )
                
                # Save dashboard to HTML
                with open(str(executor_dashboard_path), 'w') as f:
                    f.write(executor_dashboard.to_html())
                logger.info(f"TradeExecutor dashboard saved to {executor_dashboard_path}")
        else:
            logger.warning("No closed positions from TradeExecutor for dashboard creation")
        
    except Exception as e:
        logger.exception(f"Error in backtest: {str(e)}")
    
    # Print performance stats
    logger.info(f"Indicator calculation took {monitor.get_execution_time('indicator_calculation'):.2f} seconds")
    logger.info(f"Signal generation took {monitor.get_execution_time('signal_generation'):.2f} seconds")
    logger.info(f"Backtest took {monitor.get_execution_time('backtest'):.2f} seconds")
    
if __name__ == "__main__":
    run_trade_executor_test()
