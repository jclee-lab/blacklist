import { Suspense } from 'react';
import FortinetClient from './FortinetClient';

export default async function FortinetPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">FortiGate 연동</h1>
        <p className="text-gray-600">FortiGate 방화벽 블랙리스트 연동 관리</p>
      </div>

      <Suspense fallback={<div className="text-center py-8">로딩 중...</div>}>
        <FortinetClient />
      </Suspense>
    </main>
  );
}
