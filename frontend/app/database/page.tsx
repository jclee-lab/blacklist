'use client';

import { useState, Suspense } from 'react';
import { Database, Table2 } from 'lucide-react';
import DatabaseOverviewClient from './DatabaseOverviewClient';
import TableBrowserClient from './TableBrowserClient';

export default function DatabasePage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'browser'>('overview');

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">데이터베이스</h1>
        <p className="text-gray-600">PostgreSQL 테이블 현황 및 데이터 브라우징</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center transition ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Database className="h-5 w-5 mr-2" />
            테이블 현황
          </button>
          <button
            onClick={() => setActiveTab('browser')}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center transition ${
              activeTab === 'browser'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Table2 className="h-5 w-5 mr-2" />
            데이터 브라우저
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <Suspense fallback={<div className="text-center py-8">로딩 중...</div>}>
        {activeTab === 'overview' ? (
          <DatabaseOverviewClient />
        ) : (
          <TableBrowserClient />
        )}
      </Suspense>
    </main>
  );
}
