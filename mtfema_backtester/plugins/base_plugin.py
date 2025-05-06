"""
Base classes for MT 9 EMA Backtester plugins
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional, List, Union, Tuple

class BasePlugin(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the plugin version."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return the plugin description."""
        pass
    
    @property
    @abstractmethod
    def author(self) -> str:
        """Return the plugin author."""
        pass

class BaseIndicatorPlugin(BasePlugin):
    """Base class for indicator plugins."""
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Calculate the indicator values.
        
        Args:
            data: DataFrame with OHLCV data
            **kwargs: Additional parameters for the indicator
            
        Returns:
            Series with indicator values
        """
        pass
    
    @property
    @abstractmethod
    def default_params(self) -> Dict[str, Any]:
        """Return the default parameters for the indicator."""
        pass
    
    @property
    def category(self) -> str:
        """Return the indicator category."""
        return "General"
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and return corrected parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            Dictionary of validated parameters
        """
        result = self.default_params.copy()
        result.update(params)
        return result

class BaseStrategyPlugin(BasePlugin):
    """Base class for strategy plugins."""
    
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame], **kwargs) -> pd.Series:
        """
        Generate trade signals based on the strategy logic.
        
        Args:
            data: Dictionary of DataFrames for different timeframes
            **kwargs: Additional parameters for the strategy
            
        Returns:
            Series with trade signals (1 for buy, -1 for sell, 0 for no trade)
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate required indicators for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    @property
    @abstractmethod
    def default_params(self) -> Dict[str, Any]:
        """Return the default parameters for the strategy."""
        pass
    
    @property
    def required_timeframes(self) -> List[str]:
        """Return the required timeframes for the strategy."""
        return ["D"]  # Default to daily timeframe
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and return corrected parameters.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            Dictionary of validated parameters
        """
        result = self.default_params.copy()
        result.update(params)
        return result

class BaseVisualizationPlugin(BasePlugin):
    """Base class for visualization plugins."""
    
    @abstractmethod
    def create_figure(self, data: pd.DataFrame, results: Dict[str, Any], **kwargs) -> Any:
        """
        Create a visualization figure.
        
        Args:
            data: DataFrame with OHLCV and indicator data
            results: Dictionary with backtest results
            **kwargs: Additional parameters for the visualization
            
        Returns:
            Figure object (plotly, matplotlib, etc.)
        """
        pass
    
    @property
    @abstractmethod
    def supported_libraries(self) -> List[str]:
        """Return the supported visualization libraries."""
        pass
