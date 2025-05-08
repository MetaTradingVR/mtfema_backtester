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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import backtester modules
from mtfema_backtester.backtest import Backtest
from mtfema_backtester.strategy import MT9EMAStrategy
from mtfema_backtester.optimizer import StrategyOptimizer

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

# Storage for backtest results and optimization results
# In a production app, this would use a database
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# Keep track of running backtests
active_backtests: Dict[str, Dict[str, Any]] = {}

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

@app.post("/api/optimization/run")
async def run_optimization(params: OptimizationParams, background_tasks: BackgroundTasks):
    """Run a new optimization"""
    optimization_id = str(uuid.uuid4())
    
    # Store the optimization params
    active_backtests[optimization_id] = {
        "status": "queued",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
    }
    
    # Run the optimization in the background
    background_tasks.add_task(run_optimization_task, optimization_id, params)
    
    return {"id": optimization_id}

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
        active_backtests[optimization_id]["status"] = "running"
        
        # In a real implementation, this would call the actual optimization logic
        # For now, simulate an optimization
        logger.info(f"Running optimization {optimization_id} with params: {params}")
        time.sleep(5)  # Simulate processing time
        
        # Generate sample results
        result = generate_sample_optimization_result(optimization_id, params)
        
        # Save results
        file_path = RESULTS_DIR / f"optimization_{optimization_id}.json"
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)
        
        active_backtests[optimization_id]["status"] = "completed"
        active_backtests[optimization_id]["end_time"] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"Error running optimization {optimization_id}: {e}")
        active_backtests[optimization_id]["status"] = "error"
        active_backtests[optimization_id]["error"] = str(e)

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
    
    # For each parameter combination
    for ema_period in range(
        int(param_ranges.get("ema_period", {}).get("min", 5)),
        int(param_ranges.get("ema_period", {}).get("max", 15)) + 1
    ):
        for ext_threshold in [
            round(x * 0.1, 1)
            for x in range(
                int(param_ranges.get("extension_threshold", {}).get("min", 5) * 10),
                int(param_ranges.get("extension_threshold", {}).get("max", 15) * 10) + 1
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
    
    return {
        "id": optimization_id,
        "symbol": params.symbol,
        "timeframe": params.timeframe,
        "start_date": params.start_date,
        "end_date": params.end_date,
        "param_ranges": params.param_ranges,
        "metric": params.metric,
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 