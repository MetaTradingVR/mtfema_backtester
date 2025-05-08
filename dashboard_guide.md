# MT 9 EMA Backtester Dashboard Guide

This guide provides detailed instructions for setting up, using, and extending the MT 9 EMA Backtester Dashboard.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Using the Dashboard](#using-the-dashboard)
  - [Overview Tab](#overview-tab)
  - [Trades Tab](#trades-tab)
  - [Optimization Tab](#optimization-tab)
  - [Live Trading Tab](#live-trading-tab)
  - [Theme Switching](#theme-switching)
- [API Integration](#api-integration)
- [Extending the Dashboard](#extending-the-dashboard)
- [Troubleshooting](#troubleshooting)

## Overview

The MT 9 EMA Backtester Dashboard is a web-based interface that provides visualization and analysis tools for the MT 9 EMA trading strategy. It allows you to:

- View backtest results with comprehensive performance metrics
- Analyze trade history and performance patterns
- Explore parameter optimization results
- Monitor live trading performance
- Switch between light and dark themes

The dashboard is built with Next.js, TypeScript, and modern UI components (Tailwind CSS, shadcn/UI), connecting to a Python FastAPI backend that serves backtest results and live trading data.

![Dashboard Preview](docs/images/dashboard_preview.png)

## Installation

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.8+ with FastAPI and Uvicorn
- MT 9 EMA Backtester core implementation

### Dashboard Setup

1. Navigate to the dashboard directory:
   ```bash
   cd mtfema-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open http://localhost:3000 in your browser

### API Server Setup

1. Install required Python packages:
   ```bash
   pip install fastapi uvicorn pandas
   ```

2. Start the API server:
   ```bash
   python api_server.py
   ```

## Configuration

### Environment Variables

Create a `.env.local` file in the dashboard directory with the following variables:

```
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

Adjust the URL if your API server is running on a different host or port.

## Using the Dashboard

### Overview Tab

The Overview tab provides high-level performance metrics including:

- **Total return percentage**: Displayed prominently with color coding (green for positive, red for negative)
- **Win rate**: Percentage of profitable trades
- **Sharpe ratio**: Risk-adjusted return metric
- **Equity curve visualization**: Interactive chart showing account equity over time
- **Drawdown analysis**: Visual representation of drawdown periods
- **Monthly performance calendar**: Heat map showing returns by month

![Overview Tab](docs/images/overview_tab.png)

#### Equity Curve Component

The equity curve visualization shows the growth of your trading account over time, with:

- Interactive zooming and panning
- Tooltips with date and equity value
- Optional overlay of benchmark comparison
- Date range filtering

#### Drawdown Analysis Component

The drawdown analysis helps you understand the depth and duration of losing periods:

- Visual representation of drawdown periods
- Maximum drawdown highlighted
- Recovery periods marked
- Statistical summary of drawdowns

#### Monthly Performance Calendar

The monthly performance calendar provides a visual way to identify seasonal patterns:

- Color-coded monthly returns (green for positive, red for negative)
- Intensity of color represents magnitude of returns
- Yearly summary statistics
- Click to view detailed monthly breakdown

### Trades Tab

The Trades tab displays a detailed list of all trades from your backtest results, including:

- Entry and exit dates
- Trade direction (Long/Short)
- Entry and exit prices
- Profit/loss in both absolute and percentage terms
- Trade duration
- Sortable columns for data analysis
- Filtering options to focus on specific trade types

![Trades Tab](docs/images/trades_tab.png)

### Optimization Tab

The Optimization tab visualizes parameter combinations and their impact on performance:

- **Parameter heatmap**: Shows the relationship between two parameters (e.g., EMA period and extension threshold) and their impact on performance metrics
- **Parameter impact charts**: Visualize how individual parameters affect returns
- **Parallel coordinates**: Multi-parameter analysis for exploring relationships between parameters and metrics

![Optimization Tab](docs/images/optimization_tab.png)

#### Parameter Heatmap Component

The parameter heatmap allows you to visualize how combinations of two parameters affect performance:

- Customizable X and Y axis parameters
- Selectable performance metric (total return, win rate, Sharpe ratio, etc.)
- Color intensity indicating performance levels
- Value labels for precise reading
- Color scale representing metric range

#### Parameter Impact Component

The parameter impact analysis helps identify which parameters have the greatest influence on strategy performance:

- Bar charts showing performance across parameter values
- Multiple metrics support (return, win rate, Sharpe ratio)
- Statistical significance indicators
- Trend lines to identify optimal parameter ranges

#### Parallel Coordinates Component

The parallel coordinates visualization allows you to explore relationships between multiple parameters simultaneously:

- Multiple parameter axes
- Color-coded by performance metric
- Interactive filtering by dragging on axes
- Highlighting of top-performing configurations
- Export of optimal parameter sets

### Live Trading Tab

The Live Trading tab provides real-time monitoring of trading activity:

- Current positions and open trades
- Account equity and daily P&L
- Recent signals and executions
- Performance metrics
- Trade controls for manual intervention

![Live Trading Tab](docs/images/live_trading_tab.png)

### Theme Switching

The dashboard supports light, dark, and system themes:

- Click the theme switcher in the top navigation bar
- Choose between Light, Dark, or System
- System setting follows your operating system preference
- Theme preference is saved between sessions

## API Integration

The dashboard communicates with the Python backend through these API endpoints:

- `/api/backtest/results` - Get all backtest results
- `/api/backtest/{id}` - Get a specific backtest result
- `/api/backtest/run` - Run a new backtest
- `/api/optimization/results` - Get optimization results
- `/api/live/status` - Get live trading status

All API responses are typed using TypeScript interfaces to ensure data consistency.

## Extending the Dashboard

### Adding New Visualizations

1. Create a new component in `src/components/visualizations/`:
   ```tsx
   // src/components/visualizations/my-visualization.tsx
   "use client";
   
   import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
   
   interface MyVisualizationProps {
     data: any[];
     title?: string;
   }
   
   export function MyVisualization({ data, title = "My Visualization" }: MyVisualizationProps) {
     return (
       <Card>
         <CardHeader>
           <CardTitle>{title}</CardTitle>
         </CardHeader>
         <CardContent>
           {/* Visualization content */}
         </CardContent>
       </Card>
     );
   }
   ```

2. Import and use your component in the appropriate tab in `src/app/page.tsx`:
   ```tsx
   import { MyVisualization } from "@/components/visualizations/my-visualization";
   
   // In your page component:
   <MyVisualization data={yourData} title="Custom Visualization" />
   ```

### Adding New API Endpoints

1. Update the API types in `src/lib/api.ts`:
   ```tsx
   export interface NewDataType {
     // Define your data structure
   }
   
   export async function fetchNewData(): Promise<NewDataType[]> {
     try {
       const response = await fetch(`${API_BASE_URL}/new-endpoint`);
       if (!response.ok) {
         throw new Error(`Error: ${response.status}`);
       }
       return await response.json();
     } catch (error) {
       console.error('Error fetching new data:', error);
       return [];
     }
   }
   ```

2. Add the corresponding endpoint to `api_server.py`:
   ```python
   @app.get("/api/new-endpoint")
   async def get_new_data():
       # Implementation
       return {"data": your_data}
   ```

### Customizing Themes

To customize the dashboard's theme:

1. Modify the CSS variables in `src/app/globals.css`:
   ```css
   :root {
     --primary: oklch(0.208 0.042 265.755);
     --primary-foreground: oklch(0.984 0.003 247.858);
     /* Add other variables */
   }

   .dark {
     --primary: oklch(0.929 0.013 255.508);
     --primary-foreground: oklch(0.208 0.042 265.755);
     /* Add other variables */
   }
   ```

2. The theme provider in `src/components/ui/theme-provider.tsx` handles theme application.

## Troubleshooting

### Dashboard Connection Issues

If the dashboard cannot connect to the API server:

1. Check that the API server is running
2. Verify the API URL in `.env.local` is correct
3. Check for CORS issues in browser console
4. Ensure network connectivity between the dashboard and API server

### API Server Issues

If the API server fails to start or respond:

1. Check that all required Python packages are installed
2. Verify port 5000 is not in use by another application
3. Check the API server logs for error messages
4. Ensure the MT 9 EMA Backtester core modules are properly installed

### Visualization Rendering Issues

If charts or visualizations don't render correctly:

1. Check browser console for JavaScript errors
2. Ensure data is in the expected format
3. Try clearing browser cache
4. Verify browser compatibility (the dashboard works best with Chrome, Firefox, Edge, or Safari)

### Theme Switching Issues

If theme switching doesn't work:

1. Make sure localStorage is enabled in your browser
2. Check if the ThemeProvider is properly mounted in the layout
3. Verify CSS variables are correctly defined
4. Try a different browser to rule out browser-specific issues 