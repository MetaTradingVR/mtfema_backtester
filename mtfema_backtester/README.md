# Multi-Timeframe 9 EMA Extension Strategy Backtester

A comprehensive backtesting system for the Multi-Timeframe 9 EMA Extension trading strategy, built with Python 3.13.

[![CI](https://github.com/yourusername/mtfema-backtester/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mtfema-backtester/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/mtfema-backtester/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/mtfema-backtester)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://yourusername.github.io/mtfema-backtester/)

## Overview

The Multi-Timeframe 9 EMA Extension (MT 9 EMA) strategy is a powerful trading approach that uses the 9-period Exponential Moving Average (EMA) across multiple timeframes to identify high-probability trading opportunities. This backtester provides a robust framework for testing and optimizing this strategy across various financial instruments and market conditions.

### Key Features

- **Multi-Timeframe Analysis**: Test the strategy using data from multiple timeframes simultaneously
- **Comprehensive Backtesting**: Get detailed performance metrics, trade statistics, and equity curves
- **Broker Integration**: Connect to live or paper trading accounts through supported brokers (Tradovate, Rithmic)
- **Visualization Tools**: Interactive charts and reports for analyzing strategy performance
- **Plugin System**: Extend the system with custom indicators, strategies, and visualizations
- **Web-Based UI**: User-friendly interface built with Streamlit

## Installation

### Requirements

- Python 3.10 or higher
- pip package manager

### Setup

This project implements a complete backtesting system for a trading strategy based on price extensions from the 9-period Exponential Moving Average (EMA) across multiple timeframes. The strategy looks for significant extensions away from the 9 EMA, followed by retracements and reclamations, with confluence across different timeframes.

## Features

- **Multi-Timeframe Analysis**: Combines signals from different timeframes for higher conviction trades
- **Customizable Parameters**: Adjust extension thresholds, EMA periods, and risk parameters through YAML/JSON configs
- **Comprehensive Backtesting**: Full P&L calculation, drawdown analysis, and trade statistics
- **Advanced Visualization**: Charts showing entries, exits, equity curve, and key metrics
- **Performance Optimization**: Numba JIT compilation and vectorized calculations for faster backtesting
- **Parallel Processing**: Multi-core parameter optimization with multiprocessing
- **Trade Journal**: Automatic logging of all trade decisions and outcomes
- **Community Features**: Share setups, signals, and join the MT 9 EMA trader community
- **Robust Testing**: Comprehensive test suite with unit, integration, and performance tests
- **Continuous Integration**: GitHub Actions workflow for automated testing and quality control

## System Architecture

The system is organized into several key components:

### Core Components
- `strategy/`: Contains the trading logic implementation
  - `signal_generator.py`: Identifies potential trading setups
  - `target_manager.py`: Manages take profit and stop loss levels
  - `conflict_resolver.py`: Resolves conflicting signals from different timeframes
  - `extension_detector.py`: Detects price extensions from the EMA
  - `reclamation_detector.py`: Identifies EMA reclamation patterns
  - `pullback_validator.py`: Validates pullback conditions before entry
- `backtest/`: The backtesting engine that simulates trades
  - `backtest_engine.py`: Standard backtesting implementation
  - `optimized_backtester.py`: High-performance implementation with Numba
- `indicators/`: Technical indicators implementation (EMAs, etc.)
- `visualization/`: Tools for generating charts and performance graphs
- `dashboard/`: Interactive dashboard for analyzing results
- `optimization/`: Parameter optimization framework

### Support Modules
- `data/`: Data handling and preprocessing
- `utils/`: Utility functions and helpers
- `config_manager.py`: Enhanced configuration management system
- `journal/`: Trade journaling and logging
- `community/`: Community integration and sharing features

## Installation

### Requirements

- Python 3.7+ (Python 3.13 recommended)
- Jupyter Lab (for interactive development)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mtfema-backtester.git
   cd mtfema-backtester
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r mtfema_backtester/requirements.txt
   ```

4. TA-Lib Installation:
   
   This project can use either TA-Lib or pandas-ta for technical indicators. 
   
   To install TA-Lib automatically (for Windows), run:
   ```
   python -m mtfema_backtester.utils.talib_installer
   ```
   
   This script will automatically detect your Python version and download the appropriate wheel package.
   
   For manual installation:
   
   - **Windows**: 
     ```
     pip install --no-cache-dir -U https://github.com/mrjbq7/ta-lib/releases/download/0.4.24/TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
     ```
     (Replace cp310 with your Python version)
   
   - **macOS**:
     ```
     brew install ta-lib
     pip install ta-lib
     ```
   
   - **Linux**:
     ```
     apt-get install ta-lib
     pip install ta-lib
     ```

5. (Optional) Install performance enhancement packages:
   ```
   pip install numba
   ```

## Usage

### Basic Usage

Run the backtester in test mode to verify setup:

```bash
python -m mtfema_backtester.main --mode test --symbol SPY --timeframes 1d,1h,15m --save-plots
```

### Running a Backtest

To run a full backtest:

```bash
python -m mtfema_backtester.main --mode backtest --symbol SPY --timeframes 1d,1h,15m --start-date 2022-01-01 --end-date 2023-01-01 --initial-capital 100000 --risk-per-trade 1.0 --save-plots
```

### Using Configuration Files

Create a `config.yaml` file with your parameters:

```yaml
data:
  default_symbol: "SPY"
  default_timeframes: ["1d", "1h", "15m"]
  cache_enabled: true

strategy:
  ema:
    period: 9
    extension_thresholds:
      "1d": 1.5
      "1h": 1.0
      "15m": 0.8

backtest:
  initial_capital: 100000
  commission: 0.001
  slippage: 0.001
```

Then run with:

```bash
python -m mtfema_backtester.main --config config.yaml
```

### Running Tests

Run the test suite with:

```bash
pytest
```

For specific test types:

```bash
# Run only unit tests
pytest tests/unit

# Run only performance tests
pytest tests/performance

# Run tests with coverage report
pytest --cov=mtfema_backtester
```

## Performance Optimization

The system includes performance optimizations for faster backtesting:

- **Numba JIT**: Automatically accelerates computational bottlenecks if installed
- **Vectorized Operations**: Uses NumPy vectorized operations where possible
- **Multiprocessing**: Parallel execution of parameter optimization
- **Memory Optimization**: Optimized data structures for reduced memory usage

To enable high-performance mode:

```python
from mtfema_backtester.backtest.optimized_backtester import OptimizedBacktester

backtester = OptimizedBacktester(
    use_numba=True,
    use_multiprocessing=True,
    max_workers=4  # Adjust based on your CPU cores
)

# Run backtest
results = backtester.run(data, strategy_func, strategy_params)
```

## Configuration System

The enhanced configuration system supports:

- YAML and JSON configuration files
- Environment variable overrides
- Hierarchical configuration with dot notation access
- Type validation and conversion

Example usage:

```python
from mtfema_backtester.config_manager import get_config

# Get global config instance
config = get_config()

# Get a specific value
ema_period = config.get_typed('strategy.ema.period', int, 9)

# Get a complete section
risk_params = config.get_section('risk')
```

Environment variable overrides follow this pattern:

```
MTFEMA_STRATEGY__EMA_PERIOD=21
MTFEMA_BACKTEST__INITIAL_CAPITAL=200000
```

## Output

Backtest results are saved to the output directory (default: `./output/backtest/`) and include:

- Equity curve CSV
- Trade list CSV
- Performance metrics JSON
- Interactive HTML plots (if `--save-plots` is specified)
- Performance benchmarks (if using the optimized backtester)

## Development and Contributing

### Testing

This project uses pytest for testing:

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for component interactions
- `tests/performance/`: Performance benchmarks and scaling tests

### Continuous Integration

The project uses GitHub Actions for CI/CD:

- Runs tests on multiple Python versions
- Performs code quality checks (flake8, black, mypy)
- Generates test coverage reports
- Builds documentation

### Documentation

Documentation is built using MkDocs and hosted on GitHub Pages.

## License

MIT

## Acknowledgements

This project was created with the help of Claude AI.