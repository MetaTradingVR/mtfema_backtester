class Optimizer:
    """
    Strategy parameter optimizer for the MT 9 EMA Backtester.
    """
    
    def __init__(self, strategy_class, param_grid, data_path, initial_capital=10000.0,
                optimization_target='sharpe_ratio', n_jobs=1):
        """
        Initialize the optimizer.
        
        Args:
            strategy_class: Strategy class to optimize
            param_grid: Dictionary of parameter names and lists of values to test
            data_path: Path to data file
            initial_capital: Initial capital amount
            optimization_target: Metric to optimize ('sharpe_ratio', 'total_return', etc.)
            n_jobs: Number of parallel jobs to run (-1 for all available cores)
        """
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.data_path = data_path
        self.initial_capital = initial_capital
        self.optimization_target = optimization_target
        self.n_jobs = n_jobs
        
        # Generate parameter combinations
        self.param_combinations = self._generate_param_combinations()
        
        # Results storage
        self.results = []
        
        logger.info(f"Optimizer initialized with {len(self.param_combinations)} parameter combinations")
    
    def _generate_param_combinations(self):
        """
        Generate all combinations of parameters to test.
        
        Returns:
            List of parameter dictionaries
        """
        import itertools
        
        # Get parameter names and values
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        
        # Generate all combinations
        combinations = list(itertools.product(*param_values))
        
        # Convert to list of dictionaries
        param_dicts = []
        for combo in combinations:
            param_dict = {name: value for name, value in zip(param_names, combo)}
            param_dicts.append(param_dict)
        
        return param_dicts
    
    def _evaluate_parameters(self, params):
        """
        Evaluate a single set of parameters.
        
        Args:
            params: Parameter dictionary
            
        Returns:
            Tuple of (params, result_metrics)
        """
        # Create strategy with these parameters
        strategy = self.strategy_class(**params)
        
        # Create backtester
        backtester = Backtester(
            strategy=strategy,
            data_source="csv",
            data_path=self.data_path,
            initial_capital=self.initial_capital
        )
        
        # Run backtest
        results = backtester.run()
        
        if results is None:
            logger.warning(f"Backtest failed for parameters: {params}")
            return params, None
        
        # Extract the target metric
        if self.optimization_target in results.metrics:
            target_value = results.metrics[self.optimization_target]
        else:
            logger.warning(f"Optimization target '{self.optimization_target}' not found in results metrics")
            target_value = 0
        
        return params, {
            'target_value': target_value,
            'metrics': results.metrics,
            'params': params
        }
    
    def run(self):
        """
        Run the optimization process.
        
        Returns:
            OptimizationResults object
        """
        logger.info(f"Starting optimization with target: {self.optimization_target}")
        
        # Check if we can use parallel processing
        if self.n_jobs != 1:
            try:
                from concurrent.futures import ProcessPoolExecutor
                import multiprocessing
                
                # Determine number of workers
                if self.n_jobs == -1:
                    n_workers = multiprocessing.cpu_count()
                else:
                    n_workers = min(self.n_jobs, multiprocessing.cpu_count())
                
                logger.info(f"Running optimization in parallel with {n_workers} workers")
                
                # Run evaluations in parallel
                with ProcessPoolExecutor(max_workers=n_workers) as executor:
                    results = list(executor.map(self._evaluate_parameters, self.param_combinations))
                
                # Filter out failed evaluations
                self.results = [r for _, r in results if r is not None]
                
            except ImportError:
                logger.warning("Could not import parallel processing modules, falling back to sequential execution")
                self._run_sequential()
        else:
            # Run sequentially
            self._run_sequential()
        
        # Sort results by target value (descending)
        self.results.sort(key=lambda x: x['target_value'], reverse=True)
        
        logger.info(f"Optimization completed. Best {self.optimization_target}: {self.results[0]['target_value']}")
        
        return OptimizationResults(self.results, self.optimization_target)
    
    def _run_sequential(self):
        """Run the optimization sequentially."""
        logger.info("Running optimization sequentially")
        
        total_params = len(self.param_combinations)
        
        for i, params in enumerate(self.param_combinations):
            logger.info(f"Evaluating parameters {i+1}/{total_params}: {params}")
            
            _, result = self._evaluate_parameters(params)
            
            if result is not None:
                self.results.append(result)


class OptimizationResults:
    """
    Container for optimization results with analysis methods.
    """
    
    def __init__(self, results, target_metric):
        """
        Initialize optimization results.
        
        Args:
            results: List of result dictionaries
            target_metric: The metric that was optimized
        """
        self.results = results
        self.target_metric = target_metric
    
    def get_best_parameters(self):
        """
        Get the best parameter set.
        
        Returns:
            Dictionary of best parameters
        """
        if not self.results:
            return {}
            
        return self.results[0]['params']
    
    def get_top_parameters(self, n=5):
        """
        Get the top N parameter sets.
        
        Args:
            n: Number of top results to return
            
        Returns:
            List of top parameter dictionaries
        """
        if not self.results:
            return []
            
        return [result['params'] for result in self.results[:n]]
    
    def summary(self):
        """
        Generate a summary of optimization results.
        
        Returns:
            Formatted string with optimization summary
        """
        if not self.results:
            return "No optimization results available"
            
        lines = []
        lines.append("=" * 60)
        lines.append("OPTIMIZATION RESULTS SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Target Metric: {self.target_metric}")
        lines.append(f"Total Parameter Combinations: {len(self.results)}")
        lines.append("")
        
        # Top 5 results
        lines.append("TOP 5 PARAMETER SETS")
        lines.append("-" * 60)
        
        for i, result in enumerate(self.results[:5]):
            lines.append(f"Rank {i+1}: {self.target_metric} = {result['target_value']}")
            for param, value in result['params'].items():
                lines.append(f"  {param}: {value}")
            lines.append("")
        
        # Parameter importance
        lines.append("PARAMETER IMPORTANCE")
        lines.append("-" * 60)
        
        param_importance = self._calculate_parameter_importance()
        for param, importance in param_importance.items():
            lines.append(f"{param}: {importance:.2f}")
        
        return "\n".join(lines)
    
    def _calculate_parameter_importance(self):
        """
        Calculate a simple measure of parameter importance.
        
        Returns:
            Dictionary of parameter names and importance scores
        """
        if not self.results or len(self.results) < 2:
            return {}
            
        # Get all parameter names
        all_params = set()
        for result in self.results:
            all_params.update(result['params'].keys())
        
        # Calculate importance for each parameter
        importance = {}
        
        for param in all_params:
            # Group results by parameter value
            values = {}
            
            for result in self.results:
                if param in result['params']:
                    value = result['params'][param]
                    if value not in values:
                        values[value] = []
                    values[value].append(result['target_value'])
            
            # Calculate average performance for each value
            avg_performance = {value: sum(perfs)/len(perfs) for value, perfs in values.items()}
            
            # Calculate variance in performance across different values
            if len(avg_performance) > 1:
                variance = max(avg_performance.values()) - min(avg_performance.values())
            else:
                variance = 0
            
            importance[param] = variance
        
        # Normalize importance scores
        max_importance = max(importance.values()) if importance else 1
        if max_importance > 0:
            importance = {param: score/max_importance for param, score in importance.items()}
        
        # Sort by importance (descending)
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return importance
    
    def plot_parameter_impact(self, parameter):
        """
        Plot the impact of a parameter on the target metric.
        
        Args:
            parameter: Parameter name to analyze
        """
        try:
            import matplotlib.pyplot as plt
            
            # Extract parameter values and corresponding target metric values
            param_values = []
            target_values = []
            
            for result in self.results:
                if parameter in result['params']:
                    param_values.append(result['params'][parameter])
                    target_values.append(result['target_value'])
            
            # Group by parameter value
            grouped_values = {}
            for param, target in zip(param_values, target_values):
                if param not in grouped_values:
                    grouped_values[param] = []
                grouped_values[param].append(target)
            
            # Calculate average for each parameter value
            avg_values = {param: sum(targets)/len(targets) for param, targets in grouped_values.items()}
            
            # Sort by parameter value
            sorted_items = sorted(avg_values.items())
            x_values = [item[0] for item in sorted_items]
            y_values = [item[1] for item in sorted_items]
            
            # Create plot
            plt.figure(figsize=(10, 6))
            plt.plot(x_values, y_values, 'o-')
            plt.title(f'Impact of {parameter} on {self.target_metric}')
            plt.xlabel(parameter)
            plt.ylabel(self.target_metric)
            plt.grid(True)
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            logger.warning("Matplotlib not available. Cannot plot parameter impact.")
