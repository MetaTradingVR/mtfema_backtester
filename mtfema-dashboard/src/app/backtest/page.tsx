"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

// Temporary mock API functions until we fix the API client issues
const fetchBacktestResults = async (): Promise<BacktestResult[]> => {
  // Simulate API call
  return [];
};

interface BacktestResult {
  id: string;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  total_return: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  trades: any[];
  equity_curve: any[];
}

export default function BacktestPage() {
  const [activeTab, setActiveTab] = useState("run");
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBacktest, setSelectedBacktest] = useState<string | null>(null);

  useEffect(() => {
    async function loadResults() {
      try {
        setLoading(true);
        const data = await fetchBacktestResults();
        setResults(data);
        if (data.length > 0 && !selectedBacktest) {
          setSelectedBacktest(data[0].id);
        }
        setError(null);
      } catch (err) {
        setError("Error loading backtest results");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadResults();
  }, [selectedBacktest]);

  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col gap-4">
        {/* No h1 title here to prevent duplication with header */}
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="run">Run Backtest</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>
          
          <TabsContent value="run" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Backtest Configuration</CardTitle>
                <CardDescription>
                  Configure and run strategy backtests
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground p-4">
                  Backtest form will be implemented here
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="results" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Backtest Results</CardTitle>
                <CardDescription>
                  View and analyze backtest performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex justify-center items-center h-40">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : error ? (
                  <div className="text-center text-destructive p-4">
                    {error}
                    <Button 
                      variant="outline" 
                      className="ml-4"
                      onClick={() => fetchBacktestResults().then(setResults)}
                    >
                      Retry
                    </Button>
                  </div>
                ) : results.length === 0 ? (
                  <div className="text-center text-muted-foreground p-4">
                    No backtest results found. Run a backtest to see results here.
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground p-4">
                    Results list will be displayed here
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="analysis" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Analysis</CardTitle>
                <CardDescription>
                  Detailed analysis of backtest performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center text-muted-foreground p-4">
                  Performance analysis will be displayed here
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
