"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { fetchParameterHeatmap, HeatmapData } from "@/lib/api"
import dynamic from "next/dynamic"

// Dynamically import Plot from react-plotly.js
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => <div className="h-[400px] flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>
})

interface HeatmapChartProps {
  optimizationId: string;
  param1: string;
  param2: string;
  metric: string;
}

export function HeatmapChart({ optimizationId, param1, param2, metric }: HeatmapChartProps) {
  const [data, setData] = useState<HeatmapData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    async function loadHeatmapData() {
      try {
        setLoading(true)
        setError(null)
        const heatmapData = await fetchParameterHeatmap(optimizationId, param1, param2, metric)
        setData(heatmapData)
      } catch (err) {
        console.error(err)
        setError("Failed to load heatmap data")
      } finally {
        setLoading(false)
      }
    }

    loadHeatmapData()
  }, [optimizationId, param1, param2, metric])

  if (loading) {
    return (
      <div className="h-[400px] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="h-[400px] flex items-center justify-center flex-col gap-2 text-center">
        <p className="text-destructive">{error || "No data available"}</p>
        <p className="text-muted-foreground text-sm">
          Try selecting different parameters or check the optimization results
        </p>
      </div>
    )
  }

  const plotData = [{
    type: "heatmap",
    z: data.z_values,
    x: data.x_values,
    y: data.y_values,
    colorscale: "Viridis",
    colorbar: {
      title: data.metric,
      titleside: "right"
    }
  }] as any

  const layout = {
    title: {
      text: `Effect of ${param1} and ${param2} on ${metric}`,
      font: {
        family: "Inter, sans-serif",
        size: 16
      }
    },
    xaxis: {
      title: data.x_label,
      tickfont: {
        family: "Inter, sans-serif",
        size: 12
      }
    },
    yaxis: {
      title: data.y_label,
      tickfont: {
        family: "Inter, sans-serif",
        size: 12
      }
    },
    margin: {
      l: 60,
      r: 30,
      t: 60,
      b: 60
    },
    autosize: true
  } as any

  return (
    <div className="w-full h-[400px]" ref={chartRef}>
      {data && (
        <Plot
          data={plotData}
          layout={layout}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: "100%", height: "100%" }}
        />
      )}
    </div>
  )
} 