'use client';

import { useState, useEffect } from 'react';
import { Download, RefreshCw, Shield, AlertCircle, CheckCircle, Activity, Clock } from 'lucide-react';

interface FortinetIP {
  id: number;
  ip_address: string;
  country?: string;
  reason?: string;
  confidence_level?: number;
  detection_date?: string;
  removal_date?: string;
  is_active: boolean;
}

interface ActiveSession {
  id: number;
  ip_address: string;
  country?: string;
  reason?: string;
  confidence_level?: number;
  detection_date?: string;
  removal_date?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  active_hours?: number;
  session_status: 'active' | 'inactive' | 'expired';
}

interface SessionStats {
  total_sessions: number;
  active_count: number;
  last_hour: number;
  last_24h: number;
  unique_countries: number;
}

interface FortinetStats {
  total_active: number;
  last_updated: string;
}

type ViewTab = 'active-ips' | 'active-sessions';

export default function FortinetClient() {
  const [activeTab, setActiveTab] = useState<ViewTab>('active-ips');
  const [activeIPs, setActiveIPs] = useState<FortinetIP[]>([]);
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [stats, setStats] = useState<FortinetStats | null>(null);
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://blacklist-app:2542';

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'active-ips') {
        const response = await fetch(`/api/fortinet/active-ips?limit=20`);

        if (!response.ok) {
          throw new Error('API 요청 실패');
        }

        const data = await response.json();

        if (data.success) {
          setActiveIPs(data.data || []);
          setStats({
            total_active: data.total || 0,
            last_updated: new Date().toISOString(),
          });
        } else {
          setError(data.error || '데이터를 불러올 수 없습니다');
        }
      } else if (activeTab === 'active-sessions') {
        const response = await fetch(`/api/fortinet/active-sessions?limit=50&hours=24`);

        if (!response.ok) {
          throw new Error('API 요청 실패');
        }

        const data = await response.json();

        if (data.success) {
          setActiveSessions(data.data || []);
          setSessionStats(data.stats || null);
        } else {
          setError(data.error || '데이터를 불러올 수 없습니다');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const downloadBlocklist = async () => {
    try {
      const response = await fetch(`/api/fortinet/blocklist`);
      const data = await response.json();

      if (data.success && data.blocklist) {
        // Create downloadable text file
        const blob = new Blob([data.blocklist], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fortinet-blocklist-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        alert('블랙리스트 다운로드 실패');
      }
    } catch (err) {
      alert('다운로드 중 오류 발생');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">데이터 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-red-500 mr-3" />
          <div>
            <h3 className="text-red-800 font-semibold">오류 발생</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('active-ips')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition ${
              activeTab === 'active-ips'
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center">
              <Shield className="h-5 w-5 mr-2" />
              활성 IP 목록
            </div>
          </button>
          <button
            onClick={() => setActiveTab('active-sessions')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition ${
              activeTab === 'active-sessions'
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center">
              <Activity className="h-5 w-5 mr-2" />
              활성 세션 모니터링
            </div>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {activeTab === 'active-ips' && stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">활성 차단 IP</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {stats?.total_active.toLocaleString() || '0'}
                </p>
              </div>
              <Shield className="h-12 w-12 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">마지막 업데이트</p>
                <p className="text-sm font-medium text-gray-900 mt-2">
                  {stats?.last_updated ? new Date(stats.last_updated).toLocaleString('ko-KR') : '-'}
                </p>
              </div>
              <CheckCircle className="h-12 w-12 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">FortiGate 상태</p>
                <p className="text-lg font-semibold text-green-600 mt-2">연동 가능</p>
              </div>
              <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      )}

      {/* Session Stats Cards */}
      {activeTab === 'active-sessions' && sessionStats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-xs">전체 세션</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {sessionStats.total_sessions.toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-xs">활성 세션</p>
            <p className="text-2xl font-bold text-green-600 mt-1">
              {sessionStats.active_count.toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-xs">최근 1시간</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">
              {sessionStats.last_hour.toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-xs">최근 24시간</p>
            <p className="text-2xl font-bold text-purple-600 mt-1">
              {sessionStats.last_24h.toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-xs">국가 수</p>
            <p className="text-2xl font-bold text-orange-600 mt-1">
              {sessionStats.unique_countries.toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h3 className="text-lg font-semibold text-gray-900">FortiGate 블랙리스트 관리</h3>
          <div className="flex gap-3">
            <button
              onClick={fetchData}
              className="flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              새로고침
            </button>
            <button
              onClick={downloadBlocklist}
              className="flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
            >
              <Download className="h-4 w-4 mr-2" />
              블랙리스트 다운로드
            </button>
          </div>
        </div>

        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">API 엔드포인트</h4>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-mono bg-white px-2 py-1 rounded text-blue-700">
                GET /api/fortinet/active-ips
              </span>
              <span className="text-gray-600 ml-2">- 활성 IP 목록 조회</span>
            </div>
            <div>
              <span className="font-mono bg-white px-2 py-1 rounded text-blue-700">
                GET /api/fortinet/blocklist
              </span>
              <span className="text-gray-600 ml-2">- FortiGate 형식 블랙리스트</span>
            </div>
          </div>
        </div>
      </div>

      {/* Active IPs Table */}
      {activeTab === 'active-ips' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              활성 차단 IP (최근 {activeIPs.length}개)
            </h3>
          </div>

          {activeIPs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP 주소</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">국가</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">탐지 사유</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">신뢰도</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">탐지일</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activeIPs.map((ip) => (
                    <tr key={ip.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-sm text-gray-900">{ip.ip_address}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-600">{ip.country || '-'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-600 line-clamp-2">{ip.reason || '-'}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          (ip.confidence_level || 0) >= 80
                            ? 'bg-red-100 text-red-800'
                            : (ip.confidence_level || 0) >= 50
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {ip.confidence_level || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {ip.detection_date ? new Date(ip.detection_date).toLocaleDateString('ko-KR') : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {ip.is_active ? (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            활성
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                            비활성
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-6 py-12 text-center text-gray-500">
              활성 IP가 없습니다
            </div>
          )}
        </div>
      )}

      {/* Active Sessions Table */}
      {activeTab === 'active-sessions' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              활성 세션 목록 (최근 24시간)
            </h3>
          </div>

          {activeSessions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP 주소</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">국가</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">세션 상태</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">활성 시간</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">신뢰도</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">탐지일</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">탐지 사유</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activeSessions.map((session) => (
                    <tr key={session.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-sm text-gray-900">{session.ip_address}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-600">{session.country || '-'}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {session.session_status === 'active' ? (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            <Activity className="h-3 w-3 mr-1" />
                            활성
                          </span>
                        ) : session.session_status === 'expired' ? (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                            <Clock className="h-3 w-3 mr-1" />
                            만료
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                            비활성
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {session.active_hours ? `${session.active_hours.toFixed(1)}시간` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          (session.confidence_level || 0) >= 80
                            ? 'bg-red-100 text-red-800'
                            : (session.confidence_level || 0) >= 50
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {session.confidence_level || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {session.detection_date ? new Date(session.detection_date).toLocaleString('ko-KR') : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-600 line-clamp-2">{session.reason || '-'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-6 py-12 text-center text-gray-500">
              활성 세션이 없습니다
            </div>
          )}
        </div>
      )}
    </div>
  );
}
