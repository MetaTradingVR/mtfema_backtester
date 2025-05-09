"use client";

import { useState, useEffect } from "react";
import { fetchParameterHeatmap } from "@/lib/api";
import { Loader2 } from "lucide-react";

// Import dynamic Plot component from Plotly
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => <Loader2 className="h-8 w-8 animate-spin mx-auto" />,
});

interface HeatmapChartProps {
  optimizationId: string;
  param1: string;
  param2: string;
  metric: string;
}

export function HeatmapChart({ optimizationId, param1, param2, metric }: HeatmapChartProps) {
  const [heatmapData, setHeatmapData] = useState<{
    x_values: number[];
    y_values: number[];
    z_values: number[][];
    x_label: string;
    y_label: string;
    metric: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHeatmapData() {
      if (!param1 || !param2) return;
      
      try {
        setLoading(true);
        const data = await fetchParameterHeatmap(optimizationId, param1, param2, metric);
        if (data) {
          setHeatmapData(data);
          setError(null);
        } else {
          setError("Failed to load heatmap data");
        }
      } catch (err) {
        console.error("Error loading heatmap data:", err);
        setError("Error loading heatmap data");
      } finally {
        setLoading(false);
      }
    }

    loadHeatmapData();
  }, [optimizationId, param1, param2, metric]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !heatmapData) {
    return (
      <div className="flex justify-center items-center h-full text-destructive">
        {error || "No data available"}
      </div>
    );
  }

  const { x_values, y_values, z_values, x_label, y_label } = heatmapData;

  // Create data for heatmap plot
  const plotData = [
    {
      type: "heatmap" as const, // Type assertion to make TypeScript happy with Plotly
      z: z_values,
      x: x_values,
      y: y_values,
      colorscale: 'Jet',
      colorbar: {
        title: metric,
        titleside: 'right' as const,
      },
    },
  ];

  // Create layout for heatmap plot
  const layout = {
    title: {
      text: `Impact of ${x_label} and ${y_label} on ${metric}`,
      font: {
        family: 'Arial, sans-serif',
        size: 16,
      },
    },
    xaxis: {
      title: x_label,
      tickfont: {
        family: 'Arial, sans-serif',
        size: 12,
      },
    },
    yaxis: {
      title: y_label,
      tickfont: {
        family: 'Arial, sans-serif',
        size: 12,
      },
    },
    margin: {
      l: 70,
      r: 50,
      t: 80,
      b: 70,
    },
    autosize: true,
  };

  return (
    <Plot
      data={plotData}
      layout={layout}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%", height: "100%" }}
    />
  );
} 