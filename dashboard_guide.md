# MT 9 EMA Backtester Dashboard Guide

This guide provides detailed instructions for setting up, using, and extending the MT 9 EMA Backtester Dashboard.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Using the Dashboard](#using-the-dashboard)
- [API Integration](#api-integration)
- [Extending the Dashboard](#extending-the-dashboard)
- [Troubleshooting](#troubleshooting)

## Overview

The MT 9 EMA Backtester Dashboard is a web-based interface that provides visualization and analysis tools for the MT 9 EMA trading strategy. It allows you to:

- View backtest results with comprehensive performance metrics
- Analyze trade history and performance patterns
- Explore parameter optimization results
- Monitor live trading performance

The dashboard is built with Next.js, TypeScript, and modern UI components, connecting to a Python FastAPI backend that serves backtest results and live trading data.

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
- Total return percentage
- Win rate
- Sharpe ratio
- Equity curve visualization
- Drawdown analysis
- Monthly performance calendar

### Trades Tab

The Trades tab displays a detailed list of all trades from your backtest results, including:
- Entry and exit dates
- Trade direction (Long/Short)
- Entry and exit prices
- Profit/loss in both absolute and percentage terms
- Trade duration

### Optimization Tab

The Optimization tab visualizes parameter combinations and their impact on performance:
- Parameter heatmap showing the relationship between two parameters
- Parameter impact charts showing how individual parameters affect returns
- Parallel coordinates for multi-parameter analysis

### Live Trading Tab

The Live Trading tab provides real-time monitoring of trading activity:
- Current positions and open trades
- Account equity and daily P&L
- Recent signals and executions
- Performance metrics

## API Integration

The dashboard communicates with the Python backend through these API endpoints:

- `/api/backtest/results` - Get all backtest results
- `/api/backtest/{id}` - Get a specific backtest result
- `/api/backtest/run` - Run a new backtest
- `/api/optimization/results` - Get optimization results
- `/api/live/status` - Get live trading status

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