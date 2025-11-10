import { Suspense } from 'react';
import IPManagementClient from './IPManagementClient';

export default async function IPManagementPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">IP 관리</h1>
        <p className="text-gray-600">화이트리스트 및 블랙리스트 통합 관리</p>
      </div>

      <Suspense fallback={<div className="text-center py-8">로딩 중...</div>}>
        <IPManagementClient />
      </Suspense>
    </main>
  );
}
