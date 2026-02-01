'use client';

import { useState, useEffect } from 'react';
import {
  Settings,
  CheckCircle,
  XCircle,
  Play,
  RefreshCw,
  AlertCircle,
  Lock,
  Clock,
  Database,
  TrendingUp,
} from 'lucide-react';
import {
  getCredential,
  getCollectionStatus,
  getBlacklistStats,
  testCredential,
  triggerCollectionService,
  updateCredential,
} from '@/lib/api';

interface CollectorStatus {
  enabled: boolean;
  error_count: number;
  interval_seconds: number;
  last_run: string | null;
  next_run: string | null;
  run_count: number;
}

interface Credential {
  service_name: string;
  username: string;
  enabled: boolean;
  collection_interval?: string;
  last_collection?: string;
  connection_status?: 'connected' | 'locked' | 'failed' | 'unknown';
  status_message?: string;
}

interface CollectionStatus {
  is_running: boolean;
  collectors: Record<string, CollectorStatus>;
}

interface BlacklistStats {
  total_ips: number;
  sources: Array<{ source: string; count: number }>;
  last_update: string;
}

const COLLECTORS = ['REGTECH'];

export default function CollectionManagementClient() {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatus | null>(null);
  const [blacklistStats, setBlacklistStats] = useState<BlacklistStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState<Record<string, boolean>>({});
  const [triggeringCollection, setTriggeringCollection] = useState<Record<string, boolean>>({});

  // Modal state for credential management
  const [showCredentialModal, setShowCredentialModal] = useState(false);
  const [editingService, setEditingService] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);
  const [credentialForm, setCredentialForm] = useState({
    username: '',
    password: '',
    enabled: true,
    collection_interval: 'daily',
  });

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch credentials for all collectors
      const credPromises = COLLECTORS.map(async (service) => {
        try {
          const data = await getCredential(service.toLowerCase());
          if (data && data.success && data.data) {
            return {
              service_name: data.data.service_name,
              username: data.data.username,
              enabled: data.data.enabled,
              collection_interval: data.data.collection_interval,
              last_collection: data.data.last_collection,
              connection_status: 'unknown' as const,
            };
          }
        } catch (error) {
          console.error(`Failed to fetch ${service} credentials:`, error);
        }
        return null;
      });

      const credResults = await Promise.all(credPromises);
      const validCreds = credResults.filter((c) => c !== null) as Credential[];
      setCredentials(validCreds);

      // Fetch collection status
      const statusData = await getCollectionStatus();
      if (statusData && statusData.success && statusData.data) {
        setCollectionStatus(statusData.data);
      }

      // Fetch blacklist stats
      const statsData = await getBlacklistStats();
      if (statsData && statsData.success && statsData.data) {
        setBlacklistStats(statsData.data);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (serviceName: string) => {
    setTestingConnection((prev) => ({ ...prev, [serviceName]: true }));
    try {
      const data = await testCredential(serviceName.toLowerCase());

      // Update credential status
      setCredentials((prev) =>
        prev.map((cred) =>
          cred.service_name === serviceName
            ? {
                ...cred,
                connection_status: data.success ? 'connected' : 'failed',
                status_message: data.message || data.error,
              }
            : cred
        )
      );

      if (data.success) {
        setNotification({ type: 'success', message: `${serviceName} 연결 테스트 성공!` });
      } else {
        setNotification({
          type: 'error',
          message: `${serviceName} 연결 실패: ${data.message || data.error}`,
        });
      }
    } catch (error) {
      setNotification({ type: 'error', message: `${serviceName} 연결 테스트 중 오류 발생` });
    } finally {
      setTestingConnection((prev) => ({ ...prev, [serviceName]: false }));
    }
  };

  const triggerCollection = async (serviceName: string) => {
    setTriggeringCollection((prev) => ({ ...prev, [serviceName]: true }));
    try {
      const data = await triggerCollectionService(serviceName.toLowerCase(), { force: true });

      if (data.success) {
        setNotification({ type: 'success', message: `${serviceName} 수집 작업이 시작되었습니다!` });
        setTimeout(fetchData, 2000);
      } else {
        setNotification({
          type: 'error',
          message: `${serviceName} 수집 실패: ${data.error || '알 수 없는 오류'}`,
        });
      }
    } catch (error) {
      setNotification({ type: 'error', message: `${serviceName} 수집 작업 중 오류 발생` });
    } finally {
      setTriggeringCollection((prev) => ({ ...prev, [serviceName]: false }));
    }
  };

  const openEditModal = (serviceName: string) => {
    const cred = credentials.find((c) => c.service_name === serviceName);
    if (cred) {
      setEditingService(serviceName);
      setCredentialForm({
        username: cred.username,
        password: '',
        enabled: cred.enabled,
        collection_interval: cred.collection_interval || 'daily',
      });
      setShowCredentialModal(true);
    }
  };

  const saveCredentials = async () => {
    if (!editingService) return;

    try {
      const data = await updateCredential(editingService.toLowerCase(), credentialForm);

      if (data.success) {
        setNotification({
          type: 'success',
          message: `${editingService} 인증 정보가 저장되었습니다!`,
        });
        setShowCredentialModal(false);
        setEditingService(null);
        setCredentialForm({
          username: '',
          password: '',
          enabled: true,
          collection_interval: 'daily',
        });
        fetchData();
      } else {
        setNotification({
          type: 'error',
          message: `저장 실패: ${data.error || '알 수 없는 오류'}`,
        });
      }
    } catch (error) {
      setNotification({ type: 'error', message: '저장 중 오류 발생' });
    }
  };

  const getConnectionStatusIcon = (status?: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'locked':
        return <Lock className="h-5 w-5 text-red-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getConnectionStatusBadge = (status?: string) => {
    switch (status) {
      case 'connected':
        return (
          <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full flex items-center">
            <CheckCircle className="h-4 w-4 inline mr-1" />
            연결 성공
          </span>
        );
      case 'locked':
        return (
          <span className="px-3 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded-full flex items-center">
            <Lock className="h-4 w-4 inline mr-1" />
            계정 잠김
          </span>
        );
      case 'failed':
        return (
          <span className="px-3 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded-full flex items-center">
            <XCircle className="h-4 w-4 inline mr-1" />
            연결 실패
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded-full flex items-center">
            <AlertCircle className="h-4 w-4 inline mr-1" />
            미테스트
          </span>
        );
    }
  };

  const formatInterval = (seconds: number) => {
    if (seconds >= 86400) return `${Math.floor(seconds / 86400)}일`;
    if (seconds >= 3600) return `${Math.floor(seconds / 3600)}시간`;
    return `${Math.floor(seconds / 60)}분`;
  };

  const getSourceCount = (source: string) => {
    if (!blacklistStats?.sources) return 0;
    const found = blacklistStats.sources.find((s) => s.source === source);
    return found?.count || 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">데이터 로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {notification && (
        <div
          role="alert"
          aria-live="polite"
          className={`rounded-md p-4 ${notification.type === 'success' ? 'bg-green-50' : 'bg-red-50'}`}
        >
          <div className="flex justify-between items-center">
            <p
              className={`text-sm font-medium ${notification.type === 'success' ? 'text-green-800' : 'text-red-800'}`}
            >
              {notification.message}
            </p>
            <button
              type="button"
              onClick={() => setNotification(null)}
              className={`ml-4 text-sm font-medium ${notification.type === 'success' ? 'text-green-600 hover:text-green-500' : 'text-red-600 hover:text-red-500'}`}
            >
              닫기
            </button>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">수집 상태</p>
              {(() => {
                const isCollecting = Object.values(triggeringCollection).some((v) => v);
                return (
                  <p
                    className={`text-2xl font-bold mt-2 ${isCollecting ? 'text-green-600' : 'text-gray-900'}`}
                  >
                    {isCollecting ? '수집 중' : '대기 중'}
                  </p>
                );
              })()}
            </div>
            {Object.values(triggeringCollection).some((v) => v) ? (
              <RefreshCw className="h-12 w-12 text-green-500 animate-spin" />
            ) : (
              <RefreshCw className="h-12 w-12 text-gray-400" />
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">현재 등록 IP</p>
              <p className="text-2xl font-bold text-blue-600 mt-2">
                {blacklistStats?.total_ips?.toLocaleString() || 0}
              </p>
            </div>
            <Database className="h-12 w-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">활성 수집기</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {collectionStatus?.collectors
                  ? Object.values(collectionStatus.collectors).filter((c) => c.enabled).length
                  : 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                전체:{' '}
                {collectionStatus?.collectors ? Object.keys(collectionStatus.collectors).length : 0}
                개
              </p>
            </div>
            <Settings className="h-12 w-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">마지막 업데이트</p>
              <p className="text-sm font-medium text-gray-900 mt-2">
                {blacklistStats?.last_update
                  ? new Date(blacklistStats.last_update).toLocaleString('ko-KR')
                  : '없음'}
              </p>
            </div>
            <Clock className="h-12 w-12 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Collector Cards */}
      <div>
        <div className="px-6 py-4 flex items-center justify-between mb-6">
          <div className="flex items-center">
            <TrendingUp className="h-5 w-5 text-gray-700 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">수집기 현황</h3>
          </div>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {collectionStatus?.collectors &&
            Object.entries(collectionStatus.collectors).map(([name, collector]) => {
              const cred = credentials.find((c) => c.service_name === name);
              const sourceCount = getSourceCount(name);

              return (
                <div key={name} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  {/* Card Header with Color */}
                  <div
                    className={`px-6 py-4 ${
                      name === 'REGTECH'
                        ? 'bg-gradient-to-r from-pink-500 to-pink-600'
                        : name === 'SECUDIUM'
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600'
                          : 'bg-gradient-to-r from-gray-500 to-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="text-xl font-bold text-white">{name}</h4>
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          collector.enabled ? 'bg-white/20 text-white' : 'bg-red-500 text-white'
                        }`}
                      >
                        {collector.enabled ? '활성' : '비활성'}
                      </span>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-6">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">{collector.run_count}</p>
                        <p className="text-xs text-gray-500">수집 횟수</p>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-red-600">{collector.error_count}</p>
                        <p className="text-xs text-gray-500">오류 횟수</p>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">
                          {sourceCount.toLocaleString()}
                        </p>
                        <p className="text-xs text-gray-500">누적 수집</p>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">사용자명:</span>
                        <span className="font-medium">{cred?.username || '-'}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">수집 주기:</span>
                        <span className="font-medium">
                          {formatInterval(collector.interval_seconds)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">마지막 수집:</span>
                        <span className="font-medium">
                          {collector.last_run
                            ? new Date(collector.last_run).toLocaleString('ko-KR')
                            : '없음'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">다음 수집:</span>
                        <span className="font-medium text-blue-600">
                          {collector.next_run
                            ? new Date(collector.next_run).toLocaleString('ko-KR')
                            : '대기 중'}
                        </span>
                      </div>
                    </div>

                    {/* Connection Status */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        {getConnectionStatusIcon(cred?.connection_status)}
                        <span className="text-sm text-gray-600">연결 상태</span>
                      </div>
                      {getConnectionStatusBadge(cred?.connection_status)}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => testConnection(name)}
                        disabled={testingConnection[name] || !collector.enabled}
                        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        {testingConnection[name] ? (
                          <>
                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                            테스트 중...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            연결 테스트
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => triggerCollection(name)}
                        disabled={triggeringCollection[name] || !collector.enabled}
                        className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        {triggeringCollection[name] ? (
                          <>
                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                            수집 중...
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-2" />
                            즉시 수집
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => openEditModal(name)}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm flex items-center"
                      >
                        <Settings className="h-4 w-4 mr-2" />
                        설정
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Credential Edit Modal */}
      {showCredentialModal && editingService && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => {
            setShowCredentialModal(false);
            setEditingService(null);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setShowCredentialModal(false);
              setEditingService(null);
            }
          }}
          role="presentation"
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="credential-modal-title"
            className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="credential-modal-title" className="text-xl font-bold text-gray-900 mb-4">
              {editingService} 인증 정보 수정
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">사용자명</label>
                <input
                  type="text"
                  value={credentialForm.username}
                  onChange={(e) =>
                    setCredentialForm({ ...credentialForm, username: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="사용자명 입력"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input
                  type="password"
                  value={credentialForm.password}
                  onChange={(e) =>
                    setCredentialForm({ ...credentialForm, password: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="새 비밀번호 입력 (변경 시만)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  비밀번호를 변경하지 않으려면 비워두세요
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">수집 주기</label>
                <select
                  value={credentialForm.collection_interval}
                  onChange={(e) =>
                    setCredentialForm({ ...credentialForm, collection_interval: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="hourly">시간별</option>
                  <option value="daily">일일</option>
                  <option value="weekly">주간</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={credentialForm.enabled}
                  onChange={(e) =>
                    setCredentialForm({ ...credentialForm, enabled: e.target.checked })
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enabled" className="ml-2 block text-sm text-gray-700">
                  수집 활성화
                </label>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={saveCredentials}
                disabled={!credentialForm.username}
                className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition disabled:opacity-50"
              >
                저장
              </button>
              <button
                onClick={() => {
                  setShowCredentialModal(false);
                  setEditingService(null);
                  setCredentialForm({
                    username: '',
                    password: '',
                    enabled: true,
                    collection_interval: 'daily',
                  });
                }}
                className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
