import os
import json
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
import importlib
import importlib.util
import sys
import inspect
import traceback
import pandas_ta as ta

from ..models.indicator import CustomIndicator, IndicatorParameter
from ..config import DATA_DIR, TEMP_DATA_DIR

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DATA_DIR, exist_ok=True)

# Standard indicator wrapper
class StandardIndicatorWrapper:
    """A wrapper for standard indicators from libraries like pandas-ta."""
    
    def __init__(self, library_name: str, indicator_name: str, params: Dict[str, Any] = None):
        self.library_name = library_name
        self.indicator_name = indicator_name
        self.params = params or {}
        
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate the indicator using the specified library."""
        if self.library_name == 'pandas_ta':
            return self._calculate_pandas_ta(data)
        elif self.library_name == 'talib':
            return self._calculate_talib(data)
        else:
            raise ValueError(f"Unsupported library: {self.library_name}")
    
    def _calculate_pandas_ta(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate using pandas-ta library."""
        try:
            # Get the function from pandas_ta
            indicator_func = getattr(ta, self.indicator_name, None)
            if not indicator_func:
                raise ValueError(f"Indicator '{self.indicator_name}' not found in pandas_ta")
            
            # Handle special cases for certain indicators
            if self.indicator_name == 'sma':
                result = indicator_func(close=data[self.params.get('source', 'close')], length=self.params.get('length', 20))
                return {'sma': result}
                
            elif self.indicator_name == 'ema':
                result = indicator_func(close=data[self.params.get('source', 'close')], length=self.params.get('length', 20))
                return {'ema': result}
                
            elif self.indicator_name == 'macd':
                result = indicator_func(
                    close=data[self.params.get('source', 'close')], 
                    fast=self.params.get('fast_length', 12),
                    slow=self.params.get('slow_length', 26),
                    signal=self.params.get('signal_length', 9)
                )
                # MACD returns a DataFrame with multiple columns
                return {col: result[col] for col in result.columns}
                
            elif self.indicator_name == 'rsi':
                result = indicator_func(
                    close=data[self.params.get('source', 'close')], 
                    length=self.params.get('length', 14),
                    drift=self.params.get('drift', 1)
                )
                return {'rsi': result}
                
            elif self.indicator_name == 'bbands':
                result = indicator_func(
                    close=data[self.params.get('source', 'close')],
                    length=self.params.get('length', 20),
                    std=self.params.get('std_dev', 2.0)
                )
                # BBands returns a DataFrame with multiple columns
                return {col: result[col] for col in result.columns}
                
            elif self.indicator_name == 'stoch':
                result = indicator_func(
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    k=self.params.get('k_length', 14),
                    d=self.params.get('d_length', 3),
                    smooth_k=self.params.get('smooth_k', 3)
                )
                # Stochastic returns a DataFrame with multiple columns
                return {col: result[col] for col in result.columns}
                
            elif self.indicator_name == 'atr':
                result = indicator_func(
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    length=self.params.get('length', 14)
                )
                return {'atr': result}
                
            elif self.indicator_name == 'obv':
                result = indicator_func(close=data['close'], volume=data['volume'])
                return {'obv': result}
                
            elif self.indicator_name == 'vwap':
                result = indicator_func(
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    volume=data['volume'],
                    anchor=self.params.get('anchor', 'D')
                )
                return {'vwap': result}
            
            # Generic case - try to infer parameters
            else:
                # Get function signature
                sig = inspect.signature(indicator_func)
                
                # Match parameters with function signature
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param_name in self.params:
                        kwargs[param_name] = self.params[param_name]
                    elif param_name in data.columns:
                        kwargs[param_name] = data[param_name]
                
                result = indicator_func(**kwargs)
                
                # Handle different return types
                if isinstance(result, pd.DataFrame):
                    return {col: result[col] for col in result.columns}
                elif isinstance(result, pd.Series):
                    return {self.indicator_name: result}
                elif isinstance(result, tuple):
                    return {f"{self.indicator_name}_{i}": series for i, series in enumerate(result)}
                else:
                    raise ValueError(f"Unexpected return type from indicator: {type(result)}")
                
        except Exception as e:
            traceback.print_exc()
            raise ValueError(f"Error calculating {self.indicator_name}: {str(e)}")
    
    def _calculate_talib(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate using TA-Lib library."""
        # This would be implemented similar to pandas_ta but using the talib package
        # For now, we're focusing on pandas_ta implementation
        raise NotImplementedError("TA-Lib support is not yet implemented")

class IndicatorService:
    """Service for managing and calculating indicators."""
    
    def __init__(self):
        self.indicators_file = os.path.join(DATA_DIR, "indicators.json")
        self.standard_indicators_file = os.path.join(DATA_DIR, "standard_indicators.json")
        
        # Initialize indicator storage files if they don't exist
        if not os.path.exists(self.indicators_file):
            with open(self.indicators_file, "w") as f:
                json.dump([], f)
                
        if not os.path.exists(self.standard_indicators_file):
            with open(self.standard_indicators_file, "w") as f:
                json.dump([], f)
    
    # Custom indicators methods
    def get_all_indicators(self) -> List[CustomIndicator]:
        """Get all custom indicators."""
        try:
            with open(self.indicators_file, "r") as f:
                return [CustomIndicator(**indicator) for indicator in json.load(f)]
        except Exception as e:
            print(f"Error loading indicators: {e}")
            return []
    
    def get_indicator_by_id(self, indicator_id: str) -> Optional[CustomIndicator]:
        """Get a specific indicator by ID."""
        indicators = self.get_all_indicators()
        for indicator in indicators:
            if indicator.id == indicator_id:
                return indicator
        return None
    
    def create_indicator(self, indicator: CustomIndicator) -> str:
        """Create a new custom indicator."""
        indicators = self.get_all_indicators()
        
        # Generate ID and timestamps
        indicator_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Update indicator
        indicator_dict = indicator.dict()
        indicator_dict["id"] = indicator_id
        indicator_dict["created_at"] = now
        indicator_dict["updated_at"] = now
        
        # Add to list and save
        indicators.append(indicator_dict)
        with open(self.indicators_file, "w") as f:
            json.dump(indicators, f, indent=2)
        
        return indicator_id
    
    def update_indicator(self, indicator_id: str, indicator: CustomIndicator) -> bool:
        """Update an existing custom indicator."""
        indicators = self.get_all_indicators()
        
        # Find the indicator
        for i, ind in enumerate(indicators):
            if ind.id == indicator_id:
                # Update indicator
                indicator_dict = indicator.dict()
                indicator_dict["id"] = indicator_id
                indicator_dict["created_at"] = ind.created_at
                indicator_dict["updated_at"] = datetime.now().isoformat()
                
                # Replace in list and save
                indicators[i] = indicator_dict
                with open(self.indicators_file, "w") as f:
                    json.dump([ind.dict() if isinstance(ind, CustomIndicator) else ind for ind in indicators], f, indent=2)
                
                return True
        
        return False
    
    def delete_indicator(self, indicator_id: str) -> bool:
        """Delete a custom indicator."""
        indicators = self.get_all_indicators()
        
        # Filter out the indicator to delete
        updated_indicators = [ind.dict() if isinstance(ind, CustomIndicator) else ind 
                             for ind in indicators if ind.id != indicator_id]
        
        if len(updated_indicators) < len(indicators):
            with open(self.indicators_file, "w") as f:
                json.dump(updated_indicators, f, indent=2)
            return True
        
        return False
    
    # Standard indicators methods
    def get_standard_indicators_catalog(self) -> List[Dict[str, Any]]:
        """Get the catalog of available standard indicators."""
        # In a real implementation, this might come from a database
        # Here we're defining our catalog of supported indicators
        
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
                            {"name": "length", "type": "int", "default": 20, "min": 2, "max": 500, "description": "Period length"},
                            {"name": "source", "type": "string", "default": "close", "options": ["open", "high", "low", "close", "volume"], "description": "Input data source"}
                        ],
                        "inputs": ["close"],
                        "outputs": ["sma"],
                        "source_library": "pandas_ta"
                    },
                    {
                        "id": "ema",
                        "name": "Exponential Moving Average (EMA)",
                        "category": "trend",
                        "description": "Exponential moving average that gives more weight to recent prices",
                        "parameters": [
                            {"name": "length", "type": "int", "default": 20, "min": 2, "max": 500, "description": "Period length"},
                            {"name": "source", "type": "string", "default": "close", "options": ["open", "high", "low", "close", "volume"], "description": "Input data source"}
                        ],
                        "inputs": ["close"],
                        "outputs": ["ema"],
                        "source_library": "pandas_ta"
                    },
                    {
                        "id": "macd",
                        "name": "Moving Average Convergence Divergence (MACD)",
                        "category": "trend",
                        "description": "Trend-following momentum indicator showing relationship between two moving averages",
                        "parameters": [
                            {"name": "fast_length", "type": "int", "default": 12, "min": 2, "max": 500, "description": "Fast EMA period"},
                            {"name": "slow_length", "type": "int", "default": 26, "min": 2, "max": 500, "description": "Slow EMA period"},
                            {"name": "signal_length", "type": "int", "default": 9, "min": 2, "max": 500, "description": "Signal period"},
                            {"name": "source", "type": "string", "default": "close", "options": ["open", "high", "low", "close"], "description": "Input data source"}
                        ],
                        "inputs": ["close"],
                        "outputs": ["macd", "macd_signal", "macd_histogram"],
                        "source_library": "pandas_ta"
                    }
                ]
            },
            {
                "id": "momentum",
                "name": "Momentum Indicators",
                "description": "Indicators that measure market strength or weakness",
                "indicators": [
                    {
                        "id": "rsi",
                        "name": "Relative Strength Index (RSI)",
                        "category": "momentum",
                        "description": "Momentum oscillator that measures the speed and change of price movements",
                        "parameters": [
                            {"name": "length", "type": "int", "default": 14, "min": 2, "max": 500, "description": "Period length"},
                            {"name": "source", "type": "string", "default": "close", "options": ["open", "high", "low", "close"], "description": "Input data source"},
                            {"name": "drift", "type": "int", "default": 1, "min": 1, "max": 10, "description": "Offset or shift"}
                        ],
                        "inputs": ["close"],
                        "outputs": ["rsi"],
                        "source_library": "pandas_ta"
                    },
                    {
                        "id": "stoch",
                        "name": "Stochastic Oscillator",
                        "category": "momentum",
                        "description": "Compares a particular closing price to a range of prices over a certain period of time",
                        "parameters": [
                            {"name": "k_length", "type": "int", "default": 14, "min": 2, "max": 500, "description": "%K length"},
                            {"name": "d_length", "type": "int", "default": 3, "min": 1, "max": 500, "description": "%D length"},
                            {"name": "smooth_k", "type": "int", "default": 3, "min": 1, "max": 500, "description": "%K smoothing"}
                        ],
                        "inputs": ["high", "low", "close"],
                        "outputs": ["stoch_k", "stoch_d"],
                        "source_library": "pandas_ta"
                    }
                ]
            },
            {
                "id": "volatility",
                "name": "Volatility Indicators",
                "description": "Indicators that measure market volatility",
                "indicators": [
                    {
                        "id": "bbands",
                        "name": "Bollinger Bands",
                        "category": "volatility",
                        "description": "Volatility bands placed above and below a moving average",
                        "parameters": [
                            {"name": "length", "type": "int", "default": 20, "min": 2, "max": 500, "description": "SMA period length"},
                            {"name": "std_dev", "type": "float", "default": 2.0, "min": 0.1, "max": 10.0, "description": "Standard deviation multiplier"},
                            {"name": "source", "type": "string", "default": "close", "options": ["open", "high", "low", "close"], "description": "Input data source"}
                        ],
                        "inputs": ["close"],
                        "outputs": ["bbands_upper", "bbands_middle", "bbands_lower"],
                        "source_library": "pandas_ta"
                    },
                    {
                        "id": "atr",
                        "name": "Average True Range (ATR)",
                        "category": "volatility",
                        "description": "Measures market volatility by decomposing the range of each bar",
                        "parameters": [
                            {"name": "length", "type": "int", "default": 14, "min": 1, "max": 500, "description": "Period length"}
                        ],
                        "inputs": ["high", "low", "close"],
                        "outputs": ["atr"],
                        "source_library": "pandas_ta"
                    }
                ]
            },
            {
                "id": "volume",
                "name": "Volume Indicators",
                "description": "Indicators that use volume data to determine market strength",
                "indicators": [
                    {
                        "id": "obv",
                        "name": "On-Balance Volume (OBV)",
                        "category": "volume",
                        "description": "Cumulative total of up and down volume",
                        "parameters": [],
                        "inputs": ["close", "volume"],
                        "outputs": ["obv"],
                        "source_library": "pandas_ta"
                    },
                    {
                        "id": "vwap",
                        "name": "Volume Weighted Average Price (VWAP)",
                        "category": "volume",
                        "description": "Average price weighted by volume",
                        "parameters": [
                            {"name": "anchor", "type": "string", "default": "D", "options": ["D", "W", "M"], "description": "Anchor period (day, week, month)"}
                        ],
                        "inputs": ["high", "low", "close", "volume"],
                        "outputs": ["vwap"],
                        "source_library": "pandas_ta"
                    }
                ]
            }
        ]
    
    def get_standard_indicator_definition(self, definition_id: str) -> Optional[Dict[str, Any]]:
        """Get a standard indicator definition by ID."""
        catalog = self.get_standard_indicators_catalog()
        
        for category in catalog:
            for indicator in category["indicators"]:
                if indicator["id"] == definition_id:
                    return indicator
        
        return None
    
    def get_all_standard_indicators(self) -> List[Dict[str, Any]]:
        """Get all saved configured standard indicators."""
        try:
            with open(self.standard_indicators_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading standard indicators: {e}")
            return []
    
    def get_standard_indicator_by_id(self, indicator_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific configured standard indicator by ID."""
        indicators = self.get_all_standard_indicators()
        for indicator in indicators:
            if indicator["id"] == indicator_id:
                return indicator
        return None
    
    def save_standard_indicator(self, indicator: Dict[str, Any]) -> str:
        """Save a configured standard indicator."""
        indicators = self.get_all_standard_indicators()
        
        # Generate ID and timestamps if new
        if not indicator.get("id"):
            indicator["id"] = str(uuid.uuid4())
            indicator["created_at"] = datetime.now().isoformat()
            
        indicator["updated_at"] = datetime.now().isoformat()
        
        # Check if updating existing
        for i, ind in enumerate(indicators):
            if ind["id"] == indicator["id"]:
                indicators[i] = indicator
                with open(self.standard_indicators_file, "w") as f:
                    json.dump(indicators, f, indent=2)
                return indicator["id"]
        
        # Add new
        indicators.append(indicator)
        with open(self.standard_indicators_file, "w") as f:
            json.dump(indicators, f, indent=2)
        
        return indicator["id"]
    
    def delete_standard_indicator(self, indicator_id: str) -> bool:
        """Delete a configured standard indicator."""
        indicators = self.get_all_standard_indicators()
        
        # Filter out the indicator to delete
        updated_indicators = [ind for ind in indicators if ind["id"] != indicator_id]
        
        if len(updated_indicators) < len(indicators):
            with open(self.standard_indicators_file, "w") as f:
                json.dump(updated_indicators, f, indent=2)
            return True
        
        return False
    
    def calculate_standard_indicator(
        self, 
        definition_id: str,
        parameters: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, List[float]]:
        """Calculate a standard indicator with the given parameters."""
        definition = self.get_standard_indicator_definition(definition_id)
        if not definition:
            raise ValueError(f"Indicator definition not found: {definition_id}")
        
        # Create the indicator wrapper
        wrapper = StandardIndicatorWrapper(
            library_name=definition["source_library"],
            indicator_name=definition_id,
            params=parameters
        )
        
        # Calculate the indicator
        result = wrapper.calculate(data)
        
        # Convert to lists for JSON serialization
        return {key: values.fillna(0).tolist() for key, values in result.items()}
    
    def generate_sample_data(self, periods: int = 100, include_price: bool = True) -> pd.DataFrame:
        """Generate sample OHLCV data for testing indicators."""
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=periods)
        dates = pd.date_range(start=start_date, end=end_date, periods=periods)
        
        # Generate random price data
        base_price = 100.0
        volatility = 2.0
        
        # Generate random walk
        returns = np.random.normal(0, volatility, periods) / 100
        price_changes = np.cumprod(1 + returns)
        prices = base_price * price_changes
        
        # Create OHLCV data
        data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, periods)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            'close': prices,
            'volume': np.random.normal(100000, 20000, periods) * (1 + np.abs(returns) * 10)
        }, index=dates)
        
        # Ensure high >= open, close, low and low <= open, close
        data['high'] = data[['high', 'open', 'close']].max(axis=1)
        data['low'] = data[['low', 'open', 'close']].min(axis=1)
        
        # Ensure all volumes are positive
        data['volume'] = data['volume'].clip(lower=10000)
        
        return data 