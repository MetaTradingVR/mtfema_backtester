"""
Test script for the optimization framework.

This script runs a test of the parameter optimization system for
the MT 9 EMA Extension Strategy.
"""

import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

from mtfema_backtester.backtester import Optimizer
from mtfema_backtester.strategy.mtfema_strategy import MTFEMAStrategy
from mtfema_backtester.utils.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_optimization_test():
    """Run a test of the optimization framework."""
    logger.info("Starting optimization test")
    
    # Create performance monitor
    monitor = PerformanceMonitor('optimization_test')
    
    # Define parameter grid
    param_grid = {
        'ema_period': [9, 13, 21],
        'extension_threshold': [0.5, 1.0, 1.5, 2.0],
        'reclamation_threshold': [0.3, 0.5, 0.7],
        'use_volume_confirmation': [False, True],
        'atr_period': [14, 21],
    }
    
    # Calculate total combinations
    import itertools
    total_combinations = 1
    for values in param_grid.values():
        total_combinations *= len(values)
    logger.info(f"Testing {total_combinations} parameter combinations")
    
    # Define test data path
    data_path = Path("data/test_data.csv")
    
    # Make sure data exists
    if not data_path.exists():
        logger.error(f"Test data file not found: {data_path}")
        return
    
    # Create optimizer
    with monitor.measure_performance('optimization'):
        optimizer = Optimizer(
            strategy_class=MTFEMAStrategy,
            param_grid=param_grid,
            data_path=data_path,
            initial_capital=10000.0,
            optimization_target='sharpe_ratio',
            n_jobs=-1  # Use all available cores
        )
        
        # Run optimization
        logger.info("Running optimization...")
        results = optimizer.run()
        
        # Print top results
        logger.info("Top 5 parameter sets:")
        for i, params in enumerate(results.get_top_parameters(5)):
            metrics = results.get_parameter_metrics(params)
            logger.info(f"{i+1}. Parameters: {params}")
            logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            logger.info(f"   Total Return: {metrics['total_return']:.2%}")
            logger.info(f"   Win Rate: {metrics['win_rate']:.2%}")
            logger.info(f"   Profit Factor: {metrics['profit_factor']:.2f}")
            logger.info(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
        
        # Plot results
        logger.info("Generating optimization visualizations...")
        results.plot_parameter_importance()
        results.plot_parameter_distributions()
        
        # Save best parameters
        best_params = results.get_best_parameters()
        logger.info(f"Best parameters: {best_params}")
        
        # Optional: save to file
        import json
        with open("optimal_parameters.json", "w") as f:
            json.dump(best_params, f, indent=4)
        
    # Print performance stats
    logger.info(f"Optimization completed in {monitor.get_execution_time('optimization'):.2f} seconds")
    
if __name__ == "__main__":
    run_optimization_test()
