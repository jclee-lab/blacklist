import { Activity, Database, Shield, Server } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <div className="p-3 bg-blue-500 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
          <Activity className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">대시보드</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: "총 차단 IP", value: "14,429", icon: Shield, color: "text-blue-600" },
          { label: "활성 차단", value: "8,181", icon: Activity, color: "text-green-600" },
          { label: "오늘 수집", value: "1,240", icon: Database, color: "text-purple-600" },
          { label: "시스템 상태", value: "정상", icon: Server, color: "text-emerald-600" },
        ].map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
              <stat.icon className={`w-8 h-8 ${stat.color}`} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 h-96">
          <h2 className="text-lg font-bold text-gray-900 mb-4">최근 차단 추이</h2>
          <div className="flex items-center justify-center h-full text-gray-400">
            차트 영역 (Recharts)
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 h-96">
          <h2 className="text-lg font-bold text-gray-900 mb-4">국가별 분포</h2>
          <div className="flex items-center justify-center h-full text-gray-400">
            지도 영역
          </div>
        </div>
      </div>
    </div>
  );
}
