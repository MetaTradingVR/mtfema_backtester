"""
Performance-optimized backtester implementation for the Multi-Timeframe 9 EMA Extension Strategy.

This module provides a highly optimized backtesting engine using:
- Numba JIT compilation for faster calculations
- Vectorized operations instead of loops
- Multiprocessing support for parallel execution
"""

import numpy as np
import pandas as pd
import logging
import time
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from datetime import datetime
import multiprocessing as mp
from functools import partial

# Try to import numba, but provide fallbacks if not available
try:
    import numba
    from numba import jit, njit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    # Create dummy decorators for graceful fallback
    def jit(*args, **kwargs):
        if len(args) and callable(args[0]):
            return args[0]
        else:
            def decorator(func):
                return func
            return decorator
    
    # Alias njit to jit
    njit = jit
    
    # Define prange as regular range for fallback
    prange = range
    
    NUMBA_AVAILABLE = False
    logging.warning("Numba not available. Performance will be reduced.")

# Configure logger
logger = logging.getLogger(__name__)

class OptimizedBacktester:
    """
    Performance-optimized backtester for the Multi-Timeframe 9 EMA Extension Strategy.
    
    This backtester uses Numba JIT compilation for faster execution and vectorized
    operations where possible to minimize Python loops.
    """
    
    def __init__(self, 
                initial_capital: float = 100000.0,
                commission: float = 0.001,
                slippage: float = 0.001,
                use_numba: bool = True,
                use_multiprocessing: bool = False,
                max_workers: int = None):
        """
        Initialize the optimized backtester.
        
        Args:
            initial_capital: Initial capital for backtesting
            commission: Commission per trade (fraction)
            slippage: Slippage per trade (fraction)
            use_numba: Whether to use Numba for optimization (if available)
            use_multiprocessing: Whether to use multiprocessing for parallel execution
            max_workers: Maximum number of worker processes (None = auto)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.use_numba = use_numba and NUMBA_AVAILABLE
        self.use_multiprocessing = use_multiprocessing
        self.max_workers = max_workers or mp.cpu_count()
        
        # Performance tracking
        self.calculation_times = {}
        
        # Results storage
        self.equity_curve = None
        self.trades = []
        self.performance_metrics = {}
        
        logger.info(f"Initialized OptimizedBacktester with numba={self.use_numba}, "
                   f"multiprocessing={self.use_multiprocessing}, max_workers={self.max_workers}")
    
    def run(self, data: Dict[str, pd.DataFrame], 
           strategy_func: Callable, 
           strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run a backtest with the given data and strategy function.
        
        Args:
            data: Dictionary of dataframes by timeframe
            strategy_func: Function that generates signals
            strategy_params: Parameters for the strategy function
            
        Returns:
            Dictionary with backtest results
        """
        start_time = time.time()
        logger.info("Starting optimized backtest")
        
        # Set default strategy params if none provided
        if strategy_params is None:
            strategy_params = {}
        
        # Prepare data for processing
        prepared_data = self._prepare_data(data)
        
        # Get signals from strategy
        signals = self._get_strategy_signals(prepared_data, strategy_func, strategy_params)
        
        # Process signals to generate trades
        trades, equity_curve = self._process_signals(prepared_data, signals)
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(equity_curve, trades)
        
        # Store results
        self.equity_curve = equity_curve
        self.trades = trades
        self.performance_metrics = metrics
        
        # Track total execution time
        execution_time = time.time() - start_time
        logger.info(f"Backtest completed in {execution_time:.2f} seconds")
        self.calculation_times['total'] = execution_time
        
        # Return results
        return {
            'equity_curve': equity_curve,
            'trades': trades,
            'performance_metrics': metrics,
            'calculation_times': self.calculation_times
        }
    
    def _prepare_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Prepare data for optimized processing.
        
        Args:
            data: Dictionary of dataframes by timeframe
            
        Returns:
            Dictionary of numpy arrays by timeframe and column
        """
        start_time = time.time()
        
        prepared_data = {}
        all_dates = set()
        
        # First pass: extract all unique dates
        for tf, df in data.items():
            all_dates.update(df.index)
        
        # Sort dates
        sorted_dates = sorted(all_dates)
        date_indices = {date: i for i, date in enumerate(sorted_dates)}
        
        # Second pass: prepare arrays
        for tf, df in data.items():
            # Get numpy arrays
            opens = df['Open'].values
            highs = df['High'].values
            lows = df['Low'].values
            closes = df['Close'].values
            volumes = df['Volume'].values if 'Volume' in df.columns else np.zeros(len(df))
            
            # Create date mapping
            tf_dates = df.index
            tf_indices = np.zeros(len(sorted_dates), dtype=np.int32) - 1
            
            for i, date in enumerate(tf_dates):
                tf_indices[date_indices[date]] = i
            
            # Store arrays
            prepared_data[tf] = {
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes,
                'date_indices': tf_indices
            }
            
            # Add any indicator columns
            for col in df.columns:
                if col not in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    prepared_data[tf][col.lower()] = df[col].values
        
        # Store common date information
        prepared_data['_common'] = {
            'dates': np.array(sorted_dates),
            'total_bars': len(sorted_dates)
        }
        
        self.calculation_times['prepare_data'] = time.time() - start_time
        return prepared_data
    
    def _get_strategy_signals(self, 
                             prepared_data: Dict[str, Dict[str, np.ndarray]],
                             strategy_func: Callable,
                             strategy_params: Dict[str, Any]) -> np.ndarray:
        """
        Get signals from the strategy function.
        
        Args:
            prepared_data: Prepared data arrays
            strategy_func: Function that generates signals
            strategy_params: Parameters for the strategy function
            
        Returns:
            Numpy array of signals
        """
        start_time = time.time()
        
        # Get common data
        total_bars = prepared_data['_common']['total_bars']
        
        # Initialize signal arrays
        signals = np.zeros((total_bars, 3))  # [entry_signal, exit_signal, direction]
        
        # Use strategy function to get signals
        try:
            if self.use_numba and hasattr(strategy_func, 'py_func'):
                # It's a numba function, call directly
                signals = strategy_func(prepared_data, strategy_params)
            else:
                # Regular Python function
                signals = strategy_func(prepared_data, strategy_params)
        except Exception as e:
            logger.error(f"Error in strategy function: {str(e)}")
            raise
        
        self.calculation_times['get_signals'] = time.time() - start_time
        return signals
    
    @staticmethod
    @njit(fastmath=True)
    def _calculate_position_metrics(
        prices: np.ndarray,
        position_size: np.ndarray,
        commission_rate: float,
        slippage_rate: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate position-related metrics using Numba.
        
        Args:
            prices: Array of prices
            position_size: Array of position sizes
            commission_rate: Commission rate
            slippage_rate: Slippage rate
            
        Returns:
            Tuple of (position_value, trade_costs, pnl)
        """
        n = len(prices)
        position_value = np.zeros(n)
        trade_costs = np.zeros(n)
        pnl = np.zeros(n)
        
        for i in range(1, n):
            # Calculate position value
            position_value[i] = position_size[i] * prices[i]
            
            # Calculate trade costs when position size changes
            size_change = abs(position_size[i] - position_size[i-1])
            if size_change > 0:
                # Apply commission and slippage
                trade_cost = size_change * prices[i] * (commission_rate + slippage_rate)
                trade_costs[i] = trade_cost
            
            # Calculate P&L
            if position_size[i-1] != 0:
                # Calculate P&L from price change
                price_change = prices[i] - prices[i-1]
                pnl[i] = position_size[i-1] * price_change
        
        return position_value, trade_costs, pnl
    
    def _process_signals(self,
                        prepared_data: Dict[str, Dict[str, np.ndarray]],
                        signals: np.ndarray) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
        """
        Process signals to generate trades and equity curve.
        
        Args:
            prepared_data: Prepared data arrays
            signals: Array of signals
            
        Returns:
            Tuple of (trades list, equity curve dataframe)
        """
        start_time = time.time()
        
        # Get common data
        dates = prepared_data['_common']['dates']
        total_bars = prepared_data['_common']['total_bars']
        
        # Get main price data (using first timeframe)
        main_tf = next(tf for tf in prepared_data.keys() if tf != '_common')
        close_prices = prepared_data[main_tf]['close']
        date_indices = prepared_data[main_tf]['date_indices']
        
        # Initialize arrays for calculations
        position = np.zeros(total_bars)
        position_size = np.zeros(total_bars)
        equity = np.zeros(total_bars)
        cash = np.zeros(total_bars)
        
        # Set initial cash
        cash[0] = self.initial_capital
        equity[0] = self.initial_capital
        
        # Process signals using Numba if available
        if self.use_numba:
            position, position_size, cash, equity = self._process_signals_numba(
                signals, close_prices, date_indices, self.initial_capital,
                self.commission, self.slippage, total_bars
            )
        else:
            # Fallback to Python implementation
            for i in range(1, total_bars):
                # Get price for this bar
                price_idx = date_indices[i]
                if price_idx == -1:
                    # No price data for this date, carry forward
                    position[i] = position[i-1]
                    position_size[i] = position_size[i-1]
                    cash[i] = cash[i-1]
                    equity[i] = cash[i] + position_size[i] * (
                        close_prices[date_indices[max(0, i-1)]] if date_indices[max(0, i-1)] != -1 else 0
                    )
                    continue
                
                price = close_prices[price_idx]
                
                # Check for entry signal
                if signals[i, 0] == 1 and position[i-1] == 0:
                    # Long entry
                    direction = signals[i, 2]
                    position[i] = direction
                    
                    # Calculate position size
                    risk_amount = 0.01 * equity[i-1]  # 1% risk
                    position_size[i] = risk_amount / price if direction == 1 else risk_amount / price * -1
                    
                    # Apply costs
                    cost = abs(position_size[i]) * price * (self.commission + self.slippage)
                    cash[i] = cash[i-1] - abs(position_size[i]) * price - cost
                
                # Check for exit signal
                elif signals[i, 1] == 1 and position[i-1] != 0:
                    # Exit position
                    cash[i] = cash[i-1] + position_size[i-1] * price
                    
                    # Apply costs
                    cost = abs(position_size[i-1]) * price * (self.commission + self.slippage)
                    cash[i] = cash[i] - cost
                    
                    position[i] = 0
                    position_size[i] = 0
                
                else:
                    # No signal, carry forward
                    position[i] = position[i-1]
                    position_size[i] = position_size[i-1]
                    cash[i] = cash[i-1]
                
                # Calculate equity
                equity[i] = cash[i] + position_size[i] * price
        
        # Convert to trade list
        trades = self._extract_trades(
            dates, position, position_size, close_prices, date_indices
        )
        
        # Create equity curve dataframe
        equity_df = pd.DataFrame({
            'Equity': equity,
            'Cash': cash,
            'Position': position,
            'Position_Size': position_size
        }, index=dates)
        
        self.calculation_times['process_signals'] = time.time() - start_time
        return trades, equity_df
    
    @staticmethod
    @njit(fastmath=True)
    def _process_signals_numba(
        signals: np.ndarray,
        prices: np.ndarray,
        date_indices: np.ndarray,
        initial_capital: float,
        commission: float,
        slippage: float,
        total_bars: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Process signals using Numba for performance.
        
        Args:
            signals: Signals array [entry, exit, direction]
            prices: Close prices array
            date_indices: Mapping from bar index to price index
            initial_capital: Initial capital
            commission: Commission rate
            slippage: Slippage rate
            total_bars: Total number of bars
            
        Returns:
            Tuple of (position, position_size, cash, equity) arrays
        """
        # Initialize arrays
        position = np.zeros(total_bars)
        position_size = np.zeros(total_bars)
        cash = np.zeros(total_bars)
        equity = np.zeros(total_bars)
        
        # Set initial values
        cash[0] = initial_capital
        equity[0] = initial_capital
        
        # Process each bar
        for i in range(1, total_bars):
            # Get price for this bar
            price_idx = date_indices[i]
            if price_idx == -1:
                # No price data for this date, carry forward
                position[i] = position[i-1]
                position_size[i] = position_size[i-1]
                cash[i] = cash[i-1]
                
                # Find last valid price
                last_valid_idx = -1
                for j in range(i-1, -1, -1):
                    if date_indices[j] != -1:
                        last_valid_idx = date_indices[j]
                        break
                
                if last_valid_idx != -1:
                    equity[i] = cash[i] + position_size[i] * prices[last_valid_idx]
                else:
                    equity[i] = cash[i]
                
                continue
            
            price = prices[price_idx]
            
            # Check for entry signal
            if signals[i, 0] == 1 and position[i-1] == 0:
                # Entry
                direction = signals[i, 2]
                position[i] = direction
                
                # Calculate position size (1% risk)
                risk_amount = 0.01 * equity[i-1]
                position_size[i] = risk_amount / price if direction == 1 else risk_amount / price * -1
                
                # Apply costs
                cost = abs(position_size[i]) * price * (commission + slippage)
                cash[i] = cash[i-1] - abs(position_size[i]) * price - cost
            
            # Check for exit signal
            elif signals[i, 1] == 1 and position[i-1] != 0:
                # Exit
                cash[i] = cash[i-1] + position_size[i-1] * price
                
                # Apply costs
                cost = abs(position_size[i-1]) * price * (commission + slippage)
                cash[i] = cash[i] - cost
                
                position[i] = 0
                position_size[i] = 0
            
            else:
                # No signal, carry forward
                position[i] = position[i-1]
                position_size[i] = position_size[i-1]
                cash[i] = cash[i-1]
            
            # Calculate equity
            equity[i] = cash[i] + position_size[i] * price
        
        return position, position_size, cash, equity
    
    def _extract_trades(self,
                       dates: np.ndarray,
                       position: np.ndarray,
                       position_size: np.ndarray,
                       prices: np.ndarray,
                       date_indices: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract trade information from position array.
        
        Args:
            dates: Array of dates
            position: Array of positions (1 for long, -1 for short, 0 for flat)
            position_size: Array of position sizes
            prices: Array of prices
            date_indices: Mapping from bar index to price index
            
        Returns:
            List of trade dictionaries
        """
        trades = []
        current_trade = None
        
        for i in range(1, len(position)):
            # Entry
            if position[i] != 0 and position[i-1] == 0:
                # Get price for this entry
                price_idx = date_indices[i]
                if price_idx == -1:
                    continue  # Skip if no price data
                
                entry_price = prices[price_idx]
                
                # Create new trade
                current_trade = {
                    'entry_date': dates[i],
                    'entry_price': entry_price,
                    'direction': 'LONG' if position[i] > 0 else 'SHORT',
                    'size': abs(position_size[i]),
                    'initial_risk': 0.01,  # 1% risk per trade
                }
            
            # Exit
            elif position[i] == 0 and position[i-1] != 0:
                if current_trade is None:
                    continue  # Skip if no active trade
                
                # Get price for this exit
                price_idx = date_indices[i]
                if price_idx == -1:
                    continue  # Skip if no price data
                
                exit_price = prices[price_idx]
                
                # Calculate P&L
                if current_trade['direction'] == 'LONG':
                    pnl = (exit_price - current_trade['entry_price']) * current_trade['size']
                else:
                    pnl = (current_trade['entry_price'] - exit_price) * current_trade['size']
                
                # Apply costs
                costs = current_trade['size'] * exit_price * (self.commission + self.slippage)
                costs += current_trade['size'] * current_trade['entry_price'] * (self.commission + self.slippage)
                
                # Complete the trade
                current_trade.update({
                    'exit_date': dates[i],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'costs': costs,
                    'net_pnl': pnl - costs,
                    'duration': (dates[i] - current_trade['entry_date']).total_seconds() / 86400,  # Duration in days
                    'return': (pnl - costs) / (current_trade['size'] * current_trade['entry_price']) * 100  # Return in %
                })
                
                # Add to trades list
                trades.append(current_trade)
                current_trade = None
        
        # Check if there's an open trade at the end
        if current_trade is not None:
            # Find the last valid price
            last_idx = -1
            for i in range(len(date_indices)-1, -1, -1):
                if date_indices[i] != -1:
                    last_idx = i
                    break
            
            if last_idx != -1:
                current_trade['exit_date'] = dates[-1]
                current_trade['exit_price'] = prices[date_indices[last_idx]]
                current_trade['status'] = 'OPEN'
                trades.append(current_trade)
        
        return trades
    
    def _calculate_performance_metrics(self, 
                                     equity_curve: pd.DataFrame, 
                                     trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate performance metrics from the equity curve and trades.
        
        Args:
            equity_curve: Equity curve dataframe
            trades: List of trade dictionaries
            
        Returns:
            Dictionary of performance metrics
        """
        start_time = time.time()
        
        metrics = {}
        
        # Basic metrics
        if len(equity_curve) > 0:
            initial_equity = equity_curve['Equity'].iloc[0]
            final_equity = equity_curve['Equity'].iloc[-1]
            metrics['total_return'] = (final_equity / initial_equity - 1) * 100  # %
            metrics['initial_equity'] = initial_equity
            metrics['final_equity'] = final_equity
            
            # Calculate drawdown
            equity_curve['Drawdown'] = 1 - equity_curve['Equity'] / equity_curve['Equity'].cummax()
            metrics['max_drawdown'] = equity_curve['Drawdown'].max() * 100  # %
            
            # Calculate daily returns
            if isinstance(equity_curve.index[0], datetime):
                equity_curve['Date'] = equity_curve.index.date
                daily_equity = equity_curve.groupby('Date')['Equity'].last()
                daily_returns = daily_equity.pct_change().dropna()
                
                if len(daily_returns) > 0:
                    metrics['annual_return'] = daily_returns.mean() * 252 * 100  # %
                    metrics['annual_volatility'] = daily_returns.std() * np.sqrt(252) * 100  # %
                    metrics['sharpe_ratio'] = (metrics['annual_return'] / 100) / (metrics['annual_volatility'] / 100) if metrics['annual_volatility'] > 0 else 0
        
        # Trade-based metrics
        if trades:
            metrics['total_trades'] = len(trades)
            win_trades = [t for t in trades if t.get('net_pnl', 0) > 0]
            loss_trades = [t for t in trades if t.get('net_pnl', 0) <= 0]
            
            metrics['winning_trades'] = len(win_trades)
            metrics['losing_trades'] = len(loss_trades)
            metrics['win_rate'] = len(win_trades) / len(trades) * 100 if trades else 0  # %
            
            if win_trades:
                metrics['avg_win'] = sum(t['net_pnl'] for t in win_trades) / len(win_trades)
            if loss_trades:
                metrics['avg_loss'] = sum(t['net_pnl'] for t in loss_trades) / len(loss_trades)
            
            if metrics.get('avg_loss', 0) != 0 and metrics.get('avg_win', 0) != 0:
                metrics['profit_factor'] = abs(metrics['avg_win'] * metrics['winning_trades'] / 
                                            (metrics['avg_loss'] * metrics['losing_trades']))
            
            # Calculate average trade duration
            if all('duration' in t for t in trades):
                metrics['avg_duration'] = sum(t['duration'] for t in trades) / len(trades)
        
        self.calculation_times['calculate_metrics'] = time.time() - start_time
        return metrics
    
    def run_parallel(self, 
                    data: Dict[str, pd.DataFrame],
                    strategy_func: Callable,
                    param_grid: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run multiple backtests in parallel with different parameters.
        
        Args:
            data: Dictionary of dataframes by timeframe
            strategy_func: Function that generates signals
            param_grid: List of parameter dictionaries to test
            
        Returns:
            List of backtest results dictionaries
        """
        if not self.use_multiprocessing:
            logger.warning("Multiprocessing disabled, running sequentially")
            return [self.run(data, strategy_func, params) for params in param_grid]
        
        start_time = time.time()
        logger.info(f"Running {len(param_grid)} backtests in parallel with {self.max_workers} workers")
        
        # Prepare data once to avoid redundant preparation
        prepared_data = self._prepare_data(data)
        
        # Create a partial function for the worker
        worker_func = partial(
            self._parallel_worker,
            prepared_data=prepared_data,
            strategy_func=strategy_func
        )
        
        # Run with multiprocessing
        with mp.Pool(self.max_workers) as pool:
            results = pool.map(worker_func, param_grid)
        
        execution_time = time.time() - start_time
        logger.info(f"Parallel backtests completed in {execution_time:.2f} seconds")
        
        return results
    
    def _parallel_worker(self,
                       params: Dict[str, Any],
                       prepared_data: Dict[str, Dict[str, np.ndarray]],
                       strategy_func: Callable) -> Dict[str, Any]:
        """
        Worker function for parallel backtesting.
        
        Args:
            params: Strategy parameters
            prepared_data: Prepared data arrays
            strategy_func: Strategy function
            
        Returns:
            Backtest results dictionary
        """
        # Get signals
        signals = self._get_strategy_signals(prepared_data, strategy_func, params)
        
        # Process signals
        trades, equity_curve = self._process_signals(prepared_data, signals)
        
        # Calculate metrics
        metrics = self._calculate_performance_metrics(equity_curve, trades)
        
        # Return results
        return {
            'params': params,
            'equity_curve': equity_curve,
            'trades': trades,
            'performance_metrics': metrics
        }
    
    def benchmark(self, data: Dict[str, pd.DataFrame], 
                strategy_func: Callable, 
                strategy_params: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Benchmark the backtesting performance.
        
        Args:
            data: Dictionary of dataframes by timeframe
            strategy_func: Function that generates signals
            strategy_params: Parameters for the strategy function
            
        Returns:
            Dictionary with benchmark results
        """
        logger.info("Running benchmark")
        
        # Initialize results
        results = {}
        
        # Time data preparation
        start_time = time.time()
        prepared_data = self._prepare_data(data)
        results['prepare_data'] = time.time() - start_time
        
        # Time signal generation
        start_time = time.time()
        signals = self._get_strategy_signals(prepared_data, strategy_func, strategy_params or {})
        results['generate_signals'] = time.time() - start_time
        
        # Time position processing
        start_time = time.time()
        trades, equity_curve = self._process_signals(prepared_data, signals)
        results['process_signals'] = time.time() - start_time
        
        # Time metrics calculation
        start_time = time.time()
        _ = self._calculate_performance_metrics(equity_curve, trades)
        results['calculate_metrics'] = time.time() - start_time
        
        # Total time
        results['total'] = sum(results.values())
        
        # Log results
        logger.info(f"Benchmark results: {results}")
        
        return results 