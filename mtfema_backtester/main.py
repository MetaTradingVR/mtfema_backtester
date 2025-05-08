import os
import sys
import argparse
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add the project directory to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup TA-Lib or alternative first
from mtfema_backtester.utils.talib_installer import setup_talib
# Try to setup TA-Lib (will fall back to pandas-ta if needed)
setup_talib()

# Import modules from the project
from mtfema_backtester.data.data_loader import DataLoader
from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.indicators.ema import calculate_ema, detect_9ema_extension
from mtfema_backtester.indicators.bollinger import calculate_bollinger_bands, detect_bollinger_breakouts
from mtfema_backtester.indicators.paperfeet import calculate_paperfeet_rsi
from mtfema_backtester.strategy.extension_detector import detect_extensions
from mtfema_backtester.strategy.reclamation_detector import ReclamationDetector
from mtfema_backtester.visualization.plot_indicators import plot_ema_extension, plot_bollinger_bands
from mtfema_backtester.utils.logger import setup_logger
from mtfema_backtester.backtest.backtest_engine import BacktestEngine
from mtfema_backtester.config import BACKTEST_CONFIG, RISK_PARAMS, STRATEGY_PARAMS

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MTF EMA Extension Strategy Backtester")
    
    # Data parameters
    parser.add_argument("--symbol", type=str, default="SPY", 
                        help="Trading symbol to download (default: SPY)")
    parser.add_argument("--start-date", type=str, default=None,
                        help="Start date for backtesting (format: YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None,
                        help="End date for backtesting (format: YYYY-MM-DD)")
    
    # Timeframe parameters
    parser.add_argument("--timeframes", type=str, default="1d,1h,15m",
                        help="Comma-separated list of timeframes (default: 1d,1h,15m)")
    
    # Strategy parameters
    parser.add_argument("--ema-period", type=int, default=9,
                        help="EMA period (default: 9)")
    parser.add_argument("--extension-threshold", type=float, default=1.0,
                        help="Extension threshold percentage (default: 1.0)")
    
    # Backtest parameters
    parser.add_argument("--initial-capital", type=float, default=BACKTEST_CONFIG["initial_capital"],
                        help=f"Initial capital for backtesting (default: {BACKTEST_CONFIG['initial_capital']})")
    parser.add_argument("--commission", type=float, default=BACKTEST_CONFIG["commission"],
                        help=f"Commission per trade (%) (default: {BACKTEST_CONFIG['commission']})")
    parser.add_argument("--risk-per-trade", type=float, default=RISK_PARAMS["max_risk_per_trade"],
                        help=f"Maximum risk per trade (%) (default: {RISK_PARAMS['max_risk_per_trade']})")
    
    # Output parameters
    parser.add_argument("--output-dir", type=str, default="./output",
                        help="Directory for output files (default: ./output)")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level (default: INFO)")
    
    # Mode parameters
    parser.add_argument("--mode", type=str, default="test",
                        choices=["test", "backtest", "optimize", "live"],
                        help="Operation mode (default: test)")
    parser.add_argument("--save-plots", action="store_true",
                        help="Save generated plots to files")
    parser.add_argument("--no-cache", action="store_true",
                        help="Disable data caching")
    
    return parser.parse_args()

def setup_environment(args):
    """Set up the environment based on command line arguments"""
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger(os.path.join(args.output_dir, "logs"), level=log_level)
    
    # Set default dates if not provided
    if args.start_date is None:
        args.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    if args.end_date is None:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Environment set up with: Symbol={args.symbol}, "
                f"Timeframes={args.timeframes}, Mode={args.mode}")
    
    return logger

def run_test_mode(args, logger):
    """Run in test mode to verify the system components"""
    logger.info("Running in TEST mode")
    
    # Initialize data loader
    data_loader = DataLoader(cache_dir=os.path.join(args.output_dir, "cache"))
    
    # Parse timeframes
    timeframes = [tf.strip() for tf in args.timeframes.split(',')]
    logger.info(f"Testing with timeframes: {timeframes}")
    
    # Load data for all timeframes
    data_dict = {}
    for tf in timeframes:
        logger.info(f"Loading {args.symbol} data for {tf} timeframe")
        data = data_loader.get_data(
            args.symbol, tf, args.start_date, args.end_date, 
            use_cache=not args.no_cache
        )
        if data is not None and not data.empty:
            data_dict[tf] = data
            logger.info(f"Loaded {len(data)} rows for {tf} timeframe")
        else:
            logger.warning(f"Failed to load data for {tf} timeframe")
    
    if not data_dict:
        logger.error("No data loaded. Exiting test mode.")
        return False
    
    # Initialize TimeframeData
    tf_data = TimeframeData(data_dict)
    
    # Process each timeframe
    for tf in tf_data.get_available_timeframes():
        logger.info(f"Processing {tf} timeframe")
        data = tf_data.get_timeframe(tf)
        
        # Calculate 9 EMA and extension
        ema, extension, signals = detect_9ema_extension(
            data, 
            ema_period=args.ema_period,
            threshold=args.extension_threshold
        )
        
        # Store indicators
        tf_data.add_indicator(tf, f"EMA_{args.ema_period}", ema)
        tf_data.add_indicator(tf, "Extension", extension)
        tf_data.add_indicator(tf, "ExtensionSignal", signals)
        
        # Calculate Bollinger Bands
        middle_band, upper_band, lower_band = calculate_bollinger_bands(data, period=20, std_dev=2.0)
        if not (middle_band.empty or upper_band.empty or lower_band.empty):
            # Ensure the data is 1-dimensional
            if hasattr(middle_band, 'values'):
                middle_band = middle_band.values
            if hasattr(upper_band, 'values'):
                upper_band = upper_band.values
            if hasattr(lower_band, 'values'):
                lower_band = lower_band.values
                
            # Create a DataFrame with all bands
            bb = pd.DataFrame({
                'Middle': middle_band,
                'Upper': upper_band,
                'Lower': lower_band
            }, index=data.index)
            tf_data.add_indicator(tf, "BollingerBands", bb)
            bb_signals = detect_bollinger_breakouts(data, upper_band, lower_band)
            tf_data.add_indicator(tf, "BollingerBreakout", bb_signals)
        
        # Calculate PaperFeet Laguerre RSI
        pf = calculate_paperfeet_rsi(data)
        if not pf.empty:
            tf_data.add_indicator(tf, "PaperFeet", pf)
        
        # Create and save plots
        if args.save_plots:
            plots_dir = os.path.join(args.output_dir, "plots")
            os.makedirs(plots_dir, exist_ok=True)
            
            # EMA Extension plot
            ema_plot = plot_ema_extension(
                data, ema, extension, signals, 
                title=f"{args.symbol} {tf} - 9 EMA Extension"
            )
            ema_plot.write_html(
                os.path.join(plots_dir, f"{args.symbol}_{tf}_ema_extension.html")
            )
            logger.info(f"Saved EMA extension plot for {tf} timeframe")
            
            # Bollinger Bands plot
            if not (middle_band.empty or upper_band.empty or lower_band.empty):
                bb_plot = plot_bollinger_bands(
                    data, bb, bb_signals,
                    title=f"{args.symbol} {tf} - Bollinger Bands"
                )
                bb_plot.write_html(
                    os.path.join(plots_dir, f"{args.symbol}_{tf}_bollinger.html")
                )
                logger.info(f"Saved Bollinger Bands plot for {tf} timeframe")
    
    logger.info("Test mode completed successfully")
    return True

def run_backtest_mode(args, logger):
    """Run in backtest mode to evaluate the strategy"""
    logger.info("Running in BACKTEST mode")
    
    # Initialize data loader
    data_loader = DataLoader(cache_dir=os.path.join(args.output_dir, "cache"))
    
    # Parse timeframes
    timeframes = [tf.strip() for tf in args.timeframes.split(',')]
    logger.info(f"Backtesting with timeframes: {timeframes}")
    
    # Load data for all timeframes
    data_dict = {}
    for tf in timeframes:
        logger.info(f"Loading {args.symbol} data for {tf} timeframe")
        data = data_loader.get_data(
            args.symbol, tf, args.start_date, args.end_date, 
            use_cache=not args.no_cache
        )
        if data is not None and not data.empty:
            data_dict[tf] = data
            logger.info(f"Loaded {len(data)} rows for {tf} timeframe")
        else:
            logger.warning(f"Failed to load data for {tf} timeframe")
    
    if not data_dict:
        logger.error("No data loaded. Exiting backtest mode.")
        return False
    
    # Initialize TimeframeData
    tf_data = TimeframeData(data_dict)
    
    # Calculate indicators for all timeframes
    for tf in tf_data.get_available_timeframes():
        logger.info(f"Calculating indicators for {tf} timeframe")
        data = tf_data.get_timeframe(tf)
        
        # Calculate 9 EMA
        ema = calculate_ema(data, period=args.ema_period)
        tf_data.add_indicator(tf, f"EMA_{args.ema_period}", ema)
        
        # Calculate Bollinger Bands
        middle_band, upper_band, lower_band = calculate_bollinger_bands(data, period=20, std_dev=2.0)
        if not (middle_band.empty or upper_band.empty or lower_band.empty):
            # Ensure the data is 1-dimensional
            if hasattr(middle_band, 'values'):
                middle_band = middle_band.values
            if hasattr(upper_band, 'values'):
                upper_band = upper_band.values
            if hasattr(lower_band, 'values'):
                lower_band = lower_band.values
                
            # Create a DataFrame with all bands
            bb = pd.DataFrame({
                'Middle': middle_band,
                'Upper': upper_band,
                'Lower': lower_band
            }, index=data.index)
            tf_data.add_indicator(tf, "BollingerBands", bb)
        
        # Calculate PaperFeet Laguerre RSI
        pf = calculate_paperfeet_rsi(data)
        if not pf.empty:
            tf_data.add_indicator(tf, "PaperFeet", pf)
    
    # Setup backtest engine
    backtest = BacktestEngine(
        timeframe_data=tf_data,
        initial_capital=args.initial_capital,
        commission=args.commission / 100.0,  # Convert from percentage to decimal
        slippage=BACKTEST_CONFIG["slippage"],
        execution_delay=BACKTEST_CONFIG["execution_delay"],
        enable_fractional_shares=BACKTEST_CONFIG["enable_fractional_shares"]
    )
    
    # Override risk parameters
    if args.risk_per_trade != RISK_PARAMS["max_risk_per_trade"]:
        RISK_PARAMS["max_risk_per_trade"] = args.risk_per_trade
    
    # Run backtest
    logger.info("Starting backtest...")
    results = backtest.run()
    
    # Save results
    output_dir = os.path.join(args.output_dir, "backtest")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save equity curve
    equity_curve = pd.DataFrame({
        'Equity': results['equity_curve']
    })
    equity_curve.to_csv(os.path.join(output_dir, f"{args.symbol}_equity_curve.csv"))
    
    # Save trade list
    trades = results['trades']
    trades_df = pd.DataFrame([t.to_dict() for t in trades])
    trades_df.to_csv(os.path.join(output_dir, f"{args.symbol}_trades.csv"), index=False)
    
    # Save performance metrics
    metrics = results['metrics']
    with open(os.path.join(output_dir, f"{args.symbol}_metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=4)
    
    # Print summary
    logger.info("\n--- Backtest Results ---")
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    logger.info(f"Initial Capital: ${args.initial_capital:.2f}")
    logger.info(f"Final Equity: ${results['equity_curve'][-1]:.2f}")
    logger.info(f"Total Return: {(results['equity_curve'][-1] / args.initial_capital - 1) * 100:.2f}%")
    logger.info(f"Total Trades: {metrics['total_trades']}")
    logger.info(f"Win Rate: {metrics['win_rate'] * 100:.2f}%")
    logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}")
    logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    # Generate and save plots
    if args.save_plots:
        plots_dir = os.path.join(output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        # Equity curve plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=results['equity_curve'],
            mode='lines',
            name='Equity',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title=f"{args.symbol} - Equity Curve",
            xaxis_title="Trade",
            yaxis_title="Equity ($)",
            template="plotly_white"
        )
        fig.write_html(os.path.join(plots_dir, f"{args.symbol}_equity_curve.html"))
        
        # Trade distribution plot
        if trades:
            # Calculate returns for each trade
            returns = [t.profit / args.initial_capital * 100 for t in trades]
            
            # Create trade distribution plot
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=returns,
                nbinsx=20,
                marker_color='blue',
                opacity=0.7,
                name='Trade Returns'
            ))
            fig.update_layout(
                title=f"{args.symbol} - Trade Return Distribution",
                xaxis_title="Return (%)",
                yaxis_title="Frequency",
                template="plotly_white"
            )
            fig.write_html(os.path.join(plots_dir, f"{args.symbol}_trade_distribution.html"))
            
            # Monthly returns heatmap
            if trades_df.shape[0] > 0:
                # Convert entry_time to datetime if it's a string
                trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
                
                # Extract month and year from entry_time
                trades_df['month'] = trades_df['entry_time'].dt.month
                trades_df['year'] = trades_df['entry_time'].dt.year
                
                # Group by month and year and sum profits
                monthly_returns = trades_df.groupby(['year', 'month'])['profit'].sum().reset_index()
                
                # Pivot the data for heatmap
                pivot_returns = monthly_returns.pivot(index='month', columns='year', values='profit')
                
                # Create a mask for NaN values
                mask = pivot_returns.isnull()
                
                # Create the monthly returns heatmap
                fig = go.Figure(data=go.Heatmap(
                    z=pivot_returns.values,
                    x=pivot_returns.columns,
                    y=pivot_returns.index,
                    colorscale='RdYlGn',
                    colorbar=dict(title='Profit ($)'),
                    zauto=True
                ))
                fig.update_layout(
                    title=f"{args.symbol} - Monthly Returns Heatmap",
                    xaxis_title="Year",
                    yaxis_title="Month",
                    template="plotly_white"
                )
                fig.write_html(os.path.join(plots_dir, f"{args.symbol}_monthly_returns.html"))
    
    logger.info(f"Backtest results saved to {output_dir}")
    return True

def run_optimize_mode(args, logger):
    """Run in optimize mode to find optimal parameters"""
    logger.info("Running in OPTIMIZE mode")
    logger.warning("Optimize mode not fully implemented yet")
    # Placeholder for future implementation
    return False

def run_live_mode(args, logger):
    """Run in live mode for real-time analysis"""
    logger.info("Running in LIVE mode")
    logger.warning("Live mode not fully implemented yet")
    # Placeholder for future implementation
    return False

def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_args()
    
    # Setup environment and logging
    logger = setup_environment(args)
    
    try:
        logger.info(f"Starting MTF EMA Extension Backtester")
        
        # Run in the specified mode
        if args.mode == "test":
            success = run_test_mode(args, logger)
        elif args.mode == "backtest":
            success = run_backtest_mode(args, logger)
        elif args.mode == "optimize":
            success = run_optimize_mode(args, logger)
        elif args.mode == "live":
            success = run_live_mode(args, logger)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            success = False
        
        if success:
            logger.info(f"Successfully completed {args.mode} mode")
            return 0
        else:
            logger.error(f"Failed to complete {args.mode} mode")
            return 1
            
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())