'use client';

import { useState, Suspense } from 'react';
import { Database, Table2 } from 'lucide-react';
import DatabaseOverviewClient from './DatabaseOverviewClient';
import TableBrowserClient from './TableBrowserClient';
import PageHeader from '@/components/ui/PageHeader';
import Tabs from '@/components/ui/Tabs';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function DatabasePage() {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const tabs = [
    { id: 'overview', label: '테이블 현황', icon: Database },
    { id: 'browser', label: '데이터 브라우저', icon: Table2 },
  ];

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <PageHeader
        title="데이터베이스"
        description="PostgreSQL 테이블 현황 및 데이터 브라우징"
        icon={Database}
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <Suspense fallback={<LoadingSpinner message="데이터 로딩 중..." />}>
        {activeTab === 'overview' ? <DatabaseOverviewClient /> : <TableBrowserClient />}
      </Suspense>
    </main>
  );
}
