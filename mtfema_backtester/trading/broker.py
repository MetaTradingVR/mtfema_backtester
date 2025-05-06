class BaseBroker(ABC):
    """Abstract base class for broker implementations."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the broker name."""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker.
        
        Returns:
            True if connected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the broker is connected."""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dictionary with account details (balance, equity, margin, etc.)
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object or None if no position exists
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """
        Get all orders, optionally filtered by status.
        
        Args:
            status: Optional filter for order status
            
        Returns:
            List of Order objects
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get an order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """
        Place a new order.
        
        Args:
            order: Order to place
            
        Returns:
            Updated order with broker-assigned ID and status
            
        Raises:
            Exception: If order placement fails
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if canceled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, **kwargs) -> Order:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            **kwargs: Parameters to modify (price, quantity, etc.)
            
        Returns:
            Updated order
            
        Raises:
            Exception: If order modification fails
        """
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        """
        Get historical market data.
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe (e.g., "1m", "5m", "1h", "1d")
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with price information (bid, ask, last)
        """
        pass
    
    def subscribe_to_market_data(self, symbol: str, callback: callable):
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data updates
            
        Note:
            Default implementation does nothing. Override in concrete classes.
        """
        pass
    
    def unsubscribe_from_market_data(self, symbol: str):
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbol: Trading symbol
            
        Note:
            Default implementation does nothing. Override in concrete classes.
        """
        pass
"""
Base classes for broker implementations in the MT 9 EMA Backtester
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
import uuid


class OrderType(Enum):
    """Order types supported by brokers."""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


class OrderSide(Enum):
    """Order side (buy/sell)."""
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    """Order status states."""
    PENDING = auto()  # Order submitted but not yet acknowledged
    OPEN = auto()     # Order acknowledged and active
    FILLED = auto()   # Order completely filled
    PARTIALLY_FILLED = auto()  # Order partially filled
    CANCELED = auto()  # Order canceled
    REJECTED = auto()  # Order rejected
    EXPIRED = auto()   # Order expired


class TimeInForce(Enum):
    """Time in force options."""
    DAY = auto()      # Valid for the trading day
    GTC = auto()      # Good till canceled
    IOC = auto()      # Immediate or cancel
    FOK = auto()      # Fill or kill


class Order:
    """Represents a trading order."""
    
    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        client_order_id: Optional[str] = None
    ):
        """
        Initialize an order.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            order_type: Order type (MARKET, LIMIT, STOP, STOP_LIMIT)
            price: Limit price (required for LIMIT and STOP_LIMIT orders)
            stop_price: Stop price (required for STOP and STOP_LIMIT orders)
            time_in_force: Time in force (DAY, GTC, IOC, FOK)
            client_order_id: Optional client-assigned order ID
        """
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        
        # Generate client order ID if not provided
        self.client_order_id = client_order_id or str(uuid.uuid4())
        
        # Order state
        self.id = None  # Broker-assigned ID
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.avg_fill_price = 0.0
        self.commission = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.fills = []  # List of fill details
        
        # Validate order parameters
        self._validate()
    
    def _validate(self):
        """Validate order parameters."""
        if self.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and self.price is None:
            raise ValueError(f"Price is required for {self.order_type} orders")
        
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError(f"Stop price is required for {self.order_type} orders")
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
    
    @property
    def is_active(self) -> bool:
        """Check if the order is active (pending or open)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def is_filled(self) -> bool:
        """Check if the order is filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def remaining_quantity(self) -> float:
        """Get remaining quantity to be filled."""
        return self.quantity - self.filled_quantity
    
    def __str__(self) -> str:
        """String representation of the order."""
        return (
            f"Order(id={self.id}, symbol={self.symbol}, side={self.side}, "
            f"type={self.order_type}, status={self.status}, "
            f"qty={self.quantity}, filled={self.filled_quantity}, "
            f"price={self.price}, stop_price={self.stop_price})"
        )
    
    def __repr__(self) -> str:
        """Detailed representation of the order."""
        return self.__str__()


class Position:
    """Represents a trading position."""
    
    def __init__(
        self,
        symbol: str,
        quantity: float,
        avg_price: float,
        side: OrderSide,
        unrealized_pnl: float = 0.0,
        realized_pnl: float = 0.0
    ):
        """
        Initialize a position.
        
        Args:
            symbol: Trading symbol
            quantity: Position quantity
            avg_price: Average entry price
            side: Position side (BUY/SELL)
            unrealized_pnl: Unrealized profit/loss
            realized_pnl: Realized profit/loss
        """
        self.symbol = symbol
        self.quantity = quantity
        self.avg_price = avg_price
        self.side = side
        self.unrealized_pnl = unrealized_pnl
        self.realized_pnl = realized_pnl
        self.current_price = avg_price
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_price(self, price: float):
        """
        Update position with current price.
        
        Args:
            price: Current market price
        """
        self.current_price = price
        
        # Calculate unrealized P&L
        if self.side == OrderSide.BUY:
            self.unrealized_pnl = (price - self.avg_price) * self.quantity
        else:
            self.unrealized_pnl = (self.avg_price - price) * self.quantity
        
        self.updated_at = datetime.now()
    
    @property
    def pnl_percent(self) -> float:
        """Calculate P&L as a percentage of position value."""
        if self.avg_price == 0 or self.quantity == 0:
            return 0.0
        
        position_value = self.avg_price * self.quantity
        
        if position_value == 0:
            return 0.0
        
        return (self.unrealized_pnl / position_value) * 100
    
    def __str__(self) -> str:
        """String representation of the position."""
        return (
            f"Position(symbol={self.symbol}, side={self.side}, "
            f"qty={self.quantity}, avg_price={self.avg_price:.2f}, "
            f"curr_price={self.current_price:.2f}, "
            f"pnl=${self.unrealized_pnl:.2f} ({self.pnl_percent:.2f}%))"
        )
    
    def __repr__(self) -> str:
        """Detailed representation of the position."""
        return self.__str__()


class BaseBroker(ABC):
    """Abstract base class for broker implementations."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the broker name."""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker.
        
        Returns:
            True if connected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the broker is connected."""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dictionary with account details (balance, equity, margin, etc.)
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object or None if no position exists
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """
        Get all orders, optionally filtered by status.
        
        Args:
            status: Optional filter for order status
            
        Returns:
            List of Order objects
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get an order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """
        Place a new order.
        
        Args:
            order: Order to place
            
        Returns:
            Updated order with broker-assigned ID and status
            
        Raises:
            Exception: If order placement fails
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if canceled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, **kwargs) -> Order:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            **kwargs: Parameters to modify (price, quantity, etc.)
            
        Returns:
            Updated order
            
        Raises:
            Exception: If order modification fails
        """
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        """
        Get historical market data.
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe (e.g., "1m", "5m", "1h", "1d")
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with price information (bid, ask, last)
        """
        pass
    
    def subscribe_to_market_data(self, symbol: str, callback: callable):
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data updates
            
        Note:
            Default implementation does nothing. Override in concrete classes.
        """
        pass
    
    def unsubscribe_from_market_data(self, symbol: str):
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbol: Trading symbol
            
        Note:
            Default implementation does nothing. Override in concrete classes.
        """
        pass