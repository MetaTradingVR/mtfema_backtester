"use client"

import React, { useState, useEffect } from 'react';

export function SimpleServerIndicator() {
  const [status, setStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [showTooltip, setShowTooltip] = useState(false);

  // Simple colors
  const colors = {
    online: '#4ade80', // Green
    offline: '#f87171', // Red
    checking: '#94a3b8', // Gray
  };

  // Check server status on mount and every 10 seconds
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/status');
        setStatus(response.ok ? 'online' : 'offline');
      } catch (error) {
        setStatus('offline');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // Start server function
  const startServer = async () => {
    try {
      await fetch('http://localhost:5001/launcher/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      alert('Server start requested. It may take a few moments to start.');
    } catch (error) {
      alert('Failed to start server. Launcher may not be running.');
    }
  };

  return (
    <div className="relative" style={{ width: '120px' }}>
      {/* Simple indicator */}
      <div 
        className="flex items-center gap-2 p-2 rounded-md cursor-pointer border border-gray-700 bg-gray-800"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div 
          className="w-3 h-3 rounded-full" 
          style={{ backgroundColor: colors[status] }} 
        />
        <span className="text-xs font-medium">
          Server {status === 'checking' ? 'Checking...' : status}
        </span>
      </div>
      
      {/* Simple tooltip */}
      {showTooltip && (
        <div className="absolute top-full right-0 mt-1 p-2 bg-gray-800 rounded-md shadow-lg border border-gray-700 z-50 w-48">
          <p className="text-xs mb-2">
            {status === 'online' 
              ? 'Server is running normally' 
              : status === 'offline' 
                ? 'Server is currently offline'
                : 'Checking server status...'}
          </p>
          
          {status === 'offline' && (
            <button 
              onClick={startServer}
              className="w-full text-xs bg-blue-600 text-white p-1 rounded-sm hover:bg-blue-700"
            >
              Start Server
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default SimpleServerIndicator;
