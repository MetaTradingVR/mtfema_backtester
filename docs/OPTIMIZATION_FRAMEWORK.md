# Optimization Framework Documentation

## Overview

The MTFEMA Backtester optimization framework provides powerful tools for tuning strategy parameters to achieve optimal performance. It offers multiple optimization methods, comprehensive result tracking, and interactive visualizations to help understand parameter relationships and identify the most impactful parameters.

## Key Features

- Multiple optimization methods:
  - Grid search for exhaustive exploration
  - Randomized search for efficient exploration of large parameter spaces 
  - Bayesian optimization for intelligent parameter space exploration
- Parallel processing for improved performance
- Interactive visualizations for result analysis
- Parameter importance analysis
- Result storage and retrieval
- Graceful fallback mechanisms when optional dependencies are unavailable

## Components

### Core Optimizer

The `Optimizer` class (`mtfema_backtester/optimization/optimizer.py`) provides the foundation for parameter optimization with grid search and randomized search capabilities.

Key methods:
- `run_grid_search()`: Exhaustively tests all parameter combinations
- `run_randomized_search(n_iter)`: Randomly samples parameter combinations
- `get_top_n_results(n)`: Returns the best parameter combinations
- `get_param_importance()`: Analyzes parameter impact on performance
- `visualize_results()`: Creates comprehensive visualizations

### Bayesian Optimizer

The `BayesianOptimizer` class (`mtfema_backtester/optimization/bayesian_optimizer.py`) extends the core optimizer with Bayesian optimization methods using surrogate models.

Key features:
- Three surrogate models:
  - Gaussian Process (GP): Best for smooth objective functions
  - Random Forest (RF): Robust to noisy objective functions
  - Gradient Boosted Regression Trees (GBRT): Good for complex parameter spaces
- Multiple acquisition functions:
  - Expected Improvement (EI)
  - Probability of Improvement (PI)
  - Lower Confidence Bound (LCB)
- Specialized visualizations for convergence analysis

### Visualization Capabilities

The `OptimizationVisualizer` class (`mtfema_backtester/optimization/visualization.py`) provides rich visualization tools for analyzing optimization results.

Available visualizations:
- Parameter importance charts
- Parallel coordinates plots
- Parameter heatmaps
- Scatter matrix plots
- Comprehensive optimization dashboards

## Usage

### Basic Grid Search Example

```python
from mtfema_backtester.optimization.optimizer import Optimizer

# Define parameter grid
param_grid = {
    "ema.period": [9, 13, 21],
    "ema.extension_thresholds.1h": [0.8, 1.0, 1.2],
    "risk_management.reward_risk_ratio": [1.5, 2.0, 2.5, 3.0],
}

# Define backtest function (should return metrics, trades_df, equity_curve)
def run_backtest(params, data):
    # Run backtest with given parameters
    # ...
    return metrics, trades_df, equity_curve

# Create optimizer
optimizer = Optimizer(
    backtest_func=run_backtest,
    param_grid=param_grid,
    data=market_data,  # Your market data
    optimization_target='sharpe_ratio',
    secondary_target='total_return_pct',
    n_jobs=-1,  # Use all available cores
    output_dir="./optimization_results"
)

# Run grid search
best_result = optimizer.run_grid_search(save_results=True)

# Print best parameters
print("Best parameters:", best_result['params'])
print("Best Sharpe ratio:", best_result['metrics']['sharpe_ratio'])

# Analyze parameter importance
importance = optimizer.get_param_importance()
print("Parameter importance:", importance)

# Create visualizations
optimizer.visualize_results()
```

### Randomized Search Example

```python
# For large parameter spaces, use randomized search
n_iterations = 100
best_result = optimizer.run_randomized_search(n_iter=n_iterations, save_results=True)
```

### Bayesian Optimization Example

```python
from mtfema_backtester.optimization.bayesian_optimizer import BayesianOptimizer

# Create Bayesian optimizer
bayesian_optimizer = BayesianOptimizer(
    backtest_func=run_backtest,
    param_grid=param_grid,
    data=market_data,
    optimization_target='sharpe_ratio',
    secondary_target='total_return_pct',
    n_jobs=-1,
    output_dir="./optimization_results",
    surrogate_model='GP',  # 'GP', 'RF', or 'GBRT'
    n_initial_points=10,
    acq_func='EI'  # 'EI', 'PI', 'LCB'
)

# Run Bayesian optimization
best_result = bayesian_optimizer.run_bayesian_optimization(n_calls=50, save_results=True)
```

### Command Line Interface

The optimization framework can be accessed through the command-line interface using `run_nq_test.py`:

```bash
# Grid search optimization
python run_nq_test.py --mode optimize --optimizer grid --symbol SPY --start-date 2023-01-01 --end-date 2023-06-30

# Randomized search with 50 iterations
python run_nq_test.py --mode optimize --optimizer random --optimize-iterations 50 --symbol SPY

# Bayesian optimization with Gaussian Process surrogate model
python run_nq_test.py --mode optimize --optimizer bayesian --opt-surrogate GP --opt-acq-func EI --opt-initial-points 10 --symbol SPY
```

## Result Storage

Optimization results are stored in the `optimization_results` directory:

```
optimization_results/
├── results_20250816_143722/
│   ├── all_results.json         # All parameter combinations and metrics
│   ├── best_result.json         # Best parameter combination and metrics
│   ├── param_grid.json          # Original parameter grid definition
│   └── visualizations/          # Interactive visualizations
│       ├── parameter_importance.html
│       ├── parallel_coordinates.html
│       ├── scatter_matrix.html
│       ├── optimization_dashboard.html
│       └── heatmap_*.html
└── bayesian_results_20250816_144235/  # Bayesian-specific results
    ├── skopt_result.pkl         # scikit-optimize result object
    ├── convergence.png          # Convergence plot
    ├── objective.png            # Objective function plot
    └── evaluations.png          # Evaluations plot
```

## Best Practices

1. **Start with a small grid**: Begin optimization with a small parameter grid to ensure your backtesting function works correctly.

2. **Increase grid resolution near promising areas**: After identifying promising regions, refine your search with a denser grid around those areas.

3. **Consider computation resources**: Grid search can be computationally expensive. For large parameter spaces, start with randomized search and then refine with grid search or Bayesian optimization.

4. **Avoid overfitting**: Be cautious about optimizing too many parameters simultaneously, as this increases the risk of overfitting. Focus on the most impactful parameters first.

5. **Examine multiple metrics**: While optimization targets a primary metric, examine secondary metrics to ensure the strategy meets all requirements.

6. **Analyze parameter importance**: Use parameter importance analysis to understand which parameters have the most impact on performance.

7. **Use visualizations**: Leverage the visualization tools to gain insights into parameter relationships and identify patterns.

## Dependencies

The optimization framework requires:

- numpy
- pandas
- concurrent.futures (included in Python standard library)
- plotly (for visualizations)
- scikit-optimize (optional, for Bayesian optimization)

## Common Issues and Solutions

1. **Issue**: Optimization runs too slowly.  
   **Solution**: Reduce parameter grid size, use randomized search, or increase `n_jobs` to utilize more CPU cores.

2. **Issue**: "scikit-optimize not available" warning.  
   **Solution**: Install scikit-optimize with `pip install scikit-optimize` for Bayesian optimization capabilities.

3. **Issue**: Memory errors during parallel processing.  
   **Solution**: Reduce `n_jobs` parameter to limit concurrent processes.

4. **Issue**: Visualization errors.  
   **Solution**: Ensure plotly is installed with `pip install plotly`.

5. **Issue**: Optimization produces poor results.  
   **Solution**: Check that your backtesting function correctly calculates performance metrics, and try different optimization targets.

## API Reference

### Optimizer Class

```python
class Optimizer:
    def __init__(self, 
                 backtest_func, 
                 param_grid, 
                 data=None,
                 optimization_target='sharpe_ratio',
                 secondary_target='total_return_pct',
                 n_jobs=-1,
                 output_dir="./optimization_results"):
        """Initialize the optimizer."""
        
    def run_grid_search(self, save_results=True):
        """Run a grid search over all parameter combinations."""
        
    def run_randomized_search(self, n_iter=100, save_results=True):
        """Run a randomized search over a subset of parameter combinations."""
        
    def get_top_n_results(self, n=10):
        """Get the top N results."""
        
    def get_param_importance(self):
        """Calculate parameter importance based on correlation with optimization target."""
        
    def visualize_results(self, output_dir=None):
        """Create comprehensive visualizations for optimization results."""
```

### BayesianOptimizer Class

```python
class BayesianOptimizer(Optimizer):
    def __init__(self, 
                 backtest_func, 
                 param_grid, 
                 data=None,
                 optimization_target='sharpe_ratio',
                 secondary_target='total_return_pct',
                 n_jobs=-1,
                 output_dir="./optimization_results",
                 surrogate_model='GP',
                 n_initial_points=10,
                 acq_func='EI',
                 acq_optimizer='auto'):
        """Initialize the Bayesian optimizer."""
        
    def run_bayesian_optimization(self, n_calls=50, save_results=True):
        """Run Bayesian optimization for parameter tuning."""
        
    def create_bayesian_visualizations(self, output_dir=None):
        """Create specialized visualizations for Bayesian optimization."""
```

### OptimizationVisualizer Class

```python
class OptimizationVisualizer:
    def __init__(self, results, 
                 target_metric='sharpe_ratio',
                 output_dir="./optimization_viz"):
        """Initialize the visualization with optimization results."""
        
    def create_parameter_importance_chart(self, save=True):
        """Create a parameter importance chart."""
        
    def create_parallel_coordinates_plot(self, top_n=50, save=True):
        """Create a parallel coordinates plot for the top N parameter combinations."""
        
    def create_scatter_matrix(self, top_n=100, save=True):
        """Create a scatter matrix plot for the top N parameter combinations."""
        
    def create_parameter_heatmap(self, param1, param2, save=True):
        """Create a heatmap for two parameters."""
        
    def create_optimization_dashboard(self, top_n=50, save=True):
        """Create a comprehensive optimization dashboard."""
``` 