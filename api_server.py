"""
MT 9 EMA Backtester API Server

This module provides API endpoints for the MT 9 EMA Backtester dashboard.
It serves backtest results, optimization data, and live trading updates.
"""

import os
import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Note: The actual implementation uses sample data generators.
# In a production version, these would be real implementations.
# from mtfema_backtester.backtest import Backtest
# from mtfema_backtester.strategy import MT9EMAStrategy

# Import backtester modules that actually exist
from mtfema_backtester.backtest import execute_backtest, calculate_performance_metrics

# Import optimization modules
try:
    from mtfema_backtester.optimization.optimizer import Optimizer
    from mtfema_backtester.optimization.bayesian_optimizer import BayesianOptimizer, SKOPT_AVAILABLE
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    logging.warning("Optimization modules not available. Using sample data instead.")

# Import indicator modules
try:
    from mtfema_backtester.utils.indicators import Indicator, create_indicator, get_indicator_registry
    INDICATORS_AVAILABLE = True
except ImportError:
    INDICATORS_AVAILABLE = False
    logging.warning("Indicator modules not available. Using sample data instead.")

# Import pandas-ta for standard indicators
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
    logging.info("pandas-ta library successfully imported")
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logging.warning("pandas-ta library not available. Standard indicators will use sample data.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_server")

# Initialize FastAPI app
app = FastAPI(
    title="MT 9 EMA Backtester API",
    description="API server for the MT 9 EMA Backtester dashboard",
    version="1.0.0",
)

# Initialize app state
app.state.start_time = time.time()

# Add CORS middleware to allow requests from the Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models
class BacktestParams(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    params: Dict[str, Union[int, float, str]]

class BacktestResponse(BaseModel):
    id: str

class OptimizationParams(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    param_ranges: Dict[str, Dict[str, Union[int, float]]]
    metric: str = "total_return"
    method: str = "grid"  # "grid", "random", or "bayesian"
    iterations: Optional[int] = None  # For random and bayesian methods
    surrogate_model: Optional[str] = "GP"  # For bayesian: "GP", "RF", or "GBRT"
    acq_func: Optional[str] = "EI"  # For bayesian: "EI", "PI", "LCB"
    n_initial_points: Optional[int] = 10  # For bayesian

class OptimizationResponse(BaseModel):
    id: str

class OptimizationStatus(BaseModel):
    id: str
    status: str
    progress: Optional[float] = None
    eta_minutes: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

# Indicator data models
class IndicatorParameter(BaseModel):
    name: str
    type: str = "float"  # "int", "float", "string", "bool"
    default: Any
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    options: Optional[List[Any]] = None
    description: Optional[str] = None

class IndicatorInfo(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[IndicatorParameter] = []
    output_fields: List[str] = []
    built_in: bool = True

class CustomIndicatorCode(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[IndicatorParameter] = []
    code: str
    test_data: Optional[bool] = False  # If True, generate test data
    save: bool = True  # If True, save to registry

# Standard Indicator Models
class StandardIndicator(BaseModel):
    id: Optional[str] = None
    definition_id: str  # References standard indicator definition ID
    name: str
    parameters: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StandardIndicatorTestRequest(BaseModel):
    definition_id: str
    parameters: Dict[str, Any]
    test_data: bool = True
    include_price: bool = True

# Storage for backtest results and optimization results
# In a production app, this would use a database
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# Storage for custom indicators
INDICATORS_DIR = Path("indicators")
INDICATORS_DIR.mkdir(exist_ok=True)

# Storage for standard indicators
STANDARD_INDICATORS_DIR = Path("indicators/standard")
STANDARD_INDICATORS_DIR.mkdir(exist_ok=True, parents=True)

# Keep track of running backtests and optimizations
active_backtests: Dict[str, Dict[str, Any]] = {}
active_optimizations: Dict[str, Dict[str, Any]] = {}

# Define API endpoints

@app.get("/api/status")
async def get_server_status():
    """Get the current status of all server systems"""
    try:
        # Check the status of each major component
        status = {
            "server": {
                "status": "online",
                "version": "1.0.0",
                "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0
            },
            "components": {
                "backtesting": {
                    "status": "available",
                    "active_jobs": len(active_backtests)
                },
                "optimization": {
                    "status": "available" if OPTIMIZATION_AVAILABLE else "unavailable",
                    "active_jobs": len(active_optimizations)
                },
                "indicators": {
                    "status": "available" if INDICATORS_AVAILABLE else "unavailable",
                    "count": len(get_indicator_registry().list_indicators()) if INDICATORS_AVAILABLE else 0
                },
                "live_trading": {
                    "status": "disconnected"  # This would be updated in a real implementation
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Overall system status
        all_available = all(component["status"] in ["available", "online"] 
                           for system in status["components"].values() 
                           for component in [system] if isinstance(system, dict))
        
        status["overall_status"] = "healthy" if all_available else "degraded"
        
        return status
    except Exception as e:
        logger.error(f"Error getting server status: {str(e)}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/backtest/results")
async def get_backtest_results():
    """Get all backtest results"""
    try:
        results = []
        for file_path in RESULTS_DIR.glob("backtest_*.json"):
            with open(file_path, "r") as f:
                results.append(json.load(f))
        return results
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/{backtest_id}")
async def get_backtest_by_id(backtest_id: str):
    """Get a specific backtest result by ID"""
    try:
        file_path = RESULTS_DIR / f"backtest_{backtest_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        with open(file_path, "r") as f:
            return json.load(f)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backtest {backtest_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest/run", response_model=BacktestResponse)
async def run_backtest(params: BacktestParams, background_tasks: BackgroundTasks):
    """Run a new backtest"""
    backtest_id = str(uuid.uuid4())
    
    # Store the backtest params
    active_backtests[backtest_id] = {
        "status": "queued",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
    }
    
    # Run the backtest in the background
    background_tasks.add_task(run_backtest_task, backtest_id, params)
    
    return {"id": backtest_id}

@app.get("/api/backtest/status/{backtest_id}")
async def get_backtest_status(backtest_id: str):
    """Get the status of a running backtest"""
    if backtest_id in active_backtests:
        return active_backtests[backtest_id]
    
    # Check if it's completed
    file_path = RESULTS_DIR / f"backtest_{backtest_id}.json"
    if file_path.exists():
        return {"status": "completed"}
    
    raise HTTPException(status_code=404, detail="Backtest not found")

@app.get("/api/optimization/results")
async def get_optimization_results():
    """Get all optimization results"""
    try:
        results = []
        for file_path in RESULTS_DIR.glob("optimization_*.json"):
            with open(file_path, "r") as f:
                results.append(json.load(f))
        
        # Flatten results for easy consumption by the frontend
        flattened_results = []
        for opt_result in results:
            for result in opt_result.get("results", []):
                flattened_results.append({
                    "params": result.get("params", {}),
                    "metrics": result.get("metrics", {})
                })
        
        return flattened_results
    except Exception as e:
        logger.error(f"Error getting optimization results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/optimization/{optimization_id}")
async def get_optimization_by_id(optimization_id: str):
    """Get a specific optimization result by ID"""
    try:
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Optimization not found")
        
        with open(file_path, "r") as f:
            return json.load(f)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization {optimization_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimization/run", response_model=OptimizationResponse)
async def run_optimization(params: OptimizationParams, background_tasks: BackgroundTasks):
    """Run a new optimization"""
    optimization_id = str(uuid.uuid4())
    
    # Store the optimization params
    active_optimizations[optimization_id] = {
        "id": optimization_id,
        "status": "queued",
        "params": params.dict(),
        "progress": 0.0,
        "started_at": datetime.now().isoformat(),
    }
    
    # Run the optimization in the background
    background_tasks.add_task(run_optimization_task, optimization_id, params)
    
    return {"id": optimization_id}

@app.get("/api/optimization/status/{optimization_id}", response_model=OptimizationStatus)
async def get_optimization_status(optimization_id: str):
    """Get the status of a running optimization"""
    if optimization_id in active_optimizations:
        return active_optimizations[optimization_id]
    
    # Check if it's completed
    file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
    if file_path.exists():
        return {
            "id": optimization_id,
            "status": "completed",
            "progress": 100.0,
            "completed_at": datetime.now().isoformat()  # Actual completion time would be better
        }
    
    raise HTTPException(status_code=404, detail="Optimization not found")

@app.get("/api/optimization/methods")
async def get_optimization_methods():
    """Get available optimization methods and options"""
    methods = {
        "grid": {
            "description": "Exhaustive grid search of parameter space",
            "options": {}
        },
        "random": {
            "description": "Random sampling of parameter space",
            "options": {
                "iterations": "Number of random samples to evaluate"
            }
        }
    }
    
    # Add Bayesian optimization if available
    if OPTIMIZATION_AVAILABLE and SKOPT_AVAILABLE:
        methods["bayesian"] = {
            "description": "Bayesian optimization using surrogate models",
            "options": {
                "iterations": "Total number of evaluations",
                "surrogate_model": ["GP", "RF", "GBRT"],
                "acq_func": ["EI", "PI", "LCB"],
                "n_initial_points": "Number of initial random points"
            }
        }
    
    return methods

@app.get("/api/optimization/parameter-importance/{optimization_id}")
async def get_parameter_importance(optimization_id: str):
    """Get parameter importance analysis for an optimization run"""
    try:
        # Check if the optimization exists
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Optimization not found")
            
        # Load the optimization results
        with open(file_path, "r") as f:
            opt_results = json.load(f)
        
        # Extract all parameters and results
        params_list = []
        metrics_list = []
        
        for result in opt_results.get('results', []):
            params = result.get('params', {})
            metrics = result.get('metrics', {})
            
            if params and metrics:
                params_list.append(params)
                metrics_list.append(metrics)
        
        if not params_list:
            return {}
        
        # Convert to DataFrame for easier analysis
        import pandas as pd
        from scipy.stats import pearsonr
        
        # Create DataFrame with parameters
        params_df = pd.DataFrame(params_list)
        
        # Create DataFrame with target metric
        metrics_df = pd.DataFrame(metrics_list)
        
        # Get target metric (default to total_return if available)
        target_metric = opt_results.get('target_metric', 'total_return')
        if target_metric not in metrics_df.columns and len(metrics_df.columns) > 0:
            target_metric = metrics_df.columns[0]
        
        # Calculate correlations between parameters and target metric
        importance = {}
        for param in params_df.columns:
            try:
                # Calculate absolute correlation
                corr, _ = pearsonr(params_df[param], metrics_df[target_metric])
                importance[param] = abs(corr)
            except Exception:
                importance[param] = 0.0
        
        # Normalize to sum to 1
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        # Sort by importance
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parameter importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/optimization/heatmap")
async def get_parameter_heatmap(
    optimization_id: str,
    param1: str,
    param2: str,
    metric: str = "total_return"
):
    """Get heatmap data for two parameters"""
    try:
        # Check if the optimization exists
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Optimization not found")
        
        # Load the optimization results
        with open(file_path, "r") as f:
            opt_results = json.load(f)
        
        # Extract all parameters and results
        params_list = []
        metrics_list = []
        
        for result in opt_results.get('results', []):
            params = result.get('params', {})
            metrics = result.get('metrics', {})
            
            if params and metrics and param1 in params and param2 in params:
                params_list.append(params)
                metrics_list.append(metrics)
        
        if not params_list:
            return {
                "x_values": [],
                "y_values": [],
                "z_values": [],
                "x_label": param1,
                "y_label": param2,
                "metric": metric
            }
        
        # Convert to DataFrame for easier analysis
        import pandas as pd
        import numpy as np
        
        # Create DataFrame with parameters and target metric
        df = pd.DataFrame(params_list)
        for key, value in zip(metrics_list[0].keys(), zip(*[m.values() for m in metrics_list])):
            df[key] = value
        
        # Get unique values for each parameter
        x_values = sorted(df[param1].unique().tolist())
        y_values = sorted(df[param2].unique().tolist())
        
        # Create the z-value grid
        z_values = []
        for y in y_values:
            row = []
            for x in x_values:
                # Find matching entries
                matches = df[(df[param1] == x) & (df[param2] == y)]
                if not matches.empty and metric in matches.columns:
                    # Use average if multiple matches
                    value = matches[metric].mean()
                    row.append(round(float(value), 2))
                else:
                    # Use NaN for missing combinations
                    row.append(None)
            z_values.append(row)
        
        # Fill NaN values with interpolated values if possible
        z_array = np.array(z_values, dtype=float)
        mask = np.isnan(z_array)
        z_array_filled = z_array.copy()
        
        if not np.all(mask):  # If not all values are NaN
            # Simple interpolation by averaging neighbors
            for i in range(len(y_values)):
                for j in range(len(x_values)):
                    if np.isnan(z_array[i, j]):
                        neighbors = []
                        # Check all adjacent cells
                        for ni, nj in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]:
                            if 0 <= ni < len(y_values) and 0 <= nj < len(x_values):
                                if not np.isnan(z_array[ni, nj]):
                                    neighbors.append(z_array[ni, nj])
                        
                        if neighbors:  # If any valid neighbors
                            z_array_filled[i, j] = sum(neighbors) / len(neighbors)
        
        # Convert back to list format with rounding
        z_values = [[round(float(val), 2) if not np.isnan(val) else None for val in row] for row in z_array_filled]
        
        return {
            "x_values": x_values,
            "y_values": y_values,
            "z_values": z_values,
            "x_label": param1,
            "y_label": param2,
            "metric": metric
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parameter heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/optimization/parallel-coordinates/{optimization_id}")
async def get_parallel_coordinates_data(optimization_id: str, metric: str = "total_return"):
    """Get data formatted for parallel coordinates visualization"""
    try:
        # Check if the optimization exists
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Optimization not found")
        
        # Load the optimization results
        with open(file_path, "r") as f:
            opt_results = json.load(f)
        
        # Extract parameters and results
        results = []
        
        for result in opt_results.get('results', []):
            params = result.get('params', {})
            metrics = result.get('metrics', {})
            
            if params and metrics and metric in metrics:
                # Combine parameters and metrics into a single object
                item = {**params, metric: metrics[metric]}
                results.append(item)
        
        # Extract parameter names (excluding the metric)
        parameters = list(results[0].keys()) if results else []
        if metric in parameters:
            parameters.remove(metric)
        
        return {
            "results": results,
            "parameters": parameters,
            "metric": metric
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parallel coordinates data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/optimization/metrics/{optimization_id}")
async def get_optimization_metrics(optimization_id: str):
    """Get available metrics from an optimization result"""
    try:
        # Check if the optimization exists
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Optimization not found")
        
        # Load the optimization results
        with open(file_path, "r") as f:
            opt_results = json.load(f)
        
        # Extract metrics from first result (assuming all results have the same metrics)
        metrics = []
        if opt_results.get('results') and len(opt_results['results']) > 0:
            first_result = opt_results['results'][0]
            if 'metrics' in first_result:
                metrics = list(first_result['metrics'].keys())
        
        # Get the target metric if available
        target_metric = opt_results.get('target_metric')
        
        return {
            "metrics": metrics,
            "target_metric": target_metric
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimization/cancel/{optimization_id}", response_model=dict)
def cancel_optimization(optimization_id: str):
    """Cancel a running optimization"""
    if not OPTIMIZATION_AVAILABLE:
        return {"message": f"Optimization {optimization_id} cancelled (simulation)"}
    
    # In a real implementation, we would use the Optimizer class to cancel the optimization
    # For now, we'll just update the status file
    optimization_path = RESULTS_DIR / f"optimization_{optimization_id}_status.json"
    
    if not optimization_path.exists():
        raise HTTPException(status_code=404, detail=f"Optimization {optimization_id} not found")
    
    with open(optimization_path, "r") as f:
        status = json.load(f)
    
    status["status"] = "cancelled"
    status["completed_at"] = datetime.now().isoformat()
    
    with open(optimization_path, "w") as f:
        json.dump(status, f, indent=2)
    
    return {"message": f"Optimization {optimization_id} cancelled"}

# Indicator Management API Endpoints

@app.get("/api/indicators", response_model=List[IndicatorInfo])
def list_indicators():
    """List all available indicators"""
    if not INDICATORS_AVAILABLE:
        # Return sample indicators if the indicator module is not available
        return generate_sample_indicators()
    
    # Get the indicator registry and list all registered indicators
    registry = get_indicator_registry()
    indicators = []
    
    for indicator_name in registry.list_indicators():
        # Get indicator class
        indicator_class = registry.get_indicator_class(indicator_name)
        
        # Create a sample instance to inspect parameters
        try:
            sample_instance = indicator_class()
            params = []
            
            # Extract parameter info
            for param_name, param_value in sample_instance.params.items():
                param_type = "float"
                if isinstance(param_value, int):
                    param_type = "int"
                elif isinstance(param_value, str):
                    param_type = "string"
                elif isinstance(param_value, bool):
                    param_type = "bool"
                
                params.append(IndicatorParameter(
                    name=param_name,
                    type=param_type,
                    default=param_value
                ))
            
            # Determine if this is a built-in or custom indicator
            is_builtin = indicator_class.__module__.startswith('mtfema_backtester')
            
            # Create the indicator info
            indicator_info = IndicatorInfo(
                name=indicator_name,
                description=indicator_class.__doc__,
                parameters=params,
                built_in=is_builtin
            )
            
            indicators.append(indicator_info)
        except Exception as e:
            logger.error(f"Error inspecting indicator {indicator_name}: {str(e)}")
    
    return indicators

@app.post("/api/indicators/test", response_model=Dict[str, Any])
def test_indicator(indicator: CustomIndicatorCode):
    """Test a custom indicator with sample data"""
    if not INDICATORS_AVAILABLE:
        # Return sample test results
        return generate_sample_indicator_test(indicator.name)
    
    try:
        # Generate sample data for testing
        data = generate_sample_data_for_indicators()
        
        # If this is Python code that defines a class, we need to execute it
        # This is a security risk in production environments!
        # In a real app, we would use a sandboxed environment
        if "class" in indicator.code and "(Indicator)" in indicator.code:
            # Execute the code in a dictionary namespace
            namespace = {}
            exec(f"from mtfema_backtester.utils.indicators import Indicator\n{indicator.code}", namespace)
            
            # Find the indicator class in the namespace
            indicator_class = None
            for name, obj in namespace.items():
                if isinstance(obj, type) and issubclass(obj, Indicator) and obj != Indicator:
                    indicator_class = obj
                    break
            
            if indicator_class is None:
                raise ValueError("No Indicator subclass found in the provided code")
            
            # Create an instance and calculate
            params = {param.name: param.default for param in indicator.parameters}
            instance = indicator_class(**params)
            results = instance.calculate(data)
            
            # Get a preview of the results
            preview = {k: v.tail(10).tolist() for k, v in results.items()}
            
            # Optionally save to registry
            if indicator.save:
                registry = get_indicator_registry()
                registry.register(indicator.name, indicator_class)
                
                # Save the code to disk for persistence
                indicator_path = INDICATORS_DIR / f"{indicator.name}.py"
                with open(indicator_path, "w") as f:
                    f.write(indicator.code)
            
            return {
                "success": True,
                "message": "Indicator calculated successfully",
                "preview": preview
            }
        else:
            return {
                "success": False,
                "message": "The provided code does not contain a valid Indicator subclass"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error testing indicator: {str(e)}"
        }

@app.post("/api/indicators", response_model=Dict[str, Any])
def create_indicator(indicator: CustomIndicatorCode):
    """Create a new custom indicator"""
    if not INDICATORS_AVAILABLE:
        return {
            "success": True,
            "message": f"Indicator {indicator.name} created (simulation)"
        }
    
    try:
        # Check if the indicator already exists
        registry = get_indicator_registry()
        if indicator.name in registry.list_indicators():
            return {
                "success": False,
                "message": f"Indicator {indicator.name} already exists"
            }
        
        # Same logic as in test_indicator, but always save
        namespace = {}
        exec(f"from mtfema_backtester.utils.indicators import Indicator\n{indicator.code}", namespace)
        
        indicator_class = None
        for name, obj in namespace.items():
            if isinstance(obj, type) and issubclass(obj, Indicator) and obj != Indicator:
                indicator_class = obj
                break
        
        if indicator_class is None:
            raise ValueError("No Indicator subclass found in the provided code")
        
        # Register the indicator
        registry.register(indicator.name, indicator_class)
        
        # Save the code to disk for persistence
        indicator_path = INDICATORS_DIR / f"{indicator.name}.py"
        with open(indicator_path, "w") as f:
            f.write(indicator.code)
        
        return {
            "success": True,
            "message": f"Indicator {indicator.name} created successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating indicator: {str(e)}"
        }

@app.delete("/api/indicators/{indicator_name}", response_model=Dict[str, Any])
def delete_indicator(indicator_name: str):
    """Delete a custom indicator"""
    if not INDICATORS_AVAILABLE:
        return {
            "success": True,
            "message": f"Indicator {indicator_name} deleted (simulation)"
        }
    
    try:
        # Check if the indicator exists
        registry = get_indicator_registry()
        if indicator_name not in registry.list_indicators():
            return {
                "success": False,
                "message": f"Indicator {indicator_name} not found"
            }
        
        # Get the indicator class to check if it's built-in
        indicator_class = registry.get_indicator_class(indicator_name)
        is_builtin = indicator_class.__module__.startswith('mtfema_backtester')
        
        if is_builtin:
            return {
                "success": False,
                "message": f"Cannot delete built-in indicator {indicator_name}"
            }
        
        # Remove from registry
        registry.unregister(indicator_name)
        
        # Delete the file if it exists
        indicator_path = INDICATORS_DIR / f"{indicator_name}.py"
        if indicator_path.exists():
            indicator_path.unlink()
        
        return {
            "success": True,
            "message": f"Indicator {indicator_name} deleted successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting indicator: {str(e)}"
        }

@app.get("/api/live/status")
async def get_live_trading_status():
    """Get current live trading status"""
    # In a real app, this would query the live trading system
    # For now, return sample data
    return {
        "timestamp": datetime.now().isoformat(),
        "symbol": "NQ=F",
        "current_position": "Long",
        "last_signal": "Buy",
        "active_trades": [
            {
                "id": "live-1",
                "symbol": "NQ=F",
                "direction": "Long",
                "entry_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "entry_price": 15420,
                "current_price": 15450,
                "current_pnl": 30,
                "current_pnl_pct": 0.19
            }
        ],
        "account_equity": 10342.56,
        "daily_pnl": 124.80
    }

# Background task functions
async def run_backtest_task(backtest_id: str, params: BacktestParams):
    """Run a backtest in the background"""
    try:
        active_backtests[backtest_id]["status"] = "running"
        
        # In a real implementation, this would call the actual backtest logic
        # For now, simulate a backtest
        logger.info(f"Running backtest {backtest_id} with params: {params}")
        time.sleep(2)  # Simulate processing time
        
        # Generate sample results
        result = generate_sample_backtest_result(backtest_id, params)
        
        # Save results
        file_path = RESULTS_DIR / f"backtest_{backtest_id}.json"
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)
        
        active_backtests[backtest_id]["status"] = "completed"
        active_backtests[backtest_id]["end_time"] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"Error running backtest {backtest_id}: {e}")
        active_backtests[backtest_id]["status"] = "error"
        active_backtests[backtest_id]["error"] = str(e)

async def run_optimization_task(optimization_id: str, params: OptimizationParams):
    """Run optimization in the background"""
    try:
        active_optimizations[optimization_id]["status"] = "running"
        logger.info(f"Running optimization {optimization_id} with params: {params}")
        
        # In a real implementation, this would call the actual optimization logic
        # using our new optimization framework
        if OPTIMIZATION_AVAILABLE:
            total_combinations = 1
            try:
                # Create parameter grid from ranges
                param_grid = {}
                for param_name, range_data in params.param_ranges.items():
                    min_val = range_data.get("min", 0)
                    max_val = range_data.get("max", 0)
                    step = range_data.get("step", 1)
                    
                    if isinstance(min_val, int) and isinstance(max_val, int):
                        param_grid[param_name] = list(range(min_val, max_val + 1, step))
                    else:
                        # For float ranges
                        param_values = []
                        current = min_val
                        while current <= max_val:
                            param_values.append(current)
                            current += step
                        param_grid[param_name] = param_values
                    
                    # Calculate total combinations
                    total_combinations *= len(param_grid[param_name])
                
                # Progress update function for status tracking
                def update_progress(completed, total):
                    progress = round((completed / total) * 100, 1)
                    active_optimizations[optimization_id]["progress"] = progress
                    # Calculate ETA
                    elapsed = (datetime.now() - datetime.fromisoformat(active_optimizations[optimization_id]["started_at"])).total_seconds()
                    if completed > 0:
                        eta_seconds = (elapsed / completed) * (total - completed)
                        active_optimizations[optimization_id]["eta_minutes"] = round(eta_seconds / 60, 1)
                
                # Simulate optimization with timed updates
                # In a real implementation, this would use our optimization framework
                total_iterations = params.iterations or total_combinations
                for i in range(total_iterations):
                    time.sleep(0.2)  # Simulate computation time
                    if i % 5 == 0:  # Update every 5 iterations
                        update_progress(i, total_iterations)
                
                active_optimizations[optimization_id]["progress"] = 100.0
                
            except Exception as e:
                logger.error(f"Error in optimization process: {e}")
                # Fall back to sample data
                time.sleep(3)  # Simulate processing time
        else:
            # Using sample data
            time.sleep(5)  # Simulate processing time
        
        # Generate sample or real results
        result = generate_sample_optimization_result(optimization_id, params)
        
        # Save results
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)
        
        active_optimizations[optimization_id]["status"] = "completed"
        active_optimizations[optimization_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"Error running optimization {optimization_id}: {e}")
        active_optimizations[optimization_id]["status"] = "error"
        active_optimizations[optimization_id]["error"] = str(e)

# Helper functions
def generate_sample_backtest_result(backtest_id: str, params: BacktestParams) -> Dict:
    """Generate sample backtest results for demonstration"""
    start_date = datetime.strptime(params.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(params.end_date, "%Y-%m-%d")
    
    # Create sample equity curve
    dates = []
    equity = []
    current_date = start_date
    current_equity = 10000
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday
            dates.append(current_date.strftime("%Y-%m-%d"))
            
            # Random daily change between -1% and +1.5%
            daily_change = (pd.Series(1).sample(1, random_state=int(current_date.timestamp())).values[0] * 2.5) - 1
            current_equity *= (1 + daily_change / 100)
            equity.append(round(current_equity, 2))
        
        current_date += timedelta(days=1)
    
    # Create sample trades
    trades = []
    trade_days = sorted(pd.Series(dates).sample(min(20, len(dates)), random_state=42).tolist())
    
    for i, trade_date in enumerate(trade_days):
        direction = "Long" if i % 2 == 0 else "Short"
        entry_price = 15000 + i * 100
        profit_loss = 80 if direction == "Long" else -40
        exit_price = entry_price + profit_loss
        
        # Find the exit date (1-3 days later)
        exit_idx = min(dates.index(trade_date) + 1 + (i % 3), len(dates) - 1)
        exit_date = dates[exit_idx]
        
        trades.append({
            "id": f"trade-{i}",
            "entry_date": trade_date,
            "exit_date": exit_date,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "profit_loss": profit_loss,
            "profit_loss_pct": round(profit_loss / entry_price * 100, 2),
            "duration_hours": (i % 5) * 8 + 4
        })
    
    # Calculate performance metrics
    win_count = sum(1 for t in trades if t["profit_loss"] > 0)
    total_trades = len(trades)
    win_rate = round(win_count / total_trades * 100, 1) if total_trades > 0 else 0
    
    final_equity = equity[-1] if equity else 10000
    total_return = round((final_equity / 10000 - 1) * 100, 2)
    
    return {
        "id": backtest_id,
        "symbol": params.symbol,
        "timeframe": params.timeframe,
        "start_date": params.start_date,
        "end_date": params.end_date,
        "params": params.params,
        "performance": {
            "total_return": total_return,
            "win_rate": win_rate,
            "sharpe_ratio": round(1.2 + total_return / 20, 2),
            "max_drawdown": round(8 + (20 - total_return) / 5, 1),
            "profit_factor": round(1.5 + total_return / 40, 2),
            "total_trades": total_trades,
            "avg_trade": round(sum(t["profit_loss"] for t in trades) / total_trades, 2) if total_trades > 0 else 0
        },
        "equity_curve": [{"date": d, "equity": e} for d, e in zip(dates, equity)],
        "trades": trades
    }

def generate_sample_optimization_result(optimization_id: str, params: OptimizationParams) -> Dict:
    """Generate sample optimization results for demonstration"""
    results = []
    
    param_ranges = params.param_ranges
    
    # Extract parameter ranges for common parameters
    ema_range = param_ranges.get("ema_period", {"min": 5, "max": 15})
    ext_range = param_ranges.get("extension_threshold", {"min": 0.5, "max": 1.5})
    
    # For each parameter combination
    for ema_period in range(
        int(ema_range.get("min", 5)),
        int(ema_range.get("max", 15)) + 1
    ):
        for ext_threshold in [
            round(x * 0.1, 1)
            for x in range(
                int(ext_range.get("min", 5) * 10),
                int(ext_range.get("max", 15) * 10) + 1
            )
        ]:
            # Calculate a deterministic but varied return based on parameters
            base_return = 5 + (ema_period - 7) ** 2 * (-0.3) + (ext_threshold - 1) ** 2 * (-10)
            
            # Add some random variation
            import random
            random.seed(ema_period * 100 + ext_threshold * 10)
            variation = (random.random() - 0.5) * 5
            
            total_return = base_return + variation
            win_rate = 35 + base_return / 2 + (random.random() - 0.5) * 10
            
            results.append({
                "params": {
                    "ema_period": ema_period,
                    "extension_threshold": ext_threshold
                },
                "metrics": {
                    "total_return": round(total_return, 2),
                    "win_rate": round(win_rate, 1),
                    "sharpe_ratio": round(0.8 + total_return / 20, 2),
                    "max_drawdown": round((20 - total_return) * 0.5, 1)
                }
            })
    
    # Sort by the target metric for easier access to best results
    results.sort(key=lambda x: x["metrics"][params.metric], reverse=True)
    
    # Add method-specific data for Bayesian optimization
    method_data = {}
    if params.method == "bayesian":
        method_data = {
            "surrogate_model": params.surrogate_model,
            "acq_func": params.acq_func,
            "convergence": [
                {"iteration": i, "value": 5 + i * 0.2 + (30 - i) * 0.01 * (i ** 0.5)} 
                for i in range(1, (params.iterations or 30) + 1)
            ]
        }
    
    return {
        "id": optimization_id,
        "symbol": params.symbol,
        "timeframe": params.timeframe,
        "start_date": params.start_date,
        "end_date": params.end_date,
        "param_ranges": params.param_ranges,
        "metric": params.metric,
        "method": params.method,
        "iterations": params.iterations,
        "method_data": method_data,
        "best_params": results[0]["params"] if results else {},
        "best_metrics": results[0]["metrics"] if results else {},
        "results": results
    }

# Helper function to generate sample indicators
def generate_sample_indicators():
    """Generate sample indicator data for demonstration"""
    return [
        IndicatorInfo(
            name="EMA",
            description="Exponential Moving Average",
            parameters=[
                IndicatorParameter(name="period", type="int", default=9, min=2, max=200),
                IndicatorParameter(name="source", type="string", default="close", 
                                  options=["open", "high", "low", "close", "volume"])
            ],
            output_fields=["value"],
            built_in=True
        ),
        IndicatorInfo(
            name="BollingerBands",
            description="Bollinger Bands indicator",
            parameters=[
                IndicatorParameter(name="period", type="int", default=20, min=2, max=200),
                IndicatorParameter(name="deviation", type="float", default=2.0, min=0.1, max=5.0),
                IndicatorParameter(name="source", type="string", default="close")
            ],
            output_fields=["middle", "upper", "lower"],
            built_in=True
        ),
        IndicatorInfo(
            name="ZigZag",
            description="ZigZag indicator for identifying significant market reversals",
            parameters=[
                IndicatorParameter(name="deviation", type="float", default=5.0, min=0.1, max=20.0),
                IndicatorParameter(name="depth", type="int", default=12, min=1, max=50)
            ],
            output_fields=["line", "pivots"],
            built_in=True
        ),
        IndicatorInfo(
            name="RSI",
            description="Relative Strength Index",
            parameters=[
                IndicatorParameter(name="period", type="int", default=14, min=2, max=50),
                IndicatorParameter(name="source", type="string", default="close")
            ],
            output_fields=["value"],
            built_in=False
        )
    ]

# Helper function to generate sample indicator test results
def generate_sample_indicator_test(name: str):
    """Generate sample test results for an indicator"""
    import numpy as np
    dates = pd.date_range(start="2023-01-01", periods=10)
    
    # Generate random data that looks like indicator output
    if name == "RSI":
        values = np.random.uniform(30, 70, 10).tolist()
    elif name == "BollingerBands":
        middle = np.random.uniform(100, 110, 10).tolist()
        upper = np.random.uniform(105, 115, 10).tolist()
        lower = np.random.uniform(95, 105, 10).tolist()
        return {
            "success": True,
            "message": "Indicator calculated successfully (simulation)",
            "preview": {
                "middle": middle,
                "upper": upper,
                "lower": lower
            }
        }
    else:  # Generic case
        values = np.random.uniform(50, 150, 10).tolist()
    
    return {
        "success": True,
        "message": "Indicator calculated successfully (simulation)",
        "preview": {"value": values}
    }

# Helper function to generate sample data for testing indicators
def generate_sample_data_for_indicators():
    """Generate sample OHLCV data for testing indicators"""
    import numpy as np
    
    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=100)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate synthetic price data
    n = len(dates)
    base_price = 100
    trend = np.linspace(0, 20, n)  # Upward trend
    noise = np.random.normal(0, 1, n)  # Random noise
    cycle = 10 * np.sin(np.linspace(0, 8*np.pi, n))  # Cyclic component
    
    # Generate OHLC data
    close = base_price + trend + noise + cycle
    high = close + np.random.uniform(0.1, 2, n)
    low = close - np.random.uniform(0.1, 2, n)
    open_price = close.shift(1).fillna(close[0])
    
    # Create DataFrame
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100, 1000, n)
    }, index=dates)
    
    return data

def load_custom_indicators():
    """Load custom indicators from disk on startup"""
    if not INDICATORS_AVAILABLE:
        return
    
    try:
        registry = get_indicator_registry()
        
        # Load all custom indicators from the indicators directory
        if not INDICATORS_DIR.exists():
            return
        
        for indicator_file in INDICATORS_DIR.glob("*.py"):
            try:
                # Generate a module name based on the file name
                module_name = f"custom_indicator_{indicator_file.stem}"
                
                # Import the module
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, indicator_file)
                if spec is None or spec.loader is None:
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the Indicator subclass in the module
                for name, obj in module.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, Indicator) and obj != Indicator:
                        # Register the indicator with its file name
                        registry.register(indicator_file.stem, obj)
                        logger.info(f"Loaded custom indicator: {indicator_file.stem}")
                        break
            except Exception as e:
                logger.error(f"Error loading custom indicator {indicator_file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading custom indicators: {str(e)}")

# New routes for standard indicators from libraries like pandas-ta
@app.get("/api/indicators/standard-catalog")
def get_standard_indicators_catalog():
    """Get the catalog of available standard indicators from pandas-ta"""
    if not PANDAS_TA_AVAILABLE:
        # Return sample data if pandas-ta is not available
        return generate_sample_standard_indicators_catalog()
    
    try:
        # Create a comprehensive alphabetical list of indicators
        # Start with most common indicator categories
        categories = []
        all_indicators = []
        
        # List of all indicators we want to expose from pandas-ta
        # This approach ensures we have a complete list without dynamic import issues
        indicators_list = [
            # Moving Averages
            {"id": "sma", "name": "Simple Moving Average (SMA)", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "ema", "name": "Exponential Moving Average (EMA)", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "dema", "name": "Double Exponential Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "tema", "name": "Triple Exponential Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "trima", "name": "Triangular Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "wma", "name": "Weighted Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "hma", "name": "Hull Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "zlma", "name": "Zero Lag Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "vwma", "name": "Volume Weighted Moving Average", "category": "moving_averages", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "vwap", "name": "Volume Weighted Average Price", "category": "moving_averages", 
             "params": [{"name": "anchor", "type": "string", "default": "D", "options": ["D", "W", "M"]}]},
            
            # Overlap
            {"id": "bbands", "name": "Bollinger Bands", "category": "overlap", 
             "params": [
                 {"name": "length", "type": "int", "default": 20, "min": 2, "max": 500},
                 {"name": "std", "type": "float", "default": 2.0, "min": 0.1, "max": 10.0}
             ]},
            {"id": "kc", "name": "Keltner Channels", "category": "overlap", 
             "params": [
                 {"name": "length", "type": "int", "default": 20, "min": 2, "max": 500},
                 {"name": "scalar", "type": "float", "default": 2.0, "min": 0.1, "max": 10.0}
             ]},
            {"id": "donchian", "name": "Donchian Channels", "category": "overlap", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "ichimoku", "name": "Ichimoku Cloud", "category": "overlap", 
             "params": [
                 {"name": "tenkan", "type": "int", "default": 9, "min": 2, "max": 100},
                 {"name": "kijun", "type": "int", "default": 26, "min": 2, "max": 100},
                 {"name": "senkou", "type": "int", "default": 52, "min": 2, "max": 100}
             ]},
            
            # Momentum
            {"id": "macd", "name": "MACD", "category": "momentum", 
             "params": [
                 {"name": "fast", "type": "int", "default": 12, "min": 2, "max": 100},
                 {"name": "slow", "type": "int", "default": 26, "min": 2, "max": 100},
                 {"name": "signal", "type": "int", "default": 9, "min": 2, "max": 50}
             ]},
            {"id": "rsi", "name": "Relative Strength Index", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "stoch", "name": "Stochastic Oscillator", "category": "momentum", 
             "params": [
                 {"name": "k", "type": "int", "default": 14, "min": 1, "max": 100},
                 {"name": "d", "type": "int", "default": 3, "min": 1, "max": 100}
             ]},
            {"id": "cmo", "name": "Chande Momentum Oscillator", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "cci", "name": "Commodity Channel Index", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "willr", "name": "Williams %R", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "mfi", "name": "Money Flow Index", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "tsi", "name": "True Strength Index", "category": "momentum", 
             "params": [
                 {"name": "fast", "type": "int", "default": 13, "min": 1, "max": 100},
                 {"name": "slow", "type": "int", "default": 25, "min": 1, "max": 100}
             ]},
            {"id": "coppock", "name": "Coppock Curve", "category": "momentum", 
             "params": [
                 {"name": "length", "type": "int", "default": 10, "min": 2, "max": 100},
                 {"name": "fast", "type": "int", "default": 11, "min": 2, "max": 100},
                 {"name": "slow", "type": "int", "default": 14, "min": 2, "max": 100}
             ]},
            {"id": "ppo", "name": "Percentage Price Oscillator", "category": "momentum", 
             "params": [
                 {"name": "fast", "type": "int", "default": 12, "min": 2, "max": 100},
                 {"name": "slow", "type": "int", "default": 26, "min": 2, "max": 100},
                 {"name": "signal", "type": "int", "default": 9, "min": 2, "max": 50}
             ]},
            {"id": "roc", "name": "Rate of Change", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 10, "min": 1, "max": 100}]},
            {"id": "mom", "name": "Momentum", "category": "momentum", 
             "params": [{"name": "length", "type": "int", "default": 10, "min": 1, "max": 100}]},
            {"id": "apo", "name": "Absolute Price Oscillator", "category": "momentum", 
             "params": [
                 {"name": "fast", "type": "int", "default": 12, "min": 2, "max": 100},
                 {"name": "slow", "type": "int", "default": 26, "min": 2, "max": 100}
             ]},
             
            # Trend
            {"id": "adx", "name": "Average Directional Index", "category": "trend", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "aroon", "name": "Aroon", "category": "trend", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
            {"id": "psar", "name": "Parabolic SAR", "category": "trend", 
             "params": [
                 {"name": "acceleration", "type": "float", "default": 0.02, "min": 0.01, "max": 0.5},
                 {"name": "max_acceleration", "type": "float", "default": 0.2, "min": 0.1, "max": 1.0}
             ]},
            {"id": "supertrend", "name": "SuperTrend", "category": "trend", 
             "params": [
                 {"name": "length", "type": "int", "default": 10, "min": 1, "max": 100},
                 {"name": "multiplier", "type": "float", "default": 3.0, "min": 0.5, "max": 10.0}
             ]},
            {"id": "vortex", "name": "Vortex Indicator", "category": "trend", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}]},
             
            # Volatility
            {"id": "atr", "name": "Average True Range", "category": "volatility", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 1, "max": 100}]},
            {"id": "natr", "name": "Normalized ATR", "category": "volatility", 
             "params": [{"name": "length", "type": "int", "default": 14, "min": 1, "max": 100}]},
            {"id": "true_range", "name": "True Range", "category": "volatility", "params": []},
            {"id": "massi", "name": "Mass Index", "category": "volatility", 
             "params": [
                 {"name": "fast", "type": "int", "default": 9, "min": 1, "max": 100},
                 {"name": "slow", "type": "int", "default": 25, "min": 1, "max": 100}
             ]},

            # Volume
            {"id": "obv", "name": "On-Balance Volume", "category": "volume", "params": []},
            {"id": "cmf", "name": "Chaikin Money Flow", "category": "volume", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 100}]},
            {"id": "ad", "name": "Accumulation/Distribution", "category": "volume", "params": []},
            {"id": "eom", "name": "Ease of Movement", "category": "volume", 
             "params": [
                 {"name": "length", "type": "int", "default": 14, "min": 2, "max": 100},
                 {"name": "divisor", "type": "int", "default": 100000000, "min": 1, "max": 1000000000}
             ]},
            {"id": "pvt", "name": "Price Volume Trend", "category": "volume", "params": []},
            {"id": "vp", "name": "Volume Profile", "category": "volume", 
             "params": [{"name": "bins", "type": "int", "default": 20, "min": 5, "max": 100}]},

            # Statistics
            {"id": "stdev", "name": "Standard Deviation", "category": "statistics", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "zscore", "name": "Z-Score", "category": "statistics", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
            {"id": "variance", "name": "Variance", "category": "statistics", 
             "params": [{"name": "length", "type": "int", "default": 20, "min": 2, "max": 500}]},
        ]
        
        # Sort alphabetically by name for easy browsing
        sorted_indicators = sorted(indicators_list, key=lambda x: x["name"])
        
        # Process each indicator
        for indicator_info in sorted_indicators:
            # Convert our simplified params format to the full format expected by frontend
            parameters = []
            for param in indicator_info.get("params", []):
                parameter = {
                    "name": param["name"],
                    "type": param["type"],
                    "default": param["default"],
                    "description": f"{param['name']} parameter"
                }
                
                if "min" in param:
                    parameter["min"] = param["min"]
                if "max" in param:
                    parameter["max"] = param["max"]
                if "options" in param:
                    parameter["options"] = param["options"]
                
                parameters.append(parameter)
            
            # Create the full indicator definition
            indicator = {
                "id": indicator_info["id"],
                "name": indicator_info["name"],
                "category": indicator_info["category"],
                "description": f"{indicator_info['name']} technical indicator",
                "parameters": parameters,
                "inputs": ["close"] if not any(x in indicator_info["id"] for x in ["atr", "psar", "supertrend", "donchian", "ichimoku", "cci", "willr"]) else ["high", "low", "close"],
                "outputs": [indicator_info["id"]],
                "source_library": "pandas_ta"
            }
            
            # Add volume as an input if it's a volume indicator
            if indicator_info["category"] in ["volume"]:
                if "inputs" in indicator and "volume" not in indicator["inputs"]:
                    indicator["inputs"].append("volume")
            
            all_indicators.append(indicator)
        
        # Group indicators by category for organization
        category_map = {
            "moving_averages": {"id": "moving_averages", "name": "Moving Averages", "description": "Various types of moving averages", "indicators": []},
            "overlap": {"id": "overlap", "name": "Overlay Indicators", "description": "Indicators that overlay on price", "indicators": []},
            "momentum": {"id": "momentum", "name": "Momentum Indicators", "description": "Indicators that measure momentum", "indicators": []},
            "trend": {"id": "trend", "name": "Trend Indicators", "description": "Indicators that measure trend direction and strength", "indicators": []},
            "volatility": {"id": "volatility", "name": "Volatility Indicators", "description": "Indicators that measure volatility", "indicators": []},
            "volume": {"id": "volume", "name": "Volume Indicators", "description": "Indicators that use volume", "indicators": []},
            "statistics": {"id": "statistics", "name": "Statistical Indicators", "description": "Statistical measures and indicators", "indicators": []}
        }
        
        # Assign indicators to categories
        for indicator in all_indicators:
            category = indicator["category"]
            if category in category_map:
                category_map[category]["indicators"].append(indicator)
        
        # Create a special "all" category with alphabetically sorted indicators
        all_category = {
            "id": "all",
            "name": "All Indicators (A-Z)",
            "description": "All available indicators in alphabetical order",
            "indicators": all_indicators
        }
        
        # Build the final categories list
        categories = [all_category]  # Put "All" category first
        
        # Add all non-empty categories
        for category_id in ["moving_averages", "overlap", "momentum", "trend", "volatility", "volume", "statistics"]:
            if category_map[category_id]["indicators"]:
                categories.append(category_map[category_id])
        
        return categories
    except Exception as e:
        logger.error(f"Error getting standard indicators catalog: {str(e)}")
        return []

@app.post("/api/indicators/standard/test")
def test_standard_indicator(request: StandardIndicatorTestRequest):
    """Test a standard indicator with the provided configuration"""
    try:
        indicator_id = request.definition_id
        parameters = request.parameters
        
        if not indicator_id:
            return {"error": "Missing indicator_id"}
        
        # Generate sample data for testing
        df = generate_sample_data(300)  # 300 rows of sample data
        
        # Apply the indicator based on its ID
        # This is where we need to map the indicator ID to the appropriate pandas_ta function
        if not PANDAS_TA_AVAILABLE:
            return {"error": "pandas_ta library is not available"}
        
        # Common parameters for most indicators
        length = parameters.get("length", 20)
        
        # Handle different indicator types
        result_df = None
        
        # Moving Averages
        if indicator_id in ["sma", "ema", "dema", "tema", "trima", "wma", "zlma"]:
            ma_func = getattr(ta, indicator_id)
            result_df = df.copy()
            result_df[indicator_id] = ma_func(df["close"], length=length)
            
        elif indicator_id == "hma":
            result_df = df.copy()
            result_df["hma"] = ta.hma(df["close"], length=length)
            
        elif indicator_id == "vwma":
            result_df = df.copy()
            result_df["vwma"] = ta.vwma(df["close"], df["volume"], length=length)
            
        elif indicator_id == "vwap":
            result_df = df.copy()
            anchor = parameters.get("anchor", "D")
            result_df["vwap"] = ta.vwap(df["high"], df["low"], df["close"], df["volume"], anchor=anchor)
            
        # Overlap indicators
        elif indicator_id == "bbands":
            std = parameters.get("std", 2.0)
            result_df = df.copy()
            bbands = ta.bbands(df["close"], length=length, std=std)
            result_df["bbands_upper"] = bbands["BBU_" + str(length) + "_" + str(std)]
            result_df["bbands_middle"] = bbands["BBM_" + str(length) + "_" + str(std)]
            result_df["bbands_lower"] = bbands["BBL_" + str(length) + "_" + str(std)]
            
        elif indicator_id == "kc":
            scalar = parameters.get("scalar", 2.0)
            result_df = df.copy()
            kc = ta.kc(df["high"], df["low"], df["close"], length=length, scalar=scalar)
            # Extract column names from result and map to expected output names
            kc_cols = kc.columns
            kc_upper_col = [col for col in kc_cols if "KCU" in col][0]
            kc_lower_col = [col for col in kc_cols if "KCL" in col][0]
            kc_middle_col = [col for col in kc_cols if "KCB" in col][0]
            result_df["kc_upper"] = kc[kc_upper_col]
            result_df["kc_lower"] = kc[kc_lower_col]
            result_df["kc_middle"] = kc[kc_middle_col]
            
        elif indicator_id == "donchian":
            result_df = df.copy()
            dc = ta.donchian(df["high"], df["low"], length=length)
            # Extract column names
            dc_cols = dc.columns
            dc_upper_col = [col for col in dc_cols if "DCU" in col][0]
            dc_lower_col = [col for col in dc_cols if "DCL" in col][0]
            dc_middle_col = [col for col in dc_cols if "DCM" in col][0]
            result_df["donchian_upper"] = dc[dc_upper_col]
            result_df["donchian_lower"] = dc[dc_lower_col]
            result_df["donchian_middle"] = dc[dc_middle_col]
            
        elif indicator_id == "ichimoku":
            tenkan = parameters.get("tenkan", 9)
            kijun = parameters.get("kijun", 26)
            senkou = parameters.get("senkou", 52)
            result_df = df.copy()
            ichimoku = ta.ichimoku(df["high"], df["low"], df["close"], 
                                  tenkan=tenkan, kijun=kijun, senkou=senkou)
            # Map ichimoku components to results
            for col in ichimoku.columns:
                result_df[col.lower()] = ichimoku[col]
            
        # Momentum indicators
        elif indicator_id == "macd":
            fast = parameters.get("fast", 12)
            slow = parameters.get("slow", 26)
            signal = parameters.get("signal", 9)
            result_df = df.copy()
            macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
            # Extract column names
            macd_cols = macd.columns
            result_df["macd"] = macd[macd_cols[0]]
            result_df["macd_signal"] = macd[macd_cols[1]]
            result_df["macd_histogram"] = macd[macd_cols[2]]
            
        elif indicator_id == "rsi":
            result_df = df.copy()
            result_df["rsi"] = ta.rsi(df["close"], length=length)
            
        elif indicator_id == "stoch":
            k = parameters.get("k", 14)
            d = parameters.get("d", 3)
            result_df = df.copy()
            stoch = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d)
            # Extract column names
            stoch_cols = stoch.columns
            result_df["stoch_k"] = stoch[stoch_cols[0]]
            result_df["stoch_d"] = stoch[stoch_cols[1]]
            
        elif indicator_id == "cmo":
            result_df = df.copy()
            result_df["cmo"] = ta.cmo(df["close"], length=length)
            
        elif indicator_id == "cci":
            result_df = df.copy()
            result_df["cci"] = ta.cci(df["high"], df["low"], df["close"], length=length)
            
        elif indicator_id == "willr":
            result_df = df.copy()
            result_df["willr"] = ta.willr(df["high"], df["low"], df["close"], length=length)
            
        elif indicator_id == "mfi":
            result_df = df.copy()
            result_df["mfi"] = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=length)
            
        elif indicator_id == "tsi":
            fast = parameters.get("fast", 13)
            slow = parameters.get("slow", 25)
            result_df = df.copy()
            tsi = ta.tsi(df["close"], fast=fast, slow=slow)
            result_df["tsi"] = tsi
            
        elif indicator_id == "coppock":
            fast = parameters.get("fast", 11)
            slow = parameters.get("slow", 14)
            result_df = df.copy()
            result_df["coppock"] = ta.coppock(df["close"], length=length, fast=fast, slow=slow)
            
        elif indicator_id in ["ppo", "apo"]:
            fast = parameters.get("fast", 12)
            slow = parameters.get("slow", 26)
            result_df = df.copy()
            indicator_func = getattr(ta, indicator_id)
            if indicator_id == "ppo":
                signal = parameters.get("signal", 9)
                ppo = indicator_func(df["close"], fast=fast, slow=slow, signal=signal)
                ppo_cols = ppo.columns
                result_df["ppo"] = ppo[ppo_cols[0]]
                result_df["ppo_signal"] = ppo[ppo_cols[1]]
                result_df["ppo_histogram"] = ppo[ppo_cols[2]]
            else:
                result_df[indicator_id] = indicator_func(df["close"], fast=fast, slow=slow)
            
        elif indicator_id in ["roc", "mom"]:
            result_df = df.copy()
            indicator_func = getattr(ta, indicator_id)
            result_df[indicator_id] = indicator_func(df["close"], length=length)
            
        # Trend indicators
        elif indicator_id == "adx":
            result_df = df.copy()
            adx = ta.adx(df["high"], df["low"], df["close"], length=length)
            # Extract column names
            adx_cols = adx.columns
            for col in adx_cols:
                result_df[col.lower()] = adx[col]
            
        elif indicator_id == "aroon":
            result_df = df.copy()
            aroon = ta.aroon(df["high"], df["low"], length=length)
            # Extract column names
            aroon_cols = aroon.columns
            result_df["aroon_up"] = aroon[aroon_cols[0]]
            result_df["aroon_down"] = aroon[aroon_cols[1]]
            result_df["aroon_osc"] = aroon[aroon_cols[2]]
            
        elif indicator_id == "psar":
            acceleration = parameters.get("acceleration", 0.02)
            max_acceleration = parameters.get("max_acceleration", 0.2)
            result_df = df.copy()
            result_df["psar"] = ta.psar(df["high"], df["low"], df["close"], 
                                       acceleration=acceleration, 
                                       max_acceleration=max_acceleration)
            
        elif indicator_id == "supertrend":
            length = parameters.get("length", 10)
            multiplier = parameters.get("multiplier", 3.0)
            result_df = df.copy()
            supertrend = ta.supertrend(df["high"], df["low"], df["close"], 
                                      length=length, multiplier=multiplier)
            # Extract column names
            supertrend_cols = supertrend.columns
            result_df["supertrend"] = supertrend[supertrend_cols[0]]
            result_df["direction"] = supertrend[supertrend_cols[1]]
            
        elif indicator_id == "vortex":
            result_df = df.copy()
            vortex = ta.vortex(df["high"], df["low"], df["close"], length=length)
            # Extract column names
            vortex_cols = vortex.columns
            result_df["vortex_pos"] = vortex[vortex_cols[0]]
            result_df["vortex_neg"] = vortex[vortex_cols[1]]
            result_df["vortex_diff"] = vortex[vortex_cols[2]]
            
        # Volatility indicators
        elif indicator_id == "atr":
            result_df = df.copy()
            result_df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=length)
            
        elif indicator_id == "natr":
            result_df = df.copy()
            result_df["natr"] = ta.natr(df["high"], df["low"], df["close"], length=length)
            
        elif indicator_id == "true_range":
            result_df = df.copy()
            result_df["true_range"] = ta.true_range(df["high"], df["low"], df["close"])
            
        elif indicator_id == "massi":
            fast = parameters.get("fast", 9)
            slow = parameters.get("slow", 25)
            result_df = df.copy()
            result_df["massi"] = ta.massi(df["high"], df["low"], fast=fast, slow=slow)
            
        # Volume indicators
        elif indicator_id == "obv":
            result_df = df.copy()
            result_df["obv"] = ta.obv(df["close"], df["volume"])
            
        elif indicator_id == "cmf":
            result_df = df.copy()
            result_df["cmf"] = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=length)
            
        elif indicator_id == "ad":
            result_df = df.copy()
            result_df["ad"] = ta.ad(df["high"], df["low"], df["close"], df["volume"])
            
        elif indicator_id == "eom":
            divisor = parameters.get("divisor", 100000000)
            result_df = df.copy()
            result_df["eom"] = ta.eom(df["high"], df["low"], df["close"], df["volume"], 
                                     length=length, divisor=divisor)
            
        elif indicator_id == "pvt":
            result_df = df.copy()
            result_df["pvt"] = ta.pvt(df["close"], df["volume"])
            
        # Statistical indicators
        elif indicator_id in ["stdev", "variance", "zscore"]:
            result_df = df.copy()
            indicator_func = getattr(ta, indicator_id)
            result_df[indicator_id] = indicator_func(df["close"], length=length)
            
        else:
            return {
                "success": False,
                "message": f"Unknown indicator: {indicator_id}"
            }
        
        if result_df is None:
            return {
                "success": False,
                "message": "Failed to compute indicator"
            }
            
        # Convert the result to JSON for response
        # Drop any NaN values which can't be serialized to JSON
        result_df = result_df.fillna(None)
        
        # Format the response to match what the frontend expects
        preview = {}
        
        # Get the last 10 rows of indicator data
        # Skip the OHLCV columns
        skip_cols = ["open", "high", "low", "close", "volume", "timestamp"]
        indicator_cols = [col for col in result_df.columns if col not in skip_cols]
        
        for col in indicator_cols:
            preview[col] = result_df[col].tail(10).tolist()
            
        response = {
            "success": True,
            "message": "Indicator calculated successfully",
            "preview": preview
        }
        
        # Include price data if requested
        if request.include_price:
            response["price_data"] = {
                "open": result_df["open"].tail(10).tolist(),
                "high": result_df["high"].tail(10).tolist(),
                "low": result_df["low"].tail(10).tolist(),
                "close": result_df["close"].tail(10).tolist(),
                "volume": result_df["volume"].tail(10).tolist()
            }
            response["dates"] = [str(d) for d in result_df["timestamp"].tail(10).tolist()]
            
        return response
        
    except Exception as e:
        logger.error(f"Error testing standard indicator: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error testing indicator: {str(e)}"
        }

@app.post("/api/indicators/standard/save")
def save_standard_indicator(indicator: StandardIndicator):
    """Save a configured standard indicator"""
    if not PANDAS_TA_AVAILABLE:
        # Return success even in simulation mode
        return {
            "success": True,
            "message": "Standard indicator saved (simulation)",
            "id": str(uuid.uuid4())
        }
    
    try:
        # Generate a unique ID if not provided
        if not indicator.id:
            indicator.id = str(uuid.uuid4())
            
        # Add timestamps
        now = datetime.now().isoformat()
        indicator.created_at = now
        indicator.updated_at = now
        
        # Save to disk
        indicator_path = STANDARD_INDICATORS_DIR / f"{indicator.id}.json"
        with open(indicator_path, "w") as f:
            f.write(json.dumps(indicator.dict(), indent=2))
            
        return {
            "success": True,
            "message": f"Standard indicator {indicator.name} saved successfully",
            "id": indicator.id
        }
    except Exception as e:
        logger.error(f"Error saving standard indicator: {str(e)}")
        return {
            "success": False,
            "message": f"Error saving indicator: {str(e)}"
        }

@app.get("/api/indicators/standard")
def list_standard_indicators():
    """List all saved standard indicators"""
    try:
        indicators = []
        
        # Check if directory exists
        if not STANDARD_INDICATORS_DIR.exists():
            return indicators
            
        # Load all JSON files from the standard indicators directory
        for file_path in STANDARD_INDICATORS_DIR.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    indicator = json.loads(f.read())
                    indicators.append(indicator)
            except Exception as e:
                logger.error(f"Error loading standard indicator from {file_path}: {str(e)}")
                
        return indicators
    except Exception as e:
        logger.error(f"Error listing standard indicators: {str(e)}")
        return []

# Helper function to generate sample standard indicators catalog
def generate_sample_standard_indicators_catalog():
    """Generate a sample catalog if pandas-ta is not available"""
    return [
        {
            "id": "trend",
            "name": "Trend Indicators",
            "description": "Indicators that help identify market direction and strength",
            "indicators": [
                {
                    "id": "sma",
                    "name": "Simple Moving Average (SMA)",
                    "category": "trend",
                    "description": "Simple moving average over a specified period",
                    "parameters": [
                        {"name": "length", "type": "int", "default": 20, "min": 2, "max": 500, 
                         "description": "Period length"},
                        {"name": "source", "type": "string", "default": "close", 
                         "options": ["open", "high", "low", "close", "volume"], 
                         "description": "Input data source"}
                    ],
                    "inputs": ["close"],
                    "outputs": ["sma"],
                    "source_library": "pandas_ta"
                }
            ]
        }
    ]

def generate_sample_data(num_rows=300):
    """Generate sample OHLCV data for testing indicators"""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Start with a base price
    base_price = 100.0
    
    # Generate timestamps
    end_date = datetime.now()
    dates = [end_date - timedelta(days=i) for i in range(num_rows)]
    dates.reverse()
    
    # Generate price data with some randomness but realistic behavior
    # Start with random walk
    np.random.seed(42)  # For reproducibility
    
    # Simple price generation based on random walk
    changes = np.random.normal(0, 1, num_rows) * 0.5
    # Add some trend
    trend = np.linspace(0, 3, num_rows) * 0.3
    changes = changes + trend
    
    # Calculate close prices
    close_prices = base_price + np.cumsum(changes)
    
    # Generate other OHLC values based on close with some randomness
    highs = close_prices + np.random.random(num_rows) * 2
    lows = close_prices - np.random.random(num_rows) * 2
    
    # Make sure highs are always higher than lows
    for i in range(num_rows):
        if highs[i] <= lows[i]:
            highs[i] = lows[i] + 0.01
    
    # Generate open prices between high and low
    opens = lows + np.random.random(num_rows) * (highs - lows)
    
    # Generate volumes (higher on bigger price moves)
    volumes = (np.abs(changes) * 10000 + 5000) * np.random.random(num_rows) * 5
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': close_prices,
        'volume': volumes
    })
    
    # Add some gaps and volatility to make it more realistic
    # Add a sudden drop
    drop_idx = num_rows // 3
    drop_pct = 0.05
    df.loc[drop_idx:, ['open', 'high', 'low', 'close']] *= (1 - drop_pct)
    
    # Add a rally
    rally_idx = num_rows * 2 // 3
    rally_pct = 0.08
    df.loc[rally_idx:, ['open', 'high', 'low', 'close']] *= (1 + rally_pct)
    
    # Ensure all values are positive and correctly ordered
    df['low'] = df[['open', 'close']].min(axis=1) * 0.99
    df['high'] = df[['open', 'close']].max(axis=1) * 1.01
    
    return df

# Helper function to generate sample standard indicator test results
def generate_sample_standard_indicator_test(indicator_id):
    """Generate sample test results for a standard indicator"""
    # Generate some sample series data (50 points)
    series_data = [round(50 + 5 * (i % 10) + i/10, 2) for i in range(50)]
    dates = [(datetime.now() - timedelta(days=50-i)).strftime("%Y-%m-%d") for i in range(50)]
    
    # Return last 10 values for the preview
    preview_data = series_data[-10:]
    preview_dates = dates[-10:]
    
    # Create different output based on indicator type
    if indicator_id == "rsi":
        # RSI oscillates between 0-100
        rsi_data = [min(max(30 + 40 * ((i % 10) / 10), 30), 70) for i in range(50)]
        preview = {"rsi": rsi_data[-10:]}
    elif indicator_id == "macd":
        # MACD has multiple output series
        macd_data = [round((i % 10) - 5, 2) for i in range(50)]
        signal_data = [round((i % 8) - 4, 2) for i in range(50)]
        hist_data = [round(macd_data[i] - signal_data[i], 2) for i in range(50)]
        preview = {
            "macd": macd_data[-10:],
            "macd_signal": signal_data[-10:],
            "macd_histogram": hist_data[-10:]
        }
    elif indicator_id == "bbands":
        # Bollinger Bands have upper, middle, and lower bands
        middle = series_data
        upper = [round(val + 10 + (i % 5), 2) for i, val in enumerate(middle)]
        lower = [round(val - 10 - (i % 5), 2) for i, val in enumerate(middle)]
        preview = {
            "bbands_lower": lower[-10:],
            "bbands_middle": middle[-10:],
            "bbands_upper": upper[-10:]
        }
    else:
        # Default to a single series for other indicators
        preview = {f"{indicator_id}": preview_data}
    
    # Include price data in the response
    price_data = {
        "open": [round(val - 1, 2) for val in series_data[-10:]],
        "high": [round(val + 2, 2) for val in series_data[-10:]],
        "low": [round(val - 2, 2) for val in series_data[-10:]],
        "close": series_data[-10:],
        "volume": [int(10000 + 5000 * (i % 5)) for i in range(10)]
    }
    
    return {
        "success": True,
        "message": "Indicator calculated successfully",
        "preview": preview,
        "dates": preview_dates,
        "price_data": price_data
    }

if __name__ == "__main__":
    # Load custom indicators before starting the server
    if INDICATORS_AVAILABLE:
        load_custom_indicators()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)