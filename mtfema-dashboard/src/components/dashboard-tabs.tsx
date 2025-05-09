"use client";

import React from 'react';
import { SimpleServerIndicator } from './simple-server-indicator';

interface DashboardTabsProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onTabChange: (id: string) => void;
}

export function DashboardTabs({ tabs, activeTab, onTabChange }: DashboardTabsProps) {
  return (
    <div className="flex justify-between items-center mb-6 border-b border-gray-700">
      <div className="flex space-x-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors ${
              activeTab === tab.id
                ? 'bg-gray-700/50 text-white border-t border-l border-r border-gray-700'
                : 'text-gray-400 hover:text-white hover:bg-gray-700/30'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="py-1">
        <SimpleServerIndicator />
      </div>
    </div>
  );
}

export default DashboardTabs;
