"""
MT9 EMA Backtester Indicator Templates

This file contains reusable templates for:
1. Creating custom indicators
2. Registering indicators
3. Using indicators in strategies

Simply copy these templates and customize them for your needs.
"""

import pandas as pd
import numpy as np

# Import from the MT9 framework
from mtfema_backtester.utils.indicators import Indicator, create_indicator, get_indicator_registry

# ===============================================================
# TEMPLATE 1: CREATING A CUSTOM INDICATOR
# ===============================================================

class TemplateIndicator(Indicator):
    """
    Template for creating a custom indicator.
    Replace this with your indicator description.
    """
    
    def __init__(self, param1=10, param2=20, name=None):
        """
        Initialize your indicator parameters here.
        
        Args:
            param1: First parameter description
            param2: Second parameter description
            name: Optional custom name for this indicator
        """
        # Store all parameters in this dictionary
        params = {
            'param1': param1, 
            'param2': param2
        }
        
        # Initialize the base class
        super().__init__(name or "MyIndicator", params)
        
        # List the data columns your indicator requires
        self.required_columns = ['open', 'high', 'low', 'close']
    
    def _validate_params(self) -> None:
        """
        Optional: Validate your indicator parameters.
        Raise ValueError if any parameters are invalid.
        """
        if self.params['param1'] <= 0:
            raise ValueError(f"param1 must be positive, got {self.params['param1']}")
    
    def _calculate(self, data: pd.DataFrame) -> dict:
        """
        Calculate your indicator values here.
        This is where your core logic goes.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with calculated values
        """
        # Get parameters from self.params
        param1 = self.params['param1']
        param2 = self.params['param2']
        
        # Your calculation logic here
        # Example: Simple moving averages with different periods
        value1 = data['close'].rolling(window=param1).mean()
        value2 = data['close'].rolling(window=param2).mean()
        
        # Return dictionary of result values
        return {
            'value1': value1,       # Will be automatically prefixed with indicator name
            'value2': value2,       # e.g., "MyIndicator_value1" 
            'diff': value1 - value2  # e.g., "MyIndicator_diff"
        }


# ===============================================================
# TEMPLATE 2: REGISTERING A CUSTOM INDICATOR
# ===============================================================

def register_template_indicator():
    """
    Template for registering a custom indicator.
    This makes your indicator available through create_indicator().
    """
    # Get the global indicator registry
    registry = get_indicator_registry()
    
    # Register your indicator with a name
    registry.register("TemplateIndicator", TemplateIndicator)
    
    # You can register multiple indicators
    # registry.register("AnotherIndicator", AnotherIndicator)
    
    # Verify registration
    print(f"Available indicators: {registry.list_indicators()}")


# ===============================================================
# TEMPLATE 3: USING INDICATORS IN STRATEGIES
# ===============================================================

def use_indicators_template(data):
    """
    Template for using indicators in strategies.
    
    Args:
        data: DataFrame with OHLCV price data
    """
    # STEP 1: Create indicator instances
    # Built-in indicator (example)
    ema = create_indicator("EMA", period=9, source='close')
    
    # Custom indicator (example)
    custom_ind = create_indicator("TemplateIndicator", param1=10, param2=20)
    
    # STEP 2: Calculate indicator values
    ema_results = ema.calculate(data)
    custom_results = custom_ind.calculate(data)
    
    # STEP 3: Access indicator values
    ema_values = ema_results['value']  # EMA has a 'value' result
    custom_value1 = custom_results['MyIndicator_value1']
    custom_value2 = custom_results['MyIndicator_value2']
    
    # STEP 4: Generate signals based on indicator values
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0  # Initialize with no signal
    
    # Example signal logic
    for i in range(1, len(data)):
        # Buy signal example
        if custom_value1.iloc[i-1] < custom_value2.iloc[i-1] and custom_value1.iloc[i] > custom_value2.iloc[i]:
            signals['signal'].iloc[i] = 1  # Buy signal
        
        # Sell signal example
        elif custom_value1.iloc[i-1] > custom_value2.iloc[i-1] and custom_value1.iloc[i] < custom_value2.iloc[i]:
            signals['signal'].iloc[i] = -1  # Sell signal
    
    return signals


# ===============================================================
# USAGE EXAMPLE
# ===============================================================

def example_workflow():
    """
    Example workflow showing how to put everything together.
    """
    # 1. First, register your custom indicator
    register_template_indicator()
    
    # 2. Load or generate price data
    # (Replace this with your actual data loading code)
    dates = pd.date_range(start='2023-01-01', end='2023-03-01', freq='D')
    n = len(dates)
    data = pd.DataFrame({
        'open': np.random.normal(100, 5, n),
        'high': np.random.normal(102, 5, n),
        'low': np.random.normal(98, 5, n),
        'close': np.random.normal(101, 5, n),
        'volume': np.random.randint(1000, 10000, n)
    }, index=dates)
    
    # 3. Use indicators to generate signals
    signals = use_indicators_template(data)
    
    # 4. Now you can use these signals in your backtest or trading system
    print(f"Generated {signals['signal'].abs().sum()} trading signals")
    
    return {
        'data': data,
        'signals': signals
    }


if __name__ == "__main__":
    # This code runs when you execute this file directly
    print("Running indicator templates example...")
    example_workflow()
    print("Done! You can use these templates in your own strategies.")
