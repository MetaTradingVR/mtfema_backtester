"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ParameterHeatmap } from "@/components/visualizations/parameter-heatmap";
import { ParameterImpact } from "@/components/visualizations/parameter-impact";
import { ParallelCoordinates } from "@/components/visualizations/parallel-coordinates";
import { LiveTradingDashboard } from "@/components/visualizations/live-trading-dashboard";
import { fetchBacktestResults, fetchOptimizationResults, runBacktest, type BacktestResult, type OptimizationResult } from "@/lib/api";
import { EquityCurve } from "@/components/visualizations/equity-curve";
import { DrawdownAnalysis } from "@/components/visualizations/drawdown-analysis";
import { MonthlyPerformance } from "@/components/visualizations/monthly-performance";
import { SimpleServerIndicator } from "@/components/simple-server-indicator";

export default function Home() {
  const [activeTab, setActiveTab] = useState("overview");
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [optimizationResults, setOptimizationResults] = useState<OptimizationResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [backtestParams, setBacktestParams] = useState({
    symbol: "NQ=F",
    timeframe: "M15",
    startDate: "2023-01-01",
    endDate: "2023-12-31",
    ema_period: 9,
    extension_threshold: 1.0
  });

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const results = await fetchBacktestResults();
        if (results.length > 0) {
          setBacktestResults(results[0]);
        }

        const optResults = await fetchOptimizationResults();
        setOptimizationResults(optResults);
        
      } catch (err) {
        setError("Failed to load data. Please try again.");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setBacktestParams(prev => ({
      ...prev,
      [name]: name === 'ema_period' ? parseInt(value) : 
              name === 'extension_threshold' ? parseFloat(value) : 
              value
    }));
  };

  const handleRunBacktest = async () => {
    try {
      setIsBacktesting(true);
      setError(null);
      
      const response = await runBacktest({
        symbol: backtestParams.symbol,
        timeframe: backtestParams.timeframe,
        start_date: backtestParams.startDate,
        end_date: backtestParams.endDate,
        params: {
          ema_period: backtestParams.ema_period,
          extension_threshold: backtestParams.extension_threshold
        }
      });
      
      // Refresh data after backtest
      const results = await fetchBacktestResults();
      if (results.length > 0) {
        setBacktestResults(results[0]);
      }
      
      // Switch to results tab
      setActiveTab("overview");
      
    } catch (err) {
      setError("Failed to run backtest. Please try again.");
      console.error(err);
    } finally {
      setIsBacktesting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Sidebar */}
        <div className="w-64 border-r p-4 shrink-0">
          <h2 className="text-lg font-semibold mb-4">Controls</h2>
          {error && (
            <div className="mb-4 p-2 bg-red-100 text-red-800 rounded text-sm">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="timeframe">Timeframe</label>
              <select 
                id="timeframe"
                name="timeframe"
                className="w-full border rounded p-2"
                value={backtestParams.timeframe}
                onChange={handleInputChange}
              >
                <option value="M5">M5</option>
                <option value="M15">M15</option>
                <option value="H1">H1</option>
                <option value="H4">H4</option>
                <option value="D1">D1</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="symbol">Symbol</label>
              <select 
                id="symbol"
                name="symbol"
                className="w-full border rounded p-2"
                value={backtestParams.symbol}
                onChange={handleInputChange}
              >
                <option value="ES">ES</option>
                <option value="NQ">NQ</option>
                <option value="NQ=F">NQ=F</option>
                <option value="CL">CL</option>
                <option value="GC">GC</option>
                <option value="EUR/USD">EUR/USD</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Date Range</label>
              <input 
                type="date" 
                name="startDate"
                className="w-full border rounded p-2 mb-2" 
                value={backtestParams.startDate}
                onChange={handleInputChange}
              />
              <input 
                type="date" 
                name="endDate"
                className="w-full border rounded p-2" 
                value={backtestParams.endDate}
                onChange={handleInputChange}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Strategy Parameters</label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs mb-1" htmlFor="ema_period">EMA Period</label>
                  <input 
                    type="number" 
                    id="ema_period"
                    name="ema_period"
                    className="w-full border rounded p-1 text-sm" 
                    value={backtestParams.ema_period}
                    onChange={handleInputChange}
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1" htmlFor="extension_threshold">Extension %</label>
                  <input 
                    type="number" 
                    id="extension_threshold"
                    name="extension_threshold"
                    className="w-full border rounded p-1 text-sm" 
                    value={backtestParams.extension_threshold}
                    step="0.1" 
                    onChange={handleInputChange}
                  />
                </div>
              </div>
            </div>
            <Button 
              className="w-full" 
              onClick={handleRunBacktest} 
              disabled={isBacktesting}
            >
              {isBacktesting ? "Running..." : "Run Backtest"}
            </Button>
          </div>
        </div>

        {/* Main content area */}
        <div className="flex-1 p-6 overflow-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
                <p>Loading data...</p>
              </div>
            </div>
          ) : (
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="trades">Trades</TabsTrigger>
                <TabsTrigger value="optimization">Optimization</TabsTrigger>
                <TabsTrigger value="live-trading">Live Trading</TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Strategy Performance</CardTitle>
                    <CardDescription>Key performance metrics for the MT 9 EMA Strategy</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardHeader className="py-3">
                          <CardTitle className="text-base">Total Return</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className={`text-3xl font-bold ${
                            backtestResults?.performance.total_return && 
                            backtestResults.performance.total_return > 0 ? 
                            'text-green-600' : 'text-red-600'
                          }`}>
                            {backtestResults?.performance.total_return 
                              ? `${backtestResults.performance.total_return > 0 ? '+' : ''}${backtestResults.performance.total_return.toFixed(2)}%` 
                              : 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="py-3">
                          <CardTitle className="text-base">Win Rate</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-3xl font-bold">
                            {backtestResults?.performance.win_rate 
                              ? `${backtestResults.performance.win_rate.toFixed(1)}%` 
                              : 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="py-3">
                          <CardTitle className="text-base">Sharpe Ratio</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-3xl font-bold">
                            {backtestResults?.performance.sharpe_ratio 
                              ? backtestResults.performance.sharpe_ratio.toFixed(2)
                              : 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                    </div>
                  </CardContent>
                </Card>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <EquityCurve 
                    equityCurve={backtestResults?.equity_curve || []}
                    title="Equity Curve"
                  />
                  <DrawdownAnalysis 
                    equityCurve={backtestResults?.equity_curve || []}
                    title="Drawdown Analysis"
                  />
                </div>
                
                <MonthlyPerformance
                  monthlyReturns={generateMonthlyReturns(backtestResults)}
                  title="Monthly Performance"
                />
              </TabsContent>

              {/* Trades Tab */}
              <TabsContent value="trades" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Trade List</CardTitle>
                    <CardDescription>All trades executed during the backtesting period</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[600px] overflow-auto">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="text-left border-b">
                            <th className="p-2">Date</th>
                            <th className="p-2">Direction</th>
                            <th className="p-2">Entry</th>
                            <th className="p-2">Exit</th>
                            <th className="p-2">P/L</th>
                            <th className="p-2">Duration</th>
                          </tr>
                        </thead>
                        <tbody>
                          {backtestResults?.trades && backtestResults.trades.length > 0 ? (
                            backtestResults.trades.map((trade, i) => (
                              <tr key={trade.id} className="border-b hover:bg-slate-50">
                                <td className="p-2">{trade.entry_date}</td>
                                <td className="p-2">{trade.direction}</td>
                                <td className="p-2">${trade.entry_price.toFixed(2)}</td>
                                <td className="p-2">${trade.exit_price.toFixed(2)}</td>
                                <td className={`p-2 ${trade.profit_loss > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {trade.profit_loss > 0 ? '+' : ''}${trade.profit_loss.toFixed(2)}
                                </td>
                                <td className="p-2">{trade.duration_hours}h</td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={6} className="p-4 text-center text-muted-foreground">
                                No trade data available
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Optimization Tab */}
              <TabsContent value="optimization" className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  <ParameterHeatmap
                    data={optimizationResults}
                    paramX="ema_period"
                    paramY="extension_threshold"
                    metric="total_return"
                    title="Parameter Optimization Heatmap"
                  />
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <ParameterImpact
                      data={optimizationResults}
                      parameters={["ema_period"]}
                      metric="total_return"
                      title="EMA Period Impact"
                    />
                    
                    <ParameterImpact 
                      data={optimizationResults}
                      parameters={["extension_threshold"]}
                      metric="total_return"
                      title="Extension Threshold Impact"
                    />
                  </div>
                  
                  <ParallelCoordinates
                    data={optimizationResults}
                    parameters={["ema_period", "extension_threshold"]}
                    colorMetric="total_return"
                    title="Multi-Parameter Analysis"
                  />
                </div>
              </TabsContent>

              {/* Live Trading Tab */}
              <TabsContent value="live-trading">
                <LiveTradingDashboard />
              </TabsContent>
            </Tabs>
          )}
        </div>
      </div>
      
      {/* Footer */}
      <footer className="border-t py-4">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} MT 9 EMA Backtester. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm">Privacy</Button>
            <Button variant="ghost" size="sm">Terms</Button>
            <Button variant="ghost" size="sm">Contact</Button>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Helper function to generate monthly returns from backtest data
function generateMonthlyReturns(backtestResults: BacktestResult | null): { year: number; month: number; return: number }[] {
  if (!backtestResults || !backtestResults.equity_curve || backtestResults.equity_curve.length < 2) {
    return [];
  }

  const monthlyReturns: { year: number; month: number; return: number }[] = [];
  const equityCurve = backtestResults.equity_curve;
  
  // Group points by year and month
  const months: Record<string, { start: number; end: number }> = {};
  
  equityCurve.forEach(point => {
    const date = new Date(point.date);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const key = `${year}-${month}`;
    
    if (!months[key]) {
      months[key] = { start: point.equity, end: point.equity };
    } else {
      // Update end value for this month
      months[key].end = point.equity;
    }
  });
  
  // Calculate monthly returns
  for (const [key, value] of Object.entries(months)) {
    const [year, month] = key.split('-').map(Number);
    const monthlyReturn = ((value.end - value.start) / value.start) * 100;
    
    monthlyReturns.push({
      year,
      month,
      return: parseFloat(monthlyReturn.toFixed(2))
    });
  }
  
  return monthlyReturns;
}
