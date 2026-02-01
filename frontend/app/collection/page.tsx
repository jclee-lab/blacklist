'use client';

import { Suspense, useCallback } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Settings, History, Key, Database, List } from 'lucide-react';
import CollectionManagementClient from './CollectionManagementClient';
import CollectionHistoryClient from './CollectionHistoryClient';
import CredentialsManagementClient from './CredentialsManagementClient';
import CollectedDataClient from './CollectedDataClient';
import PageHeader from '@/components/ui/PageHeader';
import Tabs from '@/components/ui/Tabs';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

const VALID_TABS = ['management', 'data', 'credentials', 'history'] as const;
type TabId = (typeof VALID_TABS)[number];

function CollectionContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const tabParam = searchParams.get('tab');
  const activeTab: TabId = VALID_TABS.includes(tabParam as TabId)
    ? (tabParam as TabId)
    : 'management';

  const setActiveTab = useCallback(
    (tab: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (tab === 'management') {
        params.delete('tab');
      } else {
        params.set('tab', tab);
      }
      const queryString = params.toString();
      router.push(queryString ? `${pathname}?${queryString}` : pathname);
    },
    [searchParams, router, pathname]
  );

  const tabs = [
    { id: 'management', label: '수집 관리', icon: Settings },
    { id: 'data', label: '수집 데이터', icon: List },
    { id: 'credentials', label: '인증정보', icon: Key },
    { id: 'history', label: '수집 이력', icon: History },
  ];

  return (
    <>
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <Suspense fallback={<LoadingSpinner message="데이터 로딩 중..." />}>
        {activeTab === 'management' ? (
          <CollectionManagementClient />
        ) : activeTab === 'data' ? (
          <CollectedDataClient />
        ) : activeTab === 'credentials' ? (
          <CredentialsManagementClient />
        ) : (
          <CollectionHistoryClient />
        )}
      </Suspense>
    </>
  );
}

export default function CollectionPage() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <PageHeader
        title="데이터 수집"
        description="REGTECH 데이터 수집 관리 및 이력"
        icon={Database}
      />

      <Suspense fallback={<LoadingSpinner message="로딩 중..." />}>
        <CollectionContent />
      </Suspense>
    </main>
  );
}
