'use client';

import { useState, useEffect } from 'react';
import { Save, Eye, EyeOff, Lock, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { getCredential, updateCredential } from '@/lib/api';

interface Credential {
  service_name: string;
  username: string;
  password: string;
  enabled: boolean;
  collection_interval: string;
  last_collection: string | null;
}

export default function CredentialsManagementClient() {
  const [regtechCred, setRegtechCred] = useState<Credential | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState<{ [key: string]: boolean }>({});
  const [editMode, setEditMode] = useState<{ [key: string]: boolean }>({});
  const [formData, setFormData] = useState<{ [key: string]: Partial<Credential> }>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    setLoading(true);
    try {
      const regtechData = await getCredential('regtech');

      if (regtechData) {
        setRegtechCred(regtechData.data);
        setFormData((prev) => ({ ...prev, regtech: regtechData.data }));
      }
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
      setMessage({ type: 'error', text: '인증정보 로드 실패' });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (source: string) => {
    setEditMode({ ...editMode, [source]: true });
  };

  const handleCancel = (source: string) => {
    setEditMode({ ...editMode, [source]: false });
    // Reset form data
    if (source === 'regtech' && regtechCred) {
      setFormData({ ...formData, regtech: regtechCred });
    }
  };

  const handleSave = async (source: string) => {
    setSaving(source);
    setMessage(null);

    try {
      const data = formData[source];
      const result = await updateCredential(source, data);

      if (result && result.success) {
        setMessage({ type: 'success', text: `${source.toUpperCase()} 인증정보 저장 완료` });
        setEditMode({ ...editMode, [source]: false });
        await fetchCredentials();
      } else {
        setMessage({ type: 'error', text: result.error || '저장 실패' });
      }
    } catch (error) {
      console.error('Save error:', error);
      setMessage({ type: 'error', text: '저장 중 오류 발생' });
    } finally {
      setSaving(null);
    }
  };

  const handleInputChange = (source: string, field: string, value: string | boolean | number) => {
    setFormData({
      ...formData,
      [source]: {
        ...formData[source],
        [field]: value,
      },
    });
  };

  const togglePasswordVisibility = (source: string) => {
    setShowPassword({ ...showPassword, [source]: !showPassword[source] });
  };

  const renderCredentialCard = (
    source: string,
    credential: Credential | null,
    displayName: string,
    color: string
  ) => {
    const isEditing = editMode[source];
    const isSaving = saving === source;
    const data = formData[source] || credential || {};

    return (
      <div className={`bg-white rounded-lg shadow-md border-l-4 ${color}`}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div
                className={`p-2 rounded-lg ${color.replace('border-', 'bg-').replace('500', '100')}`}
              >
                <Lock className={`h-6 w-6 ${color.replace('border-', 'text-')}`} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">{displayName}</h3>
                <p className="text-sm text-gray-500">
                  {credential?.service_name || source.toUpperCase()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {credential && (
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    data.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {data.enabled ? '활성' : '비활성'}
                </span>
              )}
            </div>
          </div>

          {!credential && !isEditing ? (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">인증정보가 등록되지 않았습니다</p>
              <button
                onClick={() => handleEdit(source)}
                className={`px-4 py-2 ${color.replace('border-', 'bg-')} text-white rounded-lg hover:opacity-90 transition`}
              >
                등록하기
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">사용자명</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={data.username || ''}
                    onChange={(e) => handleInputChange(source, 'username', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="사용자명 입력"
                  />
                ) : (
                  <p className="text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded">
                    {data.username || '-'}
                  </p>
                )}
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                {isEditing ? (
                  <div className="relative">
                    <input
                      type={showPassword[source] ? 'text' : 'password'}
                      value={data.password === '***masked***' ? '' : data.password || ''}
                      onChange={(e) => handleInputChange(source, 'password', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                      placeholder="비밀번호 입력 (변경 시에만)"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility(source)}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword[source] ? (
                        <EyeOff className="h-5 w-5" />
                      ) : (
                        <Eye className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                ) : (
                  <p className="text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded">
                    ••••••••••••
                  </p>
                )}
              </div>

              {/* Collection Interval */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">수집 주기</label>
                {isEditing ? (
                  <select
                    value={data.collection_interval || 'daily'}
                    onChange={(e) =>
                      handleInputChange(source, 'collection_interval', e.target.value)
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="hourly">매시간</option>
                    <option value="daily">매일</option>
                    <option value="weekly">매주</option>
                  </select>
                ) : (
                  <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded">
                    {data.collection_interval === 'hourly'
                      ? '매시간'
                      : data.collection_interval === 'daily'
                        ? '매일'
                        : data.collection_interval === 'weekly'
                          ? '매주'
                          : '-'}
                  </p>
                )}
              </div>

              {/* Enabled */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">자동 수집 활성화</span>
                {isEditing ? (
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={data.enabled || false}
                      onChange={(e) => handleInputChange(source, 'enabled', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                ) : (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      data.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {data.enabled ? 'ON' : 'OFF'}
                  </span>
                )}
              </div>

              {/* Last Collection */}
              {data.last_collection && (
                <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                  <span className="font-medium">마지막 수집:</span>{' '}
                  {new Date(data.last_collection).toLocaleString('ko-KR')}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4 border-t">
                {isEditing ? (
                  <>
                    <button
                      onClick={() => handleSave(source)}
                      disabled={isSaving}
                      className={`flex-1 flex items-center justify-center px-4 py-2 ${color.replace('border-', 'bg-')} text-white rounded-lg hover:opacity-90 transition disabled:opacity-50`}
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          저장 중...
                        </>
                      ) : (
                        <>
                          <Save className="h-5 w-5 mr-2" />
                          저장
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleCancel(source)}
                      disabled={isSaving}
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition disabled:opacity-50"
                    >
                      취소
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleEdit(source)}
                    className={`w-full px-4 py-2 ${color.replace('border-', 'bg-')} text-white rounded-lg hover:opacity-90 transition`}
                  >
                    수정
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">인증정보 로드 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Alert Message */}
      {message && (
        <div
          className={`p-4 rounded-lg flex items-center space-x-3 ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="h-5 w-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
          )}
          <p className="font-medium">{message.text}</p>
          <button
            onClick={() => setMessage(null)}
            className="ml-auto text-gray-500 hover:text-gray-700"
          >
            ×
          </button>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">보안 안내</h3>
            <p className="mt-1 text-sm text-blue-700">
              모든 인증정보는 AES-256 암호화되어 데이터베이스에 안전하게 저장됩니다. 비밀번호는
              마스킹되어 표시되며, 변경 시에만 입력하시면 됩니다.
            </p>
          </div>
        </div>
      </div>

      {/* Credentials Grid */}
      <div className="grid grid-cols-1 gap-6">
        {renderCredentialCard('regtech', regtechCred, 'REGTECH 인증정보', 'border-pink-500')}
      </div>
    </div>
  );
}
