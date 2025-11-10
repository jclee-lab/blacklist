'use client';

import { useState, Suspense } from 'react';
import { Settings, History } from 'lucide-react';
import CollectionManagementClient from './CollectionManagementClient';
import CollectionHistoryClient from './CollectionHistoryClient';

export default function CollectionPage() {
  const [activeTab, setActiveTab] = useState<'management' | 'history'>('management');

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">데이터 수집</h1>
        <p className="text-gray-600">REGTECH, SECUDIUM 등 다중 소스 데이터 수집 관리 및 이력</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('management')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center transition ${
              activeTab === 'management'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Settings className="h-5 w-5 mr-2" />
            수집 관리
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center transition ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <History className="h-5 w-5 mr-2" />
            수집 이력
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <Suspense fallback={<div className="text-center py-8">로딩 중...</div>}>
        {activeTab === 'management' ? (
          <CollectionManagementClient />
        ) : (
          <CollectionHistoryClient />
        )}
      </Suspense>
    </main>
  );
}
