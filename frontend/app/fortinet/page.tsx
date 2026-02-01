'use client';

import { Suspense } from 'react';
import { Shield } from 'lucide-react';
import FortinetClient from './FortinetClient';
import PageHeader from '@/components/ui/PageHeader';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function FortinetPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <PageHeader
        title="FortiGate 연동"
        description="FortiGate 방화벽 블랙리스트 연동 관리"
        icon={Shield}
      />

      <Suspense fallback={<LoadingSpinner message="데이터 로딩 중..." />}>
        <FortinetClient />
      </Suspense>
    </main>
  );
}
