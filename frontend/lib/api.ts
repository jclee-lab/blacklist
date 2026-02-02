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
  const { data } = await api.get('/dashboard/stats');
  return data;
};

// 시스템 상태 API (Dashboard)
export const getSystemStatus = async () => {
  const { data } = await api.get('/dashboard/status');
  return data;
};

// 화이트리스트 조회 API
export const getWhitelist = async (params?: string) => {
  const url = params ? `/ip-management/whitelist?${params}` : '/ip-management/whitelist';
  const { data } = await api.get(url);
  return data;
};

// 수집 상태 API
export const getCollectionStatus = async () => {
  const { data } = await api.get('/collection/status');
  return data;
};

// IP 검색 API
export const searchIP = async (ip: string) => {
  const { data } = await api.get(`/search/${ip}`);
  return data;
};

// 수집 내역 API
export const getCollectionHistory = async (params?: string) => {
  const url = params ? `/collection/history?${params}` : '/collection/history';
  const { data } = await api.get(url);
  return data;
};

// 수집 통계 API
export const getCollectionStatistics = async () => {
  const { data } = await api.get('/collection/statistics');
  return data;
};

// 블랙리스트 목록 조회 API
export const getBlacklist = async (params?: string) => {
  const url = params ? `/ip-management/blacklist?${params}` : '/ip-management/blacklist';
  const { data } = await api.get(url);
  return data;
};

// 블랙리스트 통계 API
export const getBlacklistStats = async () => {
  const { data } = await api.get('/blacklist/stats');
  return data;
};

// 인증정보 조회 API
export const getCredential = async (source: string) => {
  const { data } = await api.get(`/collection/credentials/${source}`);
  return data;
};

// 인증정보 수정 API
export const updateCredential = async (source: string, credentialData: Record<string, unknown>) => {
  const { data } = await api.put(`/collection/credentials/${source}`, credentialData);
  return data;
};

// 인증정보 연결 테스트 API
export const testCredential = async (source: string) => {
  const { data } = await api.post(`/collection/credentials/${source}/test`);
  return data;
};

// 데이터베이스 테이블 목록 API
export const getDatabaseTables = async () => {
  const { data } = await api.get('/database/tables');
  return data;
};

// 데이터베이스 스키마 조회 API
export const getDatabaseSchema = async () => {
  const { data } = await api.get('/database/schema');
  return data;
};

// Fortinet 로그 조회 API
export const getFortinetPullLogs = async (params?: string) => {
  const url = params ? `/fortinet/pull-logs?${params}` : '/fortinet/pull-logs';
  const { data } = await api.get(url);
  return data;
};

// Fortinet 차단 목록 조회 API
export const getFortinetBlocklist = async () => {
  // 텍스트/JSON 등 content-type에 따라 처리 필요하지만 axios는 기본적으로 json 파싱 시도
  // 텍스트일 경우 data에 텍스트가 들어감
  const response = await api.get('/fortinet/blocklist', {
    responseType: 'text', // 텍스트로 받을 수도 있음, 헤더 확인 필요하지만 일단 text로
    transformResponse: [
      (data) => {
        // Try to parse JSON, if fails return text
        try {
          return JSON.parse(data);
        } catch {
          return data;
        }
      },
    ],
  });
  // Return full response object to access headers if needed, or normalize return
  // FortinetClient logic uses headers.get('content-type')
  // We should probably return a normalized structure or the AxiosResponse
  return response;
};

// 통합 IP 목록 조회 API
export const getUnifiedIPs = async (params?: string) => {
  const url = params ? `/ip-management/unified?${params}` : '/ip-management/unified';
  const { data } = await api.get(url);
  return data;
};

// IP 추가 API
export const addIP = async (type: 'whitelist' | 'blacklist', payload: Record<string, unknown>) => {
  const { data } = await api.post(`/ip-management/${type}`, payload);
  return data;
};

// IP 수정 API
export const updateIP = async (
  type: 'whitelist' | 'blacklist',
  id: number,
  payload: Record<string, unknown>
) => {
  const { data } = await api.put(`/ip-management/${type}/${id}`, payload);
  return data;
};

// IP 삭제 API
export const deleteIP = async (type: 'whitelist' | 'blacklist', id: number) => {
  const { data } = await api.delete(`/ip-management/${type}/${id}`);
  return data;
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
  const { data } = await collectionApi.post('/collection/regtech/trigger', {
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
  const { data } = await collectionApi.post(`/collection/trigger/${serviceName}`, options || {});
  return data;
};

// 시스템 상태 API
export const getHealth = async () => {
  const { data } = await axios.get('/health');
  return data;
};

// 인증 상태 API
export const getAuthStatus = async () => {
  const { data } = await api.get('/collection/credentials/regtech');
  return data;
};

// 일별 탐지 통계 API
export const getDailyDetectionStats = async (days: number = 30) => {
  const { data } = await api.get(`/analytics/detection-timeline?days=${days}`);
  return data;
};

export default api;
