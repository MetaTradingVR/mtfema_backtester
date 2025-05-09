"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { IndicatorBuilder } from "@/components/indicators/indicator-builder";
import { SimpleServerIndicator } from "@/components/simple-server-indicator";
import { PageHeader } from "@/components/page-header";
import { fetchIndicatorById, updateIndicator, testIndicator, CustomIndicator, IndicatorTestRequest } from '@/lib/api';

export default function IndicatorDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [indicator, setIndicator] = useState<CustomIndicator | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("edit");

  // Load indicator on initial render
  useEffect(() => {
    loadIndicator();
  }, [params.id]);

  // Function to load indicator from API
  const loadIndicator = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchIndicatorById(params.id);
      
      if (data) {
        setIndicator(data);
      } else {
        setError('Indicator not found. It may have been deleted.');
      }
    } catch (err) {
      setError('Failed to load indicator. Please try again later.');
      console.error('Error loading indicator:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle indicator update
  const handleUpdateIndicator = async (indicatorData: CustomIndicator) => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      // Use the API function to update
      const result = await updateIndicator(params.id, indicatorData);
      
      if (result.success) {
        setSuccessMessage('Indicator updated successfully!');
        // Update local state with new data
        setIndicator(indicatorData);
        // Show success message temporarily
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        setError(result.message);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(`Error updating indicator: ${err.message}`);
      } else {
        setError('An unknown error occurred while updating the indicator');
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Handle running an indicator test
  const handleTestIndicator = async () => {
    if (!indicator) return;
    
    setIsSaving(true);
    setError(null);
    
    try {
      // Prepare test request
      const testRequest: IndicatorTestRequest = {
        name: indicator.name,
        description: indicator.description,
        parameters: indicator.parameters,
        code: indicator.code,
        test_data: true,
        save: false,
        include_price: true
      };
      
      // Use API function to test
      const result = await testIndicator(testRequest);
      
      if (result.success) {
        setSuccessMessage('Test completed successfully!');
        // Switch to test results tab
        setActiveTab('test');
      } else {
        setError(`Test failed: ${result.message}`);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(`Error testing indicator: ${err.message}`);
      } else {
        setError('An unknown error occurred while testing the indicator');
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Handle navigating back to indicators list
  const handleBack = () => {
    router.push('/indicators');
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <PageHeader
          heading={indicator ? `Edit: ${indicator.name}` : 'Edit Indicator'}
          text="Modify and test your custom indicator."
        />
        <SimpleServerIndicator />
      </div>
      
      <div className="mb-4">
        <Button variant="outline" onClick={handleBack}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to Indicators
        </Button>
      </div>
      
      {/* Error Message */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {/* Success Message */}
      {successMessage && (
        <Alert className="mb-6 bg-green-50 border-green-300 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-100">
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      )}
      
      {/* Loading State */}
      {isLoading ? (
        <Card>
          <CardContent className="flex justify-center items-center h-40">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </CardContent>
        </Card>
      ) : indicator ? (
        <div className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="mb-6">
                  <TabsTrigger value="edit">Edit</TabsTrigger>
                  <TabsTrigger value="test">Test Results</TabsTrigger>
                  <TabsTrigger value="usage">Usage Examples</TabsTrigger>
                </TabsList>
                
                <TabsContent value="edit">
                  <IndicatorBuilder 
                    onSave={handleUpdateIndicator}
                    onCancel={handleBack}
                    initialData={indicator}
                  />
                </TabsContent>
                
                <TabsContent value="test">
                  <div className="text-center py-12">
                    <h2 className="text-2xl font-bold mb-4">Indicator Testing</h2>
                    <p className="text-gray-500 mb-6">Run tests to verify your indicator's behavior with real market data.</p>
                    
                    <Button onClick={handleTestIndicator} disabled={isSaving}>
                      {isSaving ? "Running Test..." : "Run Test"}
                    </Button>
                    
                    <div className="mt-8 text-sm text-gray-500">
                      <p>Test results will appear here after running a test.</p>
                      <p>Tests use real historical data to validate your indicator's calculation.</p>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="usage">
                  <div className="space-y-6">
                    <div className="border rounded-md p-6 bg-gray-50 dark:bg-gray-800">
                      <h3 className="text-lg font-medium mb-4">Using This Indicator in Strategies</h3>
                      
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium mb-2">Python Usage:</h4>
                          <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
{`from mtfema_backtester.utils.indicators import create_indicator

# Create indicator instance
${indicator.name.toLowerCase()} = create_indicator("${indicator.name}")

# Calculate indicator values
results = ${indicator.name.toLowerCase()}.calculate(price_data)

# Access results
${indicator.name.toLowerCase()}_values = results["${indicator.name}_value"]`}
                          </pre>
                        </div>
                        
                        <div>
                          <h4 className="font-medium mb-2">Strategy Integration:</h4>
                          <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
{`def generate_signals(data, params):
    # Create indicator
    ${indicator.name.toLowerCase()} = create_indicator("${indicator.name}")
    
    # Calculate indicator
    ${indicator.name.toLowerCase()}_results = ${indicator.name.toLowerCase()}.calculate(data)
    
    # Generate signals based on indicator values
    signals = []
    
    for i in range(1, len(data)):
        if ${indicator.name.toLowerCase()}_results["${indicator.name}_value"].iloc[i] > some_threshold:
            signals.append({"type": "BUY", "price": data["close"].iloc[i], "index": i})
            
    return signals`}
                          </pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <AlertTitle className="text-lg mb-2">Indicator Not Found</AlertTitle>
            <AlertDescription className="mb-6">
              The requested indicator could not be found. It may have been deleted.
            </AlertDescription>
            <Button onClick={handleBack}>
              Return to Indicators List
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 