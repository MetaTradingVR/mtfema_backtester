import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Dynamically import Plot from react-plotly.js
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false, // Disable server-side rendering
});

interface ParameterHeatmapProps {
  data: any; // Will be replaced with proper type later
  paramX: string;
  paramY: string;
  metric: string;
  title: string;
  className?: string;
}

export function ParameterHeatmap({ data, paramX, paramY, metric, title, className }: ParameterHeatmapProps) {
  const [plotData, setPlotData] = useState<any[]>([]);
  const [plotLayout, setPlotLayout] = useState<any>({});

  // Helper function to determine text color based on background intensity
  function getContrastColor(value: number, zValues: number[][]) {
    const allValues = zValues.flat().filter(v => v !== null) as number[];
    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    
    // Normalize the value between 0 and 1
    const normalized = (value - min) / (max - min);
    
    // Use white text for darker backgrounds, black for lighter ones
    return normalized > 0.6 ? 'white' : 'black';
  }

  // Generate sample data for demo purposes
  const generateSampleData = () => {
    const sampleData = [];
    const emaPeriods = [7, 9, 11, 13, 15];
    const thresholds = [0.5, 0.75, 1.0, 1.25, 1.5];
    
    for (const period of emaPeriods) {
      for (const threshold of thresholds) {
        // Generate a random return value that tends to be better for certain combinations
        const baseReturn = 15 - Math.abs(period - 9) * 2 - Math.abs(threshold - 1.0) * 10;
        const randomFactor = Math.random() * 10 - 5;
        
        sampleData.push({
          ema_period: period,
          extension_threshold: threshold,
          total_return: baseReturn + randomFactor,
          win_rate: 50 + Math.random() * 20,
          sharpe_ratio: 1 + Math.random()
        });
      }
    }
    
    return sampleData;
  };

  useEffect(() => {
    if (data && data.length > 0) {
      // Extract unique values for x and y axes
      const xValues = [...new Set(data.map((item: any) => item[paramX]))].sort();
      const yValues = [...new Set(data.map((item: any) => item[paramY]))].sort();
      
      // Create a 2D array for z values (initialized with nulls)
      const zValues: (number | null)[][] = Array(yValues.length)
        .fill(null)
        .map(() => Array(xValues.length).fill(null));

      // Populate z values based on the data
      for (const item of data) {
        const xIndex = xValues.indexOf(item[paramX]);
        const yIndex = yValues.indexOf(item[paramY]);
        if (xIndex !== -1 && yIndex !== -1) {
          zValues[yIndex][xIndex] = item[metric];
        }
      }

      // Create annotations for displaying values in cells
      const annotations: any[] = [];
      for (let i = 0; i < yValues.length; i++) {
        for (let j = 0; j < xValues.length; j++) {
          const value = zValues[i][j];
          if (value !== null && value !== undefined) {
            const text = `${typeof value === 'number' ? value.toFixed(2) : value}`;
            annotations.push({
              x: xValues[j],
              y: yValues[i],
              text,
              font: {
                color: getContrastColor(value, zValues as any)
              },
              showarrow: false
            });
          }
        }
      }

      // Create the heatmap trace
      const trace = {
        x: xValues,
        y: yValues,
        z: zValues,
        type: 'heatmap',
        colorscale: 'RdYlGn',
        showscale: true,
        colorbar: {
          title: metric,
          thickness: 20,
          len: 0.75
        }
      };

      // Set the plot data and layout
      setPlotData([trace]);
      setPlotLayout({
        title: {
          text: `${title}: ${metric}`
        },
        xaxis: {
          title: {
            text: paramX
          },
          type: 'category'
        },
        yaxis: {
          title: {
            text: paramY
          },
          type: 'category'
        },
        annotations: annotations,
        margin: { l: 60, r: 50, b: 50, t: 80 },
        height: 500,
        autosize: true
      });
    } else {
      // Use sample data if no data is provided
      const sampleData = generateSampleData();
      
      // Process the data to extract unique values for x and y axes
      const xValues = [...new Set(sampleData.map(item => item.ema_period))].sort((a, b) => a - b);
      const yValues = [...new Set(sampleData.map(item => item.extension_threshold))].sort((a, b) => a - b);

      // Create a 2D array for z values (initialized with nulls)
      const zValues: (number | null)[][] = Array(yValues.length)
        .fill(null)
        .map(() => Array(xValues.length).fill(null));

      // Populate z values based on the data
      for (const item of sampleData) {
        const xIndex = xValues.indexOf(item.ema_period);
        const yIndex = yValues.indexOf(item.extension_threshold);
        if (xIndex !== -1 && yIndex !== -1) {
          zValues[yIndex][xIndex] = item.total_return;
        }
      }

      // Create annotations for displaying values in cells
      const annotations: any[] = [];
      for (let i = 0; i < yValues.length; i++) {
        for (let j = 0; j < xValues.length; j++) {
          const value = zValues[i][j];
          if (value !== null) {
            const text = `${value.toFixed(2)}%`;
            annotations.push({
              x: xValues[j],
              y: yValues[i],
              text,
              font: {
                color: getContrastColor(value, zValues as any)
              },
              showarrow: false
            });
          }
        }
      }

      // Create the heatmap trace
      const trace = {
        x: xValues,
        y: yValues,
        z: zValues,
        type: 'heatmap',
        colorscale: 'RdYlGn',
        showscale: true,
        colorbar: {
          title: 'Total Return (%)',
          thickness: 20,
          len: 0.75
        }
      };

      // Set the plot data and layout
      setPlotData([trace]);
      setPlotLayout({
        title: {
          text: 'Parameter Optimization: Total Return (Sample Data)'
        },
        xaxis: {
          title: {
            text: 'EMA Period'
          },
          type: 'category'
        },
        yaxis: {
          title: {
            text: 'Extension Threshold'
          },
          type: 'category'
        },
        annotations: annotations,
        margin: { l: 60, r: 50, b: 50, t: 80 },
        height: 500,
        autosize: true
      });
    }
  }, [data, paramX, paramY, metric, title]);

  return (
    <Card className={`w-full h-full ${className || ''}`}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Exploring the impact of different parameter values</CardDescription>
      </CardHeader>
      <CardContent>
        {plotData.length > 0 ? (
          <Plot
            data={plotData}
            layout={plotLayout}
            config={{ responsive: true }}
            className="w-full h-[500px]"
          />
        ) : (
          <div className="w-full h-[500px] flex items-center justify-center">Processing data...</div>
        )}
      </CardContent>
    </Card>
  );
}
