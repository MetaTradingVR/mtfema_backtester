"use client"

import { useState } from "react"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { BacktestConfigForm } from "@/components/backtest/backtest-config-form"
import { IndicatorResults } from "@/components/backtest/indicator-results"
import { runBacktestWithIndicators, type BacktestParams, type BacktestResult } from "@/lib/api"
import { PageHeader } from "@/components/page-header"

export default function BacktestPage() {
  const [activeTab, setActiveTab] = useState("configure")
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<BacktestResult | null>(null)
  
  // Handle running a backtest
  const handleRunBacktest = async (params: BacktestParams) => {
    setIsRunning(true)
    setError(null)
    
    try {
      // Run the backtest with custom indicators
      const response = await runBacktestWithIndicators(params)
      
      // Fetch the results
      // Note: Normally you would fetch the results using the ID returned from the API
      // This is a simplified version that assumes the result is returned directly
      
      // Mock result for development (remove in production)
      const mockResult: BacktestResult = {
        id: response.id || "mock-id",
        symbol: params.symbol,
        timeframe: params.timeframe,
        start_date: params.start_date,
        end_date: params.end_date,
        params: {
          ...params.strategy_params
        },
        performance: {
          total_return: 18.4,
          win_rate: 62.7,
          sharpe_ratio: 1.42,
          max_drawdown: 8.6,
          profit_factor: 1.85,
          total_trades: 142,
          avg_trade: 0.13
        },
        equity_curve: Array.from({ length: 100 }, (_, i) => ({
          date: new Date(2023, 0, i + 1).toISOString().split('T')[0],
          equity: 10000 * (1 + (Math.sin(i / 10) * 0.05) + (i / 100))
        })),
        trades: Array.from({ length: 20 }, (_, i) => ({
          id: `trade-${i}`,
          entry_date: new Date(2023, i % 12, (i * 3) % 28 + 1).toISOString().split('T')[0],
          exit_date: new Date(2023, i % 12, (i * 3) % 28 + 2 + (i % 3)).toISOString().split('T')[0],
          direction: i % 2 === 0 ? 'Long' : 'Short',
          entry_price: 15000 + i * 100,
          exit_price: 15000 + i * 100 + (i % 2 === 0 ? 80 : -40),
          profit_loss: i % 2 === 0 ? 80 : -40,
          profit_loss_pct: i % 2 === 0 ? 0.53 : -0.27,
          duration_hours: i * 2 + 1
        })),
        // Include custom indicators in the result if provided
        custom_indicators: params.custom_indicators
      }
      
      setResult(mockResult)
      
      // Switch to results tab
      setActiveTab("results")
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError("An unknown error occurred")
      }
    } finally {
      setIsRunning(false)
    }
  }
  
  // Render backtest results
  const renderResults = () => {
    if (!result) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">Run a backtest to see results here</p>
        </div>
      )
    }
    
    // Generate dates array for charts
    const dates = result.equity_curve.map(point => point.date)
    
    // Generate price data for charts (mock data for development)
    const prices = {
      open: Array.from({ length: dates.length }, (_, i) => 15000 + i * 10 - (i % 2) * 20),
      high: Array.from({ length: dates.length }, (_, i) => 15100 + i * 10 + (i % 3) * 15),
      low: Array.from({ length: dates.length }, (_, i) => 14950 + i * 10 - (i % 3) * 15),
      close: Array.from({ length: dates.length }, (_, i) => 15020 + i * 10 + (i % 2) * 20)
    }
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Return</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{result.performance.total_return.toFixed(2)}%</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{result.performance.win_rate.toFixed(2)}%</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Profit Factor</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{result.performance.profit_factor.toFixed(2)}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{result.performance.max_drawdown.toFixed(2)}%</div>
            </CardContent>
          </Card>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>Equity Curve</CardTitle>
            <CardDescription>
              Performance over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-md">
              <p className="text-muted-foreground">Equity chart will be rendered here</p>
              {/* Replace with actual chart component in production */}
            </div>
          </CardContent>
        </Card>
        
        {/* Add the indicator results component if we have custom indicators */}
        {result.custom_indicators && result.custom_indicators.length > 0 && (
          <IndicatorResults 
            indicators={result.custom_indicators} 
            dates={dates}
            prices={prices}
          />
        )}
      </div>
    )
  }
  
  // Render trade details
  const renderTrades = () => {
    if (!result) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">Run a backtest to see trade history</p>
        </div>
      )
    }
    
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Trade Summary</CardTitle>
            <CardDescription>
              Overview of all trades
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="py-2 px-4 text-left">ID</th>
                    <th className="py-2 px-4 text-left">Direction</th>
                    <th className="py-2 px-4 text-left">Entry Date</th>
                    <th className="py-2 px-4 text-left">Exit Date</th>
                    <th className="py-2 px-4 text-right">Entry Price</th>
                    <th className="py-2 px-4 text-right">Exit Price</th>
                    <th className="py-2 px-4 text-right">P/L</th>
                    <th className="py-2 px-4 text-right">P/L %</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((trade) => (
                    <tr key={trade.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="py-2 px-4">{trade.id}</td>
                      <td className="py-2 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          trade.direction === 'Long' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' 
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                        }`}>
                          {trade.direction}
                        </span>
                      </td>
                      <td className="py-2 px-4">{trade.entry_date}</td>
                      <td className="py-2 px-4">{trade.exit_date}</td>
                      <td className="py-2 px-4 text-right">{trade.entry_price.toFixed(2)}</td>
                      <td className="py-2 px-4 text-right">{trade.exit_price.toFixed(2)}</td>
                      <td className={`py-2 px-4 text-right ${
                        trade.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {trade.profit_loss.toFixed(2)}
                      </td>
                      <td className={`py-2 px-4 text-right ${
                        trade.profit_loss_pct >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {trade.profit_loss_pct.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto py-6">
      <PageHeader
        heading="Backtest Strategy"
        text="Test the MT 9 EMA strategy with historical data and custom indicators"
      />
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="configure">Configure</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="trades">Trades</TabsTrigger>
        </TabsList>
        
        <TabsContent value="configure" className="space-y-4">
          <BacktestConfigForm 
            onSubmit={handleRunBacktest}
            isSubmitting={isRunning}
            error={error}
          />
        </TabsContent>
        
        <TabsContent value="results" className="space-y-4">
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {renderResults()}
        </TabsContent>
        
        <TabsContent value="trades" className="space-y-4">
          {renderTrades()}
        </TabsContent>
      </Tabs>
    </div>
  )
} 