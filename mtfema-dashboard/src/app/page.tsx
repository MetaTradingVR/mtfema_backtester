"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ParameterHeatmap } from "@/components/visualizations/parameter-heatmap";
import { ParameterImpact } from "@/components/visualizations/parameter-impact";
import { ParallelCoordinates } from "@/components/visualizations/parallel-coordinates";
import { LiveTradingDashboard } from "@/components/visualizations/live-trading-dashboard";

export default function Home() {
  const [activeTab, setActiveTab] = useState("overview");
  const [isBacktesting, setIsBacktesting] = useState(false);

  const handleRunBacktest = () => {
    setIsBacktesting(true);
    // Simulate backtest completion after 3 seconds
    setTimeout(() => {
      setIsBacktesting(false);
      setActiveTab("optimization");
    }, 3000);
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">MT 9 EMA Backtester</h1>
          <nav className="flex gap-4 items-center">
            <a href="#" className="hover:underline">Documentation</a>
            <a href="#" className="hover:underline">Settings</a>
            <Button onClick={handleRunBacktest} disabled={isBacktesting}>
              {isBacktesting ? "Running..." : "Run Backtest"}
            </Button>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Sidebar */}
        <div className="w-64 border-r p-4 shrink-0">
          <h2 className="text-lg font-semibold mb-4">Controls</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Timeframe</label>
              <select className="w-full border rounded p-2">
                <option>M5</option>
                <option>M15</option>
                <option>H1</option>
                <option>H4</option>
                <option>D1</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Symbol</label>
              <select className="w-full border rounded p-2">
                <option>ES</option>
                <option>NQ</option>
                <option selected>NQ=F</option>
                <option>CL</option>
                <option>GC</option>
                <option>EUR/USD</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Date Range</label>
              <input type="date" className="w-full border rounded p-2 mb-2" defaultValue="2023-01-01" />
              <input type="date" className="w-full border rounded p-2" defaultValue="2023-12-31" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Strategy Parameters</label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs mb-1">EMA Period</label>
                  <input type="number" className="w-full border rounded p-1 text-sm" defaultValue="9" />
                </div>
                <div>
                  <label className="block text-xs mb-1">Extension %</label>
                  <input type="number" className="w-full border rounded p-1 text-sm" defaultValue="1.0" step="0.1" />
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
                        <p className="text-3xl font-bold text-green-600">+18.4%</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="py-3">
                        <CardTitle className="text-base">Win Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-3xl font-bold">62.7%</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="py-3">
                        <CardTitle className="text-base">Sharpe Ratio</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-3xl font-bold">1.42</p>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Equity Curve</CardTitle>
                    <CardDescription>Cumulative performance over time</CardDescription>
                  </CardHeader>
                  <CardContent className="h-[300px] flex items-center justify-center bg-slate-50">
                    <p className="text-muted-foreground">Equity curve will appear here</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Drawdown Analysis</CardTitle>
                    <CardDescription>Drawdown periods and recovery</CardDescription>
                  </CardHeader>
                  <CardContent className="h-[300px] flex items-center justify-center bg-slate-50">
                    <p className="text-muted-foreground">Drawdown chart will appear here</p>
                  </CardContent>
                </Card>
              </div>
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
                        {Array.from({ length: 10 }).map((_, i) => (
                          <tr key={i} className="border-b hover:bg-slate-50">
                            <td className="p-2">2023-{Math.floor(i/2) + 1}-{i*3 + 1}</td>
                            <td className="p-2">{i % 2 === 0 ? 'Long' : 'Short'}</td>
                            <td className="p-2">${(15000 + i * 100).toFixed(2)}</td>
                            <td className="p-2">${(15000 + i * 100 + (i % 2 === 0 ? 80 : -40)).toFixed(2)}</td>
                            <td className={`p-2 ${i % 2 === 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {i % 2 === 0 ? '+$80.00' : '-$40.00'}
                            </td>
                            <td className="p-2">{i*2 + 1}h</td>
                          </tr>
                        ))}
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
                  data={[]}
                  paramX="ema_period"
                  paramY="extension_threshold"
                  metric="total_return"
                  title="Parameter Optimization Heatmap"
                />
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <ParameterImpact
                    data={[]}
                    parameters={["ema_period"]}
                    metric="total_return"
                    title="EMA Period Impact"
                  />
                  
                  <ParameterImpact 
                    data={[]}
                    parameters={["extension_threshold"]}
                    metric="total_return"
                    title="Extension Threshold Impact"
                  />
                </div>
                
                <ParallelCoordinates
                  data={[]}
                  parameters={["ema_period", "extension_threshold", "stop_loss"]}
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
