# Configuration Guide

The Multi-Timeframe 9 EMA Extension Strategy Backtester features a robust configuration system that allows you to customize all aspects of your strategy and backtests without modifying code.

## Configuration Overview

The system supports:

- **Multiple file formats**: YAML and JSON
- **Environment variable overrides**: Set config values via environment variables
- **Hierarchical configuration**: Access values using dot notation
- **Type validation**: Automatic type checking and conversion
- **Default values**: Fallback values when a setting isn't specified
- **Configuration sections**: Group related settings together

## Configuration File

The default configuration is stored in `mtfema_backtester/config.yaml`, but you can create your own configuration file:

```yaml
# Data Configuration
data:
  default_symbol: "SPY"
  default_timeframes: ["1d", "1h", "15m"]
  default_lookback_days: 365
  cache_enabled: true
  cache_directory: "./data/cache"

# Strategy Parameters
strategy:
  # EMA Configuration
  ema:
    period: 9
    apply_to: "Close"  # Price field to use for EMA calculation
    extension_thresholds:
      "1d": 1.5  # Daily timeframe extension threshold (%)
      "1h": 1.0  # Hourly timeframe extension threshold (%)
      "15m": 0.8  # 15-min timeframe extension threshold (%)
    reclamation_confirmation_bars: 2  # Bars needed to confirm EMA reclamation
  
  # Bollinger Bands Configuration
  bollinger:
    period: 20
    std_dev: 2.0
    apply_to: "Close"
    squeeze_threshold: 0.1  # Threshold for identifying volatility squeezes
  
  # Fibonacci Levels
  fibonacci:
    levels: [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618]
    extension_levels: [1.0, 1.272, 1.618, 2.0, 2.618]
    pullback_zone: [0.382, 0.618]  # Zone for valid pullbacks

# Risk Management
risk:
  max_risk_per_trade: 1.0  # Maximum risk per trade (% of account)
  default_stop_loss: 2.0   # Default stop loss (% from entry)
  target_risk_reward: 2.0  # Minimum risk/reward ratio
  trailing_stop:
    enabled: true
    activation: 1.0      # Activate trailing stop after this R multiple
    step: 0.5             # Step size for trailing stop adjustments
  position_sizing: "fixed_risk"  # Options: fixed_risk, fixed_size, kelly

# Backtesting Configuration
backtest:
  commission: 0.001         # Commission per trade (%)
  slippage: 0.001           # Slippage per trade (%)
  initial_capital: 100000   # Initial capital for backtesting
  execution_delay: 0        # Execution delay in bars
  contract_size: 100        # Contract size for position sizing calculations
  enable_fractional_shares: true  # Allow fractional share positions

# Performance Configuration
performance:
  use_numba: true
  use_multiprocessing: true
  max_workers: 4
  vectorized_operations: true
  memory_optimization: true
```

## Using a Custom Configuration

To use a custom configuration file:

```bash
python -m mtfema_backtester.main --config path/to/your/config.yaml
```

## Environment Variable Overrides

You can override any configuration value using environment variables with the following pattern:

```
MTFEMA_SECTION__KEY=value
```

For example:

```bash
# Set the EMA period to 21
export MTFEMA_STRATEGY__EMA__PERIOD=21

# Set the initial capital to 200000
export MTFEMA_BACKTEST__INITIAL_CAPITAL=200000

# Disable Numba JIT compilation
export MTFEMA_PERFORMANCE__USE_NUMBA=false
```

In Windows PowerShell:

```powershell
$env:MTFEMA_STRATEGY__EMA__PERIOD = "21"
$env:MTFEMA_BACKTEST__INITIAL_CAPITAL = "200000"
$env:MTFEMA_PERFORMANCE__USE_NUMBA = "false"
```

## Using the Configuration in Code

The configuration system provides a Python API for accessing settings in your code:

```python
from mtfema_backtester.config_manager import get_config

# Get the global configuration instance
config = get_config()

# Get a simple value
ema_period = config.get('strategy.ema.period')  # Returns 9 by default

# Get a value with type checking
initial_capital = config.get_typed('backtest.initial_capital', float)  # Returns 100000.0

# Get a value with a default fallback
max_workers = config.get('performance.max_workers', 4)  # Returns 4 if not set

# Get an entire section
risk_params = config.get_section('risk')  # Returns a dictionary with all risk settings
```

## Configuration Sections

### Data Configuration

Controls data loading and caching:

| Setting | Type | Description |
|---------|------|-------------|
| `data.default_symbol` | string | Default symbol to use if none specified |
| `data.default_timeframes` | list | List of default timeframes to analyze |
| `data.default_lookback_days` | int | Number of days of historical data to load |
| `data.cache_enabled` | bool | Whether to cache downloaded data |
| `data.cache_directory` | string | Directory for cached data files |

### Strategy Configuration

Controls the trading strategy parameters:

| Setting | Type | Description |
|---------|------|-------------|
| `strategy.ema.period` | int | EMA period for the strategy (default: 9) |
| `strategy.ema.apply_to` | string | Price field to use for EMA calculation |
| `strategy.ema.extension_thresholds` | dict | Extension thresholds by timeframe |
| `strategy.bollinger.period` | int | Period for Bollinger Bands calculation |
| `strategy.bollinger.std_dev` | float | Standard deviation for Bollinger Bands |
| `strategy.fibonacci.levels` | list | Fibonacci retracement levels |
| `strategy.fibonacci.pullback_zone` | list | Fibonacci zone for valid pullbacks |

### Risk Management

Controls position sizing and risk parameters:

| Setting | Type | Description |
|---------|------|-------------|
| `risk.max_risk_per_trade` | float | Maximum risk per trade (% of account) |
| `risk.default_stop_loss` | float | Default stop loss (% from entry) |
| `risk.target_risk_reward` | float | Minimum risk/reward ratio |
| `risk.trailing_stop.enabled` | bool | Whether to use trailing stops |
| `risk.position_sizing` | string | Position sizing method |

### Backtest Configuration

Controls backtesting parameters:

| Setting | Type | Description |
|---------|------|-------------|
| `backtest.commission` | float | Commission per trade (%) |
| `backtest.slippage` | float | Slippage per trade (%) |
| `backtest.initial_capital` | float | Initial capital for backtesting |
| `backtest.execution_delay` | int | Execution delay in bars |
| `backtest.enable_fractional_shares` | bool | Allow fractional share positions |

### Performance Configuration

Controls performance optimization:

| Setting | Type | Description |
|---------|------|-------------|
| `performance.use_numba` | bool | Whether to use Numba JIT compilation |
| `performance.use_multiprocessing` | bool | Whether to use multiprocessing |
| `performance.max_workers` | int | Maximum number of worker processes |
| `performance.vectorized_operations` | bool | Use vectorized operations |
| `performance.memory_optimization` | bool | Use memory optimization techniques |

## Advanced Configuration

### Using JSON Format

You can also use JSON format for configuration:

```json
{
  "data": {
    "default_symbol": "SPY",
    "default_timeframes": ["1d", "1h", "15m"],
    "cache_enabled": true
  },
  "strategy": {
    "ema": {
      "period": 9,
      "extension_thresholds": {
        "1d": 1.5,
        "1h": 1.0,
        "15m": 0.8
      }
    }
  }
}
```

### Programmatically Setting Configuration

You can set configuration values programmatically:

```python
from mtfema_backtester.config_manager import ConfigManager

# Create a custom configuration manager
config = ConfigManager(config_file="path/to/config.yaml")

# Use it in your code
ema_period = config.get('strategy.ema.period')
```

## Best Practices

1. **Start with a copy of the default config**: 
   ```bash
   cp mtfema_backtester/config.yaml ./my_strategy.yaml
   ```

2. **Use environment variables for temporary changes**:
   ```bash
   export MTFEMA_BACKTEST__INITIAL_CAPITAL=50000 python -m mtfema_backtester.main
   ```

3. **Create separate config files for different strategies**:
   ```
   strategy1.yaml
   strategy2.yaml
   ```

4. **Use nested configuration**:
   ```yaml
   strategy:
     ema_crossover:
       enabled: true
       fast_period: 9
       slow_period: 21
     bollinger_bands:
       enabled: false
   ```

5. **Save benchmark configurations** to reproduce results later.

## Debugging Configuration

To debug configuration issues, you can print the entire configuration:

```python
from mtfema_backtester.config_manager import get_config
import json

config = get_config()
print(json.dumps(config.dump(), indent=2))
```

This will show all settings, including defaults and overrides. 