/**
 * Stats Routes
 * /api/stats endpoint
 */

import { Hono } from 'hono';
import type { Env, StatsResponse } from '../types/index.js';
import { DatabaseService } from '../services/database.js';
import { CacheService } from '../services/cache.js';
import { CacheKeys, CacheTTL } from '../types/index.js';

const stats = new Hono<{ Bindings: Env }>();

/**
 * GET /api/stats
 * Get comprehensive statistics
 */
stats.get('/', async (c) => {
  const cache = new CacheService(c.env.CACHE);
  const db = new DatabaseService(c.env.DB);

  // Check cache
  const cached = await cache.get<StatsResponse>(CacheKeys.STATS);
  if (cached) {
    return c.json(cached);
  }

  // Get total counts
  const counts = await db.queryOne<{
    total_ips: number;
    active_ips: number;
  }>(`
    SELECT 
      COUNT(*) as total_ips,
      SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_ips
    FROM blacklist_ips
  `);

  // Get source breakdown
  const sourceResults = await db.query<{ source: string; count: number }>(`
    SELECT source, COUNT(*) as count 
    FROM blacklist_ips 
    WHERE is_active = 1 
    GROUP BY source 
    ORDER BY count DESC
  `);
  const sources: Record<string, number> = {};
  for (const row of sourceResults) {
    sources[row.source] = row.count;
  }

  // Get category breakdown
  const categoryResults = await db.query<{ category: string; count: number }>(`
    SELECT category, COUNT(*) as count 
    FROM blacklist_ips 
    WHERE is_active = 1 
    GROUP BY category 
    ORDER BY count DESC
  `);
  const categories: Record<string, number> = {};
  for (const row of categoryResults) {
    categories[row.category] = row.count;
  }

  // Get top countries
  const countryResults = await db.query<{ country: string; count: number }>(`
    SELECT country, COUNT(*) as count 
    FROM blacklist_ips 
    WHERE is_active = 1 AND country IS NOT NULL 
    GROUP BY country 
    ORDER BY count DESC 
    LIMIT 10
  `);
  const countries: Record<string, number> = {};
  for (const row of countryResults) {
    countries[row.country] = row.count;
  }

  // Get last update time
  const lastUpdate = await db.queryOne<{ last_seen: string }>(`
    SELECT MAX(last_seen) as last_seen FROM blacklist_ips WHERE is_active = 1
  `);

  // Get collection status
  const collectionStatus = await db.query<{
    service_name: string;
    status: string;
    last_run: string | null;
  }>(`
    SELECT service_name, status, last_run 
    FROM collection_status 
    ORDER BY service_name
  `);

  const response: StatsResponse = {
    total_ips: counts?.total_ips ?? 0,
    active_ips: counts?.active_ips ?? 0,
    sources,
    categories,
    countries,
    last_update: lastUpdate?.last_seen ?? new Date().toISOString(),
    collection_status: collectionStatus,
  };

  // Cache for 5 minutes
  await cache.set(CacheKeys.STATS, response, CacheTTL.STATS);

  return c.json(response);
});

/**
 * GET /api/stats/collection
 * Get collection-specific statistics
 */
stats.get('/collection', async (c) => {
  const db = new DatabaseService(c.env.DB);
  const cache = new CacheService(c.env.CACHE);

  const cacheKey = CacheKeys.COLLECTION_STATUS;
  const cached = await cache.get(cacheKey);
  if (cached) {
    return c.json(cached);
  }

  // Get collection history summary
  const history = await db.query<{
    service_name: string;
    total_collections: number;
    successful_collections: number;
    total_items: number;
    avg_time_ms: number;
    last_collection: string;
  }>(`
    SELECT 
      service_name,
      COUNT(*) as total_collections,
      SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_collections,
      SUM(items_collected) as total_items,
      AVG(execution_time_ms) as avg_time_ms,
      MAX(collection_date) as last_collection
    FROM collection_history
    GROUP BY service_name
    ORDER BY last_collection DESC
  `);

  // Get current status
  const status = await db.query<{
    service_name: string;
    enabled: number;
    status: string;
    last_run: string | null;
    next_run: string | null;
    error_count: number;
    success_count: number;
  }>(`
    SELECT * FROM collection_status ORDER BY service_name
  `);

  const response = {
    history,
    status: status.map((s) => ({
      ...s,
      enabled: s.enabled === 1,
    })),
  };

  await cache.set(cacheKey, response, CacheTTL.COLLECTION_STATUS);

  return c.json(response);
});

/**
 * GET /api/stats/timeline
 * Get collection timeline (items per day)
 */
stats.get('/timeline', async (c) => {
  const url = new URL(c.req.url);
  const days = parseInt(url.searchParams.get('days') || '30', 10);
  const db = new DatabaseService(c.env.DB);

  const timeline = await db.query<{
    date: string;
    count: number;
    source: string;
  }>(`
    SELECT 
      date(detection_date) as date,
      COUNT(*) as count,
      source
    FROM blacklist_ips
    WHERE detection_date >= datetime('now', '-${days} days')
    GROUP BY date(detection_date), source
    ORDER BY date DESC
  `);

  return c.json({ timeline, days });
});

export default stats;
