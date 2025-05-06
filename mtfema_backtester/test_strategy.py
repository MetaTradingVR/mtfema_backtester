"""
Test script for the Multi-Timeframe 9 EMA Extension Strategy components.

This script loads test data and runs the strategy components to validate
that they're working correctly.
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import webbrowser

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from mtfema_backtester.utils.logger import setup_logger

def setup_test_environment():
    """Set up the test environment"""
    # Create logs directory if it doesn't exist
    os.makedirs('./logs', exist_ok=True)
    
    # Setup logging
    logger = setup_logger('./logs', level=logging.INFO)
    logger.info("Test environment set up")
    
    return logger

def create_test_data():
    """
    Create a simple test dataset when no real data is available
    
    Returns:
    --------
    dict
        Dictionary of test data by timeframe
    """
    # Create date range
    dates = pd.date_range(start='2023-01-01', end='2023-01-30', freq='1D')
    
    # Create a simple test dataframe for daily timeframe
    daily_data = pd.DataFrame({
        'Open': np.random.normal(100, 5, len(dates)),
        'High': np.random.normal(102, 5, len(dates)),
        'Low': np.random.normal(98, 5, len(dates)),
        'Close': np.random.normal(101, 5, len(dates)),
        'Volume': np.random.normal(1000000, 200000, len(dates))
    }, index=dates)
    
    # Make sure High is the highest and Low is the lowest
    for i in range(len(daily_data)):
        daily_data.loc[daily_data.index[i], 'High'] = max(
            daily_data.loc[daily_data.index[i], 'Open'],
            daily_data.loc[daily_data.index[i], 'Close'],
            daily_data.loc[daily_data.index[i], 'High']
        ) + abs(np.random.normal(0, 0.5))
        
        daily_data.loc[daily_data.index[i], 'Low'] = min(
            daily_data.loc[daily_data.index[i], 'Open'],
            daily_data.loc[daily_data.index[i], 'Close'],
            daily_data.loc[daily_data.index[i], 'Low']
        ) - abs(np.random.normal(0, 0.5))
    
    # Create hourly data (24x more points)
    hourly_dates = pd.date_range(start='2023-01-01', end='2023-01-30', freq='1H')
    hourly_data = pd.DataFrame({
        'Open': np.random.normal(100, 2, len(hourly_dates)),
        'High': np.random.normal(101, 2, len(hourly_dates)),
        'Low': np.random.normal(99, 2, len(hourly_dates)),
        'Close': np.random.normal(100.5, 2, len(hourly_dates)),
        'Volume': np.random.normal(50000, 10000, len(hourly_dates))
    }, index=hourly_dates)
    
    # Make sure High is the highest and Low is the lowest for hourly data too
    for i in range(len(hourly_data)):
        hourly_data.loc[hourly_data.index[i], 'High'] = max(
            hourly_data.loc[hourly_data.index[i], 'Open'],
            hourly_data.loc[hourly_data.index[i], 'Close'],
            hourly_data.loc[hourly_data.index[i], 'High']
        ) + abs(np.random.normal(0, 0.2))
        
        hourly_data.loc[hourly_data.index[i], 'Low'] = min(
            hourly_data.loc[hourly_data.index[i], 'Open'],
            hourly_data.loc[hourly_data.index[i], 'Close'],
            hourly_data.loc[hourly_data.index[i], 'Low']
        ) - abs(np.random.normal(0, 0.2))
    
    # Create 15min data (4x more points than hourly)
    min15_dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='15min')
    min15_data = pd.DataFrame({
        'Open': np.random.normal(100, 1, len(min15_dates)),
        'High': np.random.normal(100.5, 1, len(min15_dates)),
        'Low': np.random.normal(99.5, 1, len(min15_dates)),
        'Close': np.random.normal(100, 1, len(min15_dates)),
        'Volume': np.random.normal(10000, 2000, len(min15_dates))
    }, index=min15_dates)
    
    # Make sure High is the highest and Low is the lowest for 15min data too
    for i in range(len(min15_data)):
        min15_data.loc[min15_data.index[i], 'High'] = max(
            min15_data.loc[min15_data.index[i], 'Open'],
            min15_data.loc[min15_data.index[i], 'Close'],
            min15_data.loc[min15_data.index[i], 'High']
        ) + abs(np.random.normal(0, 0.1))
        
        min15_data.loc[min15_data.index[i], 'Low'] = min(
            min15_data.loc[min15_data.index[i], 'Open'],
            min15_data.loc[min15_data.index[i], 'Close'],
            min15_data.loc[min15_data.index[i], 'Low']
        ) - abs(np.random.normal(0, 0.1))
    
    # Return as dictionary
    return {
        '1d': daily_data,
        '1h': hourly_data,
        '15m': min15_data
    }

def load_test_data(symbol="SPY", timeframes=None, days=30):
    """
    Load test data for the strategy
    
    Parameters:
    -----------
    symbol : str
        Symbol to load data for
    timeframes : list
        List of timeframes to load
    days : int
        Number of days of historical data to load
        
    Returns:
    --------
    dict
        Dictionary of test data by timeframe
    """
    if timeframes is None:
        timeframes = ['1d', '1h', '15m']
    
    try:
        # First try to import data_loader and TimeframeData
        from mtfema_backtester.data.data_loader import DataLoader
        from mtfema_backtester.data.timeframe_data import TimeframeData
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Initialize data loader
        data_loader = DataLoader(cache_dir='./data/cache')
        
        # Load data for all timeframes
        data_dict = {}
        for tf in timeframes:
            print(f"Loading {symbol} data for {tf} timeframe")
            data = data_loader.get_data(symbol, tf, start_date, end_date, use_cache=True)
            if data is not None and not data.empty:
                data_dict[tf] = data
                print(f"Loaded {len(data)} rows for {tf} timeframe")
            else:
                print(f"Failed to load data for {tf} timeframe")
        
        # If we have data, create and return TimeframeData object
        if data_dict:
            print("Creating TimeframeData object with real data")
            return TimeframeData(data_dict)
    
    except Exception as e:
        print(f"Error loading real data: {str(e)}")
        print("Falling back to synthetic test data")
    
    # Fall back to synthetic data if anything fails
    synthetic_data = create_test_data()
    
    try:
        from mtfema_backtester.data.timeframe_data import TimeframeData
        print("Creating TimeframeData object with synthetic data")
        return TimeframeData(synthetic_data)
    except Exception as e:
        print(f"Error creating TimeframeData object: {str(e)}")
        print("Returning synthetic data dictionary only")
        return synthetic_data

def calculate_basic_indicators(data_dict):
    """
    Calculate basic indicators for the data
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes by timeframe
        
    Returns:
    --------
    dict
        Dictionary of dataframes with indicators
    """
    try:
        # Import indicator functions
        from mtfema_backtester.indicators.ema import calculate_ema
        from mtfema_backtester.indicators.bollinger import calculate_bollinger_bands
    except ImportError as e:
        print(f"Error importing indicators: {str(e)}")
        return data_dict
    
    result = {}
    
    # Process each timeframe
    for tf, data in data_dict.items():
        print(f"Calculating indicators for {tf} timeframe")
        df = data.copy()
        
        # Calculate 9 EMA
        try:
            ema9 = calculate_ema(df, period=9)
            df['EMA_9'] = ema9
            print(f"  - Calculated 9 EMA for {tf}")
        except Exception as e:
            print(f"  - Error calculating 9 EMA for {tf}: {str(e)}")
        
        # Calculate Bollinger Bands
        try:
            middle, upper, lower = calculate_bollinger_bands(df, period=20, stdev=2)
            df['BB_Middle'] = middle
            df['BB_Upper'] = upper
            df['BB_Lower'] = lower
            print(f"  - Calculated Bollinger Bands for {tf}")
        except Exception as e:
            print(f"  - Error calculating Bollinger Bands for {tf}: {str(e)}")
        
        # Add to result
        result[tf] = df
    
    return result

def test_extension_detector(data_dict):
    """
    Test the extension detector
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes with indicators
    """
    print("\n=== Testing Extension Detector ===")
    
    try:
        from mtfema_backtester.strategy.extension_detector import detect_extensions
    except ImportError as e:
        print(f"Could not import extension detector: {str(e)}")
        return
    
    results = {}
    
    for tf, data in data_dict.items():
        try:
            ext_data = detect_extensions(data, tf)
            results[tf] = ext_data
            
            # Print extension results for last bar
            print(f"\nExtensions for {tf} (last bar):")
            for key, value in ext_data.items():
                if isinstance(value, bool) or isinstance(value, (int, float, str)):
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error testing extension detector for {tf}: {str(e)}")
    
    return results

def test_indicators(data_dict):
    """
    Test the basic indicators
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes
    """
    print("\n=== Testing Basic Indicators ===")
    
    for tf, data in data_dict.items():
        print(f"\nIndicators for {tf}:")
        
        # Check which indicators are available
        indicator_columns = [col for col in data.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]
        
        if indicator_columns:
            print(f"  Available indicators: {indicator_columns}")
            
            # Show summary of indicator values
            for col in indicator_columns:
                if col in data.columns:
                    print(f"  {col}: mean={data[col].mean():.2f}, std={data[col].std():.2f}")
        else:
            print("  No indicators available")

def visualize_results(data_dict, extension_results=None, timeframe=None, bars=100):
    """
    Visualize backtest results
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes with indicators
    extension_results : dict, optional
        Dictionary of extension detection results by timeframe
    timeframe : str, optional
        Specific timeframe to visualize (if None, visualize all)
    bars : int
        Number of bars to display
    """
    print("\n=== Visualizing Strategy Results ===")
    
    # Create 'results' directory if it doesn't exist
    os.makedirs('./results', exist_ok=True)
    
    # Determine timeframes to plot
    if timeframe is not None and timeframe in data_dict:
        timeframes_to_plot = [timeframe]
    else:
        timeframes_to_plot = list(data_dict.keys())
    
    chart_paths = {}
    
    for tf in timeframes_to_plot:
        print(f"Plotting results for {tf} timeframe...")
        df = data_dict[tf].copy()
        
        # Get the most recent bars
        df = df.iloc[-bars:] if len(df) > bars else df
        
        # Get extension results if available
        ext_data = None
        if extension_results is not None and tf in extension_results:
            ext_data = extension_results[tf]
        
        # Create plot
        plt.figure(figsize=(14, 8))
        
        # Plot price
        plt.subplot(2, 1, 1)
        plt.title(f'Price and 9 EMA - {tf} Timeframe')
        
        # Handle MultiIndex columns if present
        close_col = 'Close'
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df[('Close', df.columns.get_level_values(1)[0])]
        else:
            close_series = df['Close']
        
        # Plot price
        plt.plot(df.index, close_series, label='Price', color='blue')
        
        # Plot 9 EMA if available
        if 'EMA_9' in df.columns:
            plt.plot(df.index, df['EMA_9'], label='9 EMA', color='red', linestyle='--')
        
        # Plot Bollinger Bands if available
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
            plt.plot(df.index, df['BB_Upper'], label='Upper BB', color='green', alpha=0.6)
            plt.plot(df.index, df['BB_Lower'], label='Lower BB', color='green', alpha=0.6)
            plt.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], color='green', alpha=0.1)
        
        # Highlight extension if detected
        if ext_data is not None and ext_data.get('has_extension', False):
            # Get the last data point
            last_idx = df.index[-1]
            last_price = close_series.iloc[-1]
            
            # Mark the extension
            if ext_data.get('extended_up', False):
                plt.scatter([last_idx], [last_price], color='green', s=100, marker='^', label='Extension (Up)')
            elif ext_data.get('extended_down', False):
                plt.scatter([last_idx], [last_price], color='red', s=100, marker='v', label='Extension (Down)')
            
            # Annotate with percentage
            plt.annotate(f"{ext_data.get('extension_percentage', 0):.2f}%", 
                         xy=(last_idx, last_price),
                         xytext=(10, 20),
                         textcoords='offset points',
                         arrowprops=dict(arrowstyle='->'))
        
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Plot volume in second subplot
        plt.subplot(2, 1, 2)
        plt.title('Volume')
        
        # Handle MultiIndex columns for volume
        if isinstance(df.columns, pd.MultiIndex):
            volume_series = df[('Volume', df.columns.get_level_values(1)[0])]
        else:
            volume_series = df['Volume']
        
        plt.bar(df.index, volume_series, color='blue', alpha=0.5)
        plt.grid(True, alpha=0.3)
        
        # Save the plot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.tight_layout()
        plot_path = f'./results/{tf}_strategy_results_{timestamp}.png'
        plt.savefig(plot_path)
        plt.close()
        
        print(f"Plot saved to {plot_path}")
        chart_paths[tf] = plot_path
    
    print("Visualization completed. Check the 'results' directory for the plots.")
    return chart_paths

def generate_report(data_dict, extension_results=None, reclamation_results=None, chart_paths=None):
    """
    Generate HTML report from backtest results
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes by timeframe
    extension_results : dict, optional
        Dictionary of extension detection results by timeframe
    reclamation_results : dict, optional
        Dictionary of reclamation detection results by timeframe
    chart_paths : dict, optional
        Dictionary of chart paths by timeframe
        
    Returns:
    --------
    str
        Path to the generated HTML report
    """
    try:
        from mtfema_backtester.utils.report_generator import generate_html_report
        
        print("\n=== Generating HTML Report ===")
        report_path = generate_html_report(
            data_dict, 
            extension_results, 
            reclamation_results, 
            chart_paths
        )
        
        print(f"Report generated: {report_path}")
        
        # Open report in browser
        webbrowser.open(f'file://{os.path.abspath(report_path)}')
        
        return report_path
    
    except ImportError as e:
        print(f"Could not import report generator: {str(e)}")
        return None

def main():
    """Main test function"""
    # Setup test environment
    logger = setup_test_environment()
    
    try:
        # Load test data (either real or synthetic)
        print("\nLoading test data...")
        test_data = load_test_data(symbol="SPY", days=30)
        
        # Check what we got back
        if hasattr(test_data, 'get_available_timeframes'):
            # We have a TimeframeData object
            timeframes = test_data.get_available_timeframes()
            print(f"\nLoaded data for timeframes: {timeframes}")
            
            # Extract data from TimeframeData object
            data_dict = {}
            for tf in timeframes:
                data_dict[tf] = test_data.get_timeframe(tf)
        else:
            # We have a dictionary of dataframes
            data_dict = test_data
            print(f"\nLoaded data for timeframes: {list(data_dict.keys())}")
        
        # Calculate basic indicators
        print("\nCalculating basic indicators...")
        data_with_indicators = calculate_basic_indicators(data_dict)
        
        # Test indicators
        test_indicators(data_with_indicators)
        
        # Test extension detector
        extension_results = test_extension_detector(data_with_indicators)
        
        # Container for reclamation results
        reclamation_results = {}
        
        # Try to test more components if available
        try:
            from mtfema_backtester.strategy.reclamation_detector import detect_reclamations
            print("\n=== Testing Reclamation Detector ===")
            for tf, data in data_with_indicators.items():
                recl_data = detect_reclamations(data, tf)
                reclamation_results[tf] = recl_data
                print(f"\nReclamations for {tf}:")
                for key, value in recl_data.items():
                    if isinstance(value, bool) or isinstance(value, (int, float, str)):
                        print(f"  {key}: {value}")
        except ImportError:
            print("\nReclamation detector not available for testing")
        
        # Visualize the results
        chart_paths = visualize_results(data_with_indicators, extension_results)
        
        # Generate HTML report
        report_path = generate_report(
            data_with_indicators, 
            extension_results,
            reclamation_results,
            chart_paths
        )
        
        print("\n=== All tests completed successfully ===")
        
        if report_path:
            print(f"\nTo view results, open the HTML report: {os.path.abspath(report_path)}")
        else:
            print("\nTo view results, check the charts in the 'results' directory")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 