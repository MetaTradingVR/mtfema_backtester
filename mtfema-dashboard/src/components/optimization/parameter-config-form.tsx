"use client";

import { useState } from "react";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { 
  Form, 
  FormControl, 
  FormDescription, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormMessage 
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { PlusCircle, MinusCircle, HelpCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

// Define the schema for a parameter range
const paramRangeSchema = z.object({
  name: z.string(),
  displayName: z.string(),
  description: z.string(),
  enabled: z.boolean().default(true),
  min: z.number(),
  max: z.number(),
  step: z.number().min(0.00001),
  default: z.number().optional(),
  isInteger: z.boolean().default(false),
});

// Define the overall parameter configuration schema
const paramConfigSchema = z.object({
  parameters: z.array(paramRangeSchema)
});

type ParameterRange = z.infer<typeof paramRangeSchema>;
type ParameterConfig = z.infer<typeof paramConfigSchema>;

// Define props for the component
interface ParameterConfigFormProps {
  onSubmit: (paramRanges: Record<string, any>) => void;
  defaultParameters?: ParameterRange[];
  isSubmitting?: boolean;
}

export function ParameterConfigForm({ 
  onSubmit, 
  defaultParameters = [], 
  isSubmitting = false 
}: ParameterConfigFormProps) {
  const [parameters, setParameters] = useState<ParameterRange[]>(
    defaultParameters.length > 0 ? defaultParameters : [
      {
        name: "ema_period",
        displayName: "EMA Period",
        description: "The period used for the exponential moving average calculation",
        enabled: true,
        min: 5,
        max: 15,
        step: 1,
        default: 9,
        isInteger: true
      },
      {
        name: "extension_threshold",
        displayName: "Extension Threshold",
        description: "The threshold for determining price extensions from the EMA",
        enabled: true,
        min: 0.5,
        max: 1.5,
        step: 0.1,
        default: 1.0,
        isInteger: false
      },
      {
        name: "stop_loss",
        displayName: "Stop Loss",
        description: "Stop loss percentage from entry price",
        enabled: false,
        min: 0.5,
        max: 2.0,
        step: 0.1,
        default: 1.0,
        isInteger: false
      },
      {
        name: "take_profit",
        displayName: "Take Profit",
        description: "Take profit percentage from entry price",
        enabled: false,
        min: 1.0,
        max: 3.0,
        step: 0.2,
        default: 2.0,
        isInteger: false
      },
      {
        name: "reward_risk_ratio",
        displayName: "Reward/Risk Ratio",
        description: "The ratio of potential reward to risk for trade sizing",
        enabled: false,
        min: 1.0,
        max: 3.0,
        step: 0.1,
        default: 2.0,
        isInteger: false
      }
    ]
  );

  // Configure the form with default values
  const form = useForm<ParameterConfig>({
    resolver: zodResolver(paramConfigSchema),
    defaultValues: {
      parameters
    },
    values: {
      parameters
    }
  });

  // Create a new parameter
  const addParameter = () => {
    const newParam: ParameterRange = {
      name: `param_${parameters.length + 1}`,
      displayName: `Parameter ${parameters.length + 1}`,
      description: "Custom parameter",
      enabled: true,
      min: 0,
      max: 10,
      step: 1,
      isInteger: true
    };

    setParameters([...parameters, newParam]);
  };

  // Remove a parameter
  const removeParameter = (index: number) => {
    const newParams = [...parameters];
    newParams.splice(index, 1);
    setParameters(newParams);
  };

  // Toggle parameter enabled/disabled
  const toggleParameter = (index: number, enabled: boolean) => {
    const newParams = [...parameters];
    newParams[index].enabled = enabled;
    setParameters(newParams);
  };

  // Update parameter values
  const updateParameter = (index: number, field: keyof ParameterRange, value: any) => {
    const newParams = [...parameters];
    newParams[index][field] = value;
    
    // Handle min/max relationship
    if (field === 'min' && newParams[index].max < value) {
      newParams[index].max = value;
    } else if (field === 'max' && newParams[index].min > value) {
      newParams[index].min = value;
    }

    // Integer parameters need integer step
    if (field === 'isInteger' && value === true) {
      newParams[index].step = 1;
    }
    
    setParameters(newParams);
  };

  // Handle form submission
  const handleSubmit = () => {
    // Build parameter ranges for optimization
    const paramRanges: Record<string, any> = {};
    
    parameters.forEach(param => {
      if (param.enabled) {
        paramRanges[param.name] = {
          min: param.min,
          max: param.max,
          step: param.step
        };
      }
    });

    onSubmit(paramRanges);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Parameter Configuration</CardTitle>
          <CardDescription>
            Configure the parameters to optimize
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="multiple" className="w-full">
            {parameters.map((param, index) => (
              <AccordionItem key={index} value={`param-${index}`}>
                <AccordionTrigger className="py-2">
                  <div className="flex items-center justify-between w-full pr-4">
                    <div className="flex items-center">
                      <Switch 
                        checked={param.enabled} 
                        onCheckedChange={(checked) => toggleParameter(index, checked)}
                        className="mr-2"
                      />
                      <span className={param.enabled ? "font-medium" : "font-medium text-muted-foreground"}>
                        {param.displayName}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {param.enabled && `[${param.min} to ${param.max}, step: ${param.step}]`}
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pt-2">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Parameter Name</Label>
                        <Input 
                          type="text" 
                          value={param.displayName}
                          onChange={(e) => updateParameter(index, 'displayName', e.target.value)}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>
                          <div className="flex items-center">
                            Internal Name
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <HelpCircle className="ml-1 h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  Internal parameter name used in the strategy code
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </div>
                        </Label>
                        <Input 
                          type="text" 
                          value={param.name}
                          onChange={(e) => updateParameter(index, 'name', e.target.value)}
                          className="w-full"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Description</Label>
                      <Input 
                        type="text" 
                        value={param.description}
                        onChange={(e) => updateParameter(index, 'description', e.target.value)}
                        className="w-full"
                      />
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>Minimum Value</Label>
                        <Input 
                          type="number" 
                          value={param.min}
                          onChange={(e) => updateParameter(index, 'min', parseFloat(e.target.value))}
                          step={param.isInteger ? 1 : 0.1}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Maximum Value</Label>
                        <Input 
                          type="number" 
                          value={param.max}
                          onChange={(e) => updateParameter(index, 'max', parseFloat(e.target.value))}
                          step={param.isInteger ? 1 : 0.1}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Step Size</Label>
                        <Input 
                          type="number" 
                          value={param.step}
                          onChange={(e) => updateParameter(index, 'step', parseFloat(e.target.value))}
                          step={0.01}
                          min={0.01}
                          className="w-full"
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 pt-2">
                      <Switch 
                        checked={param.isInteger} 
                        onCheckedChange={(checked) => updateParameter(index, 'isInteger', checked)}
                        id={`integer-${index}`}
                      />
                      <Label htmlFor={`integer-${index}`}>Integer values only</Label>
                      
                      <div className="ml-auto">
                        <Button 
                          variant="destructive" 
                          size="sm"
                          onClick={() => removeParameter(index)}
                          disabled={parameters.length <= 1}
                        >
                          <MinusCircle className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      </div>
                    </div>
                    
                    {param.enabled && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span>Range Preview</span>
                            <span className="text-muted-foreground">
                              {param.isInteger 
                                ? `${Math.ceil((param.max - param.min) / param.step) + 1} values`
                                : `${Math.ceil((param.max - param.min) / param.step) + 1} values`}
                            </span>
                          </div>
                          <div className="h-8 relative">
                            <Slider
                              value={[param.min, param.max]}
                              min={param.min - (param.max - param.min) * 0.2}
                              max={param.max + (param.max - param.min) * 0.2}
                              step={param.step}
                              className="mt-2"
                              disabled
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
          
          <div className="mt-6 flex justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={addParameter}
              disabled={isSubmitting}
            >
              <PlusCircle className="h-4 w-4 mr-1" />
              Add Parameter
            </Button>
            
            <Button 
              type="button" 
              onClick={handleSubmit}
              disabled={isSubmitting || parameters.filter(p => p.enabled).length === 0}
            >
              {isSubmitting ? "Processing..." : "Apply Parameters"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper Label component 
function Label({ children, htmlFor }: { children: React.ReactNode; htmlFor?: string }) {
  return (
    <div className="text-sm font-medium text-foreground mb-1.5" {...(htmlFor && { htmlFor })}>
      {children}
    </div>
  );
}
