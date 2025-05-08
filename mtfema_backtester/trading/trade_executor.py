"""
Trade execution handler for the Multi-Timeframe 9 EMA Strategy.

This module handles signal processing, position management, and trade execution
for the MT 9 EMA Extension Strategy.
"""

import logging
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Utility functions
def get_timeframe_minutes(timeframe: str) -> int:
    """Get timeframe in minutes, e.g. '1h' -> 60."""
    if not timeframe:
        return 0
        
    # Extract number and unit
    if timeframe[-1].isalpha():
        number = int(timeframe[:-1])
        unit = timeframe[-1].lower()
    else:
        return int(timeframe)  # Assume it's already in minutes
        
    # Convert to minutes
    if unit == 'm':
        return number
    elif unit == 'h':
        return number * 60
    elif unit == 'd':
        return number * 60 * 24
    elif unit == 'w':
        return number * 60 * 24 * 7
    else:
        raise ValueError(f"Unsupported timeframe unit: {unit}")

def get_next_timeframe_in_hierarchy(timeframe: str) -> Optional[str]:
    """Get the next timeframe in the hierarchy."""
    # Standard timeframe hierarchy
    hierarchy = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    
    try:
        idx = hierarchy.index(timeframe)
        if idx < len(hierarchy) - 1:
            return hierarchy[idx + 1]
    except ValueError:
        pass
    
    return None

# Simple performance monitor class
class PerformanceMonitor:
    """Simple performance monitoring class."""
    
    def __init__(self, name: str):
        self.name = name
        self.metrics = {}
        self.start_time = time.time()
    
    def register_metric(self, name: str, initial_value: Any = 0):
        """Register a new metric."""
        self.metrics[name] = initial_value
    
    def increment_metric(self, name: str, value: Any = 1):
        """Increment a metric."""
        if name not in self.metrics:
            self.metrics[name] = 0
        self.metrics[name] += value
    
    def set_metric(self, name: str, value: Any):
        """Set a metric value."""
        self.metrics[name] = value
    
    def get_metric(self, name: str) -> Any:
        """Get a metric value."""
        return self.metrics.get(name, 0)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return self.metrics
        
    def measure_performance(self, label: str):
        """Context manager for measuring execution time."""
        class MeasureContext:
            def __init__(self, monitor, label):
                self.monitor = monitor
                self.label = label
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                logger.debug(f"{self.label} took {elapsed:.4f} seconds")
                self.monitor.set_metric(f"{self.label}_time", elapsed)
                
        return MeasureContext(self, label)

logger = logging.getLogger(__name__)

class TradeExecutor:
    """
    Trade execution handler for the Multi-Timeframe 9 EMA Strategy.
    Manages signal generation, position sizing, and trade management.
    """
    
    def __init__(self, strategy: Optional[Any] = None, account_balance: float = 10000.0, risk_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the trade executor.
        
        Args:
            strategy: Strategy instance (optional)
            account_balance: Initial account balance
            risk_settings: Dictionary of risk management settings
        """
        self.strategy = strategy
        self.account_balance = account_balance
        self.risk_settings = risk_settings or {}
        self.open_positions = []
        self.closed_positions = []
        self.equity_curve = [(datetime.now(), account_balance)]
        self.monitor = PerformanceMonitor('trade_execution')
        
        # Initialize metrics
        self._init_metrics()
        
        logger.info(f"TradeExecutor initialized with balance: {account_balance}")
    
    def _init_metrics(self):
        """Initialize performance metrics."""
        self.monitor.register_metric('trade_count', 0)
        self.monitor.register_metric('win_count', 0)
        self.monitor.register_metric('loss_count', 0)
        self.monitor.register_metric('total_profit', 0.0)
        self.monitor.register_metric('total_loss', 0.0)
        self.monitor.register_metric('max_drawdown', 0.0)
        
    def process_update(self, timeframe_data: Dict[str, Dict]):
        """
        Process market updates across timeframes.
        
        Args:
            timeframe_data: Dictionary of market data by timeframe
        """
        with self.monitor.measure_performance('process_update'):
            # Update strategy with latest data if available
            signals = []
            if self.strategy is not None:
                try:
                    signals = self.strategy.update(timeframe_data)
                except Exception as e:
                    logger.error(f"Error updating strategy: {str(e)}")
            
            # Process any new signals
            if signals:
                self._process_signals(signals, timeframe_data)
            
            # Manage existing positions
            self._manage_positions(timeframe_data)
            
            # Update equity curve
            self._update_equity_curve()
    
    def process_signal(self, signal: Dict, timeframe_data: Optional[Dict[str, Dict]] = None):
        """
        Process a single trading signal.
        
        Args:
            signal: Trading signal dictionary
            timeframe_data: Optional current market data by timeframe
        
        Returns:
            Dict: Created position or None if trade couldn't be taken
        """
        # Check if we can take this trade (max trades, etc.)
        if not self._can_take_trade(signal):
            logger.info(f"Skipping {signal['direction']} signal on {signal['timeframe']} due to trade limits")
            return None
        
        # Calculate position size
        position_size, risk_amount = self._calculate_position_size(
            signal['entry_price'], 
            signal['stop_price'],
            signal.get('risk_factor', 1.0)
        )
        
        # Create and open the position
        position = self._create_position(signal, position_size, risk_amount)
        
        # Add to open positions
        self.open_positions.append(position)
        
        # Manage position with current market data if provided
        if timeframe_data:
            self._manage_positions(timeframe_data)
            self._update_equity_curve()
            
        return position

    def _process_signals(self, signals: List[Dict], timeframe_data: Dict[str, Dict]):
        """
        Process new trading signals.
        
        Args:
            signals: List of signal dictionaries
            timeframe_data: Current market data by timeframe
        """
        for signal in signals:
            self.process_signal(signal, timeframe_data)
            
            # Update metrics
            self.monitor.increment_metric('trade_count')
            
            logger.info(f"Opened {signal['direction']} position of {position_size} units on {signal['timeframe']} at {signal['entry_price']}")
    
    def _can_take_trade(self, signal: Dict) -> bool:
        """
        Check if we can take a new trade.
        
        Args:
            signal: Trading signal dictionary
            
        Returns:
            bool: True if we can take the trade
        """
        # Get maximum allowed trades
        max_trades = self.risk_settings.get('max_concurrent_trades', 3)
        
        # Check if we're already at max trades
        if len(self.open_positions) >= max_trades:
            return False
        
        # Check if we already have a trade in this timeframe
        for position in self.open_positions:
            if position['timeframe'] == signal['timeframe']:
                return False
        
        # Check if we have a conflicting trade
        # (e.g., don't want to be long and short at the same time)
        if self.open_positions:
            for position in self.open_positions:
                if position['direction'] != signal['direction']:
                    # Check if we allow mixed directions
                    if not self.risk_settings.get('allow_mixed_directions', False):
                        return False
        
        return True
    
    def _calculate_position_size(self, entry_price: float, stop_price: float, 
                                risk_factor: float = 1.0) -> Tuple[float, float]:
        """
        Calculate position size based on risk parameters.
        
        Args:
            entry_price: Entry price
            stop_price: Stop loss price
            risk_factor: Risk adjustment factor (0.0-1.0)
            
        Returns:
            Tuple of (position_size, risk_amount)
        """
        # Get risk percentage from settings
        risk_pct = self.risk_settings.get('account_risk_percent', 1.0) / 100.0
        
        # Adjust risk based on factor
        adjusted_risk_pct = risk_pct * risk_factor
        
        # Calculate risk amount
        risk_amount = self.account_balance * adjusted_risk_pct
        
        # Calculate stop distance
        stop_distance = abs(entry_price - stop_price)
        
        if stop_distance <= 0:
            logger.warning(f"Invalid stop distance: {stop_distance}")
            return 0.0, 0.0
        
        # Calculate position size
        position_size = risk_amount / stop_distance
        
        # Apply position size limits
        max_position_pct = self.risk_settings.get('max_position_size_percent', 20.0) / 100.0
        max_position_size = (self.account_balance * max_position_pct) / entry_price
        
        position_size = min(position_size, max_position_size)
        
        # Recalculate actual risk amount based on position size
        actual_risk = position_size * stop_distance
        
        return position_size, actual_risk
    
    def _create_position(self, signal: Dict, position_size: float, risk_amount: float) -> Dict:
        """
        Create a new position from a signal.
        
        Args:
            signal: Trading signal dictionary
            position_size: Calculated position size
            risk_amount: Amount of money at risk
            
        Returns:
            Dict: Position dictionary
        """
        # Create position object
        position = {
            'id': f"{len(self.open_positions) + len(self.closed_positions) + 1}",
            'timeframe': signal['timeframe'],
            'direction': signal['direction'],
            'entry_time': signal['entry_time'],
            'entry_price': signal['entry_price'],
            'position_size': position_size,
            'stop_price': signal['stop_price'],
            'initial_stop': signal['stop_price'],  # Keep track of initial stop
            'target_price': signal['target_price'],
            'target_timeframe': signal.get('target_timeframe'),
            'risk_amount': risk_amount,
            'current_price': signal['entry_price'],
            'current_value': position_size * signal['entry_price'],
            'status': 'open',
            'exit_time': None,
            'exit_price': None,
            'exit_reason': None,
            'profit_loss': 0.0,
            'profit_loss_pct': 0.0,
            'targets_hit': [],  # Track progression through timeframes
            'max_favorable_excursion': 0.0,  # Track maximum favorable price movement
            'max_adverse_excursion': 0.0,    # Track maximum adverse price movement
        }
        
        return position
        
    def _manage_positions(self, timeframe_data: Dict[str, Dict]):
        """
        Manage existing positions.
        
        Args:
            timeframe_data: Current market data by timeframe
        """
        # Keep track of positions to remove from open_positions
        positions_to_close = []
        
        for position in self.open_positions:
            tf = position['timeframe']
            
            # Skip if no data for this timeframe
            if tf not in timeframe_data:
                continue
                
            # Get current price data
            current_data = timeframe_data[tf]
            high_price = current_data.get('high', current_data.get('close'))
            low_price = current_data.get('low', current_data.get('close'))
            close_price = current_data.get('close')
            
            # Update position's current price and value
            position['current_price'] = close_price
            position['current_value'] = position['position_size'] * close_price
            
            # Calculate current P&L
            self._update_position_pnl(position)
            
            # Check for stop loss hit
            if self._check_stop_hit(position, low_price, high_price):
                # Close the position
                self._close_position(position, position['stop_price'], 'stop_loss', current_data.get('timestamp', datetime.now()))
                positions_to_close.append(position)
                continue
            
            # Check for target hit
            if self._check_target_hit(position, low_price, high_price):
                if position.get('target_timeframe') and self.risk_settings.get('use_progressive_targeting', True):
                    # Record target hit and progress to next timeframe
                    self._progress_position_target(position, timeframe_data)
                else:
                    # Close position at target
                    self._close_position(position, position['target_price'], 'target_hit', current_data.get('timestamp', datetime.now()))
                    positions_to_close.append(position)
                    continue
            
            # Update MAE/MFE
            self._update_position_excursions(position, low_price, high_price)
            
            # Update trailing stop if enabled
            if self.risk_settings.get('use_trailing_stop', False):
                self._update_trailing_stop(position)
        
        # Remove closed positions from open_positions
        for position in positions_to_close:
            self.open_positions.remove(position)
            self.closed_positions.append(position)
    
    def _update_position_pnl(self, position: Dict):
        """
        Update position's profit/loss values.
        
        Args:
            position: Position dictionary to update
        """
        entry_price = position['entry_price']
        current_price = position['current_price']
        position_size = position['position_size']
        
        # Calculate P&L based on direction
        if position['direction'] == 'LONG':
            profit_loss = (current_price - entry_price) * position_size
        else:  # SHORT
            profit_loss = (entry_price - current_price) * position_size
        
        position['profit_loss'] = profit_loss
        position['profit_loss_pct'] = profit_loss / (entry_price * position_size) if (entry_price * position_size) != 0 else 0.0
    
    def _check_stop_hit(self, position: Dict, low_price: float, high_price: float) -> bool:
        """
        Check if stop loss has been hit.
        
        Args:
            position: Position dictionary
            low_price: Current bar's low price
            high_price: Current bar's high price
            
        Returns:
            bool: True if stop was hit
        """
        if position['direction'] == 'LONG':
            return low_price <= position['stop_price']
        else:  # SHORT
            return high_price >= position['stop_price']
    
    def _check_target_hit(self, position: Dict, low_price: float, high_price: float) -> bool:
        """
        Check if target has been hit.
        
        Args:
            position: Position dictionary
            low_price: Current bar's low price
            high_price: Current bar's high price
            
        Returns:
            bool: True if target was hit
        """
        if position['direction'] == 'LONG':
            return high_price >= position['target_price']
        else:  # SHORT
            return low_price <= position['target_price']
    
    def _update_position_excursions(self, position: Dict, low_price: float, high_price: float):
        """
        Update maximum favorable and adverse excursions.
        
        Args:
            position: Position dictionary
            low_price: Current bar's low price
            high_price: Current bar's high price
        """
        entry_price = position['entry_price']
        position_size = position['position_size']
        
        if position['direction'] == 'LONG':
            # For long positions
            favorable_price = high_price
            adverse_price = low_price
            
            favorable_excursion = (favorable_price - entry_price) * position_size
            adverse_excursion = (adverse_price - entry_price) * position_size
        else:
            # For short positions
            favorable_price = low_price
            adverse_price = high_price
            
            favorable_excursion = (entry_price - favorable_price) * position_size
            adverse_excursion = (entry_price - adverse_price) * position_size
        
        # Update MFE if needed
        if favorable_excursion > position.get('max_favorable_excursion', 0.0):
            position['max_favorable_excursion'] = favorable_excursion
        
        # Update MAE if needed (note: MAE is typically negative)
        if adverse_excursion < position.get('max_adverse_excursion', 0.0):
            position['max_adverse_excursion'] = adverse_excursion
    
    def _progress_position_target(self, position: Dict, timeframe_data: Dict[str, Dict]):
        """
        Progress position to next target in timeframe hierarchy.
        
        Args:
            position: Position dictionary
            timeframe_data: Current market data by timeframe
        """
        current_tf = position['timeframe']
        next_tf = position.get('target_timeframe')
        
        if not next_tf:
            return
        
        # Record the current target hit
        target_hit = {
            'timeframe': current_tf,
            'price': position['target_price'],
            'time': datetime.now(),  # Should be updated from data timestamp
        }
        
        position['targets_hit'].append(target_hit)
        logger.info(f"Position {position['id']} hit target for {current_tf} at {position['target_price']}")
        
        # Update to next timeframe in hierarchy
        position['timeframe'] = next_tf
        
        # Find the next timeframe in hierarchy
        next_target_tf = get_next_timeframe_in_hierarchy(next_tf)
        position['target_timeframe'] = next_target_tf
        
        # Set new target price from next timeframe's EMA
        if next_target_tf and next_target_tf in timeframe_data:
            indicators = None
            if self.strategy is not None and hasattr(self.strategy, 'get_indicators'):
                try:
                    indicators = self.strategy.get_indicators()
                except Exception as e:
                    logger.error(f"Error getting indicators: {str(e)}")
            
            if indicators and next_target_tf in indicators and 'ema' in indicators[next_target_tf]:
                # Use next timeframe's EMA as target
                ema_value = indicators[next_target_tf]['ema'][-1]
                position['target_price'] = ema_value
                logger.info(f"New target set at {ema_value} for {next_target_tf}")
            else:
                # If EMA not available, adjust target based on reward-risk ratio
                self._set_default_target(position)
        else:
            # Final target in hierarchy or no data available
            self._set_default_target(position)
        
        # Update stop loss to protect profits
        self._update_stop_after_target_hit(position)
    
    def _set_default_target(self, position: Dict):
        """
        Set default target based on reward-risk ratio.
        
        Args:
            position: Position dictionary
        """
        # Get reward-risk ratio from settings
        rr_ratio = self.risk_settings.get('reward_risk_ratio', 2.0)
        
        # Calculate initial risk
        initial_risk = abs(position['entry_price'] - position['initial_stop'])
        
        # Set target based on risk ratio
        if position['direction'] == 'LONG':
            position['target_price'] = position['entry_price'] + (initial_risk * rr_ratio)
        else:  # SHORT
            position['target_price'] = position['entry_price'] - (initial_risk * rr_ratio)
        
        logger.info(f"Set default target at {position['target_price']} with {rr_ratio}:1 reward-risk ratio")
    
    def _update_stop_after_target_hit(self, position: Dict):
        """
        Update stop loss after hitting a target.
        
        Args:
            position: Position dictionary
        """
        # Get stop policy from settings
        stop_policy = self.risk_settings.get('target_hit_stop_policy', 'breakeven')
        
        if stop_policy == 'breakeven':
            # Move stop to breakeven
            position['stop_price'] = position['entry_price']
            logger.info(f"Moved stop to breakeven at {position['entry_price']}")
        
        elif stop_policy == 'previous_target':
            # Move stop to previous target level
            if position['targets_hit']:
                prev_target = position['targets_hit'][-1]['price']
                
                # Add a small buffer
                buffer = 0.001  # 0.1%
                if position['direction'] == 'LONG':
                    position['stop_price'] = prev_target * (1 - buffer)
                else:  # SHORT
                    position['stop_price'] = prev_target * (1 + buffer)
                
                logger.info(f"Moved stop to previous target at {position['stop_price']}")
            else:
                # Fallback to breakeven
                position['stop_price'] = position['entry_price']
        
        elif stop_policy == 'trailing':
            # Set a trailing stop based on ATR or fixed percentage
            self._update_trailing_stop(position)
    
    def _update_trailing_stop(self, position: Dict):
        """
        Update trailing stop price.
        
        Args:
            position: Position dictionary
        """
        # Only trail if in profit
        if (position['direction'] == 'LONG' and position['current_price'] > position['entry_price']) or \
           (position['direction'] == 'SHORT' and position['current_price'] < position['entry_price']):
            
            # Get trailing stop parameters
            atr_multiple = self.risk_settings.get('trailing_stop_atr_multiple', 2.0)
            min_distance_pct = self.risk_settings.get('trailing_stop_min_distance', 0.5) / 100.0
            
            # Get ATR if available (ideally from strategy indicators)
            atr_value = None
            indicators = self.strategy.get_indicators()
            tf = position['timeframe']
            if tf in indicators and 'atr' in indicators[tf]:
                atr_value = indicators[tf]['atr'][-1]
            
            # Calculate new stop price
            if position['direction'] == 'LONG':
                if atr_value:
                    # ATR-based trailing stop
                    new_stop = position['current_price'] - (atr_value * atr_multiple)
                else:
                    # Percentage-based trailing stop
                    new_stop = position['current_price'] * (1 - min_distance_pct)
                
                # Only move stop up, never down
                if new_stop > position['stop_price']:
                    position['stop_price'] = new_stop
                    logger.debug(f"Updated trailing stop to {new_stop}")
            
            else:  # SHORT
                if atr_value:
                    # ATR-based trailing stop
                    new_stop = position['current_price'] + (atr_value * atr_multiple)
                else:
                    # Percentage-based trailing stop
                    new_stop = position['current_price'] * (1 + min_distance_pct)
                
                # Only move stop down, never up
                if new_stop < position['stop_price']:
                    position['stop_price'] = new_stop
                    logger.debug(f"Updated trailing stop to {new_stop}")
    
    def _close_position(self, position: Dict, exit_price: float, reason: str, exit_time: datetime):
        """
        Close a position and update statistics.
        
        Args:
            position: Position dictionary
            exit_price: Exit price
            reason: Reason for closing
            exit_time: Exit timestamp
        """
        # Store exit details
        position['exit_price'] = exit_price
        position['exit_reason'] = reason
        position['exit_time'] = exit_time
        position['status'] = 'closed'
        
        # Calculate final P&L
        entry_price = position['entry_price']
        position_size = position['position_size']
        
        if position['direction'] == 'LONG':
            profit_loss = (exit_price - entry_price) * position_size
        else:  # SHORT
            profit_loss = (entry_price - exit_price) * position_size
        
        position['profit_loss'] = profit_loss
        position['profit_loss_pct'] = profit_loss / (entry_price * position_size) if (entry_price * position_size) != 0 else 0.0
        
        # Update account balance
        self.account_balance += profit_loss
        
        # Update metrics
        if profit_loss > 0:
            self.monitor.increment_metric('win_count')
            self.monitor.increment_metric('total_profit', profit_loss)
        else:
            self.monitor.increment_metric('loss_count')
            self.monitor.increment_metric('total_loss', abs(profit_loss))
        
        logger.info(f"Closed {position['direction']} position on {position['timeframe']} " 
                    f"at {exit_price} with P&L: {profit_loss:.2f} ({position['profit_loss_pct']:.2%})")
    
    def _update_equity_curve(self):
        """Update the equity curve with current account balance."""
        self.equity_curve.append((datetime.now(), self.account_balance))
        
        # Calculate drawdown
        peak = max(balance for _, balance in self.equity_curve)
        current = self.account_balance
        drawdown = (peak - current) / peak if peak > 0 else 0.0
        
        # Update max drawdown if needed
        current_max_dd = self.monitor.get_metric('max_drawdown')
        if drawdown > current_max_dd:
            self.monitor.set_metric('max_drawdown', drawdown)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get all performance metrics.
        
        Returns:
            Dict: Performance metrics
        """
        metrics = self.monitor.get_metrics()
        
        # Calculate additional metrics
        win_count = metrics.get('win_count', 0)
        loss_count = metrics.get('loss_count', 0)
        total_trades = win_count + loss_count
        
        if total_trades > 0:
            metrics['win_rate'] = win_count / total_trades
        else:
            metrics['win_rate'] = 0.0
            
        total_profit = metrics.get('total_profit', 0.0)
        total_loss = metrics.get('total_loss', 0.0)
        
        if total_loss > 0:
            metrics['profit_factor'] = total_profit / total_loss
        else:
            metrics['profit_factor'] = float('inf') if total_profit > 0 else 0.0
        
        # Account metrics
        metrics['current_balance'] = self.account_balance
        
        return metrics
    
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List: Open positions
        """
        return self.open_positions
    
    def get_closed_positions(self) -> List[Dict]:
        """
        Get all closed positions.
        
        Returns:
            List: Closed positions
        """
        return self.closed_positions
    
    def get_equity_curve(self) -> List[Tuple[datetime, float]]:
        """
        Get equity curve data.
        
        Returns:
            List: Equity curve as (timestamp, balance) tuples
        """
        return self.equity_curve
