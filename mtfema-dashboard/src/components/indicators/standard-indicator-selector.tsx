"use client"

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  fetchStandardIndicatorsCatalog,
  testStandardIndicator,
  saveStandardIndicator,
  type StandardIndicatorCategory,
  type StandardIndicatorDefinition,
  type StandardIndicator,
  type IndicatorParameter,
  type IndicatorTestResult
} from '@/lib/api'
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export interface SelectedStandardIndicator {
  id: string;
  definition_id: string;
  name: string;
  parameters: Record<string, any>;
  category?: string;
  source_library?: string;
}

interface StandardIndicatorSelectorProps {
  selectedIndicators: SelectedStandardIndicator[];
  onSelectIndicator: (indicator: SelectedStandardIndicator) => void;
  onRemoveIndicator: (id: string) => void;
  onUpdateIndicatorParams: (id: string, params: Record<string, any>) => void;
}

export function StandardIndicatorSelector({
  selectedIndicators,
  onSelectIndicator,
  onRemoveIndicator,
  onUpdateIndicatorParams
}: StandardIndicatorSelectorProps) {
  // State
  const [categories, setCategories] = useState<StandardIndicatorCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedIndicator, setSelectedIndicator] = useState<StandardIndicatorDefinition | null>(null);
  const [customName, setCustomName] = useState('');
  const [indicatorParams, setIndicatorParams] = useState<Record<string, any>>({});
  const [dialogOpen, setDialogOpen] = useState(false);
  const [testResult, setTestResult] = useState<IndicatorTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showTestDialog, setShowTestDialog] = useState(false);
  
  // Load standard indicators catalog
  useEffect(() => {
    const fetchIndicators = async () => {
      try {
        setLoading(true);
        setError(null); // Clear any previous errors
        
        // Use the updated API function which adds an "All" alphabetical category
        const categoriesData = await fetchStandardIndicatorsCatalog();
        
        // Debug - log how many categories and indicators we received
        console.log(`Loaded ${categoriesData.length} categories`);
        if (categoriesData.length > 0) {
          const totalIndicators = categoriesData.reduce((sum, cat) => sum + (cat.indicators?.length || 0), 0);
          console.log(`Total indicators: ${totalIndicators}`);
          
          // Log first few indicators for debugging
          if (categoriesData[0]?.indicators?.length > 0) {
            console.log('First indicator:', categoriesData[0].indicators[0]);
          }
        }
        
        setCategories(categoriesData);
        
        // If we have categories, set the active category to the first one (which should be "All")
        if (categoriesData && categoriesData.length > 0) {
          setActiveCategory(categoriesData[0].id);
        } else {
          setError("No indicator categories found");
        }
        setLoading(false);
      } catch (error) {
        console.error('Error fetching standard indicators:', error);
        setError("Failed to load indicators: " + (error instanceof Error ? error.message : String(error)));
        setCategories([]);
        setLoading(false);
      }
    };

    fetchIndicators();
  }, []);
  
  // Get indicators for the active category
  const activeIndicators = useMemo(() => {
    if (!activeCategory) return [];
    const category = categories.find(c => c.id === activeCategory);
    return category?.indicators || [];
  }, [categories, activeCategory]);
  
  // Handle selecting an indicator to configure
  const handleSelectIndicatorForConfig = (indicator: StandardIndicatorDefinition) => {
    setSelectedIndicator(indicator);
    setCustomName(indicator.name);
    
    // Initialize parameters with default values
    const params: Record<string, any> = {};
    indicator.parameters.forEach(param => {
      params[param.name] = param.default;
    });
    setIndicatorParams(params);
    
    setDialogOpen(true);
  };
  
  // Handle updating a parameter value
  const handleParamChange = (name: string, value: any) => {
    setIndicatorParams(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Test the indicator with current parameters
  const handleTestIndicator = async () => {
    if (!selectedIndicator) return;
    
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await testStandardIndicator(
        selectedIndicator.id,
        indicatorParams
      );
      
      setTestResult(result);
    } catch (err) {
      console.error('Error testing indicator:', err);
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Unknown error testing indicator'
      });
    } finally {
      setIsTesting(false);
    }
  };
  
  // Add the configured indicator
  const handleAddIndicator = () => {
    if (!selectedIndicator) return;
    
    // Create a unique ID
    const uniqueId = `${selectedIndicator.id}_${Date.now()}`;
    
    // Create the selected indicator object
    const newIndicator: SelectedStandardIndicator = {
      id: uniqueId,
      definition_id: selectedIndicator.id,
      name: customName || selectedIndicator.name,
      parameters: indicatorParams,
      category: selectedIndicator.category,
      source_library: selectedIndicator.source_library
    };
    
    // Add to selected indicators
    onSelectIndicator(newIndicator);
    
    // Close the dialog
    setDialogOpen(false);
    setSelectedIndicator(null);
    setCustomName('');
    setIndicatorParams({});
    setTestResult(null);
  };
  
  // Reset dialog state when closing
  const handleDialogOpenChange = (open: boolean) => {
    setDialogOpen(open);
    if (!open) {
      setSelectedIndicator(null);
      setCustomName('');
      setIndicatorParams({});
      setTestResult(null);
    }
  };
  
  // Render parameter input based on type
  const renderParameterInput = (
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
              id={`param-${param.name}`}
              checked={value} 
              onCheckedChange={(checked: boolean) => onChange(param.name, checked)}
            />
            <label 
              htmlFor={`param-${param.name}`}
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
  
  const handleSave = () => {
    if (!selectedIndicator || !isValidConfiguration()) {
      console.error('Invalid configuration');
      return;
    }
    
    const newIndicator: SelectedStandardIndicator = {
      id: `${selectedIndicator.id}_${Date.now()}`,
      definition_id: selectedIndicator.id,
      name: customName || selectedIndicator.name,
      parameters: indicatorParams,
      category: selectedIndicator.category,
      source_library: selectedIndicator.source_library
    };
    
    onSelectIndicator(newIndicator);
    setDialogOpen(false);
    setSelectedIndicator(null);
    setCustomName('');
    setIndicatorParams({});
    setTestResult(null);
  };
  
  const isValidConfiguration = () => {
    return selectedIndicator && customName.trim() !== '' && Object.values(indicatorParams).every(value => value !== undefined && value !== null);
  };
  
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-xl">Standard Technical Indicators</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-40">
            <LoadingSpinner size="lg" />
            <p className="ml-2 text-muted-foreground">Loading indicators...</p>
          </div>
        ) : error ? (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : categories.length > 0 ? (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Standard Indicators</h2>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowTestDialog(true)}
                  disabled={!selectedIndicator}
                >
                  Test
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSave}
                  disabled={!selectedIndicator || !isValidConfiguration()}
                >
                  Save
                </Button>
              </div>
            </div>
            
            <Tabs value={activeCategory || ''} onValueChange={setActiveCategory}>
              <TabsList className="w-full flex overflow-x-auto">
                {categories.map(category => (
                  <TabsTrigger 
                    key={category.id} 
                    value={category.id}
                    className="flex-shrink-0"
                  >
                    {category.name} ({category.indicators?.length || 0})
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {categories.map(category => (
                <TabsContent key={category.id} value={category.id} className="mt-4">
                  <div className="space-y-1">
                    <h3 className="text-sm font-medium text-muted-foreground">{category.description}</h3>
                    {category.indicators && category.indicators.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                        {category.indicators.map(indicator => (
                          <Card key={indicator.id} className="overflow-hidden">
                            <div className="p-4">
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="font-medium">{indicator.name}</h4>
                                <Badge variant="outline">{indicator.source_library}</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-4">{indicator.description}</p>
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button 
                                      variant="secondary" 
                                      size="sm"
                                      className="w-full"
                                      onClick={() => handleSelectIndicatorForConfig(indicator)}
                                    >
                                      Configure
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Configure and add this indicator</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            </div>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-6">
                        <p className="text-muted-foreground">No indicators in this category</p>
                      </div>
                    )}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
            
            {/* Selected Indicators Section */}
            <div className="mt-8">
              <h3 className="text-md font-semibold mb-4">Selected Standard Indicators</h3>
              
              {selectedIndicators.length === 0 ? (
                <div className="text-center py-3 text-muted-foreground text-sm border rounded-md">
                  No standard indicators selected. Configure an indicator from the categories above.
                </div>
              ) : (
                <Accordion type="multiple" className="w-full">
                  {selectedIndicators.map((indicator) => (
                    <AccordionItem key={indicator.id} value={indicator.id}>
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center">
                            <span>{indicator.name}</span>
                            {indicator.category && (
                              <Badge variant="outline" className="ml-2">
                                {indicator.category}
                              </Badge>
                            )}
                          </div>
                          <Badge variant="secondary" className="ml-2">
                            {indicator.source_library || 'pandas_ta'}
                          </Badge>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-4 pt-2">
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {Object.entries(indicator.parameters).map(([key, value]) => (
                              <div key={key} className="bg-gray-50 dark:bg-gray-800 p-2 rounded-md">
                                <span className="text-xs text-gray-500 block">{key}</span>
                                <span className="font-medium">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                          
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="mt-2 text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={() => onRemoveIndicator(indicator.id)}
                          >
                            Remove Indicator
                          </Button>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No standard indicators available</p>
          </div>
        )}
        
        {/* Indicator Configuration Dialog */}
        <Dialog open={dialogOpen} onOpenChange={handleDialogOpenChange}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Configure {selectedIndicator?.name}</DialogTitle>
              <DialogDescription>
                Customize the indicator parameters and test before adding
              </DialogDescription>
            </DialogHeader>
            
            {selectedIndicator && (
              <div className="space-y-6 py-4">
                <div className="space-y-2">
                  <Label htmlFor="indicator-name">Indicator Name</Label>
                  <Input
                    id="indicator-name"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    placeholder={selectedIndicator.name}
                  />
                  <p className="text-sm text-muted-foreground">
                    Custom name for this configured indicator
                  </p>
                </div>
                
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Parameters</h4>
                  
                  {selectedIndicator.parameters.length === 0 ? (
                    <p className="text-sm text-muted-foreground">This indicator has no configurable parameters</p>
                  ) : (
                    <div className="space-y-4">
                      {selectedIndicator.parameters.map((param) => (
                        <div key={param.name} className="grid grid-cols-3 gap-4 items-center">
                          <Label htmlFor={`param-${param.name}`} className="text-sm col-span-1">
                            {param.name}
                            {param.description && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <span className="ml-1 cursor-help text-muted-foreground">ⓘ</span>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="max-w-xs">{param.description}</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                          </Label>
                          
                          <div className="col-span-2">
                            {renderParameterInput(
                              param,
                              indicatorParams[param.name],
                              handleParamChange
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Test Results Section */}
                {testResult && (
                  <div className="mt-4 p-4 border rounded-md bg-gray-50 dark:bg-gray-800">
                    <h4 className="text-sm font-medium mb-2">Test Results</h4>
                    
                    {testResult.success ? (
                      <div className="text-green-600 dark:text-green-400 text-sm">
                        Indicator tested successfully
                      </div>
                    ) : (
                      <div className="text-red-600 dark:text-red-400 text-sm">
                        {testResult.message}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            
            <DialogFooter className="flex items-center justify-between gap-2 sm:justify-between">
              <Button
                type="button"
                variant="outline"
                disabled={isTesting || !selectedIndicator}
                onClick={handleTestIndicator}
              >
                {isTesting ? "Testing..." : "Test Indicator"}
              </Button>
              
              <div className="flex gap-2">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button 
                  type="button" 
                  onClick={handleAddIndicator}
                  disabled={!selectedIndicator || customName.trim() === ''}
                >
                  Add Indicator
                </Button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
} 