#!/usr/bin/env python
"""
NQ (Nasdaq 100 futures) Test Script for MT 9 EMA Extension Strategy Backtester

This script runs a backtest with NQ data to evaluate the multi-timeframe 9 EMA extension strategy
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import json

# Import project modules
from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.data.data_loader import DataLoader
from mtfema_backtester.indicators.ema import calculate_ema, detect_9ema_extension
from mtfema_backtester.indicators.bollinger import calculate_bollinger_bands, detect_bollinger_breakouts
from mtfema_backtester.visualization.plot_indicators import plot_ema_extension, plot_bollinger_bands
from mtfema_backtester.strategy.reclamation_detector import ReclamationDetector
from mtfema_backtester.config import STRATEGY_PARAMS, StrategyParameters
from mtfema_backtester.analysis.performance_metrics import PerformanceMetrics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nq_test.log')
    ]
)
logger = logging.getLogger("nq_test")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="NQ Test for MT 9 EMA Backtester")
    
    # Data parameters
    parser.add_argument("--symbol", type=str, default="NQ",
                       help="Trading symbol to use (default: NQ)")
    parser.add_argument("--start-date", type=str, default=None,
                       help="Start date (format: YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None,
                       help="End date (format: YYYY-MM-DD)")
    parser.add_argument("--timeframes", type=str, default="1d,1h,15m",
                       help="Comma-separated list of timeframes (default: 1d,1h,15m)")
    parser.add_argument("--ema-period", type=int, default=None,
                       help="EMA period (default: from config)")
    parser.add_argument("--output-dir", type=str, default="./output/nq_test",
                       help="Directory for output files")
    parser.add_argument("--params-file", type=str, default=None,
                       help="JSON file with strategy parameters")
    parser.add_argument("--generate-params", type=str, default=None,
                       help="Generate parameter file template (specify output path)")
    parser.add_argument("--mode", type=str, choices=["test", "backtest", "optimize"], 
                       default="test", help="Test mode (default: test)")
    
    return parser.parse_args()

def normalize_timeframe(tf):
    """Normalize timeframe string to standard format"""
    # Common timeframe mappings
    mappings = {
        # Days
        '1': '1d', 'd': '1d', 'day': '1d', 'daily': '1d', '1day': '1d',
        # Hours
        'h': '1h', 'hour': '1h', '1hour': '1h', '60m': '1h', '60min': '1h',
        # Minutes
        'm': '1m', 'min': '1m', 'minute': '1m', '1minute': '1m',
        # Weeks
        'w': '1w', 'week': '1w', '1week': '1w', 'weekly': '1w',
        # Months
        'M': '1M', 'month': '1M', '1month': '1M', 'monthly': '1M'
    }
    
    # Check if already in standard format
    standard_formats = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M']
    if tf in standard_formats:
        return tf
    
    # Try direct mapping
    if tf.lower() in mappings:
        return mappings[tf.lower()]
    
    # Try to infer format
    if tf.isdigit():
        # If just a number, assume it's days
        return f"{tf}d"
    
    # Return original with warning
    logger.warning(f"Unrecognized timeframe format: {tf}, using as-is")
    return tf

def generate_parameter_template(output_path):
    """Generate a template parameter file with default values"""
    try:
        # Create a new StrategyParameters instance with default values
        params = StrategyParameters()
        
        # Save the parameters to the specified path
        params.save_params(output_path)
        
        logger.info(f"Generated parameter template at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating parameter template: {str(e)}")
        return False

def run_test_mode(args, strategy_params):
    """Run in test mode - load data and visualize indicators"""
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "cache"), exist_ok=True)
    
    # Set date range
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=365)
        
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    # Parse and normalize timeframes
    raw_timeframes = [tf.strip() for tf in args.timeframes.split(',')]
    timeframes = [normalize_timeframe(tf) for tf in raw_timeframes]
    
    logger.info(f"Running NQ test with symbol: {args.symbol}")
    logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"Timeframes: {timeframes}")
    
    # Use custom EMA period or from config
    ema_period = args.ema_period if args.ema_period is not None else strategy_params.get_param('ema.period')
    
    # Initialize data loader
    data_loader = DataLoader(cache_dir=os.path.join(args.output_dir, "cache"))
    
    # Load data for all timeframes
    data_dict = {}
    for tf in timeframes:
        logger.info(f"Loading {args.symbol} data for {tf} timeframe")
        data = data_loader.get_data(
            args.symbol, tf, start_date, end_date, use_cache=True
        )
        if data is not None and not data.empty:
            data_dict[tf] = data
            logger.info(f"Loaded {len(data)} rows for {tf} timeframe")
        else:
            logger.warning(f"Failed to load data for {tf} timeframe")
    
    if not data_dict:
        logger.error("No data loaded. Exiting.")
        return False
    
    # Initialize TimeframeData
    tf_data = TimeframeData(data_dict)
    
    # Process each timeframe
    for tf in tf_data.get_available_timeframes():
        logger.info(f"Processing {tf} timeframe")
        data = tf_data.get_timeframe(tf)
        
        # Get extension threshold for this timeframe
        threshold = strategy_params.get_extension_threshold(tf)
        logger.info(f"Using extension threshold of {threshold*100:.2f}% for {tf}")
        
        # Calculate 9 EMA and extension
        ema, extension, signals = detect_9ema_extension(
            data, 
            ema_period=ema_period,
            threshold=threshold
        )
        
        # Store indicators
        tf_data.add_indicator(tf, f"EMA_{ema_period}", ema)
        tf_data.add_indicator(tf, "Extension", extension)
        tf_data.add_indicator(tf, "ExtensionSignal", signals)
        
        # Get Bollinger Band parameters from config
        bb_period = strategy_params.get_param('bollinger.period')
        bb_std_dev = strategy_params.get_param('bollinger.std_dev')
        
        # Calculate Bollinger Bands
        middle_band, upper_band, lower_band = calculate_bollinger_bands(
            data, period=bb_period, std_dev=bb_std_dev
        )
        if not (middle_band.empty or upper_band.empty or lower_band.empty):
            # Ensure the data is 1-dimensional
            if hasattr(middle_band, 'values'):
                middle_band_values = middle_band.values
                if len(middle_band_values.shape) > 1:
                    middle_band_values = middle_band_values.flatten()
            else:
                middle_band_values = middle_band
            
            if hasattr(upper_band, 'values'):
                upper_band_values = upper_band.values
                if len(upper_band_values.shape) > 1:
                    upper_band_values = upper_band_values.flatten()
            else:
                upper_band_values = upper_band
            
            if hasattr(lower_band, 'values'):
                lower_band_values = lower_band.values
                if len(lower_band_values.shape) > 1:
                    lower_band_values = lower_band_values.flatten()
            else:
                lower_band_values = lower_band
            
            # Create a DataFrame with all bands
            bb = pd.DataFrame({
                'Middle': middle_band_values,
                'Upper': upper_band_values,
                'Lower': lower_band_values
            }, index=data.index)
            
            tf_data.add_indicator(tf, "BollingerBands", bb)
            bb_signals = detect_bollinger_breakouts(data, upper_band, lower_band)
            tf_data.add_indicator(tf, "BollingerBreakout", bb_signals)
        
        # Get reclamation confirmation bars from config
        confirmation_bars = strategy_params.get_param('ema.reclamation_confirmation_bars')
        
        # Detect EMA reclamations
        reclamation_detector = ReclamationDetector(ema_period=ema_period, confirmation_bars=confirmation_bars)
        reclamation_data = reclamation_detector.detect_reclamation(data, ema)
        if not reclamation_data.empty:
            tf_data.add_indicator(tf, "Reclamation", reclamation_data)
        
        # Create visualizations
        try:
            # EMA Extension plot
            fig_ema = plot_ema_extension(
                data.iloc[-200:],  # Last 200 bars
                ema.iloc[-200:],
                extension.iloc[-200:],
                title=f"{args.symbol} {tf} - {ema_period} EMA Extension"
            )
            
            if fig_ema is not None:
                filename = os.path.join(args.output_dir, f"{args.symbol}_{tf}_ema_extension.html")
                fig_ema.write_html(filename)
                logger.info(f"Saved EMA Extension plot to {filename}")
            
            # Bollinger Bands plot
            if not (middle_band.empty or upper_band.empty or lower_band.empty):
                bb_last_200 = bb.iloc[-200:]
                fig_bb = plot_bollinger_bands(
                    data.iloc[-200:],
                    bb_last_200,
                    bb_signals.iloc[-200:],
                    title=f"{args.symbol} {tf} - Bollinger Bands"
                )
                
                if fig_bb is not None:
                    filename = os.path.join(args.output_dir, f"{args.symbol}_{tf}_bollinger_bands.html")
                    fig_bb.write_html(filename)
                    logger.info(f"Saved Bollinger Bands plot to {filename}")
        
        except Exception as e:
            logger.error(f"Error creating visualizations for {tf}: {str(e)}")
    
    # Save summary of all indicators to a file
    try:
        summary = {
            'symbol': args.symbol,
            'timeframes': timeframes,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'indicators': {}
        }
        
        for tf in tf_data.get_available_timeframes():
            # Get indicator summary for this timeframe
            summary['indicators'][tf] = {
                'rows': len(tf_data.get_timeframe(tf)),
                'available_indicators': tf_data.get_indicators(tf)
            }
            
            # Add extension stats
            ext_signals = tf_data.get_indicator(tf, "ExtensionSignal")
            if ext_signals:
                summary['indicators'][tf]['extensions'] = {
                    'has_extension': ext_signals.get('has_extension', False),
                    'extended_up': ext_signals.get('extended_up', False),
                    'extended_down': ext_signals.get('extended_down', False),
                    'extension_percentage': ext_signals.get('extension_percentage', 0.0)
                }
            
            # Add reclamation stats if available
            reclamation_data = tf_data.get_indicator(tf, "Reclamation")
            if reclamation_data is not None and not reclamation_data.empty:
                bullish_count = reclamation_data.get('BullishReclaim', pd.Series()).sum()
                bearish_count = reclamation_data.get('BearishReclaim', pd.Series()).sum()
                
                summary['indicators'][tf]['reclamations'] = {
                    'bullish_count': int(bullish_count) if not np.isnan(bullish_count) else 0,
                    'bearish_count': int(bearish_count) if not np.isnan(bearish_count) else 0
                }
        
        # Save summary to file
        summary_file = os.path.join(args.output_dir, f"{args.symbol}_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=4)
            
        logger.info(f"Saved indicator summary to {summary_file}")
    except Exception as e:
        logger.error(f"Error saving indicator summary: {str(e)}")
    
    logger.info("NQ test completed successfully!")
    return True

def run_backtest_mode(args, strategy_params):
    """Run in backtest mode - evaluate strategy performance"""
    logger.info("Starting backtest mode")
    # TODO: Implement backtest mode with signal generation and performance metrics
    # This is a placeholder for future implementation
    logger.warning("Backtest mode not fully implemented yet")
    return True

def run_optimize_mode(args, strategy_params):
    """Run in optimize mode - test multiple parameter combinations"""
    logger.info("Starting optimization mode")
    # TODO: Implement parameter optimization
    # This is a placeholder for future implementation
    logger.warning("Optimize mode not fully implemented yet")
    return True

def main():
    """Main function"""
    args = parse_args()
    
    # Generate parameter template if requested
    if args.generate_params:
        if generate_parameter_template(args.generate_params):
            logger.info(f"Parameter template generated at {args.generate_params}")
            return True
        else:
            logger.error("Failed to generate parameter template")
            return False
    
    # Load strategy parameters
    if args.params_file:
        strategy_params = StrategyParameters(args.params_file)
    else:
        strategy_params = STRATEGY_PARAMS
    
    # Run in the selected mode
    if args.mode == "test":
        return run_test_mode(args, strategy_params)
    elif args.mode == "backtest":
        return run_backtest_mode(args, strategy_params)
    elif args.mode == "optimize":
        return run_optimize_mode(args, strategy_params)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        return False

if __name__ == "__main__":
    main() 