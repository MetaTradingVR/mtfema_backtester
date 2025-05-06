"""
Built-in Bollinger Bands indicator plugin
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from mtfema_backtester.plugins.base_plugin import BaseIndicatorPlugin

class BollingerBandsIndicator(BaseIndicatorPlugin):
    """Bollinger Bands indicator plugin."""
    
    @property
    def name(self) -> str:
        return "Bollinger Bands"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Bollinger Bands - volatility bands placed above and below a moving average"
    
    @property
    def author(self) -> str:
        return "MT 9 EMA Backtester Team"
    
    @property
    def category(self) -> str:
        return "Volatility"
    
    @property
    def default_params(self) -> Dict[str, Any]:
        return {
            "period": 20,
            "std_dev": 2.0,
            "apply_to": "close",
            "ma_type": "sma"
        }
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            data: DataFrame with OHLCV data
            **kwargs: Additional parameters (period, std_dev, apply_to, ma_type)
            
        Returns:
            DataFrame with middle band, upper band, and lower band
        """
        # Validate parameters
        params = self.validate_parameters(kwargs)
        period = params["period"]
        std_dev = params["std_dev"]
        price_col = params["apply_to"].lower()
        ma_type = params["ma_type"].lower()
        
        # Get price series
        if price_col not in data.columns:
            raise ValueError(f"Column '{price_col}' not found in data")
            
        prices = data[price_col]
        
        # Calculate middle band (moving average)
        if ma_type == "sma":
            middle_band = prices.rolling(window=period).mean()
        elif ma_type == "ema":
            middle_band = prices.ewm(span=period, adjust=False).mean()
        else:
            raise ValueError(f"Unsupported MA type: {ma_type}")
        
        # Calculate standard deviation
        std = prices.rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        # Create result DataFrame
        result = pd.DataFrame({
            'middle_band': middle_band,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'bandwidth': (upper_band - lower_band) / middle_band,
            'b_percent': (prices - lower_band) / (upper_band - lower_band)
        })
        
        return result
