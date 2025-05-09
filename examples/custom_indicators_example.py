"""
Custom Indicators Example for MT9 EMA Backtester

This example demonstrates:
1. How to use existing indicators (ZigZag, Fibonacci)
2. How to create a custom indicator
3. How to implement a strategy using these indicators
4. How to visualize indicator data and trading signals
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys

# Add project root to Python path to ensure imports work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import from MT9 EMA Backtester framework
from mtfema_backtester.utils.indicators import Indicator, create_indicator, get_indicator_registry
from mtfema_backtester.utils.indicators import ZigZag, FibRetracement  # Our newly added indicators

# Step 1: Create a Custom Indicator
class PriceChannelIndicator(Indicator):
    """
    Price Channel indicator that tracks highest highs and lowest lows over a period.
    """
    
    def __init__(self, period: int = 20, name: str = None):
        """
        Initialize the Price Channel indicator.
        
        Args:
            period: Lookback period for highest high and lowest low
            name: Optional custom name for this indicator
        """
        params = {'period': period}
        super().__init__(name or "PriceChannel", params)
        self.required_columns = ['high', 'low']
    
    def _validate_params(self) -> None:
        """
        Validate Price Channel parameters.
        """
        if self.params['period'] <= 0:
            raise ValueError(f"Period must be positive, got {self.params['period']}")
    
    def _calculate(self, data: pd.DataFrame) -> dict:
        """
        Calculate the Price Channel indicator.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with 'upper', 'lower', and 'middle' keys
        """
        period = self.params['period']
        
        # Calculate upper and lower bands
        upper = data['high'].rolling(window=period).max()
        lower = data['low'].rolling(window=period).min()
        
        # Calculate middle line (average of upper and lower)
        middle = (upper + lower) / 2
        
        # Calculate width of the channel as a percentage
        width = (upper - lower) / middle * 100
        
        return {
            'upper': upper,
            'lower': lower,
            'middle': middle,
            'width': width
        }


# Step 2: Register the Custom Indicator
def register_custom_indicators():
    """Register our custom indicator with the indicator registry."""
    registry = get_indicator_registry()
    registry.register("PriceChannel", PriceChannelIndicator)
    
    # Verify all available indicators
    available_indicators = registry.list_indicators()
    print(f"Available indicators: {available_indicators}")


# Step 3: Create a Strategy using Custom and Built-in Indicators
def create_strategy_example(data: pd.DataFrame):
    """
    Create example indicators and demonstrate their usage.
    
    Args:
        data: DataFrame with OHLCV price data
    
    Returns:
        Dict containing indicator results and signals
    """
    # Make sure our custom indicator is registered
    register_custom_indicators()
    
    # Create instances of indicators
    price_channel = create_indicator("PriceChannel", period=20)
    zigzag = create_indicator("ZigZag", deviation=5.0, depth=10)
    fib = create_indicator("FibRetracement", 
                           levels=[0.0, 0.382, 0.5, 0.618, 0.786, 1.0],
                           extension_levels=[1.272, 1.618, 2.618],
                           use_zigzag=True,
                           zigzag_deviation=5.0,
                           zigzag_depth=10)
    
    # Calculate indicators
    pc_results = price_channel.calculate(data)
    zz_results = zigzag.calculate(data)
    fib_results = fib.calculate(data)
    
    # Generate trading signals (simple example)
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0  # Initialize with no signal
    
    # Example signal logic: Buy when price crosses above the lower price channel
    # and is above a Fibonacci level, sell when it crosses below the upper channel
    for i in range(1, len(data)):
        # Check for buy signals
        if (data['close'].iloc[i-1] < pc_results['lower'].iloc[i-1] and 
            data['close'].iloc[i] > pc_results['lower'].iloc[i] and
            data['close'].iloc[i] > fib_results.get(f'level_0.618', pd.Series(0, index=data.index)).iloc[i]):
            signals['signal'].iloc[i] = 1
        
        # Check for sell signals
        elif (data['close'].iloc[i-1] > pc_results['upper'].iloc[i-1] and 
              data['close'].iloc[i] < pc_results['upper'].iloc[i]):
            signals['signal'].iloc[i] = -1
    
    return {
        'price_channel': pc_results,
        'zigzag': zz_results,
        'fib': fib_results,
        'signals': signals
    }


# Step 4: Visualize the indicators and signals
def visualize_strategy(data: pd.DataFrame, results: dict):
    """
    Create visualization of price data with indicators and signals.
    
    Args:
        data: DataFrame with price data
        results: Dict with indicator results and signals
    """
    print("Creating visualization...")
    
    # Create figure for visualization
    plt.figure(figsize=(15, 10))
    
    # Price chart with indicators
    ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2)
    ax1.set_title('Custom Indicators Strategy Example')
    ax1.set_ylabel('Price')
    
    # Plot price candlesticks (simplified)
    ax1.plot(data.index, data['close'], label='Close Price', color='black', alpha=0.7)
    
    # Plot Price Channel
    if 'price_channel' in results:
        ax1.plot(data.index, results['price_channel']['upper'], label='Upper Channel', color='red', linestyle='--')
        ax1.plot(data.index, results['price_channel']['lower'], label='Lower Channel', color='green', linestyle='--')
        ax1.plot(data.index, results['price_channel']['middle'], label='Middle Channel', color='blue', linestyle='--')
    
    # Plot ZigZag
    if 'zigzag' in results:
        ax1.plot(data.index, results['zigzag']['line'], label='ZigZag', color='purple', linewidth=1.5)
    
    # Plot Fibonacci levels
    if 'fib' in results:
        # Plotting only the 0.618 level for clarity
        fib_level = 0.618
        level_key = f'level_{fib_level:.3f}'
        if level_key in results['fib']:
            ax1.plot(data.index, results['fib'][level_key], 
                     label=f'Fib {fib_level}', color='orange', linestyle='-.')
    
    # Plot buy/sell signals
    if 'signals' in results:
        signals = results['signals']
        
        # Buy signals (1)
        buy_signals = signals[signals['signal'] == 1]
        if not buy_signals.empty:
            ax1.scatter(buy_signals.index, data.loc[buy_signals.index, 'close'], 
                       marker='^', color='green', s=100, label='Buy Signal')
        
        # Sell signals (-1)
        sell_signals = signals[signals['signal'] == -1]
        if not sell_signals.empty:
            ax1.scatter(sell_signals.index, data.loc[sell_signals.index, 'close'], 
                       marker='v', color='red', s=100, label='Sell Signal')
    
    ax1.grid(True)
    ax1.legend(loc='upper left')
    
    # Plot Price Channel Width in bottom panel
    if 'price_channel' in results:
        ax2 = plt.subplot2grid((3, 1), (2, 0), sharex=ax1)
        ax2.plot(data.index, results['price_channel']['width'], label='Channel Width %', color='blue')
        ax2.axhline(y=10, color='red', linestyle='--', alpha=0.3)  # Example threshold
        ax2.set_ylabel('Width %')
        ax2.grid(True)
        ax2.legend(loc='upper left')
    
    plt.tight_layout()
    plt.show()


# Step 5: Generate sample data for demonstration
def generate_sample_data(days: int = 100):
    """
    Generate sample OHLCV data for demonstration purposes.
    
    Args:
        days: Number of days of data to generate
        
    Returns:
        DataFrame with OHLCV data
    """
    print("Generating sample data...")
    
    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate synthetic price data
    n = len(dates)
    base_price = 100
    trend = np.linspace(0, 20, n)  # Upward trend
    noise = np.random.normal(0, 1, n)  # Random noise
    cycle = 10 * np.sin(np.linspace(0, 8*np.pi, n))  # Cyclic component
    
    # Generate OHLC data
    close = base_price + trend + noise + cycle
    high = close + np.random.uniform(0.1, 2, n)
    low = close - np.random.uniform(0.1, 2, n)
    open_price = close.shift(1).fillna(close[0])
    
    # Create DataFrame
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100, 1000, n)
    }, index=dates)
    
    return data


# Main example execution
def run_example():
    """Run the full example."""
    print("\n=== MT9 EMA Backtester: Custom Indicators Example ===\n")
    
    # Step 1: Check if we can load real data
    try:
        print("Attempting to load real data...")
        # This will vary based on your project structure
        try:
            from mtfema_backtester.data.data_provider import get_sample_data
            data = get_sample_data('NQ', '1D', start_date='2023-01-01', end_date='2023-04-01')
            print("Successfully loaded real data.")
        except:
            # Fallback to other data sources
            print("Sample data not available, trying alternate sources...")
            raise Exception("Need to use generated data")
    except Exception as e:
        print(f"Could not load real data: {str(e)}")
        print("Using generated sample data instead.")
        data = generate_sample_data(days=100)
    
    # Step 2: Create and register custom indicators
    print("\nStep 2: Registering custom indicators...")
    register_custom_indicators()
    
    # Step 3: Create strategy and calculate indicators
    print("\nStep 3: Calculating indicators and generating signals...")
    results = create_strategy_example(data)
    
    # Step 4: Visualize the strategy
    print("\nStep 4: Visualizing the strategy...")
    visualize_strategy(data, results)
    
    print("\nExample completed. You can modify this code to create your own indicators and strategies.")


# Run the example if this script is executed directly
if __name__ == "__main__":
    run_example()
