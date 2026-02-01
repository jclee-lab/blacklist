'use client';

import { useState, useEffect } from 'react';
import { Settings, Database, Shield, Bell, Clock, Save, RefreshCw } from 'lucide-react';
import PageHeader from '@/components/ui/PageHeader';
import Tabs from '@/components/ui/Tabs';

interface SystemSettings {
  auto_deactivate_expired: boolean;
  collection_interval_hours: number;
  cache_ttl_seconds: number;
  max_batch_size: number;
}

interface NotificationSettings {
  email_alerts: boolean;
  slack_alerts: boolean;
  alert_threshold: number;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<string>('system');
  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    auto_deactivate_expired: true,
    collection_interval_hours: 24,
    cache_ttl_seconds: 300,
    max_batch_size: 1000,
  });
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    email_alerts: false,
    slack_alerts: false,
    alert_threshold: 100,
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const tabs = [
    { id: 'system', label: '시스템 설정', icon: Settings },
    { id: 'database', label: '데이터베이스', icon: Database },
    { id: 'security', label: '보안', icon: Shield },
    { id: 'notifications', label: '알림', icon: Bell },
  ];

  const handleSaveSettings = async () => {
    setSaving(true);
    setMessage(null);
    try {
      // API call would go here
      await new Promise((resolve) => setTimeout(resolve, 500));
      setMessage({ type: 'success', text: '설정이 저장되었습니다.' });
    } catch (error) {
      setMessage({ type: 'error', text: '설정 저장에 실패했습니다.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <PageHeader title="설정" description="시스템 설정 및 환경 구성" icon={Settings} />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        {message && (
          <div
            className={`mb-4 p-3 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        {activeTab === 'system' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">시스템 설정</h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    해제일 경과 IP 자동 비활성화
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    removal_date가 지난 IP를 자동으로 비활성화합니다
                  </p>
                </div>
                <button
                  onClick={() =>
                    setSystemSettings((s) => ({
                      ...s,
                      auto_deactivate_expired: !s.auto_deactivate_expired,
                    }))
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    systemSettings.auto_deactivate_expired
                      ? 'bg-blue-600'
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      systemSettings.auto_deactivate_expired ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  수집 주기 (시간)
                </label>
                <input
                  type="number"
                  value={systemSettings.collection_interval_hours}
                  onChange={(e) =>
                    setSystemSettings((s) => ({
                      ...s,
                      collection_interval_hours: parseInt(e.target.value) || 24,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  min="1"
                  max="168"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  캐시 TTL (초)
                </label>
                <input
                  type="number"
                  value={systemSettings.cache_ttl_seconds}
                  onChange={(e) =>
                    setSystemSettings((s) => ({
                      ...s,
                      cache_ttl_seconds: parseInt(e.target.value) || 300,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  min="60"
                  max="3600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  배치 처리 크기
                </label>
                <input
                  type="number"
                  value={systemSettings.max_batch_size}
                  onChange={(e) =>
                    setSystemSettings((s) => ({
                      ...s,
                      max_batch_size: parseInt(e.target.value) || 1000,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  min="100"
                  max="10000"
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'database' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">데이터베이스 설정</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">호스트</p>
                <p className="text-lg font-medium text-gray-900 dark:text-white">
                  blacklist-postgres
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">포트</p>
                <p className="text-lg font-medium text-gray-900 dark:text-white">5432</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">데이터베이스</p>
                <p className="text-lg font-medium text-gray-900 dark:text-white">blacklist</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">연결 풀</p>
                <p className="text-lg font-medium text-gray-900 dark:text-white">3-8 connections</p>
              </div>
            </div>

            <div className="mt-4">
              <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600">
                <RefreshCw className="w-4 h-4" />
                연결 테스트
              </button>
            </div>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">보안 설정</h3>

            <div className="space-y-4">
              <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  보안 설정은 관리자만 변경할 수 있습니다. 인증 정보는 수집 관리 페이지에서
                  관리하세요.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">CSRF 보호</p>
                  <p className="text-lg font-medium text-green-600 dark:text-green-400">활성화</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Rate Limiting</p>
                  <p className="text-lg font-medium text-green-600 dark:text-green-400">활성화</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">인증정보 암호화</p>
                  <p className="text-lg font-medium text-green-600 dark:text-green-400">AES-256</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-500 dark:text-gray-400">API 인증</p>
                  <p className="text-lg font-medium text-gray-600 dark:text-gray-400">비활성화</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">알림 설정</h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    이메일 알림
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    중요 이벤트 발생 시 이메일로 알림
                  </p>
                </div>
                <button
                  onClick={() =>
                    setNotificationSettings((s) => ({ ...s, email_alerts: !s.email_alerts }))
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notificationSettings.email_alerts
                      ? 'bg-blue-600'
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notificationSettings.email_alerts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Slack 알림
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Slack 채널로 알림 전송</p>
                </div>
                <button
                  onClick={() =>
                    setNotificationSettings((s) => ({ ...s, slack_alerts: !s.slack_alerts }))
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notificationSettings.slack_alerts
                      ? 'bg-blue-600'
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notificationSettings.slack_alerts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  알림 임계값 (신규 IP 수)
                </label>
                <input
                  type="number"
                  value={notificationSettings.alert_threshold}
                  onChange={(e) =>
                    setNotificationSettings((s) => ({
                      ...s,
                      alert_threshold: parseInt(e.target.value) || 100,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  min="10"
                  max="10000"
                />
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? '저장 중...' : '설정 저장'}
          </button>
        </div>
      </div>
    </main>
  );
}
