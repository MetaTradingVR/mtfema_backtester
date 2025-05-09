"use client";

import { useState, useEffect, useRef } from "react";
import { OptimizationResult } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

// Import dynamic Plot component from Plotly
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => <Loader2 className="h-8 w-8 animate-spin mx-auto" />,
});

interface ParallelCoordinatesProps {
  results: OptimizationResult[];
  maxResults?: number;
  colorMetric?: string;
}

export function ParallelCoordinates({ 
  results, 
  maxResults = 50,
  colorMetric = "total_return" 
}: ParallelCoordinatesProps) {
  const [filteredResults, setFilteredResults] = useState<OptimizationResult[]>([]);
  const [dimensions, setDimensions] = useState<{ label: string; values: number[] }[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>(colorMetric);
  const chartRef = useRef<HTMLDivElement>(null);

  // Process results to generate parallel coordinates data
  useEffect(() => {
    // Sort results by the selected metric (descending) and take top maxResults
    const sorted = [...results].sort((a, b) => 
      (b.metrics[selectedMetric] || 0) - (a.metrics[selectedMetric] || 0)
    ).slice(0, maxResults);
    
    setFilteredResults(sorted);
    
    // Extract parameter and metric dimensions
    if (sorted.length > 0) {
      // Get all parameter names
      const paramNames = new Set<string>();
      sorted.forEach(result => {
        Object.keys(result.params).forEach(key => paramNames.add(key));
      });
      
      // Get all metric names (except the coloring metric)
      const metricNames = new Set<string>();
      sorted.forEach(result => {
        Object.keys(result.metrics).forEach(key => {
          if (key !== selectedMetric) {
            metricNames.add(key);
          }
        });
      });
      
      // Create dimensions for parameters
      const paramDimensions = Array.from(paramNames).map(param => ({
        label: param,
        values: sorted.map(result => 
          typeof result.params[param] === 'number' 
            ? result.params[param] as number 
            : 0
        )
      }));
      
      // Create dimensions for metrics
      const metricDimensions = Array.from(metricNames).map(metric => ({
        label: metric,
        values: sorted.map(result => result.metrics[metric] || 0)
      }));
      
      // Combine dimensions (parameters first, then metrics)
      setDimensions([...paramDimensions, ...metricDimensions]);
    }
  }, [results, maxResults, selectedMetric]);

  // Generate colors based on the selected metric
  const getColors = () => {
    if (filteredResults.length === 0) return [];
    
    const values = filteredResults.map(r => r.metrics[selectedMetric] || 0);
    const min = Math.min(...values);
    const max = Math.max(...values);
    
    // Generate a color scale (blue to red)
    return values.map(val => {
      // Normalize value between 0 and 1
      const norm = max > min ? (val - min) / (max - min) : 0.5;
      
      // Calculate color - blue for low values, red for high values
      // Using a simplified color scale for demonstration
      return `rgb(${Math.round(norm * 255)}, ${Math.round((1 - Math.abs(norm - 0.5) * 2) * 100)}, ${Math.round((1 - norm) * 255)})`;
    });
  };

  if (results.length === 0) {
    return (
      <div className="flex justify-center items-center h-full text-muted-foreground">
        No optimization results available
      </div>
    );
  }

  // Plotly data
  const plotData = [{
    type: 'parcoords',
    line: {
      color: getColors(),
      colorscale: 'Jet',
      showscale: true,
      cmin: Math.min(...filteredResults.map(r => r.metrics[selectedMetric] || 0)),
      cmax: Math.max(...filteredResults.map(r => r.metrics[selectedMetric] || 0)),
      colorbar: {
        title: selectedMetric,
      }
    },
    dimensions: dimensions.map(dim => ({
      label: dim.label,
      values: dim.values,
    })),
  }];

  // Plotly layout
  const layout = {
    title: {
      text: 'Parameter Relationships',
      font: {
        family: 'Arial, sans-serif',
        size: 18
      }
    },
    autosize: true,
    height: 400,
    margin: {
      l: 80,
      r: 80,
      t: 80,
      b: 80
    }
  };

  return (
    <div className="space-y-4 w-full h-full">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-sm">Color by:</span>
          <Select value={selectedMetric} onValueChange={setSelectedMetric}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select metric" />
            </SelectTrigger>
            <SelectContent>
              {Object.keys(filteredResults[0]?.metrics || {}).map(metric => (
                <SelectItem key={metric} value={metric}>
                  {metric.replace('_', ' ')}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <span className="text-xs text-muted-foreground">
          Showing top {filteredResults.length} results
        </span>
      </div>
      
      <div ref={chartRef} className="w-full h-[400px]">
        <Plot
          data={plotData}
          layout={layout}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
} 