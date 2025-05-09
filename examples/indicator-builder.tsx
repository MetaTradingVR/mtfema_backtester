/**
 * IndicatorBuilder Component
 * 
 * A streamlined interface for creating and testing custom indicators without coding.
 * This component is optimized for performance and usability.
 */

import { useState, useCallback } from 'react';
import { 
  IndicatorInfo, 
  IndicatorParameter, 
  CustomIndicatorCode,
  testIndicator, 
  createIndicator 
} from '../lib/api';

// Predefined templates to help users get started quickly
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

export interface IndicatorBuilderProps {
  onSave?: (indicator: IndicatorInfo) => void;
  onCancel?: () => void;
}

export const IndicatorBuilder = ({ onSave, onCancel }: IndicatorBuilderProps) => {
  // Main state
  const [name, setName] = useState('CustomIndicator');
  const [description, setDescription] = useState('A custom indicator');
  const [parameters, setParameters] = useState<IndicatorParameter[]>(DEFAULT_PARAMETERS);
  const [code, setCode] = useState(INDICATOR_TEMPLATES['Simple']);
  const [activeTemplate, setActiveTemplate] = useState('Simple');
  
  // Test results state
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Add a new parameter
  const addParameter = () => {
    setParameters([
      ...parameters,
      { name: `param${parameters.length + 1}`, type: 'float', default: 0 }
    ]);
  };
  
  // Remove a parameter
  const removeParameter = (index: number) => {
    setParameters(parameters.filter((_, i) => i !== index));
  };
  
  // Update parameter properties
  const updateParameter = (index: number, field: string, value: any) => {
    const updatedParams = [...parameters];
    updatedParams[index] = { ...updatedParams[index], [field]: value };
    setParameters(updatedParams);
  };
  
  // Load a template
  const loadTemplate = (templateName: string) => {
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
  };
  
  // Test the indicator
  const handleTest = async () => {
    setIsLoading(true);
    setErrorMessage('');
    setTestResults(null);
    
    try {
      const indicatorData: CustomIndicatorCode = {
        name,
        description,
        parameters,
        code,
        test_data: true,
        save: false
      };
      
      const result = await testIndicator(indicatorData);
      
      if (result.success) {
        setTestResults(result.preview);
      } else {
        setErrorMessage(result.message);
      }
    } catch (error) {
      setErrorMessage(`Error testing indicator: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Save the indicator
  const handleSave = async () => {
    setIsLoading(true);
    setErrorMessage('');
    
    try {
      const indicatorData: CustomIndicatorCode = {
        name,
        description,
        parameters,
        code,
        save: true
      };
      
      const result = await createIndicator(indicatorData);
      
      if (result.success) {
        onSave?.({
          name,
          description,
          parameters,
          output_fields: ['value'],
          built_in: false
        });
      } else {
        setErrorMessage(result.message);
      }
    } catch (error) {
      setErrorMessage(`Error saving indicator: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Custom Indicator Builder</h2>
      
      {/* Header section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Indicator Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="MyCustomIndicator"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">
            Templates
          </label>
          <select
            value={activeTemplate}
            onChange={(e) => loadTemplate(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
          >
            {Object.keys(INDICATOR_TEMPLATES).map(template => (
              <option key={template} value={template}>
                {template}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">
          Description
        </label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
          placeholder="Describe what this indicator does"
        />
      </div>
      
      {/* Parameters section */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-medium">
            Parameters
          </label>
          <button
            onClick={addParameter}
            className="px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Add Parameter
          </button>
        </div>
        
        <div className="space-y-2">
          {parameters.map((param, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 p-2 border rounded bg-gray-50 dark:bg-gray-700">
              <div className="flex-1 min-w-[120px]">
                <input
                  type="text"
                  value={param.name}
                  onChange={(e) => updateParameter(index, 'name', e.target.value)}
                  className="w-full px-2 py-1 border rounded-md text-sm"
                  placeholder="Name"
                />
              </div>
              
              <div className="w-[100px]">
                <select
                  value={param.type}
                  onChange={(e) => updateParameter(index, 'type', e.target.value)}
                  className="w-full px-2 py-1 border rounded-md text-sm"
                >
                  <option value="int">Integer</option>
                  <option value="float">Float</option>
                  <option value="string">String</option>
                  <option value="bool">Boolean</option>
                </select>
              </div>
              
              <div className="flex-1 min-w-[100px]">
                {param.type === 'string' && param.options ? (
                  <select
                    value={param.default}
                    onChange={(e) => updateParameter(index, 'default', e.target.value)}
                    className="w-full px-2 py-1 border rounded-md text-sm"
                  >
                    {param.options.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                ) : param.type === 'bool' ? (
                  <select
                    value={param.default.toString()}
                    onChange={(e) => updateParameter(index, 'default', e.target.value === 'true')}
                    className="w-full px-2 py-1 border rounded-md text-sm"
                  >
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </select>
                ) : (
                  <input
                    type={param.type === 'int' ? 'number' : param.type === 'float' ? 'number' : 'text'}
                    step={param.type === 'float' ? '0.01' : '1'}
                    value={param.default}
                    onChange={(e) => {
                      const value = param.type === 'int' ? parseInt(e.target.value) : 
                                   param.type === 'float' ? parseFloat(e.target.value) : 
                                   e.target.value;
                      updateParameter(index, 'default', value);
                    }}
                    className="w-full px-2 py-1 border rounded-md text-sm"
                    placeholder="Default value"
                  />
                )}
              </div>
              
              <button
                onClick={() => removeParameter(index)}
                className="p-1 text-red-500 hover:text-red-700"
                title="Remove parameter"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
      
      {/* Code section */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">
          Indicator Code
        </label>
        <div className="border rounded-md bg-gray-50 dark:bg-gray-900">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full px-3 py-2 font-mono text-sm bg-transparent"
            rows={15}
            spellCheck={false}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Note: This code will be executed on the server. Make sure it follows the Indicator class structure.
        </p>
      </div>
      
      {/* Feedback section */}
      {errorMessage && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-md">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}
      
      {testResults && (
        <div className="mb-4">
          <h3 className="text-sm font-medium mb-2">Test Results:</h3>
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-700 mb-2">Indicator calculated successfully!</p>
            <div className="text-xs overflow-auto max-h-40">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(testResults, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
      
      {/* Action buttons */}
      <div className="flex justify-end space-x-2 mt-4">
        {onCancel && (
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 border rounded hover:bg-gray-100"
            disabled={isLoading}
          >
            Cancel
          </button>
        )}
        
        <button
          onClick={handleTest}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          disabled={isLoading}
        >
          {isLoading ? 'Testing...' : 'Test Indicator'}
        </button>
        
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          disabled={isLoading || !!errorMessage}
        >
          {isLoading ? 'Saving...' : 'Save Indicator'}
        </button>
      </div>
    </div>
  );
};

export default IndicatorBuilder;
