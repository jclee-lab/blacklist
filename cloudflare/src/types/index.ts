/**
 * Cloudflare Workers Types
 * Bindings and shared interfaces for Blacklist API
 */

import type { D1Database, KVNamespace, Queue, Fetcher } from '@cloudflare/workers-types';

// ============================================================
// Environment Bindings
// ============================================================

export interface Env {
  // D1 Database
  DB: D1Database;

  // KV Namespaces
  CACHE: KVNamespace;
  SESSIONS: KVNamespace;

  // Queues
  COLLECTION_QUEUE: Queue<CollectionJob>;

  // Browser Rendering (Puppeteer)
  BROWSER: Fetcher;

  // Environment Variables
  ENVIRONMENT: 'production' | 'staging' | 'preview';
  LOG_LEVEL: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  CORS_ORIGINS: string;
  API_VERSION: string;

  // Secrets
  CREDENTIAL_MASTER_KEY: string;
  REGTECH_USERNAME: string;
  REGTECH_PASSWORD: string;
  INGEST_API_KEY: string;
}

export interface BlacklistItem {
  ip_address: string;
  source: string;
  category: string;
  country: string;
  reason: string;
  confidence_level: number;
  detection_count: number;
  is_active: number;
  detection_date: string | null;
  removal_date: string | null;
  raw_data: string;
}

// ============================================================
// Database Models
// ============================================================

export interface BlacklistIP {
  id: number;
  ip_address: string;
  reason: string | null;
  source: string;
  category: string;
  confidence_level: number;
  detection_count: number;
  is_active: number; // 0 or 1 (SQLite boolean)
  country: string | null;
  detection_date: string | null;
  removal_date: string | null;
  last_seen: string;
  created_at: string;
  updated_at: string;
  raw_data: string; // JSON string
  data_source: string;
}

export interface CollectionCredential {
  id: number;
  service_name: string;
  username: string | null;
  password: string | null;
  config: string; // JSON string
  encrypted: number;
  is_active: number;
  enabled: number;
  collection_interval: number;
  source: string;
  last_collection: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionHistory {
  id: number;
  service_name: string;
  collection_date: string;
  items_collected: number;
  success: number;
  error_message: string | null;
  execution_time_ms: number;
  details: string; // JSON string
}

export interface CollectionStatus {
  id: number;
  service_name: string;
  enabled: number;
  last_run: string | null;
  next_run: string | null;
  status: 'idle' | 'running' | 'error' | 'disabled';
  error_count: number;
  success_count: number;
  config: string; // JSON string
  updated_at: string;
}

export interface SystemSetting {
  id: number;
  setting_key: string;
  setting_value: string | null;
  description: string | null;
  display_order: number;
  setting_type: string;
  is_encrypted: number;
  is_active: number;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface FortigatePullLog {
  id: number;
  ip_address: string | null;
  device_ip: string | null;
  user_agent: string | null;
  request_path: string | null;
  request_count: number;
  ip_count: number;
  response_time_ms: number;
  last_request_at: string;
  created_at: string;
}

export interface WhitelistIP {
  id: number;
  ip_address: string;
  reason: string | null;
  source: string;
  country: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// API Types
// ============================================================

export interface PaginationParams {
  page: number;
  limit: number;
  offset: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface APIError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
}

export interface StatsResponse {
  total_ips: number;
  active_ips: number;
  sources: Record<string, number>;
  categories: Record<string, number>;
  countries: Record<string, number>;
  last_update: string;
  collection_status: {
    service_name: string;
    status: string;
    last_run: string | null;
  }[];
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  environment: string;
  timestamp: string;
  checks: {
    database: boolean;
    cache: boolean;
  };
}

// ============================================================
// Queue Types
// ============================================================

export interface CollectionJob {
  service_name: string;
  triggered_by: 'cron' | 'manual';
  timestamp: string;
  config?: Record<string, unknown>;
}

export interface CollectionResult {
  service_name: string;
  items_collected: number;
  success: boolean;
  error_message?: string;
  execution_time_ms: number;
}

// ============================================================
// REGTECH Types
// ============================================================

export interface REGTECHResponse {
  resultCode: string;
  resultMessage: string;
  data?: {
    ipList: REGTECHIPItem[];
    totalCount: number;
  };
}

export interface REGTECHIPItem {
  ipAddress: string;
  detectionDate: string;
  detectionCount: number;
  reason: string;
  countryCode: string;
}

// ============================================================
// Cache Keys
// ============================================================

export const CacheKeys = {
  STATS: 'stats:global',
  BLACKLIST_PAGE: (page: number, limit: number) => `blacklist:page:${page}:${limit}`,
  SOURCES: 'sources:list',
  CATEGORIES: 'categories:list',
  COLLECTION_STATUS: 'collection:status',
} as const;

export const CacheTTL = {
  STATS: 300, // 5 minutes
  BLACKLIST: 60, // 1 minute
  SOURCES: 3600, // 1 hour
  COLLECTION_STATUS: 30, // 30 seconds
} as const;
