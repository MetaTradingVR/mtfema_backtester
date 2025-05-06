"""
Configuration settings for the Multi-Timeframe 9 EMA Extension Strategy
"""

# Data Configuration
DATA_CONFIG = {
    "default_symbol": "SPY",
    "default_timeframes": ["1d", "1h", "15m"],
    "default_lookback_days": 365,
    "cache_enabled": True,
    "cache_directory": "./data/cache"
}

# Strategy Parameters
STRATEGY_PARAMS = {
    # EMA Configuration
    "ema": {
        "period": 9,
        "apply_to": "Close",  # Price field to use for EMA calculation
        "extension_thresholds": {
            "1d": 1.5,  # Daily timeframe extension threshold (%)
            "1h": 1.0,  # Hourly timeframe extension threshold (%)
            "15m": 0.8  # 15-min timeframe extension threshold (%)
        },
        "reclamation_confirmation_bars": 2  # Bars needed to confirm EMA reclamation
    },
    
    # Bollinger Bands Configuration
    "bollinger": {
        "period": 20, 
        "std_dev": 2.0,
        "apply_to": "Close",
        "squeeze_threshold": 0.1  # Threshold for identifying volatility squeezes
    },
    
    # ZigZag Configuration
    "zigzag": {
        "depth": 5,  # Minimum number of bars between pivot points
        "deviation": 5,  # Minimum percentage deviation for a new pivot
        "backstep": 3   # Number of bars to wait before identifying a new pivot
    },
    
    # Fibonacci Levels
    "fibonacci": {
        "levels": [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618],
        "extension_levels": [1.0, 1.272, 1.618, 2.0, 2.618],
        "pullback_zone": [0.382, 0.618]  # Zone for valid pullbacks
    },
    
    # Multi-Timeframe Configuration
    "timeframe_weights": {
        "1d": 0.5,   # Daily timeframe weight in decision making
        "1h": 0.3,   # Hourly timeframe weight
        "15m": 0.2   # 15-min timeframe weight
    },
    
    # Conflict Resolution
    "conflict_resolution": {
        "prioritize_higher_timeframe": True,  # Higher TF signals override lower TF
        "minimum_agreement": 2  # Minimum number of timeframes that must agree
    }
}

# Risk Management
RISK_PARAMS = {
    "max_risk_per_trade": 1.0,  # Maximum risk per trade (% of account)
    "default_stop_loss": 2.0,   # Default stop loss (% from entry)
    "target_risk_reward": 2.0,  # Minimum risk/reward ratio
    "trailing_stop": {
        "enabled": True,
        "activation": 1.0,      # Activate trailing stop after this R multiple
        "step": 0.5             # Step size for trailing stop adjustments
    },
    "position_sizing": "fixed_risk"  # Options: fixed_risk, fixed_size, kelly
}

# Backtesting Configuration
BACKTEST_CONFIG = {
    "commission": 0.001,         # Commission per trade (%)
    "slippage": 0.001,           # Slippage per trade (%)
    "initial_capital": 100000,   # Initial capital for backtesting
    "execution_delay": 0,        # Execution delay in bars
    "contract_size": 100,        # Contract size for position sizing calculations
    "enable_fractional_shares": True  # Allow fractional share positions
}

# Optimization Configuration
OPTIMIZATION_CONFIG = {
    "optimizer_type": "grid",    # Options: grid, random, bayesian
    "max_iterations": 100,       # Maximum number of iterations
    "cross_validation": {
        "enabled": True,
        "folds": 5,              # Number of time-based folds for validation
        "expanding_window": True # Use expanding window validation
    },
    "optimization_metric": "sharpe_ratio"  # Metric to optimize
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "log_file": "./logs/backtest.log",
    "console_output": True,
    "log_trades": True
}

# Visualization Configuration
VISUALIZATION_CONFIG = {
    "default_theme": "light",
    "chart_type": "candlestick",
    "show_volume": True,
    "show_indicators": True,
    "highlight_signals": True,
    "save_charts": True,
    "charts_directory": "./output/charts"
}