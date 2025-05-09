"""
Bayesian Optimization implementation for parameter tuning.

This module extends the optimization framework with Bayesian methods
for more efficient parameter space exploration.
"""

import numpy as np
import logging
from pathlib import Path
import time
from typing import Dict, List, Any, Callable, Tuple, Optional

# Import base optimizer
from mtfema_backtester.optimization.optimizer import Optimizer

logger = logging.getLogger(__name__)

try:
    # Import scikit-optimize
    import skopt
    from skopt import gp_minimize, forest_minimize, gbrt_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    
    SKOPT_AVAILABLE = True
except ImportError:
    logger.warning("scikit-optimize not installed. Bayesian optimization will not be available.")
    logger.warning("Install with: pip install scikit-optimize")
    SKOPT_AVAILABLE = False

class BayesianOptimizer(Optimizer):
    """
    Bayesian Optimization for strategy parameters.
    
    This optimizer uses Gaussian Process regression to build a surrogate
    model of the objective function and efficiently explores the parameter space.
    """
    
    def __init__(self, 
                 backtest_func: Callable, 
                 param_grid: Dict[str, List[Any]], 
                 data=None,
                 optimization_target: str = 'sharpe_ratio',
                 secondary_target: str = 'total_return_pct',
                 n_jobs: int = -1,
                 output_dir: str = "./optimization_results",
                 surrogate_model: str = 'GP',
                 n_initial_points: int = 10,
                 acq_func: str = 'EI',
                 acq_optimizer: str = 'auto'):
        """
        Initialize the Bayesian optimizer.
        
        Args:
            backtest_func: Function that runs a backtest with given parameters
                           Expected signature: backtest_func(params, data) -> (metrics, trades_df, equity_curve)
            param_grid: Dictionary of parameter names and values to optimize
            data: Data to pass to the backtest function (will be passed as is)
            optimization_target: Metric to optimize (must be returned in metrics dictionary)
            secondary_target: Secondary metric to use for tiebreakers
            n_jobs: Number of parallel jobs (-1 to use all available cores)
            output_dir: Directory to save optimization results
            surrogate_model: Type of surrogate model ('GP', 'RF', or 'GBRT')
            n_initial_points: Number of initial random points before fitting model
            acq_func: Acquisition function ('EI', 'PI', 'LCB', 'gp_hedge')
            acq_optimizer: Optimizer for acquisition function ('auto', 'sampling', 'lbfgs')
        """
        # Initialize base optimizer
        super().__init__(
            backtest_func=backtest_func,
            param_grid=param_grid,
            data=data,
            optimization_target=optimization_target,
            secondary_target=secondary_target,
            n_jobs=n_jobs,
            output_dir=output_dir
        )
        
        # Bayesian optimization specific parameters
        self.surrogate_model = surrogate_model
        self.n_initial_points = n_initial_points
        self.acq_func = acq_func
        self.acq_optimizer = acq_optimizer
        
        # Track optimization results
        self.skopt_result = None
        
        # Check if scikit-optimize is available
        if not SKOPT_AVAILABLE:
            logger.warning("scikit-optimize not available. Bayesian optimization will fall back to random search.")
    
    def _convert_param_grid_to_space(self):
        """
        Convert parameter grid to skopt space definition.
        
        Returns:
            Tuple of (space, param_names)
            - space: List of skopt space objects (Real, Integer, Categorical)
            - param_names: List of parameter names
        """
        if not SKOPT_AVAILABLE:
            logger.error("scikit-optimize not available. Cannot convert parameter grid to space.")
            return None, []
            
        space = []
        param_names = []
        
        for param_name, param_values in self.param_grid.items():
            param_names.append(param_name)
            
            # Handle different parameter types
            if all(isinstance(v, (int, np.integer)) for v in param_values):
                # Integer parameter - use min/max from values
                space.append(Integer(min(param_values), max(param_values), name=param_name))
            elif all(isinstance(v, (float, np.floating)) for v in param_values):
                # Real/float parameter - use min/max from values
                space.append(Real(min(param_values), max(param_values), name=param_name))
            else:
                # Categorical parameter (or mixed types) - use as-is
                space.append(Categorical(param_values, name=param_name))
        
        return space, param_names
    
    def run_bayesian_optimization(self, n_calls=50, save_results=True):
        """
        Run Bayesian optimization for parameter tuning.
        
        Args:
            n_calls: Total number of function evaluations
            save_results: Whether to save results to disk
            
        Returns:
            Dictionary with best parameters and metrics
        """
        if not SKOPT_AVAILABLE:
            logger.warning("scikit-optimize not available. Falling back to randomized search.")
            return self.run_randomized_search(n_iter=n_calls, save_results=save_results)
            
        logger.info(f"Starting Bayesian optimization with {self.surrogate_model} surrogate model")
        logger.info(f"Using {self.acq_func} acquisition function with {self.n_initial_points} initial points")
        start_time = time.time()
        
        # Convert parameter grid to skopt space
        space, param_names = self._convert_param_grid_to_space()
        if not space:
            logger.error("Failed to convert parameter grid to space. Falling back to randomized search.")
            return self.run_randomized_search(n_iter=n_calls, save_results=save_results)
        
        # Define objective function wrapper for skopt
        @use_named_args(space)
        def objective_func(**params):
            # Convert to dictionary with parameter names
            param_dict = {name: params[name] for name in param_names}
            
            # Run backtest
            try:
                params_copy, metrics = self.run_backtest(param_dict)
                
                # Store result for later use
                if 'error' not in metrics and self.optimization_target in metrics:
                    self.results.append({
                        'params': param_dict,
                        'metrics': metrics
                    })
                
                # Return negative metric for minimization (skopt minimizes)
                if 'error' in metrics or self.optimization_target not in metrics:
                    return 0.0
                return -metrics[self.optimization_target]  # Negative because skopt minimizes
                
            except Exception as e:
                logger.error(f"Error in objective function: {str(e)}")
                return 0.0
        
        # Select surrogate model based on specified type
        if self.surrogate_model == 'RF':
            minimize_func = forest_minimize
            logger.info("Using Random Forest surrogate model")
        elif self.surrogate_model == 'GBRT':
            minimize_func = gbrt_minimize
            logger.info("Using Gradient Boosted Trees surrogate model")
        else:  # Default to GP
            minimize_func = gp_minimize
            logger.info("Using Gaussian Process surrogate model")
        
        # Clear previous results
        self.results = []
        
        # Run optimization
        try:
            self.skopt_result = minimize_func(
                objective_func, 
                space,
                n_calls=n_calls,
                n_initial_points=self.n_initial_points,
                acq_func=self.acq_func,
                acq_optimizer=self.acq_optimizer,
                n_jobs=self.n_jobs,
                random_state=42,
                verbose=True
            )
            
            # Convert result to our format
            best_params = {name: value for name, value 
                          in zip(param_names, self.skopt_result.x)}
            
            # Run backtest with best parameters to get full metrics
            _, best_metrics = self.run_backtest(best_params)
            
            # Create result dict
            best_result = {
                'params': best_params,
                'metrics': best_metrics
            }
            
            # Store as best result
            self.best_result = best_result
            
            # Save results if requested
            if save_results:
                self._save_results()
                self._save_bayesian_results()
                
            total_time = time.time() - start_time
            logger.info(f"Bayesian optimization completed in {total_time/60:.1f} minutes")
            logger.info(f"Best parameters: {self.best_result['params']}")
            logger.info(f"Best {self.optimization_target}: {self.best_result['metrics'][self.optimization_target]}")
            
            return best_result
            
        except Exception as e:
            logger.error(f"Error during Bayesian optimization: {str(e)}")
            logger.warning("Falling back to randomized search")
            return self.run_randomized_search(n_iter=n_calls, save_results=save_results)
    
    def _save_bayesian_results(self):
        """Save Bayesian-specific optimization results to disk."""
        try:
            if not SKOPT_AVAILABLE or self.skopt_result is None:
                return
                
            import joblib
            from datetime import datetime
            
            # Create output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = self.output_dir / f"bayesian_results_{timestamp}"
            results_dir.mkdir(exist_ok=True, parents=True)
            
            # Save skopt result object
            skopt_result_file = results_dir / "skopt_result.pkl"
            joblib.dump(self.skopt_result, skopt_result_file)
            
            # Create visualizations
            self.create_bayesian_visualizations(results_dir)
            
            logger.info(f"Bayesian optimization results saved to {results_dir}")
            
        except Exception as e:
            logger.error(f"Error saving Bayesian results: {str(e)}")
    
    def create_bayesian_visualizations(self, output_dir=None):
        """
        Create specialized visualizations for Bayesian optimization.
        
        Args:
            output_dir: Directory to save visualizations
        """
        if not SKOPT_AVAILABLE or self.skopt_result is None:
            logger.warning("Cannot create Bayesian visualizations: skopt not available or no results")
            return
            
        if not output_dir:
            output_dir = self.output_dir / "bayesian_viz"
            
        try:
            from pathlib import Path
            import matplotlib.pyplot as plt
            from skopt.plots import plot_convergence, plot_objective, plot_evaluations
            
            # Create directory
            viz_dir = Path(output_dir)
            viz_dir.mkdir(exist_ok=True, parents=True)
            
            # Plot convergence
            plt.figure(figsize=(10, 6))
            plot_convergence(self.skopt_result)
            plt.tight_layout()
            plt.savefig(viz_dir / "convergence.png")
            plt.close()
            
            # Plot objective function (up to 4 dimensions)
            dim_count = min(4, len(self.skopt_result.space.dimensions))
            if dim_count >= 2:  # Only plot if we have at least 2 dimensions
                plt.figure(figsize=(12, 10))
                plot_objective(self.skopt_result, dimensions=range(dim_count))
                plt.tight_layout()
                plt.savefig(viz_dir / "objective.png")
                plt.close()
            
            # Plot evaluations (up to 4 dimensions)
            if dim_count >= 2:
                plt.figure(figsize=(12, 10))
                plot_evaluations(self.skopt_result, dimensions=range(dim_count))
                plt.tight_layout()
                plt.savefig(viz_dir / "evaluations.png")
                plt.close()
            
            logger.info(f"Bayesian optimization visualizations saved to {viz_dir}")
            
        except Exception as e:
            logger.error(f"Error creating Bayesian visualizations: {str(e)}")
            
    def visualize_results(self, output_dir=None):
        """
        Create visualizations for optimization results.
        
        Overrides the base class method to include Bayesian-specific visualizations.
        
        Args:
            output_dir: Directory to save visualizations
        """
        # First call the parent class method to generate standard visualizations
        super().visualize_results(output_dir)
        
        # Then create Bayesian-specific visualizations if applicable
        if SKOPT_AVAILABLE and self.skopt_result is not None:
            if output_dir:
                bayesian_viz_dir = Path(output_dir) / "bayesian"
            else:
                bayesian_viz_dir = self.output_dir / "visualizations" / "bayesian"
                
            self.create_bayesian_visualizations(bayesian_viz_dir) 