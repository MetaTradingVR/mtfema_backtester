"""
Live trading implementation for the MT 9 EMA Extension Strategy.

This module integrates the strategy with broker APIs to enable live trading.
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import uuid
import json
from pathlib import Path

from .broker_interface import BrokerInterface, BrokerFactory, OrderStatus
from ..strategy.signal_generator import generate_signals
from .trade_executor import TradeExecutor
from .strategy_adapter import StrategyAdapter

logger = logging.getLogger(__name__)

class LiveTrader:
    """
    Live trading implementation for the MT 9 EMA Strategy.
    
    This class connects to a broker, receives market data,
    generates trading signals, and manages orders/positions.
    """
    
    def __init__(self, 
                 broker: BrokerInterface,
                 strategy_params: Dict[str, Any],
                 risk_settings: Dict[str, Any],
                 symbols: List[str],
                 timeframes: List[str],
                 data_dir: str = "./data/live"):
        """
        Initialize the live trader.
        
        Args:
            broker: Configured broker interface
            strategy_params: Strategy parameters
            risk_settings: Risk management settings
            symbols: List of symbols to trade
            timeframes: List of timeframes to analyze
            data_dir: Directory for storing market data
        """
        self.broker = broker
        self.strategy_params = strategy_params
        self.risk_settings = risk_settings
        self.symbols = symbols
        self.timeframes = timeframes
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # State variables
        self.running = False
        self.market_data = {}  # Symbol -> Timeframe -> DataFrame
        self.last_signal_time = {}  # Symbol -> Timeframe -> Datetime
        self.signal_callbacks = []
        self.order_callbacks = []
        self.position_callbacks = []
        
        # Initialize trade executors (one per symbol)
        self.executors = {}
        for symbol in symbols:
            self.executors[symbol] = TradeExecutor(
                strategy=None,  # We'll generate signals externally
                account_balance=self._get_account_balance(),
                risk_settings=risk_settings
            )
            
        # Initialize strategy adapter
        self.strategy_adapter = StrategyAdapter()
        
        # Trading threads and locks
        self.market_data_thread = None
        self.signal_thread = None
        self.execution_thread = None
        self.data_lock = threading.RLock()
        
        logger.info(f"LiveTrader initialized for {len(symbols)} symbols across {len(timeframes)} timeframes")
        
    def start(self):
        """
        Start the live trading system.
        
        This will connect to the broker, start market data subscriptions,
        and begin the signal generation and order execution processes.
        """
        if self.running:
            logger.warning("Live trader is already running")
            return
            
        logger.info("Starting live trader...")
        
        # Connect to broker if not already connected
        if not self.broker.connected:
            success = self.broker.connect()
            if not success:
                logger.error("Failed to connect to broker")
                return False
                
        # Start market data thread
        self.running = True
        self.market_data_thread = threading.Thread(
            target=self._market_data_worker,
            daemon=True
        )
        self.market_data_thread.start()
        
        # Start signal generation thread
        self.signal_thread = threading.Thread(
            target=self._signal_generation_worker,
            daemon=True
        )
        self.signal_thread.start()
        
        # Start execution thread
        self.execution_thread = threading.Thread(
            target=self._execution_worker,
            daemon=True
        )
        self.execution_thread.start()
        
        logger.info("Live trader started successfully")
        return True
        
    def stop(self):
        """
        Stop the live trading system.
        
        This will stop all threads and disconnect from the broker.
        """
        if not self.running:
            logger.warning("Live trader is not running")
            return
            
        logger.info("Stopping live trader...")
        
        # Signal threads to stop
        self.running = False
        
        # Wait for threads to complete
        if self.market_data_thread:
            self.market_data_thread.join(timeout=5.0)
            
        if self.signal_thread:
            self.signal_thread.join(timeout=5.0)
            
        if self.execution_thread:
            self.execution_thread.join(timeout=5.0)
            
        # Disconnect from broker
        if self.broker.connected:
            self.broker.disconnect()
            
        logger.info("Live trader stopped successfully")
        
    def add_signal_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add a callback function for signal events.
        
        Args:
            callback: Function to call when a signal is generated
        """
        self.signal_callbacks.append(callback)
        
    def add_order_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add a callback function for order events.
        
        Args:
            callback: Function to call when an order is updated
        """
        self.order_callbacks.append(callback)
        
    def add_position_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add a callback function for position events.
        
        Args:
            callback: Function to call when a position is updated
        """
        self.position_callbacks.append(callback)
        
    def get_market_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Get the latest market data for a symbol and timeframe.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., "1m", "1h")
            
        Returns:
            DataFrame with market data or None if not available
        """
        with self.data_lock:
            if symbol in self.market_data and timeframe in self.market_data[symbol]:
                return self.market_data[symbol][timeframe].copy()
        return None
        
    def get_active_signals(self) -> List[Dict[str, Any]]:
        """
        Get all active signals that haven't been executed.
        
        Returns:
            List of active signals
        """
        signals = []
        for symbol, executor in self.executors.items():
            # Each executor might have pending signals
            for signal in executor.get_pending_signals():
                signals.append(signal)
        return signals
    
    def _get_account_balance(self) -> float:
        """
        Get current account balance from broker.
        
        Returns:
            Current account balance
        """
        try:
            account_info = self.broker.get_account_info()
            balance = account_info.get('balance', 0.0)
            logger.info(f"Current account balance: ${balance:.2f}")
            return balance
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            return 10000.0  # Default fallback balance
    
    def _market_data_worker(self):
        """
        Worker thread for fetching and updating market data.
        """
        logger.info("Market data worker started")
        
        # Initialize data structures for each symbol and timeframe
        for symbol in self.symbols:
            self.market_data[symbol] = {}
            
            for timeframe in self.timeframes:
                self.market_data[symbol][timeframe] = pd.DataFrame()
                self.last_signal_time[symbol] = {}
        
        # Initialize update intervals for each timeframe
        update_intervals = {
            "1m": 60,   # 1 minute in seconds
            "5m": 300,  # 5 minutes in seconds
            "15m": 900,  # 15 minutes
            "30m": 1800,  # 30 minutes
            "1h": 3600,  # 1 hour
            "4h": 14400,  # 4 hours
            "1d": 86400   # 1 day
        }
        
        # Last update time for each symbol and timeframe
        last_update = {}
        for symbol in self.symbols:
            last_update[symbol] = {}
            for timeframe in self.timeframes:
                last_update[symbol][timeframe] = time.time() - update_intervals.get(timeframe, 60)
        
        while self.running:
            try:
                current_time = time.time()
                
                for symbol in self.symbols:
                    for timeframe in self.timeframes:
                        interval = update_intervals.get(timeframe, 60)
                        
                        # Check if it's time to update this timeframe
                        if current_time - last_update[symbol][timeframe] >= interval:
                            try:
                                # Fetch new market data
                                data = self.broker.get_historical_data(
                                    symbol=symbol,
                                    timeframe=timeframe,
                                    start_time=datetime.now() - timedelta(days=5),
                                    end_time=datetime.now()
                                )
                                
                                if data is not None:
                                    with self.data_lock:
                                        self.market_data[symbol][timeframe] = data
                                    
                                    # Save to file
                                    self._save_market_data(symbol, timeframe, data)
                                    
                                last_update[symbol][timeframe] = current_time
                                
                            except Exception as e:
                                logger.error(f"Error fetching market data for {symbol} {timeframe}: {str(e)}")
                
                # Sleep for a short period to avoid high CPU usage
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in market data worker: {str(e)}")
                time.sleep(5.0)  # Longer sleep on error
        
        logger.info("Market data worker stopped")
    
    def _signal_generation_worker(self):
        """
        Worker thread for generating trading signals.
        """
        logger.info("Signal generation worker started")
        
        # Initialize signal generation intervals
        signal_intervals = {
            "1m": 60,   # Check for 1m signals every 60 seconds
            "5m": 120,  # Check for 5m signals every 2 minutes
            "15m": 300,  # Every 5 minutes
            "30m": 600,  # Every 10 minutes
            "1h": 900,   # Every 15 minutes
            "4h": 1800,  # Every 30 minutes
            "1d": 3600   # Every hour
        }
        
        # Last signal check time for each symbol and timeframe
        last_check = {}
        for symbol in self.symbols:
            last_check[symbol] = {}
            for timeframe in self.timeframes:
                last_check[symbol][timeframe] = time.time() - signal_intervals.get(timeframe, 60)
        
        while self.running:
            try:
                current_time = time.time()
                
                for symbol in self.symbols:
                    for timeframe in self.timeframes:
                        interval = signal_intervals.get(timeframe, 60)
                        
                        # Check if it's time to generate signals for this timeframe
                        if current_time - last_check[symbol][timeframe] >= interval:
                            try:
                                # Get latest market data
                                data = self.get_market_data(symbol, timeframe)
                                if data is not None and not data.empty:
                                    # Generate signals
                                    signals = generate_signals(data, self.strategy_params)
                                    
                                    if signals and not signals.empty:
                                        # Get the latest signal
                                        latest_signal = signals.iloc[-1].to_dict()
                                        
                                        # Check if this is a new signal
                                        signal_time = latest_signal.get('datetime')
                                        last_time = self.last_signal_time[symbol].get(timeframe)
                                        
                                        if last_time is None or signal_time > last_time:
                                            # Convert to TradeExecutor format
                                            adapted_signals = self.strategy_adapter.convert_signals(
                                                [latest_signal], 
                                                {timeframe: data.iloc[-1].to_dict()}
                                            )
                                            
                                            for signal in adapted_signals:
                                                # Add symbol if not present
                                                if 'symbol' not in signal:
                                                    signal['symbol'] = symbol
                                                
                                                # Notify callbacks
                                                for callback in self.signal_callbacks:
                                                    try:
                                                        callback(signal)
                                                    except Exception as e:
                                                        logger.error(f"Error in signal callback: {str(e)}")
                                                
                                                # Save to queue for execution
                                                self.executors[symbol].pending_signals.append(signal)
                                            
                                            # Update last signal time
                                            self.last_signal_time[symbol][timeframe] = signal_time
                                            logger.info(f"Generated signal for {symbol} {timeframe}: {latest_signal['type']}")
                                
                                last_check[symbol][timeframe] = current_time
                                
                            except Exception as e:
                                logger.error(f"Error generating signals for {symbol} {timeframe}: {str(e)}")
                
                # Sleep to avoid high CPU usage
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in signal generation worker: {str(e)}")
                time.sleep(5.0)  # Longer sleep on error
        
        logger.info("Signal generation worker stopped")
    
    def _execution_worker(self):
        """
        Worker thread for executing trades based on signals.
        """
        logger.info("Execution worker started")
        
        while self.running:
            try:
                # Check for pending signals in each executor
                for symbol, executor in self.executors.items():
                    # Process any pending signals
                    pending_signals = executor.get_pending_signals()
                    
                    for signal in pending_signals:
                        try:
                            # Get current market data for this symbol and timeframe
                            timeframe = signal.get('timeframe', '1h')
                            data = self.get_market_data(symbol, timeframe)
                            
                            if data is not None and not data.empty:
                                # Convert current data to the format TradeExecutor expects
                                timeframe_data = {timeframe: data.iloc[-1].to_dict()}
                                
                                # Process the signal
                                position = executor.process_signal(signal, timeframe_data)
                                
                                if position:
                                    # Place order with broker
                                    order = self._place_order_for_position(position, symbol)
                                    
                                    if order:
                                        # Update position with order info
                                        position['order_id'] = order.get('order_id')
                                        position['order_status'] = order.get('status')
                                        
                                        # Notify position callbacks
                                        for callback in self.position_callbacks:
                                            try:
                                                callback(position)
                                            except Exception as e:
                                                logger.error(f"Error in position callback: {str(e)}")
                                    
                                    logger.info(f"Executed signal for {symbol}: {position['direction']} at {position['entry_price']}")
                        
                        except Exception as e:
                            logger.error(f"Error processing signal for {symbol}: {str(e)}")
                
                # Check and update existing positions
                self._update_positions()
                
                # Sleep to avoid high CPU usage
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in execution worker: {str(e)}")
                time.sleep(5.0)  # Longer sleep on error
        
        logger.info("Execution worker stopped")
    
    def _place_order_for_position(self, position: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Place an order with the broker based on a position.
        
        Args:
            position: Position dictionary from TradeExecutor
            symbol: Trading symbol
            
        Returns:
            Order information or None if failed
        """
        try:
            # Extract order details from position
            direction = position['direction']
            side = 'buy' if direction == 'long' else 'sell'
            quantity = position['position_size']
            
            # Place the order
            order = self.broker.place_order(
                symbol=symbol,
                quantity=quantity,
                side=side,
                order_type='market'  # Use market orders for now
            )
            
            # Notify order callbacks
            for callback in self.order_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    logger.error(f"Error in order callback: {str(e)}")
            
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    def _update_positions(self):
        """
        Update existing positions with current market data and broker information.
        """
        try:
            # Get current positions from broker
            broker_positions = self.broker.get_positions()
            
            # Update each executor's positions
            for symbol, executor in self.executors.items():
                # Get current market data for this symbol
                data = {}
                for timeframe in self.timeframes:
                    tf_data = self.get_market_data(symbol, timeframe)
                    if tf_data is not None and not tf_data.empty:
                        data[timeframe] = tf_data.iloc[-1].to_dict()
                
                if data:
                    # Update executor's positions with latest market data
                    executor._manage_positions(data)
                    
                    # Match executor positions with broker positions
                    for position in executor.get_open_positions():
                        position_id = position.get('id')
                        order_id = position.get('order_id')
                        
                        # Find matching broker position
                        for broker_pos in broker_positions:
                            if broker_pos.get('symbol') == symbol and (
                                    broker_pos.get('id') == position_id or
                                    broker_pos.get('order_id') == order_id):
                                
                                # Update position with broker information
                                position['broker_position_id'] = broker_pos.get('id')
                                position['current_price'] = broker_pos.get('current_price')
                                position['market_value'] = broker_pos.get('market_value')
                                
                                # Check if position needs to be closed
                                if position.get('status') == 'closed' and broker_pos.get('status') != 'closed':
                                    self._close_broker_position(broker_pos, position['exit_price'], position['exit_reason'])
                                
                                # Notify position callbacks
                                for callback in self.position_callbacks:
                                    try:
                                        callback(position)
                                    except Exception as e:
                                        logger.error(f"Error in position callback: {str(e)}")
                                
                                break
                
        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
    
    def _close_broker_position(self, broker_position: Dict[str, Any], exit_price: float, reason: str) -> bool:
        """
        Close a position with the broker.
        
        Args:
            broker_position: Position from broker
            exit_price: Exit price
            reason: Reason for closing
            
        Returns:
            True if successful
        """
        try:
            position_id = broker_position.get('id')
            symbol = broker_position.get('symbol')
            direction = broker_position.get('direction')
            quantity = broker_position.get('quantity')
            
            # Determine side for closing order (opposite of position direction)
            close_side = 'sell' if direction == 'long' else 'buy'
            
            # Place closing order
            order = self.broker.place_order(
                symbol=symbol,
                quantity=quantity,
                side=close_side,
                order_type='market'  # Use market orders for closing
            )
            
            logger.info(f"Closed position {position_id} for {symbol} at market ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return False
    
    def _save_market_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """
        Save market data to disk.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            data: Market data DataFrame
        """
        try:
            file_path = self.data_dir / f"{symbol}_{timeframe}_live.csv"
            data.to_csv(file_path)
        except Exception as e:
            logger.error(f"Error saving market data: {str(e)}")
