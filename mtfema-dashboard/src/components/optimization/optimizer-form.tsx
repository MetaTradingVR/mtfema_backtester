"use client";

import { useState, useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  fetchOptimizationMethods, 
  runOptimization, 
  fetchOptimizationStatus, 
  OptimizationMethod 
} from "@/lib/api";
import { Loader2 } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";

// Form schema
const formSchema = z.object({
  symbol: z.string().min(1, { message: "Symbol is required" }),
  timeframe: z.string().min(1, { message: "Timeframe is required" }),
  start_date: z.string().min(1, { message: "Start date is required" }),
  end_date: z.string().min(1, { message: "End date is required" }),
  metric: z.string().min(1, { message: "Optimization metric is required" }),
  method: z.string().min(1, { message: "Optimization method is required" }),
  iterations: z.coerce.number().optional(),
  surrogate_model: z.string().optional(),
  acq_func: z.string().optional(),
  n_initial_points: z.coerce.number().optional(),
  // Parameter ranges
  ema_period_min: z.coerce.number().min(1),
  ema_period_max: z.coerce.number().min(1),
  ema_period_step: z.coerce.number().min(1).default(1),
  extension_threshold_min: z.coerce.number().min(0.1),
  extension_threshold_max: z.coerce.number().min(0.1),
  extension_threshold_step: z.coerce.number().min(0.1).default(0.1),
  // Optional parameters (can be enabled/disabled)
  include_stop_loss: z.boolean().default(false),
  stop_loss_min: z.coerce.number().optional(),
  stop_loss_max: z.coerce.number().optional(),
  stop_loss_step: z.coerce.number().optional(),
  include_take_profit: z.boolean().default(false),
  take_profit_min: z.coerce.number().optional(),
  take_profit_max: z.coerce.number().optional(),
  take_profit_step: z.coerce.number().optional(),
  include_reward_risk: z.boolean().default(false),
  reward_risk_min: z.coerce.number().optional(),
  reward_risk_max: z.coerce.number().optional(),
  reward_risk_step: z.coerce.number().optional(),
});

// Props
interface OptimizerFormProps {
  onComplete: (optimizationId: string) => void;
}

export function OptimizerForm({ onComplete }: OptimizerFormProps) {
  const [optimizationMethods, setOptimizationMethods] = useState<Record<string, OptimizationMethod>>({});
  const [isLoadingMethods, setIsLoadingMethods] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeOptimizationId, setActiveOptimizationId] = useState<string | null>(null);
  const [optimizationStatus, setOptimizationStatus] = useState<{ status: string; progress: number; eta_minutes?: number } | null>(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);

  // Initialize form
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      symbol: "NQ",
      timeframe: "15m",
      start_date: "2023-01-01",
      end_date: "2023-12-31",
      metric: "total_return",
      method: "grid",
      ema_period_min: 5,
      ema_period_max: 15,
      ema_period_step: 1,
      extension_threshold_min: 0.5,
      extension_threshold_max: 1.5,
      extension_threshold_step: 0.1,
      include_stop_loss: false,
      include_take_profit: false,
      include_reward_risk: false,
    },
  });

  // Watch method to show/hide relevant fields
  const method = form.watch("method");

  // Load optimization methods on component mount
  useEffect(() => {
    async function loadOptimizationMethods() {
      try {
        setIsLoadingMethods(true);
        const methods = await fetchOptimizationMethods();
        setOptimizationMethods(methods);
      } catch (error) {
        console.error("Failed to load optimization methods:", error);
      } finally {
        setIsLoadingMethods(false);
      }
    }

    loadOptimizationMethods();
  }, []);

  // Check optimization status
  useEffect(() => {
    if (!activeOptimizationId) return;

    // Set up interval to check status
    const interval = setInterval(async () => {
      try {
        const status = await fetchOptimizationStatus(activeOptimizationId);
        if (status) {
          setOptimizationStatus({
            status: status.status,
            progress: status.progress || 0,
            eta_minutes: status.eta_minutes
          });

          // If completed, clear interval and call onComplete
          if (status.status === "completed" || status.status === "error") {
            clearInterval(interval);
            setStatusCheckInterval(null);
            setIsSubmitting(false);
            
            if (status.status === "completed") {
              onComplete(activeOptimizationId);
            }
          }
        }
      } catch (error) {
        console.error("Failed to check optimization status:", error);
      }
    }, 2000);

    setStatusCheckInterval(interval);

    // Clean up interval on unmount
    return () => {
      clearInterval(interval);
    };
  }, [activeOptimizationId, onComplete]);

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      setIsSubmitting(true);

      // Build param ranges from form values
      const param_ranges: Record<string, any> = {
        ema_period: {
          min: values.ema_period_min,
          max: values.ema_period_max,
          step: values.ema_period_step
        },
        extension_threshold: {
          min: values.extension_threshold_min,
          max: values.extension_threshold_max,
          step: values.extension_threshold_step
        }
      };

      // Add optional parameters if included
      if (values.include_stop_loss && values.stop_loss_min && values.stop_loss_max) {
        param_ranges.stop_loss = {
          min: values.stop_loss_min,
          max: values.stop_loss_max,
          step: values.stop_loss_step || 0.1
        };
      }

      if (values.include_take_profit && values.take_profit_min && values.take_profit_max) {
        param_ranges.take_profit = {
          min: values.take_profit_min,
          max: values.take_profit_max,
          step: values.take_profit_step || 0.2
        };
      }
      
      if (values.include_reward_risk && values.reward_risk_min && values.reward_risk_max) {
        param_ranges.reward_risk_ratio = {
          min: values.reward_risk_min,
          max: values.reward_risk_max,
          step: values.reward_risk_step || 0.1
        };
      }

      // Create optimization parameters
      const optimizationParams = {
        symbol: values.symbol,
        timeframe: values.timeframe,
        start_date: values.start_date,
        end_date: values.end_date,
        param_ranges,
        metric: values.metric,
        method: values.method,
        iterations: values.iterations,
        surrogate_model: values.surrogate_model,
        acq_func: values.acq_func,
        n_initial_points: values.n_initial_points
      };

      // Run optimization
      const response = await runOptimization(optimizationParams);
      setActiveOptimizationId(response.id);
      setOptimizationStatus({ status: "queued", progress: 0 });

    } catch (error) {
      console.error("Failed to start optimization:", error);
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      {activeOptimizationId && optimizationStatus ? (
        <Card className="p-4">
          <CardContent className="pt-4">
            <h3 className="text-lg font-medium mb-4">Optimization in Progress</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span>Status: {optimizationStatus.status}</span>
                  <span>{Math.round(optimizationStatus.progress)}%</span>
                </div>
                <Progress value={optimizationStatus.progress} className="h-2" />
              </div>
              
              {optimizationStatus.eta_minutes !== undefined && (
                <p className="text-sm text-muted-foreground">
                  Estimated time remaining: {Math.round(optimizationStatus.eta_minutes)} minutes
                </p>
              )}
              
              <Button 
                variant="outline" 
                onClick={() => {
                  if (statusCheckInterval) clearInterval(statusCheckInterval);
                  setActiveOptimizationId(null);
                  setOptimizationStatus(null);
                  setIsSubmitting(false);
                }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="symbol"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Symbol</FormLabel>
                    <FormControl>
                      <Input placeholder="NQ" {...field} />
                    </FormControl>
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
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select timeframe" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="5m">5 minutes</SelectItem>
                        <SelectItem value="15m">15 minutes</SelectItem>
                        <SelectItem value="30m">30 minutes</SelectItem>
                        <SelectItem value="1h">1 hour</SelectItem>
                        <SelectItem value="4h">4 hours</SelectItem>
                        <SelectItem value="1d">1 day</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
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
              
              <FormField
                control={form.control}
                name="metric"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Optimization Metric</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select metric" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="total_return">Total Return</SelectItem>
                        <SelectItem value="sharpe_ratio">Sharpe Ratio</SelectItem>
                        <SelectItem value="win_rate">Win Rate</SelectItem>
                        <SelectItem value="profit_factor">Profit Factor</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="method"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Optimization Method</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select method" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="grid">Grid Search</SelectItem>
                        <SelectItem value="random">Random Search</SelectItem>
                        <SelectItem value="bayesian">Bayesian Optimization</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      {isLoadingMethods ? (
                        "Loading method descriptions..."
                      ) : (
                        optimizationMethods[field.value]?.description || 
                        "Grid search explores all combinations. Random search samples the space. Bayesian optimization learns from previous evaluations."
                      )}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            
            {/* Method-specific options */}
            {method === "random" && (
              <FormField
                control={form.control}
                name="iterations"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Number of Iterations</FormLabel>
                    <FormControl>
                      <Input type="number" min={10} {...field} />
                    </FormControl>
                    <FormDescription>
                      Number of random parameter combinations to evaluate
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
            
            {method === "bayesian" && (
              <div className="space-y-4">
                <FormField
                  control={form.control}
                  name="iterations"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Number of Iterations</FormLabel>
                      <FormControl>
                        <Input type="number" min={10} {...field} />
                      </FormControl>
                      <FormDescription>
                        Total number of evaluations including initial points
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="surrogate_model"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Surrogate Model</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value || "GP"}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select model" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="GP">Gaussian Process (GP)</SelectItem>
                          <SelectItem value="RF">Random Forest (RF)</SelectItem>
                          <SelectItem value="GBRT">Gradient Boosted Trees (GBRT)</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        GP works best for smooth functions, RF for noisy data, GBRT for complex patterns
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="acq_func"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Acquisition Function</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value || "EI"}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select function" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="EI">Expected Improvement (EI)</SelectItem>
                          <SelectItem value="PI">Probability of Improvement (PI)</SelectItem>
                          <SelectItem value="LCB">Lower Confidence Bound (LCB)</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        EI balances exploration/exploitation, PI is more greedy, LCB is more exploratory
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="n_initial_points"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Initial Points</FormLabel>
                      <FormControl>
                        <Input type="number" min={5} {...field} />
                      </FormControl>
                      <FormDescription>
                        Number of random evaluations before using the surrogate model
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}
            
            {/* Parameter Ranges */}
            <div className="space-y-6">
              <h3 className="text-lg font-medium">Parameter Ranges</h3>
              
              <Card className="p-4">
                <CardContent className="p-0">
                  <h4 className="font-medium mb-4">EMA Period</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="ema_period_min"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Min</FormLabel>
                          <FormControl>
                            <Input type="number" min={1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="ema_period_max"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Max</FormLabel>
                          <FormControl>
                            <Input type="number" min={1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="ema_period_step"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Step</FormLabel>
                          <FormControl>
                            <Input type="number" min={1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="p-4">
                <CardContent className="p-0">
                  <h4 className="font-medium mb-4">Extension Threshold</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="extension_threshold_min"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Min</FormLabel>
                          <FormControl>
                            <Input type="number" min={0.1} step={0.1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="extension_threshold_max"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Max</FormLabel>
                          <FormControl>
                            <Input type="number" min={0.1} step={0.1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="extension_threshold_step"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Step</FormLabel>
                          <FormControl>
                            <Input type="number" min={0.1} step={0.1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>
              
              {/* Optional Parameters */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Optional Parameters</h3>
                
                <Card className="p-4">
                  <CardContent className="p-0">
                    <div className="flex justify-between items-center mb-4">
                      <h4 className="font-medium">Stop Loss</h4>
                      <FormField
                        control={form.control}
                        name="include_stop_loss"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2 space-y-0">
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                    </div>
                    
                    {form.watch("include_stop_loss") && (
                      <div className="grid grid-cols-3 gap-4">
                        <FormField
                          control={form.control}
                          name="stop_loss_min"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Min</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="stop_loss_max"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Max</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="stop_loss_step"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Step</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
                
                <Card className="p-4">
                  <CardContent className="p-0">
                    <div className="flex justify-between items-center mb-4">
                      <h4 className="font-medium">Take Profit</h4>
                      <FormField
                        control={form.control}
                        name="include_take_profit"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2 space-y-0">
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                    </div>
                    
                    {form.watch("include_take_profit") && (
                      <div className="grid grid-cols-3 gap-4">
                        <FormField
                          control={form.control}
                          name="take_profit_min"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Min</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="take_profit_max"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Max</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="take_profit_step"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Step</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
                
                <Card className="p-4">
                  <CardContent className="p-0">
                    <div className="flex justify-between items-center mb-4">
                      <h4 className="font-medium">Reward/Risk Ratio</h4>
                      <FormField
                        control={form.control}
                        name="include_reward_risk"
                        render={({ field }) => (
                          <FormItem className="flex items-center space-x-2 space-y-0">
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                    </div>
                    
                    {form.watch("include_reward_risk") && (
                      <div className="grid grid-cols-3 gap-4">
                        <FormField
                          control={form.control}
                          name="reward_risk_min"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Min</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="reward_risk_max"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Max</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="reward_risk_step"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Step</FormLabel>
                              <FormControl>
                                <Input type="number" min={0.1} step={0.1} {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
            
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Optimization...
                </>
              ) : (
                "Run Optimization"
              )}
            </Button>
          </form>
        </Form>
      )}
    </div>
  );
} 