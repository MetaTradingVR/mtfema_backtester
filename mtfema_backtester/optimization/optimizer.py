"""
Parameter optimization framework for the MT 9 EMA Extension Strategy Backtester.

This module provides grid search and evolutionary optimization for strategy parameters.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import os
import json
import itertools
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import random
import time
from typing import Dict, List, Any, Callable, Tuple, Optional

logger = logging.getLogger(__name__)

class Optimizer:
    """
    Parameter optimization for trading strategies using various techniques.
    """
    
    def __init__(self, 
                 backtest_func: Callable, 
                 param_grid: Dict[str, List[Any]], 
                 data=None,
                 optimization_target: str = 'sharpe_ratio',
                 secondary_target: str = 'total_return_pct',
                 n_jobs: int = -1,
                 output_dir: str = "./optimization_results"):
        """
        Initialize the optimizer.
        
        Args:
            backtest_func: Function that runs a backtest with given parameters
                           Expected signature: backtest_func(params, data) -> (metrics, trades_df, equity_curve)
            param_grid: Dictionary of parameter names and values to optimize
            data: Data to pass to the backtest function (will be passed as is)
            optimization_target: Metric to optimize (must be returned in metrics dictionary)
            secondary_target: Secondary metric to use for tiebreakers
            n_jobs: Number of parallel jobs (-1 to use all available cores)
            output_dir: Directory to save optimization results
        """
        self.backtest_func = backtest_func
        self.param_grid = param_grid
        self.data = data
        self.optimization_target = optimization_target
        self.secondary_target = secondary_target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Determine number of jobs
        if n_jobs == -1:
            self.n_jobs = multiprocessing.cpu_count()
        else:
            self.n_jobs = min(n_jobs, multiprocessing.cpu_count())
            
        self.results = []
        self.best_result = None
        
        logger.info(f"Optimizer initialized with {self.count_total_combinations():,} parameter combinations")
        
    def count_total_combinations(self) -> int:
        """Count the total number of parameter combinations."""
        return np.prod([len(values) for values in self.param_grid.values()])
    
    def generate_param_combinations(self):
        """Generate all parameter combinations from the parameter grid."""
        # Extract parameter names and values
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        
        # Generate all combinations
        for values in itertools.product(*param_values):
            yield dict(zip(param_names, values))
            
    def run_backtest(self, params: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run a single backtest with given parameters.
        
        Args:
            params: Parameter set to test
            
        Returns:
            Tuple of (params, metrics)
        """
        try:
            start_time = time.time()
            
            # Run backtest
            metrics, trades_df, equity_curve = self.backtest_func(params, self.data)
            
            # Add execution time
            metrics['execution_time'] = time.time() - start_time
            
            return params, metrics
            
        except Exception as e:
            logger.error(f"Error running backtest with params {params}: {str(e)}")
            return params, {'error': str(e)}
            
    def run_grid_search(self, save_results: bool = True) -> Dict[str, Any]:
        """
        Run a grid search over all parameter combinations.
        
        Args:
            save_results: Whether to save results to disk
            
        Returns:
            Dictionary with best parameters and metrics
        """
        logger.info(f"Starting grid search with {self.n_jobs} workers")
        start_time = time.time()
        
        # Generate all parameter combinations
        param_combinations = list(self.generate_param_combinations())
        total_combinations = len(param_combinations)
        
        if total_combinations == 0:
            logger.warning("No parameter combinations to test")
            return None
            
        logger.info(f"Testing {total_combinations:,} parameter combinations")
        
        # Run backtests in parallel
        completed = 0
        self.results = []
        
        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = {executor.submit(self.run_backtest, params): params for params in param_combinations}
            
            for future in as_completed(futures):
                completed += 1
                params, metrics = future.result()
                
                # Skip failures
                if 'error' in metrics:
                    logger.warning(f"Failed run: {params}")
                    continue
                    
                self.results.append({
                    'params': params,
                    'metrics': metrics
                })
                
                # Log progress
                if completed % max(1, total_combinations // 20) == 0:
                    progress = completed / total_combinations * 100
                    elapsed = time.time() - start_time
                    remaining = (elapsed / completed) * (total_combinations - completed) if completed > 0 else 0
                    
                    logger.info(f"Progress: {progress:.1f}% ({completed:,}/{total_combinations:,}), "
                                f"Elapsed: {elapsed/60:.1f} min, Remaining: {remaining/60:.1f} min")
        
        # Find best result
        self.best_result = self._find_best_result()
        
        if save_results:
            self._save_results()
            
        total_time = time.time() - start_time
        logger.info(f"Grid search completed in {total_time/60:.1f} minutes. Tested {completed:,} combinations.")
        logger.info(f"Best parameters: {self.best_result['params']}")
        logger.info(f"Best {self.optimization_target}: {self.best_result['metrics'][self.optimization_target]}")
        
        return self.best_result
    
    def run_randomized_search(self, n_iter: int = 100, save_results: bool = True) -> Dict[str, Any]:
        """
        Run a randomized search over a subset of parameter combinations.
        
        Args:
            n_iter: Number of random combinations to test
            save_results: Whether to save results to disk
            
        Returns:
            Dictionary with best parameters and metrics
        """
        logger.info(f"Starting randomized search with {n_iter} iterations using {self.n_jobs} workers")
        start_time = time.time()
        
        # Generate all parameter combinations
        all_combinations = list(self.generate_param_combinations())
        total_combinations = len(all_combinations)
        
        if total_combinations == 0:
            logger.warning("No parameter combinations to test")
            return None
            
        # If n_iter > total combinations, just do a full grid search
        if n_iter >= total_combinations:
            logger.info(f"Randomized search with {n_iter} iterations exceeds total combinations ({total_combinations}). "
                       f"Running full grid search instead.")
            return self.run_grid_search(save_results)
            
        # Sample random combinations
        random.seed(42)  # For reproducibility
        param_combinations = random.sample(all_combinations, n_iter)
        
        logger.info(f"Sampled {n_iter} parameter combinations from {total_combinations:,} total possibilities")
        
        # Run backtests in parallel
        completed = 0
        self.results = []
        
        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = {executor.submit(self.run_backtest, params): params for params in param_combinations}
            
            for future in as_completed(futures):
                completed += 1
                params, metrics = future.result()
                
                # Skip failures
                if 'error' in metrics:
                    logger.warning(f"Failed run: {params}")
                    continue
                    
                self.results.append({
                    'params': params,
                    'metrics': metrics
                })
                
                # Log progress
                if completed % max(1, n_iter // 10) == 0:
                    progress = completed / n_iter * 100
                    elapsed = time.time() - start_time
                    remaining = (elapsed / completed) * (n_iter - completed) if completed > 0 else 0
                    
                    logger.info(f"Progress: {progress:.1f}% ({completed}/{n_iter}), "
                                f"Elapsed: {elapsed/60:.1f} min, Remaining: {remaining/60:.1f} min")
        
        # Find best result
        self.best_result = self._find_best_result()
        
        if save_results:
            self._save_results()
            
        total_time = time.time() - start_time
        logger.info(f"Randomized search completed in {total_time/60:.1f} minutes. Tested {completed} combinations.")
        logger.info(f"Best parameters: {self.best_result['params']}")
        logger.info(f"Best {self.optimization_target}: {self.best_result['metrics'][self.optimization_target]}")
        
        return self.best_result
    
    def _find_best_result(self) -> Dict[str, Any]:
        """Find the best result from the results list."""
        if not self.results:
            return None
            
        # Filter results that have the optimization target
        valid_results = [r for r in self.results if self.optimization_target in r['metrics']]
        
        if not valid_results:
            return None
            
        # Sort by optimization target (assume higher is better)
        sorted_results = sorted(
            valid_results, 
            key=lambda x: (
                x['metrics'].get(self.optimization_target, float('-inf')),
                x['metrics'].get(self.secondary_target, float('-inf'))
            ),
            reverse=True
        )
        
        return sorted_results[0]
    
    def _save_results(self):
        """Save optimization results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all results
        all_results_path = self.output_dir / f"optimization_results_{timestamp}.json"
        
        # Convert results to saveable format
        saveable_results = []
        for result in self.results:
            saveable_result = {
                'params': result['params'],
                'metrics': {k: v for k, v in result['metrics'].items() if isinstance(v, (int, float, str, bool))}
            }
            saveable_results.append(saveable_result)
        
        # Save all results
        with open(all_results_path, 'w') as f:
            json.dump(saveable_results, f, indent=2)
            
        logger.info(f"Saved all optimization results to {all_results_path}")
        
        # Save best parameters
        if self.best_result:
            best_params_path = self.output_dir / f"best_params_{timestamp}.json"
            
            with open(best_params_path, 'w') as f:
                json.dump(self.best_result['params'], f, indent=2)
                
            logger.info(f"Saved best parameters to {best_params_path}")
            
        # Create optimization summary
        summary = {
            'timestamp': timestamp,
            'total_combinations_tested': len(self.results),
            'optimization_target': self.optimization_target,
            'secondary_target': self.secondary_target,
            'best_params': self.best_result['params'] if self.best_result else None,
            'best_metrics': self.best_result['metrics'] if self.best_result else None,
            'param_grid': self.param_grid
        }
        
        summary_path = self.output_dir / f"optimization_summary_{timestamp}.json"
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Saved optimization summary to {summary_path}")
    
    def create_heatmap(self, param1: str, param2: str, metric: str = None) -> Dict:
        """
        Create a heatmap of two parameters versus a metric.
        
        Args:
            param1: First parameter to use for heatmap
            param2: Second parameter to use for heatmap
            metric: Metric to visualize (defaults to optimization_target)
            
        Returns:
            Dictionary with heatmap data ready for plotting
        """
        if not self.results:
            logger.warning("No results available for heatmap")
            return None
            
        if metric is None:
            metric = self.optimization_target
            
        # Extract unique parameter values
        param1_values = sorted(list(set([r['params'].get(param1) for r in self.results if param1 in r['params']])))
        param2_values = sorted(list(set([r['params'].get(param2) for r in self.results if param2 in r['params']])))
        
        if not param1_values or not param2_values:
            logger.warning(f"Parameters {param1} and/or {param2} not found in results")
            return None
            
        # Create empty grid
        grid = np.zeros((len(param1_values), len(param2_values)))
        grid.fill(np.nan)
        
        # Fill grid with metric values
        for result in self.results:
            if param1 in result['params'] and param2 in result['params'] and metric in result['metrics']:
                p1_idx = param1_values.index(result['params'][param1])
                p2_idx = param2_values.index(result['params'][param2])
                grid[p1_idx, p2_idx] = result['metrics'][metric]
        
        return {
            'z': grid.tolist(),
            'x': param2_values,
            'y': param1_values,
            'metric': metric
        }
    
    def get_top_n_results(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top N parameter sets by the optimization target.
        
        Args:
            n: Number of top results to return
            
        Returns:
            List of top N results
        """
        if not self.results:
            return []
            
        # Filter results that have the optimization target
        valid_results = [r for r in self.results if self.optimization_target in r['metrics']]
        
        # Sort by optimization target (assume higher is better)
        sorted_results = sorted(
            valid_results, 
            key=lambda x: x['metrics'].get(self.optimization_target, float('-inf')),
            reverse=True
        )
        
        return sorted_results[:n]
    
    def get_param_importance(self) -> Dict[str, float]:
        """
        Estimate parameter importance based on correlation with the optimization target.
        
        Returns:
            Dictionary of parameter importance scores
        """
        if not self.results:
            return {}
            
        # Prepare data for correlation analysis
        data = []
        for result in self.results:
            if self.optimization_target in result['metrics']:
                row = {}
                # Add parameters
                for param, value in result['params'].items():
                    # Only use numeric parameters
                    if isinstance(value, (int, float)):
                        row[param] = value
                
                # Add target metric
                row[self.optimization_target] = result['metrics'][self.optimization_target]
                
                data.append(row)
        
        if not data:
            return {}
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Calculate correlations
        correlations = {}
        for param in df.columns:
            if param != self.optimization_target:
                correlation = df[param].corr(df[self.optimization_target])
                correlations[param] = abs(correlation)  # Use absolute value for importance
        
        # Normalize to sum to 1.0
        total = sum(correlations.values())
        if total > 0:
            for param in correlations:
                correlations[param] /= total
                
        return correlations
