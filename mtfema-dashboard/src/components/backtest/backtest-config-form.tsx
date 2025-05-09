"use client"

import { useState, useEffect } from "react"
import { z } from "zod"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from "@/components/ui/form"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { IndicatorSelector } from "@/components/backtest/indicator-selector"
import { StandardIndicatorSelector, type SelectedStandardIndicator } from "@/components/indicators/standard-indicator-selector"
import { BacktestParams } from "@/lib/api"

const backtestFormSchema = z.object({
  symbol: z.string().min(1, "Symbol is required"),
  timeframe: z.string().min(1, "Timeframe is required"),
  start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Start date must be in YYYY-MM-DD format"),
  end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "End date must be in YYYY-MM-DD format"),
  ema_period: z.coerce.number().int().min(1).max(200),
  extension_threshold: z.coerce.number().min(0.1).max(10),
  stop_loss: z.coerce.number().min(0).max(100).optional(),
  take_profit: z.coerce.number().min(0).max(500).optional(),
})

interface BacktestConfigFormProps {
  onSubmit: (data: BacktestParams) => void
  isSubmitting: boolean
}

export function BacktestConfigForm({ onSubmit, isSubmitting }: BacktestConfigFormProps) {
  // Form state
  const form = useForm<z.infer<typeof backtestFormSchema>>({
    resolver: zodResolver(backtestFormSchema),
    defaultValues: {
      symbol: "BTCUSDT",
      timeframe: "1h",
      start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
      ema_period: 9,
      extension_threshold: 1.5,
      stop_loss: 2,
      take_profit: 6,
    },
  })
  
  // Indicators state
  const [selectedCustomIndicators, setSelectedCustomIndicators] = useState<Array<{id: string, parameters: Record<string, any>}>>([])
  const [selectedStandardIndicators, setSelectedStandardIndicators] = useState<SelectedStandardIndicator[]>([])
  const [activeTab, setActiveTab] = useState<string>("custom")
  
  // Handle form submission
  const handleSubmit = (values: z.infer<typeof backtestFormSchema>) => {
    // Combine form values with selected indicators
    const params: BacktestParams = {
      ...values,
      custom_indicators: selectedCustomIndicators,
      standard_indicators: selectedStandardIndicators.map(indicator => ({
        definition_id: indicator.definition_id,
        name: indicator.name,
        parameters: indicator.parameters
      }))
    }
    
    onSubmit(params)
  }
  
  // Add custom indicator
  const handleSelectCustomIndicator = (indicator: {id: string, parameters: Record<string, any>}) => {
    setSelectedCustomIndicators(prev => [...prev, indicator])
  }
  
  // Remove custom indicator
  const handleRemoveCustomIndicator = (id: string) => {
    setSelectedCustomIndicators(prev => prev.filter(ind => ind.id !== id))
  }
  
  // Update custom indicator parameters
  const handleUpdateCustomIndicatorParams = (id: string, parameters: Record<string, any>) => {
    setSelectedCustomIndicators(prev => 
      prev.map(ind => ind.id === id ? { ...ind, parameters } : ind)
    )
  }
  
  // Add standard indicator
  const handleSelectStandardIndicator = (indicator: SelectedStandardIndicator) => {
    setSelectedStandardIndicators(prev => [...prev, indicator])
  }
  
  // Remove standard indicator
  const handleRemoveStandardIndicator = (id: string) => {
    setSelectedStandardIndicators(prev => prev.filter(ind => ind.id !== id))
  }
  
  // Update standard indicator parameters
  const handleUpdateStandardIndicatorParams = (id: string, parameters: Record<string, any>) => {
    setSelectedStandardIndicators(prev => 
      prev.map(ind => ind.id === id ? { ...ind, parameters } : ind)
    )
  }
  
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Market & Time Range</CardTitle>
            <CardDescription>
              Select the market and timeframe for your backtest
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="symbol"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Symbol</FormLabel>
                    <FormControl>
                      <Input placeholder="BTCUSDT" {...field} />
                    </FormControl>
                    <FormDescription>
                      The trading pair to backtest
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="timeframe"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Timeframe</FormLabel>
                    <Select 
                      onValueChange={field.onChange} 
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select timeframe" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1m">1 minute</SelectItem>
                        <SelectItem value="5m">5 minutes</SelectItem>
                        <SelectItem value="15m">15 minutes</SelectItem>
                        <SelectItem value="30m">30 minutes</SelectItem>
                        <SelectItem value="1h">1 hour</SelectItem>
                        <SelectItem value="4h">4 hours</SelectItem>
                        <SelectItem value="1d">1 day</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Chart timeframe
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>End Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Strategy Parameters</CardTitle>
            <CardDescription>
              Configure the MT9 EMA strategy parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="ema_period"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>EMA Period</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormDescription>
                      Period for the Exponential Moving Average
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="extension_threshold"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Extension Threshold</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.1" {...field} />
                    </FormControl>
                    <FormDescription>
                      Minimum extension factor
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="stop_loss"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Stop Loss (%)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.1" {...field} />
                    </FormControl>
                    <FormDescription>
                      Percentage from entry (optional)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="take_profit"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Take Profit (%)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.1" {...field} />
                    </FormControl>
                    <FormDescription>
                      Percentage from entry (optional)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>
        
        {/* Technical Indicators Section */}
        <Card>
          <CardHeader>
            <CardTitle>Technical Indicators</CardTitle>
            <CardDescription>
              Add technical indicators to your backtest
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="custom">Custom Indicators</TabsTrigger>
                <TabsTrigger value="standard">Standard Indicators</TabsTrigger>
              </TabsList>
              
              <TabsContent value="custom" className="mt-4">
                <IndicatorSelector 
                  selectedIndicators={selectedCustomIndicators}
                  onSelectIndicator={handleSelectCustomIndicator}
                  onRemoveIndicator={handleRemoveCustomIndicator}
                  onUpdateIndicatorParams={handleUpdateCustomIndicatorParams}
                />
              </TabsContent>
              
              <TabsContent value="standard" className="mt-4">
                <StandardIndicatorSelector
                  selectedIndicators={selectedStandardIndicators}
                  onSelectIndicator={handleSelectStandardIndicator}
                  onRemoveIndicator={handleRemoveStandardIndicator}
                  onUpdateIndicatorParams={handleUpdateStandardIndicatorParams}
                />
              </TabsContent>
            </Tabs>
            
            <div className="mt-4">
              <Alert className="bg-blue-50 dark:bg-blue-950 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800">
                <AlertDescription>
                  <div className="flex flex-col gap-2">
                    <p>Total indicators selected: {selectedCustomIndicators.length + selectedStandardIndicators.length}</p>
                    <p className="text-xs text-muted-foreground">
                      Custom indicators: {selectedCustomIndicators.length} | 
                      Standard indicators: {selectedStandardIndicators.length}
                    </p>
                  </div>
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
        
        <Button 
          type="submit" 
          className="w-full" 
          disabled={isSubmitting}
        >
          {isSubmitting ? "Running..." : "Run Backtest"}
        </Button>
      </form>
    </Form>
  )
} 