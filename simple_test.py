"""
Simple test script for the TradeExecutor class.
"""

import logging
import sys
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import our trade executor module directly
sys.path.append('.')
from mtfema_backtester.trading.trade_executor import TradeExecutor

def run_simple_test():
    """Run a simple test of the TradeExecutor."""
    logger.info("Starting simple TradeExecutor test")
    
    # Initialize TradeExecutor with default parameters
    executor = TradeExecutor(
        strategy=None,
        account_balance=10000.0,
        risk_settings={
            'account_risk_percent': 1.0,
            'max_concurrent_trades': 3,
            'reward_risk_ratio': 2.0
        }
    )
    
    # Create a simple market data dictionary
    timeframe_data = {
        '1h': {
            'datetime': datetime.now(),
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 1000
        },
        '4h': {
            'datetime': datetime.now(),
            'open': 100.0,
            'high': 102.0,
            'low': 98.0,
            'close': 101.0,
            'volume': 5000
        }
    }
    
    # Create a simple signal
    signal = {
        'entry_time': datetime.now(),
        'timeframe': '1h',
        'direction': 'long',
        'entry_price': 100.5,
        'stop_price': 99.0,
        'target_price': 102.5,  # 2:1 reward-risk
        'target_timeframe': '4h',
        'risk_factor': 1.0
    }
    
    # Process the signal
    position = executor.process_signal(signal, timeframe_data)
    
    if position:
        logger.info(f"Created position: {position['id']}")
        logger.info(f"Position size: {position['position_size']}")
        logger.info(f"Risk amount: ${position['risk_amount']:.2f}")
        logger.info(f"Target price: {position['target_price']}")
    else:
        logger.info("No position created")
    
    # Get performance metrics
    metrics = executor.get_performance_metrics()
    logger.info(f"Metrics: {metrics}")
    
    return executor

if __name__ == "__main__":
    run_simple_test()
