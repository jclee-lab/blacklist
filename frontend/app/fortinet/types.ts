export interface FortinetIP {
  id: number;
  ip_address: string;
  country?: string;
  reason?: string;
  confidence_level?: number;
  detection_date?: string;
  removal_date?: string;
  is_active: boolean;
}

export interface PullLog {
  id: number;
  device_ip: string;
  user_agent?: string;
  endpoint?: string;
  ip_count?: number;
  response_time_ms?: number;
  status_code?: number;
  created_at?: string;
}

export interface PullLogStats {
  total_pulls: number;
  successful_pulls: number;
  failed_pulls: number;
  unique_devices: number;
}

export interface FortinetStats {
  total_active: number;
  last_updated: string;
}

export type FortinetViewTab = 'active-ips' | 'pull-logs';
