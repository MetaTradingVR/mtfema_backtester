"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import dynamic from "next/dynamic";

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface DrawdownPoint {
  date: string;
  equity: number;
  drawdown_pct: number;
}

interface DrawdownAnalysisProps {
  equityCurve: { date: string; equity: number }[];
  title?: string;
}

export function DrawdownAnalysis({ equityCurve, title = "Drawdown Analysis" }: DrawdownAnalysisProps) {
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

  // Calculate drawdowns
  const drawdownData: DrawdownPoint[] = calculateDrawdowns(equityCurve);

  // Apply timeframe filter
  const filteredData = filterByTimeframe(drawdownData, selectedTimeframe);

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
          data={[
            {
              x: filteredData.map((d) => d.date),
              y: filteredData.map((d) => d.equity),
              type: "scatter",
              mode: "lines",
              name: "Equity",
              line: { color: "#4CAF50" },
              yaxis: "y"
            },
            {
              x: filteredData.map((d) => d.date),
              y: filteredData.map((d) => d.drawdown_pct),
              type: "scatter",
              mode: "lines",
              name: "Drawdown",
              line: { color: "#FF5252" },
              fill: "tozeroy",
              yaxis: "y2"
            }
          ]}
          layout={{
            autosize: true,
            margin: { l: 50, r: 50, t: 30, b: 40 },
            showlegend: true,
            legend: { orientation: "h", y: 1.1 },
            yaxis: {
              title: { text: "Equity" },
              tickfont: { color: "#4CAF50" }
            },
            yaxis2: {
              title: { text: "Drawdown %" },
              tickfont: { color: "#FF5252" },
              overlaying: "y",
              side: "right",
              range: [
                Math.min(...filteredData.map((d) => d.drawdown_pct)) * 1.1,
                0
              ]
            },
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

function calculateDrawdowns(equityCurve: { date: string; equity: number }[]): DrawdownPoint[] {
  if (equityCurve.length === 0) return [];

  let peak = equityCurve[0].equity;
  
  return equityCurve.map(point => {
    // Update peak if new high
    if (point.equity > peak) {
      peak = point.equity;
    }

    // Calculate drawdown percentage
    const drawdown_pct = peak > 0 ? ((point.equity - peak) / peak) * 100 : 0;

    return {
      date: point.date,
      equity: point.equity,
      drawdown_pct
    };
  });
}

function filterByTimeframe(
  data: DrawdownPoint[],
  timeframe: "all" | "3m" | "6m" | "1y"
): DrawdownPoint[] {
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