import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Dynamically import Plot from react-plotly.js
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false, // Disable server-side rendering
  loading: () => <div className="w-full h-[400px] flex items-center justify-center">Loading chart...</div>
});

interface LiveTradingDashboardProps {
  data?: {
    priceSeries: { timestamp: string; price: number }[];
    emaSeries: { timestamp: string; value: number }[];
    trades: {
      timestamp: string;
      type: 'ENTRY' | 'EXIT';
      price: number;
      size: number;
      pnl?: number;
      timeframe?: string;
    }[];
    positions: {
      symbol: string;
      size: number;
      entryPrice: number;
      currentPrice: number;
      pnl: number;
      openTime: string;
    }[];
    performance: {
      totalPnl: number;
      winRate: number;
      averageWin: number;
      averageLoss: number;
      profitFactor: number;
      sharpeRatio: number;
    };
  };
  className?: string;
}

export function LiveTradingDashboard({ data, className }: LiveTradingDashboardProps) {
  const [priceChartData, setPriceChartData] = useState<any[]>([]);
  const [priceChartLayout, setPriceChartLayout] = useState<any>({});
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [performanceLayout, setPerformanceLayout] = useState<any>({});
  
  // Generate sample data for demonstration
  const generateSampleData = () => {
    // Generate sample price series (last 100 candles)
    const now = new Date();
    const priceSeries = [];
    const emaSeries = [];
    let price = 4200 + Math.random() * 200; // Starting price around 4200 (ES futures)
    
    for (let i = 0; i < 100; i++) {
      const timestamp = new Date(now.getTime() - (100 - i) * 5 * 60000).toISOString(); // 5-minute candles
      
      // Simulate price movement
      price += (Math.random() - 0.48) * 5; // Slight upward bias
      priceSeries.push({ timestamp, price });
      
      // Simple 9 EMA calculation (simplified for demo)
      if (i >= 8) {
        const emaValue = priceSeries.slice(i-8, i+1).reduce((sum, p) => sum + p.price, 0) / 9;
        emaSeries.push({ timestamp, value: emaValue });
      } else {
        emaSeries.push({ timestamp, value: price }); // Placeholder until we have enough data
      }
    }
    
    // Generate sample trades
    const trades = [];
    for (let i = 20; i < 90; i += 10) {
      // Entry trade
      const entryTimestamp = priceSeries[i].timestamp;
      const entryPrice = priceSeries[i].price;
      const size = Math.random() > 0.5 ? 1 : -1; // 1 for long, -1 for short
      trades.push({
        timestamp: entryTimestamp,
        type: 'ENTRY',
        price: entryPrice,
        size,
        timeframe: Math.random() > 0.5 ? 'M5' : 'M15'
      });
      
      // Exit trade (a few bars later)
      const exitIndex = i + 3 + Math.floor(Math.random() * 5);
      if (exitIndex < priceSeries.length) {
        const exitTimestamp = priceSeries[exitIndex].timestamp;
        const exitPrice = priceSeries[exitIndex].price;
        const pnl = size * (exitPrice - entryPrice) * 50; // $50 per point for ES futures
        trades.push({
          timestamp: exitTimestamp,
          type: 'EXIT',
          price: exitPrice,
          size: -size, // Opposite of entry
          pnl
        });
      }
    }
    
    // Current open positions (if any)
    const positions = [];
    if (Math.random() > 0.5) {
      const entryIndex = 92;
      positions.push({
        symbol: 'ES',
        size: Math.random() > 0.5 ? 1 : -1,
        entryPrice: priceSeries[entryIndex].price,
        currentPrice: priceSeries[priceSeries.length - 1].price,
        pnl: (priceSeries[priceSeries.length - 1].price - priceSeries[entryIndex].price) * 50,
        openTime: priceSeries[entryIndex].timestamp
      });
    }
    
    // Performance metrics
    const completedTrades = trades.filter(t => t.type === 'EXIT');
    const winningTrades = completedTrades.filter(t => (t.pnl || 0) > 0);
    const losingTrades = completedTrades.filter(t => (t.pnl || 0) <= 0);
    
    const performance = {
      totalPnl: completedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0),
      winRate: winningTrades.length / (completedTrades.length || 1),
      averageWin: winningTrades.length ? winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / winningTrades.length : 0,
      averageLoss: losingTrades.length ? losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / losingTrades.length : 0,
      profitFactor: losingTrades.length ? Math.abs(winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)) : 0,
      sharpeRatio: 1.2 + Math.random()
    };
    
    return {
      priceSeries,
      emaSeries,
      trades,
      positions,
      performance
    };
  };
  
  useEffect(() => {
    const sampleData = data || generateSampleData();
    
    // Create price chart data
    const timestamps = sampleData.priceSeries.map(p => p.timestamp);
    
    // Price trace
    const priceTrace = {
      x: timestamps,
      y: sampleData.priceSeries.map(p => p.price),
      type: 'scatter',
      mode: 'lines',
      name: 'Price',
      line: { color: 'rgba(31, 119, 180, 1)', width: 2 }
    };
    
    // EMA trace
    const emaTrace = {
      x: timestamps,
      y: sampleData.emaSeries.map(e => e.value),
      type: 'scatter',
      mode: 'lines',
      name: '9 EMA',
      line: { color: 'rgba(255, 127, 14, 1)', width: 2 }
    };
    
    // Entry points trace
    const entryTrades = sampleData.trades.filter(t => t.type === 'ENTRY');
    const entryTraceUp = {
      x: entryTrades.filter(t => t.size > 0).map(t => t.timestamp),
      y: entryTrades.filter(t => t.size > 0).map(t => t.price),
      type: 'scatter',
      mode: 'markers',
      name: 'Long Entry',
      marker: { color: 'green', size: 10, symbol: 'triangle-up' }
    };
    
    const entryTraceDown = {
      x: entryTrades.filter(t => t.size < 0).map(t => t.timestamp),
      y: entryTrades.filter(t => t.size < 0).map(t => t.price),
      type: 'scatter',
      mode: 'markers',
      name: 'Short Entry',
      marker: { color: 'red', size: 10, symbol: 'triangle-down' }
    };
    
    // Exit points trace
    const exitTrades = sampleData.trades.filter(t => t.type === 'EXIT');
    const exitTraceUp = {
      x: exitTrades.filter(t => t.size > 0).map(t => t.timestamp),
      y: exitTrades.filter(t => t.size > 0).map(t => t.price),
      type: 'scatter',
      mode: 'markers',
      name: 'Long Exit',
      marker: { color: 'rgba(0, 128, 0, 0.5)', size: 10, symbol: 'circle' }
    };
    
    const exitTraceDown = {
      x: exitTrades.filter(t => t.size < 0).map(t => t.timestamp),
      y: exitTrades.filter(t => t.size < 0).map(t => t.price),
      type: 'scatter',
      mode: 'markers',
      name: 'Short Exit',
      marker: { color: 'rgba(255, 0, 0, 0.5)', size: 10, symbol: 'circle' }
    };
    
    // Set price chart data and layout
    setPriceChartData([priceTrace, emaTrace, entryTraceUp, entryTraceDown, exitTraceUp, exitTraceDown]);
    setPriceChartLayout({
      title: { text: 'Live Price Chart with MT 9 EMA Strategy' },
      xaxis: { 
        title: { text: 'Time' },
        type: 'date',
        rangeslider: { visible: false }
      },
      yaxis: { title: { text: 'Price' } },
      legend: { orientation: 'h', y: 1.1 },
      margin: { l: 50, r: 50, b: 50, t: 80 },
      height: 400,
      autosize: true
    });
    
    // Create performance metrics chart
    const { performance } = sampleData;
    const metricsTrace = {
      x: ['Win Rate', 'Avg Win', 'Avg Loss', 'Profit Factor', 'Sharpe Ratio'],
      y: [
        performance.winRate * 100, 
        performance.averageWin, 
        Math.abs(performance.averageLoss), // Use absolute value for visualization
        performance.profitFactor,
        performance.sharpeRatio
      ],
      type: 'bar',
      marker: {
        color: ['#22c55e', '#22c55e', '#ef4444', '#3b82f6', '#f59e0b']
      }
    };
    
    setPerformanceData([metricsTrace]);
    setPerformanceLayout({
      title: { text: 'Performance Metrics' },
      yaxis: { title: { text: 'Value' } },
      showlegend: false,
      margin: { l: 50, r: 50, b: 100, t: 80 },
      height: 400,
      autosize: true,
      annotations: [
        {
          x: 0,
          y: performance.winRate * 100,
          text: `${(performance.winRate * 100).toFixed(1)}%`,
          yanchor: 'bottom',
          showarrow: false
        },
        {
          x: 1,
          y: performance.averageWin,
          text: `$${performance.averageWin.toFixed(0)}`,
          yanchor: 'bottom',
          showarrow: false
        },
        {
          x: 2,
          y: Math.abs(performance.averageLoss),
          text: `$${Math.abs(performance.averageLoss).toFixed(0)}`,
          yanchor: 'bottom',
          showarrow: false
        },
        {
          x: 3,
          y: performance.profitFactor,
          text: performance.profitFactor.toFixed(2),
          yanchor: 'bottom',
          showarrow: false
        },
        {
          x: 4,
          y: performance.sharpeRatio,
          text: performance.sharpeRatio.toFixed(2),
          yanchor: 'bottom',
          showarrow: false
        }
      ]
    });
  }, [data]);

  return (
    <Card className={`w-full h-full ${className || ''}`}>
      <CardHeader>
        <CardTitle>Live Trading Dashboard</CardTitle>
        <CardDescription>Real-time performance monitoring for the MT 9 EMA strategy</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="price-chart" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="price-chart">Price Chart</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="positions">Positions</TabsTrigger>
          </TabsList>
          
          <TabsContent value="price-chart" className="w-full">
            {priceChartData.length > 0 ? (
              <Plot
                data={priceChartData}
                layout={priceChartLayout}
                config={{ responsive: true }}
                className="w-full"
              />
            ) : (
              <div className="w-full h-[400px] flex items-center justify-center">Loading chart...</div>
            )}
          </TabsContent>
          
          <TabsContent value="performance">
            {performanceData.length > 0 ? (
              <Plot
                data={performanceData}
                layout={performanceLayout}
                config={{ responsive: true }}
                className="w-full"
              />
            ) : (
              <div className="w-full h-[400px] flex items-center justify-center">Loading performance metrics...</div>
            )}
          </TabsContent>
          
          <TabsContent value="positions">
            <div className="w-full overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-muted">
                    <th className="p-2 text-left">Symbol</th>
                    <th className="p-2 text-left">Size</th>
                    <th className="p-2 text-left">Entry Price</th>
                    <th className="p-2 text-left">Current Price</th>
                    <th className="p-2 text-left">P&L</th>
                    <th className="p-2 text-left">Open Time</th>
                  </tr>
                </thead>
                <tbody>
                  {(data || generateSampleData()).positions.length > 0 ? (
                    (data || generateSampleData()).positions.map((position, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2">{position.symbol}</td>
                        <td className={`p-2 ${position.size > 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {position.size > 0 ? `+${position.size}` : position.size}
                        </td>
                        <td className="p-2">{position.entryPrice.toFixed(2)}</td>
                        <td className="p-2">{position.currentPrice.toFixed(2)}</td>
                        <td className={`p-2 ${position.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          ${position.pnl.toFixed(2)}
                        </td>
                        <td className="p-2">{new Date(position.openTime).toLocaleString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="p-4 text-center">No open positions</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-2">Recent Trades</h3>
              <div className="w-full overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-muted">
                      <th className="p-2 text-left">Time</th>
                      <th className="p-2 text-left">Type</th>
                      <th className="p-2 text-left">Price</th>
                      <th className="p-2 text-left">Size</th>
                      <th className="p-2 text-left">P&L</th>
                      <th className="p-2 text-left">Timeframe</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data || generateSampleData()).trades.slice(-5).reverse().map((trade, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2">{new Date(trade.timestamp).toLocaleString()}</td>
                        <td className={`p-2 ${trade.type === 'ENTRY' ? 'font-semibold' : ''}`}>{trade.type}</td>
                        <td className="p-2">{trade.price.toFixed(2)}</td>
                        <td className={`p-2 ${trade.size > 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {trade.size > 0 ? `+${trade.size}` : trade.size}
                        </td>
                        <td className={`p-2 ${(trade.pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                        </td>
                        <td className="p-2">{trade.timeframe || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
