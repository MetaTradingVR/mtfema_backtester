/**
 * ServerStatusIndicator Component
 * 
 * A lightweight status indicator that shows the health of the backend services.
 * This component is designed to be included in the layout to provide at-a-glance
 * status information without affecting performance.
 */

import { useEffect, useState } from 'react';
import { getServerStatus, ServerStatus } from '../lib/api';

// Using inline styles to avoid additional imports
const statusColors = {
  healthy: '#4ade80', // Green
  degraded: '#facc15', // Yellow
  error: '#f87171',   // Red
  offline: '#9ca3af'  // Gray
};

export const ServerStatusIndicator = () => {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch status with exponential backoff on error
  useEffect(() => {
    let isMounted = true;
    let retryCount = 0;
    let retryTimeout: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const data = await getServerStatus();
        if (isMounted) {
          setStatus(data);
          // Reset retry count on success
          retryCount = 0;
          // Schedule next update
          retryTimeout = setTimeout(fetchStatus, 10000); // Check every 10 seconds
        }
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
  }, []);

  // Don't render anything during initial load to avoid layout shifts
  if (!status) return null;

  const statusColor = statusColors[status.overall_status] || statusColors.offline;
  
  return (
    <div className="fixed right-4 bottom-4 z-50">
      {/* Compact indicator */}
      <div 
        className="flex items-center cursor-pointer p-2 rounded-full shadow-md bg-white dark:bg-gray-800"
        onClick={() => setIsExpanded(!isExpanded)}
        title={`Server Status: ${status.overall_status}`}
      >
        <div 
          className="h-3 w-3 rounded-full mr-2" 
          style={{ backgroundColor: statusColor }} 
        />
        <span className="text-xs font-medium">
          {!isExpanded && status.overall_status.toUpperCase()}
        </span>
      </div>

      {/* Expanded status panel */}
      {isExpanded && (
        <div className="absolute bottom-12 right-0 w-64 p-3 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-semibold">Server Status</h3>
            <span className="text-xs">
              v{status.server.version}
            </span>
          </div>
          
          <div className="space-y-2 text-xs">
            {/* Overall status */}
            <div className="flex justify-between">
              <span>Overall:</span>
              <span className="font-medium" style={{ color: statusColor }}>
                {status.overall_status.toUpperCase()}
              </span>
            </div>
            
            {/* Component statuses */}
            {Object.entries(status.components).map(([name, info]) => (
              <div key={name} className="flex justify-between">
                <span>{name.replace(/([A-Z])/g, ' $1').trim()}:</span>
                <span className={info.status === 'available' || info.status === 'connected' ? 'text-green-500' : 'text-gray-500'}>
                  {info.status}
                  {name === 'backtesting' && info.active_jobs > 0 && ` (${info.active_jobs} active)`}
                  {name === 'optimization' && info.active_jobs > 0 && ` (${info.active_jobs} active)`}
                </span>
              </div>
            ))}
            
            {/* Uptime */}
            <div className="flex justify-between mt-1 pt-1 border-t border-gray-200 dark:border-gray-700">
              <span>Uptime:</span>
              <span>{formatUptime(status.server.uptime_seconds)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to format uptime in a readable way
function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${Math.floor(seconds % 60)}s`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ${minutes % 60}m`;
  
  const days = Math.floor(hours / 24);
  return `${days}d ${hours % 24}h`;
}

export default ServerStatusIndicator;
