"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2, ArrowUp, ArrowDown, DollarSign, BarChart4 } from "lucide-react"
import { fetchLiveTradingStatus, LiveTradingUpdate, LiveTrade } from "@/lib/api"

export default function LiveTradingPage() {
  const [status, setStatus] = useState<LiveTradingUpdate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("dashboard")

  useEffect(() => {
    async function loadStatus() {
      try {
        setLoading(true)
        const data = await fetchLiveTradingStatus()
        setStatus(data)
        setError(null)
      } catch (err) {
        console.error(err)
        setError("Failed to load live trading status")
      } finally {
        setLoading(false)
      }
    }

    loadStatus()
    // In a real implementation, we would set up a websocket or polling
    const interval = setInterval(loadStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !status) {
    return (
      <div className="container mx-auto p-4 flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Live Trading</h1>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-3 mb-4">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="positions">Positions</TabsTrigger>
          <TabsTrigger value="signals">Recent Signals</TabsTrigger>
        </TabsList>
        
        <TabsContent value="dashboard" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Account Equity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <DollarSign className="h-5 w-5 text-muted-foreground mr-2" />
                  <div className="text-2xl font-bold">
                    ${status?.account_equity.toFixed(2)}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Daily P&L</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <BarChart4 className="h-5 w-5 text-muted-foreground mr-2" />
                  <div className={`text-2xl font-bold ${status?.daily_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {status?.daily_pnl >= 0 ? '+' : ''}{status?.daily_pnl.toFixed(2)}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Current Position</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  {status?.current_position === "Long" ? (
                    <ArrowUp className="h-5 w-5 text-green-500 mr-2" />
                  ) : status?.current_position === "Short" ? (
                    <ArrowDown className="h-5 w-5 text-red-500 mr-2" />
                  ) : (
                    <div className="h-5 w-5 mr-2" />
                  )}
                  <div className="text-xl font-medium">
                    {status?.current_position || "Flat"}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Last Signal</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <Badge className={
                    status?.last_signal === "Buy" ? "bg-green-500" : 
                    status?.last_signal === "Sell" ? "bg-red-500" :
                    status?.last_signal === "Exit" ? "bg-yellow-500" : 
                    "bg-gray-500"
                  }>
                    {status?.last_signal || "None"}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
          
          <Card>
            <CardHeader>
              <CardTitle>Active Trades</CardTitle>
              <CardDescription>Currently open positions</CardDescription>
            </CardHeader>
            <CardContent>
              {status?.active_trades.length ? (
                <div className="space-y-4">
                  {status.active_trades.map((trade) => (
                    <div key={trade.id} className="p-4 border rounded-lg">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold">{trade.symbol}</h3>
                          <p className="text-sm text-muted-foreground">
                            Entry: {new Date(trade.entry_time).toLocaleString()}
                          </p>
                        </div>
                        <Badge className={
                          trade.direction === "Long" ? "bg-green-500" : "bg-red-500"
                        }>
                          {trade.direction}
                        </Badge>
                      </div>
                      <div className="mt-2 grid grid-cols-3 gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground">Entry Price</p>
                          <p className="font-medium">{trade.entry_price}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Current Price</p>
                          <p className="font-medium">{trade.current_price}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">P&L</p>
                          <p className={`font-medium ${
                            trade.current_pnl >= 0 ? "text-green-500" : "text-red-500"
                          }`}>
                            {trade.current_pnl >= 0 ? "+" : ""}{trade.current_pnl} ({trade.current_pnl_pct.toFixed(2)}%)
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No active trades</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="positions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Open Positions</CardTitle>
              <CardDescription>Currently active positions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                {status?.active_trades.length ? (
                  <p>Position details will be displayed here</p>
                ) : (
                  <p className="text-muted-foreground">No open positions</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="signals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trading Signals</CardTitle>
              <CardDescription>Recent strategy signals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-muted-foreground">Recent signals will be displayed here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 