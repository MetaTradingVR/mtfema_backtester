"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { fetchIndicators, CustomIndicator, IndicatorParameter } from '@/lib/api'

export interface SelectedIndicator {
  id: string;
  name: string;
  parameters: Record<string, any>;
}

interface IndicatorSelectorProps {
  selectedIndicators: SelectedIndicator[];
  onSelectIndicator: (indicator: SelectedIndicator) => void;
  onRemoveIndicator: (id: string) => void;
  onUpdateIndicatorParams: (id: string, params: Record<string, any>) => void;
}

export function IndicatorSelector({
  selectedIndicators,
  onSelectIndicator,
  onRemoveIndicator,
  onUpdateIndicatorParams
}: IndicatorSelectorProps) {
  const [indicators, setIndicators] = useState<CustomIndicator[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");

  // Load available indicators
  useEffect(() => {
    const loadIndicators = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const data = await fetchIndicators();
        setIndicators(data);
      } catch (err) {
        setError('Failed to load indicators');
        console.error('Error loading indicators:', err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadIndicators();
  }, []);

  // Handle adding an indicator to the selected list
  const handleAddIndicator = () => {
    if (!selectedId) return;
    
    const indicator = indicators.find(ind => ind.id === selectedId);
    if (!indicator) return;
    
    // Check if already selected
    if (selectedIndicators.some(ind => ind.id === selectedId)) {
      return; // Already selected
    }
    
    // Create default parameters from indicator definition
    const defaultParams: Record<string, any> = {};
    indicator.parameters.forEach(param => {
      defaultParams[param.name] = param.default;
    });
    
    // Add to selected indicators
    onSelectIndicator({
      id: indicator.id || '',
      name: indicator.name,
      parameters: defaultParams
    });
    
    // Reset selection
    setSelectedId("");
  };

  // Render parameter input based on type
  const renderParameterInput = (
    indicator: SelectedIndicator,
    param: IndicatorParameter,
    value: any,
    onChange: (name: string, value: any) => void
  ) => {
    switch (param.type) {
      case 'int':
        return (
          <Input
            type="number"
            value={value}
            min={param.min}
            max={param.max}
            step={1}
            onChange={(e) => onChange(param.name, parseInt(e.target.value))}
            className="w-full"
          />
        );
      case 'float':
        return (
          <Input
            type="number"
            value={value}
            min={param.min}
            max={param.max}
            step={0.01}
            onChange={(e) => onChange(param.name, parseFloat(e.target.value))}
            className="w-full"
          />
        );
      case 'string':
        if (param.options && param.options.length > 0) {
          return (
            <Select 
              value={value} 
              onValueChange={(val) => onChange(param.name, val)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select option" />
              </SelectTrigger>
              <SelectContent>
                {param.options.map(option => (
                  <SelectItem key={option} value={option}>{option}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        } else {
          return (
            <Input
              type="text"
              value={value}
              onChange={(e) => onChange(param.name, e.target.value)}
              className="w-full"
            />
          );
        }
      case 'bool':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox 
              id={`${indicator.id}-${param.name}`}
              checked={value} 
              onCheckedChange={(checked) => onChange(param.name, !!checked)}
            />
            <label 
              htmlFor={`${indicator.id}-${param.name}`}
              className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {param.name}
            </label>
          </div>
        );
      default:
        return (
          <Input
            type="text"
            value={value}
            onChange={(e) => onChange(param.name, e.target.value)}
            className="w-full"
          />
        );
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-xl">Custom Indicators</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="mb-6">
          <div className="flex gap-2 mb-4">
            <Select
              value={selectedId}
              onValueChange={setSelectedId}
              disabled={isLoading}
              className="flex-1"
            >
              <SelectTrigger>
                <SelectValue placeholder="Select an indicator" />
              </SelectTrigger>
              <SelectContent>
                {indicators.map(indicator => (
                  <SelectItem 
                    key={indicator.id} 
                    value={indicator.id || ''}
                    disabled={selectedIndicators.some(ind => ind.id === indicator.id)}
                  >
                    {indicator.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleAddIndicator} disabled={!selectedId}>
              Add
            </Button>
          </div>
          
          {selectedIndicators.length === 0 ? (
            <div className="text-center py-3 text-muted-foreground text-sm border rounded-md">
              No indicators selected. Select indicators to include in backtest.
            </div>
          ) : (
            <Accordion type="multiple" className="w-full">
              {selectedIndicators.map((indicator) => {
                // Find the full indicator definition to get parameter metadata
                const indicatorDef = indicators.find(ind => ind.id === indicator.id);
                
                return (
                  <AccordionItem key={indicator.id} value={indicator.id}>
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center justify-between w-full">
                        <span>{indicator.name}</span>
                        <Badge variant="outline" className="ml-2">
                          {Object.keys(indicator.parameters).length} params
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      {indicatorDef ? (
                        <div className="space-y-4 pt-2">
                          {indicatorDef.parameters.map((param) => (
                            <div key={param.name} className="grid grid-cols-2 gap-4 items-center">
                              <Label htmlFor={`${indicator.id}-${param.name}`} className="text-sm">
                                {param.name} 
                                {param.description && (
                                  <span className="text-xs text-muted-foreground ml-1">
                                    ({param.description})
                                  </span>
                                )}
                              </Label>
                              
                              {renderParameterInput(
                                indicator,
                                param,
                                indicator.parameters[param.name],
                                (name, value) => {
                                  const updatedParams = {
                                    ...indicator.parameters,
                                    [name]: value
                                  };
                                  onUpdateIndicatorParams(indicator.id, updatedParams);
                                }
                              )}
                            </div>
                          ))}
                          
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="mt-2 text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={() => onRemoveIndicator(indicator.id)}
                          >
                            Remove Indicator
                          </Button>
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground py-2">
                          Error: Could not find indicator definition
                        </div>
                      )}
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          )}
        </div>
      </CardContent>
    </Card>
  );
} 