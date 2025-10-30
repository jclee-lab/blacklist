import { Activity, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

// Server-side data fetching - matching main dashboard pattern
async function getStats() {
  const res = await fetch('http://blacklist-app:2542/api/stats', {
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

async function getCollectionStatus() {
  const res = await fetch('http://blacklist-app:2542/api/collection/status', {
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

async function getSystemStatus() {
  const res = await fetch('http://blacklist-app:2542/api/status', {
    cache: 'no-store',
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function MonitoringPage() {
  // Fetch data server-side
  const [stats, collectionStatus, systemStatus] = await Promise.all([
    getStats().catch(() => null),
    getCollectionStatus().catch(() => null),
    getSystemStatus().catch(() => null),
  ]);

  const history = collectionStatus?.data?.recent_collections || [];

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">실시간 모니터링</h1>
        <p className="text-gray-600">시스템 상태 및 수집 활동 모니터링</p>
      </div>

      {/* 시스템 메트릭 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">시스템 상태</p>
              <p className={`text-2xl font-bold ${
                systemStatus?.service?.status === 'healthy'
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}>
                {systemStatus?.service?.status === 'healthy' ? '정상' : '오류'}
              </p>
            </div>
            <Activity className={`h-10 w-10 ${
              systemStatus?.service?.status === 'healthy'
                ? 'text-green-500'
                : 'text-red-500'
            }`} />
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">수집 활성화</p>
              <p className={`text-2xl font-bold ${
                systemStatus?.collection?.collection_enabled
                  ? 'text-blue-600'
                  : 'text-gray-600'
              }`}>
                {systemStatus?.collection?.collection_enabled ? '활성' : '비활성'}
              </p>
            </div>
            <TrendingUp className={`h-10 w-10 ${
              systemStatus?.collection?.collection_enabled
                ? 'text-blue-500'
                : 'text-gray-500'
            }`} />
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">활성 IP</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.active_ips?.toLocaleString() || '0'}
              </p>
            </div>
            <AlertTriangle className="h-10 w-10 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* 최근 수집 활동 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">최근 수집 활동</h2>
        </div>
        <div className="p-6">
          {history && history.length > 0 ? (
            <div className="space-y-4">
              {history.slice(0, 10).map((log: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4 flex-1 min-w-0">
                    {log.success ? (
                      <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-500 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">{log.service_name || 'N/A'}</p>
                      <p className="text-sm text-gray-600 truncate">
                        {log.items_collected || 0}개 수집
                        {log.error_message && ` - ${log.error_message}`}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 whitespace-nowrap ml-4">
                    {log.collection_date ? new Date(log.collection_date).toLocaleString('ko-KR') : 'N/A'}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-8">수집 활동 없음</p>
          )}
        </div>
      </div>
    </main>
  );
}
