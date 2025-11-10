'use client';

import { Database, Shield, PlusCircle, Clock, Activity, TrendingUp, Globe, History, Table2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    fetchSystemStatus();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchStats();
      fetchSystemStatus();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const statCards = [
    {
      title: '전체 IP 주소',
      value: stats?.total_ips || 0,
      icon: Database,
      gradient: 'from-blue-500 to-blue-600',
      bgGradient: 'from-blue-50 to-blue-100',
      iconBg: 'bg-blue-500'
    },
    {
      title: '차단된 IP',
      value: stats?.active_ips || 0,
      icon: Shield,
      gradient: 'from-red-500 to-red-600',
      bgGradient: 'from-red-50 to-red-100',
      iconBg: 'bg-red-500'
    },
    {
      title: '24시간 신규',
      value: stats?.recent_additions || 0,
      icon: PlusCircle,
      gradient: 'from-green-500 to-green-600',
      bgGradient: 'from-green-50 to-green-100',
      iconBg: 'bg-green-500'
    },
    {
      title: '화이트리스트',
      value: stats?.whitelisted_ips || 0,
      icon: Globe,
      gradient: 'from-purple-500 to-purple-600',
      bgGradient: 'from-purple-50 to-purple-100',
      iconBg: 'bg-purple-500'
    },
  ];

  const quickActions = [
    {
      href: '/monitoring',
      title: '실시간 모니터링',
      description: '시스템 상태 확인',
      icon: Activity,
      gradient: 'from-blue-500 to-cyan-500',
      iconBg: 'bg-gradient-to-br from-blue-500 to-cyan-500'
    },
    {
      href: '/collection',
      title: '데이터 수집',
      description: '수집 관리 및 이력',
      icon: History,
      gradient: 'from-green-500 to-emerald-500',
      iconBg: 'bg-gradient-to-br from-green-500 to-emerald-500'
    },
    {
      href: '/database',
      title: '데이터베이스',
      description: '테이블 현황 및 브라우저',
      icon: Table2,
      gradient: 'from-purple-500 to-pink-500',
      iconBg: 'bg-gradient-to-br from-purple-500 to-pink-500'
    },
  ];

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header with gradient */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-clip-text text-transparent mb-3">
          대시보드
        </h1>
        <p className="text-gray-600 text-lg">실시간 IP 블랙리스트 모니터링 및 관리</p>
      </div>

      {/* Stats Cards with Modern Design */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-xl p-6 shadow-lg animate-pulse">
              <div className="h-12 bg-gray-200 rounded mb-4"></div>
              <div className="h-8 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((card, index) => (
            <div
              key={index}
              className="group relative bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 overflow-hidden"
            >
              {/* Gradient background overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${card.bgGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>

              <div className="relative p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`${card.iconBg} p-3 rounded-lg text-white shadow-lg transform group-hover:scale-110 transition-transform duration-300`}>
                    <card.icon className="h-6 w-6" />
                  </div>
                </div>
                <h3 className="text-3xl font-bold text-gray-900 mb-1">
                  {card.value.toLocaleString()}
                </h3>
                <p className="text-gray-600 text-sm font-medium">{card.title}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Last Update Info */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-4 mb-8 border border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Clock className="h-5 w-5 text-gray-600" />
            <span className="text-sm text-gray-600 font-medium">마지막 업데이트:</span>
            <span className="text-sm font-semibold text-gray-900">
              {stats?.last_update ? new Date(stats.last_update).toLocaleString('ko-KR') : 'N/A'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-600 font-medium">실시간 동기화</span>
          </div>
        </div>
      </div>

      {/* Quick Actions with Modern Cards */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">빠른 작업</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => (
            <Link
              key={index}
              href={action.href}
              className="group relative bg-white rounded-xl p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 overflow-hidden"
            >
              {/* Gradient overlay on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>

              <div className="relative flex items-center space-x-4">
                <div className={`${action.iconBg} p-4 rounded-xl text-white shadow-lg transform group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
                  <action.icon className="h-8 w-8" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 text-lg mb-1 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-purple-600 transition-all duration-300">
                    {action.title}
                  </h3>
                  <p className="text-sm text-gray-600 group-hover:text-gray-700 transition-colors duration-300">
                    {action.description}
                  </p>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* System Status Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">시스템 상태</h2>
        {systemStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className={`flex items-center space-x-4 p-4 rounded-lg border ${
              systemStatus.service?.status === 'healthy'
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className={`p-3 rounded-lg ${
                systemStatus.service?.status === 'healthy'
                  ? 'bg-green-500'
                  : 'bg-red-500'
              }`}>
                <Activity className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">API 서버</p>
                <p className={`text-lg font-bold ${
                  systemStatus.service?.status === 'healthy'
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}>
                  {systemStatus.service?.status === 'healthy' ? '정상' : '오류'}
                </p>
              </div>
            </div>
            <div className={`flex items-center space-x-4 p-4 rounded-lg border ${
              systemStatus.components?.database?.status === 'healthy'
                ? 'bg-blue-50 border-blue-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className={`p-3 rounded-lg ${
                systemStatus.components?.database?.status === 'healthy'
                  ? 'bg-blue-500'
                  : 'bg-red-500'
              }`}>
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">데이터베이스</p>
                <p className={`text-lg font-bold ${
                  systemStatus.components?.database?.status === 'healthy'
                    ? 'text-blue-600'
                    : 'text-red-600'
                }`}>
                  {systemStatus.components?.database?.status === 'healthy' ? '정상' : '오류'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="bg-purple-500 p-3 rounded-lg">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">수집 활성화</p>
                <p className="text-lg font-bold text-purple-600">
                  {systemStatus.collection?.collection_enabled ? '활성' : '비활성'}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-pulse">
                <div className="bg-gray-300 p-3 rounded-lg h-12 w-12"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-300 rounded mb-2"></div>
                  <div className="h-6 bg-gray-300 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
