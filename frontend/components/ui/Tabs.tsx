'use client';

import { LucideIcon } from 'lucide-react';

interface Tab {
  id: string;
  label: string;
  icon?: LucideIcon;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'underline' | 'pills' | 'boxed';
  'aria-label'?: string;
  'data-testid'?: string;
}

export default function Tabs({ 
  tabs, 
  activeTab, 
  onChange, 
  variant = 'underline',
  'aria-label': ariaLabel = 'Tabs',
  'data-testid': testId = 'tabs'
}: TabsProps) {
  if (variant === 'pills') {
    return (
      <div 
        role="tablist" 
        aria-label={ariaLabel}
        className="flex space-x-2 mb-6"
        data-testid={testId}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              onClick={() => onChange(tab.id)}
              className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center transition ${
                isActive
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {Icon && <Icon className="h-4 w-4 mr-2" aria-hidden="true" />}
              {tab.label}
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === 'boxed') {
    return (
      <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-6" data-testid={testId}>
        <div role="tablist" aria-label={ariaLabel} className="flex border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-controls={`panel-${tab.id}`}
                onClick={() => onChange(tab.id)}
                className={`flex-1 px-6 py-4 text-sm font-medium transition flex items-center justify-center ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {Icon && <Icon className="h-5 w-5 mr-2" aria-hidden="true" />}
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  // Default: underline variant
  return (
    <div className="border-b border-gray-200 mb-6" data-testid={testId}>
      <div role="tablist" aria-label={ariaLabel} className="flex space-x-8">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              onClick={() => onChange(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center transition ${
                isActive
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {Icon && <Icon className="h-5 w-5 mr-2" aria-hidden="true" />}
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
