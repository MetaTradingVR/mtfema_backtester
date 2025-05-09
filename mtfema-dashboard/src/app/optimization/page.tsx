"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { 
  fetchOptimizationResults, 
  fetchOptimizationMetrics, 
  fetchParameterImportance, 
  fetchHeatmapData, 
  fetchParallelCoordinatesData,
  cancelOptimization 
} from "@/lib/api";
import { OptimizationResult } from "@/lib/api";
import { Loader2, Info, AlertTriangle, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { OptimizerForm } from "@/components/optimization/optimizer-form";
import { ResultsList } from "@/components/optimization/results-list";
import { ParallelCoordinates } from "@/components/optimization/parallel-coordinates";
import { ParameterImportanceChart } from "@/components/optimization/parameter-importance";
import { HeatmapChart } from "@/components/optimization/heatmap-chart";
import { ParameterConfigForm } from "@/components/optimization/parameter-config-form";

export default function OptimizationPage() {
  const [activeTab, setActiveTab] = useState("run");
  const [results, setResults] = useState<OptimizationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [parameterImportance, setParameterImportance] = useState<any[]>([]);
  const [heatmapData, setHeatmapData] = useState<any[]>([]);
  const [parallelCoordinatesData, setParallelCoordinatesData] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    async function loadResults() {
      try {
        setLoading(true);
        const data = await fetchOptimizationResults();
        setResults(data);
        setError(null);
      } catch (err) {
        setError("Error loading optimization results");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadResults();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold">Strategy Optimization</h1>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="run">Run Optimization</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>
          
          <TabsContent value="run" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Optimization Parameters</CardTitle>
                <CardDescription>
                  Configure and run parameter optimization to find the best strategy settings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <OptimizerForm onComplete={(optimizationId) => {
                  setActiveTab("results");
                  // Refresh results after a short delay
                  setTimeout(() => {
                    fetchOptimizationResults().then(setResults);
                  }, 1000);
                }} />
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="results" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Optimization Results</CardTitle>
                <CardDescription>
                  View and analyze parameter optimization results
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
                      onClick={() => fetchOptimizationResults().then(setResults)}
                    >
                      Retry
                    </Button>
                  </div>
                ) : results.length === 0 ? (
                  <div className="text-center text-muted-foreground p-4">
                    No optimization results found. Run an optimization to see results here.
                  </div>
                ) : (
                  <ResultsList results={results} onSelectResult={(id) => {
                    router.push(`/optimization/${id}`);
                  }} />
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="analysis" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Parameter Analysis</CardTitle>
                <CardDescription>
                  Analyze the impact of different parameters on strategy performance
                </CardDescription>
              </CardHeader>
              <CardContent className="min-h-[400px]">
                {loading ? (
                  <div className="flex justify-center items-center h-40">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : results.length === 0 ? (
                  <div className="text-center text-muted-foreground p-4">
                    No optimization results found. Run an optimization to see analysis.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="h-[400px]">
                      <ParameterImportanceChart results={results} metric="total_return" />
                    </div>
                    <div className="h-[400px]">
                      <ParallelCoordinates results={results} />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
} 