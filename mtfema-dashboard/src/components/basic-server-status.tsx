"use client"

/**
 * Basic Server Status Indicator
 * 
 * A simple, dependency-free status indicator for the API server
 */

import { useState, useEffect, useCallback } from 'react';

// API Endpoints
const API_BASE_URL = 'http://localhost:5000/api';
// Make sure we're using the exact URL format that the launcher expects
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
      console.log('Checking server status at:', `${API_BASE_URL}/status`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      // Some browsers may cache the API responses, so add a cache-busting parameter
      const cacheBuster = `?_=${Date.now()}`;
      const response = await fetch(`${API_BASE_URL}/status${cacheBuster}`, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        console.log('Server responded with OK status');
        setStatus('online');
        console.log('Server is online');
      } else {
        console.log('Server responded with error status:', response.status, response.statusText);
        setStatus('offline');
        checkLauncher();
        console.log('Server is offline');
      }
    } catch (error) {
      console.error('Failed to check server:', error);
      setStatus('offline');
      checkLauncher();
    }
  }, []);
  
  // Check if launcher is available
  const checkLauncher = useCallback(async () => {
    try {
      console.log('Checking launcher availability at:', `${LAUNCHER_URL}/launcher/status`);
      
      // For testing, use XMLHttpRequest which has different CORS handling than fetch
      // This provides a more robust way to detect if the server is actually there
      return new Promise<void>((resolve) => {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `${LAUNCHER_URL}/launcher/status`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.timeout = 2000; // 2 second timeout
        
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              console.log('Launcher status data:', data);
              setCanStart(true);
              console.log('Launcher is available');
            } catch (e) {
              console.error('Error parsing launcher response:', e);
              setCanStart(false);
            }
          } else {
            console.log('Launcher status error:', xhr.status, xhr.statusText);
            setCanStart(false);
          }
          resolve();
        };
        
        xhr.onerror = function() {
          console.error('Network error checking launcher');
          setCanStart(false);
          resolve();
        };
        
        xhr.ontimeout = function() {
          console.error('Timeout checking launcher');
          setCanStart(false);
          resolve();
        };
        
        xhr.send();
      });
    } catch (error) {
      console.error('Failed to check launcher:', error);
      setCanStart(false);
    }
  }, []);
  
  // Start the server
  const startServer = useCallback(async () => {
    if (status === 'starting') return;
    
    console.log('Starting server...');
    setStatus('starting');
    
    try {
      console.log('Sending server start request to:', `${LAUNCHER_URL}/launcher/start`);
      
      // Use XMLHttpRequest for better cross-origin support
      await new Promise<void>((resolve) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${LAUNCHER_URL}/launcher/start`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.timeout = 10000; // 10 second timeout
        
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            console.log('Server start requested successfully');
            resolve();
          } else {
            console.log('Failed to start server:', xhr.status, xhr.statusText);
            setStatus('offline');
            resolve();
          }
        };
        
        xhr.onerror = function() {
          console.error('Network error starting server');
          setStatus('offline');
          resolve();
        };
        
        xhr.ontimeout = function() {
          console.error('Timeout starting server');
          setStatus('offline');
          resolve();
        };
        
        xhr.send(JSON.stringify({})); // Send empty object as body
      });
      
      // Poll for server to come online
      let attempts = 0;
      const maxAttempts = 30;
      
      const poll = setInterval(() => {
        console.log(`Polling for server (attempt ${attempts + 1}/${maxAttempts})...`);
        
        // Use XMLHttpRequest for status checking too
        const statusXhr = new XMLHttpRequest();
        const cacheBuster = `?_=${Date.now()}`;
        statusXhr.open('GET', `${API_BASE_URL}/status${cacheBuster}`, true);
        statusXhr.setRequestHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
        statusXhr.timeout = 2000; // 2 second timeout
        
        statusXhr.onload = function() {
          if (statusXhr.status >= 200 && statusXhr.status < 300) {
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
        };
        
        statusXhr.onerror = function() {
          console.log(`Poll attempt ${attempts + 1} failed: Network error`);
          attempts++;
          if (attempts >= maxAttempts) {
            console.log('Failed to start server after maximum attempts');
            setStatus('offline');
            clearInterval(poll);
          }
        };
        
        statusXhr.ontimeout = function() {
          console.log(`Poll attempt ${attempts + 1} failed: Timeout`);
          attempts++;
          if (attempts >= maxAttempts) {
            console.log('Failed to start server after maximum attempts');
            setStatus('offline');
            clearInterval(poll);
          }
        };
        
        statusXhr.send();
      }, 1000);
      
    } catch (error) {
      console.error('Error starting server:', error);
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
