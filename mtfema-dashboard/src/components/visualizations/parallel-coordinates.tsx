import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Dynamically import Plot from react-plotly.js
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false, // Disable server-side rendering
  loading: () => <div className="w-full h-[500px] flex items-center justify-center">Loading visualization...</div>
});

interface ParallelCoordinatesProps {
  data: any; // Array of optimization results
  parameters: string[]; // List of parameter names to include
  colorMetric: string; // Metric to use for coloring (e.g., 'total_return')
  title?: string;
  className?: string;
}

export function ParallelCoordinates({
  data,
  parameters,
  colorMetric,
  title = "Parameter Relationships",
  className
}: ParallelCoordinatesProps) {
  const [plotData, setPlotData] = useState<any[]>([]);
  const [plotLayout, setPlotLayout] = useState<any>({});

  useEffect(() => {
    if (data && data.length > 0 && parameters.length > 0) {
      // Prepare data for parallel coordinates
      // Extract all parameter values and the color metric
      const dimensions = parameters.map(param => {
        const values = data.map((item: any) => item[param] || 0); // Use 0 as fallback for null/undefined
        const filteredValues = values.filter((val: any) => val !== null && val !== undefined);
        const min = filteredValues.length > 0 ? Math.min(...filteredValues) : 0;
        const max = filteredValues.length > 0 ? Math.max(...filteredValues) : 1;
        return {
          label: param,
          values,
          range: [min, max]
        };
      });

      // Extract color metric values
      const colorValues = data.map((item: any) => {
        const value = item[colorMetric];
        return value !== null && value !== undefined ? value : 0;
      });
      
      // Create the parallel coordinates trace
      const trace = {
        type: 'parcoords',
        line: {
          color: colorValues,
          colorscale: 'Jet',
          showscale: true,
          colorbar: {
            title: colorMetric,
            thickness: 20,
            len: 0.75
          }
        },
        dimensions
      };

      setPlotData([trace]);
      setPlotLayout({
        title: {
          text: title
        },
        margin: { l: 80, r: 80, b: 50, t: 80 },
        height: 500,
        autosize: true
      });
    } else {
      // Generate sample data if none provided
      const sampleData = generateSampleData();
      const sampleParams = ['ema_period', 'extension_threshold', 'profit_target', 'stop_loss'];
      
      // Prepare data for parallel coordinates
      const dimensions = sampleParams.map(param => {
        const values = sampleData.map(item => item[param]);
        return {
          label: param,
          values,
          range: [Math.min(...values), Math.max(...values)]
        };
      });

      // Extract color metric values
      const colorValues = sampleData.map(item => item.total_return);
      
      // Create the parallel coordinates trace
      const trace = {
        type: 'parcoords',
        line: {
          color: colorValues,
          colorscale: 'Jet',
          showscale: true,
          colorbar: {
            title: 'Total Return (%)',
            thickness: 20,
            len: 0.75
          }
        },
        dimensions
      };

      setPlotData([trace]);
      setPlotLayout({
        title: {
          text: 'Parameter Relationships (Sample Data)'
        },
        margin: { l: 80, r: 80, b: 50, t: 80 },
        height: 500,
        autosize: true
      });
    }
  }, [data, parameters, colorMetric, title]);

  // Function to generate sample data for demonstration
  const generateSampleData = () => {
    const sampleData = [];
    const emaPeriods = [7, 9, 11, 13, 15];
    const thresholds = [0.5, 0.75, 1.0, 1.25, 1.5];
    const profitTargets = [1.5, 2.0, 2.5, 3.0];
    const stopLosses = [0.5, 1.0, 1.5, 2.0];
    
    // Generate some sample configurations with performance metrics
    for (let i = 0; i < 50; i++) {
      // Pick random parameter values
      const ema = emaPeriods[Math.floor(Math.random() * emaPeriods.length)];
      const threshold = thresholds[Math.floor(Math.random() * thresholds.length)];
      const target = profitTargets[Math.floor(Math.random() * profitTargets.length)];
      const stop = stopLosses[Math.floor(Math.random() * stopLosses.length)];
      
      // Calculate a total return based on parameter choices (with some patterns)
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
    
    return sampleData;
  };

  return (
    <Card className={`w-full h-full ${className || ''}`}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Visualizing relationships between multiple parameters</CardDescription>
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
