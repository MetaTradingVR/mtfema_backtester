"use client"

/**
 * Basic Server Status Indicator
 * 
 * A simple, dependency-free status indicator for the API server
 */

import { useState, useEffect, useCallback } from 'react';

// API Endpoints
const API_BASE_URL = 'http://localhost:5000/api';
const LAUNCHER_URL = 'http://localhost:5001';

// Status colors
const statusColors = {
  online: '#4ade80', // Green
  offline: '#f87171', // Red
  checking: '#94a3b8', // Gray
  starting: '#60a5fa', // Blue
};

export function BasicServerStatus() {
  const [status, setStatus] = useState<'online' | 'offline' | 'checking' | 'starting'>('checking');
  const [canStart, setCanStart] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  
  // Check server status
  const checkStatus = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`${API_BASE_URL}/status`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        setStatus('online');
        console.log('Server is online');
      } else {
        setStatus('offline');
        checkLauncher();
        console.log('Server is offline');
      }
    } catch (error) {
      setStatus('offline');
      checkLauncher();
      console.log('Failed to check server:', error);
    }
  }, []);
  
  // Check if launcher is available
  const checkLauncher = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`${LAUNCHER_URL}/launcher/status`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        setCanStart(true);
        console.log('Launcher is available');
      } else {
        setCanStart(false);
        console.log('Launcher is not available');
      }
    } catch (error) {
      setCanStart(false);
      console.log('Failed to check launcher:', error);
    }
  }, []);
  
  // Start the server
  const startServer = useCallback(async () => {
    if (status === 'starting') return;
    
    console.log('Starting server...');
    setStatus('starting');
    
    try {
      // Create a controller to handle timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(`${LAUNCHER_URL}/launcher/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        console.log('Server start requested successfully');
        
        // Poll for server to come online
        let attempts = 0;
        const maxAttempts = 30;
        
        const poll = setInterval(async () => {
          console.log(`Polling for server (attempt ${attempts + 1}/${maxAttempts})...`);
          
          try {
            const statusController = new AbortController();
            const statusTimeoutId = setTimeout(() => statusController.abort(), 2000);
            
            const statusResponse = await fetch(`${API_BASE_URL}/status`, {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              },
              signal: statusController.signal
            });
            
            clearTimeout(statusTimeoutId);
            
            if (statusResponse.ok) {
              console.log('Server is now online');
              setStatus('online');
              clearInterval(poll);
            } else {
              attempts++;
              if (attempts >= maxAttempts) {
                console.log('Failed to start server after maximum attempts');
                setStatus('offline');
                clearInterval(poll);
              }
            }
          } catch (error) {
            console.log(`Poll attempt ${attempts + 1} failed:`, error);
            attempts++;
            if (attempts >= maxAttempts) {
              console.log('Failed to start server after maximum attempts');
              setStatus('offline');
              clearInterval(poll);
            }
          }
        }, 1000);
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.log('Failed to start server:', errorData);
        setStatus('offline');
      }
    } catch (error) {
      console.log('Error starting server:', error);
      setStatus('offline');
    }
  }, [status]);
  
  // Set up regular status checking
  useEffect(() => {
    // Initial check
    checkStatus();
    
    // Regular checks
    const interval = setInterval(checkStatus, 10000);
    
    return () => clearInterval(interval);
  }, [checkStatus]);
  
  // Get color based on status
  const getStatusColor = () => {
    return statusColors[status];
  };
  
  // Get tooltip text
  const getTooltipText = () => {
    switch (status) {
      case 'online': return 'Server is online';
      case 'offline': return canStart ? 'Server is offline - Click to start' : 'Server is offline - Launcher not available';
      case 'checking': return 'Checking server status...';
      case 'starting': return 'Starting server...';
    }
  };
  
  return (
    <div className="relative">
      {/* Status indicator - Enhanced visibility */}
      <div 
        className="flex items-center gap-2 p-2 px-3 rounded-md cursor-pointer border border-gray-200 dark:border-gray-800 shadow-sm"
        style={{ backgroundColor: `${getStatusColor()}20` }}
        onClick={() => {
          if (status === 'offline' && canStart) {
            startServer();
          } else {
            setShowTooltip(!showTooltip);
          }
        }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div 
          className="w-4 h-4 rounded-full animate-pulse" 
          style={{ backgroundColor: getStatusColor() }} 
        />
        <span className="text-sm font-medium whitespace-nowrap">
          {status === 'online' ? 'Server Online' : 
           status === 'offline' ? 'Server Offline' : 
           status === 'starting' ? 'Starting Server...' : 
           'Checking...'}
        </span>
      </div>
      
      {/* Enhanced tooltip with better styling */}
      {showTooltip && (
        <div className="absolute top-full right-0 mt-2 p-3 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-50 min-w-[220px]">
          <p className="text-sm mb-2">{getTooltipText()}</p>
          
          {status === 'offline' && canStart && (
            <button 
              className="mt-2 w-full px-3 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors font-medium"
              onClick={(e) => {
                e.stopPropagation(); // Prevent double clicks
                startServer();
              }}
            >
              Start Server
            </button>
          )}
          
          {status === 'starting' && (
            <div className="mt-2 flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse"></div>
              <span className="text-sm">Starting server, please wait...</span>
            </div>
          )}
          
          {status === 'online' && (
            <div className="mt-2 text-sm text-green-500 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Server is running normally</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default BasicServerStatus;
