"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { SimpleServerIndicator } from "@/components/simple-server-indicator"
import { IndicatorBuilder } from "@/components/indicators/indicator-builder"
import { StandardIndicatorSelector, SelectedStandardIndicator } from "@/components/indicators/standard-indicator-selector"
import { fetchIndicators, deleteIndicator, CustomIndicator, saveStandardIndicator } from '@/lib/api'
import { PageHeader } from "@/components/page-header"

export default function IndicatorsPage() {
  const router = useRouter()
  const [indicators, setIndicators] = useState<CustomIndicator[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [showConfirmDelete, setShowConfirmDelete] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('custom')
  
  // State for standard indicators
  const [selectedStandardIndicators, setSelectedStandardIndicators] = useState<SelectedStandardIndicator[]>([])
  const [standardIndicatorSuccess, setStandardIndicatorSuccess] = useState<string | null>(null)
  const [standardIndicatorError, setStandardIndicatorError] = useState<string | null>(null)

  // Load indicators on initial render
  useEffect(() => {
    loadIndicators()
  }, [])
  
  // Reset success/error messages when tab changes
  useEffect(() => {
    setStandardIndicatorSuccess(null)
    setStandardIndicatorError(null)
    setError(null)
  }, [activeTab])

  // Function to load indicators from the API
  const loadIndicators = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const data = await fetchIndicators()
      setIndicators(data)
    } catch (err) {
      setError('Failed to load indicators. Please try again later.')
      console.error('Error loading indicators:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Filter indicators based on search term
  const filteredIndicators = indicators.filter(indicator => 
    indicator.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (indicator.description && indicator.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // Handle creating a new indicator
  const handleCreateIndicator = async (indicator: CustomIndicator) => {
    // Add the new indicator to the list
    setIndicators(prev => [...prev, indicator])
    setIsCreatingNew(false)
    // Refresh the list to get the server-generated ID
    await loadIndicators()
  }

  // Handle indicator deletion
  const handleDeleteIndicator = async (id: string) => {
    setIsDeleting(true)
    setDeleteError(null)
    
    try {
      const result = await deleteIndicator(id)
      
      if (result.success) {
        // Remove from the list
        setIndicators(prev => prev.filter(ind => ind.id !== id))
        setShowConfirmDelete(null)
      } else {
        setDeleteError(result.message)
      }
    } catch (err) {
      if (err instanceof Error) {
        setDeleteError(`Error deleting indicator: ${err.message}`)
      } else {
        setDeleteError('An unknown error occurred while deleting the indicator')
      }
    } finally {
      setIsDeleting(false)
    }
  }
  
  // Handle standard indicator selection
  const handleSelectStandardIndicator = (indicator: SelectedStandardIndicator) => {
    setSelectedStandardIndicators(prev => [...prev, indicator])
    setStandardIndicatorSuccess(`Added ${indicator.name} to your selection`)
    
    // Reset success message after 3 seconds
    setTimeout(() => {
      setStandardIndicatorSuccess(null)
    }, 3000)
  }
  
  // Handle saving a standard indicator
  const handleSaveStandardIndicator = async (indicator: SelectedStandardIndicator) => {
    try {
      setStandardIndicatorError(null)
      
      const result = await saveStandardIndicator({
        definition_id: indicator.definition_id,
        name: indicator.name,
        parameters: indicator.parameters
      })
      
      if (result.success) {
        setStandardIndicatorSuccess(`Saved ${indicator.name} successfully`)
        // Remove from the selected list
        setSelectedStandardIndicators(prev => prev.filter(ind => ind.id !== indicator.id))
      } else {
        setStandardIndicatorError(result.message)
      }
    } catch (err) {
      if (err instanceof Error) {
        setStandardIndicatorError(`Error saving indicator: ${err.message}`)
      } else {
        setStandardIndicatorError('An unknown error occurred while saving the indicator')
      }
    }
  }
  
  // Remove standard indicator from selection
  const handleRemoveStandardIndicator = (id: string) => {
    setSelectedStandardIndicators(prev => prev.filter(ind => ind.id !== id))
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <PageHeader
          heading="Indicators"
          text="Create, manage, and use custom and standard technical indicators."
        />
        <SimpleServerIndicator />
      </div>
      
      <Tabs defaultValue="custom" value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <div className="flex justify-between items-center">
          <TabsList className="mb-4">
            <TabsTrigger value="custom">Custom Indicators</TabsTrigger>
            <TabsTrigger value="standard">Standard Indicators</TabsTrigger>
          </TabsList>
          
          {activeTab === 'custom' && (
            <Button onClick={() => setIsCreatingNew(true)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Create New Indicator
            </Button>
          )}
        </div>
        
        <TabsContent value="custom" className="space-y-6">
          {/* Search Controls for Custom Indicators */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row gap-4 justify-between">
                <div className="relative w-full md:w-64">
                  <Input
                    placeholder="Search indicators..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full"
                  />
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm('')}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Error State */}
          {error && (
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Loading State */}
          {isLoading ? (
            <Card>
              <CardContent className="flex justify-center items-center h-40">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </CardContent>
            </Card>
          ) : (
            /* Indicators List */
            <Card>
              <CardHeader>
                <CardTitle>Your Custom Indicators</CardTitle>
                <CardDescription>
                  {filteredIndicators.length} indicator{filteredIndicators.length !== 1 ? 's' : ''}
                  {searchTerm ? ` matching "${searchTerm}"` : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {filteredIndicators.length === 0 ? (
                  <div className="text-center py-12">
                    {searchTerm ? (
                      <div>
                        <p className="text-gray-500 mb-2">No indicators found matching "{searchTerm}"</p>
                        <Button variant="outline" onClick={() => setSearchTerm('')}>Clear Search</Button>
                      </div>
                    ) : (
                      <div>
                        <p className="text-gray-500 mb-4">You haven't created any custom indicators yet.</p>
                        <Button onClick={() => setIsCreatingNew(true)}>Create Your First Indicator</Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[300px]">Name</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="w-[200px]">Created</TableHead>
                        <TableHead className="w-[150px] text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredIndicators.map((indicator) => (
                        <TableRow key={indicator.id}>
                          <TableCell className="font-medium">{indicator.name}</TableCell>
                          <TableCell>{indicator.description || 'No description'}</TableCell>
                          <TableCell>{indicator.created_at ? new Date(indicator.created_at).toLocaleDateString() : 'Unknown'}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => router.push(`/indicators/${indicator.id}`)}
                              >
                                Edit
                              </Button>
                              <Button 
                                variant="destructive" 
                                size="sm"
                                onClick={() => setShowConfirmDelete(indicator.id || '')}
                              >
                                Delete
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="standard" className="space-y-6">
          {/* Standard Indicators Library */}
          {standardIndicatorSuccess && (
            <Alert className="bg-green-50 border-green-200 text-green-800 dark:bg-green-950 dark:border-green-800 dark:text-green-300">
              <AlertDescription>{standardIndicatorSuccess}</AlertDescription>
            </Alert>
          )}
          
          {standardIndicatorError && (
            <Alert variant="destructive">
              <AlertDescription>{standardIndicatorError}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Standard Indicators Library</CardTitle>
                <CardDescription>
                  Browse and configure technical indicators from the pandas-ta library.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <StandardIndicatorSelector 
                  selectedIndicators={selectedStandardIndicators}
                  onSelectIndicator={handleSelectStandardIndicator}
                  onRemoveIndicator={handleRemoveStandardIndicator}
                  onUpdateIndicatorParams={(id, params) => {
                    setSelectedStandardIndicators(prev => 
                      prev.map(ind => ind.id === id ? { ...ind, parameters: params } : ind)
                    )
                  }}
                />
              </CardContent>
            </Card>
            
            {selectedStandardIndicators.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Selected Standard Indicators</CardTitle>
                  <CardDescription>
                    Indicators you've configured but not yet saved.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedStandardIndicators.map((indicator) => (
                        <TableRow key={indicator.id}>
                          <TableCell className="font-medium">{indicator.name}</TableCell>
                          <TableCell>
                            {indicator.category && (
                              <Badge variant="outline">
                                {indicator.category}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>{indicator.source_library || 'pandas_ta'}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => handleSaveStandardIndicator(indicator)}
                              >
                                Save
                              </Button>
                              <Button 
                                variant="destructive" 
                                size="sm"
                                onClick={() => handleRemoveStandardIndicator(indicator.id)}
                              >
                                Remove
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
      
      {/* New Indicator Dialog */}
      <Dialog open={isCreatingNew} onOpenChange={setIsCreatingNew}>
        <DialogContent className="max-w-6xl max-h-screen overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Indicator</DialogTitle>
            <DialogDescription>
              Create a custom indicator to use in your trading strategies.
            </DialogDescription>
          </DialogHeader>
          
          <IndicatorBuilder 
            onSave={handleCreateIndicator}
            onCancel={() => setIsCreatingNew(false)}
          />
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreatingNew(false)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={showConfirmDelete !== null} onOpenChange={(open) => !open && setShowConfirmDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this indicator? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          {deleteError && (
            <Alert variant="destructive">
              <AlertDescription>{deleteError}</AlertDescription>
            </Alert>
          )}
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowConfirmDelete(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={() => showConfirmDelete && handleDeleteIndicator(showConfirmDelete)}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
