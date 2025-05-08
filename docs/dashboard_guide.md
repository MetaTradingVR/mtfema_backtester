# MT 9 EMA Backtester Dashboard Guide

This guide provides comprehensive instructions for setting up, using, and extending the MT 9 EMA Backtester Dashboard.

## Overview

The MT 9 EMA Backtester Dashboard is a modern web application built with:

- **Next.js**: React framework for server-rendered applications
- **TypeScript**: For type safety and better developer experience
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/UI**: Reusable component system
- **Plotly.js**: Interactive visualization library

The dashboard provides a comprehensive interface for:
1. Configuring and running backtests
2. Visualizing backtest results and optimizations
3. Monitoring live trading performance
4. Analyzing trade history and performance metrics

## Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Python 3.10+ (for the backtester backend)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/mtfema-backtester.git
   cd mtfema-backtester
   ```

2. **Install dashboard dependencies**:
   ```bash
   cd mtfema-dashboard
   npm install
   # or
   yarn install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open the dashboard**:
   Open [http://localhost:3000](http://localhost:3000) in your browser

## Using the Dashboard

### Dashboard Layout

The dashboard is organized into four main sections:

1. **Overview**: Displays key performance metrics and summary charts
2. **Trades**: Shows detailed trade list and analysis
3. **Optimization**: Provides parameter optimization visualizations
4. **Live Trading**: Monitors real-time trading performance

### Running a Backtest

1. Configure your backtest parameters in the sidebar:
   - Select a symbol (e.g., NQ, ES)
   - Choose timeframes to analyze
   - Set date range for backtesting
   - Configure strategy parameters

2. Click the "Run Backtest" button to start

3. When the backtest is complete, the dashboard will automatically navigate to the Optimization tab to show results

### Analyzing Optimization Results

The Optimization tab provides three key visualizations:

1. **Parameter Heatmap**: Shows how combinations of two parameters affect performance metrics
   - X and Y axes represent different parameter values
   - Color intensity represents the magnitude of the selected metric
   - Hover for exact metric values at each parameter combination

2. **Parameter Impact Analysis**: Shows how individual parameters affect performance
   - Each chart shows the average metric value for each parameter value
   - Helps identify which parameter values yield the best results

3. **Parallel Coordinates**: Visualizes relationships between multiple parameters
   - Each vertical axis represents a parameter or performance metric
   - Each line represents a backtest configuration
   - Lines are colored based on performance
   - Helps identify optimal parameter combinations

### Monitoring Live Trading

The Live Trading tab provides real-time monitoring of:

- Price charts with 9 EMA and entry/exit signals
- Current positions and unrealized P&L
- Performance metrics (win rate, profit factor, etc.)
- Recent trade history
- Account balance and equity curve

## Extending the Dashboard

### Project Structure

```
mtfema-dashboard/
├── src/
│   ├── app/                 # Next.js app directory
│   │   ├── page.tsx         # Main dashboard page
│   │   └── layout.tsx       # Root layout
│   ├── components/
│   │   ├── ui/              # UI components from shadcn/ui
│   │   └── visualizations/  # Visualization components
│   ├── lib/                 # Utility functions
│   └── styles/              # Global styles
├── public/                  # Static assets
└── package.json             # Dependencies
```

### Adding a New Visualization Component

1. **Create a new component file**:
   Create a new file in `src/components/visualizations/`, for example `trade-distribution.tsx`:

   ```tsx
   import React, { useEffect, useState } from 'react';
   import dynamic from 'next/dynamic';
   import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

   // Dynamically import Plot from react-plotly.js
   const Plot = dynamic(() => import('react-plotly.js'), {
     ssr: false, // Disable server-side rendering
   });

   interface TradeDistributionProps {
     data: any;
     title?: string;
     className?: string;
   }

   export function TradeDistribution({ data, title = "Trade Distribution", className }: TradeDistributionProps) {
     const [plotData, setPlotData] = useState<any[]>([]);
     const [plotLayout, setPlotLayout] = useState<any>({});

     useEffect(() => {
       // Process data and create visualization
       // ...

       // Set plotData and plotLayout
     }, [data, title]);

     return (
       <Card className={`w-full h-full ${className || ''}`}>
         <CardHeader>
           <CardTitle>{title}</CardTitle>
           <CardDescription>Distribution of trade results</CardDescription>
         </CardHeader>
         <CardContent>
           {plotData.length > 0 ? (
             <Plot
               data={plotData}
               layout={plotLayout}
               config={{ responsive: true }}
               className="w-full h-[400px]"
             />
           ) : (
             <div className="w-full h-[400px] flex items-center justify-center">Processing data...</div>
           )}
         </CardContent>
       </Card>
     );
   }
   ```

2. **Import and use the component** in `src/app/page.tsx`:

   ```tsx
   import { TradeDistribution } from "@/components/visualizations/trade-distribution";
   
   // Add to the appropriate tab
   <TabsContent value="trades" className="space-y-4">
     {/* Existing content */}
     <TradeDistribution data={tradeData} />
   </TabsContent>
   ```

### Adding Backend Integration

To integrate with the Python backtester backend:

1. **Create an API route** in `src/app/api/backtest/route.ts`:

   ```typescript
   import { NextResponse } from 'next/server';
   import fs from 'fs';
   import path from 'path';

   export async function GET(request: Request) {
     try {
       // Read the most recent backtest results file
       const resultsDir = path.join(process.cwd(), '../../results');
       const files = fs.readdirSync(resultsDir)
         .filter(file => file.endsWith('_results.json'))
         .sort((a, b) => {
           return fs.statSync(path.join(resultsDir, b)).mtime.getTime() - 
                  fs.statSync(path.join(resultsDir, a)).mtime.getTime();
         });
       
       if (files.length === 0) {
         return NextResponse.json({ error: 'No backtest results found' }, { status: 404 });
       }
       
       const latestFile = files[0];
       const filePath = path.join(resultsDir, latestFile);
       const fileContent = fs.readFileSync(filePath, 'utf8');
       const data = JSON.parse(fileContent);
       
       return NextResponse.json(data);
     } catch (error) {
       console.error('Error loading backtest results:', error);
       return NextResponse.json({ error: 'Failed to load backtest results' }, { status: 500 });
     }
   }
   ```

2. **Fetch data in page.tsx**:

   ```typescript
   const [backtestResults, setBacktestResults] = useState<any>(null);
   
   useEffect(() => {
     async function fetchBacktestResults() {
       try {
         const response = await fetch('/api/backtest');
         if (response.ok) {
           const data = await response.json();
           setBacktestResults(data);
         }
       } catch (error) {
         console.error('Error fetching backtest results:', error);
       }
     }
     
     fetchBacktestResults();
   }, []);
   ```

3. **Pass the data to visualization components**:

   ```tsx
   <ParameterHeatmap
     data={backtestResults?.optimization || []}
     paramX="ema_period"
     paramY="extension_threshold"
     metric="total_return"
     title="Parameter Optimization Heatmap"
   />
   ```

## Deployment

### Building for Production

```bash
# Build the dashboard for production
npm run build

# Start the production server
npm start
```

### Deployment Options

1. **Vercel** (Recommended for Next.js):
   ```bash
   npm install -g vercel
   vercel
   ```

2. **Docker**:
   Create a `Dockerfile` in the `mtfema-dashboard` directory:
   ```Dockerfile
   FROM node:18-alpine AS base
   
   FROM base AS deps
   WORKDIR /app
   COPY package.json package-lock.json ./
   RUN npm ci
   
   FROM base AS builder
   WORKDIR /app
   COPY --from=deps /app/node_modules ./node_modules
   COPY . .
   RUN npm run build
   
   FROM base AS runner
   WORKDIR /app
   ENV NODE_ENV production
   COPY --from=builder /app/public ./public
   COPY --from=builder /app/.next/standalone ./
   COPY --from=builder /app/.next/static ./.next/static
   
   EXPOSE 3000
   ENV PORT 3000
   
   CMD ["node", "server.js"]
   ```

   Build and run the Docker container:
   ```bash
   docker build -t mtfema-dashboard .
   docker run -p 3000:3000 mtfema-dashboard
   ```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**:
   - Ensure all dependencies are correctly installed with `npm install`
   - Check import paths start with `@/` for paths within the src directory

2. **Visualization not appearing**:
   - Check browser console for errors
   - Ensure data is correctly formatted for the visualization component
   - Verify that Plotly.js is correctly loaded (using dynamic import)

3. **Dashboard not connecting to backend**:
   - Verify that the Python backtester is running and generating output files
   - Check file paths in API routes match your actual directory structure
   - Look for CORS issues in browser developer console

### Getting Help

If you encounter issues not covered in this guide:
- Check the [GitHub issues](https://github.com/yourusername/mtfema-backtester/issues) for similar problems
- Open a new issue with detailed information about your problem
- Join our community discussion on Discord/Slack for real-time help 