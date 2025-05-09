"use client"

/**
 * EnhancedServerStatusIndicator Component
 * 
 * A status indicator that shows the health of backend services
 * and provides the ability to start the server with a single click when it's offline.
 */

import { useEffect, useState, useCallback } from 'react';

// Define the server status types locally since we can't access the API client
interface ServerStatusComponent {
  status: 'available' | 'unavailable' | 'connected' | 'disconnected' | 'error';
  active_jobs?: number;
  count?: number;
}

interface ServerStatus {
  overall_status: 'healthy' | 'degraded' | 'error';
  server: {
    status: 'online' | 'offline';
    version: string;
    uptime_seconds: number;
  };
  components: {
    backtesting: ServerStatusComponent;
    optimization: ServerStatusComponent;
    indicators: ServerStatusComponent;
    live_trading: ServerStatusComponent;
  };
  timestamp: string;
}

// Status colors for visual feedback
const statusColors = {
  healthy: '#4ade80', // Green
  degraded: '#facc15', // Yellow
  error: '#f87171',   // Red
  offline: '#9ca3af'  // Gray
};

// Launcher API URL (different port from main API)
const LAUNCHER_URL = 'http://localhost:5001';
const API_BASE_URL = 'http://localhost:5000/api';

export interface ServerStatusIndicatorProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  showLabel?: boolean;
}

export const ServerStatusIndicator = ({ 
  position = 'bottom-right',
  showLabel = true 
}: ServerStatusIndicatorProps) => {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [launcherAvailable, setLauncherAvailable] = useState(false);

  // Position styles
  const positionStyles = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  };

  // Check if launcher is available
  const checkLauncherStatus = useCallback(async () => {
    try {
      const response = await fetch(`${LAUNCHER_URL}/launcher/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setLauncherAvailable(true);
        return true;
      }
    } catch (error) {
      // Launcher not available
      setLauncherAvailable(false);
    }
    return false;
  }, []);

  // Start the server using launcher
  const startServer = useCallback(async () => {
    setIsStarting(true);
    setStartError(null);

    try {
      // First check if launcher is available
      const launcherActive = await checkLauncherStatus();
      
      if (!launcherActive) {
        setStartError('Server launcher is not running. Please start server_launcher.py manually.');
        setIsStarting(false);
        return;
      }

      // Request launcher to start the server
      const response = await fetch(`${LAUNCHER_URL}/launcher/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start server');
      }

      const data = await response.json();
      
      // Start polling for server to come online
      startServerPolling();
      
      // Show user feedback
      setIsStarting(true);
      
    } catch (error) {
      setStartError(`Error starting server: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsStarting(false);
    }
  }, [checkLauncherStatus]);

  // Poll for server to come online
  const startServerPolling = useCallback(() => {
    let attempts = 0;
    const maxAttempts = 30; // 30 seconds max wait
    
    const poll = () => {
      setTimeout(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/status`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          if (response.ok) {
            // Server is up!
            const data = await response.json();
            setStatus(data);
            setIsStarting(false);
            return;
          }
        } catch (error) {
          // Server still not available
        }

        attempts++;
        if (attempts < maxAttempts) {
          poll(); // Continue polling
        } else {
          // Give up after max attempts
          setIsStarting(false);
          setStartError('Server failed to start within the expected time.');
        }
      }, 1000); // Poll every second
    };

    poll();
  }, []);

  // Fetch status with exponential backoff on error
  useEffect(() => {
    let isMounted = true;
    let retryCount = 0;
    let retryTimeout: NodeJS.Timeout;

    const fetchServerStatus = useCallback(async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout
        
        const response = await fetch(`${API_BASE_URL}/status`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          setStatus(data);
        } else {
          // Server is down
          setStatus({
            overall_status: 'error',
            server: {
              status: 'offline',
              version: 'unknown',
              uptime_seconds: 0
            },
            components: {
              backtesting: { status: 'unavailable' },
              optimization: { status: 'unavailable' },
              indicators: { status: 'unavailable' },
              live_trading: { status: 'unavailable' }
            },
            timestamp: new Date().toISOString()
          });
          
          // Check launcher status
          await checkLauncherStatus();
        }
      } catch (error) {
        // Likely a network error - server is down
        console.log("Server status check failed:", error instanceof Error ? error.message : 'Unknown error');
        
        setStatus({
          overall_status: 'error',
          server: {
            status: 'offline',
            version: 'unknown',
            uptime_seconds: 0
          },
          components: {
            backtesting: { status: 'unavailable' },
            optimization: { status: 'unavailable' },
            indicators: { status: 'unavailable' },
            live_trading: { status: 'unavailable' }
          },
          timestamp: new Date().toISOString()
        });
        
        // Check launcher status
        await checkLauncherStatus();
      }
    }, [checkLauncherStatus]);

    const fetchStatus = async () => {
      try {
        await fetchServerStatus();
      } catch (error) {
        console.error('Failed to fetch server status:', error);
        if (isMounted) {
          // Exponential backoff with max of 30 seconds
          const delay = Math.min(2 ** retryCount * 1000, 30000);
          retryCount++;
          retryTimeout = setTimeout(fetchStatus, delay);
        }
      }
    };

    fetchStatus();

    return () => {
      isMounted = false;
      clearTimeout(retryTimeout);
    };
  }, [checkLauncherStatus]);

  // Gets the proper status color
  const getStatusColor = () => {
    if (isStarting) return statusColors.degraded;
    if (!status) return statusColors.offline;
    return statusColors[status.overall_status] || statusColors.offline;
  };

  // Gets the display status text
  const getStatusText = () => {
    if (isStarting) return 'STARTING';
    if (!status) return 'OFFLINE';
    return status.overall_status.toUpperCase();
  };
  
  return (
    <div className={`fixed z-50 ${positionStyles[position]}`}>
      {/* Compact indicator */}
      <div 
        className="flex items-center cursor-pointer p-2 rounded-full shadow-md bg-white dark:bg-gray-800"
        onClick={() => {
          if (!status || status.overall_status === 'error') {
            if (launcherAvailable && !isStarting) {
              startServer();
            } else {
              setIsExpanded(!isExpanded);
            }
          } else {
            setIsExpanded(!isExpanded);
          }
        }}
        title={isStarting ? 'Server is starting...' : (!status || status.overall_status === 'error') ? 
              (launcherAvailable ? 'Click to start server' : 'Server is offline') : 
              `Server Status: ${status.overall_status}`}
      >
        <div 
          className={`h-3 w-3 rounded-full mr-2 ${isStarting ? 'animate-pulse' : ''}`}
          style={{ backgroundColor: getStatusColor() }} 
        />
        {showLabel && (
          <span className="text-xs font-medium">
            {!isExpanded && getStatusText()}
          </span>
        )}
      </div>

      {/* Expanded status panel */}
      {isExpanded && (
        <div className="absolute bottom-12 right-0 w-64 p-3 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-semibold">Server Status</h3>
            {status && (
              <span className="text-xs">
                v{status.server.version}
              </span>
            )}
          </div>
          
          {!status || status.overall_status === 'error' ? (
            <div className="space-y-3 text-sm">
              <div className="flex items-center text-gray-600 dark:text-gray-300">
                <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Server is offline</span>
              </div>
              
              {startError && (
                <div className="text-xs text-red-500 mt-1">
                  {startError}
                </div>
              )}
              
              {launcherAvailable && !isStarting && (
                <button
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent closing the panel
                    startServer();
                  }}
                  className="w-full py-2 px-3 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center justify-center"
                >
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                  Start Server
                </button>
              )}
              
              {isStarting && (
                <div className="flex items-center justify-center text-blue-500">
                  <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Starting server...</span>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2 text-xs">
              {/* Overall status */}
              <div className="flex justify-between">
                <span>Overall:</span>
                <span 
                  className="font-medium"
                  style={{ color: statusColors[status.overall_status] || statusColors.offline }}
                >
                  {status.overall_status.toUpperCase()}
                </span>
              </div>
              
              {/* Component statuses */}
              {Object.entries(status.components).map(([name, info]) => (
                <div key={name} className="flex justify-between">
                  <span>{name.replace(/([A-Z])/g, ' $1').trim()}:</span>
                  <span className={info.status === 'available' || info.status === 'connected' ? 'text-green-500' : 'text-gray-500'}>
                    {info.status}
                    {name === 'backtesting' && info.active_jobs && info.active_jobs > 0 && ` (${info.active_jobs} active)`}
                    {name === 'optimization' && info.active_jobs && info.active_jobs > 0 && ` (${info.active_jobs} active)`}
                    {name === 'indicators' && info.count !== undefined && ` (${info.count} loaded)`}
                  </span>
                </div>
              ))}
              
              {/* Uptime */}
              <div className="flex justify-between mt-1 pt-1 border-t border-gray-200 dark:border-gray-700">
                <span>Uptime:</span>
                <span>{formatUptime(status.server.uptime_seconds)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Helper function to format uptime in a readable way
function formatUptime(seconds: number): string {
  if (!seconds || seconds < 0) return '0s';
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${Math.floor(seconds % 60)}s`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ${minutes % 60}m`;
  
  const days = Math.floor(hours / 24);
  return `${days}d ${hours % 24}h`;
}

export default ServerStatusIndicator;
