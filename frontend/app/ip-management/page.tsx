'use client';

import { Suspense } from 'react';
import { Shield } from 'lucide-react';
import IPManagementClient from './IPManagementClient';
import PageHeader from '@/components/ui/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function IPManagementPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <PageHeader
        title="IP 관리"
        description="화이트리스트 및 블랙리스트 통합 관리"
        icon={Shield}
      />

      <Suspense fallback={<LoadingSpinner message="데이터 로딩 중..." />}>
        <IPManagementClient />
      </Suspense>
    </main>
  );
}
