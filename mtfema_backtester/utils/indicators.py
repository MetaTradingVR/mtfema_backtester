"""
Modular indicator system for MT 9 EMA Backtester.

This module provides a flexible framework for creating, registering,
and using technical indicators in a consistent way throughout the system.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable, Type
import logging
from abc import ABC, abstractmethod
import inspect

# Will be imported after class definitions to avoid circular imports
ZigZag = None
FibRetracement = None

logger = logging.getLogger(__name__)

class Indicator(ABC):
    """
    Base class for all technical indicators.
    
    Implements the Template Method pattern for indicator calculation.
    All derived indicators should implement the _calculate method.
    """
    
    def __init__(self, name: str = None, params: Dict[str, Any] = None):
        """
        Initialize the indicator.
        
        Args:
            name: Optional custom name for this indicator instance
            params: Dictionary of parameters for this indicator
        """
        self.params = params or {}
        self.name = name or self.__class__.__name__
        self.result = None
        self.required_columns = ['open', 'high', 'low', 'close']
        self._validate_params()
    
    @abstractmethod
    def _calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate the indicator values.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary of indicator name to Series of values
        """
        pass
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate the indicator and store the result.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary of indicator name to Series of values
        """
        # Validate input data
        self._validate_data(data)
        
        # Calculate indicator
        self.result = self._calculate(data)
        
        # Add indicator name prefix to keys if not already present
        prefixed_result = {}
        for key, value in self.result.items():
            if not key.startswith(f"{self.name}_"):
                prefixed_result[f"{self.name}_{key}"] = value
            else:
                prefixed_result[key] = value
        
        self.result = prefixed_result
        return self.result
    
    def _validate_params(self) -> None:
        """
        Validate indicator parameters.
        """
        # Derived classes should override this method if they need validation
        pass
    
    def _validate_data(self, data: pd.DataFrame) -> None:
        """
        Validate input data for required columns.
        
        Args:
            data: DataFrame with price data
            
        Raises:
            ValueError: If required columns are missing
        """
        missing_columns = [col for col in self.required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in data: {missing_columns}")
    
    def get_value(self, key: str = None) -> pd.Series:
        """
        Get a specific indicator value.
        
        Args:
            key: Key for the specific indicator value, or None for default
            
        Returns:
            Series with indicator values
        """
        if self.result is None:
            raise ValueError("Indicator not calculated yet. Call calculate() first.")
            
        if key is None:
            # If no key specified, return the first value
            return next(iter(self.result.values()))
            
        # Try with and without prefix
        prefixed_key = f"{self.name}_{key}" if not key.startswith(f"{self.name}_") else key
        
        if prefixed_key in self.result:
            return self.result[prefixed_key]
        elif key in self.result:
            return self.result[key]
        else:
            raise KeyError(f"Key {key} not found in indicator result. Available keys: {list(self.result.keys())}")
            
    def apply_to_dataframe(self, data: pd.DataFrame, include_all: bool = True) -> pd.DataFrame:
        """
        Apply the indicator to a DataFrame, adding new columns.
        
        Args:
            data: DataFrame with price data
            include_all: Whether to include all indicator values or just the primary one
            
        Returns:
            DataFrame with added indicator columns
        """
        if self.result is None:
            self.calculate(data)
            
        result_df = data.copy()
        
        if include_all:
            # Add all indicator values as columns
            for key, series in self.result.items():
                result_df[key] = series
        else:
            # Add just the primary indicator value
            key = next(iter(self.result.keys()))
            result_df[key] = self.result[key]
            
        return result_df


class EMA(Indicator):
    """
    Exponential Moving Average indicator.
    """
    
    def __init__(self, period: int = 9, source: str = 'close', name: str = None):
        """
        Initialize the EMA indicator.
        
        Args:
            period: EMA period
            source: Source column for calculation
            name: Optional custom name for this indicator
        """
        params = {'period': period, 'source': source}
        super().__init__(name or f"EMA{period}", params)
        self.required_columns = [source]
    
    def _validate_params(self) -> None:
        """
        Validate EMA parameters.
        """
        if self.params['period'] <= 0:
            raise ValueError(f"Period must be positive, got {self.params['period']}")
            
        if not isinstance(self.params['source'], str):
            raise ValueError(f"Source must be a string, got {type(self.params['source'])}")
    
    def _calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate the EMA.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with 'value' key containing EMA values
        """
        period = self.params['period']
        source = self.params['source']
        
        # Calculate EMA
        ema = data[source].ewm(span=period, adjust=False).mean()
        
        return {'value': ema}


class BollingerBands(Indicator):
    """
    Bollinger Bands indicator.
    """
    
    def __init__(self, period: int = 20, deviation: float = 2.0, source: str = 'close', name: str = None):
        """
        Initialize the Bollinger Bands indicator.
        
        Args:
            period: Moving average period
            deviation: Standard deviation multiplier
            source: Source column for calculation
            name: Optional custom name for this indicator
        """
        params = {'period': period, 'deviation': deviation, 'source': source}
        super().__init__(name or "BB", params)
        self.required_columns = [source]
    
    def _validate_params(self) -> None:
        """
        Validate Bollinger Bands parameters.
        """
        if self.params['period'] <= 0:
            raise ValueError(f"Period must be positive, got {self.params['period']}")
            
        if self.params['deviation'] <= 0:
            raise ValueError(f"Deviation must be positive, got {self.params['deviation']}")
    
    def _calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with 'middle', 'upper', and 'lower' keys
        """
        period = self.params['period']
        deviation = self.params['deviation']
        source = self.params['source']
        
        # Calculate middle band (SMA)
        middle = data[source].rolling(window=period).mean()
        
        # Calculate standard deviation
        std = data[source].rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper = middle + (std * deviation)
        lower = middle - (std * deviation)
        
        # Calculate bandwidth
        bandwidth = (upper - lower) / middle * 100
        
        # Calculate percent B
        percent_b = (data[source] - lower) / (upper - lower)
        
        return {
            'middle': middle,
            'upper': upper,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }


class PaperFeet(Indicator):
    """
    PaperFeet indicator (custom indicator for trend confirmation).
    
    This indicator uses RSI, EMAs, and price action to determine market trend condition.
    It outputs color codes: 0=red (downtrend), 1=yellow (caution/transition), 2=green (uptrend)
    """
    
    def __init__(self, 
                 rsi_period: int = 14, 
                 fast_ema: int = 9, 
                 slow_ema: int = 21, 
                 signal_ema: int = 5,
                 source: str = 'close', 
                 name: str = None):
        """
        Initialize the PaperFeet indicator.
        
        Args:
            rsi_period: RSI calculation period
            fast_ema: Fast EMA period
            slow_ema: Slow EMA period
            signal_ema: Signal EMA period for smoothing
            source: Source column for calculation
            name: Optional custom name for this indicator
        """
        params = {
            'rsi_period': rsi_period,
            'fast_ema': fast_ema,
            'slow_ema': slow_ema,
            'signal_ema': signal_ema,
            'source': source
        }
        super().__init__(name or "PaperFeet", params)
        self.required_columns = ['open', 'high', 'low', 'close']
    
    def _calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate the PaperFeet indicator.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with indicator values
        """
        source = self.params['source']
        
        # Calculate RSI
        delta = data[source].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=self.params['rsi_period']).mean()
        avg_loss = loss.rolling(window=self.params['rsi_period']).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate EMAs
        fast_ema = data[source].ewm(span=self.params['fast_ema'], adjust=False).mean()
        slow_ema = data[source].ewm(span=self.params['slow_ema'], adjust=False).mean()
        
        # Calculate trend strength
        trend_strength = ((fast_ema / slow_ema) - 1) * 100
        
        # Apply signal EMA to trend strength
        signal = trend_strength.ewm(span=self.params['signal_ema'], adjust=False).mean()
        
        # Determine color based on conditions
        # Initialize color series with NaN
        color = pd.Series(np.nan, index=data.index)
        
        # Green (2): Strong uptrend
        green_condition = (
            (fast_ema > slow_ema) & 
            (signal > 0) & 
            (rsi > 50)
        )
        
        # Red (0): Strong downtrend
        red_condition = (
            (fast_ema < slow_ema) & 
            (signal < 0) & 
            (rsi < 50)
        )
        
        # Yellow (1): Transition or caution
        # All other conditions not red or green
        
        # Set colors
        color[green_condition] = 2  # Green
        color[red_condition] = 0    # Red
        color[~(green_condition | red_condition)] = 1  # Yellow for all other conditions
        
        # Forward fill any remaining NaNs
        color = color.fillna(method='ffill')
        
        return {
            'rsi': rsi,
            'fast_ema': fast_ema,
            'slow_ema': slow_ema,
            'trend_strength': trend_strength,
            'signal': signal,
            'color': color
        }


class IndicatorRegistry:
    """
    Registry for indicator classes and instances.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for global indicator registry access."""
        if cls._instance is None:
            cls._instance = super(IndicatorRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the indicator registry."""
        # Skip re-initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.indicators = {}
        self.instances = {}
        
        # Register built-in indicators
        self.register("EMA", EMA)
        self.register("BollingerBands", BollingerBands)
        self.register("PaperFeet", PaperFeet)
        self.register("ZigZag", ZigZag)
        self.register("FibRetracement", FibRetracement)
        
        logger.info("Indicator registry initialized")
    
    def register(self, name: str, indicator_class: Type[Indicator]) -> None:
        """
        Register an indicator class.
        
        Args:
            name: Name of the indicator
            indicator_class: Indicator class
        """
        if not inspect.isclass(indicator_class) or not issubclass(indicator_class, Indicator):
            raise ValueError(f"indicator_class must be a subclass of Indicator, got {indicator_class}")
            
        self.indicators[name] = indicator_class
        logger.info(f"Registered indicator: {name}")
    
    def create(self, name: str, **params) -> Indicator:
        """
        Create an indicator instance.
        
        Args:
            name: Name of the indicator
            **params: Parameters for the indicator
            
        Returns:
            Indicator instance
        """
        if name not in self.indicators:
            raise ValueError(f"Indicator {name} not registered")
            
        indicator_class = self.indicators[name]
        instance = indicator_class(**params)
        
        # Generate a unique instance ID based on parameters
        instance_id = f"{name}_{hash(frozenset(params.items()))}"
        self.instances[instance_id] = instance
        
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[Indicator]:
        """
        Get an existing indicator instance by ID.
        
        Args:
            instance_id: ID of the indicator instance
            
        Returns:
            Indicator instance or None if not found
        """
        return self.instances.get(instance_id)
    
    def list_indicators(self) -> List[str]:
        """
        List all registered indicators.
        
        Returns:
            List of indicator names
        """
        return list(self.indicators.keys())


# Helper functions for easier access

def get_indicator_registry() -> IndicatorRegistry:
    """
    Get the global indicator registry instance.
    
    Returns:
        IndicatorRegistry instance
    """
    return IndicatorRegistry()

def create_indicator(name: str, **params) -> Indicator:
    """
    Create an indicator using the global registry.
    
    Args:
        name: Name of the indicator
        **params: Parameters for the indicator
        
    Returns:
        Indicator instance
    """
    registry = get_indicator_registry()
    return registry.create(name, **params)

def apply_indicator(data: pd.DataFrame, name: str, **params) -> pd.DataFrame:
    """
    Apply an indicator to a DataFrame.
    
    Args:
        data: DataFrame with price data
        name: Name of the indicator
        **params: Parameters for the indicator
        
    Returns:
        DataFrame with added indicator columns
    """
    indicator = create_indicator(name, **params)
    return indicator.apply_to_dataframe(data)


# Import indicator implementations to avoid circular imports
from mtfema_backtester.utils.zigzag import ZigZag, FibRetracement
