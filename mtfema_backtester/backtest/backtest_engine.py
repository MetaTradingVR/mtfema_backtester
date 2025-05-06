"""
Backtesting Engine for the Multi-Timeframe 9 EMA Extension Strategy

This module provides a comprehensive backtesting framework for evaluating 
the Multi-Timeframe 9 EMA Extension Strategy across different instruments 
and market conditions.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from tqdm import tqdm
from copy import deepcopy

from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.strategy.extension_detector import detect_extensions
from mtfema_backtester.strategy.reclamation_detector import detect_reclamations
from mtfema_backtester.strategy.pullback_validator import validate_pullback
from mtfema_backtester.strategy.target_manager import get_target_for_signal
from mtfema_backtester.strategy.conflict_resolver import validate_signal_context
from mtfema_backtester.strategy.signal_generator import generate_signals
from mtfema_backtester.backtest.position import Position
from mtfema_backtester.backtest.trade import Trade
from mtfema_backtester.config import RISK_PARAMS, BACKTEST_CONFIG

logger = logging.getLogger('mtfema_backtester.backtest_engine')

class BacktestEngine:
    """
    Backtesting engine for the Multi-Timeframe 9 EMA Extension Strategy
    """
    
    def __init__(
        self, 
        timeframe_data,
        initial_capital=BACKTEST_CONFIG['initial_capital'],
        commission=BACKTEST_CONFIG['commission'],
        slippage=BACKTEST_CONFIG['slippage'],
        execution_delay=BACKTEST_CONFIG['execution_delay'],
        enable_fractional_shares=BACKTEST_CONFIG['enable_fractional_shares']
    ):
        """
        Initialize the backtesting engine
        
        Parameters:
        -----------
        timeframe_data : TimeframeData
            Multi-timeframe data for backtesting
        initial_capital : float
            Initial account balance
        commission : float
            Commission per trade (percentage)
        slippage : float
            Slippage per trade (percentage)
        execution_delay : int
            Execution delay in bars
        enable_fractional_shares : bool
            Whether to allow fractional share positions
        """
        # Validate input
        if not isinstance(timeframe_data, TimeframeData):
            raise TypeError("timeframe_data must be a TimeframeData instance")
        
        # Store parameters
        self.tf_data = timeframe_data
        self.timeframes = self.tf_data.get_available_timeframes()
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.execution_delay = execution_delay
        self.enable_fractional_shares = enable_fractional_shares
        
        # Initialize state variables
        self.reset()
        
        logger.info(f"BacktestEngine initialized with {len(self.timeframes)} timeframes: {self.timeframes}")
    
    def reset(self):
        """Reset the backtest engine to initial state"""
        # Account state
        self.equity = [self.initial_capital]
        self.balance = self.initial_capital
        self.margin_used = 0
        
        # Trade tracking
        self.positions = []
        self.open_positions = []
        self.closed_positions = []
        self.trades = []
        
        # Current state
        self.current_bar = {}
        for tf in self.timeframes:
            self.current_bar[tf] = 0
        
        # Performance metrics
        self.metrics = {}
        
        logger.info("BacktestEngine reset to initial state")
    
    def run(self, sync_timeframes=True):
        """
        Run the complete backtest
        
        Parameters:
        -----------
        sync_timeframes : bool
            Whether to synchronize timeframes (ensure they align)
            
        Returns:
        --------
        dict
            Backtest results and performance metrics
        """
        logger.info("Starting backtest run")
        
        # Reset to initial state
        self.reset()
        
        # Synchronize timeframes if requested
        if sync_timeframes:
            logger.info("Synchronizing timeframes...")
            self.tf_data.synchronize_timeframes()
        
        # Get the reference timeframe (smallest timeframe)
        ref_tf = min(self.timeframes, key=lambda x: self.tf_data.get_timeframe_minutes(x))
        ref_data = self.tf_data.get_timeframe(ref_tf)
        total_bars = len(ref_data)
        
        logger.info(f"Reference timeframe: {ref_tf} with {total_bars} bars")
        
        # Main backtesting loop
        for i in tqdm(range(total_bars), desc="Backtesting progress"):
            # Update current state for each timeframe
            for tf in self.timeframes:
                # Map reference timeframe index to this timeframe
                tf_idx = self.tf_data.map_index_between_timeframes(ref_tf, i, tf)
                if tf_idx >= 0:
                    self.current_bar[tf] = tf_idx
            
            # Process current bar for all timeframes
            self._process_bar()
            
            # Update account equity
            self.equity.append(self._calculate_equity())
        
        # Close any remaining positions
        self._close_all_positions()
        
        # Calculate performance metrics
        self._calculate_metrics()
        
        logger.info(f"Backtest completed with {len(self.trades)} trades")
        logger.info(f"Final equity: ${self.equity[-1]:.2f}")
        
        return {
            'equity_curve': self.equity,
            'trades': self.trades,
            'metrics': self.metrics
        }
    
    def _process_bar(self):
        """Process the current bar across all timeframes"""
        # Update open positions
        self._update_positions()
        
        # Generate trading signals
        signals = self._generate_signals()
        
        # Execute signals
        for signal in signals:
            self._execute_signal(signal)
    
    def _update_positions(self):
        """Update all open positions"""
        for pos in self.open_positions:
            # Check if position should be closed
            if self._should_close_position(pos):
                self._close_position(pos)
                continue
            
            # Update stop loss (trailing stop)
            if RISK_PARAMS['trailing_stop']['enabled']:
                self._update_trailing_stop(pos)
            
            # Update position target
            self._update_position_target(pos)
    
    def _generate_signals(self):
        """
        Generate trading signals based on the strategy
        
        Returns:
        --------
        list
            List of signal dictionaries
        """
        # Use the signal generator to generate signals
        signals = generate_signals(self.tf_data)
        
        # Convert the signals to the expected format
        formatted_signals = []
        
        for signal in signals:
            if signal.get('valid', False):
                formatted_signal = {
                    'timeframe': signal['timeframe'],
                    'direction': signal['direction'],
                    'price': signal['price'],
                    'time': signal['time'],
                    'confidence': signal.get('confidence', 'medium'),
                    'target': signal.get('target', {}).get('target_price'),
                    'target_timeframe': signal.get('target', {}).get('target_timeframe')
                }
                
                formatted_signals.append(formatted_signal)
        
        return formatted_signals
    
    def _validate_signal(self, timeframe, direction, extensions):
        """
        Validate a signal against higher timeframe context
        
        Parameters:
        -----------
        timeframe : str
            Timeframe of the signal
        direction : str
            Direction of the signal ('long' or 'short')
        extensions : dict
            Dictionary of extension data for all timeframes
            
        Returns:
        --------
        bool
            Whether the signal is valid
        """
        # Get timeframe hierarchy (smallest to largest)
        tf_hierarchy = sorted(
            self.timeframes,
            key=lambda x: self.tf_data.get_timeframe_minutes(x)
        )
        
        # Find position of current timeframe in hierarchy
        tf_idx = tf_hierarchy.index(timeframe)
        
        # Check higher timeframes (if any)
        higher_tfs = tf_hierarchy[tf_idx+1:] if tf_idx < len(tf_hierarchy) - 1 else []
        
        # If no higher timeframes, signal is valid
        if not higher_tfs:
            return True
        
        # Count how many higher timeframes have aligned extensions
        aligned_count = 0
        for htf in higher_tfs:
            htf_ext = extensions.get(htf, {})
            
            # Check if higher timeframe has extension in same direction
            if direction == 'long' and htf_ext.get('extended_down', False):
                aligned_count += 1
            elif direction == 'short' and htf_ext.get('extended_up', False):
                aligned_count += 1
        
        # Signal is valid if we have enough aligned higher timeframes
        min_agreement = max(1, len(higher_tfs) // 2)  # At least half of higher timeframes
        return aligned_count >= min_agreement
    
    def _execute_signal(self, signal):
        """
        Execute a trading signal by opening a position
        
        Parameters:
        -----------
        signal : dict
            Signal information
        """
        # Calculate position size
        size = self._calculate_position_size(signal)
        
        # Calculate stop loss level
        stop_level = self._calculate_stop_level(signal)
        
        # Calculate target level
        target_level = self._calculate_target_level(signal)
        
        # Create and open the position
        position = Position(
            symbol=self.tf_data.get_symbol(),
            direction=signal['direction'],
            entry_price=signal['price'],
            entry_time=signal['time'],
            size=size,
            stop_loss=stop_level,
            take_profit=target_level,
            timeframe=signal['timeframe']
        )
        
        # Add slippage to entry
        if signal['direction'] == 'long':
            position.entry_price *= (1 + self.slippage)
        else:
            position.entry_price *= (1 - self.slippage)
        
        # Add position to open positions
        self.open_positions.append(position)
        self.positions.append(position)
        
        # Update account state
        self.balance -= self._calculate_commission(position.entry_price * position.size)
        
        logger.info(f"Opened {signal['direction']} position of {size} shares at ${signal['price']:.2f}")
    
    def _close_position(self, position):
        """
        Close an open position
        
        Parameters:
        -----------
        position : Position
            Position to close
        """
        # Get current price for the position's timeframe
        tf = position.timeframe
        idx = self.current_bar[tf]
        data = self.tf_data.get_timeframe(tf)
        close_price = data.iloc[idx]['Close']
        
        # Add slippage to exit
        if position.direction == 'long':
            close_price *= (1 - self.slippage)
        else:
            close_price *= (1 + self.slippage)
        
        # Close the position
        position.close(
            exit_price=close_price,
            exit_time=data.iloc[idx]['Time'] if 'Time' in data.columns else data.index[idx]
        )
        
        # Create trade record
        trade = Trade.from_position(position)
        self.trades.append(trade)
        
        # Update account state
        self.balance += (position.exit_price * position.size) - self._calculate_commission(position.exit_price * position.size)
        
        # Move position from open to closed
        self.open_positions.remove(position)
        self.closed_positions.append(position)
        
        logger.info(f"Closed {position.direction} position at ${close_price:.2f}, P&L: ${position.realized_pnl:.2f}")
    
    def _close_all_positions(self):
        """Close all open positions"""
        positions_to_close = self.open_positions.copy()
        for position in positions_to_close:
            self._close_position(position)
    
    def _should_close_position(self, position):
        """
        Determine if a position should be closed
        
        Parameters:
        -----------
        position : Position
            Position to evaluate
            
        Returns:
        --------
        bool
            Whether the position should be closed
        """
        # Get current price data for the position's timeframe
        tf = position.timeframe
        idx = self.current_bar[tf]
        data = self.tf_data.get_timeframe(tf)
        current_bar = data.iloc[idx]
        
        # Check stop loss
        if position.direction == 'long' and current_bar['Low'] <= position.stop_loss:
            return True
        if position.direction == 'short' and current_bar['High'] >= position.stop_loss:
            return True
        
        # Check take profit
        if position.direction == 'long' and current_bar['High'] >= position.take_profit:
            return True
        if position.direction == 'short' and current_bar['Low'] <= position.take_profit:
            return True
        
        # Check if we have a reversal signal
        # (TODO: Implement more complex exit conditions based on strategy)
        
        return False
    
    def _update_trailing_stop(self, position):
        """
        Update trailing stop for a position
        
        Parameters:
        -----------
        position : Position
            Position to update
        """
        # Only update trailing stop if activated
        if not position.trailing_activated:
            # Calculate current R multiple
            r_multiple = position.current_r_multiple()
            
            # Activate trailing stop if R multiple exceeds threshold
            if r_multiple >= RISK_PARAMS['trailing_stop']['activation']:
                position.trailing_activated = True
                logger.debug(f"Activated trailing stop at {r_multiple:.2f}R")
        
        # Update trailing stop if activated
        if position.trailing_activated:
            # Get current price data for the position's timeframe
            tf = position.timeframe
            idx = self.current_bar[tf]
            data = self.tf_data.get_timeframe(tf)
            current_bar = data.iloc[idx]
            
            # Calculate new stop level
            if position.direction == 'long':
                trailing_level = current_bar['High'] * (1 - RISK_PARAMS['trailing_stop']['step'])
                if trailing_level > position.stop_loss:
                    position.stop_loss = trailing_level
                    logger.debug(f"Updated trailing stop to ${trailing_level:.2f}")
            else:
                trailing_level = current_bar['Low'] * (1 + RISK_PARAMS['trailing_stop']['step'])
                if trailing_level < position.stop_loss:
                    position.stop_loss = trailing_level
                    logger.debug(f"Updated trailing stop to ${trailing_level:.2f}")
    
    def _update_position_target(self, position):
        """
        Update position target based on progressive targeting framework
        
        Parameters:
        -----------
        position : Position
            Position to update
        """
        # Get current price for the position's timeframe
        tf = position.timeframe
        idx = self.current_bar[tf]
        data = self.tf_data.get_timeframe(tf)
        current_price = data.iloc[idx]['Close']
        
        # Check if price is approaching current target
        distance_to_target = abs(current_price - position.take_profit)
        current_atr = self._calculate_atr(tf, idx, 14)  # 14-period ATR
        
        # If price is close to target (within 0.5 ATR), consider updating
        if distance_to_target <= current_atr * 0.5:
            # Get next timeframe in hierarchy
            next_tf = self._get_next_timeframe(tf)
            
            # If there is a next timeframe, update target
            if next_tf:
                # Check if extension exists in next timeframe
                next_tf_idx = self.current_bar[next_tf]
                next_tf_data = self.tf_data.get_timeframe(next_tf)
                
                # Get 9 EMA for next timeframe
                if 'EMA_9' in next_tf_data.columns:
                    next_ema = next_tf_data.iloc[next_tf_idx]['EMA_9']
                    
                    # Update target to next timeframe's 9 EMA
                    position.take_profit = next_ema
                    position.target_timeframe = next_tf
                    
                    logger.info(f"Updated target to {next_tf} 9 EMA at ${next_ema:.2f}")
    
    def _get_next_timeframe(self, current_tf):
        """
        Get the next timeframe in the hierarchy
        
        Parameters:
        -----------
        current_tf : str
            Current timeframe
            
        Returns:
        --------
        str or None
            Next timeframe or None if current is the highest
        """
        # Get timeframe hierarchy (smallest to largest)
        tf_hierarchy = sorted(
            self.timeframes,
            key=lambda x: self.tf_data.get_timeframe_minutes(x)
        )
        
        # Find position of current timeframe in hierarchy
        tf_idx = tf_hierarchy.index(current_tf)
        
        # Return next timeframe if available
        return tf_hierarchy[tf_idx+1] if tf_idx < len(tf_hierarchy) - 1 else None
    
    def _calculate_position_size(self, signal):
        """
        Calculate position size based on risk management rules
        
        Parameters:
        -----------
        signal : dict
            Signal information
            
        Returns:
        --------
        float
            Position size in shares/contracts
        """
        # Get stop loss level
        stop_level = self._calculate_stop_level(signal)
        
        # Calculate risk amount
        risk_percent = RISK_PARAMS['max_risk_per_trade']
        risk_amount = self.balance * (risk_percent / 100.0)
        
        # Calculate dollar risk per share
        entry_price = signal['price']
        risk_per_share = abs(entry_price - stop_level)
        
        # Calculate position size
        size = risk_amount / risk_per_share
        
        # Round to whole shares if fractional shares not enabled
        if not self.enable_fractional_shares:
            size = np.floor(size)
        
        # Ensure at least 1 share
        size = max(1, size)
        
        return size
    
    def _calculate_stop_level(self, signal):
        """
        Calculate stop loss level for a signal
        
        Parameters:
        -----------
        signal : dict
            Signal information
            
        Returns:
        --------
        float
            Stop loss price level
        """
        # Get ATR for the signal's timeframe
        tf = signal['timeframe']
        idx = self.current_bar[tf]
        atr = self._calculate_atr(tf, idx, 14)  # 14-period ATR
        
        # Calculate stop loss based on ATR
        if signal['direction'] == 'long':
            return signal['price'] * (1 - atr / signal['price'] * 2)  # 2 ATR for long stops
        else:
            return signal['price'] * (1 + atr / signal['price'] * 2)  # 2 ATR for short stops
    
    def _calculate_target_level(self, signal):
        """
        Calculate initial target level for a signal
        
        Parameters:
        -----------
        signal : dict
            Signal information
            
        Returns:
        --------
        float
            Target price level
        """
        # Get the next timeframe in hierarchy
        tf = signal['timeframe']
        next_tf = self._get_next_timeframe(tf)
        
        if next_tf:
            # Get 9 EMA for next timeframe
            next_tf_idx = self.current_bar[next_tf]
            next_tf_data = self.tf_data.get_timeframe(next_tf)
            
            if 'EMA_9' in next_tf_data.columns:
                # Use next timeframe's 9 EMA as target
                target = next_tf_data.iloc[next_tf_idx]['EMA_9']
            else:
                # Fallback: use R multiple
                stop_level = self._calculate_stop_level(signal)
                risk = abs(signal['price'] - stop_level)
                target = signal['price'] + (risk * RISK_PARAMS['target_risk_reward'] * (1 if signal['direction'] == 'long' else -1))
        else:
            # Use R multiple for highest timeframe
            stop_level = self._calculate_stop_level(signal)
            risk = abs(signal['price'] - stop_level)
            target = signal['price'] + (risk * RISK_PARAMS['target_risk_reward'] * (1 if signal['direction'] == 'long' else -1))
        
        return target
    
    def _calculate_atr(self, timeframe, index, period=14):
        """
        Calculate Average True Range (ATR)
        
        Parameters:
        -----------
        timeframe : str
            Timeframe to calculate ATR for
        index : int
            Current index in the timeframe
        period : int
            ATR period
            
        Returns:
        --------
        float
            ATR value
        """
        # Get data for timeframe
        data = self.tf_data.get_timeframe(timeframe)
        
        # Ensure we have enough data
        if index < period:
            # Not enough data, use a default percentage of price
            return data.iloc[index]['Close'] * 0.01
        
        # Calculate true range
        tr = pd.DataFrame(index=data.index)
        tr['high'] = data['High']
        tr['low'] = data['Low']
        tr['close'] = data['Close'].shift(1)
        
        tr['tr1'] = tr['high'] - tr['low']
        tr['tr2'] = abs(tr['high'] - tr['close'])
        tr['tr3'] = abs(tr['low'] - tr['close'])
        
        tr['tr'] = tr[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate ATR
        atr = tr['tr'].rolling(window=period).mean().iloc[index]
        
        return atr if not np.isnan(atr) else data.iloc[index]['Close'] * 0.01
    
    def _calculate_commission(self, trade_value):
        """
        Calculate commission for a trade
        
        Parameters:
        -----------
        trade_value : float
            Trade value
            
        Returns:
        --------
        float
            Commission amount
        """
        return trade_value * self.commission
    
    def _calculate_equity(self):
        """
        Calculate current equity
        
        Returns:
        --------
        float
            Current equity value
        """
        # Start with cash balance
        equity = self.balance
        
        # Add unrealized P&L from open positions
        for pos in self.open_positions:
            # Get current price for position's timeframe
            tf = pos.timeframe
            idx = self.current_bar[tf]
            data = self.tf_data.get_timeframe(tf)
            current_price = data.iloc[idx]['Close']
            
            # Calculate unrealized P&L
            if pos.direction == 'long':
                unrealized_pnl = (current_price - pos.entry_price) * pos.size
            else:
                unrealized_pnl = (pos.entry_price - current_price) * pos.size
            
            equity += unrealized_pnl
        
        return equity
    
    def _calculate_metrics(self):
        """Calculate performance metrics for the backtest"""
        # Skip if no trades
        if not self.trades:
            self.metrics = {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
            return
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.profit > 0)
        losing_trades = sum(1 for t in self.trades if t.profit <= 0)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        gross_profit = sum(t.profit for t in self.trades if t.profit > 0)
        gross_loss = abs(sum(t.profit for t in self.trades if t.profit <= 0))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate equity curve and drawdown
        equity_curve = np.array(self.equity)
        hwm = np.maximum.accumulate(equity_curve)  # High water mark
        drawdown = (hwm - equity_curve) / hwm * 100.0  # Percentage drawdown
        max_drawdown = np.max(drawdown)
        
        # Calculate returns
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        # Sharpe ratio (annualized)
        # Assuming daily returns
        if len(returns) > 1:
            sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = 0
        
        # Store metrics
        self.metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'net_profit': gross_profit - gross_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'average_trade': (gross_profit - gross_loss) / total_trades if total_trades > 0 else 0,
            'average_winner': gross_profit / winning_trades if winning_trades > 0 else 0,
            'average_loser': -gross_loss / losing_trades if losing_trades > 0 else 0,
            'largest_winner': max(t.profit for t in self.trades) if self.trades else 0,
            'largest_loser': min(t.profit for t in self.trades) if self.trades else 0,
            'max_consecutive_winners': self._max_consecutive(lambda t: t.profit > 0),
            'max_consecutive_losers': self._max_consecutive(lambda t: t.profit <= 0)
        }
    
    def _max_consecutive(self, condition_func):
        """
        Calculate maximum consecutive occurrences
        
        Parameters:
        -----------
        condition_func : function
            Function that returns True/False for each trade
            
        Returns:
        --------
        int
            Maximum consecutive occurrences
        """
        # Skip if no trades
        if not self.trades:
            return 0
        
        # Map trades to True/False based on condition
        results = [condition_func(t) for t in self.trades]
        
        # Calculate max consecutive
        max_consecutive = 0
        current_consecutive = 0
        for r in results:
            if r:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive 