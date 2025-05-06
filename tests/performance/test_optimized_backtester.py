"""
Performance tests for the optimized backtester.
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd
from time import time
import matplotlib.pyplot as plt
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mtfema_backtester.backtest.optimized_backtester import OptimizedBacktester

@pytest.mark.performance
def test_backtester_performance_scaling():
    """Test scaling behavior of the optimized backtester with different data sizes."""
    # Number of bars to test
    bar_counts = [100, 1000, 10000, 50000]  
    
    # Results containers
    numba_times = []
    python_times = []
    
    for bars in bar_counts:
        # Create synthetic data
        dates = pd.date_range(start='2020-01-01', periods=bars, freq='1H')
        data = pd.DataFrame({
            'Open': np.random.normal(100, 1, bars),
            'High': np.random.normal(101, 1, bars),
            'Low': np.random.normal(99, 1, bars),
            'Close': np.random.normal(100.5, 1, bars),
            'Volume': np.random.normal(50000, 10000, bars)
        }, index=dates)
        
        # Make sure High is the highest and Low is the lowest
        for i in range(len(data)):
            data.loc[data.index[i], 'High'] = max(
                data.loc[data.index[i], 'Open'],
                data.loc[data.index[i], 'Close'],
                data.loc[data.index[i], 'High']
            ) + abs(np.random.normal(0, 0.2))
            
            data.loc[data.index[i], 'Low'] = min(
                data.loc[data.index[i], 'Open'],
                data.loc[data.index[i], 'Close'],
                data.loc[data.index[i], 'Low']
            ) - abs(np.random.normal(0, 0.2))
        
        # Add some basic indicators
        data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
        
        # Create a simple strategy function
        def sample_strategy(prepared_data, params):
            common_data = prepared_data['_common']
            total_bars = common_data['total_bars']
            
            # Main timeframe data
            main_tf = next(tf for tf in prepared_data.keys() if tf != '_common')
            closes = prepared_data[main_tf]['close']
            ema9 = prepared_data[main_tf].get('ema_9', 
                   np.zeros_like(closes))  # Fallback if not available
            ema20 = prepared_data[main_tf].get('ema_20', 
                    np.zeros_like(closes))  # Fallback if not available
            
            # Date mapping
            date_indices = prepared_data[main_tf]['date_indices']
            
            # Initialize signals
            signals = np.zeros((total_bars, 3))  # [entry, exit, direction]
            
            # Generate signals (simple EMA crossover)
            for i in range(1, total_bars):
                price_idx = date_indices[i]
                if price_idx <= 0 or price_idx >= len(closes) - 1:
                    continue
                    
                # Entry signal: EMA9 crosses above EMA20
                if ema9[price_idx] > ema20[price_idx] and ema9[price_idx-1] <= ema20[price_idx-1]:
                    signals[i, 0] = 1  # Entry
                    signals[i, 2] = 1  # Long
                
                # Exit signal: EMA9 crosses below EMA20
                elif ema9[price_idx] < ema20[price_idx] and ema9[price_idx-1] >= ema20[price_idx-1]:
                    signals[i, 1] = 1  # Exit
            
            return signals
        
        # Test with Numba JIT
        data_dict = {'1h': data}
        backtester = OptimizedBacktester(use_numba=True, use_multiprocessing=False)
        start = time()
        results_numba = backtester.run(data_dict, sample_strategy)
        numba_time = time() - start
        numba_times.append(numba_time)
        
        # Test without Numba JIT
        backtester = OptimizedBacktester(use_numba=False, use_multiprocessing=False)
        start = time()
        results_python = backtester.run(data_dict, sample_strategy)
        python_time = time() - start
        python_times.append(python_time)
        
        print(f"\nBars: {bars}")
        print(f"Numba time: {numba_time:.4f}s")
        print(f"Python time: {python_time:.4f}s")
        print(f"Speedup: {python_time / numba_time:.2f}x")
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(bar_counts, numba_times, marker='o', label='Numba JIT')
    plt.plot(bar_counts, python_times, marker='x', label='Python')
    plt.xlabel('Number of Bars')
    plt.ylabel('Execution Time (s)')
    plt.title('Backtester Performance Scaling')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.yscale('log')
    
    # Create plots directory if it doesn't exist
    os.makedirs('./results/performance', exist_ok=True)
    
    # Save plot
    plt.savefig('./results/performance/backtester_scaling.png')
    
    # Also assert that Numba is faster for larger datasets
    assert numba_times[-1] < python_times[-1], "Numba should be faster for large datasets"

@pytest.mark.performance
def test_parallel_execution():
    """Test parallel execution with multiple parameter sets."""
    # Create synthetic data
    bars = 10000
    dates = pd.date_range(start='2020-01-01', periods=bars, freq='1H')
    data = pd.DataFrame({
        'Open': np.random.normal(100, 1, bars),
        'High': np.random.normal(101, 1, bars),
        'Low': np.random.normal(99, 1, bars),
        'Close': np.random.normal(100.5, 1, bars),
        'Volume': np.random.normal(50000, 10000, bars)
    }, index=dates)
    
    # Add some basic indicators
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
    
    # Create a simple strategy function
    def sample_strategy(prepared_data, params):
        common_data = prepared_data['_common']
        total_bars = common_data['total_bars']
        
        # Main timeframe data
        main_tf = next(tf for tf in prepared_data.keys() if tf != '_common')
        closes = prepared_data[main_tf]['close']
        ema_fast = prepared_data[main_tf].get('ema_9', np.zeros_like(closes))
        ema_slow = prepared_data[main_tf].get('ema_20', np.zeros_like(closes))
        
        # Date mapping
        date_indices = prepared_data[main_tf]['date_indices']
        
        # Get parameters
        threshold = params.get('threshold', 0.0)
        
        # Initialize signals
        signals = np.zeros((total_bars, 3))  # [entry, exit, direction]
        
        # Generate signals
        for i in range(1, total_bars):
            price_idx = date_indices[i]
            if price_idx <= 0 or price_idx >= len(closes) - 1:
                continue
                
            # Entry signal with threshold
            if (ema_fast[price_idx] > ema_slow[price_idx] * (1 + threshold) and 
                ema_fast[price_idx-1] <= ema_slow[price_idx-1] * (1 + threshold)):
                signals[i, 0] = 1  # Entry
                signals[i, 2] = 1  # Long
            
            # Exit signal
            elif (ema_fast[price_idx] < ema_slow[price_idx] and 
                 ema_fast[price_idx-1] >= ema_slow[price_idx-1]):
                signals[i, 1] = 1  # Exit
        
        return signals
    
    # Create parameter grid
    param_grid = [
        {'threshold': t / 100} for t in range(0, 5)  # Test threshold from 0% to 5%
    ]
    
    data_dict = {'1h': data}
    
    # Test sequential execution
    backtester_seq = OptimizedBacktester(use_numba=True, use_multiprocessing=False)
    start = time()
    results_seq = [backtester_seq.run(data_dict, sample_strategy, params) for params in param_grid]
    seq_time = time() - start
    
    # Test parallel execution
    backtester_par = OptimizedBacktester(use_numba=True, use_multiprocessing=True, max_workers=4)
    start = time()
    results_par = backtester_par.run_parallel(data_dict, sample_strategy, param_grid)
    par_time = time() - start
    
    print(f"\nParameter Optimization")
    print(f"Sequential time: {seq_time:.4f}s")
    print(f"Parallel time: {par_time:.4f}s")
    print(f"Speedup: {seq_time / par_time:.2f}x")
    
    # Create plot
    plt.figure(figsize=(10, 6))
    
    # Collect performance metrics
    thresholds = [p['threshold'] for p in param_grid]
    returns_seq = [r['performance_metrics'].get('total_return', 0) for r in results_seq]
    sharpes_seq = [r['performance_metrics'].get('sharpe_ratio', 0) for r in results_seq]
    
    # Plot metrics
    plt.subplot(2, 1, 1)
    plt.plot(thresholds, returns_seq, marker='o')
    plt.xlabel('Threshold')
    plt.ylabel('Total Return (%)')
    plt.title('Parameter Optimization Results')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(thresholds, sharpes_seq, marker='x', color='green')
    plt.xlabel('Threshold')
    plt.ylabel('Sharpe Ratio')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plt.savefig('./results/performance/parameter_optimization.png')
    
    # Verify results match between sequential and parallel
    for i, (res_seq, res_par) in enumerate(zip(results_seq, results_par)):
        assert abs(res_seq['performance_metrics'].get('total_return', 0) - 
                  res_par['performance_metrics'].get('total_return', 0)) < 1e-6, \
               f"Results don't match for parameter set {i}"
    
    # If multiprocessing is working, parallel should be faster than sequential
    # But only enforce this on systems with multiple cores
    import multiprocessing
    if multiprocessing.cpu_count() > 1:
        assert par_time < seq_time, "Parallel execution should be faster with multiple cores"

@pytest.mark.performance
@pytest.mark.slow
def test_backtester_benchmark():
    """Run a detailed benchmark of the backtester components."""
    # Skip on CI to avoid long-running tests
    if os.environ.get('CI') == 'true':
        pytest.skip("Skipping slow benchmark test on CI")
    
    # Create synthetic data
    bars = 50000
    dates = pd.date_range(start='2020-01-01', periods=bars, freq='5min')
    data = pd.DataFrame({
        'Open': np.random.normal(100, 1, bars),
        'High': np.random.normal(101, 1, bars),
        'Low': np.random.normal(99, 1, bars),
        'Close': np.random.normal(100.5, 1, bars),
        'Volume': np.random.normal(50000, 10000, bars)
    }, index=dates)
    
    # Add indicators
    data['EMA_9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
    data['BB_Upper'] = data['Close'].rolling(window=20).mean() + 2 * data['Close'].rolling(window=20).std()
    data['BB_Lower'] = data['Close'].rolling(window=20).mean() - 2 * data['Close'].rolling(window=20).std()
    
    # Simple strategy function
    def sample_strategy(prepared_data, params):
        common_data = prepared_data['_common']
        total_bars = common_data['total_bars']
        
        # Main timeframe data
        main_tf = next(tf for tf in prepared_data.keys() if tf != '_common')
        closes = prepared_data[main_tf]['close']
        ema9 = prepared_data[main_tf].get('ema_9', np.zeros_like(closes))
        ema20 = prepared_data[main_tf].get('ema_20', np.zeros_like(closes))
        bb_upper = prepared_data[main_tf].get('bb_upper', np.zeros_like(closes))
        bb_lower = prepared_data[main_tf].get('bb_lower', np.zeros_like(closes))
        
        # Date mapping
        date_indices = prepared_data[main_tf]['date_indices']
        
        # Initialize signals
        signals = np.zeros((total_bars, 3))  # [entry, exit, direction]
        
        # Generate signals (combination of EMA crossover and Bollinger Bands)
        for i in range(20, total_bars):  # Skip first bars for indicator warmup
            price_idx = date_indices[i]
            if price_idx <= 0 or price_idx >= len(closes) - 1:
                continue
                
            price = closes[price_idx]
            prev_price = closes[price_idx-1]
            
            # Long entry: EMA9 crosses above EMA20 and price is near lower Bollinger Band
            if (ema9[price_idx] > ema20[price_idx] and ema9[price_idx-1] <= ema20[price_idx-1] and
                price < bb_lower[price_idx] * 1.01):
                signals[i, 0] = 1  # Entry
                signals[i, 2] = 1  # Long
            
            # Long exit: Price crosses above upper Bollinger Band
            elif signals[i-1, 2] == 1 and price > bb_upper[price_idx] and prev_price <= bb_upper[price_idx-1]:
                signals[i, 1] = 1  # Exit
            
            # Short entry: EMA9 crosses below EMA20 and price is near upper Bollinger Band
            elif (ema9[price_idx] < ema20[price_idx] and ema9[price_idx-1] >= ema20[price_idx-1] and
                 price > bb_upper[price_idx] * 0.99):
                signals[i, 0] = 1  # Entry
                signals[i, 2] = -1  # Short
            
            # Short exit: Price crosses below lower Bollinger Band
            elif signals[i-1, 2] == -1 and price < bb_lower[price_idx] and prev_price >= bb_lower[price_idx-1]:
                signals[i, 1] = 1  # Exit
        
        return signals
    
    data_dict = {'5min': data}
    
    # Run benchmark with Numba
    backtester_numba = OptimizedBacktester(
        use_numba=True, 
        use_multiprocessing=False,
        initial_capital=100000,
        commission=0.001,
        slippage=0.001
    )
    numba_benchmark = backtester_numba.benchmark(data_dict, sample_strategy)
    
    # Run benchmark without Numba
    backtester_python = OptimizedBacktester(
        use_numba=False, 
        use_multiprocessing=False,
        initial_capital=100000,
        commission=0.001,
        slippage=0.001
    )
    python_benchmark = backtester_python.benchmark(data_dict, sample_strategy)
    
    # Print results
    print("\nDetailed Benchmark Results:")
    print("\nNumba JIT:")
    for step, time_taken in numba_benchmark.items():
        print(f"  {step}: {time_taken:.4f}s")
    
    print("\nPython:")
    for step, time_taken in python_benchmark.items():
        print(f"  {step}: {time_taken:.4f}s")
    
    print("\nSpeedup:")
    for step in numba_benchmark:
        if step in python_benchmark and python_benchmark[step] > 0:
            speedup = python_benchmark[step] / numba_benchmark[step]
            print(f"  {step}: {speedup:.2f}x")
    
    # Create bar chart comparing times
    plt.figure(figsize=(12, 6))
    steps = list(numba_benchmark.keys())
    numba_times = [numba_benchmark[s] for s in steps]
    python_times = [python_benchmark[s] for s in steps]
    
    x = np.arange(len(steps))
    width = 0.35
    
    plt.bar(x - width/2, numba_times, width, label='Numba JIT')
    plt.bar(x + width/2, python_times, width, label='Python')
    
    plt.xlabel('Processing Step')
    plt.ylabel('Time (s)')
    plt.title('Backtester Component Performance')
    plt.xticks(x, steps, rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot
    plt.savefig('./results/performance/component_benchmark.png')
    
    # Assert Numba is faster overall
    assert numba_benchmark['total'] < python_benchmark['total'], "Numba should be faster overall" 