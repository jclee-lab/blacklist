'use client';

import { useState, useEffect } from 'react';
import { Database, Table, Users, Shield, RefreshCw } from 'lucide-react';

interface TableInfo {
  name: string;
  description: string;
  rows: number;
  icon: any;
  color: string;
  bgColor: string;
}

export default function DatabaseOverviewClient() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
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

  const tables: TableInfo[] = [
    {
      name: 'blacklist_ips',
      description: '블랙리스트 IP 주소',
      rows: stats?.total_ips || 0,
      icon: Shield,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      name: 'whitelist_ips',
      description: '화이트리스트 IP 주소',
      rows: stats?.whitelisted_ips || 0,
      icon: Shield,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'collection_history',
      description: '수집 이력',
      rows: 0,
      icon: Table,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'collection_credentials',
      description: '수집 인증 정보',
      rows: 1,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ];

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
      <div className="flex items-center justify-end">
        <button
          onClick={fetchStats}
          className="flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          새로고침
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tables.map((table, index) => (
          <div key={index} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className={`${table.bgColor} p-3 rounded-lg`}>
                  <table.icon className={`h-6 w-6 ${table.color}`} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{table.name}</h3>
                  <p className="text-sm text-gray-600">{table.description}</p>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">레코드 수</span>
                <span className="text-2xl font-bold text-gray-900">
                  {table.rows.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Database Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <Database className="h-6 w-6 mr-2 text-blue-600" />
          데이터베이스 정보
        </h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">데이터베이스</dt>
            <dd className="mt-1 text-sm text-gray-900">PostgreSQL 15</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">호스트</dt>
            <dd className="mt-1 text-sm text-gray-900">blacklist-postgres:5432</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">데이터베이스명</dt>
            <dd className="mt-1 text-sm text-gray-900">blacklist</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">총 테이블 수</dt>
            <dd className="mt-1 text-sm text-gray-900">{tables.length}개</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
