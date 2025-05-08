# MT 9 EMA Backtester Dashboard

A modern, responsive dashboard for visualizing and analyzing backtesting results from the MT 9 EMA trading strategy.

![Dashboard Preview](./public/dashboard-preview.png)

## Features

- **Modern UI**: Built with Next.js, Tailwind CSS, and Shadcn UI components
- **Interactive Visualizations**: Includes equity curves, drawdown analysis, parameter optimization charts
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Mode**: Supports theme switching with system preference detection
- **Real-time Data**: Connects to the Python API server for real-time backtest results and live trading data
- **Parameter Optimization**: Visualize how different parameter combinations affect strategy performance

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.8+ (for the API server)

### Installation

1. Install dashboard dependencies:

```bash
cd mtfema-dashboard
npm install
```

2. Install API server dependencies:

```bash
pip install fastapi uvicorn pandas
```

### Running the Dashboard

1. Start the development server:

```bash
cd mtfema-dashboard
npm run dev
```

2. Start the Python API server:

```bash
python api_server.py
```

3. Open your browser and navigate to `http://localhost:3000`

## Connecting to the API Server

The dashboard connects to the API server at `http://localhost:5000` by default. You can change this by setting the `NEXT_PUBLIC_API_URL` environment variable.

Example with a custom API URL:

```bash
NEXT_PUBLIC_API_URL=http://your-api-server.com/api npm run dev
```

## Dashboard Components

### Main Tabs

- **Overview**: High-level performance metrics, equity curve, and drawdown analysis
- **Trades**: Detailed list of all trades with entry/exit prices and results
- **Optimization**: Parameter optimization visualizations
- **Live Trading**: Real-time monitoring of live trading performance

### Visualization Components

- **EquityCurve**: Displays the cumulative performance over time
- **DrawdownAnalysis**: Shows drawdown periods and recovery
- **MonthlyPerformance**: Calendar view of monthly returns
- **ParameterHeatmap**: Heatmap showing performance across parameter combinations
- **ParameterImpact**: Line charts showing the impact of individual parameters
- **ParallelCoordinates**: Multi-parameter analysis chart
- **LiveTradingDashboard**: Real-time monitoring of live trading positions

## Customization

### Adding New Visualizations

1. Create a new component in `src/components/visualizations/`
2. Import and add your component to the relevant tab in `src/app/page.tsx`

### Styling

The dashboard uses Tailwind CSS for styling. You can customize the theme in `tailwind.config.js`.

## Deployment

### Building for Production

```bash
npm run build
```

The build output will be in the `.next` directory.

### Deploying to Vercel

The easiest way to deploy the dashboard is using Vercel:

```bash
npm i -g vercel
vercel
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
