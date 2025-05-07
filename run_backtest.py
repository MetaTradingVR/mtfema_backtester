#!/usr/bin/env python
"""
Backtest runner for MT 9 EMA Extension Strategy.

This script runs the MT 9 EMA Extension Strategy backtest with options for 
signal generation, backtest execution, and performance visualization.
"""

import sys
import os
import argparse
import logging
import json
import pandas as pd
from datetime import datetime
import plotly.io as pio

from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.config import StrategyParameters
from mtfema_backtester.strategy.signal_generator import generate_signals
from mtfema_backtester.backtest.backtest_engine import execute_backtest
from mtfema_backtester.backtest.performance_metrics import (
    calculate_performance_metrics,
    get_summary_statistics
)
from mtfema_backtester.visualization.performance_dashboard import (
    create_performance_dashboard,
    create_trade_timeline
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='MT 9 EMA Extension Strategy Backtester'
    )
    
    # Required arguments
    parser.add_argument('symbol', type=str, help='Symbol to backtest')
    
    # Optional arguments
    parser.add_argument(
        '--start-date', type=str, default='2022-01-01',
        help='Start date for backtest (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date', type=str, default=None,
        help='End date for backtest (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--timeframes', type=str, default='1h,4h,1d',
        help='Comma-separated list of timeframes'
    )
    parser.add_argument(
        '--params-file', type=str, default=None,
        help='JSON file with strategy parameters'
    )
    parser.add_argument(
        '--output-dir', type=str, default='./results',
        help='Directory for output files'
    )
    parser.add_argument(
        '--mode', type=str, default='backtest',
        choices=['test', 'backtest', 'optimize'],
        help='Operation mode'
    )
    parser.add_argument(
        '--reference-tf', type=str, default='4h',
        help='Reference timeframe for conflict detection'
    )
    parser.add_argument(
        '--use-cache', action='store_true',
        help='Use cached data if available'
    )
    
    return parser.parse_args()

def ensure_output_dir(output_dir):
    """Ensure the output directory exists."""
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output will be saved to {output_dir}")

def load_parameters(args):
    """Load strategy parameters from file or use defaults."""
    params = StrategyParameters()
    
    # Load from file if provided
    if args.params_file:
        try:
            logger.info(f"Loading parameters from {args.params_file}")
            params.load_from_file(args.params_file)
        except Exception as e:
            logger.error(f"Error loading parameters from file: {str(e)}")
            logger.info("Using default parameters")
    
    # Set reference timeframe
    params.set_param('timeframes.reference_timeframe', args.reference_tf)
    
    # Set timeframes
    timeframe_list = [t.strip() for t in args.timeframes.split(',')]
    params.set_param('timeframes.enabled', timeframe_list)
    
    return params

def load_data(args, params):
    """Load data for backtesting."""
    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else datetime.now()
    
    # Get timeframes
    timeframes = params.get_param('timeframes.enabled')
    
    try:
        # Initialize TimeframeData
        tf_data = TimeframeData()
        
        # Load data for each timeframe
        for tf in timeframes:
            logger.info(f"Loading {args.symbol} data for {tf} timeframe")
            tf_data.load_timeframe_data(
                args.symbol, 
                tf, 
                start_date, 
                end_date,
                use_cache=args.use_cache
            )
        
        # Calculate indicators
        logger.info("Calculating indicators")
        tf_data.calculate_indicators(params)
        
        return tf_data
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        sys.exit(1)

def run_test_mode(timeframe_data, params, output_dir):
    """Run test mode - generates signals without full backtest."""
    logger.info("Running in TEST mode")
    
    # Generate signals
    signals = generate_signals(timeframe_data, params)
    
    if signals.empty:
        logger.warning("No signals generated")
        return
    
    # Save signals to CSV
    signals_file = os.path.join(output_dir, 'signals.csv')
    signals.to_csv(signals_file)
    logger.info(f"Saved {len(signals)} signals to {signals_file}")
    
    # Print signal summary
    logger.info(f"Generated {len(signals)} signals")
    if 'type' in signals.columns:
        long_count = len(signals[signals['type'] == 'LONG'])
        short_count = len(signals[signals['type'] == 'SHORT'])
        logger.info(f"LONG signals: {long_count}, SHORT signals: {short_count}")
    
    if 'timeframe' in signals.columns:
        by_tf = signals.groupby('timeframe').size()
        logger.info("Signals by timeframe:")
        for tf, count in by_tf.items():
            logger.info(f"  {tf}: {count}")

def run_backtest_mode(timeframe_data, params, output_dir):
    """Run backtest mode - full simulation with performance metrics."""
    logger.info("Running in BACKTEST mode")
    
    # Generate signals
    signals = generate_signals(timeframe_data, params)
    
    if signals.empty:
        logger.warning("No signals generated")
        return
    
    # Save signals to CSV
    signals_file = os.path.join(output_dir, 'signals.csv')
    signals.to_csv(signals_file)
    logger.info(f"Saved {len(signals)} signals to {signals_file}")
    
    # Execute backtest
    logger.info("Executing backtest")
    trades_df, final_balance, equity_curve = execute_backtest(signals, timeframe_data, params)
    
    if trades_df.empty:
        logger.warning("No trades executed")
        return
    
    # Save trades to CSV
    trades_file = os.path.join(output_dir, 'trades.csv')
    trades_df.to_csv(trades_file)
    logger.info(f"Saved {len(trades_df)} trades to {trades_file}")
    
    # Calculate performance metrics
    logger.info("Calculating performance metrics")
    initial_balance = params.get_param('risk_management.initial_balance', 10000.0)
    metrics, equity_curve = calculate_performance_metrics(trades_df, initial_balance)
    
    # Save metrics to JSON
    metrics_file = os.path.join(output_dir, 'metrics.json')
    # Convert any non-serializable objects to strings
    serializable_metrics = {}
    for k, v in metrics.items():
        if isinstance(v, dict):
            serializable_metrics[k] = {str(kk): str(vv) if not isinstance(vv, (int, float)) else vv 
                                      for kk, vv in v.items()}
        else:
            serializable_metrics[k] = str(v) if not isinstance(v, (int, float)) else v
            
    with open(metrics_file, 'w') as f:
        json.dump(serializable_metrics, f, indent=2)
    logger.info(f"Saved performance metrics to {metrics_file}")
    
    # Save equity curve to CSV
    equity_file = os.path.join(output_dir, 'equity_curve.csv')
    equity_curve.to_csv(equity_file)
    logger.info(f"Saved equity curve to {equity_file}")
    
    # Create performance dashboard
    logger.info("Creating performance dashboard")
    dashboard = create_performance_dashboard(trades_df, timeframe_data, metrics, equity_curve, params)
    dashboard_file = os.path.join(output_dir, 'dashboard.html')
    pio.write_html(dashboard, dashboard_file)
    logger.info(f"Saved performance dashboard to {dashboard_file}")
    
    # Create trade timeline
    logger.info("Creating trade timeline")
    timeline = create_trade_timeline(trades_df, timeframe_data)
    timeline_file = os.path.join(output_dir, 'trade_timeline.html')
    pio.write_html(timeline, timeline_file)
    logger.info(f"Saved trade timeline to {timeline_file}")
    
    # Print summary statistics
    summary = get_summary_statistics(trades_df, metrics, initial_balance)
    logger.info("\n" + summary)
    
    # Save summary to text file
    summary_file = os.path.join(output_dir, 'summary.txt')
    with open(summary_file, 'w') as f:
        f.write(summary)
    logger.info(f"Saved summary to {summary_file}")

def run_optimize_mode(timeframe_data, params, output_dir):
    """Run optimize mode - parameter optimization."""
    logger.info("Running in OPTIMIZE mode")
    logger.warning("Optimization mode not fully implemented yet")
    # This is a placeholder for future implementation

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Ensure output directory exists
    ensure_output_dir(args.output_dir)
    
    # Load parameters
    params = load_parameters(args)
    
    # Load data
    timeframe_data = load_data(args, params)
    
    # Run selected mode
    if args.mode == 'test':
        run_test_mode(timeframe_data, params, args.output_dir)
    elif args.mode == 'backtest':
        run_backtest_mode(timeframe_data, params, args.output_dir)
    elif args.mode == 'optimize':
        run_optimize_mode(timeframe_data, params, args.output_dir)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)
    
    logger.info("Backtest completed successfully")

if __name__ == '__main__':
    main() 