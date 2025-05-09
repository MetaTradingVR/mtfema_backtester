"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, RefreshCw, Download } from "lucide-react";
import { HeatmapChart } from "./heatmap-chart";
import { ParallelCoordinates } from "./parallel-coordinates";
import { ParameterImportance } from "./parameter-importance";
import { DataTable } from "@/components/data-table";
import { 
  fetchOptimizationResults, 
  fetchOptimizationMetrics, 
  fetchParameterImportance,
  fetchHeatmapData,
  fetchParallelCoordinatesData 
} from "@/lib/api";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  Legend,
  ScatterChart,
  Scatter,
  ZAxis
} from "recharts";

interface OptimizationResultsProps {
  optimizationId: string;
  onBack: () => void;
}

export function OptimizationResults({ optimizationId, onBack }: OptimizationResultsProps) {
  const [results, setResults] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>("");
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [parallelData, setParallelData] = useState<any>(null);
  const [parameterImportance, setParameterImportance] = useState<any>(null);
  const [isLoading, setIsLoading] = useState({
    results: true,
    metrics: true,
    heatmap: true,
    parallel: true,
    importance: true
  });
  const [errors, setErrors] = useState<Record<string, string | null>>({
    results: null,
    metrics: null,
    heatmap: null,
    parallel: null,
    importance: null
  });
  
  // Load optimization metrics
  useEffect(() => {
    async function loadMetrics() {
      try {
        setIsLoading(prev => ({ ...prev, metrics: true }));
        const data = await fetchOptimizationMetrics(optimizationId);
        setMetrics(data.metrics || []);
        
        // Set default selected metric
        if (data.metrics && data.metrics.length > 0) {
          const preferredMetrics = ["total_return", "sharpe_ratio", "profit_factor"];
          const defaultMetric = preferredMetrics.find(m => data.metrics.includes(m)) || data.metrics[0];
          setSelectedMetric(defaultMetric);
        }
      } catch (error) {
        console.error("Failed to load metrics:", error);
        setErrors(prev => ({ ...prev, metrics: "Failed to load available metrics" }));
      } finally {
        setIsLoading(prev => ({ ...prev, metrics: false }));
      }
    }
    
    loadMetrics();
  }, [optimizationId]);
  
  // Load optimization results
  useEffect(() => {
    async function loadResults() {
      try {
        setIsLoading(prev => ({ ...prev, results: true }));
        const data = await fetchOptimizationResults(optimizationId);
        setResults(data.results || []);
      } catch (error) {
        console.error("Failed to load results:", error);
        setErrors(prev => ({ ...prev, results: "Failed to load optimization results" }));
      } finally {
        setIsLoading(prev => ({ ...prev, results: false }));
      }
    }
    
    loadResults();
  }, [optimizationId]);
  
  // Load parameter importance data when metric is selected
  useEffect(() => {
    async function loadParameterImportance() {
      if (!selectedMetric) return;
      
      try {
        setIsLoading(prev => ({ ...prev, importance: true }));
        const data = await fetchParameterImportance(optimizationId, selectedMetric);
        setParameterImportance(data);
      } catch (error) {
        console.error("Failed to load parameter importance:", error);
        setErrors(prev => ({ ...prev, importance: "Failed to load parameter importance data" }));
      } finally {
        setIsLoading(prev => ({ ...prev, importance: false }));
      }
    }
    
    loadParameterImportance();
  }, [optimizationId, selectedMetric]);
  
  // Load heatmap data when metric is selected
  useEffect(() => {
    async function loadHeatmapData() {
      if (!selectedMetric) return;
      
      try {
        setIsLoading(prev => ({ ...prev, heatmap: true }));
        const data = await fetchHeatmapData(optimizationId, selectedMetric);
        setHeatmapData(data);
      } catch (error) {
        console.error("Failed to load heatmap data:", error);
        setErrors(prev => ({ ...prev, heatmap: "Failed to load heatmap visualization data" }));
      } finally {
        setIsLoading(prev => ({ ...prev, heatmap: false }));
      }
    }
    
    loadHeatmapData();
  }, [optimizationId, selectedMetric]);
  
  // Load parallel coordinates data when metric is selected
  useEffect(() => {
    async function loadParallelData() {
      if (!selectedMetric) return;
      
      try {
        setIsLoading(prev => ({ ...prev, parallel: true }));
        const data = await fetchParallelCoordinatesData(optimizationId, selectedMetric);
        setParallelData(data);
      } catch (error) {
        console.error("Failed to load parallel coordinates data:", error);
        setErrors(prev => ({ ...prev, parallel: "Failed to load parallel coordinates data" }));
      } finally {
        setIsLoading(prev => ({ ...prev, parallel: false }));
      }
    }
    
    loadParallelData();
  }, [optimizationId, selectedMetric]);
  
  // Handle metric change
  const handleMetricChange = (metric: string) => {
    setSelectedMetric(metric);
  };

  // Export results as CSV
  const exportResultsCSV = () => {
    if (!results || results.length === 0) return;
    
    // Get all possible headers from the results
    const headers = Array.from(
      new Set(
        results.flatMap(result => Object.keys(result))
      )
    );
    
    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...results.map(result => 
        headers.map(header => {
          const value = result[header];
          // Handle numbers, strings, null and undefined
          if (value === null || value === undefined) return '';
          if (typeof value === 'number') return value;
          return `"${String(value).replace(/"/g, '""')}"`;
        }).join(',')
      )
    ].join('\n');
    
    // Create and download the file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `optimization-results-${optimizationId}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Get best set of parameters based on selected metric
  const getBestParameters = () => {
    if (!results || results.length === 0 || !selectedMetric) return null;
    
    // Sort by metric value (assuming higher is better)
    const sortedResults = [...results].sort((a, b) => {
      const aValue = a[selectedMetric] || 0;
      const bValue = b[selectedMetric] || 0;
      return bValue - aValue;
    });
    
    return sortedResults[0];
  };
  
  const bestParameters = getBestParameters();
  
  // Format parameter value for display
  const formatParamValue = (value: any) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      return Number.isInteger(value) ? value.toString() : value.toFixed(2);
    }
    return value.toString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={onBack}>
          ← Back to Optimizer
        </Button>
        
        <div className="flex items-center space-x-2">
          {metrics.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">Optimization Metric:</span>
              <select
                className="h-8 rounded-md border border-input bg-background px-3 py-1 text-sm"
                value={selectedMetric}
                onChange={(e) => handleMetricChange(e.target.value)}
              >
                {metrics.map((metric) => (
                  <option key={metric} value={metric}>
                    {metric.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>
          )}
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={exportResultsCSV}
            disabled={!results || results.length === 0}
          >
            <Download className="h-4 w-4 mr-1" />
            Export Results
          </Button>
        </div>
      </div>
      
      {/* Best Parameters Card */}
      <Card>
        <CardHeader>
          <CardTitle>Best Parameters</CardTitle>
          <CardDescription>
            Optimal parameter values based on {selectedMetric ? selectedMetric.replace(/_/g, ' ') : 'selected metric'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading.results ? (
            <div className="space-y-2">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-6 w-3/5" />
              <Skeleton className="h-6 w-2/3" />
            </div>
          ) : errors.results ? (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{errors.results}</AlertDescription>
            </Alert>
          ) : bestParameters ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Best Result Metrics */}
              <div className="col-span-1 space-y-2">
                <h3 className="text-lg font-medium">Performance</h3>
                <div className="space-y-1.5">
                  {Object.entries(bestParameters)
                    .filter(([key]) => !key.includes('_min') && !key.includes('_max') && !key.includes('_step'))
                    .filter(([key]) => !['id', 'timestamp', 'optimization_id', 'params'].includes(key))
                    .slice(0, 5)
                    .map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm text-muted-foreground">{key.replace(/_/g, ' ')}:</span>
                        <span className="text-sm font-medium">
                          {typeof value === 'number' ? 
                            Number.isInteger(value) ? value : value.toFixed(2) 
                            : value}
                        </span>
                      </div>
                    ))
                  }
                </div>
              </div>
              
              {/* Parameter Values */}
              <div className="col-span-2 space-y-2">
                <h3 className="text-lg font-medium">Parameter Values</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(bestParameters.params || {}).map(([key, value]) => (
                    <div key={key} className="p-3 bg-muted rounded-md">
                      <div className="text-xs text-muted-foreground mb-1">{key.replace(/_/g, ' ')}</div>
                      <div className="font-medium">{formatParamValue(value)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              No optimization results available
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Visualization Tabs */}
      <Tabs defaultValue="heatmap" className="space-y-4">
        <TabsList className="grid grid-cols-3 md:w-[400px]">
          <TabsTrigger value="heatmap">Parameter Heatmap</TabsTrigger>
          <TabsTrigger value="parallel">Parallel Coords</TabsTrigger>
          <TabsTrigger value="importance">Parameter Impact</TabsTrigger>
        </TabsList>
        
        <TabsContent value="heatmap" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parameter Heatmap</CardTitle>
              <CardDescription>
                Visualize how combinations of parameters affect {selectedMetric ? selectedMetric.replace(/_/g, ' ') : 'performance'}
              </CardDescription>
            </CardHeader>
            <CardContent className="min-h-[400px]">
              {isLoading.heatmap ? (
                <div className="flex items-center justify-center h-[400px]">
                  <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : errors.heatmap ? (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{errors.heatmap}</AlertDescription>
                </Alert>
              ) : heatmapData ? (
                <div className="h-[500px]">
                  <HeatmapChart 
                    xAxisParameter={heatmapData.x_param}
                    yAxisParameter={heatmapData.y_param}
                    xValues={heatmapData.x_values}
                    yValues={heatmapData.y_values}
                    zValues={heatmapData.z_values}
                    metric={selectedMetric}
                  />
                </div>
              ) : (
                <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                  No heatmap data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="parallel" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parallel Coordinates Plot</CardTitle>
              <CardDescription>
                See relationships between multiple parameters and {selectedMetric ? selectedMetric.replace(/_/g, ' ') : 'performance'}
              </CardDescription>
            </CardHeader>
            <CardContent className="min-h-[400px]">
              {isLoading.parallel ? (
                <div className="flex items-center justify-center h-[400px]">
                  <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : errors.parallel ? (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{errors.parallel}</AlertDescription>
                </Alert>
              ) : parallelData ? (
                <div className="h-[500px]">
                  <ParallelCoordinates 
                    data={parallelData.data} 
                    dimensions={parallelData.dimensions}
                    colorScale={parallelData.color_scale}
                    metric={selectedMetric}
                  />
                </div>
              ) : (
                <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                  No parallel coordinates data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="importance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parameter Importance Analysis</CardTitle>
              <CardDescription>
                Understand which parameters have the most impact on {selectedMetric ? selectedMetric.replace(/_/g, ' ') : 'performance'}
              </CardDescription>
            </CardHeader>
            <CardContent className="min-h-[400px]">
              {isLoading.importance ? (
                <div className="flex items-center justify-center h-[400px]">
                  <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : errors.importance ? (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{errors.importance}</AlertDescription>
                </Alert>
              ) : parameterImportance ? (
                <div className="space-y-6">
                  <ParameterImportance 
                    data={parameterImportance.importance_scores} 
                    metric={selectedMetric}
                  />
                  
                  {/* Parameter Distribution Scatter Plots */}
                  <div className="mt-8 pt-4 border-t">
                    <h3 className="text-lg font-medium mb-4">Parameter Performance Distribution</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {parameterImportance.scatter_data && 
                        Object.entries(parameterImportance.scatter_data).map(([param, data]: [string, any]) => (
                          <div key={param} className="bg-muted/50 rounded-lg p-4">
                            <h4 className="text-sm font-medium mb-2">{param.replace(/_/g, ' ')}</h4>
                            <ResponsiveContainer width="100%" height={200}>
                              <ScatterChart
                                margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                  type="number" 
                                  dataKey="value" 
                                  name={param} 
                                  tick={{ fontSize: 12 }}
                                  label={{ 
                                    value: param.replace(/_/g, ' '), 
                                    position: 'bottom', 
                                    fontSize: 12 
                                  }}
                                />
                                <YAxis 
                                  type="number" 
                                  dataKey="performance" 
                                  name={selectedMetric} 
                                  tick={{ fontSize: 12 }}
                                  label={{ 
                                    value: selectedMetric.replace(/_/g, ' '), 
                                    angle: -90, 
                                    position: 'left', 
                                    fontSize: 12
                                  }}
                                />
                                <ZAxis type="number" range={[50, 200]} />
                                <RechartsTooltip 
                                  cursor={{ strokeDasharray: '3 3' }} 
                                  formatter={(value: any, name: any) => {
                                    if (name === 'performance') {
                                      return [
                                        typeof value === 'number' ? value.toFixed(2) : value,
                                        selectedMetric.replace(/_/g, ' ')
                                      ];
                                    }
                                    return [value, name.replace(/_/g, ' ')];
                                  }}
                                />
                                <Scatter 
                                  name={param} 
                                  data={data} 
                                  fill="#8884d8" 
                                />
                              </ScatterChart>
                            </ResponsiveContainer>
                          </div>
                        ))
                      }
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                  No parameter importance data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Optimization Results</CardTitle>
          <CardDescription>
            Complete list of all parameter combinations and their performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading.results ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : errors.results ? (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{errors.results}</AlertDescription>
            </Alert>
          ) : results && results.length > 0 ? (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2 font-medium">Rank</th>
                      {Object.keys(results[0].params || {}).map((key) => (
                        <th key={key} className="text-left p-2 font-medium">
                          {key.replace(/_/g, ' ')}
                        </th>
                      ))}
                      {Object.keys(results[0])
                        .filter(key => !key.includes('_min') && !key.includes('_max') && !key.includes('_step'))
                        .filter(key => !['id', 'timestamp', 'optimization_id', 'params'].includes(key))
                        .slice(0, 4)
                        .map((key) => (
                          <th key={key} className="text-left p-2 font-medium">
                            {key.replace(/_/g, ' ')}
                          </th>
                        ))
                      }
                    </tr>
                  </thead>
                  <tbody>
                    {[...results]
                      .sort((a, b) => (b[selectedMetric] || 0) - (a[selectedMetric] || 0))
                      .slice(0, 50)
                      .map((result, index) => (
                        <tr key={index} className="border-b hover:bg-muted/50">
                          <td className="p-2">{index + 1}</td>
                          {Object.values(result.params || {}).map((value: any, i) => (
                            <td key={i} className="p-2">
                              {formatParamValue(value)}
                            </td>
                          ))}
                          {Object.keys(result)
                            .filter(key => !key.includes('_min') && !key.includes('_max') && !key.includes('_step'))
                            .filter(key => !['id', 'timestamp', 'optimization_id', 'params'].includes(key))
                            .slice(0, 4)
                            .map((key) => (
                              <td key={key} className="p-2">
                                {typeof result[key] === 'number' 
                                  ? Number.isInteger(result[key]) ? result[key] : result[key].toFixed(2)
                                  : result[key]}
                              </td>
                            ))
                          }
                        </tr>
                      ))
                    }
                  </tbody>
                </table>
              </div>
              {results.length > 50 && (
                <div className="text-sm text-muted-foreground text-center">
                  Showing top 50 of {results.length} results
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              No optimization results available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
