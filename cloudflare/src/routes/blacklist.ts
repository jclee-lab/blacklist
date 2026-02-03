/**
 * Blacklist Routes
 * /api/blacklist/* endpoints
 */

import { Hono } from 'hono';
import type { Env, BlacklistIP, PaginatedResponse } from '../types/index.js';
import { DatabaseService, parsePagination } from '../services/database.js';
import { CacheService } from '../services/cache.js';
import { CacheKeys, CacheTTL } from '../types/index.js';

const blacklist = new Hono<{ Bindings: Env }>();

/**
 * GET /api/blacklist/list
 * Get paginated list of blacklisted IPs
 */
blacklist.get('/list', async (c) => {
  const url = new URL(c.req.url);
  const pagination = parsePagination(url);
  const cache = new CacheService(c.env.CACHE);
  const db = new DatabaseService(c.env.DB);

  // Check cache first
  const cacheKey = CacheKeys.BLACKLIST_PAGE(pagination.page, pagination.limit);
  const cached = await cache.get<PaginatedResponse<BlacklistIP>>(cacheKey);
  if (cached) {
    return c.json(cached);
  }

  // Query database
  const result = await db.queryPaginated<BlacklistIP>(
    `SELECT * FROM blacklist_ips WHERE is_active = 1 ORDER BY last_seen DESC`,
    `SELECT COUNT(*) as count FROM blacklist_ips WHERE is_active = 1`,
    [],
    pagination
  );

  // Cache result
  await cache.set(cacheKey, result, CacheTTL.BLACKLIST);

  return c.json(result);
});

/**
 * GET /api/blacklist/search
 * Search blacklisted IPs by various criteria
 */
blacklist.get('/search', async (c) => {
  const url = new URL(c.req.url);
  const pagination = parsePagination(url);
  const db = new DatabaseService(c.env.DB);

  // Extract search parameters
  const ip = url.searchParams.get('ip');
  const source = url.searchParams.get('source');
  const category = url.searchParams.get('category');
  const country = url.searchParams.get('country');
  const minConfidence = url.searchParams.get('min_confidence');

  // Build WHERE clause
  const conditions: string[] = ['is_active = 1'];
  const params: unknown[] = [];

  if (ip) {
    conditions.push('ip_address LIKE ?');
    params.push(`%${ip}%`);
  }

  if (source) {
    conditions.push('source = ?');
    params.push(source);
  }

  if (category) {
    conditions.push('category = ?');
    params.push(category);
  }

  if (country) {
    conditions.push('country = ?');
    params.push(country);
  }

  if (minConfidence) {
    conditions.push('confidence_level >= ?');
    params.push(parseInt(minConfidence, 10));
  }

  const whereClause = conditions.join(' AND ');

  const result = await db.queryPaginated<BlacklistIP>(
    `SELECT * FROM blacklist_ips WHERE ${whereClause} ORDER BY last_seen DESC`,
    `SELECT COUNT(*) as count FROM blacklist_ips WHERE ${whereClause}`,
    params,
    pagination
  );

  return c.json(result);
});

/**
 * GET /api/blacklist/sources
 * Get breakdown of IPs by source
 */
blacklist.get('/sources', async (c) => {
  const cache = new CacheService(c.env.CACHE);
  const db = new DatabaseService(c.env.DB);

  // Check cache
  const cached = await cache.get<{ sources: Record<string, number> }>(CacheKeys.SOURCES);
  if (cached) {
    return c.json(cached);
  }

  // Query for source breakdown
  const results = await db.query<{ source: string; count: number }>(
    `SELECT source, COUNT(*) as count 
     FROM blacklist_ips 
     WHERE is_active = 1 
     GROUP BY source 
     ORDER BY count DESC`
  );

  const sources: Record<string, number> = {};
  for (const row of results) {
    sources[row.source] = row.count;
  }

  const response = { sources };
  await cache.set(CacheKeys.SOURCES, response, CacheTTL.SOURCES);

  return c.json(response);
});

/**
 * GET /api/blacklist/categories
 * Get breakdown of IPs by category
 */
blacklist.get('/categories', async (c) => {
  const cache = new CacheService(c.env.CACHE);
  const db = new DatabaseService(c.env.DB);

  const cacheKey = 'categories:list';
  const cached = await cache.get<{ categories: Record<string, number> }>(cacheKey);
  if (cached) {
    return c.json(cached);
  }

  const results = await db.query<{ category: string; count: number }>(
    `SELECT category, COUNT(*) as count 
     FROM blacklist_ips 
     WHERE is_active = 1 
     GROUP BY category 
     ORDER BY count DESC`
  );

  const categories: Record<string, number> = {};
  for (const row of results) {
    categories[row.category] = row.count;
  }

  const response = { categories };
  await cache.set(cacheKey, response, CacheTTL.SOURCES);

  return c.json(response);
});

/**
 * GET /api/blacklist/countries
 * Get breakdown of IPs by country
 */
blacklist.get('/countries', async (c) => {
  const cache = new CacheService(c.env.CACHE);
  const db = new DatabaseService(c.env.DB);

  const cacheKey = 'countries:list';
  const cached = await cache.get<{ countries: Record<string, number> }>(cacheKey);
  if (cached) {
    return c.json(cached);
  }

  const results = await db.query<{ country: string; count: number }>(
    `SELECT country, COUNT(*) as count 
     FROM blacklist_ips 
     WHERE is_active = 1 AND country IS NOT NULL 
     GROUP BY country 
     ORDER BY count DESC`
  );

  const countries: Record<string, number> = {};
  for (const row of results) {
    countries[row.country] = row.count;
  }

  const response = { countries };
  await cache.set(cacheKey, response, CacheTTL.SOURCES);

  return c.json(response);
});

/**
 * GET /api/blacklist/:ip
 * Get details for a specific IP
 */
blacklist.get('/:ip', async (c) => {
  const ip = c.req.param('ip');
  const db = new DatabaseService(c.env.DB);

  const result = await db.queryOne<BlacklistIP>(
    `SELECT * FROM blacklist_ips WHERE ip_address = ?`,
    [ip]
  );

  if (!result) {
    return c.json({ error: 'IP not found' }, 404);
  }

  // Parse raw_data JSON
  const data = {
    ...result,
    raw_data: result.raw_data ? JSON.parse(result.raw_data) : null,
  };

  return c.json(data);
});

/**
 * GET /api/blacklist/fortinet/format
 * Get IPs in FortiGate-compatible format
 */
blacklist.get('/fortinet/format', async (c) => {
  const db = new DatabaseService(c.env.DB);
  const cache = new CacheService(c.env.CACHE);

  // Get client info for logging
  const clientIP = c.req.header('CF-Connecting-IP') || 'unknown';
  const userAgent = c.req.header('User-Agent') || 'unknown';

  // Check cache
  const cacheKey = 'fortinet:format';
  const cached = await cache.get<string>(cacheKey);

  // Get IPs
  let ips: string[];
  if (cached) {
    ips = cached.split('\n');
  } else {
    const results = await db.query<{ ip_address: string }>(
      `SELECT DISTINCT ip_address FROM blacklist_ips WHERE is_active = 1`
    );
    ips = results.map((r) => r.ip_address);
    await cache.set(cacheKey, ips.join('\n'), CacheTTL.BLACKLIST);
  }

  // Log the pull
  await db.execute(
    `INSERT INTO fortinet_pull_logs (device_ip, user_agent, request_path, ip_count, created_at)
     VALUES (?, ?, ?, ?, datetime('now'))`,
    [clientIP, userAgent, '/api/blacklist/fortinet/format', ips.length]
  );

  // Return as plain text (one IP per line)
  return c.text(ips.join('\n'), 200, {
    'Content-Type': 'text/plain',
    'X-IP-Count': String(ips.length),
  });
});

export default blacklist;
