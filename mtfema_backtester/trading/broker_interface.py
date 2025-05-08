"""
Broker interface for the MT 9 EMA Extension Strategy.

This module defines the base interface for broker connections and order management.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
import pandas as pd

logger = logging.getLogger(__name__)

class OrderStatus:
    """Order status constants"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderType:
    """Order type constants"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    
class OrderSide:
    """Order side constants"""
    BUY = "buy"
    SELL = "sell"
    
class TimeInForce:
    """Time in force constants"""
    GTC = "gtc"  # Good till canceled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill
    DAY = "day"  # Day order

class BrokerInterface(ABC):
    """
    Abstract base class defining the broker interface.
    
    All broker implementations must implement these methods.
    """
    
    def __init__(self, credentials: Dict[str, Any], is_paper: bool = True):
        """
        Initialize the broker interface.
        
        Args:
            credentials: Dictionary with broker credentials
            is_paper: Whether to use paper trading
        """
        self.credentials = credentials
        self.is_paper = is_paper
        self.connected = False
        self.account_id = None
        self.orders = {}
        self.positions = {}
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker API.
        
        Returns:
            bool: True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker API.
        
        Returns:
            bool: True if disconnection successful
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dict: Account information
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List[Dict]: Current positions
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get orders with optional status filter.
        
        Args:
            status: Optional status filter
            
        Returns:
            List[Dict]: List of orders
        """
        pass
    
    @abstractmethod
    def place_order(self, 
                    symbol: str, 
                    quantity: float, 
                    side: str, 
                    order_type: str = OrderType.MARKET,
                    limit_price: Optional[float] = None,
                    stop_price: Optional[float] = None,
                    time_in_force: str = TimeInForce.GTC,
                    **kwargs) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol: Instrument symbol
            quantity: Order quantity
            side: Order side (buy/sell)
            order_type: Order type
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            time_in_force: Time in force
            **kwargs: Additional broker-specific parameters
            
        Returns:
            Dict: Order information
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            bool: True if cancellation successful
        """
        pass
    
    @abstractmethod
    def modify_order(self, 
                     order_id: str, 
                     quantity: Optional[float] = None,
                     limit_price: Optional[float] = None,
                     stop_price: Optional[float] = None,
                     **kwargs) -> Dict[str, Any]:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            quantity: New quantity
            limit_price: New limit price
            stop_price: New stop price
            **kwargs: Additional broker-specific parameters
            
        Returns:
            Dict: Updated order information
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get status of a specific order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Dict: Order status information
        """
        pass
    
    @abstractmethod
    def get_market_data(self, 
                       symbol: str, 
                       data_type: str = "quote",
                       **kwargs) -> Dict[str, Any]:
        """
        Get current market data for a symbol.
        
        Args:
            symbol: Instrument symbol
            data_type: Type of data (quote, trade, etc.)
            **kwargs: Additional parameters
            
        Returns:
            Dict: Market data
        """
        pass
    
    @abstractmethod
    def get_historical_data(self,
                          symbol: str,
                          timeframe: str,
                          start_time: datetime,
                          end_time: datetime,
                          **kwargs) -> Optional[pd.DataFrame]:
        """
        Get market data for a symbol.
        
        Args:
            symbol: Instrument symbol
            data_type: Type of data (quote, trade, etc.)
            **kwargs: Additional parameters
            
        Returns:
            Dict: Market data
        """
        pass
    
    @abstractmethod
    def get_historical_data(self,
                           symbol: str,
                           timeframe: str,
                           start_time: datetime,
                           end_time: Optional[datetime] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Instrument symbol
            timeframe: Timeframe (e.g. "1m", "1h")
            start_time: Start time
            end_time: End time (defaults to now)
            **kwargs: Additional parameters
            
        Returns:
            Dict: Historical data
        """
        pass
    
    def generate_order_id(self) -> str:
        """
        Generate a unique order ID.
        
        Returns:
            str: Unique order ID
        """
        return str(uuid.uuid4())
    
    def _validate_connection(self) -> bool:
        """
        Check if connected to broker API.
        
        Returns:
            bool: True if connected
        """
        if not self.connected:
            logger.error("Not connected to broker API")
            return False
        return True
    
    def _log_order(self, order_info: Dict[str, Any]) -> None:
        """
        Log order information.
        
        Args:
            order_info: Order information to log
        """
        order_id = order_info.get("order_id", "unknown")
        symbol = order_info.get("symbol", "unknown")
        side = order_info.get("side", "unknown")
        quantity = order_info.get("quantity", 0)
        order_type = order_info.get("order_type", "unknown")
        status = order_info.get("status", "unknown")
        
        logger.info(f"Order {order_id}: {side} {quantity} {symbol} ({order_type}) - {status}")
        
        # Cache order
        self.orders[order_id] = order_info

class BrokerFactory:
    """
    Factory for creating broker instances.
    """
    
    _broker_registry = {}
    
    @classmethod
    def register(cls, broker_name: str, broker_class):
        """
        Register a broker implementation.
        
        Args:
            broker_name: Name of the broker
            broker_class: Broker class
        """
        cls._broker_registry[broker_name.lower()] = broker_class
        
    @classmethod
    def create(cls, 
               broker_name: str, 
               credentials: Dict[str, Any], 
               is_paper: bool = True) -> BrokerInterface:
        """
        Create a broker instance.
        
        Args:
            broker_name: Name of the broker
            credentials: Broker credentials
            is_paper: Whether to use paper trading
            
        Returns:
            BrokerInterface: Broker instance
            
        Raises:
            ValueError: If broker not found
        """
        broker_class = cls._broker_registry.get(broker_name.lower())
        
        if not broker_class:
            available_brokers = ", ".join(cls._broker_registry.keys())
            raise ValueError(f"Broker '{broker_name}' not found. Available brokers: {available_brokers}")
            
        return broker_class(credentials, is_paper)
    
    @classmethod
    def get_available_brokers(cls) -> List[str]:
        """
        Get list of available brokers.
        
        Returns:
            List[str]: Available broker names
        """
        return list(cls._broker_registry.keys())
