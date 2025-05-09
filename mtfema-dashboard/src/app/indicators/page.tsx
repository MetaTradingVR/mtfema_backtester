"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  PlusCircle,
  RefreshCw, 
  AlertTriangle
} from "lucide-react"
import { IndicatorBuilder } from '@/components/indicators/indicator-builder'
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

// Define indicator type
interface Indicator {
  id: string
  name: string
  description?: string
  updated_at: string
}

// Loading placeholder for optimized page loading
const IndicatorListSkeleton = () => (
  <div className="space-y-3">
    {[1, 2, 3].map(i => (
      <div key={i} className="flex items-center space-x-4 border p-4 rounded-md">
        <div className="h-12 w-12 rounded-full bg-gray-200 animate-pulse" />
        <div className="space-y-2 flex-1">
          <div className="h-4 w-[250px] bg-gray-200 animate-pulse rounded" />
          <div className="h-4 w-[300px] bg-gray-200 animate-pulse rounded" />
        </div>
      </div>
    ))}
  </div>
)

export default function IndicatorsPage() {
  // State for indicators, loading, and errors
  const [indicators, setIndicators] = useState<Indicator[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showBuilder, setShowBuilder] = useState(false)
  
  // Optimized indicator fetching with error handling
  const fetchIndicators = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:5000/api/indicators', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Adding cache control to prevent stale data
        cache: 'no-store',
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch indicators: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        setIndicators(data.indicators || [])
      } else {
        setError(data.message || 'Unknown error occurred')
      }
    } catch (err) {
      setError(`Error fetching indicators: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setIsLoading(false)
    }
  }, [])
  
  // Fetch indicators on initial load
  useEffect(() => {
    fetchIndicators()
  }, [fetchIndicators])
  
  // Handle indicator delete
  const handleDeleteIndicator = async (id: string) => {
    if (!confirm('Are you sure you want to delete this indicator?')) {
      return
    }
    
    try {
      const response = await fetch(`http://localhost:5000/api/indicators/${id}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        throw new Error(`Failed to delete indicator: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        // Remove the deleted indicator from state without fetching again
        setIndicators(indicators.filter(ind => ind.id !== id))
      } else {
        setError(data.message || 'Unknown error occurred')
      }
    } catch (err) {
      setError(`Error deleting indicator: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }
  
  // Format date for better readability
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString()
    } catch (e) {
      return dateString
    }
  }
  
  // Save indicator and refresh the list
  const handleSaveIndicator = () => {
    setShowBuilder(false)
    fetchIndicators()
  }
  
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Custom Indicators</h1>
          <p className="mt-2 text-muted-foreground">
            Create, manage and test custom indicators for your trading strategies
          </p>
        </div>
      </div>
      
      {/* Action Bar */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-2">
          <Button 
            onClick={() => setShowBuilder(true)}
            disabled={showBuilder}
          >
            <PlusCircle className="mr-2 h-4 w-4" />
            Create New Indicator
          </Button>
          
          <Button 
            variant="outline" 
            onClick={fetchIndicators}
            disabled={isLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>
      
      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {/* Indicator Builder */}
      {showBuilder && (
        <div className="my-6">
          <IndicatorBuilder 
            onSave={handleSaveIndicator}
            onCancel={() => setShowBuilder(false)}
          />
        </div>
      )}
      
      {/* Indicator List */}
      <Card>
        <CardHeader>
          <CardTitle>Available Indicators</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <IndicatorListSkeleton />
          ) : indicators.length > 0 ? (
            <div className="divide-y">
              {indicators.map((indicator) => (
                <div key={indicator.id} className="py-4 flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-medium">{indicator.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{indicator.description || 'No description'}</p>
                    <p className="text-xs text-gray-400 mt-2">
                      Last updated: {formatDate(indicator.updated_at)}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        // Open the indicator in the builder - future enhancement
                        // For now, just alert the user
                        alert('Editing existing indicators will be available in a future update')
                      }}
                    >
                      Edit
                    </Button>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => handleDeleteIndicator(indicator.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No custom indicators found</p>
              <p className="text-sm text-gray-400 mt-2">
                Click "Create New Indicator" to get started
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
