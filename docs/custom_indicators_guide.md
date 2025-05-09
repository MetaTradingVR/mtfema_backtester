# MT9 EMA Backtester: Custom Indicators Guide

## Introduction

Custom indicators are the building blocks of advanced trading strategies. The MT9 EMA Backtester provides a powerful framework for creating, testing, and implementing custom technical indicators in your trading workflow. This guide explains everything you need to know about working with custom indicators in the MT9 ecosystem.

## Table of Contents

1. [Understanding the Indicator Framework](#understanding-the-indicator-framework)
2. [Using Built-in Indicators](#using-built-in-indicators)
3. [Creating Custom Indicators](#creating-custom-indicators)
4. [Testing and Visualization](#testing-and-visualization)
5. [Integration with Strategies](#integration-with-strategies)
6. [JupyterLab Integration](#jupyterlab-integration)
7. [Dashboard Integration](#dashboard-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Understanding the Indicator Framework

The MT9 EMA Backtester uses a modular indicator system with these key components:

### Core Components

- **Indicator (Base Class)**: All indicators inherit from this abstract base class
- **IndicatorRegistry**: Manages all available indicators in the system
- **Helper Functions**: `create_indicator()`, `get_indicator_registry()`, and `apply_indicator()`

### How Indicators Work

1. An indicator is a calculation applied to price or volume data
2. Each indicator has a set of parameters that control its behavior
3. Indicators return one or more result series (pandas.Series objects)
4. The calculation results are cached for efficiency
5. Indicators can be composed (one indicator can use another's output)

## Using Built-in Indicators

The system comes with several built-in indicators:

- **EMA**: Exponential Moving Average
- **SMA**: Simple Moving Average
- **BollingerBands**: Bollinger Bands
- **ATR**: Average True Range
- **ZigZag**: Price reversal indicator
- **FibRetracement**: Fibonacci retracement levels

### Example Usage

```python
from mtfema_backtester.utils.indicators import create_indicator

# Create an EMA indicator with period=9
ema = create_indicator("EMA", period=9, source='close')

# Calculate EMA on price data
results = ema.calculate(price_data)

# Access the EMA values
ema_values = results['value']
```

## Creating Custom Indicators

Creating a custom indicator involves:

1. Creating a class that inherits from `Indicator`
2. Implementing the `_calculate` method
3. Registering the indicator with the registry

### Step-by-Step Process

#### 1. Create the Indicator Class

```python
from mtfema_backtester.utils.indicators import Indicator

class CustomIndicator(Indicator):
    """Custom indicator description"""
    
    def __init__(self, param1=10, param2=20, name=None):
        params = {'param1': param1, 'param2': param2}
        super().__init__(name or "Custom", params)
        self.required_columns = ['close', 'volume']  # Required data columns
    
    def _validate_params(self):
        """Optional: Validate parameters"""
        if self.params['param1'] <= 0:
            raise ValueError(f"param1 must be positive, got {self.params['param1']}")
    
    def _calculate(self, data):
        """Calculate indicator values"""
        param1 = self.params['param1']
        param2 = self.params['param2']
        
        # Your calculation logic here
        result = data['close'] * data['volume'].rolling(param1).mean() / data['volume'].rolling(param2).mean()
        
        return {'value': result}
```

#### 2. Register the Indicator

```python
from mtfema_backtester.utils.indicators import get_indicator_registry

# Get the indicator registry
registry = get_indicator_registry()

# Register the custom indicator
registry.register("CustomIndicator", CustomIndicator)
```

#### 3. Use the Custom Indicator

```python
# Create an instance
custom = create_indicator("CustomIndicator", param1=15, param2=30)

# Calculate values
results = custom.calculate(price_data)

# Access the results
values = results['Custom_value']  # Prefixed with indicator name
```

### Common Indicator Patterns

#### Price Action Indicators

```python
def _calculate(self, data):
    # Calculation based on price movement patterns
    return {'pattern': pattern_series}
```

#### Volume-Based Indicators

```python
def _calculate(self, data):
    # Calculation incorporating volume
    return {'value': volume_weighted_series}
```

#### Oscillators

```python
def _calculate(self, data):
    # Oscillator calculation (typically bounded values)
    return {'value': oscillator_series}
```

## Testing and Visualization

### Basic Visualization

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(data.index, data['close'], label='Price')
plt.plot(data.index, indicator_results['value'], label='Indicator')
plt.legend()
plt.show()
```

### Advanced Visualization with Plotly

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Create subplot
fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

# Add price chart
fig.add_trace(go.Candlestick(
    x=data.index, open=data['open'], high=data['high'], 
    low=data['low'], close=data['close']), 
    row=1, col=1)

# Add indicator
fig.add_trace(go.Scatter(
    x=data.index, y=indicator_results['value'], 
    name='Custom Indicator'), 
    row=2, col=1)

fig.update_layout(height=800, title='Custom Indicator Test')
fig.show()
```

## Integration with Strategies

### Using Indicators in Strategy Logic

```python
def generate_signals(data, params):
    # Create indicators
    ema_short = create_indicator("EMA", period=params['short_period'])
    ema_long = create_indicator("EMA", period=params['long_period'])
    custom = create_indicator("CustomIndicator", param1=params['custom_param1'])
    
    # Calculate indicators
    ema_short_results = ema_short.calculate(data)
    ema_long_results = ema_long.calculate(data)
    custom_results = custom.calculate(data)
    
    # Generate signals based on indicator values
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0
    
    # Crossover strategy with custom indicator filter
    for i in range(1, len(data)):
        if (ema_short_results['value'].iloc[i-1] < ema_long_results['value'].iloc[i-1] and
            ema_short_results['value'].iloc[i] > ema_long_results['value'].iloc[i] and
            custom_results['Custom_value'].iloc[i] > params['custom_threshold']):
            signals['signal'].iloc[i] = 1  # Buy
            
        elif (ema_short_results['value'].iloc[i-1] > ema_long_results['value'].iloc[i-1] and
              ema_short_results['value'].iloc[i] < ema_long_results['value'].iloc[i]):
            signals['signal'].iloc[i] = -1  # Sell
    
    return signals
```

## JupyterLab Integration

See the `examples/jupyter_integration_guide.md` file for detailed instructions on using custom indicators in JupyterLab.

## Dashboard Integration

See the `examples/dashboard_integration.md` file for information on the planned dashboard integration for custom indicators.

## Best Practices

### Performance Optimization

1. **Vectorized Operations**: Use pandas/numpy vectorized operations when possible
2. **Avoid Loops**: Minimize Python loops for calculations
3. **Caching**: Take advantage of the built-in caching system

### Code Organization

1. **Group Related Indicators**: Organize similar indicators in the same module
2. **Clear Documentation**: Document parameters and calculation logic
3. **Meaningful Names**: Use descriptive names for result keys

### Testing

1. **Create Test Cases**: Test with known values and edge cases
2. **Validate Against Other Implementations**: Compare results with established libraries
3. **Benchmark Performance**: Monitor calculation time for large datasets

## Troubleshooting

### Common Issues

1. **Missing Data Columns**: Ensure your data has all required columns
2. **Parameter Validation**: Check that parameters are within valid ranges
3. **NaN Values**: Handle NaN values appropriately in calculations

### Debugging Tips

1. **Intermediate Calculations**: Output intermediate steps for complex calculations
2. **Visual Inspection**: Plot results to visually identify issues
3. **Compare with Simple Cases**: Test with simplified data to verify logic

## Examples

Find complete examples in:

- `examples/custom_indicators_example.py`: Complete working example
- `examples/indicator_templates.py`: Templates for common indicator types
