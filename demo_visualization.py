"""
MT 9 EMA Backtester - Visualization Demo

This script demonstrates the enhanced visualization capabilities
of the MT 9 EMA Extension Strategy Backtester.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import logging
import random
import time
import webbrowser
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backtester components
from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.strategy.signal_generator import SignalGenerator
from mtfema_backtester.strategy.extension_detector import ExtensionDetector
from mtfema_backtester.backtest.backtest_engine import BacktestEngine
from mtfema_backtester.backtest.performance_metrics import calculate_performance_metrics
from mtfema_backtester.visualization.dashboard_components import (
    create_equity_curve_component,
    create_trade_distribution_component,
    create_metrics_summary_component
)
from mtfema_backtester.visualization.enhanced_dashboard import create_enhanced_dashboard
from mtfema_backtester.visualization.plot_indicators import plot_ema_extension

# Import our new visualization components
from mtfema_backtester.visualization.optimization_visuals import (
    create_optimization_heatmap,
    create_parameter_impact_chart,
    create_parallel_coordinates_plot,
    create_optimization_dashboard
)

# For demo purposes, let's create a mock LiveTrader class
class MockLiveTrader:
    def __init__(self):
        self.running = False
        self.signal_callbacks = []
        self.order_callbacks = []
        self.position_callbacks = []
        self.broker = MockBroker()
    
    def add_signal_callback(self, callback):
        self.signal_callbacks.append(callback)
    
    def add_order_callback(self, callback):
        self.order_callbacks.append(callback)
    
    def add_position_callback(self, callback):
        self.position_callbacks.append(callback)
    
    def start(self):
        self.running = True
        logger.info("Mock LiveTrader started")
    
    def stop(self):
        self.running = False
        logger.info("Mock LiveTrader stopped")

# For demo purposes, let's create a mock Broker class
class MockBroker:
    def __init__(self):
        self.account_balance = 100000.0
    
    def get_account_info(self):
        return {
            'balance': self.account_balance,
            'available': self.account_balance * 0.8,
            'margin': self.account_balance * 0.2,
            'unrealized_pl': random.uniform(-2000, 5000)
        }

def generate_sample_data(symbol='ES', timeframe='1h', periods=1000):
    """Generate sample OHLCV data for demonstration purposes."""
    logger.info(f"Generating sample data for {symbol} on {timeframe} timeframe")
    
    # Generate datetime index
    end_date = datetime.now()
    if timeframe == '1h':
        start_date = end_date - timedelta(hours=periods)
        index = pd.date_range(start=start_date, end=end_date, freq='H')
    elif timeframe == '1d':
        start_date = end_date - timedelta(days=periods)
        index = pd.date_range(start=start_date, end=end_date, freq='D')
    else:
        # Default to 1-hour data
        start_date = end_date - timedelta(hours=periods)
        index = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # Generate a random walk for the close prices
    close = [100]
    for i in range(1, len(index)):
        close.append(close[-1] + random.uniform(-2, 2))
    close = np.array(close)
    
    # Calculate open, high, and low based on close
    open_prices = close - random.uniform(0.5, 1.5)
    high = np.maximum(close, open_prices) + random.uniform(0.5, 2.0)
    low = np.minimum(close, open_prices) - random.uniform(0.5, 2.0)
    
    # Create volume data
    volume = np.random.normal(1000000, 200000, size=len(index))
    volume = np.round(np.abs(volume))
    
    # Create DataFrame
    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=index)
    
    return df

def run_sample_backtest():
    """Run a sample backtest with the MT 9 EMA strategy."""
    logger.info("Running sample backtest")
    
    # Generate sample data for multiple timeframes
    timeframes = ['1h', '4h', '1d']
    data = {}
    for tf in timeframes:
        data[tf] = generate_sample_data(timeframe=tf, periods=1000)
    
    # Create TimeframeData object
    tf_data = TimeframeData()
    for tf, df in data.items():
        tf_data.set_data(tf, df.copy())
    
    # Create strategy components
    extension_detector = ExtensionDetector(
        ema_period=9,
        extension_threshold=1.5,
        reclamation_threshold=0.5
    )
    
    signal_generator = SignalGenerator(
        extension_detector=extension_detector,
        timeframes=timeframes,
        target_symbol='ES'
    )
    
    # Generate signals
    signals = signal_generator.generate_signals(tf_data)
    
    # Run backtest
    backtest_params = {
        'initial_capital': 100000,
        'position_size': 1,
        'risk_percent': 1.0,
        'slippage': 0.01,
        'commission': 2.0,
    }
    
    engine = BacktestEngine(params=backtest_params)
    trades, equity_curve = engine.run_backtest(signals, tf_data)
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(trades, equity_curve)
    
    return trades, equity_curve, metrics, tf_data

def generate_sample_optimization_results(n_params=3, n_results=100):
    """Generate sample optimization results for demonstration purposes."""
    logger.info("Generating sample optimization results")
    
    # Define parameters for optimization
    params = [
        'ema_period',
        'extension_threshold',
        'reclamation_threshold',
        'risk_percent',
        'target_multiple'
    ]
    
    # Select a subset of parameters if requested
    selected_params = params[:n_params]
    
    # Create random parameter combinations
    results = []
    for i in range(n_results):
        result = {
            'ema_period': np.random.choice([8, 9, 10, 11, 12]),
            'extension_threshold': round(random.uniform(1.0, 2.0), 1),
            'reclamation_threshold': round(random.uniform(0.3, 0.7), 1),
            'risk_percent': round(random.uniform(0.5, 2.0), 1),
            'target_multiple': round(random.uniform(1.5, 3.0), 1)
        }
        
        # Calculate performance metrics based on parameters
        # Here we simulate some correlation between params and metrics
        base_return = random.uniform(10, 40)
        param_effect = (
            (result['ema_period'] - 9) * -5 +
            (result['extension_threshold'] - 1.5) * -10 +
            (result['reclamation_threshold'] - 0.5) * 15 +
            (result['risk_percent'] - 1.0) * 8 +
            (result['target_multiple'] - 2.0) * 12
        )
        
        # Add some random noise
        noise = random.uniform(-10, 10)
        
        # Calculate metrics
        total_return = base_return + param_effect + noise
        win_rate = min(80, max(30, 50 + total_return/10 + random.uniform(-5, 5)))
        profit_factor = 1.0 + total_return/50
        max_drawdown = min(50, max(5, 30 - total_return/5 + random.uniform(-5, 5)))
        sharpe_ratio = total_return / (max_drawdown/2)
        sortino_ratio = sharpe_ratio * random.uniform(1.1, 1.5)
        calmar_ratio = total_return / max_drawdown
        avg_trade = total_return / random.randint(20, 40)
        
        # Add metrics to results
        result.update({
            'total_return': round(total_return, 2),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'avg_trade': round(avg_trade, 2)
        })
        
        results.append(result)
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    return df

def demo_live_trading_dashboard():
    """Set up and demo the live trading dashboard with simulated data."""
    try:
        # Import the dashboard only now to avoid early import errors
        from mtfema_backtester.visualization.live_trading_dashboard import (
            LiveTradingDashboard, create_live_trading_dashboard
        )
        
        logger.info("Setting up live trading dashboard")
        
        # Create mock live trader
        live_trader = MockLiveTrader()
        
        # Create dashboard
        dashboard = LiveTradingDashboard(live_trader, port=8051)
        
        # Start the dashboard
        dashboard.start(open_browser=True)
        
        # Simulate some activity for demonstration
        logger.info("Generating simulated trading activity...")
        time.sleep(2)  # Wait for dashboard to start
        
        # Start the mock trader
        live_trader.start()
        
        # Generate some sample signals
        for i in range(10):
            for callback in live_trader.signal_callbacks:
                signal = {
                    'datetime': datetime.now() - timedelta(minutes=i*10),
                    'symbol': 'ES',
                    'direction': 'long' if random.random() > 0.5 else 'short',
                    'timeframe': random.choice(['5m', '15m', '1h', '4h']),
                    'confidence': random.uniform(0.6, 0.95)
                }
                callback(signal)
            time.sleep(0.5)
        
        # Generate some sample positions
        for i in range(3):
            for callback in live_trader.position_callbacks:
                position = {
                    'id': f"pos_{i}",
                    'symbol': 'ES',
                    'direction': 'long' if random.random() > 0.5 else 'short',
                    'timestamp': datetime.now(),
                    'quantity': random.randint(1, 5),
                    'entry_price': random.uniform(4000, 4100),
                    'current_price': random.uniform(4000, 4100),
                    'unrealized_pl': random.uniform(-500, 1000),
                    'status': 'open',
                    'timeframe': random.choice(['15m', '1h', '4h'])
                }
                callback(position)
            time.sleep(1)
        
        # Let the dashboard run for a bit
        logger.info("Live trading dashboard running at http://localhost:8051")
        logger.info("Press Ctrl+C to stop the demo")
        
        # Return dashboard to allow stopping in the main function
        return dashboard, live_trader
        
    except Exception as e:
        logger.error(f"Error setting up live trading dashboard: {str(e)}")
        return None, None

def run_demo():
    """Run a comprehensive demo of the MT 9 EMA Backtester visualizations."""
    logger.info("Starting MT 9 EMA Backtester Visualization Demo")
    
    # Part 1: Backtest Visualization
    logger.info("\n\n=== Part 1: Backtest Results Visualization ===")
    
    # Run a sample backtest
    trades, equity_curve, metrics, tf_data = run_sample_backtest()
    
    # Save trades to CSV for reference
    trades_df = pd.DataFrame([t.__dict__ for t in trades])
    trades_df.to_csv('demo_trades.csv', index=False)
    logger.info(f"Sample backtest complete. Generated {len(trades)} trades.")
    
    # Create enhanced dashboard
    dashboard_path = 'demo_dashboard.html'
    create_enhanced_dashboard(trades_df, equity_curve, metrics, dashboard_path)
    logger.info(f"Enhanced dashboard saved to {dashboard_path}")
    
    # Open the dashboard in browser
    webbrowser.open(f'file://{os.path.abspath(dashboard_path)}')
    logger.info("Opening enhanced dashboard in browser...")
    time.sleep(3)  # Wait for browser to load
    
    # Part 2: Optimization Visualization
    logger.info("\n\n=== Part 2: Parameter Optimization Visualization ===")
    
    # Generate sample optimization results
    opt_results = generate_sample_optimization_results(n_params=5, n_results=100)
    
    # Save optimization results to CSV for reference
    opt_results.to_csv('demo_optimization.csv', index=False)
    logger.info(f"Generated {len(opt_results)} sample optimization results.")
    
    # Create optimization dashboard
    opt_dashboard_path = 'demo_optimization_dashboard.html'
    create_optimization_dashboard(opt_results, opt_dashboard_path)
    logger.info(f"Optimization dashboard saved to {opt_dashboard_path}")
    
    # Open the dashboard in browser
    webbrowser.open(f'file://{os.path.abspath(opt_dashboard_path)}')
    logger.info("Opening optimization dashboard in browser...")
    time.sleep(3)  # Wait for browser to load
    
    # Part 3: Live Trading Dashboard
    logger.info("\n\n=== Part 3: Live Trading Dashboard ===")
    logger.info("Setting up simulated live trading dashboard...")
    
    # Run the live trading dashboard demo
    dashboard, live_trader = demo_live_trading_dashboard()
    
    # Keep the script running to allow interaction with the dashboard
    if dashboard:
        try:
            logger.info("\n\nDemo is running. Press Ctrl+C to exit.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Demo terminated by user.")
            if live_trader:
                live_trader.stop()
    
    logger.info("\n\nMT 9 EMA Backtester Visualization Demo complete.")

if __name__ == "__main__":
    run_demo()
