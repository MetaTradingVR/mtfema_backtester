"use client"

import React, { useState, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BacktestIndicator } from '@/lib/api'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => <div className="w-full h-64 bg-gray-100 animate-pulse rounded-md flex items-center justify-center">Loading chart...</div>
})

interface IndicatorResultsProps {
  indicators: BacktestIndicator[]
  dates: string[]
  prices?: {
    open: number[]
    high: number[]
    low: number[]
    close: number[]
    volume?: number[]
  }
}

export function IndicatorResults({ indicators, dates, prices }: IndicatorResultsProps) {
  const [selectedIndicator, setSelectedIndicator] = useState<string | null>(
    indicators.length > 0 ? indicators[0].id : null
  )
  
  // Get the currently selected indicator
  const currentIndicator = useMemo(() => {
    return indicators.find(ind => ind.id === selectedIndicator) || null
  }, [indicators, selectedIndicator])
  
  // Generate the plot data
  const plotData = useMemo(() => {
    if (!currentIndicator || !currentIndicator.values) {
      return []
    }
    
    const data: any[] = []
    
    // Add price chart if available
    if (prices) {
      data.push({
        type: 'candlestick',
        x: dates,
        open: prices.open,
        high: prices.high,
        low: prices.low,
        close: prices.close,
        name: 'Price',
        increasing: { line: { color: '#26a69a' } },
        decreasing: { line: { color: '#ef5350' } },
        yaxis: 'y'
      })
    }
    
    // Add each indicator output
    Object.entries(currentIndicator.values).forEach(([key, values]) => {
      data.push({
        type: 'scatter',
        mode: 'lines',
        x: dates,
        y: values,
        name: key,
        yaxis: prices ? 'y2' : 'y'
      })
    })
    
    return data
  }, [currentIndicator, dates, prices])
  
  // Plot layout
  const layout = useMemo(() => {
    return {
      autosize: true,
      height: 500,
      margin: { l: 50, r: 50, t: 50, b: 50 },
      title: {
        text: currentIndicator ? `${currentIndicator.name} Indicator Results` : 'Indicator Results'
      },
      xaxis: { 
        title: 'Date',
        rangeslider: { visible: false }
      },
      yaxis: {
        title: prices ? 'Price' : 'Value',
        domain: prices ? [0, 0.7] : [0, 1]
      },
      yaxis2: prices ? {
        title: 'Indicator Value',
        domain: [0.7, 1],
        overlaying: false
      } : undefined,
      legend: { 
        orientation: 'h',
        y: -0.2
      },
      dragmode: 'zoom',
      hovermode: 'closest',
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)'
    }
  }, [currentIndicator, prices])
  
  // Configuration options
  const config = {
    responsive: true,
    scrollZoom: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d']
  }
  
  if (indicators.length === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-center">
          <p className="text-muted-foreground">No custom indicators were used in this backtest</p>
        </CardContent>
      </Card>
    )
  }
  
  if (!currentIndicator?.values) {
    return (
      <Card>
        <CardContent className="py-6 text-center">
          <p className="text-muted-foreground">No indicator data available</p>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Custom Indicator Analysis</CardTitle>
        <div className="flex flex-wrap gap-2 mt-2">
          {indicators.map(indicator => (
            <Button
              key={indicator.id}
              variant={selectedIndicator === indicator.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedIndicator(indicator.id)}
            >
              {indicator.name}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="border rounded-md bg-white dark:bg-gray-800 p-2">
          <Plot 
            data={plotData} 
            layout={layout} 
            config={config} 
            className="w-full" 
          />
        </div>
        
        {currentIndicator && (
          <div className="mt-4 space-y-2">
            <h3 className="text-sm font-medium">Parameters</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {Object.entries(currentIndicator.parameters).map(([key, value]) => (
                <div key={key} className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md">
                  <span className="text-xs text-gray-500 block">{key}</span>
                  <span className="font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 