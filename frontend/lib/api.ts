import axios from 'axios';

// API 클라이언트 설정 - Next.js Rewrites 사용
const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-store',
    Pragma: 'no-cache',
    Expires: '0',
  },
});

// 수집 API 전용 인스턴스
export const collectionApi = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 통계 API
export const getStats = async () => {
  const { data } = await api.get('/web-stats');
  return data;
};

// 시스템 상태 API (Dashboard)
export const getSystemStatus = async () => {
  const { data } = await api.get('/connection/status');
  return data;
};

// 화이트리스트 조회 API (현재 미지원 - blacklist/list 사용)
export const getWhitelist = async (params?: string) => {
  // Backend에 whitelist 전용 API 없음, blacklist/list로 대체
  const url = params ? `/blacklist/list?${params}` : '/blacklist/list';
  const { data } = await api.get(url);
  return data;
};

// 수집 상태 API
export const getCollectionStatus = async () => {
  const { data } = await api.get('/proxy/collection/status');
  return data;
};

// IP 검색 API
export const searchIP = async (ip: string) => {
  const { data } = await api.get(`/search/${ip}`);
  return data;
};

// 수집 내역 API
export const getCollectionHistory = async (params?: string) => {
  const url = params ? `/proxy/collection/history?${params}` : '/proxy/collection/history';
  const { data } = await api.get(url);
  return data;
};

// 수집 통계 API
export const getCollectionStatistics = async () => {
  const { data } = await api.get('/proxy/collection/statistics');
  return data;
};

// 블랙리스트 목록 조회 API
export const getBlacklist = async (params?: string) => {
  const url = params ? `/blacklist/list?${params}` : '/blacklist/list';
  const { data } = await api.get(url);
  return data;
};

// 블랙리스트 통계 API
export const getBlacklistStats = async () => {
  const { data } = await api.get('/collection/stats');
  return data;
};

// 인증정보 조회 API
export const getCredential = async (source: string) => {
  const { data } = await api.get(`/proxy/collection/credentials/${source}`);
  return data;
};

// 인증정보 수정 API
export const updateCredential = async (source: string, credentialData: Record<string, unknown>) => {
  const { data } = await api.put(`/proxy/collection/credentials/${source}`, credentialData);
  return data;
};

// 인증정보 연결 테스트 API
export const testCredential = async (source: string) => {
  const { data } = await api.post(`/proxy/collection/credentials/${source}/test`);
  return data;
};

// 데이터베이스 테이블 목록 API
export const getDatabaseTables = async () => {
  return { success: false, tables: {} as Record<string, unknown>, message: 'Not supported' };
};

// 데이터베이스 스키마 조회 API
export const getDatabaseSchema = async () => {
  return { success: false, schema: {} as Record<string, unknown>, message: 'Not supported' };
};

// Fortinet 로그 조회 API
export const getFortinetPullLogs = async (params?: string) => {
  return { success: false, data: [] as unknown[], stats: null, error: 'Not supported' };
};

// Fortinet 차단 목록 조회 API
export const getFortinetBlocklist = async () => {
  return { data: '', headers: { 'content-type': 'text/plain' } };
};

// 통합 IP 목록 조회 API
export const getUnifiedIPs = async (params?: string) => {
  const url = params ? `/blacklist/list?${params}` : '/blacklist/list';
  const { data } = await api.get(url);
  return data;
};

// IP 추가 API (미지원 - 읽기 전용)
export const addIP = async (type: 'whitelist' | 'blacklist', payload: Record<string, unknown>) => {
  console.warn('IP 추가 API 미지원');
  return { success: false, message: 'Not supported' };
};

// IP 수정 API (미지원 - 읽기 전용)
export const updateIP = async (
  type: 'whitelist' | 'blacklist',
  id: number,
  payload: Record<string, unknown>
) => {
  console.warn('IP 수정 API 미지원');
  return { success: false, message: 'Not supported' };
};

// IP 삭제 API (미지원 - 읽기 전용)
export const deleteIP = async (type: 'whitelist' | 'blacklist', id: number) => {
  console.warn('IP 삭제 API 미지원');
  return { success: false, message: 'Not supported' };
};

// Raw 데이터 내보내기 API
export const exportBlacklistRaw = async (params?: string) => {
  const url = params ? `/blacklist/export-raw?${params}` : '/blacklist/export-raw';
  const response = await api.get(url, {
    responseType: 'blob', // 파일 다운로드를 위해 blob으로 설정
  });
  return response.data; // Blob 반환
};

// 수집 트리거 API
export const triggerCollection = async (startDate: string, endDate: string) => {
  const { data } = await collectionApi.post('/proxy/collection/trigger/regtech', {
    start_date: startDate,
    end_date: endDate,
  });
  return data;
};

// 서비스별 수집 트리거 API
export const triggerCollectionService = async (
  serviceName: string,
  options?: { force?: boolean }
) => {
  const { data } = await collectionApi.post(`/proxy/collection/trigger/${serviceName}`, options || {});
  return data;
};

// 시스템 상태 API
export const getHealth = async () => {
  const { data } = await axios.get('/health');
  return data;
};

// 인증 상태 API
export const getAuthStatus = async () => {
  const { data } = await api.get('/proxy/collection/credentials/regtech');
  return data;
};

// 일별 탐지 통계 API
export const getDailyDetectionStats = async (days: number = 30) => {
  const { data } = await api.get(`/analytics/detection-timeline?days=${days}`);
  return data;
};

export default api;
