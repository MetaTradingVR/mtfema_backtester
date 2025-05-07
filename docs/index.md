# 📋 For the latest project status, implementation progress, and roadmap, see [PROJECT_STATUS.md](PROJECT_STATUS.md). This is the canonical, timestamped source for all planning and progress updates.

# MT 9 EMA Extension Strategy Backtester

Welcome to the documentation for the Multi-Timeframe 9 EMA Extension Strategy Backtester.

## Strategy Overview

The MT 9 EMA Extension Strategy is based on identifying significant price extensions from the 9-period Exponential Moving Average (EMA) across multiple timeframes. The strategy uses a hierarchical approach to timeframes, allowing for systematic entry and exit management.

### Key Strategy Components

1. **9 EMA Extension Detection**
   - Identifies when price has extended significantly from the 9 EMA
   - Uses dynamic thresholds based on timeframe volatility
   - Generates extension signals for potential reversal setups

2. **EMA Reclamation**
   - Detects when price returns to and reclaims the 9 EMA after an extension
   - Confirms the end of an extension phase
   - Provides potential entry signals

3. **Fibonacci Pullbacks**
   - Validates entries based on Fibonacci retracement levels
   - Ensures high-probability entry points
   - Optimizes risk-reward ratios

4. **Progressive Targeting**
   - Follows targets through the timeframe hierarchy
   - Uses higher timeframe structures for exit management
   - Maximizes profit potential while managing risk

## Backtester Features

- **Multi-Timeframe Analysis**: Support for any combination of timeframes
- **Customizable Parameters**: Extensive configuration options
- **Performance Metrics**: Comprehensive trade statistics
- **Interactive Visualization**: HTML-based charts and dashboards
- **Optimization Tools**: Parameter testing and optimization

## Getting Started

To get started with the backtester:

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run a test with the NQ futures data:
   ```
   python run_nq_test.py --mode test
   ```

3. Generate and customize parameters:
   ```
   python run_nq_test.py --generate-params my_params.json
   python run_nq_test.py --params-file my_params.json
   ```

## Operation Modes

- **Test Mode**: Visualize indicators without generating trades
- **Backtest Mode**: Evaluate trading performance with specific parameters
- **Optimize Mode**: Test multiple parameter combinations

## Resources

- [Strategy Parameters Documentation](parameters.md)
- [Performance Metrics Guide](metrics.md)
- [Current Project Status](PROJECT_STATUS.md)
- [Development Roadmap](../DEVELOPMENT.md)

## Contributing

Contributions to the backtester are welcome. Please see the [contribution guidelines](CONTRIBUTING.md) for more information.

## Recent Enhancements

The project has been enhanced with several key improvements:

1. **[Enhanced Documentation](enhancements.md#1-enhanced-documentation)**: Comprehensive documentation with architecture overview, installation guide, and usage examples.

2. **[Testing Framework](enhancements.md#2-testing-framework)**: Complete pytest setup with unit, integration, and performance tests.

3. **[Performance Optimization](enhancements.md#3-performance-optimization)**: Numba JIT-accelerated backtester with vectorized operations.

4. **[Continuous Integration](enhancements.md#4-continuous-integration)**: GitHub Actions workflow for automated testing and code quality checks.

5. **[Enhanced Configuration Management](enhancements.md#5-enhanced-configuration-management)**: Flexible configuration system with YAML/JSON support and environment variables.

## Overview

This project implements a complete backtesting system for a trading strategy based on price extensions from the 9-period Exponential Moving Average (EMA) across multiple timeframes. The strategy looks for significant extensions away from the 9 EMA, followed by retracements and reclamations, with confluence across different timeframes.

## Key Features

- **Multi-Timeframe Analysis**: Combines signals from different timeframes (1m → 5m → 10m → 15m → 30m → 1h → 4h → daily → weekly → monthly)
- **Comprehensive Backtesting**: Full P&L calculation, drawdown analysis, and trade statistics
- **Advanced Visualization**: Charts showing entries, exits, equity curve, and key metrics
- **Performance Optimization**: Numba JIT compilation, vectorized operations, and multiprocessing support
- **Flexible Configuration**: YAML/JSON configs with environment variable overrides
- **Robust Testing**: Unit, integration, and performance tests with > 90% coverage
- **Continuous Integration**: GitHub Actions workflow with testing on multiple Python versions

## Getting Started

- [Installation Guide](installation.md): Step-by-step installation instructions
- [Quick Start Guide](quickstart.md): Run your first backtest
- [Configuration Guide](configuration.md): Customize the strategy to your needs

## User Guide

- [Running Backtests](backtests.md): Detailed guide to running backtests
- [Analyzing Results](results.md): Interpreting and visualizing backtest results
- [Strategy Details](strategy.md): Understanding the strategy logic

## Developer Guide

- [Architecture](architecture.md): System architecture and component interactions
- [Testing](testing.md): How to run and write tests
- [Contributing](contributing.md): Guidelines for contributing to the project

## Performance Benchmarks

| Dataset Size | Standard Implementation | Optimized Implementation | Speedup |
|--------------|-------------------------|--------------------------|---------|
| 1,000 bars   | 0.42s                   | 0.15s                    | 2.8x    |
| 10,000 bars  | 4.61s                   | 0.57s                    | 8.1x    |
| 50,000 bars  | 23.15s                  | 2.85s                    | 8.1x    |
| 100,000 bars | 48.72s                  | 5.93s                    | 8.2x    |

*Benchmarks run on an Intel i7-10700K, 32GB RAM, Python 3.10*

## Project Structure

```
mtfema_backtester/
├── data/               # Data loading and handling
├── indicators/         # Technical indicators
├── strategy/           # Strategy components
├── backtest/           # Backtesting engine
│   └── optimized_backtester.py  # Performance-optimized implementation
├── visualization/      # Visualization tools
├── utils/              # Utility functions
├── config_manager.py   # Enhanced configuration system
├── main.py             # CLI entry point
└── requirements.txt    # Dependencies

tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
└── performance/        # Performance tests

.github/
└── workflows/          # CI/CD configuration
    └── ci.yml          # GitHub Actions workflow
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

This project was created with the help of Claude AI. 