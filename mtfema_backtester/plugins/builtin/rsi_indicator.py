"""
Built-in RSI (Relative Strength Index) indicator plugin
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from mtfema_backtester.plugins.base_plugin import BaseIndicatorPlugin

class RSIIndicator(BaseIndicatorPlugin):
    """RSI (Relative Strength Index) indicator plugin."""
    
    @property
    def name(self) -> str:
        return "RSI"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Relative Strength Index (RSI) - measures the speed and magnitude of price movements"
    
    @property
    def author(self) -> str:
        return "MT 9 EMA Backtester Team"
    
    @property
    def category(self) -> str:
        return "Momentum"
    
    @property
    def default_params(self) -> Dict[str, Any]:
        return {
            "period": 14,
            "apply_to": "close",
            "oversold": 30,
            "overbought": 70
        }
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Calculate RSI values.
        
        Args:
            data: DataFrame with OHLCV data
            **kwargs: Additional parameters (period, apply_to)
            
        Returns:
            Series with RSI values
        """
        # Validate parameters
        params = self.validate_parameters(kwargs)
        period = params["period"]
        price_col = params["apply_to"].lower()
        
        # Get price series
        if price_col not in data.columns:
            raise ValueError(f"Column '{price_col}' not found in data")
            
        prices = data[price_col]
        
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.copy()
        losses = delta.copy()
        
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
