"use client"

import { useState } from "react"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function BacktestPage() {
  const [activeTab, setActiveTab] = useState("configure")
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Backtest Strategy</h1>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-3 mb-4">
          <TabsTrigger value="configure">Configure</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="trades">Trades</TabsTrigger>
        </TabsList>
        
        <TabsContent value="configure" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Strategy Configuration</CardTitle>
              <CardDescription>
                Set parameters for the MT 9 EMA strategy
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Symbol</label>
                    <Select defaultValue="NQ=F">
                      <SelectTrigger>
                        <SelectValue placeholder="Select symbol" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NQ=F">NQ=F (Nasdaq)</SelectItem>
                        <SelectItem value="ES=F">ES=F (S&P 500)</SelectItem>
                        <SelectItem value="YM=F">YM=F (Dow)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Timeframe</label>
                    <Select defaultValue="M15">
                      <SelectTrigger>
                        <SelectValue placeholder="Select timeframe" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="M5">5 Minutes</SelectItem>
                        <SelectItem value="M15">15 Minutes</SelectItem>
                        <SelectItem value="M30">30 Minutes</SelectItem>
                        <SelectItem value="H1">1 Hour</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Start Date</label>
                    <Input type="date" defaultValue="2023-01-01" />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">End Date</label>
                    <Input type="date" defaultValue="2023-12-31" />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-md font-semibold">Strategy Parameters</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">EMA Period</label>
                      <Input type="number" min="1" max="50" defaultValue="9" />
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Extension %</label>
                      <Input type="number" min="0.1" max="5" step="0.1" defaultValue="1" />
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Stop Loss %</label>
                      <Input type="number" min="0.1" max="10" step="0.1" defaultValue="2" />
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Take Profit %</label>
                      <Input type="number" min="0.1" max="10" step="0.1" defaultValue="3" />
                    </div>
                  </div>
                </div>
                
                <Button type="submit" className="w-full">Run Backtest</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="results" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Backtest Results</CardTitle>
              <CardDescription>
                Performance metrics and statistics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-muted-foreground">Run a backtest to see results here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="trades" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trade History</CardTitle>
              <CardDescription>
                Individual trade details and analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-muted-foreground">Run a backtest to see trade history</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 