import numpy as np
import pandas as pd
from numba import jit, prange
import time
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

class PerformanceOptimizedBacktester:
    """
    Performance-optimized implementation of the backtesting engine
    that uses vectorized operations and JIT compilation for faster execution.
    """
    
    def __init__(self, data, strategy_params, use_multiprocessing=False):
        """
        Initialize the performance-optimized backtester
        
        Args:
            data: Dictionary of pandas DataFrames with price data for each timeframe
            strategy_params: Dictionary of strategy parameters
            use_multiprocessing: Whether to use multiprocessing for parallel execution
        """
        self.data = data
        self.params = strategy_params
        self.use_multiprocessing = use_multiprocessing
        self.cpu_count = multiprocessing.cpu_count()
        
    @staticmethod
    @jit(nopython=True)
    def _calculate_ema_fast(prices, period):
        """
        JIT-compiled function to calculate EMA quickly
        
        Args:
            prices: numpy array of prices
            period: EMA period
            
        Returns:
            numpy array with EMA values
        """
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[:period] = np.nan
        ema[period-1] = np.mean(prices[:period])
        
        for i in range(period, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
            
        return ema
    
    @staticmethod
    @jit(nopython=True)
    def _calculate_extensions_fast(prices, ema, threshold, lookback):
        """
        JIT-compiled function to detect price extensions
        
        Args:
            prices: numpy array of close prices
            ema: numpy array of EMA values
            threshold: Extension threshold multiple
            lookback: Lookback period for highest/lowest EMA
            
        Returns:
            numpy array with boolean values indicating extensions
        """
        n = len(prices)
        extensions = np.zeros(n, dtype=np.bool_)
        
        for i in range(lookback, n):
            # Skip if we don't have valid EMA values
            if np.isnan(ema[i]) or np.isnan(ema[i-1]):
                continue
                
            # Calculate percent distance from EMA
            pct_from_ema = (prices[i] - ema[i]) / ema[i]
            
            # Check if extension threshold is exceeded
            if abs(pct_from_ema) > threshold:
                extensions[i] = True
                
        return extensions
    
    @staticmethod
    @jit(nopython=True)
    def _execute_trades_fast(signals, prices, stop_pct, target_pct):
        """
        JIT-compiled function to execute trades and calculate P&L
        
        Args:
            signals: numpy array with trade signals (1 for buy, -1 for sell, 0 for no trade)
            prices: numpy array with close prices
            stop_pct: Stop loss percentage
            target_pct: Take profit percentage
            
        Returns:
            tuple of (equity_curve, trades)
        """
        n = len(signals)
        equity = np.ones(n)
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(1, n):
            # Process existing position if we have one
            if position != 0:
                # Check for stop loss
                if position == 1 and prices[i] <= entry_price * (1 - stop_pct):
                    # Stop loss hit for long position
                    pnl = (prices[i] / entry_price - 1)
                    equity[i] = equity[i-1] * (1 + pnl)
                    trades.append((i, entry_idx, position, entry_price, prices[i], pnl))
                    position = 0
                elif position == -1 and prices[i] >= entry_price * (1 + stop_pct):
                    # Stop loss hit for short position
                    pnl = (entry_price / prices[i] - 1)
                    equity[i] = equity[i-1] * (1 + pnl)
                    trades.append((i, entry_idx, position, entry_price, prices[i], pnl))
                    position = 0
                # Check for take profit
                elif position == 1 and prices[i] >= entry_price * (1 + target_pct):
                    # Take profit hit for long position
                    pnl = target_pct  # Fixed take profit
                    equity[i] = equity[i-1] * (1 + pnl)
                    trades.append((i, entry_idx, position, entry_price, prices[i], pnl))
                    position = 0
                elif position == -1 and prices[i] <= entry_price * (1 - target_pct):
                    # Take profit hit for short position
                    pnl = target_pct  # Fixed take profit
                    equity[i] = equity[i-1] * (1 + pnl)
                    trades.append((i, entry_idx, position, entry_price, prices[i], pnl))
                    position = 0
                else:
                    # Position still open
                    equity[i] = equity[i-1]
            else:
                # No position, copy previous equity
                equity[i] = equity[i-1]
                
            # Check for new trade signal
            if position == 0 and signals[i] != 0:
                position = signals[i]  # 1 for long, -1 for short
                entry_price = prices[i]
                entry_idx = i
        
        return equity, trades
    
    def _process_timeframe(self, tf_name, tf_data):
        """
        Process a single timeframe's data to generate signals
        
        Args:
            tf_name: Timeframe name
            tf_data: DataFrame with price data for this timeframe
            
        Returns:
            DataFrame with signals for this timeframe
        """
        # Convert to numpy for faster operations
        closes = tf_data['close'].values
        
        # Calculate EMA using fast method
        ema = self._calculate_ema_fast(closes, self.params['ema_period'])
        
        # Detect extensions
        extensions = self._calculate_extensions_fast(
            closes, 
            ema, 
            self.params['extension_threshold'],
            self.params['lookback_period']
        )
        
        # Convert back to DataFrame
        result = pd.DataFrame({
            'close': closes,
            'ema': ema,
            'extension': extensions
        }, index=tf_data.index)
        
        return result
    
    def run(self):
        """
        Run the backtest with performance optimizations
        
        Returns:
            Dictionary with backtest results
        """
        start_time = time.time()
        
        processed_data = {}
        
        # Process each timeframe
        if self.use_multiprocessing and len(self.data) > 1:
            # Use process pool for parallel execution
            with ProcessPoolExecutor(max_workers=min(len(self.data), self.cpu_count)) as executor:
                future_to_tf = {
                    executor.submit(self._process_timeframe, tf, data): tf 
                    for tf, data in self.data.items()
                }
                
                for future in future_to_tf:
                    tf = future_to_tf[future]
                    processed_data[tf] = future.result()
        else:
            # Single-threaded execution
            for tf, data in self.data.items():
                processed_data[tf] = self._process_timeframe(tf, data)
        
        # Use the highest timeframe for signals
        primary_tf = max(self.data.keys())
        signals = np.zeros(len(processed_data[primary_tf]))
        
        # Generate signals (simplified for example)
        for i in range(1, len(signals)):
            # This is where your actual signal logic would go
            # For now just using a simplified approach for illustration
            has_extension = any(processed_data[tf]['extension'].iloc[i-1] for tf in processed_data)
            price_above_ema = all(
                processed_data[tf]['close'].iloc[i] > processed_data[tf]['ema'].iloc[i] 
                for tf in processed_data
            )
            
            if has_extension and price_above_ema:
                signals[i] = 1  # Buy signal
            elif has_extension and not price_above_ema:
                signals[i] = -1  # Sell signal
        
        # Execute trades
        closes = processed_data[primary_tf]['close'].values
        equity, trades = self._execute_trades_fast(
            signals, 
            closes,
            self.params['stop_loss_pct'],
            self.params['take_profit_pct']
        )
        
        # Calculate performance metrics
        returns = np.diff(equity) / equity[:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
        max_dd = np.max(np.maximum.accumulate(equity) - equity)
        
        execution_time = time.time() - start_time
        
        return {
            'equity_curve': equity,
            'trades': trades,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'execution_time': execution_time
        }

def benchmark_performance():
    """
    Benchmark the performance of the optimized backtester vs. standard implementation
    """
    # Example usage
    import random
    
    # Generate sample data
    dates = pd.date_range(start='2020-01-01', periods=10000, freq='D')
    data = {}
    
    # Create data for multiple timeframes
    for tf in ['D', '4H', '1H']:
        n_periods = len(dates) * (1 if tf == 'D' else 6 if tf == '4H' else 24)
        idx = pd.date_range(start='2020-01-01', periods=n_periods, freq=tf)
        
        # Generate random price data
        random.seed(42)  # For reproducibility
        base = 100
        closes = [base]
        for _ in range(n_periods-1):
            closes.append(closes[-1] * (1 + random.normalvariate(0.0001, 0.01)))
            
        # Create dataframe
        df = pd.DataFrame({
            'open': closes[:-1] + [closes[-1]],
            'high': [p * (1 + random.uniform(0, 0.01)) for p in closes],
            'low': [p * (1 - random.uniform(0, 0.01)) for p in closes],
            'close': closes,
            'volume': [random.randint(1000, 10000) for _ in range(n_periods)]
        }, index=idx)
        
        data[tf] = df
    
    # Strategy parameters
    params = {
        'ema_period': 9,
        'extension_threshold': 0.02,
        'lookback_period': 5,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.03
    }
    
    # Run optimized version
    print("Running optimized version...")
    optimized = PerformanceOptimizedBacktester(data, params)
    opt_results = optimized.run()
    
    print(f"Execution time: {opt_results['execution_time']:.2f} seconds")
    print(f"Sharpe ratio: {opt_results['sharpe_ratio']:.2f}")
    print(f"Max drawdown: {opt_results['max_drawdown']:.2%}")
    
    # With multiprocessing
    print("\nRunning with multiprocessing...")
    mp_optimized = PerformanceOptimizedBacktester(data, params, use_multiprocessing=True)
    mp_results = mp_optimized.run()
    
    print(f"Execution time: {mp_results['execution_time']:.2f} seconds")
    print(f"Speed improvement: {opt_results['execution_time'] / mp_results['execution_time']:.2f}x")

if __name__ == "__main__":
    benchmark_performance()
