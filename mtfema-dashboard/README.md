# MT 9 EMA Backtester Dashboard

A modern, interactive web interface for the MT 9 EMA Backtester, built with Next.js, TypeScript, Tailwind CSS, and Plotly.js.

## Features

- **Comprehensive Dashboard**: Monitor and analyze backtesting results and live trading performance
- **Interactive Visualizations**: Explore parameter optimization results and trade analytics
- **Parameter Optimization Tools**: Visualize how different parameter combinations affect strategy performance
- **Live Trading Interface**: Monitor real-time trading activity and performance metrics

## Visualization Components

### Parameter Optimization

- **Parameter Heatmap**: Visualize how different combinations of parameter values affect trading performance metrics
- **Parameter Impact Analysis**: Understand how individual parameter values impact overall strategy performance
- **Parallel Coordinates**: Explore relationships between multiple parameters simultaneously

### Trading Performance

- **Live Trading Dashboard**: Monitor real-time trading activity with price charts and performance metrics
- **Trade Analysis**: Review completed trades with entry/exit points and performance statistics
- **Equity Curve**: Track account balance changes over time with drawdown visualization

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mtfema-backtester.git
   cd mtfema-backtester/mtfema-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Integration with MT 9 EMA Backtester

The dashboard integrates with the MT 9 EMA Backtester Python backend through:

1. **File-based Integration**: Reading JSON output from backtesting results
2. **API Integration**: Optional REST API for real-time updates (when using the live trading mode)

### Data Integration

1. Run your backtest using the Python backtester:
   ```bash
   python run_backtest.py --output results/backtest_results.json
   ```

2. The dashboard will automatically load the most recent results file in the results directory

### Live Trading Mode

To use live trading mode:

1. Start the MT 9 EMA Backtester in live trading mode:
   ```bash
   python run_live_trade.py --web-dashboard
   ```

2. Open the dashboard and navigate to the "Live Trading" tab

## Development

### Project Structure

```
mtfema-dashboard/
├── public/                  # Static assets
├── src/
│   ├── app/                 # Next.js app directory
│   │   ├── page.tsx         # Main dashboard page
│   │   └── layout.tsx       # Root layout component
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   └── visualizations/  # Trading visualization components
│   └── lib/                 # Utility functions and hooks
└── package.json             # Project dependencies
```

### Adding New Visualizations

To add a new visualization component:

1. Create a new file in `src/components/visualizations/`
2. Import the component in `src/app/page.tsx`
3. Add the component to the appropriate tab in the dashboard

## License

[MIT License](LICENSE)
