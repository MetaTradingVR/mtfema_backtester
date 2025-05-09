"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { 
  fetchOptimizationById, 
  fetchOptimizationResults, 
  fetchOptimizationMetrics,
  fetchParameterImportance, 
  fetchHeatmapData, 
  fetchParallelCoordinatesData, 
  cancelOptimization 
} from "@/lib/api";
import { Loader2, ArrowLeft, Download, RefreshCw, AlertTriangle } from "lucide-react";
import { ParallelCoordinates } from "@/components/optimization/parallel-coordinates";
import { ParameterImportanceChart } from "@/components/optimization/parameter-importance";
import { HeatmapChart } from "@/components/optimization/heatmap-chart";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function OptimizationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = typeof params.id === "string" ? params.id : "";
  
  const [optimization, setOptimization] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedParams, setSelectedParams] = useState<{param1: string; param2: string}>({
    param1: "",
    param2: ""
  });

  useEffect(() => {
    async function loadOptimization() {
      try {
        setLoading(true);
        const data = await fetchOptimizationById(id);
        if (data) {
          setOptimization(data);
          
          // Set initial parameters for heatmap if we have results
          if (data.results && data.results.length > 0 && data.results[0].params) {
            const paramKeys = Object.keys(data.results[0].params);
            if (paramKeys.length >= 2) {
              setSelectedParams({
                param1: paramKeys[0],
                param2: paramKeys[1]
              });
            }
          }
          
          setError(null);
        } else {
          setError("Optimization not found");
        }
      } catch (err) {
        console.error("Error loading optimization:", err);
        setError("Failed to load optimization data");
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      loadOptimization();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="container mx-auto p-4 flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !optimization) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-destructive/10 text-destructive p-4 rounded-md">
          {error || "Failed to load optimization"}
          <Button 
            variant="outline" 
            size="sm" 
            className="ml-4"
            onClick={() => router.push("/optimization")}
          >
            Back to Optimizations
          </Button>
        </div>
      </div>
    );
  }

  // Get all unique parameter names
  const paramNames = Array.from(
    new Set(
      optimization.results.flatMap(result => 
        Object.keys(result.params)
      )
    )
  );

  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => router.push("/optimization")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <h1 className="text-2xl font-bold">Optimization Results</h1>
          </div>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Results
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="font-medium">Symbol:</dt>
                  <dd>{optimization.symbol}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="font-medium">Timeframe:</dt>
                  <dd>{optimization.timeframe}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="font-medium">Date Range:</dt>
                  <dd>{optimization.start_date} - {optimization.end_date}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="font-medium">Method:</dt>
                  <dd>
                    <Badge variant="outline">
                      {optimization.method === "grid" 
                        ? "Grid Search" 
                        : optimization.method === "random" 
                          ? "Random Search"
                          : "Bayesian Optimization"}
                    </Badge>
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="font-medium">Results:</dt>
                  <dd>{optimization.results.length}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="font-medium">Metric:</dt>
                  <dd>{optimization.metric}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>
          
          <Card className="md:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle>Best Parameters</CardTitle>
              <CardDescription>
                These parameters produced the best results based on {optimization.metric}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {Object.entries(optimization.best_params).map(([key, value]) => (
                  <Badge key={key} variant="secondary" className="text-xs">
                    {key}: {value}
                  </Badge>
                ))}
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Performance Metrics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(optimization.best_metrics).map(([key, value]) => (
                    <div key={key} className="bg-muted/50 p-2 rounded-md">
                      <div className="text-xs text-muted-foreground">{key.replace('_', ' ')}</div>
                      <div className="text-lg font-semibold">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                        {key.includes('return') || key.includes('rate') ? '%' : ''}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <Tabs defaultValue="results" className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="visualizations">Visualizations</TabsTrigger>
            <TabsTrigger value="analysis">Parameter Analysis</TabsTrigger>
          </TabsList>
          
          <TabsContent value="results" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Top Results</CardTitle>
                <CardDescription>
                  Showing top 20 parameter combinations sorted by {optimization.metric}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[80px]">Rank</TableHead>
                        <TableHead>Parameters</TableHead>
                        {Object.keys(optimization.results[0]?.metrics || {}).map(metric => (
                          <TableHead key={metric} className="w-[120px]">
                            {metric.replace('_', ' ')}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {optimization.results.slice(0, 20).map((result, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">#{index + 1}</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {Object.entries(result.params).map(([key, value]) => (
                                <Badge key={key} variant="outline" className="text-xs">
                                  {key}: {value}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          {Object.entries(result.metrics).map(([key, value]) => (
                            <TableCell 
                              key={key}
                              className={
                                key === 'total_return' && typeof value === 'number'
                                  ? value > 0 ? 'text-green-600' : 'text-red-600'
                                  : ''
                              }
                            >
                              {typeof value === 'number' ? value.toFixed(2) : value}
                              {key.includes('return') || key.includes('rate') ? '%' : ''}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="visualizations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Parameter Relationships</CardTitle>
                <CardDescription>
                  Parallel coordinates plot showing relationships between parameters and metrics
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[500px]">
                <ParallelCoordinates 
                  results={optimization.results} 
                  maxResults={50} 
                  colorMetric={optimization.metric} 
                />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Parameter Heatmap</CardTitle>
                <CardDescription>
                  Heatmap showing the impact of two parameters on performance
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[500px]">
                <div className="flex flex-wrap gap-4 mb-4">
                  <div>
                    <label className="block mb-2 text-sm font-medium">Parameter 1</label>
                    <select
                      className="w-[150px] rounded-md border border-input px-3 py-2 text-sm"
                      value={selectedParams.param1}
                      onChange={(e) => setSelectedParams({...selectedParams, param1: e.target.value})}
                    >
                      {paramNames.map(param => (
                        <option key={param} value={param}>{param}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block mb-2 text-sm font-medium">Parameter 2</label>
                    <select
                      className="w-[150px] rounded-md border border-input px-3 py-2 text-sm"
                      value={selectedParams.param2}
                      onChange={(e) => setSelectedParams({...selectedParams, param2: e.target.value})}
                    >
                      {paramNames.map(param => (
                        <option key={param} value={param}>{param}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                {selectedParams.param1 && selectedParams.param2 ? (
                  <div className="h-[400px]">
                    <HeatmapChart 
                      optimizationId={id}
                      param1={selectedParams.param1}
                      param2={selectedParams.param2}
                      metric={optimization.metric}
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                    Select two parameters to view heatmap
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="analysis" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Parameter Importance</CardTitle>
                <CardDescription>
                  Analysis of how each parameter impacts the optimization results
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[500px]">
                <ParameterImportanceChart
                  results={optimization.results}
                  metric={optimization.metric}
                  optimizationId={id}
                />
              </CardContent>
            </Card>
            
            {optimization.method === "bayesian" && optimization.method_data?.convergence && (
              <Card>
                <CardHeader>
                  <CardTitle>Convergence Plot</CardTitle>
                  <CardDescription>
                    Shows how the optimization progressed over iterations
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[400px]">
                  <div className="text-center text-muted-foreground p-4">
                    Convergence plot visualization
                    {/* We would implement the convergence plot here */}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
} 