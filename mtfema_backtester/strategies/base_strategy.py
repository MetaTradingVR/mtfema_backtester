"""
Base strategy class for the MT 9 EMA Backtester
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""
    
    def __init__(self):
        """Initialize base strategy."""
        self.name = self.__class__.__name__
    
    @property
    def name(self) -> str:
        """Get strategy name."""
        return self._name
    
    @name.setter
    def name(self, value: str):
        """Set strategy name."""
        self._name = value
    
    @property
    def version(self) -> str:
        """Get strategy version."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get strategy description."""
        return "Base strategy class"
    
    @property
    def required_timeframes(self) -> List[str]:
        """Get required timeframes."""
        return ["1h"]
    
    def initialize(self, symbols: List[str], start_date: str, end_date: str):
        """
        Initialize the strategy for backtesting.
        
        Args:
            symbols: List of symbols to trade
            start_date: Start date for backtesting
            end_date: End date for backtesting
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
    
    def calculate_indicators(self, data: Dict[str, Dict[str, pd.DataFrame]]):
        """
        Calculate required indicators for all symbols and timeframes.
        
        Args:
            data: Dictionary of DataFrames for different symbols and timeframes
                {symbol: {timeframe: DataFrame}}
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: Dict[str, Dict[str, pd.DataFrame]], current_date: datetime) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on the strategy logic.
        
        Args:
            data: Dictionary of DataFrames for different symbols and timeframes
            current_date: Current date in the backtest
            
        Returns:
            List of signal dictionaries with trade details
        """
        pass
    
    def update_trades(self, data: Dict[str, Dict[str, pd.DataFrame]], current_date: datetime) -> List[Dict[str, Any]]:
        """
        Update active trades based on current market data.
        
        Args:
            data: Dictionary of DataFrames for different symbols and timeframes
            current_date: Current date in the backtest
            
        Returns:
            List of closed trade dictionaries
        """
        return []
    
    def on_new_signal(self, signal: Dict[str, Any]):
        """
        Process a new trading signal.
        
        Args:
            signal: Signal dictionary with trade details
        """
        pass
    
    def on_trade_closed(self, trade: Dict[str, Any]):
        """
        Process a closed trade.
        
        Args:
            trade: Closed trade dictionary
        """
        pass
    
    def get_position_size(self, signal: Dict[str, Any], account_balance: float, risk_percent: float = 1.0) -> float:
        """
        Calculate position size based on risk management.
        
        Args:
            signal: Signal dictionary with trade details
            account_balance: Current account balance
            risk_percent: Percentage of account balance to risk per trade
            
        Returns:
            Position size in units
        """
        return 1.0  # Default implementation returns a fixed size
    
    def generate_entry_orders(self, signal: Dict[str, Any], account_balance: float) -> Dict[str, Any]:
        """
        Generate order details for a signal.
        
        Args:
            signal: Signal dictionary with trade details
            account_balance: Current account balance
            
        Returns:
            Order details dictionary
        """
        # Create basic order details
        order = {
            'symbol': signal['symbol'],
            'direction': signal['direction'],
            'order_type': 'market',
            'quantity': self.get_position_size(signal, account_balance),
            'price': signal.get('entry_price')
        }
        
        return order
