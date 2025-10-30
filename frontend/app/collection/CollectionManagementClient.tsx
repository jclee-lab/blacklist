'use client';

import { useState, useEffect } from 'react';
import { Settings, CheckCircle, XCircle, Play, RefreshCw, Key, AlertCircle, Lock, Unlock } from 'lucide-react';

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
  last_collection?: string;
  next_collection?: string;
  success: boolean;
  collectors?: Record<string, any>;
}

const COLLECTORS = ['REGTECH', 'SECUDIUM'];

export default function CollectionManagementClient() {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState<Record<string, boolean>>({});
  const [triggeringCollection, setTriggeringCollection] = useState<Record<string, boolean>>({});

  // Removed dropdown - show all collectors as cards

  // Modal state for credential management
  const [showCredentialModal, setShowCredentialModal] = useState(false);
  const [editingService, setEditingService] = useState<string | null>(null);
  const [credentialForm, setCredentialForm] = useState({
    username: '',
    password: '',
    enabled: true,
    collection_interval: 'daily',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch credentials for all collectors
      const credPromises = COLLECTORS.map(async (service) => {
        try {
          const res = await fetch(`/api/collection/credentials/${service}`);
          if (res.ok) {
            const data = await res.json();
            if (data.success) {
              return {
                service_name: data.service_name,
                username: data.username,
                enabled: data.enabled,
                collection_interval: data.collection_interval,
                last_collection: data.last_collection,
                connection_status: 'unknown' as const,
              };
            }
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
      const statusRes = await fetch(`/api/collection/status`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setCollectionStatus(statusData);
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
      const res = await fetch(`/api/collection/credentials/${serviceName}/test`, {
        method: 'POST',
      });
      const data = await res.json();

      // Update credential status
      setCredentials((prev) =>
        prev.map((cred) =>
          cred.service_name === serviceName
            ? {
                ...cred,
                connection_status: data.status,
                status_message: data.message,
              }
            : cred
        )
      );

      if (data.status === 'connected') {
        alert(`✅ ${serviceName} 연결 테스트 성공!`);
      } else if (data.status === 'locked') {
        alert(`🔒 ${serviceName} 계정이 잠겼습니다. 관리자에게 문의하세요.`);
      } else {
        alert(`❌ ${serviceName} 연결 실패: ${data.message}`);
      }
    } catch (error) {
      alert(`❌ ${serviceName} 연결 테스트 중 오류 발생`);
    } finally {
      setTestingConnection((prev) => ({ ...prev, [serviceName]: false }));
    }
  };

  const triggerCollection = async (serviceName: string) => {
    setTriggeringCollection((prev) => ({ ...prev, [serviceName]: true }));
    try {
      const res = await fetch(`/api/collection/trigger/${serviceName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: false }),
      });
      const data = await res.json();

      if (data.success) {
        alert(`✅ ${serviceName} 수집 작업이 시작되었습니다!`);
        fetchData();
      } else {
        alert(`❌ ${serviceName} 수집 실패: ${data.error || '알 수 없는 오류'}`);
      }
    } catch (error) {
      alert(`❌ ${serviceName} 수집 작업 중 오류 발생`);
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
      const res = await fetch(`/api/collection/credentials/${editingService}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentialForm),
      });

      const data = await res.json();

      if (data.success) {
        alert(`✅ ${editingService} 인증 정보가 저장되었습니다!`);
        setShowCredentialModal(false);
        setEditingService(null);
        setCredentialForm({ username: '', password: '', enabled: true, collection_interval: 'daily' });
        fetchData();
      } else {
        alert(`❌ 저장 실패: ${data.error || '알 수 없는 오류'}`);
      }
    } catch (error) {
      alert('❌ 저장 중 오류 발생');
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

  const getConnectionStatusBadge = (status?: string, message?: string) => {
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
      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">수집 상태</p>
              <p className={`text-2xl font-bold mt-2 ${collectionStatus?.is_running ? 'text-green-600' : 'text-gray-900'}`}>
                {collectionStatus?.is_running ? '실행 중' : '대기 중'}
              </p>
            </div>
            {collectionStatus?.is_running ? (
              <Play className="h-12 w-12 text-green-500" />
            ) : (
              <RefreshCw className="h-12 w-12 text-gray-400" />
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">설정된 수집기</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">{credentials.length}</p>
              <p className="text-xs text-gray-500 mt-1">
                활성: {credentials.filter((c) => c.enabled).length}개
              </p>
            </div>
            <Settings className="h-12 w-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">마지막 수집</p>
              <p className="text-sm font-medium text-gray-900 mt-2">
                {collectionStatus?.last_collection
                  ? new Date(collectionStatus.last_collection).toLocaleString('ko-KR')
                  : '없음'}
              </p>
            </div>
            <RefreshCw className="h-12 w-12 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Credentials Management - Card Grid */}
      <div>
        <div className="px-6 py-4 flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Key className="h-5 w-5 text-gray-700 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">인증 정보 관리</h3>
          </div>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </button>
        </div>

        {credentials.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {credentials.map((cred) => (
                <div key={cred.service_name} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  {/* Card Header with Color */}
                  <div className={`px-6 py-4 ${
                    cred.service_name === 'REGTECH'
                      ? 'bg-gradient-to-r from-pink-500 to-pink-600'
                      : 'bg-gradient-to-r from-blue-500 to-blue-600'
                  }`}>
                    <h4 className="text-xl font-bold text-white">{cred.service_name}</h4>
                  </div>

                  {/* Card Body */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        {getConnectionStatusIcon(cred.connection_status)}
                        <div>
                          <p className="text-sm font-medium text-gray-700">사용자명: {cred.username}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            수집 주기: {cred.collection_interval === 'daily' ? '일일' : cred.collection_interval === 'hourly' ? '시간별' : '주간'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getConnectionStatusBadge(cred.connection_status, cred.status_message)}
                      </div>
                    </div>

                  {cred.connection_status === 'locked' && (
                    <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800 flex items-center">
                        <Lock className="h-4 w-4 mr-2" />
                        <strong>경고:</strong> 계정이 잠겼습니다. 서비스 관리자에게 문의하여 계정을 활성화하세요.
                      </p>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 mt-3">
                    <button
                      onClick={() => testConnection(cred.service_name)}
                      disabled={testingConnection[cred.service_name] || !cred.enabled}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      title={!cred.enabled ? '수집이 비활성화되어 있습니다' : '연결 테스트 실행'}
                    >
                      {testingConnection[cred.service_name] ? (
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
                      onClick={() => triggerCollection(cred.service_name)}
                      disabled={triggeringCollection[cred.service_name] || !cred.enabled}
                      className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    >
                      {triggeringCollection[cred.service_name] ? (
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
                      onClick={() => openEditModal(cred.service_name)}
                      className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm flex items-center"
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      설정 변경
                    </button>
                  </div>

                    {cred.last_collection && (
                      <p className="text-xs text-gray-500 mt-3">
                        마지막 수집: {new Date(cred.last_collection).toLocaleString('ko-KR')}
                      </p>
                    )}
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
            <p>설정된 인증 정보가 없습니다</p>
          </div>
        )}
      </div>

      {/* Credential Edit Modal */}
      {showCredentialModal && editingService && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-gray-900 mb-4">{editingService} 인증 정보 수정</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">사용자명</label>
                <input
                  type="text"
                  value={credentialForm.username}
                  onChange={(e) => setCredentialForm({ ...credentialForm, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="사용자명 입력"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input
                  type="password"
                  value={credentialForm.password}
                  onChange={(e) => setCredentialForm({ ...credentialForm, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="새 비밀번호 입력 (변경 시만)"
                />
                <p className="text-xs text-gray-500 mt-1">비밀번호를 변경하지 않으려면 비워두세요</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">수집 주기</label>
                <select
                  value={credentialForm.collection_interval}
                  onChange={(e) => setCredentialForm({ ...credentialForm, collection_interval: e.target.value })}
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
                  onChange={(e) => setCredentialForm({ ...credentialForm, enabled: e.target.checked })}
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
                  setCredentialForm({ username: '', password: '', enabled: true, collection_interval: 'daily' });
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
