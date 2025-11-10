import { useQuery } from '@tanstack/react-query';
import { getStats, getHealth, getCollectionHistory, getAuthStatus } from '@/lib/api';

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 30000, // 30초마다 자동 새로고침
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 10000, // 10초마다
  });
}

export function useCollectionHistory() {
  return useQuery({
    queryKey: ['collectionHistory'],
    queryFn: getCollectionHistory,
    refetchInterval: 15000,
  });
}

export function useAuthStatus() {
  return useQuery({
    queryKey: ['authStatus'],
    queryFn: getAuthStatus,
  });
}
