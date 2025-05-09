# Using MT9 EMA Custom Indicators in JupyterLab

This guide shows how to leverage your existing MT9 EMA Backtester indicator framework within JupyterLab for interactive development and visualization.

## Setting Up

1. **Launch JupyterLab**
   ```bash
   # Navigate to your project directory
   cd c:\Users\Trade\PycharmProjects\mtfema_backtester
   
   # Launch JupyterLab
   jupyter lab
   ```

2. **Create a New Notebook**
   - Click "File" → "New" → "Notebook"
   - Select Python kernel

3. **Add Project Path to Notebook**
   ```python
   # First cell: Add project path to Python path
   import os
   import sys
   
   # Add project root to path
   project_root = os.path.abspath('.')
   if project_root not in sys.path:
       sys.path.append(project_root)
   ```

## Sample Notebook Code

Here's a complete example you can copy into a notebook:

```python
# Cell 1: Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mtfema_backtester.utils.indicators import Indicator, create_indicator, get_indicator_registry
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Cell 2: Load or create sample data
def get_sample_data(days=100):
    """Generate sample price data"""
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate synthetic price data
    n = len(dates)
    base_price = 100
    trend = np.linspace(0, 20, n)  # Upward trend
    noise = np.random.normal(0, 1, n)  # Random noise
    cycle = 10 * np.sin(np.linspace(0, 8*np.pi, n))  # Cyclic component
    
    # Generate OHLC data
    close = base_price + trend + noise + cycle
    high = close + np.random.uniform(0.1, 2, n)
    low = close - np.random.uniform(0.1, 2, n)
    open_price = close.shift(1).fillna(close[0])
    
    # Create DataFrame
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100, 1000, n)
    }, index=dates)
    
    return data

# Get data
data = get_sample_data(days=100)

# Display first few rows
data.head()

# Cell 3: Create a custom indicator
class RSI(Indicator):
    """Relative Strength Index indicator"""
    
    def __init__(self, period=14, source='close', name=None):
        params = {'period': period, 'source': source}
        super().__init__(name or "RSI", params)
        self.required_columns = [source]
    
    def _validate_params(self):
        if self.params['period'] <= 0:
            raise ValueError(f"Period must be positive, got {self.params['period']}")
    
    def _calculate(self, data):
        period = self.params['period']
        source = self.params['source']
        
        # Calculate price changes
        delta = data[source].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return {'value': rsi}

# Register the indicator
registry = get_indicator_registry()
registry.register("RSI", RSI)

# Cell 4: Calculate indicator values
# Create indicator instances
ema9 = create_indicator("EMA", period=9, source='close')
ema21 = create_indicator("EMA", period=21, source='close')
rsi = create_indicator("RSI", period=14)

# Calculate indicators
ema9_results = ema9.calculate(data)
ema21_results = ema21.calculate(data)
rsi_results = rsi.calculate(data)

# Cell 5: Interactive visualization with Plotly
# Create subplots
fig = make_subplots(rows=2, cols=1, 
                   shared_xaxes=True,
                   vertical_spacing=0.1,
                   subplot_titles=('Price with EMAs', 'RSI'),
                   row_heights=[0.7, 0.3])

# Add price data
fig.add_trace(
    go.Candlestick(x=data.index,
                  open=data['open'],
                  high=data['high'],
                  low=data['low'],
                  close=data['close'],
                  name='Price'),
    row=1, col=1
)

# Add EMAs
fig.add_trace(
    go.Scatter(x=data.index, y=ema9_results['value'], 
              name='EMA 9',
              line=dict(color='blue', width=1)),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=data.index, y=ema21_results['value'], 
              name='EMA 21',
              line=dict(color='red', width=1)),
    row=1, col=1
)

# Add RSI
fig.add_trace(
    go.Scatter(x=data.index, y=rsi_results['value'], 
              name='RSI 14',
              line=dict(color='purple', width=1)),
    row=2, col=1
)

# Add RSI levels
fig.add_shape(
    type="line", x0=data.index[0], x1=data.index[-1], y0=70, y1=70,
    line=dict(color="red", width=1, dash="dash"),
    row=2, col=1
)

fig.add_shape(
    type="line", x0=data.index[0], x1=data.index[-1], y0=30, y1=30,
    line=dict(color="green", width=1, dash="dash"),
    row=2, col=1
)

# Update layout
fig.update_layout(
    title='Custom Indicator Analysis',
    xaxis_title='Date',
    height=800,
    width=1000,
    showlegend=True,
    xaxis_rangeslider_visible=False
)

# Show figure
fig.show()

# Cell 6: Generate trading signals based on indicator values
signals = pd.DataFrame(index=data.index)
signals['signal'] = 0  # No signal

# EMA crossover strategy
for i in range(1, len(data)):
    # Check for crossover (EMA 9 crosses above EMA 21)
    if (ema9_results['value'].iloc[i-1] <= ema21_results['value'].iloc[i-1] and
        ema9_results['value'].iloc[i] > ema21_results['value'].iloc[i] and
        rsi_results['value'].iloc[i] > 50):
        signals['signal'].iloc[i] = 1  # Buy signal
    
    # Check for crossunder (EMA 9 crosses below EMA 21)
    elif (ema9_results['value'].iloc[i-1] >= ema21_results['value'].iloc[i-1] and
          ema9_results['value'].iloc[i] < ema21_results['value'].iloc[i] and
          rsi_results['value'].iloc[i] < 50):
        signals['signal'].iloc[i] = -1  # Sell signal

# Display signals
signals[signals['signal'] != 0].head(10)

# Cell 7: Visualize signals on price chart
# Create subplots
fig = make_subplots(rows=2, cols=1, 
                   shared_xaxes=True,
                   vertical_spacing=0.1,
                   subplot_titles=('Price with Signals', 'RSI'),
                   row_heights=[0.7, 0.3])

# Add price data
fig.add_trace(
    go.Candlestick(x=data.index,
                  open=data['open'],
                  high=data['high'],
                  low=data['low'],
                  close=data['close'],
                  name='Price'),
    row=1, col=1
)

# Add EMAs
fig.add_trace(
    go.Scatter(x=data.index, y=ema9_results['value'], 
              name='EMA 9',
              line=dict(color='blue', width=1)),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=data.index, y=ema21_results['value'], 
              name='EMA 21',
              line=dict(color='red', width=1)),
    row=1, col=1
)

# Add Buy signals
buy_signals = signals[signals['signal'] == 1]
fig.add_trace(
    go.Scatter(
        x=buy_signals.index,
        y=data.loc[buy_signals.index, 'low'] - 2,  # Place markers below candles
        mode='markers',
        marker=dict(symbol='triangle-up', size=15, color='green'),
        name='Buy Signal'
    ),
    row=1, col=1
)

# Add Sell signals
sell_signals = signals[signals['signal'] == -1]
fig.add_trace(
    go.Scatter(
        x=sell_signals.index,
        y=data.loc[sell_signals.index, 'high'] + 2,  # Place markers above candles
        mode='markers',
        marker=dict(symbol='triangle-down', size=15, color='red'),
        name='Sell Signal'
    ),
    row=1, col=1
)

# Add RSI
fig.add_trace(
    go.Scatter(x=data.index, y=rsi_results['value'], 
              name='RSI 14',
              line=dict(color='purple', width=1)),
    row=2, col=1
)

# Update layout
fig.update_layout(
    title='Trading Signals Based on Custom Indicators',
    xaxis_title='Date',
    height=800,
    width=1000,
    showlegend=True,
    xaxis_rangeslider_visible=False
)

# Show figure
fig.show()
```

## Connecting to Your Backend API

To connect your notebook to your existing backend API:

```python
import requests
import json

# API endpoints
API_BASE = "http://localhost:5000/api"

# Function to load data from API
def get_data_from_api(symbol, timeframe, start_date, end_date):
    endpoint = f"{API_BASE}/data/historical"
    params = {
        "symbol": symbol,
        "timeframe": timeframe,
        "start_date": start_date,
        "end_date": end_date
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return pd.DataFrame(response.json()["data"])
    else:
        raise Exception(f"API request failed: {response.text}")

# Function to run backtest via API
def run_backtest_api(strategy_params):
    endpoint = f"{API_BASE}/backtest/run"
    response = requests.post(endpoint, json=strategy_params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed: {response.text}")

# Example usage
data = get_data_from_api("NQ", "1D", "2023-01-01", "2023-04-01")
```

## Interactive Parameter Exploration

Use Jupyter widgets for interactive parameter adjustment:

```python
import ipywidgets as widgets
from IPython.display import display

# Create sliders for parameters
period_slider = widgets.IntSlider(value=14, min=2, max=50, step=1, description='RSI Period:')
threshold_slider = widgets.IntSlider(value=70, min=50, max=90, step=1, description='Overbought:')

# Function to update visualization based on parameters
def update_chart(period, threshold):
    # Create RSI with new parameters
    rsi_custom = create_indicator("RSI", period=period)
    rsi_results = rsi_custom.calculate(data)
    
    # Create visualization
    # (similar to previous code, but with updated parameters)
    # ...
    
    return fig

# Create interactive widget
interactive_chart = widgets.interactive(update_chart, 
                                      period=period_slider, 
                                      threshold=threshold_slider)

# Display widget
display(interactive_chart)
```

## Advanced: Building a Custom Indicator Library

You can create a notebook that serves as your personal indicator library:

```python
# Create a cell for each custom indicator
# Then run registry.register() for each one

# Example:
class SuperTrend(Indicator):
    """SuperTrend indicator implementation"""
    # implementation...

class VWAP(Indicator):
    """Volume Weighted Average Price"""
    # implementation...

# Register all custom indicators
registry = get_indicator_registry()
registry.register("SuperTrend", SuperTrend)
registry.register("VWAP", VWAP)

# Save the list for future reference
custom_indicators = registry.list_indicators()
print(f"Available indicators: {custom_indicators}")
```

## Next Steps

1. **Create a Dashboard-Notebook Bridge**: Implement functions to export indicators created in notebooks to your dashboard
2. **Create a Notebook Indicator Template**: Start with a template notebook for quick indicator development
3. **Build an Indicator Testing Suite**: Create notebooks specifically for validating indicator performance
