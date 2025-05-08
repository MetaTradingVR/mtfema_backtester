"""Tradovate broker implementation for MT 9 EMA Extension Strategy.

This module provides integration with the Tradovate API for live trading.
"""

import logging
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
import websocket

from .broker_interface import BrokerInterface, OrderStatus, OrderType, OrderSide, TimeInForce

logger = logging.getLogger(__name__)

class TradovateBroker(BrokerInterface):
    """Tradovate broker implementation.
    
    Implements the BrokerInterface for the Tradovate API.
    """
    
    def __init__(self, credentials: Dict[str, Any], is_paper: bool = True):
        """Initialize the Tradovate broker.
        
        Args:
            credentials: Dictionary with broker credentials
            is_paper: Whether to use paper trading
        """
        super().__init__(credentials, is_paper)
        
        # Base URL
        if is_paper:
            self._base_url = "https://demo.tradovateapi.com/v1/"
            self._ws_url = "wss://demo.tradovateapi.com/v1/websocket"
        else:
            self._base_url = "https://live.tradovateapi.com/v1/"
            self._ws_url = "wss://live.tradovateapi.com/v1/websocket"
            
        # Auth tokens
        self._access_token = None
        self._md_access_token = None  # Market data token
        
        # WebSocket
        self._ws = None
        self._ws_thread = None
        self._ws_connected = False
        self._ws_lock = threading.RLock()
        
        # Contract cache
        self._contract_cache = {}
        
        # Subscriptions for market data
        self._subscriptions = {}
        
        # Current prices
        self._current_prices = {}
        
        # Map of timeframes to Tradovate chart parameters
        self._timeframe_map = {
            "1m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 1},
            "5m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 5},
            "15m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 15},
            "30m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 30},
            "1h": {"chartDescription": "Hour", "chartUnit": "h", "chartUnits": 1},
            "4h": {"chartDescription": "Hour", "chartUnit": "h", "chartUnits": 4},
            "1d": {"chartDescription": "Day", "chartUnit": "d", "chartUnits": 1}
        }
    def connect(self) -> bool:
        """
        Connect to the Tradovate API.
        
        Returns:
            True if connection successful
        """
        if self.connected:
            logger.info("Already connected to Tradovate")
            return True
            
        try:
            # Authenticate with Tradovate API
            logger.info("Connecting to Tradovate API...")
            
            # Get authentication credentials
            username = self.credentials.get("username")
            password = self.credentials.get("password")
            client_id = self.credentials.get("client_id")
            client_secret = self.credentials.get("client_secret")
            
            if not all([username, password, client_id, client_secret]):
                raise ValueError("Missing required credentials for Tradovate")
            
            # Authenticate with password grant
            url = urljoin(self._base_url, "auth/accesstokenrequest")
            
            payload = {
                "name": username,
                "password": password,
                "appId": client_id,
                "appVersion": "1.0",
                "cid": client_id,
                "sec": client_secret
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            auth_data = response.json()
            self._access_token = auth_data.get("accessToken")
            self.account_id = auth_data.get("userId")
            
            if not self._access_token:
                raise ValueError("Failed to get access token from Tradovate")
            
            # Also get market data access token if different from main token
            self._md_access_token = self._access_token
            
            # Initialize WebSocket connection
            self._init_websocket()
            
            # Update connected state
            self.connected = True
            
            logger.info("Successfully connected to Tradovate API")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Tradovate API: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the Tradovate API.
        
        Returns:
            True if disconnection successful
        """
        if not self.connected:
            return True
            
        try:
            logger.info("Disconnecting from Tradovate API...")
            
            # Close WebSocket connection
            self._close_websocket()
            
            # Clear tokens and state
            self._access_token = None
            self._md_access_token = None
            self.connected = False
            
            logger.info("Successfully disconnected from Tradovate API")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from Tradovate API: {str(e)}")
            return False
    
    def _init_websocket(self):
        """
        Initialize WebSocket connection for real-time data.
        """
        try:
            # Initialize WebSocket connection
            if self._ws_connected or self._ws_thread and self._ws_thread.is_alive():
                return
                
            # Create WebSocket connection
            def on_message(ws, message):
                self._handle_ws_message(message)
                
            def on_error(ws, error):
                logger.error(f"WebSocket error: {str(error)}")
                
            def on_close(ws, close_status_code, close_msg):
                logger.info(f"WebSocket closed: {close_msg}")
                self._ws_connected = False
                
            def on_open(ws):
                logger.info("WebSocket connection opened")
                self._ws_connected = True
                
                # Authenticate WebSocket
                auth_msg = {
                    "command": "authorize",
                    "payload": {
                        "token": self._access_token
                    }
                }
                ws.send(json.dumps(auth_msg))
                
            # Create WebSocket with callbacks
            self._ws = websocket.WebSocketApp(
                self._ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Start WebSocket in a separate thread
            self._ws_thread = threading.Thread(
                target=self._ws.run_forever,
                daemon=True
            )
            self._ws_thread.start()
            
            # Wait for connection to establish
            start_time = time.time()
            while not self._ws_connected and time.time() - start_time < 10:
                time.sleep(0.1)
                
            if not self._ws_connected:
                raise RuntimeError("Failed to establish WebSocket connection")
                
        except Exception as e:
            logger.error(f"Error initializing WebSocket: {str(e)}")
            self._ws_connected = False
            
    def _close_websocket(self):
        """
        Close WebSocket connection.
        """
        try:
            if self._ws:
                self._ws.close()
                
            self._ws_connected = False
            
            if self._ws_thread and self._ws_thread.is_alive():
                self._ws_thread.join(timeout=2.0)
                
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}")
            
    def _handle_ws_message(self, message):
        """
        Handle WebSocket message.
        
        Args:
            message: Message from WebSocket
        """
        try:
            msg_data = json.loads(message)
            
            # Check message type
            if "e" in msg_data:  # Event message
                event_type = msg_data.get("e")
                data = msg_data.get("d", {})
                
                if event_type == "md":
                    # Market data update
                    self._handle_market_data_update(data)
                    
                elif event_type == "order":
                    # Order update
                    self._handle_order_update(data)
                    
                elif event_type == "position":
                    # Position update
                    self._handle_position_update(data)
                    
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
            
    def _handle_market_data_update(self, data):
        """
        Handle market data update from WebSocket.
        
        Args:
            data: Market data update
        """
        try:
            symbol = data.get("s")  # Symbol
            
            if not symbol or symbol not in self._subscriptions:
                return
                
            # Update price data
            price_data = {
                "bid": float(data.get("b", 0)),
                "ask": float(data.get("a", 0)),
                "last": float(data.get("l", 0)),
                "timestamp": datetime.now()
            }
            
            # If missing last price, use mid price
            if price_data["last"] == 0 and price_data["bid"] > 0 and price_data["ask"] > 0:
                price_data["last"] = (price_data["bid"] + price_data["ask"]) / 2
                
            # Update current prices
            self._current_prices[symbol] = price_data
            
            # Notify callbacks
            for callback in self._subscriptions.get(symbol, []):
                try:
                    callback(price_data)
                except Exception as e:
                    logger.error(f"Error in market data callback: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error handling market data update: {str(e)}")
            
    def _handle_order_update(self, data):
        """
        Handle order update from WebSocket.
        
        Args:
            data: Order update data
        """
        try:
            order_id = str(data.get("orderId"))
            
            if not order_id:
                return
                
            # Convert to standard format
            order = self._convert_tradovate_order(data)
            
            # Update orders
            self.orders[order_id] = order
            
        except Exception as e:
            logger.error(f"Error handling order update: {str(e)}")
            
    def _handle_position_update(self, data):
        """
        Handle position update from WebSocket.
        
        Args:
            data: Position update data
        """
        try:
            position_id = str(data.get("positionId"))
            contract_id = data.get("contractId")
            
            if not position_id or not contract_id:
                return
                
            # Convert to standard format
            position = self._convert_tradovate_position(data)
            
            # Update positions
            self.positions[position_id] = position
            
        except Exception as e:
            logger.error(f"Error handling position update: {str(e)}")
            
    def _get_contract_id(self, symbol: str) -> Optional[int]:
        """
        Get contract ID for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Contract ID or None if not found
        """
        # Check cache first
        if symbol in self._contract_cache:
            return self._contract_cache[symbol]
            
        try:
            # Find contract
            url = urljoin(self._base_url, "contract/find")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            params = {
                "name": symbol
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            contracts = response.json()
            
            if not contracts:
                return None
                
            # Get first matching contract
            contract_id = contracts[0].get("id")
            
            # Cache the result
            if contract_id:
                self._contract_cache[symbol] = contract_id
                
            return contract_id
            
        except Exception as e:
            logger.error(f"Error getting contract ID: {str(e)}")
            return None
            
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dict with account information
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Get account information
            url = urljoin(self._base_url, "account/list")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            accounts = response.json()
            
            if not accounts:
                raise ValueError("No accounts found")
                
            # Get first account
            account = accounts[0]
            account_id = account.get("id")
            
            # Get account balance
            url = urljoin(self._base_url, "accountRiskStatus/get")
            
            params = {
                "accountId": account_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            risk_status = response.json()
            
            # Extract account information
            balance = risk_status.get("netLiq", 0.0)
            available = risk_status.get("availableFunds", 0.0)
            margin = risk_status.get("initialMargin", 0.0)
            
            return {
                "account_id": account_id,
                "balance": balance,
                "available": available,
                "margin": margin,
                "currency": "USD"
            }
            
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            
            # Return default values
            return {
                "account_id": self.account_id,
                "balance": 0.0,
                "available": 0.0,
                "margin": 0.0,
                "currency": "USD"
            }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of positions
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Refresh positions
            self._sync_positions()
            
            # Convert to list
            return list(self.positions.values())
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def _sync_positions(self):
        """
        Synchronize positions with Tradovate API.
        """
        try:
            # Get account ID
            account_info = self.get_account_info()
            account_id = account_info.get("account_id")
            
            if not account_id:
                return
                
            # Get positions
            url = urljoin(self._base_url, "position/list")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            params = {
                "accountId": account_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            positions = response.json()
            
            # Clear current positions
            self.positions = {}
            
            # Process positions
            for position in positions:
                # Convert to standard format
                pos = self._convert_tradovate_position(position)
                
                # Store by ID
                self.positions[pos["id"]] = pos
                
        except Exception as e:
            logger.error(f"Error syncing positions: {str(e)}")
    
    def _convert_tradovate_position(self, position) -> Dict[str, Any]:
        """
        Convert Tradovate position to standard format.
        
        Args:
            position: Tradovate position data
            
        Returns:
            Standardized position data
        """
        try:
            position_id = str(position.get("id"))
            contract_id = position.get("contractId")
            
            # Get contract details
            contract = self._get_contract_by_id(contract_id)
            symbol = contract.get("name") if contract else "Unknown"
            
            # Determine direction and quantity
            netpos = position.get("netPos", 0)
            direction = "long" if netpos > 0 else "short"
            quantity = abs(netpos)
            
            # Calculate profit/loss
            avg_price = position.get("avgPrice", 0.0)
            current_price = 0.0
            
            if symbol in self._current_prices:
                current_price = self._current_prices[symbol].get("last", 0.0)
                
            # Calculate position value
            point_value = contract.get("pointValue", 1.0) if contract else 1.0
            price_delta = current_price - avg_price if direction == "long" else avg_price - current_price
            unrealized_pl = price_delta * quantity * point_value
            
            return {
                "id": position_id,
                "symbol": symbol,
                "direction": direction,
                "quantity": quantity,
                "entry_price": avg_price,
                "current_price": current_price,
                "unrealized_pl": unrealized_pl,
                "realized_pl": position.get("totalPl", 0.0) - unrealized_pl,
                "timestamp": datetime.now(),
                "status": "open"
            }
            
        except Exception as e:
            logger.error(f"Error converting position: {str(e)}")
            
            # Return default values
            return {
                "id": position.get("id", str(uuid.uuid4())),
                "symbol": "Unknown",
                "direction": "long",
                "quantity": 0,
                "entry_price": 0.0,
                "current_price": 0.0,
                "unrealized_pl": 0.0,
                "realized_pl": 0.0,
                "timestamp": datetime.now(),
                "status": "unknown"
            }
    
    def _get_contract_by_id(self, contract_id) -> Optional[Dict[str, Any]]:
        """
        Get contract details by ID.
        
        Args:
            contract_id: Contract ID
            
        Returns:
            Contract details or None if not found
        """
        try:
            # Get contract details
            url = urljoin(self._base_url, "contract/get")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            params = {
                "id": contract_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting contract details: {str(e)}")
            return None
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get orders with optional status filter.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of orders
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Refresh orders
            self._sync_orders()
            
            if status is None:
                return list(self.orders.values())
                
            # Filter by status
            return [order for order in self.orders.values() if order["status"] == status]
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def _sync_orders(self):
        """
        Synchronize orders with Tradovate API.
        """
        try:
            # Get account ID
            account_info = self.get_account_info()
            account_id = account_info.get("account_id")
            
            if not account_id:
                return
                
            # Get orders
            url = urljoin(self._base_url, "order/list")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            params = {
                "accountId": account_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            orders = response.json()
            
            # Clear current orders
            self.orders = {}
            
            # Process orders
            for order in orders:
                # Convert to standard format
                ord = self._convert_tradovate_order(order)
                
                # Store by ID
                self.orders[ord["id"]] = ord
                
        except Exception as e:
            logger.error(f"Error syncing orders: {str(e)}")
    
    def _convert_tradovate_order(self, order) -> Dict[str, Any]:
        """
        Convert Tradovate order to standard format.
        
        Args:
            order: Tradovate order data
            
        Returns:
            Standardized order data
        """
        try:
            order_id = str(order.get("id"))
            contract_id = order.get("contractId")
            
            # Get contract details
            contract = self._get_contract_by_id(contract_id)
            symbol = contract.get("name") if contract else "Unknown"
            
            # Determine order type
            order_type_map = {
                "Market": OrderType.MARKET,
                "Limit": OrderType.LIMIT,
                "Stop": OrderType.STOP,
                "StopLimit": OrderType.STOP_LIMIT
            }
            
            order_type = order_type_map.get(order.get("orderType"), OrderType.MARKET)
            
            # Determine side
            action = order.get("action")
            side = OrderSide.BUY if action == "Buy" else OrderSide.SELL
            
            # Determine status
            status_map = {
                "Working": OrderStatus.ACCEPTED,
                "Completed": OrderStatus.COMPLETED,
                "Canceled": OrderStatus.CANCELED,
                "Rejected": OrderStatus.REJECTED,
                "Pending": OrderStatus.PENDING
            }
            
            status = status_map.get(order.get("status"), OrderStatus.PENDING)
            
            return {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "quantity": order.get("qty", 0),
                "filled": order.get("filledQty", 0),
                "order_type": order_type,
                "limit_price": order.get("limitPrice", 0.0),
                "stop_price": order.get("stopPrice", 0.0),
                "status": status,
                "timestamp": datetime.fromtimestamp(order.get("timestamp", time.time()) / 1000) if order.get("timestamp") else datetime.now(),
                "account_id": order.get("accountId")
            }
            
        except Exception as e:
            logger.error(f"Error converting order: {str(e)}")
            
            # Return default values
            return {
                "id": order.get("id", str(uuid.uuid4())),
                "symbol": "Unknown",
                "side": OrderSide.BUY,
                "quantity": 0,
                "filled": 0,
                "order_type": OrderType.MARKET,
                "limit_price": 0.0,
                "stop_price": 0.0,
                "status": OrderStatus.PENDING,
                "timestamp": datetime.now(),
                "account_id": order.get("accountId")
            }
    
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
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Get contract ID
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
                
            # Get account ID
            account_info = self.get_account_info()
            account_id = account_info.get("account_id")
            
            if not account_id:
                raise ValueError("Account not found")
                
            # Map order type
            type_map = {
                OrderType.MARKET: "Market",
                OrderType.LIMIT: "Limit",
                OrderType.STOP: "Stop",
                OrderType.STOP_LIMIT: "StopLimit"
            }
            
            tradovate_order_type = type_map.get(order_type, "Market")
            
            # Map side
            action = "Buy" if side == OrderSide.BUY else "Sell"
            
            # Map time in force
            tif_map = {
                TimeInForce.GTC: "GTC",
                TimeInForce.IOC: "IOC",
                TimeInForce.FOK: "FOK",
                TimeInForce.DAY: "Day"
            }
            
            tradovate_tif = tif_map.get(time_in_force, "GTC")
            
            # Prepare order payload
            payload = {
                "accountId": account_id,
                "contractId": contract_id,
                "action": action,
                "orderQty": int(quantity),
                "orderType": tradovate_order_type,
                "timeInForce": tradovate_tif
            }
            
            # Add prices if needed
            if tradovate_order_type in ["Limit", "StopLimit"] and limit_price is not None:
                payload["limitPrice"] = limit_price
                
            if tradovate_order_type in ["Stop", "StopLimit"] and stop_price is not None:
                payload["stopPrice"] = stop_price
                
            # Place order
            url = urljoin(self._base_url, "order/placeOrder")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            order_data = response.json()
            
            # Convert to standard format
            order = self._convert_tradovate_order(order_data)
            
            # Update orders
            self.orders[order["id"]] = order
            
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            
            # Return default values
            return {
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "filled": 0,
                "order_type": order_type,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "status": OrderStatus.REJECTED,
                "timestamp": datetime.now(),
                "error": str(e)
            }
            
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation successful
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Get order details
            order = self.orders.get(order_id)
            if not order:
                # Try to find order
                orders = self.get_orders()
                for o in orders:
                    if o["id"] == order_id:
                        order = o
                        break
                        
            if not order:
                raise ValueError(f"Order not found: {order_id}")
                
            # Check if order can be canceled
            if order["status"] in [OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.REJECTED]:
                logger.warning(f"Order cannot be canceled (status: {order['status']}): {order_id}")
                return False
                
            # Cancel order
            url = urljoin(self._base_url, "order/cancelOrder")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            payload = {
                "orderId": int(order_id)
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Update order status
            self.orders[order_id]["status"] = OrderStatus.CANCELED
            
            return True
            
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            return False
    
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
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Get order details
            order = self.orders.get(order_id)
            if not order:
                # Try to find order
                orders = self.get_orders()
                for o in orders:
                    if o["id"] == order_id:
                        order = o
                        break
                        
            if not order:
                raise ValueError(f"Order not found: {order_id}")
                
            # Check if order can be modified
            if order["status"] in [OrderStatus.COMPLETED, OrderStatus.CANCELED, OrderStatus.REJECTED]:
                raise ValueError(f"Order cannot be modified (status: {order['status']}): {order_id}")
                
            # Prepare modify payload
            payload = {
                "orderId": int(order_id)
            }
            
            # Add parameters to modify
            changes_made = False
            
            if quantity is not None and quantity != order["quantity"]:
                payload["orderQty"] = int(quantity)
                changes_made = True
                
            if limit_price is not None and limit_price != order["limit_price"]:
                payload["limitPrice"] = limit_price
                changes_made = True
                
            if stop_price is not None and stop_price != order["stop_price"]:
                payload["stopPrice"] = stop_price
                changes_made = True
                
            if not changes_made:
                logger.warning(f"No changes to make for order: {order_id}")
                return order
                
            # Modify order
            url = urljoin(self._base_url, "order/modifyOrder")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Get updated order
            order_data = response.json()
            
            # Convert to standard format
            updated_order = self._convert_tradovate_order(order_data)
            
            # Update orders
            self.orders[order_id] = updated_order
            
            return updated_order
            
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            
            # Return original order
            return order if order else {
                "id": order_id,
                "status": OrderStatus.REJECTED,
                "error": str(e)
            }
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get status of a specific order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Dict: Order status information
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Check if we have this order
            if order_id in self.orders:
                # Refresh orders
                self._sync_orders()
                
                return self.orders.get(order_id, {
                    "id": order_id,
                    "status": OrderStatus.REJECTED,
                    "error": "Order not found"
                })
            
            # Try to find order
            url = urljoin(self._base_url, "order/get")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            params = {
                "id": int(order_id)
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                return {
                    "id": order_id,
                    "status": OrderStatus.REJECTED,
                    "error": "Order not found"
                }
                
            response.raise_for_status()
            
            # Convert to standard format
            order_data = response.json()
            order = self._convert_tradovate_order(order_data)
            
            # Update orders
            self.orders[order_id] = order
            
            return order
            
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            
            return {
                "id": order_id,
                "status": OrderStatus.REJECTED,
                "error": str(e)
            }
    
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
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Get contract ID
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
                
            if data_type == "quote":
                # Return current price
                return self.get_current_price(symbol)
                
            # Request market data
            url = urljoin(self._base_url, "md/getQuote")
            
            headers = {
                "Authorization": f"Bearer {self._md_access_token}"
            }
            
            params = {
                "contractId": contract_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format data based on type
            if data_type == "orderbook":
                return {
                    "bids": [{ "price": data.get("bid", 0.0), "size": data.get("bidSize", 0) }],
                    "asks": [{ "price": data.get("ask", 0.0), "size": data.get("askSize", 0) }],
                    "timestamp": datetime.now()
                }
                
            else:  # Default to quote
                bid = data.get("bid", 0.0)
                ask = data.get("ask", 0.0)
                last = data.get("last", 0.0)
                
                # If missing last price, use mid price
                if last == 0.0 and bid > 0.0 and ask > 0.0:
                    last = (bid + ask) / 2
                
                price_data = {
                    "bid": bid,
                    "ask": ask,
                    "last": last,
                    "volume": data.get("volume", 0),
                    "timestamp": datetime.now()
                }
                
                # Update current prices
                self._current_prices[symbol] = price_data
                
                return price_data
                
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            
            # Return default values
            return {
                "bid": 0.0,
                "ask": 0.0,
                "last": 0.0,
                "volume": 0,
                "timestamp": datetime.now()
            }
    
    def get_historical_data(self,
                          symbol: str,
                          timeframe: str,
                          start_time: datetime,
                          end_time: datetime,
                          **kwargs) -> Optional[pd.DataFrame]:
        """
        Get historical market data.
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe (e.g., "1m", "1h")
            start_time: Start time for data
            end_time: End time for data
            **kwargs: Additional parameters
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
            
        try:
            # Estimate number of bars
            # Calculate approximate bars based on timeframe and date range
            tf_minutes = {
                "1m": 1,
                "5m": 5,
                "15m": 15,
                "30m": 30,
                "1h": 60,
                "4h": 240,
                "1d": 1440
            }
            
            minutes = tf_minutes.get(timeframe, 60)
            time_diff = (end_time - start_time).total_seconds() / 60
            count = min(int(time_diff / minutes) + 10, 5000)  # Tradovate limit is often 5000 bars
            
            # Get contract ID
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
                
            # Check if timeframe is supported
            if timeframe not in self._timeframe_map:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
                
            # Map timeframe to Tradovate chart parameters
            tf_settings = self._timeframe_map[timeframe]
            
            # Prepare chart request
            url = urljoin(self._base_url, "chart/get")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            payload = {
                "contractId": contract_id,
                "chartDescription": tf_settings["chartDescription"],
                "underlyingType": "contract",
                "chartUnit": tf_settings["chartUnit"],
                "chartUnits": tf_settings["chartUnits"],
                "barsBack": count
            }
            
            # Get chart data
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            chart_data = response.json()
            bars = chart_data.get("bars", [])
            
            # Convert to DataFrame
            data = {
                "timestamp": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": []
            }
            
            for bar in bars:
                data["timestamp"].append(datetime.fromtimestamp(bar["timestamp"] / 1000))
                data["open"].append(bar["open"])
                data["high"].append(bar["high"])
                data["low"].append(bar["low"])
                data["close"].append(bar["close"])
                data["volume"].append(bar.get("volume", 0))
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index("timestamp", inplace=True)
                
                # Filter by date range
                df = df[(df.index >= start_time) & (df.index <= end_time)]
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
            
    def subscribe_to_market_data(self, symbol: str, callback: callable):
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data updates
        """
        if not self.connected:
            raise RuntimeError("Broker is not connected")
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
            
            # Initialize subscription list if needed
            if symbol not in self._subscriptions:
                self._subscriptions[symbol] = []
            
            # Add callback if not already subscribed
            if callback not in self._subscriptions[symbol]:
                self._subscriptions[symbol].append(callback)
            
            # Subscribe to market data via WebSocket
            if self._ws_connected:
                with self._ws_lock:
                    subscribe_msg = {
                        "command": "md-subscribe",
                        "payload": {
                            "Symbol": symbol,
                            "ContractId": contract_id
                        }
                    }
                    self._ws.send(json.dumps(subscribe_msg))
            
            logger.info(f"Subscribed to market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error subscribing to market data: {str(e)}")
    
    def unsubscribe_from_market_data(self, symbol: str):
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbol: Trading symbol
        """
        if not self.connected:
            return
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                return
            
            # Remove all callbacks
            if symbol in self._subscriptions:
                del self._subscriptions[symbol]
            
            # Unsubscribe from market data via WebSocket
            if self._ws_connected:
                with self._ws_lock:
                    unsubscribe_msg = {
                        "command": "md-unsubscribe",
                        "payload": {
                            "Symbol": symbol,
                            "ContractId": contract_id
                        }
                    }
                    self._ws.send(json.dumps(unsubscribe_msg))
            
            logger.info(f"Unsubscribed from market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing from market data: {str(e)}")

    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with price information (bid, ask, last)
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        # First check if we already have price data
        if symbol in self._current_prices:
            return self._current_prices[symbol]
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
            
            # Request quote data
            url = urljoin(self._base_url, "md/getQuote")
            
            headers = {
                "Authorization": f"Bearer {self._md_access_token}"
            }
            
            params = {
                "contractId": contract_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            quote_data = response.json()
            
            # Extract price data
            bid = quote_data.get("bid", 0.0)
            ask = quote_data.get("ask", 0.0)
            last = quote_data.get("last", 0.0)
            
            # If missing last price, use mid price
            if last == 0.0 and bid > 0.0 and ask > 0.0:
                last = (bid + ask) / 2
            
            # Create price data
            price_data = {
                "bid": bid,
                "ask": ask,
                "last": last,
                "timestamp": datetime.now()
            }
            
            # Update current prices
            self._current_prices[symbol] = price_data
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            
            # Return default values
            return {
                "bid": 0.0,
                "ask": 0.0,
                "last": 0.0,
                "timestamp": datetime.now()
            }
    
    def subscribe_to_market_data(self, symbol: str, callback: callable):
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data updates
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
            
            # Initialize subscription list if needed
            if symbol not in self._subscriptions:
                self._subscriptions[symbol] = []
            
            # Add callback if not already subscribed
            if callback not in self._subscriptions[symbol]:
                self._subscriptions[symbol].append(callback)
            
            # Subscribe to market data via WebSocket
            if self._ws_connected:
                with self._ws_lock:
                    subscribe_msg = {
                        "command": "md-subscribe",
                        "payload": {
                            "Symbol": symbol,
                            "ContractId": contract_id
                        }
                    }
                    self._ws.send(json.dumps(subscribe_msg))
            
            logger.info(f"Subscribed to market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error subscribing to market data: {str(e)}")
    
    def unsubscribe_from_market_data(self, symbol: str):
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbol: Trading symbol
        """
        if not self.is_connected:
            return
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                return
            
            # Remove all callbacks
            if symbol in self._subscriptions:
                del self._subscriptions[symbol]
            
            # Unsubscribe via WebSocket
            if self._ws_connected:
                with self._ws_lock:
                    unsubscribe_msg = {
                        "command": "md-unsubscribe",
                        "payload": {
                            "Symbol": symbol,
                            "ContractId": contract_id
                        }
                    }
                    self._ws.send(json.dumps(unsubscribe_msg))
            
            logger.info(f"Unsubscribed from market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing from market data: {str(e)}")
