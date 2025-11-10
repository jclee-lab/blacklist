// 통계 데이터 타입
export interface Statistics {
  total_ips: number;
  active_ips: number;
  recent_additions: number;
  last_update: string;
}

// 수집 로그 타입
export interface CollectionLog {
  service_name: string;
  collection_date: string;
  items_collected: number;
  success: boolean;
  error_message?: string;
  timestamp?: string;
  source?: string;
}

// IP 검색 결과 타입
export interface IPSearchResult {
  ip_address: string;
  source?: string;
  category?: string;
  country?: string;
  is_active: boolean;
  created_at: string;
  reason?: string;
}

// 시스템 상태 타입
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  mode?: string;
}

// 인증 상태 타입
export interface AuthStatus {
  configured: boolean;
  authenticated: boolean;
  regtech_id?: string;
}
