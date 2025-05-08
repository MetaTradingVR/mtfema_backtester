"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import dynamic from "next/dynamic";

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface EquityCurveProps {
  equityCurve: { date: string; equity: number }[];
  title?: string;
  benchmark?: { date: string; value: number }[];
}

export function EquityCurve({ 
  equityCurve, 
  benchmark, 
  title = "Equity Curve" 
}: EquityCurveProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState<"all" | "3m" | "6m" | "1y">("all");

  // Skip if no data
  if (!equityCurve || equityCurve.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center">
          <p className="text-muted-foreground">No equity data available</p>
        </CardContent>
      </Card>
    );
  }

  // Apply timeframe filter
  const filteredData = filterByTimeframe(equityCurve, selectedTimeframe);
  
  // Calculate percentage change from start
  const normalizedData = normalizeData(filteredData);
  
  // Prepare benchmark data if available
  const normalizedBenchmark = benchmark 
    ? normalizeData(filterByTimeframe(benchmark, selectedTimeframe)) 
    : null;

  const plotData: any[] = [
    {
      x: normalizedData.map((d) => d.date),
      y: normalizedData.map((d) => d.value),
      type: "scatter",
      mode: "lines",
      name: "Strategy",
      line: { color: "#4CAF50", width: 2 }
    }
  ];

  // Add benchmark if available
  if (normalizedBenchmark && normalizedBenchmark.length > 0) {
    plotData.push({
      x: normalizedBenchmark.map((d) => d.date),
      y: normalizedBenchmark.map((d) => d.value),
      type: "scatter",
      mode: "lines",
      name: "Benchmark",
      line: { color: "#2196F3", width: 2, dash: "dash" }
    });
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>{title}</CardTitle>
        <div className="flex gap-1">
          <button
            onClick={() => setSelectedTimeframe("all")}
            className={`px-2 py-1 text-xs rounded ${
              selectedTimeframe === "all" ? "bg-primary text-primary-foreground" : "bg-secondary"
            }`}
          >
            All
          </button>
          <button
            onClick={() => setSelectedTimeframe("1y")}
            className={`px-2 py-1 text-xs rounded ${
              selectedTimeframe === "1y" ? "bg-primary text-primary-foreground" : "bg-secondary"
            }`}
          >
            1Y
          </button>
          <button
            onClick={() => setSelectedTimeframe("6m")}
            className={`px-2 py-1 text-xs rounded ${
              selectedTimeframe === "6m" ? "bg-primary text-primary-foreground" : "bg-secondary"
            }`}
          >
            6M
          </button>
          <button
            onClick={() => setSelectedTimeframe("3m")}
            className={`px-2 py-1 text-xs rounded ${
              selectedTimeframe === "3m" ? "bg-primary text-primary-foreground" : "bg-secondary"
            }`}
          >
            3M
          </button>
        </div>
      </CardHeader>
      <CardContent className="h-[300px] pt-4">
        <Plot
          data={plotData}
          layout={{
            autosize: true,
            margin: { l: 50, r: 50, t: 30, b: 40 },
            yaxis: {
              title: { text: "% Change" },
              tickformat: "+.1%",
              hoverformat: "+.2%",
              showgrid: true,
              zeroline: true,
              zerolinecolor: "#666",
              zerolinewidth: 1
            },
            xaxis: {
              showgrid: true
            },
            showlegend: true,
            legend: { orientation: "h", y: 1.1 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)"
          }}
          config={{
            responsive: true,
            displayModeBar: false
          }}
          style={{ width: "100%", height: "100%" }}
        />
      </CardContent>
    </Card>
  );
}

interface NormalizedPoint {
  date: string;
  value: number;
}

function normalizeData(
  data: { date: string; equity?: number; value?: number }[]
): NormalizedPoint[] {
  if (data.length === 0) return [];

  const startValue = data[0].equity ?? data[0].value ?? 0;
  if (startValue === 0) return [];

  return data.map(point => {
    const currentValue = point.equity ?? point.value ?? 0;
    return {
      date: point.date,
      value: (currentValue / startValue) - 1 // Convert to percentage change
    };
  });
}

function filterByTimeframe(
  data: { date: string; equity?: number; value?: number }[],
  timeframe: "all" | "3m" | "6m" | "1y"
): typeof data {
  if (timeframe === "all" || data.length === 0) {
    return data;
  }

  const now = new Date();
  const cutoffDate = new Date();
  
  switch (timeframe) {
    case "3m":
      cutoffDate.setMonth(now.getMonth() - 3);
      break;
    case "6m":
      cutoffDate.setMonth(now.getMonth() - 6);
      break;
    case "1y":
      cutoffDate.setFullYear(now.getFullYear() - 1);
      break;
  }

  return data.filter(point => new Date(point.date) >= cutoffDate);
} 