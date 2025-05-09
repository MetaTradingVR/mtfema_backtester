/**
 * MT9 EMA Backtester API Client - Custom Indicators and Status Monitoring
 * 
 * This file contains extensions to the existing API client for:
 * 1. Server status monitoring
 * 2. Custom indicator management
 * 
 * Add these functions to your existing src/lib/api.ts file.
 */

import { API_BASE_URL } from './constants';

// Types for server status monitoring
export interface ServerStatus {
  overall_status: 'healthy' | 'degraded' | 'error';
  server: {
    status: 'online' | 'offline';
    version: string;
    uptime_seconds: number;
  };
  components: {
    backtesting: {
      status: 'available' | 'unavailable';
      active_jobs: number;
    };
    optimization: {
      status: 'available' | 'unavailable';
      active_jobs: number;
    };
    indicators: {
      status: 'available' | 'unavailable';
      count: number;
    };
    live_trading: {
      status: 'connected' | 'disconnected' | 'error';
    };
  };
  timestamp: string;
}

// Types for custom indicators
export interface IndicatorParameter {
  name: string;
  type: 'int' | 'float' | 'string' | 'bool';
  default: any;
  min?: number;
  max?: number;
  options?: string[];
  description?: string;
}

export interface IndicatorInfo {
  name: string;
  description?: string;
  parameters: IndicatorParameter[];
  output_fields: string[];
  built_in: boolean;
}

export interface CustomIndicatorCode {
  name: string;
  description?: string;
  parameters: IndicatorParameter[];
  code: string;
  test_data?: boolean;
  save: boolean;
}

export interface IndicatorTestResult {
  success: boolean;
  message: string;
  preview?: Record<string, number[]>;
}

// Server status monitoring functions
export async function getServerStatus(): Promise<ServerStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Server status request failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching server status:', error);
    // Return a fallback error status when we can't reach the server
    return {
      overall_status: 'error',
      server: {
        status: 'offline',
        version: 'unknown',
        uptime_seconds: 0,
      },
      components: {
        backtesting: { status: 'unavailable', active_jobs: 0 },
        optimization: { status: 'unavailable', active_jobs: 0 },
        indicators: { status: 'unavailable', count: 0 },
        live_trading: { status: 'disconnected' },
      },
      timestamp: new Date().toISOString(),
    };
  }
}

// Custom indicator management functions
export async function getIndicators(): Promise<IndicatorInfo[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/indicators`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get indicators: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching indicators:', error);
    return [];
  }
}

export async function testIndicator(indicator: CustomIndicatorCode): Promise<IndicatorTestResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/indicators/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(indicator),
    });

    if (!response.ok) {
      throw new Error(`Failed to test indicator: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error testing indicator:', error);
    return {
      success: false,
      message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

export async function createIndicator(indicator: CustomIndicatorCode): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/indicators`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(indicator),
    });

    if (!response.ok) {
      throw new Error(`Failed to create indicator: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating indicator:', error);
    return {
      success: false,
      message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

export async function deleteIndicator(indicatorName: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/indicators/${indicatorName}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete indicator: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error deleting indicator:', error);
    return {
      success: false,
      message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}
