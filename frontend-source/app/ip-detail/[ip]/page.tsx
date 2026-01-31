"use client";

import { useQuery } from "@tanstack/react-query";
import { fetcher } from "@/lib/api";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Shield, Globe, Calendar, AlertTriangle, Activity, FileJson, Info } from "lucide-react";
import Link from "next/link";

interface IPDetailData {
  id: number;
  ip_address: string;
  reason: string;
  source: string;
  category: string;
  confidence_level: number;
  detection_count: number;
  is_active: boolean;
  country: string;
  detection_date: string;
  removal_date: string;
  last_seen: string;
  raw_data: any;
}

interface DetailResponse {
  success: boolean;
  data: IPDetailData;
}

export default function IPDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ip = params.ip as string;

  const { data, isLoading, error } = useQuery<DetailResponse>({
    queryKey: ["ip-detail", ip],
    queryFn: () => fetcher(`/api/blacklist/${ip}`),
    enabled: !!ip,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-lg text-gray-500 animate-pulse">IP 정보 로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <div className="text-lg text-red-500 font-bold">에러 발생</div>
        <p className="text-gray-600">{(error as Error).message}</p>
        <button 
          onClick={() => router.back()}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 transition-colors"
        >
          돌아가기
        </button>
      </div>
    );
  }

  const detail = data?.data;

  if (!detail) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <div className="text-lg text-gray-500">데이터를 찾을 수 없습니다.</div>
        <Link href="/ip-management" className="mt-4 text-blue-500 hover:underline">
          목록으로 돌아가기
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors"
            aria-label="Go back"
          >
            <ArrowLeft className="w-6 h-6 text-gray-600" />
          </button>
          <div className="p-3 bg-blue-500 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{detail.ip_address}</h1>
            <p className="text-gray-500 text-sm mt-1">상세 정보 및 분석 리포트</p>
          </div>
        </div>
        <div className="flex space-x-3">
           <span className={`px-4 py-2 rounded-full text-sm font-bold shadow-sm ${detail.is_active ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-gray-100 text-gray-800 border border-gray-200'}`}>
              {detail.is_active ? '활성 상태 (Active)' : '비활성 (Inactive)'}
           </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info Card */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center">
              <Info className="w-5 h-5 text-blue-500 mr-2" />
              <h2 className="font-bold text-gray-800">기본 정보</h2>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">차단 사유</label>
                <p className="text-gray-900 font-medium text-lg">{detail.reason}</p>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">출처 (Source)</label>
                <div className="flex items-center">
                   <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm font-medium border border-blue-100">
                     {detail.source}
                   </span>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">카테고리</label>
                <p className="text-gray-900">{detail.category}</p>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">국가</label>
                <div className="flex items-center space-x-2">
                  <Globe className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-900">{detail.country}</span>
                  {/* Simple flag emoji mapping could be added here if needed, or rely on country code */}
                </div>
              </div>
            </div>
          </div>

          {/* Raw Data Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center">
              <FileJson className="w-5 h-5 text-purple-500 mr-2" />
              <h2 className="font-bold text-gray-800">Raw Data</h2>
            </div>
            <div className="p-0">
              <pre className="bg-gray-900 text-gray-100 p-6 overflow-x-auto text-sm font-mono leading-relaxed">
                {JSON.stringify(detail.raw_data, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Sidebar Stats */}
        <div className="space-y-6">
          {/* Confidence Score */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-800 flex items-center">
                <Activity className="w-5 h-5 text-orange-500 mr-2" />
                신뢰도 점수
              </h3>
              <span className="text-2xl font-bold text-blue-600">{detail.confidence_level}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-3 mb-2">
              <div 
                className={`h-3 rounded-full transition-all duration-1000 ${
                  detail.confidence_level > 80 ? 'bg-red-500' : 
                  detail.confidence_level > 50 ? 'bg-orange-500' : 'bg-green-500'
                }`}
                style={{ width: `${detail.confidence_level}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 text-right">높을수록 위협 가능성이 높습니다.</p>
          </div>

          {/* Detection Stats */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
            <h3 className="font-bold text-gray-800 flex items-center border-b border-gray-100 pb-2">
              <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
              탐지 통계
            </h3>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">누적 탐지 횟수</span>
              <span className="font-bold text-gray-900 bg-gray-100 px-2 py-1 rounded">{detail.detection_count}회</span>
            </div>
          </div>

          {/* Dates */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
             <h3 className="font-bold text-gray-800 flex items-center border-b border-gray-100 pb-2">
              <Calendar className="w-5 h-5 text-green-500 mr-2" />
              타임라인
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-500">최초 탐지일</p>
                <p className="font-medium text-gray-900">{detail.detection_date}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">최근 활동 (Last Seen)</p>
                <p className="font-medium text-gray-900">{detail.last_seen || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">해제 예정일</p>
                <p className="font-medium text-gray-900">{detail.removal_date || '-'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
