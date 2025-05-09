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
        """Save all results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory with timestamp
        results_dir = self.output_dir / f"results_{timestamp}"
        results_dir.mkdir(exist_ok=True, parents=True)
        
        # Save all results
        all_results_file = results_dir / "all_results.json"
        
        # Prepare results for JSON serialization
        serializable_results = []
        for result in self.results:
            # Convert numpy values to Python native types
            cleaned_result = {
                'params': {k: self._make_serializable(v) for k, v in result['params'].items()},
                'metrics': {k: self._make_serializable(v) for k, v in result['metrics'].items()}
            }
            serializable_results.append(cleaned_result)
            
        with open(all_results_file, 'w') as f:
            json.dump(serializable_results, f, indent=4)
            
        # Save best result
        if self.best_result:
            best_result_file = results_dir / "best_result.json"
            cleaned_best = {
                'params': {k: self._make_serializable(v) for k, v in self.best_result['params'].items()},
                'metrics': {k: self._make_serializable(v) for k, v in self.best_result['metrics'].items()}
            }
            with open(best_result_file, 'w') as f:
                json.dump(cleaned_best, f, indent=4)
        
        # Save parameter grid
        param_grid_file = results_dir / "param_grid.json"
        with open(param_grid_file, 'w') as f:
            json.dump(self.param_grid, f, indent=4)
            
        logger.info(f"Results saved to {results_dir}")
        
        # Create visualizations if the visualization module is available
        try:
            from mtfema_backtester.optimization.visualization import visualize_optimization_results
            
            # Create visualization directory
            viz_dir = results_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True, parents=True)
            
            # Generate visualizations
            visualize_optimization_results(
                results=self.results,
                target_metric=self.optimization_target,
                output_dir=str(viz_dir)
            )
            
            logger.info(f"Optimization visualizations created in {viz_dir}")
            
        except ImportError:
            logger.warning("Visualization module not available. Skipping visualization generation.")

    def _make_serializable(self, value):
        """Make a value JSON serializable."""
        if isinstance(value, np.integer):
            return int(value)
        elif isinstance(value, np.floating):
            return float(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, list):
            return [self._make_serializable(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._make_serializable(v) for k, v in value.items()}
        else:
            return value
            
    def create_heatmap(self, param1: str, param2: str, metric: str = None) -> Dict:
        """
        Create a heatmap of two parameters' effect on a metric.
        
        Args:
            param1: First parameter to vary
            param2: Second parameter to vary
            metric: Metric to measure (defaults to optimization_target)
            
        Returns:
            Dictionary with heatmap data:
            - x_values: List of values for param1
            - y_values: List of values for param2
            - z_values: 2D array of metric values
        """
        if metric is None:
            metric = self.optimization_target
            
        metric_key = f"metrics.{metric}"
        
        # Extract values for all three parameters
        data = []
        for result in self.results:
            if metric not in result['metrics']:
                logger.warning(f"Metric {metric} not found in result")
                continue
                
            # Get parameter values
            p1_value = self._get_nested_param(result['params'], param1)
            p2_value = self._get_nested_param(result['params'], param2)
            
            if p1_value is None or p2_value is None:
                logger.warning(f"Parameters {param1} or {param2} not found in result")
                continue
                
            data.append({
                'p1': p1_value,
                'p2': p2_value,
                'metric': result['metrics'][metric]
            })
            
        if not data:
            logger.warning("No valid data for heatmap")
            return {}
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Get unique values for each parameter
        p1_values = sorted(df['p1'].unique())
        p2_values = sorted(df['p2'].unique())
        
        # Handle case where values are not numeric
        if not p1_values or not p2_values:
            logger.warning("Not enough unique values for parameters")
            return {}
            
        # Create 2D grid for heatmap
        z_values = np.zeros((len(p2_values), len(p1_values)))
        z_values.fill(np.nan)
        
        # Fill in grid with average metric values
        for i, p2_val in enumerate(p2_values):
            for j, p1_val in enumerate(p1_values):
                mask = (df['p1'] == p1_val) & (df['p2'] == p2_val)
                if mask.any():
                    z_values[i, j] = df.loc[mask, 'metric'].mean()
        
        return {
            'x_values': p1_values,
            'y_values': p2_values,
            'z_values': z_values
        }
        
    def _get_nested_param(self, params, param_path):
        """Get a parameter value from a nested path."""
        if param_path in params:
            return params[param_path]
            
        # Try splitting the path
        parts = param_path.split('.')
        if len(parts) == 1:
            return None
            
        # Navigate down the path
        value = params
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
                
        return value
        
    def get_top_n_results(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top N results.
        
        Args:
            n: Number of top results to return
            
        Returns:
            List of result dictionaries with params and metrics
        """
        if not self.results:
            return []
            
        # Sort by optimization target (descending)
        sorted_results = sorted(
            self.results, 
            key=lambda x: x['metrics'].get(self.optimization_target, float('-inf')), 
            reverse=True
        )
        
        # Return top N
        return sorted_results[:n]
        
    def get_param_importance(self) -> Dict[str, float]:
        """
        Calculate parameter importance based on correlation with optimization target.
        
        Returns:
            Dictionary mapping parameter names to importance scores
        """
        # Convert results to DataFrame
        data = []
        
        for result in self.results:
            row = {}
            
            # Flatten parameters
            for param_name, param_value in result['params'].items():
                # Skip non-numeric parameters
                if not isinstance(param_value, (int, float, np.number)):
                    continue
                row[param_name] = param_value
                
            # Add optimization target
            if self.optimization_target in result['metrics']:
                row[self.optimization_target] = result['metrics'][self.optimization_target]
                data.append(row)
                
        if not data:
            logger.warning("No valid data for parameter importance calculation")
            return {}
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Calculate correlation with optimization target
        importance = {}
        for col in df.columns:
            if col == self.optimization_target:
                continue
                
            # Skip columns with only one unique value
            if df[col].nunique() <= 1:
                continue
                
            try:
                corr = df[[col, self.optimization_target]].corr().iloc[0, 1]
                # Use absolute correlation as importance
                importance[col] = abs(corr)
            except Exception as e:
                logger.warning(f"Error calculating correlation for {col}: {str(e)}")
                
        # Sort by importance
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return importance
        
    def visualize_results(self, output_dir: str = None) -> None:
        """
        Create comprehensive visualizations for optimization results.
        
        Args:
            output_dir: Directory to save visualizations (defaults to self.output_dir / "visualizations")
        """
        if not output_dir:
            output_dir = str(self.output_dir / "visualizations")
            
        try:
            from mtfema_backtester.optimization.visualization import visualize_optimization_results
            
            # Create visualization directory
            viz_dir = Path(output_dir)
            viz_dir.mkdir(exist_ok=True, parents=True)
            
            # Generate visualizations
            visualize_optimization_results(
                results=self.results,
                target_metric=self.optimization_target,
                output_dir=str(viz_dir)
            )
            
            logger.info(f"Optimization visualizations created in {viz_dir}")
            
        except ImportError:
            logger.warning("Visualization module not available. Skipping visualization generation.")
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            
    def run_bayesian_search(self, n_calls=50, surrogate_model='GP', 
                           acq_func='EI', n_initial_points=10, save_results=True):
        """
        Run Bayesian optimization search (placeholder method).
        
        This method requires the BayesianOptimizer class which will be implemented separately.
        
        Args:
            n_calls: Total number of function evaluations
            surrogate_model: Type of surrogate model ('GP', 'RF', or 'GBRT')
            acq_func: Acquisition function type ('EI', 'PI', 'LCB', etc.)
            n_initial_points: Number of initial random points
            save_results: Whether to save results
            
        Returns:
            Dictionary with best parameters and metrics
        """
        logger.warning("Bayesian optimization not directly supported in base Optimizer class.")
        logger.info("To use Bayesian optimization, use BayesianOptimizer class instead.")
        logger.info("Falling back to randomized search as a substitute.")
        
        return self.run_randomized_search(n_iter=n_calls, save_results=save_results)
