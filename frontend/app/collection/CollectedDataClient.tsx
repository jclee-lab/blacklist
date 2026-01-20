'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  Globe,
  Shield,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Search,
  Filter,
} from 'lucide-react';

interface CollectedIP {
  id: number;
  ip_address: string;
  reason: string;
  source: string;
  country: string;
  detection_date: string;
  is_active: boolean;
  created_at: string;
}

interface Stats {
  total: number;
  by_source: Record<string, number>;
  by_country: Record<string, number>;
  by_reason: Record<string, number>;
}

import { getBlacklist, getStats } from '@/lib/api';

const ITEMS_PER_PAGE = 20;

export default function CollectedDataClient() {
  const [data, setData] = useState<CollectedIP[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [sourceFilter, setSourceFilter] = useState('');
  const [searchIP, setSearchIP] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: ITEMS_PER_PAGE.toString(),
      });
      if (sourceFilter) params.append('source', sourceFilter);
      if (searchIP) params.append('ip', searchIP);

      const json = await getBlacklist(params.toString());
      if (json) {
        const items = json.data?.items || [];
        const pagination = json.data?.pagination || {};
        setData(items);
        setTotalItems(pagination.total || 0);
      }

      const statsJson = await getStats();
      if (statsJson && statsJson.success && statsJson.data) {
        setStats({
          total: statsJson.data.total_ips || 0,
          by_source: statsJson.data.by_source || {},
          by_country: statsJson.data.by_country || {},
          by_reason: statsJson.data.by_reason || {},
        });
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, sourceFilter, searchIP]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

  const getCountryFlag = (code: string) => {
    if (!code || code === 'UNKNOWN' || code.length !== 2) return '🌐';
    const codePoints = code
      .toUpperCase()
      .split('')
      .map((char) => 127397 + char.charCodeAt(0));
    return String.fromCodePoint(...codePoints);
  };

  const getReasonColor = (reason: string) => {
    if (reason?.includes('SQL')) return 'bg-red-100 text-red-800';
    if (reason?.includes('WordPress')) return 'bg-orange-100 text-orange-800';
    if (reason?.includes('공격')) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Shield className="h-8 w-8 opacity-80" />
            <span className="text-3xl font-bold">{stats?.total || 0}</span>
          </div>
          <p className="text-blue-100 text-sm mt-2">총 블랙리스트 IP</p>
        </div>

        <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <AlertTriangle className="h-8 w-8 opacity-80" />
            <span className="text-3xl font-bold">{stats?.by_source?.REGTECH || 0}</span>
          </div>
          <p className="text-pink-100 text-sm mt-2">REGTECH 수집</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Globe className="h-8 w-8 opacity-80" />
            <span className="text-3xl font-bold">
              {stats?.by_country ? Object.keys(stats.by_country).length : 0}
            </span>
          </div>
          <p className="text-green-100 text-sm mt-2">탐지 국가 수</p>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Filter className="h-8 w-8 opacity-80" />
            <span className="text-3xl font-bold">
              {stats?.by_reason ? Object.keys(stats.by_reason).length : 0}
            </span>
          </div>
          <p className="text-purple-100 text-sm mt-2">위협 유형</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-900">수집된 IP 목록</h3>
          <div className="flex gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="IP 검색..."
                value={searchIP}
                onChange={(e) => setSearchIP(e.target.value)}
                className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 소스</option>
              <option value="REGTECH">REGTECH</option>
              <option value="MANUAL">수동 등록</option>
            </select>
            <button
              onClick={fetchData}
              className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">IP 주소</th>
                <th className="px-4 py-3 text-left font-medium">소스</th>
                <th className="px-4 py-3 text-left font-medium">국가</th>
                <th className="px-4 py-3 text-left font-medium">위협 유형</th>
                <th className="px-4 py-3 text-left font-medium">탐지일</th>
                <th className="px-4 py-3 text-center font-medium">상태</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((ip) => (
                <tr key={ip.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-mono text-blue-600">{ip.ip_address}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        ip.source === 'REGTECH'
                          ? 'bg-pink-100 text-pink-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {ip.source}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1">
                      <span className="text-lg">{getCountryFlag(ip.country)}</span>
                      <span className="text-gray-600">{ip.country || '-'}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getReasonColor(ip.reason)}`}>
                      {ip.reason || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {ip.detection_date
                      ? new Date(ip.detection_date).toLocaleDateString('ko-KR')
                      : '-'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {ip.is_active ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        활성
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
                        비활성
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <Shield className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>수집된 데이터가 없습니다</p>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-6 pt-4 border-t">
            <p className="text-sm text-gray-600">
              총 {totalItems.toLocaleString()}개 중 {(currentPage - 1) * ITEMS_PER_PAGE + 1}-
              {Math.min(currentPage * ITEMS_PER_PAGE, totalItems)}개 표시
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-600">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg border hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {stats?.by_country && Object.keys(stats.by_country).length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">국가별 분포</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.by_country)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 20)
              .map(([country, count]) => (
                <div
                  key={country}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg"
                >
                  <span className="text-lg">{getCountryFlag(country)}</span>
                  <span className="text-sm font-medium text-gray-700">{country}</span>
                  <span className="text-xs text-gray-500">({count})</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
