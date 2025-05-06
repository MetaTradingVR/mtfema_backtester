# Multi-Timeframe 9 EMA Extension Strategy Backtester
# MT 9 EMA Backtester

A professional backtesting platform for the Multi-Timeframe 9 EMA Extension Strategy, featuring comprehensive analysis tools, community features, and advanced trading analytics.

## Features

### Core Backtesting
- Test 9 EMA strategy across multiple timeframes simultaneously
- Detailed performance metrics and visualizations
- Customizable parameters and settings
- Support for various financial instruments and markets

### Community Integration
- Share trading signals with other users
- Subscribe to signals from successful traders
- Reputation system and leaderboards
- Knowledge sharing and collaboration

### Mobile Support
- Responsive design that works on any device
- Optimized charts and tables for mobile viewing
- Touch-friendly interfaces
- Offline capabilities

## Installation

```bash
# Clone the repository
git clone https://github.com/MetaTradingVR/mtfema_backtester.git
cd mtfema_backtester

# Install dependencies
python talib_installer.py  # Installs TA-Lib with appropriate wheel for your system
pip install -r requirements.txt
```

## Quick Start

```bash
# Run a basic backtest
python run_backtest.bat  # Windows
./run_backtest.sh        # Unix/Mac

# With custom parameters
python main.py --symbol ES --start 2023-01-01 --end 2023-12-31 --capital 100000 --risk 0.01
```

## Project Structure

```
mtfema_backtester/
├── backtesting/         # Core backtesting engine
├── community/           # Community features
│   ├── forums/          # Forum functionality
│   ├── reputation/      # Reputation system
│   ├── signals/         # Signal subscription system
│   └── sharing/         # Trading setup sharing
├── data/                # Data handling and processing
├── indicators/          # Technical indicators and analysis
├── models/              # Position and trade management
├── utils/               # Utility functions
├── visualization/       # Charting and data visualization
├── docs/                # Documentation
├── tests/               # Test suite
└── examples/            # Usage examples
```

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Strategy Overview](docs/strategy_overview.md)
- [Community Features](docs/COMMUNITY_FEATURES.md)
- [Reputation System](docs/reputation_system.md)
- [Feature Flags](docs/feature_flags.md)
- [API Rate Limiting](docs/api_rate_limiting.md)
- [Enhancement Summary](docs/enhancement_summary.md)
- [Mobile Accessibility](docs/mobile_accessibility.md)
- [Security Considerations](docs/security_considerations.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Special thanks to the trading community for their feedback and contributions
- Inspired by professional trading methodologies and market microstructure analysis

## Overview

The MT 9 EMA Backtester is a sophisticated Python-based platform designed to backtest and optimize the Multi-Timeframe 9 EMA Extension Strategy. This strategy leverages price extensions from the 9 EMA across multiple timeframes to identify high-probability trading opportunities.

## Highlights

- **Multi-Timeframe Analysis**: Combines signals from different timeframes (1m → 5m → 10m → 15m → 30m → 1h → 4h → daily → weekly → monthly)
- **Enhanced Performance**: Numba JIT compilation, vectorized operations, and multiprocessing support
- **Flexible Configuration**: YAML/JSON configs with environment variable overrides
- **Comprehensive Testing**: Unit, integration, and performance tests with > 90% coverage
- **Continuous Integration**: GitHub Actions workflow with testing on multiple Python versions
- **Rich Visualization**: Detailed charts and performance dashboards

## Key Features

- **Strategy Components**:
  - Extension detection from 9 EMA across timeframes
  - EMA reclamation for entry signals
  - Pullback entry with Fibonacci retracements
  - Progressive targeting through higher timeframes
  - Conflict resolution between timeframes
  - Sophisticated risk management and position sizing

- **Performance Optimizations**:
  - Numba JIT compilation for critical calculations
  - Vectorized operations instead of loops
  - Multiprocessing for parallel parameter optimization
  - Memory-efficient data structures

- **Configuration System**:
  - Support for YAML and JSON configuration files
  - Environment variable overrides (e.g., `MTFEMA_STRATEGY__EMA_PERIOD=21`)
  - Type conversion and validation
  - Hierarchical configuration with dot notation access
  - Global configuration instance with caching

- **Testing Framework**:
  - Pytest-based test suite with fixtures
  - Unit tests for individual components
  - Integration tests for component interactions
  - Performance benchmarking and scaling tests
  - Coverage reporting

- **Continuous Integration**:
  - GitHub Actions workflow for automated testing
  - Multi-Python version testing (3.9, 3.10, 3.11, 3.13)
  - Code quality checks (flake8, black, mypy)
  - Documentation builds and deployment

- **Feature Flag System**:
  - Gradual rollout of new features
  - User targeting for beta features
  - Environment-based feature control
  - Feature dependency management
  - Runtime feature toggling

- **API Rate Limiting**:
  - Token bucket algorithm implementation
  - Broker-specific rate limits
  - Automatic retries with exponential backoff
  - Decorator-based application
  - Thread-safe implementation

- **Community Features**:
  - Trading setup sharing
  - Signal creation and subscription
  - Forum system with categories
  - User profiles and reputation
  - Performance leaderboards

- **Global Accessibility**:
  - Multi-language support
  - Right-to-left text support
  - Responsive mobile design
  - Progressive web app capabilities
  - Offline functionality

## Project Status

The project has successfully implemented the following enhancements:

1. ✅ **Enhanced Documentation**: Comprehensive documentation with architecture overview, installation guide, and usage examples.
2. ✅ **Testing Framework**: Complete pytest setup with unit, integration, and performance tests.
3. ✅ **Performance Optimization**: Numba JIT-accelerated backtester with vectorized operations.
4. ✅ **Continuous Integration**: GitHub Actions workflow for automated testing and code quality checks.
5. ✅ **Enhanced Configuration Management**: Flexible configuration system with YAML/JSON support and environment variables.
6. ✅ **Feature Flag System**: Gradual rollout capability for new features with user targeting.
7. ✅ **API Rate Limiting**: Robust rate limiting for reliable broker API integration.
8. ✅ **Community Features**: System for sharing setups, signals, and participating in forums.
9. ✅ **Global Accessibility**: Multi-language support and mobile-optimized design.
10. ✅ **Community Prioritization**: Structured approach to feature prioritization.

## Acknowledgements

This project was created with the help of Claude AI. 