# Multi-Timeframe 9 EMA Extension Strategy Backtester
# MT 9 EMA Backtester

📋 **Project Status & Roadmap:**
For the latest project status, implementation progress, and roadmap, see [project_status.md](project_status.md).

## 🚀 Key Components

### 🔄 Trade Execution System
- **Robust Signal Processing**: Convert strategy signals into executable trades
- **Position Management**: Track and manage open positions 
- **Performance Monitoring**: Real-time P&L calculation and metrics tracking
- **Risk Management**: Implement position sizing and trade limits
- **Flexible Integration**: Works with multiple data sources and signal formats

### 📊 Trading Dashboard

A modern, interactive web dashboard built with Next.js, Tailwind CSS, and Plotly.js for visualizing backtesting results and monitoring live trading:

![MT 9 EMA Dashboard](docs/images/dashboard_preview.png)

#### Dashboard Features

- **Comprehensive Visualization**: Interactive charts and graphs for backtest analysis
- **Parameter Optimization Tools**: Visualize how different parameter combinations affect trading performance
- **Live Trading Interface**: Monitor real-time trading activity and performance
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Theme Support**: Customizable UI theme based on user preference

#### Running the Dashboard

```bash
# Navigate to the dashboard directory
cd mtfema-dashboard

# Install dependencies
npm install

# Start the development server
npm run dev

# Open http://localhost:3000 in your browser
```

#### Dashboard Components

- **Parameter Heatmap**: Visualize how different parameter combinations affect performance metrics
- **Parameter Impact Analysis**: Understand which parameters have the greatest influence
- **Parallel Coordinates**: Explore relationships between multiple parameters simultaneously
- **Live Trading Dashboard**: Monitor real-time trading with price charts and performance metrics
- **Trade List**: Detailed view of all executed trades with performance metrics
- **Monthly Performance Calendar**: Visual representation of returns by month
- **Equity Curve**: Track account equity over time with drawdown analysis

For more details, see the [dashboard documentation](dashboard_guide.md).

### 📁 Data Import System

Flexible data handling for multiple sources and formats:

- **Configurable CSV Import**: Map any CSV format to the required structure
- **Date Format Handling**: Support for various date and time formats
- **Import Templates**: Save and reuse import configurations
- **Error Handling**: Robust validation and error reporting
- **Pre-processing**: Automatic data cleaning and preparation

### 🔍 Parameter Optimization

Comprehensive framework for finding optimal strategy parameters:

- **Grid Search**: Systematically test parameter combinations
- **Randomized Search**: Efficiently explore large parameter spaces
- **Parallel Processing**: Utilize multiple cores for faster optimization
- **Result Tracking**: Save and compare optimization runs
- **Parameter Importance**: Identify which parameters have the greatest impact
- **Visualization Tools**: Intuitive visual representation of optimization results

### 📊 Advanced Visualization Features

The backtester includes several advanced visualization tools for comprehensive strategy analysis:

#### Extension Map
Visualizes extensions across all timeframes with a heatmap interface, making it easy to identify multi-timeframe confluence. Color coding shows extension direction (positive/negative) and intensity.

#### Signal Timeline
Displays trading signals chronologically across different timeframes, with markers color-coded by direction (long/short) and sized by confidence level. Offers detailed hover information for in-depth signal analysis.

#### Progression Tracker
Shows how trades progress through the timeframe hierarchy using an interactive Sankey diagram. Visualizes the flow from entry timeframe to subsequent target timeframes, with link thickness proportional to frequency.

#### Conflict Map
Highlights detected timeframe conflicts with visual indicators for different conflict types (Consolidation, Direct Correction, Trap Setup). Makes it easy to understand where and why risk adjustments were applied.

All visualizations are built with Plotly for modern, interactive display and can be saved as standalone HTML files for sharing or further analysis.

#### Parameter Optimization Visualization

The backtester includes powerful parameter optimization visualizations:

- **Parameter Heatmaps**: Visualize how different parameter combinations affect key metrics like total return and Sharpe ratio with color-coded intensity maps
- **Parameter Impact Analysis**: Discover which parameters have the greatest influence on strategy performance with ranked bar charts
- **Parallel Coordinates**: Analyze relationships between multiple parameters and metrics simultaneously with multi-dimensional visualization
- **Comprehensive Dashboard**: Export all optimization visualizations as a single HTML dashboard for deeper analysis

#### Live Trading Dashboard

The platform includes a real-time dashboard for monitoring live trading performance:

- **Real-time Equity Curve**: Monitor your account balance and drawdowns as they occur
- **Active Positions Monitor**: Track open positions with live unrealized P&L updates
- **Signal Timeline**: View recent trading signals with direction and timeframe indicators
- **Performance Metrics**: Track key statistics like win rate, profit factor, and average trade P&L
- **Trade Distribution**: Analyze the distribution of winning and losing trades
- **Control Panel**: Start and stop trading directly from the dashboard interface

### 🔄 Live Trading Features

The backtester has been extended with full live trading capabilities:

#### Broker Integration

- **Tradovate**: Full integration with Tradovate API for futures trading
- **Rithmic**: Integration with Rithmic API for professional futures trading
- **Broker-Agnostic Interface**: Modular design makes adding new brokers straightforward

#### Live Trading Features

- **Real-time Signal Generation**: Apply the same strategy logic from backtesting to live market data
- **Order Management**: Place, modify, and cancel orders with risk constraints
- **Position Tracking**: Monitor active positions with unrealized P&L calculations
- **Account Management**: Track balance, margin, and other account metrics
- **WebSocket Support**: Real-time data streaming for minimal latency

#### Running Live Trading

```python
# Create a live trader instance
from mtfema_backtester.trading.live_trader import LiveTrader
from mtfema_backtester.trading.broker_factory import BrokerFactory
from mtfema_backtester.visualization.live_trading_dashboard import create_live_trading_dashboard

# Get broker instance through factory
broker = BrokerFactory.get_broker('tradovate', api_key='your_key', api_secret='your_secret')

# Create live trader
live_trader = LiveTrader(broker=broker, symbols=['ES'], timeframes=['5m', '15m', '1h', '4h'])

# Start dashboard
dashboard = create_live_trading_dashboard(live_trader, port=8051)

# Start trading
live_trader.start()
```

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
python run_backtest.py --symbol ES --start 2023-01-01 --end 2023-12-31 --capital 100000 --risk 0.01
```

## Project Structure

```
mtfema_backtester/
├── backtesting/         # Core backtesting engine
├── trading/             # Live trading components
│   ├── broker/          # Broker interfaces
│   ├── execution/       # Order execution
│   ├── risk/            # Risk management
│   └── signals/         # Signal generation
├── data/                # Data handling and processing
│   └── importer.py      # Flexible data import system
├── indicators/          # Technical indicators and analysis
├── models/              # Position and trade management
├── optimization/        # Parameter optimization framework
├── utils/               # Utility functions
├── visualization/       # Charting and data visualization
│   ├── dashboards/      # Python visualization dashboards
│   └── optimization/    # Optimization visualization tools
├── mtfema-dashboard/    # Next.js web dashboard
├── docs/                # Documentation
├── tests/               # Test suite
└── examples/            # Usage examples
```

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Strategy Overview](docs/strategy_overview.md)
- [Dashboard Guide](docs/dashboard_guide.md)
- [Live Trading Guide](docs/live_trading.md)
- [Parameter Optimization](docs/parameter_optimization.md)
- [Data Import Guide](docs/data_import.md)
- [API Integration](docs/api_integration.md)
- [Project Status](project_status.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Special thanks to the trading community for their feedback and contributions
- Inspired by professional trading methodologies and market microstructure analysis

## Overview

The Multi-Timeframe 9 EMA Extension strategy is a versatile trading approach that leverages price extensions from the 9-period Exponential Moving Average (EMA) across multiple timeframes to identify high-probability trading opportunities. This backtester provides a complete framework for testing and optimizing this strategy on historical data.

### Key Features

- **Multi-Timeframe Analysis**: Simultaneously analyze price action across multiple timeframes
- **Advanced Extension Detection**: Identify significant price extensions from the 9 EMA
- **Adaptive Parameters**: Dynamically adjust thresholds based on market volatility
- **Comprehensive Performance Metrics**: Track and analyze detailed strategy performance
- **Visualization Tools**: Generate charts and diagrams of strategy behavior
- **Trade Management**: Simulate realistic trade entries, exits, and position sizing
- **Customization Options**: Easily modify strategy parameters and rules

## Installation

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
- **Live Trading**: Support for real-time trading with broker integrations (Tradovate and Rithmic)

## Development Status

- [x] Basic indicator calculation and visualization
- [x] EMA extension detection
- [x] Reclamation detection
- [x] Configurable parameters system
- [x] Performance metrics framework
- [x] Complete signal generation engine
- [x] Progressive targeting implementation
- [x] Optimization framework
- [x] Live trading with broker integrations

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
11. ✅ **Live Trading Support**: Integration with brokers (Tradovate and Rithmic) for real-time trading.

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

## Live Trading

The MT 9 EMA Backtester now supports live trading through broker integrations:

### Supported Brokers
- **Tradovate**: Popular among professional futures traders and prop firms
- **Rithmic**: Advanced order routing system widely used in futures trading

### Live Trading Features
- Real-time market data processing across multiple timeframes
- Live signal generation using the same strategy logic as backtesting
- Automated order execution with customizable risk parameters
- Position management with dynamic stops and targets
- WebSocket connections for real-time market data and order updates

### Getting Started with Live Trading

```python
from mtfema_backtester.trading.live_trader import LiveTrader
from mtfema_backtester.trading.broker_factory import BrokerFactory

# Create a broker instance
broker = BrokerFactory.create(
    broker_name="tradovate",  # or "rithmic"
    credentials={
        "username": "your_username",
        "password": "your_password",
        "client_id": "your_client_id",
        "client_secret": "your_client_secret"
    },
    is_paper=True  # Use paper trading
)

# Initialize live trader
live_trader = LiveTrader(
    broker=broker,
    strategy_params={
        "ema_length": 9,
        "extension_threshold": 0.5,
        "reclamation_threshold": 0.2
    },
    risk_settings={
        "account_risk_pct": 1.0,
        "max_positions": 3
    },
    symbols=["ES", "NQ"],
    timeframes=["5m", "15m", "1h"]
)

# Start live trading
live_trader.start()
```

## Project Structure

```
mtfema_backtester/
├── backtest/           # Backtesting engine
├── data/               # Data handling modules
├── indicators/         # Technical indicators
├── strategy/           # Strategy components
├── trading/            # Live trading components
│   ├── broker_interface.py  # Broker interface definition
│   ├── tradovate_broker.py  # Tradovate implementation
│   ├── rithmic_broker.py    # Rithmic implementation
│   ├── live_trader.py       # Live trading orchestration
│   └── strategy_adapter.py  # Adapt strategy to broker
├── utils/              # Utility functions
├── visualization/      # Plotting and visualization
├── main.py             # Main entry point
└── config.py           # Configuration parameters
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 