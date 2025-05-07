# Multi-Timeframe 9 EMA Extension Strategy Backtester
# MT 9 EMA Backtester

📋 **Project Status & Roadmap:**
For the latest, timestamped project status, implementation progress, and roadmap, see [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md). This is the canonical source for all planning and progress updates.

## 📊 Advanced Visualization Features (Added 2025-05-06)

The backtester includes several advanced visualization tools for comprehensive strategy analysis:

### Extension Map
Visualizes extensions across all timeframes with a heatmap interface, making it easy to identify multi-timeframe confluence. Color coding shows extension direction (positive/negative) and intensity.

### Signal Timeline
Displays trading signals chronologically across different timeframes, with markers color-coded by direction (long/short) and sized by confidence level. Offers detailed hover information for in-depth signal analysis.

### Progression Tracker
Shows how trades progress through the timeframe hierarchy using an interactive Sankey diagram. Visualizes the flow from entry timeframe to subsequent target timeframes, with link thickness proportional to frequency.

### Conflict Map
Highlights detected timeframe conflicts with visual indicators for different conflict types (Consolidation, Direct Correction, Trap Setup). Makes it easy to understand where and why risk adjustments were applied.

All visualizations are built with Plotly for modern, interactive display and can be saved as standalone HTML files for sharing or further analysis.

## 🖥️ Interactive Web Interface (Added 2025-05-06)

The backtester now features a modern, responsive web interface built with Streamlit:

### Features

- **Interactive Dashboard**: Configure and run backtests from a user-friendly UI with real-time parameter updates
- **Multi-Tab Interface**: Separate tabs for different visualizations and analysis views
- **Symbol Search**: Find and select trading symbols with intelligent suggestions
- **Parameter Adjustment**: Fine-tune strategy parameters with instant feedback
- **Performance Metrics**: View key performance indicators in a clean, card-based layout
- **Trade Analysis**: Examine individual trades with detailed statistics and visualizations

### Running the Web Interface

```bash
# Install Streamlit if not already installed
pip install streamlit

# Launch the web interface
streamlit run mtfema_backtester/run_web_app.py

# The app will open in your default web browser at http://localhost:8501
```

### Customization Options

The web interface provides comprehensive parameter controls:
- EMA period and threshold adjustments
- Timeframe selection with hierarchical organization
- Risk management settings with ATR-based stop loss options
- Symbol search with popular suggestions
- Date range selection for backtesting periods

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

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/username/mtfema_backtester.git
cd mtfema_backtester

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install TA-Lib (optional but recommended)
# See https://github.com/mrjbq7/ta-lib for platform-specific instructions
```

### Docker Installation

```bash
# Build and run the Docker container
docker-compose up -d

# Run commands inside the container
docker exec mtfema python -m mtfema_backtester.main --help
```

## Using Docker

For a hassle-free setup that avoids dependency issues, you can use Docker to run the backtester:

```bash
# Windows
run-docker-backtest.bat --symbol NQ --timeframes 1d,1h,15m --start-date 2023-01-01 --end-date 2023-06-01

# Linux/Mac
./run-docker-backtest.sh --symbol NQ --timeframes 1d,1h,15m --start-date 2023-01-01 --end-date 2023-06-01
```

The Docker setup provides:
- An isolated environment with all dependencies pre-installed
- Consistent results across different systems
- Volume mounts for data, results, and logs
- Easy customization through command line parameters

You can also customize the Docker settings in `docker-compose.yml` for advanced configurations.

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

This backtester is designed to test and optimize the MT 9 EMA Extension Strategy, a sophisticated trading system that capitalizes on price extensions from the 9 EMA across a hierarchical timeframe structure. The strategy systematically identifies, validates, and trades extensions through a progressive targeting framework that moves methodically through the timeframe ladder.

## Features

- **Multi-Timeframe Analysis**: Support for any combination of timeframes (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- **EMA Extension Detection**: Identifies when price extends significantly from the 9 EMA
- **Bollinger Band Analysis**: Volatility measurement and breakout detection
- **Reclamation Detection**: Identifies when price reclaims the EMA and tracks pullbacks
- **Performance Metrics**: Comprehensive trade statistics and equity curve analysis
- **Visualization Tools**: Interactive HTML plots for visual analysis
- **Configurable Parameters**: Extensively customizable strategy parameters
- **Flexible Data Sources**: Supports Yahoo Finance with easy extension to other data providers

## Development Status

- [x] Basic indicator calculation and visualization
- [x] EMA extension detection
- [x] Reclamation detection
- [x] Configurable parameters system
- [x] Performance metrics framework
- [ ] Complete signal generation engine
- [ ] Progressive targeting implementation
- [ ] Optimization framework

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

## Advanced Metrics

The backtester calculates a comprehensive set of performance metrics:

### Standard Metrics
- **Total Return**: Overall percentage return
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profits divided by gross losses
- **Max Drawdown**: Maximum peak-to-trough decline

### Advanced Risk-Adjusted Metrics
- **Sharpe Ratio**: Return relative to risk (volatility)
- **Sortino Ratio**: Downside risk-adjusted return
- **Calmar Ratio**: Return relative to maximum drawdown
- **Omega Ratio**: Probability-weighted ratio of gains to losses
- **Maximum Consecutive Winners/Losers**: Streak analysis

### Trade Quality Metrics
- **Average Winner/Loser Size**: Analysis of trade size distribution
- **Gain-to-Pain Ratio**: Sum of returns divided by absolute sum of losses
- **Average Holding Period**: Time in market analysis
- **Expectancy**: Average profit/loss per trade

## Project Structure

```
mtfema_backtester/
├── backtest/           # Backtesting engine
├── data/               # Data handling modules
├── indicators/         # Technical indicators
├── strategy/           # Strategy components
├── utils/              # Utility functions
├── visualization/      # Plotting and visualization
├── main.py             # Main entry point
└── config.py           # Configuration parameters
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 