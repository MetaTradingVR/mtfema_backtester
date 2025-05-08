import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Dynamically import Plot from react-plotly.js
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false, // Disable server-side rendering
  loading: () => <div className="w-full h-[500px] flex items-center justify-center">Loading visualization...</div>
});

interface ParameterImpactProps {
  data: any; // Array of optimization results
  parameters: string[]; // List of parameter names to analyze
  metric: string; // Metric to evaluate (e.g., 'total_return', 'sharpe_ratio')
  title?: string;
  className?: string;
}

export function ParameterImpact({ 
  data, 
  parameters,
  metric, 
  title = "Parameter Impact Analysis", 
  className 
}: ParameterImpactProps) {
  const [plotData, setPlotData] = useState<any[]>([]);
  const [plotLayout, setPlotLayout] = useState<any>({});

  useEffect(() => {
    if (data && data.length > 0 && parameters.length > 0) {
      // Create a plot for each parameter
      const plots = parameters.map(param => {
        // Group data by parameter values
        const paramValues = [...new Set(data.map((item: any) => item[param]))].sort((a, b) => 
          typeof a === 'number' ? a - b : String(a).localeCompare(String(b))
        );
        
        // Calculate average metric value for each parameter value
        const metricValues = paramValues.map(value => {
          const matchingItems = data.filter((item: any) => item[param] === value);
          const sum = matchingItems.reduce((acc: number, item: any) => acc + item[metric], 0);
          return sum / matchingItems.length;
        });
        
        // Create bar chart
        return {
          x: paramValues,
          y: metricValues,
          type: 'bar',
          name: param,
          hovertemplate: `${param}: %{x}<br>${metric}: %{y:.2f}<extra></extra>`
        };
      });

      setPlotData(plots);
      setPlotLayout({
        title: {
          text: `${title}: ${metric}`
        },
        grid: {
          rows: Math.ceil(parameters.length / 2),
          columns: Math.min(parameters.length, 2),
          pattern: 'independent'
        },
        showlegend: false,
        margin: { l: 50, r: 50, b: 70, t: 80 },
        height: Math.max(300, 250 * Math.ceil(parameters.length / 2)),
        autosize: true
      });
    } else {
      // Generate sample data if none provided
      const sampleData = generateSampleData();
      const sampleParams = ['ema_period', 'extension_threshold', 'profit_target', 'stop_loss'];
      
      // Create a plot for each parameter
      const plots = sampleParams.map(param => {
        // Group data by parameter values
        const paramValues = [...new Set(sampleData.map(item => item[param]))].sort((a, b) => a - b);
        
        // Calculate average metric value for each parameter value
        const metricValues = paramValues.map(value => {
          const matchingItems = sampleData.filter(item => item[param] === value);
          const sum = matchingItems.reduce((acc, item) => acc + item.total_return, 0);
          return sum / matchingItems.length;
        });
        
        // Create bar chart
        return {
          x: paramValues,
          y: metricValues,
          type: 'bar',
          name: param,
          hovertemplate: `${param}: %{x}<br>Return: %{y:.2f}%<extra></extra>`
        };
      });

      setPlotData(plots);
      setPlotLayout({
        title: {
          text: 'Parameter Impact Analysis: Total Return (Sample Data)'
        },
        grid: {
          rows: 2,
          columns: 2,
          pattern: 'independent'
        },
        showlegend: false,
        margin: { l: 50, r: 50, b: 70, t: 80 },
        height: 600,
        autosize: true
      });
    }
  }, [data, parameters, metric, title]);

  // Function to generate sample data for demonstration
  const generateSampleData = () => {
    const sampleData = [];
    const emaPeriods = [7, 9, 11, 13, 15];
    const thresholds = [0.5, 0.75, 1.0, 1.25, 1.5];
    const profitTargets = [1.5, 2.0, 2.5, 3.0];
    const stopLosses = [0.5, 1.0, 1.5, 2.0];
    
    // Generate data with some realistic patterns
    for (const ema of emaPeriods) {
      for (const threshold of thresholds) {
        for (const target of profitTargets) {
          for (const stop of stopLosses) {
            // Base performance is affected by each parameter
            let baseReturn = 15;
            
            // EMA period effect (9 is optimal)
            baseReturn -= Math.abs(ema - 9) * 1.5;
            
            // Threshold effect (1.0 is optimal)
            baseReturn -= Math.abs(threshold - 1.0) * 8;
            
            // Profit target effect (higher is better, but diminishing returns)
            baseReturn += Math.log(target) * 5;
            
            // Stop loss effect (tighter stops are better)
            baseReturn -= stop * 2;
            
            // Add some randomness
            const finalReturn = baseReturn + (Math.random() * 10 - 5);
            
            sampleData.push({
              ema_period: ema,
              extension_threshold: threshold,
              profit_target: target,
              stop_loss: stop,
              total_return: Math.max(0, Number(finalReturn.toFixed(2)))
            });
          }
        }
      }
    }
    
    return sampleData;
  };

  return (
    <Card className={`w-full h-full ${className || ''}`}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Analyzing how individual parameters affect trading performance</CardDescription>
      </CardHeader>
      <CardContent>
        {plotData.length > 0 ? (
          <Plot
            data={plotData}
            layout={plotLayout}
            config={{ responsive: true }}
            className="w-full"
          />
        ) : (
          <div className="w-full h-[500px] flex items-center justify-center">Processing data...</div>
        )}
      </CardContent>
    </Card>
  );
}
