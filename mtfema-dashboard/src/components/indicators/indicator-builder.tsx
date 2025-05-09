"use client"

/**
 * Indicator Builder Component
 * 
 * A lightweight, performance-optimized interface for creating and testing custom indicators.
 * Designed with the dashboard's performance issues in mind.
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Indicator Parameter Types
export interface IndicatorParameter {
  name: string;
  type: 'int' | 'float' | 'string' | 'bool';
  default: any;
  min?: number;
  max?: number;
  options?: string[];
  description?: string;
}

// Custom Indicator Code
export interface CustomIndicator {
  name: string;
  description?: string;
  parameters: IndicatorParameter[];
  code: string;
  test_data?: boolean;
  save: boolean;
}

// Indicator Test Results
interface TestResult {
  success: boolean;
  message: string;
  preview?: Record<string, number[]>;
}

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

export const IndicatorBuilder = React.memo(({ onSave, onCancel }: IndicatorBuilderProps) => {
  // State
  const [name, setName] = useState('CustomIndicator');
  const [description, setDescription] = useState('A custom indicator');
  const [parameters, setParameters] = useState<IndicatorParameter[]>(DEFAULT_PARAMETERS);
  const [code, setCode] = useState(INDICATOR_TEMPLATES['Simple']);
  const [activeTemplate, setActiveTemplate] = useState('Simple');
  const [activeTab, setActiveTab] = useState('code');
  
  // Test results state
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, number[]> | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [savedMessage, setSavedMessage] = useState('');
  
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
  
  // Test the indicator
  const handleTest = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage('');
    setTestResults(null);
    setSavedMessage('');
    
    try {
      const indicatorData: CustomIndicator = {
        name,
        description,
        parameters,
        code,
        test_data: true,
        save: false
      };
      
      const response = await fetch(`${API_BASE_URL}/indicators/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(indicatorData),
      });
      
      const result = await response.json() as TestResult;
      
      if (result.success) {
        setTestResults(result.preview || null);
        setActiveTab('results');
      } else {
        setErrorMessage(result.message);
      }
    } catch (error) {
      setErrorMessage(`Error testing indicator: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  }, [name, description, parameters, code, setActiveTab]);
  
  // Save the indicator
  const handleSave = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage('');
    setSavedMessage('');
    
    try {
      const indicatorData: CustomIndicator = {
        name,
        description,
        parameters,
        code,
        save: true
      };
      
      const response = await fetch(`${API_BASE_URL}/indicators`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(indicatorData),
      });
      
      const result = await response.json() as { success: boolean; message: string };
      
      if (result.success) {
        setSavedMessage(`Indicator "${name}" saved successfully!`);
        if (onSave) {
          onSave(indicatorData);
        }
      } else {
        setErrorMessage(result.message);
      }
    } catch (error) {
      setErrorMessage(`Error saving indicator: ${error instanceof Error ? error.message : 'Unknown error'}`);
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
  
  return (
    <Card className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Custom Indicator Builder</h2>
        <div className="flex space-x-2">
          <Select value={activeTemplate} onValueChange={loadTemplate}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select template" />
            </SelectTrigger>
            <SelectContent>
              {templateOptions}
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
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid grid-cols-3">
          <TabsTrigger value="parameters">Parameters</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>
        
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
        
        {/* Code Tab */}
        <TabsContent value="code">
          <Label htmlFor="indicator-code" className="mb-2 block">
            Indicator Code
          </Label>
          <div className="border rounded-md p-1 bg-gray-50 dark:bg-slate-900">
            <textarea
              id="indicator-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full font-mono text-sm p-2 h-[400px] bg-transparent focus:outline-none"
              spellCheck={false}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            This code must follow the Indicator class structure from the MT9 EMA backtester framework.
          </p>
        </TabsContent>
        
        {/* Results Tab */}
        <TabsContent value="results">
          {errorMessage && (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription className="whitespace-pre-wrap font-mono text-xs">
                {errorMessage}
              </AlertDescription>
            </Alert>
          )}
          
          {testResults && (
            <div>
              <h3 className="text-lg font-medium mb-2">Test Results</h3>
              <Alert className="mb-4 bg-green-50 border-green-300 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-100">
                <AlertTitle>Success</AlertTitle>
                <AlertDescription>
                  Indicator calculated successfully!
                </AlertDescription>
              </Alert>
              
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="preview">
                  <AccordionTrigger>Preview Data</AccordionTrigger>
                  <AccordionContent>
                    <div className="overflow-auto max-h-80">
                      <pre className="text-xs p-4 bg-gray-50 dark:bg-gray-800 rounded-md whitespace-pre-wrap">
                        {JSON.stringify(testResults, null, 2)}
                      </pre>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          )}
          
          {savedMessage && (
            <Alert className="mb-4 bg-blue-50 border-blue-300 text-blue-800 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-100">
              <AlertTitle>Saved</AlertTitle>
              <AlertDescription>
                {savedMessage}
              </AlertDescription>
            </Alert>
          )}
          
          {!testResults && !errorMessage && !savedMessage && (
            <div className="text-center p-12 text-gray-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto h-12 w-12 mb-4"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
              <p>Click &quot;Test Indicator&quot; to see the results</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
      
      {/* Action buttons */}
      <div className="flex justify-end space-x-2 mt-6">
        {onCancel && (
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
        )}
        
        <Button
          variant="secondary"
          onClick={handleTest}
          disabled={isLoading}
          className="min-w-[120px]"
        >
          {isLoading ? 'Testing...' : 'Test Indicator'}
        </Button>
        
        <Button
          onClick={handleSave}
          disabled={isLoading || !!errorMessage}
          className="min-w-[120px]"
        >
          {isLoading ? 'Saving...' : 'Save Indicator'}
        </Button>
      </div>
    </Card>
  );
});

IndicatorBuilder.displayName = 'IndicatorBuilder';

export default IndicatorBuilder;
