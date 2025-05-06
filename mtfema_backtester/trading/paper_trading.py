"""
Paper trading broker implementation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import threading
import time
import uuid
import logging
from copy import deepcopy

from mtfema_backtester.trading.broker import (
    BaseBroker, Order, Position, OrderType, OrderSide, 
    TimeInForce, OrderStatus
)
from mtfema_backtester.data.data_loader import DataLoader

logger = logging.getLogger(__name__)

class PaperTradingBroker(BaseBroker):
    """Paper trading broker implementation for simulated trading."""
    
    def __init__(
        self,
        initial_balance: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.0005,
        data_source: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the paper trading broker.
        
        Args:
            initial_balance: Initial account balance
            commission_rate: Commission rate (as a decimal)
            slippage: Slippage rate (as a decimal)
            data_source: Optional data source for historical data
            api_key: Optional API key for data source
        """
        self._name = "Paper Trading Broker"
        self._connected = False
        self._data_loader = DataLoader(data_source, api_key) if data_source else None
        
        # Account state
        self._initial_balance = initial_balance
        self._balance = initial_balance
        self._commission_rate = commission_rate
        self._slippage = slippage
        
        # Trading state
        self._positions = {}  # symbol -> Position
        self._orders = {}  # order_id -> Order
        self._market_data = {}  # symbol -> DataFrame
        self._current_prices = {}  # symbol -> price dict
        
        # Market data subscriptions
        self._subscriptions = {}  # symbol -> list of callbacks
        self._data_thread = None
        self._running = False
    
    @property
    def name(self) -> str:
        return self._name
    
    def connect(self) -> bool:
        """
        Connect to the paper trading broker.
        
        Returns:
            True if connected successfully
        """
        self._connected = True
        logger.info("Connected to paper trading broker")
        return True
    
    def disconnect(self) -> bool:
        """
        Disconnect from the paper trading broker.
        
        Returns:
            True if disconnected successfully
        """
        self._stop_data_thread()
        self._connected = False
        logger.info("Disconnected from paper trading broker")
        return True
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dictionary with account details
        """
        # Calculate total equity (balance + position values)
        equity = self._balance
        for position in self._positions.values():
            equity += position.unrealized_pnl
        
        return {
            "balance": self._balance,
            "equity": equity,
            "margin_used": 0.0,  # No margin in paper trading
            "margin_available": self._balance,
            "initial_balance": self._initial_balance,
            "pnl": equity - self._initial_balance,
            "pnl_percent": (equity / self._initial_balance - 1) * 100,
            "commission_paid": sum(order.commission for order in self._orders.values()),
            "positions_count": len(self._positions)
        }
    
    def get_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        return list(self._positions.values())
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object or None if no position exists
        """
        return self._positions.get(symbol)
    
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """
        Get all orders, optionally filtered by status.
        
        Args:
            status: Optional filter for order status
            
        Returns:
            List of Order objects
        """
        if status is None:
            return list(self._orders.values())
        
        return [order for order in self._orders.values() if order.status == status]
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get an order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        return self._orders.get(order_id)
    
    def place_order(self, order: Order) -> Order:
        """
        Place a new order.
        
        Args:
            order: Order to place
            
        Returns:
            Updated order with broker-assigned ID and status
            
        Raises:
            ValueError: If order parameters are invalid
            RuntimeError: If broker is not connected
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        # Validate the order
        self._validate_order(order)
        
        # Assign an ID and update status
        order.id = str(uuid.uuid4())
        order.status = OrderStatus.OPEN
        
        # Store the order
        self._orders[order.id] = order
        
        # For market orders, execute immediately
        if order.order_type == OrderType.MARKET:
            self._execute_market_order(order)
        
        logger.info(f"Placed order: {order}")
        return order
    
    def _validate_order(self, order: Order):
        """
        Validate an order before placing.
        
        Args:
            order: Order to validate
            
        Raises:
            ValueError: If order parameters are invalid
        """
        # Check if we have price data for the symbol
        if order.symbol not in self._current_prices:
            current_price = self.get_current_price(order.symbol)
            if not current_price:
                raise ValueError(f"No price data available for {order.symbol}")
        
        # For market orders, check if we have enough balance
        if order.order_type == OrderType.MARKET:
            current_price = self._current_prices[order.symbol]["last"]
            order_cost = current_price * order.quantity
            
            if order_cost > self._balance:
                raise ValueError(f"Insufficient balance: {self._balance} < {order_cost}")
    
    def _execute_market_order(self, order: Order):
        """
        Execute a market order.
        
        Args:
            order: Market order to execute
        """
        # Get the current price
        price_data = self._current_prices[order.symbol]
        
        # Determine execution price with slippage
        if order.side == OrderSide.BUY:
            execution_price = price_data["ask"] * (1 + self._slippage)
        else:
            execution_price = price_data["bid"] * (1 - self._slippage)
        
        # Calculate commission
        commission = execution_price * order.quantity * self._commission_rate
        
        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = execution_price
        order.commission = commission
        order.updated_at = datetime.now()
        
        # Add fill details
        order.fills.append({
            "quantity": order.quantity,
            "price": execution_price,
            "commission": commission,
            "timestamp": datetime.now()
        })
        
        # Update account balance
        self._balance -= commission
        
        # Update position
        self._update_position(order)
        
        logger.info(f"Executed market order: {order}")
    
    def _update_position(self, order: Order):
        """
        Update position after an order is filled.
        
        Args:
            order: Filled order
        """
        symbol = order.symbol
        existing_position = self._positions.get(symbol)
        
        # Calculate order cost/proceeds
        order_value = order.filled_quantity * order.avg_fill_price
        
        if order.side == OrderSide.BUY:
            # Buying
            self._balance -= order_value
            
            if existing_position is None:
                # New position
                self._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    avg_price=order.avg_fill_price,
                    side=OrderSide.BUY
                )
            elif existing_position.side == OrderSide.BUY:
                # Add to existing long position
                new_quantity = existing_position.quantity + order.filled_quantity
                new_avg_price = (
                    (existing_position.quantity * existing_position.avg_price) +
                    (order.filled_quantity * order.avg_fill_price)
                ) / new_quantity
                
                existing_position.quantity = new_quantity
                existing_position.avg_price = new_avg_price
                existing_position.updated_at = datetime.now()
            else:
                # Reduce or close short position
                if order.filled_quantity < existing_position.quantity:
                    # Partial cover
                    realized_pnl = (existing_position.avg_price - order.avg_fill_price) * order.filled_quantity
                    existing_position.quantity -= order.filled_quantity
                    existing_position.realized_pnl += realized_pnl
                    existing_position.updated_at = datetime.now()
                    self._balance += realized_pnl
                elif order.filled_quantity == existing_position.quantity:
                    # Full cover
                    realized_pnl = (existing_position.avg_price - order.avg_fill_price) * order.filled_quantity
                    self._balance += realized_pnl
                    del self._positions[symbol]
                else:
                    # Cover and open long
                    realized_pnl = (existing_position.avg_price - order.avg_fill_price) * existing_position.quantity
                    self._balance += realized_pnl
                    
                    new_quantity = order.filled_quantity - existing_position.quantity
                    self._positions[symbol] = Position(
                        symbol=symbol,
                        quantity=new_quantity,
                        avg_price=order.avg_fill_price,
                        side=OrderSide.BUY
                    )
        else:
            # Selling
            self._balance += order_value
            
            if existing_position is None:
                # New short position
                self._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    avg_price=order.avg_fill_price,
                    side=OrderSide.SELL
                )
            elif existing_position.side == OrderSide.SELL:
                # Add to existing short position
                new_quantity = existing_position.quantity + order.filled_quantity
                new_avg_price = (
                    (existing_position.quantity * existing_position.avg_price) +
                    (order.filled_quantity * order.avg_fill_price)
                ) / new_quantity
                
                existing_position.quantity = new_quantity
                existing_position.avg_price = new_avg_price
                existing_position.updated_at = datetime.now()
            else:
                # Reduce or close long position
                if order.filled_quantity < existing_position.quantity:
                    # Partial sell
                    realized_pnl = (order.avg_fill_price - existing_position.avg_price) * order.filled_quantity
                    existing_position.quantity -= order.filled_quantity
                    existing_position.realized_pnl += realized_pnl
                    existing_position.updated_at = datetime.now()
                    self._balance += realized_pnl
                elif order.filled_quantity == existing_position.quantity:
                    # Full sell
                    realized_pnl = (order.avg_fill_price - existing_position.avg_price) * order.filled_quantity
                    self._balance += realized_pnl
                    del self._positions[symbol]
                else:
                    # Sell and open short
                    realized_pnl = (order.avg_fill_price - existing_position.avg_price) * existing_position.quantity
                    self._balance += realized_pnl
                    
                    new_quantity = order.filled_quantity - existing_position.quantity
                    self._positions[symbol] = Position(
                        symbol=symbol,
                        quantity=new_quantity,
                        avg_price=order.avg_fill_price,
                        side=OrderSide.SELL
                    )
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if canceled successfully, False otherwise
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        order = self._orders.get(order_id)
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        if not order.is_active:
            logger.warning(f"Cannot cancel inactive order: {order}")
            return False
        
        order.status = OrderStatus.CANCELED
        order.updated_at = datetime.now()
        
        logger.info(f"Canceled order: {order}")
        return True
    
    def modify_order(self, order_id: str, **kwargs) -> Order:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            **kwargs: Parameters to modify (price, quantity, etc.)
            
        Returns:
            Updated order
            
        Raises:
            ValueError: If order modification fails
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        order = self._orders.get(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        if not order.is_active:
            raise ValueError(f"Cannot modify inactive order: {order}")
        
        # Update allowed fields
        allowed_fields = ["price", "stop_price", "quantity", "time_in_force"]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(order, field, value)
        
        order.updated_at = datetime.now()
        
        logger.info(f"Modified order: {order}")
        return order
    
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
        if self._data_loader:
            try:
                return self._data_loader.load_data(symbol, timeframe, count)
            except Exception as e:
                logger.error(f"Error loading market data: {e}")
        
        # If no data loader or error occurred, return empty DataFrame
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with price information (bid, ask, last)
        """
        # If we already have a price, return it
        if symbol in self._current_prices:
            return self._current_prices[symbol]
        
        # Otherwise, fetch latest data
        if self._data_loader:
            try:
                df = self._data_loader.load_data(symbol, "1m", 1)
                
                if not df.empty:
                    last_price = df["close"].iloc[-1]
                    # Simulate bid/ask spread
                    bid = last_price * 0.9995
                    ask = last_price * 1.0005
                    
                    price_data = {
                        "bid": bid,
                        "ask": ask,
                        "last": last_price,
                        "timestamp": datetime.now()
                    }
                    
                    self._current_prices[symbol] = price_data
                    return price_data
            except Exception as e:
                logger.error(f"Error getting current price: {e}")
        
        # If we can't get a price, generate a random one (for testing)
        base_price = 100.0
        last_price = base_price * (1 + np.random.normal(0, 0.01))
        
        price_data = {
            "bid": last_price * 0.9995,
            "ask": last_price * 1.0005,
            "last": last_price,
            "timestamp": datetime.now()
        }
        
        self._current_prices[symbol] = price_data
        return price_data
    
    def subscribe_to_market_data(self, symbol: str, callback: callable):
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data updates
        """
        if symbol not in self._subscriptions:
            self._subscriptions[symbol] = []
        
        if callback not in self._subscriptions[symbol]:
            self._subscriptions[symbol].append(callback)
        
        # Start the data thread if not already running
        if not self._data_thread or not self._running:
            self._start_data_thread()
        
        logger.info(f"Subscribed to market data for {symbol}")
    
    def unsubscribe_from_market_data(self, symbol: str):
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbol: Trading symbol
        """
        if symbol in self._subscriptions:
            del self._subscriptions[symbol]
            
        logger.info(f"Unsubscribed from market data for {symbol}")
        
        # Stop the data thread if no more subscriptions
        if not self._subscriptions and self._data_thread and self._running:
            self._stop_data_thread()
    
    def _start_data_thread(self):
        """Start the market data simulation thread."""
        self._running = True
        self._data_thread = threading.Thread(target=self._run_data_simulation)
        self._data_thread.daemon = True
        self._data_thread.start()
        
        logger.info("Started market data simulation thread")
    
    def _stop_data_thread(self):
        """Stop the market data simulation thread."""
        self._running = False
        if self._data_thread and self._data_thread.is_alive():
            self._data_thread.join(timeout=2.0)
            
        logger.info("Stopped market data simulation thread")
    
    def _run_data_simulation(self):
        """Run market data simulation."""
        last_update_time = time.time()
        update_interval = 1.0  # Update every second
        
        while self._running:
            current_time = time.time()
            
            # Update prices and notify subscribers
            if current_time - last_update_time >= update_interval:
                for symbol in list(self._subscriptions.keys()):
                    if not self._subscriptions.get(symbol):
                        continue
                    
                    # Get or update current price
                    price_data = self.get_current_price(symbol)
                    
                    # Add a small random change
                    last_price = price_data["last"]
                    new_price = last_price * (1 + np.random.normal(0, 0.001))
                    
                    # Update price data
                    price_data = {
                        "bid": new_price * 0.9995,
                        "ask": new_price * 1.0005,
                        "last": new_price,
                        "timestamp": datetime.now()
                    }
                    
                    self._current_prices[symbol] = price_data
                    
                    # Update position unrealized P&L
                    position = self._positions.get(symbol)
                    if position:
                        position.update_price(new_price)
                    
                    # Notify callbacks
                    for callback in self._subscriptions[symbol]:
                        try:
                            callback(symbol, price_data)
                        except Exception as e:
                            logger.error(f"Error in market data callback: {e}")
                
                last_update_time = current_time
            
            # Check for pending limit and stop orders
            for order_id, order in list(self._orders.items()):
                if not order.is_active:
                    continue
                
                if order.order_type in [OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT]:
                    if symbol not in self._current_prices:
                        continue
                    
                    current_price = self._current_prices[order.symbol]["last"]
                    
                    # Check if order should be triggered
                    if self._should_trigger_order(order, current_price):
                        self._execute_pending_order(order)
            
            # Sleep a bit to avoid high CPU usage
            time.sleep(0.01)
    
    def _should_trigger_order(self, order: Order, current_price: float) -> bool:
        """
        Check if an order should be triggered based on current price.
        
        Args:
            order: Order to check
            current_price: Current market price
            
        Returns:
            True if order should be triggered, False otherwise
        """
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and current_price <= order.price:
                return True
            elif order.side == OrderSide.SELL and current_price >= order.price:
                return True
        
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                return True
            elif order.side == OrderSide.SELL and current_price <= order.stop_price:
                return True
        
        elif order.order_type == OrderType.STOP_LIMIT:
            # First, check stop price
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                # Then, check limit price
                if current_price <= order.price:
                    return True
            elif order.side == OrderSide.SELL and current_price <= order.stop_price:
                # Then, check limit price
                if current_price >= order.price:
                    return True
        
        return False
    
    def _execute_pending_order(self, order: Order):
        """
        Execute a pending limit or stop order.
        
        Args:
            order: Order to execute
        """
        # Modify the order to a market order and execute it
        order.order_type = OrderType.MARKET
        self._execute_market_order(order)
