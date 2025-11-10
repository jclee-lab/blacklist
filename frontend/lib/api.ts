import axios from 'axios';

// API 클라이언트 설정 - Next.js API 프록시 사용
const api = axios.create({
  baseURL: '/api/proxy',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 통계 API
export const getStats = async () => {
  const { data } = await api.get('/stats');
  return data; // Backend returns flat JSON, not nested under .statistics
};

// IP 검색 API
export const searchIP = async (ip: string) => {
  const { data } = await api.get(`/search/${ip}`);
  return data;
};

// 수집 내역 API
export const getCollectionHistory = async () => {
  const { data } = await api.get('/collection/history');
  return data;
};

// 수집 트리거 API
export const triggerCollection = async (startDate: string, endDate: string) => {
  const { data } = await api.post('/collection/regtech/trigger', {
    start_date: startDate,
    end_date: endDate,
  });
  return data;
};

// 시스템 상태 API (health는 /api prefix 없음)
export const getHealth = async () => {
  const { data } = await axios.get('/api/proxy/health');
  return data;
};

// 인증 상태 API
export const getAuthStatus = async () => {
  const { data } = await api.get('/credentials/regtech');
  return data;
};

export default api;
