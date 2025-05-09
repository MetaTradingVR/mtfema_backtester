"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, PlayCircle, StopCircle } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

// Temporary mock API functions until we fix the API client issues
const fetchLiveTradingStatus = async () => {
  // Simulate API call
  return {
    isRunning: false,
    activeSymbols: ["ES", "NQ"],
    lastUpdate: new Date().toISOString(),
    trades: [],
    positions: [],
    equity: [],
  };
};

const startLiveTrading = async () => {
  // Simulate API call
  return { success: true };
};

const stopLiveTrading = async () => {
  // Simulate API call
  return { success: true };
};

export default function LiveTradingPage() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [status, setStatus] = useState<any>({
    isRunning: false,
    activeSymbols: [],
    lastUpdate: null,
    trades: [],
    positions: [],
    equity: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Function to load live trading status
  const loadStatus = async () => {
    try {
      setLoading(true);
      const data = await fetchLiveTradingStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError("Error loading live trading status");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Start auto-refresh when component mounts
  useEffect(() => {
    loadStatus();
    
    let interval: NodeJS.Timeout | null = null;
    
    if (autoRefresh) {
      interval = setInterval(() => {
        loadStatus();
      }, 5000); // Refresh every 5 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  // Handle starting live trading
  const handleStart = async () => {
    try {
      setLoading(true);
      await startLiveTrading();
      await loadStatus();
    } catch (err) {
      setError("Error starting live trading");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle stopping live trading
  const handleStop = async () => {
    try {
      setLoading(true);
      await stopLiveTrading();
      await loadStatus();
    } catch (err) {
      setError("Error stopping live trading");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col gap-4">
        <div className="flex justify-between items-center">
          {/* No h1 title here to prevent duplication with header */}
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Switch 
                id="auto-refresh" 
                checked={autoRefresh} 
                onCheckedChange={setAutoRefresh} 
              />
              <Label htmlFor="auto-refresh">Auto-refresh</Label>
            </div>
            
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadStatus}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Refresh
            </Button>
          </div>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>Trading Status</CardTitle>
            <CardDescription>
              Control and monitor the live trading system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${status.isRunning ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>Status: {status.isRunning ? 'Running' : 'Stopped'}</span>
              </div>
              
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  className="flex items-center"
                  onClick={handleStart}
                  disabled={status.isRunning || loading}
                >
                  <PlayCircle className="h-4 w-4 mr-2" />
                  Start Trading
                </Button>
                <Button
                  variant="outline"
                  className="flex items-center"
                  onClick={handleStop}
                  disabled={!status.isRunning || loading}
                >
                  <StopCircle className="h-4 w-4 mr-2" />
                  Stop Trading
                </Button>
              </div>
            </div>
            
            {status.activeSymbols && status.activeSymbols.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium mb-2">Active Symbols</h3>
                <div className="flex flex-wrap gap-2">
                  {status.activeSymbols.map((symbol: string) => (
                    <span key={symbol} className="px-2 py-1 bg-muted rounded-md text-sm">
                      {symbol}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="trades">Trades</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>
          
          <TabsContent value="dashboard" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Live Trading Dashboard</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground p-4">
                  Live trading dashboard will be displayed here
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="trades" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Trades</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground p-4">
                  Trade list will be displayed here
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="account" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Account Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground p-4">
                  Account metrics will be displayed here
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
