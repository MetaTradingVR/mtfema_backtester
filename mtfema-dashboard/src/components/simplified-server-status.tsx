"use client"

/**
 * Simplified Server Status Indicator
 * 
 * A lightweight version that doesn't rely on external dependencies.
 * Shows server status and allows starting the server with a single click.
 */

import { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, Activity, RefreshCw, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import SimpleTooltip from '@/components/ui/simple-tooltip';

// API Endpoints
const LAUNCHER_URL = 'http://localhost:5001';
const API_BASE_URL = 'http://localhost:5000/api';

// Status types
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
  offline: '#94a3b8',  // Slate
  starting: '#60a5fa', // Blue
};

export interface SimplifiedServerStatusProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  showLabel?: boolean;
}

export function SimplifiedServerStatus({ 
  position = 'top-right',
  showLabel = true 
}: SimplifiedServerStatusProps) {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [launcherAvailable, setLauncherAvailable] = useState(false);

  // Check if launcher is available
  const checkLauncherStatus = useCallback(async () => {
    try {
      console.log("Checking launcher status...");
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout
      
      const response = await fetch(`${LAUNCHER_URL}/launcher/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        console.log("Launcher is available");
        setLauncherAvailable(true);
        return true;
      }
    } catch (error) {
      console.log("Launcher check failed:", 
                 error instanceof Error ? error.message : 'Unknown error');
    }
    
    console.log("Launcher is not available");
    setLauncherAvailable(false);
    return false;
  }, []);

  // Check server status
  const checkServerStatus = useCallback(async () => {
    try {
      console.log("Checking server status...");
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout
      
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
        console.log("Server is online:", data);
        setStatus(data);
        return true;
      } else {
        console.log("Server is offline (response not ok)");
        setServerOfflineStatus();
        return false;
      }
    } catch (error) {
      console.log("Server status check failed:", 
                 error instanceof Error ? error.message : 'Unknown error');
      setServerOfflineStatus();
      return false;
    }
  }, []);

  // Set offline status helper
  const setServerOfflineStatus = useCallback(() => {
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
  }, []);

  // Start the server
  const startServer = useCallback(async () => {
    if (isStarting) return; // Prevent multiple simultaneous attempts
    
    setIsStarting(true);
    setStartError(null);

    try {
      console.log("Attempting to start server...");
      
      // Check if launcher is available
      const launcherActive = await checkLauncherStatus();
      
      if (!launcherActive) {
        setStartError('Server launcher is not running. Please start server_launcher.py manually.');
        setIsStarting(false);
        return;
      }

      // Request launcher to start the server
      console.log("Calling launcher to start server...");
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout
      
      const response = await fetch(`${LAUNCHER_URL}/launcher/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start server');
      }

      console.log("Server start requested successfully");
      
      // Poll for server to come online
      startPollingServerStatus();
      
    } catch (error) {
      console.error("Error starting server:", error);
      setStartError(`Error starting server: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsStarting(false);
    }
  }, [isStarting, checkLauncherStatus]);

  // Poll for server to come online after start attempt
  const startPollingServerStatus = useCallback(() => {
    let attempts = 0;
    const maxAttempts = 30; // 30 seconds max wait
    
    const poll = async () => {
      console.log(`Polling for server (attempt ${attempts + 1}/${maxAttempts})...`);
      
      if (attempts >= maxAttempts) {
        console.log("Max polling attempts reached");
        setStartError('Server failed to start after 30 seconds. Please check server logs.');
        setIsStarting(false);
        return;
      }
      
      const serverOnline = await checkServerStatus();
      
      if (serverOnline) {
        console.log("Server is now online");
        setIsStarting(false);
      } else {
        attempts++;
        setTimeout(poll, 1000); // Check every second
      }
    };
    
    poll();
  }, [checkServerStatus]);

  // Setup regular status checking
  useEffect(() => {
    let isMounted = true;
    let checkInterval: NodeJS.Timeout;
    
    const initialCheck = async () => {
      const serverOnline = await checkServerStatus();
      
      if (!serverOnline && isMounted) {
        // Server is offline, check if launcher is available
        await checkLauncherStatus();
      }
      
      if (isMounted) {
        // Schedule regular checks
        checkInterval = setInterval(async () => {
          if (isMounted) {
            await checkServerStatus();
            
            // Periodically check launcher if server is offline
            if (status?.server?.status === 'offline') {
              await checkLauncherStatus();
            }
          }
        }, 10000); // Check every 10 seconds
      }
    };
    
    initialCheck();
    
    return () => {
      isMounted = false;
      if (checkInterval) clearInterval(checkInterval);
    };
  }, [checkServerStatus, checkLauncherStatus, status?.server?.status]);

  // Helper to format uptime
  const formatUptime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ${minutes % 60}m`;
    
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  };

  // Determine status color and icon
  const getStatusInfo = () => {
    if (isStarting) {
      return {
        color: statusColors.starting,
        icon: <RefreshCw className="h-5 w-5 animate-spin" />,
        text: 'Starting...'
      };
    }
    
    if (!status) {
      return {
        color: statusColors.offline,
        icon: <Activity className="h-5 w-5" />,
        text: 'Checking...'
      };
    }
    
    if (status.server.status === 'offline') {
      return {
        color: statusColors.error,
        icon: <AlertCircle className="h-5 w-5" />,
        text: 'Server Offline'
      };
    }
    
    switch (status.overall_status) {
      case 'healthy':
        return {
          color: statusColors.healthy,
          icon: <CheckCircle className="h-5 w-5" />,
          text: 'All Systems Online'
        };
      case 'degraded':
        return {
          color: statusColors.degraded,
          icon: <AlertCircle className="h-5 w-5" />,
          text: 'Degraded Performance'
        };
      case 'error':
        return {
          color: statusColors.error,
          icon: <AlertCircle className="h-5 w-5" />,
          text: 'System Error'
        };
      default:
        return {
          color: statusColors.offline,
          icon: <Activity className="h-5 w-5" />,
          text: 'Unknown Status'
        };
    }
  };

  const statusInfo = getStatusInfo();
  const isServerOffline = status?.server?.status === 'offline';
  const canStartServer = !isStarting && isServerOffline && launcherAvailable;

  return (
    <SimpleTooltip
      content={
        <div className="p-2 min-w-[250px]">
          <div className="font-medium flex items-center gap-2 mb-2">
            {statusInfo.icon}
            <span>
              {!status ? 'Checking server status...' : isServerOffline ? 'Server Offline' : 'Server Status'}
            </span>
          </div>
          
          {/* Status Detail */}
          {status && status.server.status === 'online' && (
            <div className="text-sm space-y-1 mb-2">
              <div className="text-gray-500 dark:text-gray-400">
                <span className="font-medium">Uptime:</span> {formatUptime(status.server.uptime_seconds)}
              </div>
              <div className="text-gray-500 dark:text-gray-400">
                <span className="font-medium">Version:</span> {status.server.version}
              </div>
            </div>
          )}
          
          {/* Components Status */}
          {status && status.server.status === 'online' && (
            <div className="text-xs grid grid-cols-2 gap-x-4 gap-y-1 mt-2">
              <div className="flex items-center gap-1">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ 
                    backgroundColor: status.components.backtesting.status === 'available' 
                      ? statusColors.healthy 
                      : statusColors.error
                  }}
                />
                <span>Backtesting</span>
              </div>
              <div className="flex items-center gap-1">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ 
                    backgroundColor: status.components.optimization.status === 'available' 
                      ? statusColors.healthy 
                      : statusColors.error
                  }}
                />
                <span>Optimization</span>
              </div>
              <div className="flex items-center gap-1">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ 
                    backgroundColor: status.components.indicators.status === 'available' 
                      ? statusColors.healthy 
                      : statusColors.error
                  }}
                />
                <span>Indicators</span>
              </div>
              <div className="flex items-center gap-1">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ 
                    backgroundColor: status.components.live_trading.status === 'available' 
                      ? statusColors.healthy 
                      : statusColors.error
                  }}
                />
                <span>Live Trading</span>
              </div>
            </div>
          )}
          
          {/* Server Offline Message */}
          {isServerOffline && (
            <div className="text-sm mt-2">
              {launcherAvailable ? (
                <span className="text-green-600 dark:text-green-400">
                  Click to start the API server
                </span>
              ) : (
                <span className="text-red-500 dark:text-red-400">
                  Server launcher not available. Please start server_launcher.py manually.
                </span>
              )}
            </div>
          )}
          
          {/* Start Error */}
          {startError && (
            <div className="text-sm text-red-500 dark:text-red-400 mt-1">
              {startError}
            </div>
          )}
          
          {/* Manual Start Button (as backup) */}
          {isServerOffline && launcherAvailable && (
            <Button 
              size="sm"
              className="mt-2 w-full"
              disabled={isStarting}
              onClick={startServer}
            >
              {isStarting ? (
                <>
                  <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="mr-1 h-3 w-3" />
                  Start Server
                </>
              )}
            </Button>
          )}
        </div>
      }
      side="bottom"
      align="end"
    >
      {/* Status Indicator */}
      <div 
        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-all ${canStartServer ? 'hover:bg-gray-100 dark:hover:bg-gray-800' : ''}`}
        style={{ backgroundColor: `${statusInfo.color}20` }}
        onClick={() => {
          if (canStartServer) {
            startServer();
          }
        }}
      >
        <div className="relative">
          <div 
            className="w-3.5 h-3.5 rounded-full animate-pulse" 
            style={{ backgroundColor: statusInfo.color }}
          />
        </div>
        
        {showLabel && (
          <span className="text-sm font-medium whitespace-nowrap">
            {statusInfo.text}
          </span>
        )}
        
        {canStartServer && (
          <Play size={16} className="text-green-600 dark:text-green-400" />
        )}
      </div>
    </SimpleTooltip>
  );
}

export default SimplifiedServerStatus;
