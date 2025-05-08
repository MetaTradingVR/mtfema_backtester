"""
Test script for live trading dashboard.

This script tests the live trading dashboard component in isolation
with simulated trading data.
"""

import os
import sys
import pandas as pd
import numpy as np
import random
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path to make imports work
sys.path.append(str(Path(__file__).parent.parent))

# Class to mock LiveTrader for testing
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
        print("Mock LiveTrader started")
    
    def stop(self):
        self.running = False
        print("Mock LiveTrader stopped")

# Class to mock Broker for testing
class MockBroker:
    def __init__(self):
        self.account_balance = 100000.0
        self.last_update = datetime.now()
    
    def get_account_info(self):
        # Simulate some random balance changes
        time_diff = (datetime.now() - self.last_update).total_seconds()
        if time_diff > 5:
            self.account_balance += random.uniform(-500, 700)
            self.last_update = datetime.now()
        
        return {
            'balance': self.account_balance,
            'available': self.account_balance * 0.8,
            'margin': self.account_balance * 0.2,
            'unrealized_pl': random.uniform(-2000, 5000)
        }

def test_live_trading_dashboard():
    """Test the live trading dashboard with simulated data."""
    try:
        # Import the dashboard
        from mtfema_backtester.visualization.live_trading_dashboard import LiveTradingDashboard
        
        print("\n=== Testing Live Trading Dashboard ===")
        
        # Create mock live trader
        live_trader = MockLiveTrader()
        
        # Create dashboard
        dashboard = LiveTradingDashboard(live_trader, port=8052)
        
        # Start the dashboard
        dashboard.start(open_browser=True)
        
        print("Live trading dashboard started at http://localhost:8052")
        
        # Start the mock trader
        live_trader.start()
        
        # Function to generate simulated data
        def generate_simulated_data():
            print("Generating simulated trading data...")
            
            # Generate sample signals
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
            
            # Generate sample positions
            for i in range(3):
                position_id = f"pos_{i}"
                
                # Open position
                open_position = {
                    'id': position_id,
                    'symbol': 'ES',
                    'direction': 'long' if random.random() > 0.5 else 'short',
                    'timestamp': datetime.now() - timedelta(minutes=30),
                    'quantity': random.randint(1, 5),
                    'entry_price': random.uniform(4000, 4100),
                    'current_price': random.uniform(4000, 4100),
                    'unrealized_pl': random.uniform(-500, 1000),
                    'status': 'open',
                    'timeframe': random.choice(['15m', '1h', '4h'])
                }
                
                for callback in live_trader.position_callbacks:
                    callback(open_position)
                
                # Wait a bit before closing some positions
                if i < 2:  # Leave one position open
                    time.sleep(10)
                    
                    # Close position
                    close_position = {
                        'id': position_id,
                        'symbol': 'ES',
                        'direction': open_position['direction'],
                        'timestamp': datetime.now(),
                        'quantity': open_position['quantity'],
                        'entry_price': open_position['entry_price'],
                        'exit_price': open_position['entry_price'] + random.uniform(-20, 40),
                        'realized_pl': random.uniform(-500, 1000),
                        'status': 'closed',
                        'timeframe': open_position['timeframe']
                    }
                    
                    for callback in live_trader.position_callbacks:
                        callback(close_position)
            
            # Generate ongoing data periodically
            while live_trader.running:
                # Update signals occasionally
                if random.random() > 0.7:
                    for callback in live_trader.signal_callbacks:
                        signal = {
                            'datetime': datetime.now(),
                            'symbol': 'ES',
                            'direction': 'long' if random.random() > 0.5 else 'short',
                            'timeframe': random.choice(['5m', '15m', '1h', '4h']),
                            'confidence': random.uniform(0.6, 0.95)
                        }
                        callback(signal)
                
                # Update position P&L
                for callback in live_trader.position_callbacks:
                    # Get the open position (should be the last one)
                    position = {
                        'id': 'pos_2',  # The one we left open
                        'symbol': 'ES',
                        'timestamp': datetime.now(),
                        'unrealized_pl': random.uniform(-1000, 2000),
                        'status': 'open'
                    }
                    callback(position)
                
                # Wait before next update
                time.sleep(5)
        
        # Start data generation in a separate thread
        data_thread = threading.Thread(target=generate_simulated_data)
        data_thread.daemon = True
        data_thread.start()
        
        print("Simulated data generation started")
        print("Dashboard will update in real-time with simulated data")
        print("\nPress Ctrl+C to stop the test when finished")
        
        try:
            # Keep the test running to allow interaction with the dashboard
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nTest terminated by user")
            live_trader.stop()
        
    except ImportError as e:
        print(f"Error importing dashboard components: {str(e)}")
        print("Make sure the live_trading_dashboard.py file is properly installed")
    except Exception as e:
        print(f"Error testing live trading dashboard: {str(e)}")

if __name__ == "__main__":
    test_live_trading_dashboard()
