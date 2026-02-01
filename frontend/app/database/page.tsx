'use client';

import { Suspense } from 'react';
import { Database } from 'lucide-react';
import DatabaseOverviewClient from './DatabaseOverviewClient';
import PageHeader from '@/components/ui/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function DatabasePage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <PageHeader title="데이터베이스" description="PostgreSQL 테이블 현황" icon={Database} />

      <Suspense fallback={<LoadingSpinner message="데이터 로딩 중..." />}>
        <DatabaseOverviewClient />
      </Suspense>
    </main>
  );
}
