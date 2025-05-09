"use client"

/**
 * Indicator Builder Component
 * 
 * A lightweight, performance-optimized interface for creating and testing custom indicators.
 * Designed with the dashboard's performance issues in mind.
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
// Import Plotly types
import { PlotParams } from 'react-plotly.js';
import { Data, Layout, Config } from 'plotly.js';
// Import API functions
import { 
  testIndicator, 
  createIndicator, 
  CustomIndicator as ApiCustomIndicator, 
  IndicatorParameter as ApiIndicatorParameter,
  IndicatorTestRequest,
  IndicatorTestResult
} from '@/lib/api';

// Dynamically import the Plotly component to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => <div className="w-full h-64 bg-gray-100 animate-pulse rounded-md flex items-center justify-center">Loading chart...</div>
});

// Indicator Parameter Types
export interface IndicatorParameter extends ApiIndicatorParameter {}

// Custom Indicator Code
export interface CustomIndicator extends ApiCustomIndicator {
  test_data?: boolean;
  save: boolean;
  include_price?: boolean;
}

// Indicator Test Results
interface TestResult extends IndicatorTestResult {}

// Indicator Templates - Memoized to reduce re-renders
const INDICATOR_TEMPLATES = {
  'Simple': 
`class CustomIndicator(Indicator):
    """A simple custom indicator"""
    
    def __init__(self, period=14, source="close", name=None):
        params = {'period': period, 'source': source}
        super().__init__(name or "CustomIndicator", params)
        self.required_columns = [source]
    
    def _calculate(self, data):
        period = self.params['period']
        source = self.params['source']
        
        # Simple moving average calculation
        result = data[source].rolling(window=period).mean()
        
        return {'value': result}`,
  
  'Oscillator': 
`class CustomOscillator(Indicator):
    """An oscillator-type indicator with upper and lower bounds"""
    
    def __init__(self, period=14, upper_threshold=70, lower_threshold=30, source="close", name=None):
        params = {
            'period': period,
            'upper_threshold': upper_threshold,
            'lower_threshold': lower_threshold,
            'source': source
        }
        super().__init__(name or "CustomOscillator", params)
        self.required_columns = [source]
    
    def _calculate(self, data):
        period = self.params['period']
        source = self.params['source']
        
        # Calculate price changes
        delta = data[source].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and indicator value (similar to RSI)
        rs = avg_gain / avg_loss
        value = 100 - (100 / (1 + rs))
        
        # Generate signals based on thresholds
        overbought = value > self.params['upper_threshold']
        oversold = value < self.params['lower_threshold']
        
        return {
            'value': value,
            'overbought': overbought,
            'oversold': oversold
        }`,
  
  'Multi-Data': 
`class MultiSourceIndicator(Indicator):
    """An indicator that combines multiple data sources"""
    
    def __init__(self, period=10, weight_close=0.6, weight_volume=0.4, name=None):
        params = {
            'period': period,
            'weight_close': weight_close,
            'weight_volume': weight_volume
        }
        super().__init__(name or "MultiSourceIndicator", params)
        self.required_columns = ['close', 'volume']
    
    def _calculate(self, data):
        period = self.params['period']
        weight_close = self.params['weight_close']
        weight_volume = self.params['weight_volume']
        
        # Normalize price and volume data
        norm_close = data['close'] / data['close'].rolling(window=period).mean()
        norm_volume = data['volume'] / data['volume'].rolling(window=period).mean()
        
        # Combine signals with weights
        combined = (norm_close * weight_close) + (norm_volume * weight_volume)
        
        # Generate trend signal
        trend = combined > combined.shift(1)
        
        return {
            'value': combined,
            'trend': trend
        }`
};

// Default parameters for new indicators
const DEFAULT_PARAMETERS: IndicatorParameter[] = [
  { name: 'period', type: 'int', default: 14, min: 2, max: 200 },
  { name: 'source', type: 'string', default: 'close', options: ['open', 'high', 'low', 'close', 'volume'] }
];

// API Endpoints
const API_BASE_URL = 'http://localhost:5000/api';

// Component Props
export interface IndicatorBuilderProps {
  onSave?: (indicator: CustomIndicator) => void;
  onCancel?: () => void;
  initialData?: CustomIndicator;
}

// Optimized parameter component to reduce re-renders
const ParameterItem = React.memo(({ 
  param, 
  index, 
  onUpdate, 
  onRemove 
}: { 
  param: IndicatorParameter, 
  index: number, 
  onUpdate: (index: number, field: string, value: any) => void,
  onRemove: (index: number) => void
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2 p-3 border rounded-md bg-gray-50 dark:bg-gray-800">
      <div className="flex-1 min-w-[120px]">
        <Label className="text-xs" htmlFor={`param-name-${index}`}>Name</Label>
        <Input
          id={`param-name-${index}`}
          value={param.name}
          onChange={(e) => onUpdate(index, 'name', e.target.value)}
          className="mt-1"
        />
      </div>
      
      <div className="w-[120px]">
        <Label className="text-xs" htmlFor={`param-type-${index}`}>Type</Label>
        <Select
          value={param.type}
          onValueChange={(value) => onUpdate(index, 'type', value)}
        >
          <SelectTrigger id={`param-type-${index}`} className="mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="int">Integer</SelectItem>
            <SelectItem value="float">Float</SelectItem>
            <SelectItem value="string">String</SelectItem>
            <SelectItem value="bool">Boolean</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div className="flex-1 min-w-[120px]">
        <Label className="text-xs" htmlFor={`param-default-${index}`}>Default</Label>
        {param.type === 'string' && param.options ? (
          <Select
            value={param.default}
            onValueChange={(value) => onUpdate(index, 'default', value)}
          >
            <SelectTrigger id={`param-default-${index}`} className="mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {param.options.map(option => (
                <SelectItem key={option} value={option}>{option}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : param.type === 'bool' ? (
          <Select
            value={param.default.toString()}
            onValueChange={(value) => onUpdate(index, 'default', value === 'true')}
          >
            <SelectTrigger id={`param-default-${index}`} className="mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="true">True</SelectItem>
              <SelectItem value="false">False</SelectItem>
            </SelectContent>
          </Select>
        ) : (
          <Input
            id={`param-default-${index}`}
            type={param.type === 'int' || param.type === 'float' ? 'number' : 'text'}
            step={param.type === 'float' ? '0.01' : '1'}
            min={param.min}
            max={param.max}
            value={param.default}
            onChange={(e) => {
              const value = param.type === 'int' ? parseInt(e.target.value) : 
                          param.type === 'float' ? parseFloat(e.target.value) : 
                          e.target.value;
              onUpdate(index, 'default', value);
            }}
            className="mt-1"
          />
        )}
      </div>
      
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onRemove(index)}
        className="text-red-500 hover:text-red-700 hover:bg-red-100 dark:hover:bg-red-900"
      >
        <span className="sr-only">Remove parameter</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
      </Button>
    </div>
  );
});

ParameterItem.displayName = 'ParameterItem';

export const IndicatorBuilder = React.memo(({ onSave, onCancel, initialData }: IndicatorBuilderProps) => {
  // State
  const [name, setName] = useState(initialData?.name || 'CustomIndicator');
  const [description, setDescription] = useState(initialData?.description || 'A custom indicator');
  const [parameters, setParameters] = useState<IndicatorParameter[]>(
    initialData?.parameters || DEFAULT_PARAMETERS
  );
  const [code, setCode] = useState(
    initialData?.code || INDICATOR_TEMPLATES['Simple']
  );
  const [activeTemplate, setActiveTemplate] = useState('Custom');
  const [activeTab, setActiveTab] = useState('code');
  
  // Test results state
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, number[]> | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [savedMessage, setSavedMessage] = useState('');
  // Add validation state
  const [validationState, setValidationState] = useState<'pending' | 'valid' | 'invalid'>('pending');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  // Template options (memoized)
  const templateOptions = useMemo(() => 
    Object.keys(INDICATOR_TEMPLATES).map(template => (
      <SelectItem key={template} value={template}>{template} Template</SelectItem>
    )),
    []
  );
  
  // Add a new parameter
  const addParameter = useCallback(() => {
    setParameters(prev => [
      ...prev,
      { name: `param${prev.length + 1}`, type: 'float', default: 0 }
    ]);
  }, []);
  
  // Remove a parameter
  const removeParameter = useCallback((index: number) => {
    setParameters(prev => prev.filter((_, i) => i !== index));
  }, []);
  
  // Update parameter properties
  const updateParameter = useCallback((index: number, field: string, value: any) => {
    setParameters(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  }, []);
  
  // Load a template
  const loadTemplate = useCallback((templateName: string) => {
    setActiveTemplate(templateName);
    setCode(INDICATOR_TEMPLATES[templateName as keyof typeof INDICATOR_TEMPLATES]);
    
    // Update parameters based on template
    if (templateName === 'Oscillator') {
      setParameters([
        { name: 'period', type: 'int', default: 14, min: 2, max: 200 },
        { name: 'upper_threshold', type: 'int', default: 70, min: 50, max: 95 },
        { name: 'lower_threshold', type: 'int', default: 30, min: 5, max: 50 },
        { name: 'source', type: 'string', default: 'close', options: ['open', 'high', 'low', 'close'] }
      ]);
    } else if (templateName === 'Multi-Data') {
      setParameters([
        { name: 'period', type: 'int', default: 10, min: 2, max: 100 },
        { name: 'weight_close', type: 'float', default: 0.6, min: 0, max: 1 },
        { name: 'weight_volume', type: 'float', default: 0.4, min: 0, max: 1 }
      ]);
    } else {
      setParameters(DEFAULT_PARAMETERS);
    }
  }, []);
  
  // Validate the indicator code for syntax errors and parameter consistency
  const validateIndicatorCode = useCallback(() => {
    // Reset validation state
    setValidationErrors([]);
    setValidationState('pending');
    
    const errors: string[] = [];
    
    // Basic syntax validation
    if (!code.includes('class') || !code.includes('def _calculate')) {
      errors.push("Code must define a class with a _calculate method");
    }
    
    // Check for required methods
    if (!code.includes('def __init__')) {
      errors.push("Missing __init__ method in indicator class");
    }
    
    // Validate parameter usage in code
    parameters.forEach(param => {
      // Check if each defined parameter is used in the code
      if (!code.includes(`self.params['${param.name}']`)) {
        errors.push(`Parameter '${param.name}' is defined but not used in the code`);
      }
    });
    
    // Check for potentially dangerous code patterns
    if (code.includes('import os') || code.includes('subprocess') || 
        code.includes('exec(') || code.includes('eval(')) {
      errors.push("Code contains potentially unsafe operations");
    }
    
    // Set validation result
    if (errors.length > 0) {
      setValidationState('invalid');
      setValidationErrors(errors);
      return false;
    } else {
      setValidationState('valid');
      return true;
    }
  }, [code, parameters]);
  
  // Test the indicator with enhanced validation
  const handleTest = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage('');
    setTestResults(null);
    setSavedMessage('');
    
    // First run client-side validation
    const isValid = validateIndicatorCode();
    if (!isValid) {
      setIsLoading(false);
      return;
    }
    
    try {
      // Prepare test request using interface from API
      const testRequest: IndicatorTestRequest = {
        name,
        description,
        parameters,
        code,
        test_data: true,
        save: false,
        include_price: true
      };
      
      // Use API function instead of direct fetch
      const result = await testIndicator(testRequest);
      
      if (result.success) {
        setTestResults(result.preview || null);
        setActiveTab('results');
        setValidationState('valid');
      } else {
        setErrorMessage(result.message);
        setValidationState('invalid');
        // Parse server-side validation errors if available
        if (result.message.includes(";")) {
          setValidationErrors(result.message.split(";").filter(m => m.trim().length > 0));
        }
      }
    } catch (error) {
      // Fallback error handling
      if (error instanceof Error) {
        setErrorMessage(`Unexpected error: ${error.message}`);
      } else {
        setErrorMessage(`Unexpected error occurred`);
      }
      setValidationState('invalid');
    } finally {
      setIsLoading(false);
    }
  }, [name, description, parameters, code, setActiveTab, validateIndicatorCode]);
  
  // Save the indicator
  const handleSave = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage('');
    setSavedMessage('');
    
    try {
      // Prepare indicator data for API
      const indicatorData: ApiCustomIndicator = {
        name,
        description,
        parameters,
        code,
      };
      
      // Use API function instead of direct fetch
      const result = await createIndicator(indicatorData);
      
      if (result.success) {
        setSavedMessage(`Indicator "${name}" saved successfully!`);
        if (onSave) {
          onSave({
            ...indicatorData,
            save: true,
            id: result.id
          });
        }
      } else {
        setErrorMessage(result.message);
      }
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(`Error saving indicator: ${error.message}`);
      } else {
        setErrorMessage(`Unknown error occurred`);
      }
    } finally {
      setIsLoading(false);
    }
  }, [name, description, parameters, code, onSave]);
  
  // Render parameter list (memoized to reduce re-renders)
  const parameterList = useMemo(() => (
    <div className="space-y-3">
      {parameters.map((param, index) => (
        <ParameterItem 
          key={`${param.name}-${index}`}
          param={param}
          index={index}
          onUpdate={updateParameter}
          onRemove={removeParameter}
        />
      ))}
    </div>
  ), [parameters, updateParameter, removeParameter]);
  
  // Render the results visualization
  const renderResultsVisualization = useMemo(() => {
    if (!testResults || Object.keys(testResults).length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-md p-6">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400 mb-4">
            <rect width="18" height="18" x="3" y="3" rx="2" ry="2"></rect>
            <line x1="3" x2="21" y1="9" y2="9"></line>
            <path d="m9 16 3-3 3 3"></path>
          </svg>
          <p className="text-gray-500 text-center">Run a test to see indicator results visualized here.</p>
          <p className="text-gray-400 text-sm text-center mt-2">Results will include charts and data tables.</p>
        </div>
      );
    }
    
    // Generate dates array if not provided (for sample data)
    const dates = testResults.dates || 
      Array.from({ length: Object.values(testResults)[0].length }, 
        (_, i) => new Date(Date.now() - (30 - i) * 86400000).toISOString().split('T')[0]
      );
    
    // Prepare plot data
    const plotData: Data[] = [];
    
    // Add price data if available
    if (testResults.price_data) {
      // Add candlestick chart for price
      plotData.push({
        type: 'candlestick',
        x: dates,
        open: testResults.price_data.open,
        high: testResults.price_data.high,
        low: testResults.price_data.low,
        close: testResults.price_data.close,
        name: 'Price',
        increasing: { line: { color: '#26a69a' } },
        decreasing: { line: { color: '#ef5350' } },
        yaxis: 'y'
      } as unknown as Data);
    }
    
    // Add each indicator result as a line
    Object.entries(testResults).forEach(([key, values]) => {
      // Skip non-array properties and price_data
      if (!Array.isArray(values) || key === 'dates' || key === 'price_data') return;
      
      plotData.push({
        type: 'scatter',
        mode: 'lines',
        x: dates,
        y: values,
        name: key,
        yaxis: testResults.price_data ? 'y2' : 'y',
      } as Data);
    });
    
    // Plot layout
    const layout: Partial<Layout> = {
      autosize: true,
      height: 500,
      margin: { l: 50, r: 50, t: 50, b: 50 },
      title: {
        text: `${name} Indicator Test Results`
      },
      xaxis: { 
        title: {
          text: 'Date'
        },
        rangeslider: { visible: false }
      },
      yaxis: {
        title: {
          text: testResults.price_data ? 'Price' : 'Value'
        },
        domain: testResults.price_data ? [0, 0.7] : [0, 1]
      },
      yaxis2: testResults.price_data ? {
        title: {
          text: 'Indicator Value'
        },
        domain: [0.7, 1],
        overlaying: false as const
      } : undefined,
      legend: { 
        orientation: 'h' as const,
        y: -0.2
      },
      dragmode: 'zoom' as const,
      hovermode: 'closest' as const,
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)'
    };
    
    // Configuration options
    const config: Partial<Config> = {
      responsive: true,
      scrollZoom: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'] as any[]
    };
    
    return (
      <div className="space-y-6">
        <div className="border rounded-md bg-white dark:bg-gray-800 p-2">
          <Plot data={plotData} layout={layout} config={config} className="w-full" />
        </div>
        
        {/* Data preview table */}
        <div className="border rounded-md overflow-auto">
          <Table>
            <TableCaption>Indicator Results Data Preview</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Date</TableHead>
                {Object.keys(testResults).filter(key => 
                  Array.isArray(testResults[key]) && key !== 'dates' && key !== 'price_data'
                ).map(key => (
                  <TableHead key={key}>{key}</TableHead>
                ))}
                {testResults.price_data && <TableHead>Price (Close)</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {dates.slice(-10).map((date, i) => (
                <TableRow key={date}>
                  <TableCell className="font-medium">{date}</TableCell>
                  {Object.entries(testResults).filter(([key]) => 
                    Array.isArray(testResults[key]) && key !== 'dates' && key !== 'price_data'
                  ).map(([key, values]) => (
                    <TableCell key={key}>{values[values.length - 10 + i]?.toFixed(4) || 'N/A'}</TableCell>
                  ))}
                  {testResults.price_data && (
                    <TableCell>
                      {testResults.price_data.close[testResults.price_data.close.length - 10 + i]?.toFixed(2) || 'N/A'}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }, [testResults, name]);
  
  // Effect to update template selection if initialData is provided
  useEffect(() => {
    if (initialData) {
      // Try to determine which template is being used
      let templateFound = false;
      Object.entries(INDICATOR_TEMPLATES).forEach(([templateName, templateCode]) => {
        // Simple heuristic - if code is similar to template, set it
        if (initialData.code.includes(templateCode.substring(0, 50))) {
          setActiveTemplate(templateName);
          templateFound = true;
        }
      });
      
      if (!templateFound) {
        setActiveTemplate('Custom');
      }
    }
  }, [initialData]);
  
  return (
    <Card className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">
          {initialData ? 'Edit Indicator' : 'Custom Indicator Builder'}
        </h2>
        <div className="flex space-x-2">
          <Select value={activeTemplate} onValueChange={loadTemplate}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select template" />
            </SelectTrigger>
            <SelectContent>
              {templateOptions}
              <SelectItem value="Custom">Custom</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      {/* Indicator Header Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <Label htmlFor="indicator-name">Indicator Name</Label>
          <Input
            id="indicator-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="MyCustomIndicator"
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="indicator-description">Description</Label>
          <Input
            id="indicator-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this indicator does"
            className="mt-1"
          />
        </div>
      </div>
      
      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="code">Code</TabsTrigger>
          <TabsTrigger value="parameters">Parameters</TabsTrigger>
          <TabsTrigger value="results">Test Results</TabsTrigger>
        </TabsList>
        
        <TabsContent value="code" className="py-4">
          <div className="space-y-4">
            <div className="relative">
              <textarea
                className="w-full h-96 font-mono text-sm p-4 border rounded bg-gray-50 dark:bg-gray-900"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
              
              {validationState === 'valid' && (
                <div className="absolute top-2 right-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  Valid ✓
                </div>
              )}
            </div>
            
            {/* Display validation errors */}
            {validationState === 'invalid' && validationErrors.length > 0 && (
              <Alert variant="destructive">
                <AlertTitle>Validation Errors</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc pl-5 mt-2 space-y-1">
                    {validationErrors.map((error, idx) => (
                      <li key={idx} className="text-sm">{error}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
            
            <div className="flex justify-between items-center">
              <Button variant="outline" onClick={validateIndicatorCode}>
                Validate Code
              </Button>
              <Button onClick={handleTest} disabled={isLoading}>
                {isLoading ? "Testing..." : "Test Indicator"}
              </Button>
            </div>
          </div>
        </TabsContent>
        
        {/* Parameters Tab */}
        <TabsContent value="parameters" className="space-y-4">
          <div className="flex justify-between items-center mb-2">
            <Label>Parameters</Label>
            <Button variant="outline" size="sm" onClick={addParameter}>
              Add Parameter
            </Button>
          </div>
          
          {parameterList}
        </TabsContent>
        
        {/* Results Tab */}
        <TabsContent value="results" className="py-4">
          {errorMessage ? (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Error Testing Indicator</AlertTitle>
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          ) : (
            <>
              {isLoading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
              ) : (
                renderResultsVisualization
              )}
            </>
          )}
          
          <div className="flex justify-end mt-4">
            <Button onClick={handleTest} disabled={isLoading} className="mr-2">
              {isLoading ? "Testing..." : "Run Test Again"}
            </Button>
            <Button onClick={handleSave} disabled={isLoading || (!testResults && !errorMessage)} variant="default">
              {isLoading ? "Saving..." : "Save Indicator"}
            </Button>
          </div>
        </TabsContent>
      </Tabs>
      
      {/* Bottom action buttons */}
      <div className="flex justify-between mt-6">
        {onCancel && (
          <Button
            variant="outline"
            onClick={onCancel}
          >
            Cancel
          </Button>
        )}
        
        <div className="flex space-x-2">
          <Button
            variant="default"
            onClick={handleSave}
            disabled={isLoading || !!errorMessage}
          >
            {isLoading ? 'Saving...' : initialData ? 'Update Indicator' : 'Save Indicator'}
          </Button>
        </div>
      </div>
    </Card>
  );
});

IndicatorBuilder.displayName = 'IndicatorBuilder';

export default IndicatorBuilder;
