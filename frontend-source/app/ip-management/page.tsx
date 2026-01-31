"use client";

import { useQuery } from "@tanstack/react-query";
import { fetcher } from "@/lib/api";
import { Shield, Search, Filter } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

interface IPData {
  id: number;
  ip_address: string;
  reason: string;
  source: string;
  category: string;
  confidence_level: number;
  is_active: boolean;
  country: string;
  detection_date: string;
}

interface APIResponse {
  success: boolean;
  data: IPData[];
  total: number;
  page: number;
  per_page: number;
}

export default function IPManagement() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useQuery<APIResponse>({
    queryKey: ["blacklist", page],
    queryFn: () => fetcher(`/api/blacklist/list?page=${page}&per_page=20`),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-blue-500 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">IP 관리</h1>
        </div>
        <div className="flex space-x-2">
          <button className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50">
            <Filter className="w-4 h-4 mr-2" />
            필터
          </button>
          <div className="relative">
            <input
              type="text"
              placeholder="IP 검색..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP 주소</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">국가</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">사유</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">출처</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신뢰도</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">탐지일</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">로딩 중...</td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-red-500">에러 발생: {(error as Error).message}</td>
                </tr>
              ) : (
                data?.data.map((ip) => (
                  <tr key={ip.id} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link href={`/ip-detail/${ip.ip_address}`} className="text-blue-600 hover:underline font-medium">
                        {ip.ip_address}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ip.country}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-xs truncate">{ip.reason}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {ip.source}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2.5 mr-2">
                          <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${ip.confidence_level}%` }}></div>
                        </div>
                        <span>{ip.confidence_level}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${ip.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {ip.is_active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ip.detection_date}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6 flex justify-between items-center">
            <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
            >
                이전
            </button>
            <span className="text-sm text-gray-700">페이지 {page}</span>
            <button 
                onClick={() => setPage(p => p + 1)}
                disabled={!data || data.data.length < 20}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
            >
                다음
            </button>
        </div>
      </div>
    </div>
  );
}
