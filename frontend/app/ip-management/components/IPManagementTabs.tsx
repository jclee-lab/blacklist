'use client';

import { Layers, ShieldCheck, ShieldAlert } from 'lucide-react';
import { TabType } from './types';

interface IPManagementTabsProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function IPManagementTabs({ activeTab, onTabChange }: IPManagementTabsProps) {
  const tabs = [
    {
      id: 'unified' as const,
      label: '통합 뷰',
      icon: Layers,
      activeClass: 'border-blue-500 text-blue-600',
    },
    {
      id: 'whitelist' as const,
      label: '화이트리스트',
      icon: ShieldCheck,
      activeClass: 'border-green-500 text-green-600',
    },
    {
      id: 'blacklist' as const,
      label: '블랙리스트',
      icon: ShieldAlert,
      activeClass: 'border-red-500 text-red-600',
    },
  ];

  return (
    <div className="flex gap-4 border-b border-gray-200">
      {tabs.map(({ id, label, icon: Icon, activeClass }) => (
        <button
          key={id}
          onClick={() => onTabChange(id)}
          className={`px-6 py-3 font-medium border-b-2 transition flex items-center gap-2 ${
            activeTab === id ? activeClass : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Icon className="h-4 w-4" />
          {label}
        </button>
      ))}
    </div>
  );
}
