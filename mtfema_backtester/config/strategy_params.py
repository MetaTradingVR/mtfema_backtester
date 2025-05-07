"""
Strategy parameters configuration for the Multi-Timeframe 9 EMA Extension Strategy.

This module contains all configurable parameters and their default values.
"""

import os
import json
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Default strategy parameters
DEFAULT_PARAMS = {
    "ema": {
        "period": 9,
        "reclamation_confirmation_bars": 2,
        "extension_thresholds": {
            "1m": 0.2,    # 0.2% extension for 1-minute timeframe
            "5m": 0.4,    # 0.4% extension for 5-minute timeframe
            "10m": 0.5,   # 0.5% extension for 10-minute timeframe
            "15m": 0.6,   # 0.6% extension for 15-minute timeframe
            "30m": 0.8,   # 0.8% extension for 30-minute timeframe
            "1h": 1.0,    # 1.0% extension for 1-hour timeframe
            "2h": 1.2,    # 1.2% extension for 2-hour timeframe
            "4h": 1.5,    # 1.5% extension for 4-hour timeframe
            "1d": 2.0,    # 2.0% extension for daily timeframe
            "1w": 3.0,    # 3.0% extension for weekly timeframe
            "1M": 4.0     # 4.0% extension for monthly timeframe
        }
    },
    "bollinger": {
        "period": 20,
        "std_dev": 2.0,
        "squeeze_threshold": 0.1
    },
    "fibonacci": {
        "pullback_min": 0.382,  # Minimum Fibonacci pullback level (38.2%)
        "pullback_max": 0.618,  # Maximum Fibonacci pullback level (61.8%)
        "extension_levels": [1.618, 2.618, 3.618, 4.236]  # Fibonacci extension levels
    },
    "risk_management": {
        "account_risk_percent": 1.0,    # Risk 1% of account per trade
        "reward_risk_ratio": 2.0,       # Target 2:1 reward-to-risk ratio
        "max_trades_per_day": 3,        # Maximum number of trades per day
        "max_correlated_exposure": 2,   # Maximum number of correlated trades
        "stop_buffer_atr_multiple": 0.5 # Stop loss buffer as multiple of ATR
    },
    "timeframes": {
        "use_timeframes": ["1d", "4h", "1h", "15m", "5m"],  # Timeframes to use
        "reference_timeframe": "4h",                        # Reference timeframe for context
        "entry_timeframe": "15m",                           # Primary entry timeframe
        "confirmation_timeframe": "5m"                      # Confirmation timeframe
    },
    "filters": {
        "min_adx": 20,                  # Minimum ADX value for trend strength
        "min_volume": 100000,           # Minimum volume for liquidity
        "max_spread_percent": 0.1,      # Maximum spread as percentage of price
        "rsi_oversold": 30,             # RSI oversold threshold
        "rsi_overbought": 70            # RSI overbought threshold
    },
    "session": {
        "trading_hours": {              # Trading session hours (market dependent)
            "start": "08:30",           # Session start time (24hr format)
            "end": "16:00"              # Session end time (24hr format)
        },
        "avoid_news": True,             # Avoid trading during high-impact news
        "avoid_fomc": True              # Avoid trading during FOMC announcements
    },
    "symbols": {
        "default_symbol": "NQ",         # Default symbol for testing
        "base_commission": 0.0,         # Base commission per trade
        "commission_per_contract": 2.5, # Commission per contract
        "base_slippage_ticks": 1,       # Base slippage in ticks
        "contract_multiplier": 20       # Contract multiplier
    }
}

class StrategyParameters:
    """
    Class for managing strategy parameters.
    
    Provides methods for loading, saving, and accessing strategy parameters.
    """
    
    def __init__(self, params_file=None):
        """
        Initialize the StrategyParameters object
        
        Parameters:
        -----------
        params_file : str, optional
            Path to a JSON file with parameter values
        """
        self.params = DEFAULT_PARAMS.copy()
        
        # Load parameters from file if provided
        if params_file is not None:
            self.load_params(params_file)
            
        logger.info("Strategy parameters initialized")
        
    def load_params(self, params_file):
        """
        Load parameters from a JSON file
        
        Parameters:
        -----------
        params_file : str
            Path to a JSON file with parameter values
            
        Returns:
        --------
        bool
            True if parameters were loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(params_file):
                logger.warning(f"Parameters file not found: {params_file}")
                return False
                
            with open(params_file, 'r') as f:
                loaded_params = json.load(f)
                
            # Update default parameters with loaded values
            self._update_nested_dict(self.params, loaded_params)
            
            logger.info(f"Loaded parameters from {params_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading parameters from {params_file}: {str(e)}")
            return False
            
    def save_params(self, params_file):
        """
        Save parameters to a JSON file
        
        Parameters:
        -----------
        params_file : str
            Path to save the parameters
            
        Returns:
        --------
        bool
            True if parameters were saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist and has a directory component
            if os.path.dirname(params_file):
                os.makedirs(os.path.dirname(params_file), exist_ok=True)
            
            with open(params_file, 'w') as f:
                json.dump(self.params, f, indent=4)
            
            logger.info(f"Saved parameters to {params_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving parameters to {params_file}: {str(e)}")
            return False
            
    def get_param(self, param_path, default=None):
        """
        Get a parameter value using a dot-separated path
        
        Parameters:
        -----------
        param_path : str
            Dot-separated path to the parameter (e.g., 'ema.period')
        default : any, optional
            Default value to return if parameter is not found
            
        Returns:
        --------
        any
            Parameter value, or default if not found
        """
        keys = param_path.split('.')
        value = self.params
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_param(self, param_path, value):
        """
        Set a parameter value using a dot-separated path
        
        Parameters:
        -----------
        param_path : str
            Dot-separated path to the parameter (e.g., 'ema.period')
        value : any
            Value to set
            
        Returns:
        --------
        bool
            True if parameter was set successfully, False otherwise
        """
        keys = param_path.split('.')
        param_dict = self.params
        
        try:
            # Navigate to the final container
            for key in keys[:-1]:
                if key not in param_dict:
                    param_dict[key] = {}
                param_dict = param_dict[key]
                
            # Set the value
            param_dict[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"Error setting parameter {param_path}: {str(e)}")
            return False
            
    def reset_to_defaults(self):
        """Reset all parameters to default values"""
        self.params = DEFAULT_PARAMS.copy()
        logger.info("Reset parameters to default values")
        
    def get_extension_threshold(self, timeframe):
        """
        Get the extension threshold for a specific timeframe
        
        Parameters:
        -----------
        timeframe : str
            Timeframe string (e.g., '1d', '1h', '15m')
            
        Returns:
        --------
        float
            Extension threshold as a percentage (0.01 = 1%)
        """
        # Get thresholds dictionary
        thresholds = self.get_param('ema.extension_thresholds', {})
        
        # Try to get the threshold for the specific timeframe
        threshold = thresholds.get(timeframe)
        
        # If not found, try to find the closest matching timeframe
        if threshold is None:
            # Extract timeframe value and unit
            import re
            match = re.match(r'(\d+)([a-zA-Z]+)', timeframe)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                # Find thresholds with the same unit
                same_unit = {k: v for k, v in thresholds.items() if k.endswith(unit)}
                
                if same_unit:
                    # Get the closest value
                    closest_tf = min(same_unit.keys(), key=lambda k: abs(int(re.match(r'(\d+)([a-zA-Z]+)', k).group(1)) - value))
                    threshold = thresholds[closest_tf]
                    logger.info(f"Using threshold from {closest_tf} for {timeframe}")
        
        # If still not found, use a default
        if threshold is None:
            threshold = 1.0  # Default to 1%
            logger.warning(f"No threshold found for {timeframe}, using default: {threshold}%")
            
        return threshold / 100.0  # Convert from percentage to decimal
            
    def _update_nested_dict(self, d, u):
        """
        Update a nested dictionary with values from another dictionary
        
        Parameters:
        -----------
        d : dict
            Dictionary to update
        u : dict
            Dictionary with update values
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
                
    def create_parameter_variants(self, param_path, values):
        """
        Create multiple parameter variants for testing
        
        Parameters:
        -----------
        param_path : str
            Dot-separated path to the parameter (e.g., 'ema.period')
        values : list
            List of values to test
            
        Returns:
        --------
        list
            List of StrategyParameters objects with different values
        """
        variants = []
        
        for value in values:
            # Create a new parameters object
            variant = StrategyParameters()
            
            # Copy the current parameters
            variant.params = self.params.copy()
            
            # Set the test value
            variant.set_param(param_path, value)
            
            variants.append(variant)
            
        return variants
        
    def __str__(self):
        """String representation of parameters"""
        return json.dumps(self.params, indent=2)

# Create a global instance
STRATEGY_PARAMS = StrategyParameters() 