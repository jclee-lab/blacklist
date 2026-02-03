/**
 * Collection Routes
 * /api/collection/* endpoints
 */

import { Hono } from 'hono';
import type { Env, CollectionJob } from '../types/index.js';
import { DatabaseService } from '../services/database.js';
import { CacheService } from '../services/cache.js';

const collection = new Hono<{ Bindings: Env }>();

/**
 * GET /api/collection/status
 * Get status of all collection services
 */
collection.get('/status', async (c) => {
  const db = new DatabaseService(c.env.DB);

  const status = await db.query<{
    service_name: string;
    enabled: number;
    status: string;
    last_run: string | null;
    next_run: string | null;
    error_count: number;
    success_count: number;
    config: string;
  }>(`SELECT * FROM collection_status ORDER BY service_name`);

  return c.json({
    services: status.map((s) => ({
      ...s,
      enabled: s.enabled === 1,
      config: JSON.parse(s.config || '{}'),
    })),
  });
});

/**
 * POST /api/collection/trigger
 * Manually trigger a collection
 */
collection.post('/trigger', async (c) => {
  const body = await c.req.json<{ service_name: string }>();
  const { service_name } = body;

  if (!service_name) {
    return c.json({ error: 'service_name is required' }, 400);
  }

  const db = new DatabaseService(c.env.DB);

  // Check if service exists and is enabled
  const service = await db.queryOne<{ enabled: number; status: string }>(
    `SELECT enabled, status FROM collection_status WHERE service_name = ?`,
    [service_name]
  );

  if (!service) {
    return c.json({ error: 'Service not found' }, 404);
  }

  if (service.enabled !== 1) {
    return c.json({ error: 'Service is disabled' }, 400);
  }

  if (service.status === 'running') {
    return c.json({ error: 'Collection already running' }, 409);
  }

  // Queue the collection job
  const job: CollectionJob = {
    service_name,
    triggered_by: 'manual',
    timestamp: new Date().toISOString(),
  };

  await c.env.COLLECTION_QUEUE.send(job);

  // Update status to running
  await db.execute(
    `UPDATE collection_status SET status = 'running', updated_at = datetime('now') WHERE service_name = ?`,
    [service_name]
  );

  return c.json({ message: 'Collection queued', job });
});

/**
 * GET /api/collection/history
 * Get collection history
 */
collection.get('/history', async (c) => {
  const url = new URL(c.req.url);
  const serviceName = url.searchParams.get('service_name');
  const limit = Math.min(100, parseInt(url.searchParams.get('limit') || '50', 10));

  const db = new DatabaseService(c.env.DB);

  let sql = `SELECT * FROM collection_history`;
  const params: unknown[] = [];

  if (serviceName) {
    sql += ` WHERE service_name = ?`;
    params.push(serviceName);
  }

  sql += ` ORDER BY collection_date DESC LIMIT ?`;
  params.push(limit);

  const history = await db.query<{
    id: number;
    service_name: string;
    collection_date: string;
    items_collected: number;
    success: number;
    error_message: string | null;
    execution_time_ms: number;
    details: string;
  }>(sql, params);

  return c.json({
    history: history.map((h) => ({
      ...h,
      success: h.success === 1,
      details: JSON.parse(h.details || '{}'),
    })),
  });
});

/**
 * GET /api/collection/credentials
 * Get collection credentials (masked)
 */
collection.get('/credentials', async (c) => {
  const db = new DatabaseService(c.env.DB);

  const credentials = await db.query<{
    id: number;
    service_name: string;
    username: string | null;
    config: string;
    encrypted: number;
    is_active: number;
    enabled: number;
    last_collection: string | null;
  }>(`
    SELECT id, service_name, username, config, encrypted, is_active, enabled, last_collection
    FROM collection_credentials
    ORDER BY service_name
  `);

  return c.json({
    credentials: credentials.map((cred) => ({
      ...cred,
      password: '********', // Always mask
      encrypted: cred.encrypted === 1,
      is_active: cred.is_active === 1,
      enabled: cred.enabled === 1,
      config: JSON.parse(cred.config || '{}'),
    })),
  });
});

/**
 * PUT /api/collection/credentials/:service_name
 * Update collection credentials
 */
collection.put('/credentials/:service_name', async (c) => {
  const serviceName = c.req.param('service_name');
  const body = await c.req.json<{
    username?: string;
    password?: string;
    config?: Record<string, unknown>;
    enabled?: boolean;
  }>();

  const db = new DatabaseService(c.env.DB);

  // Check if credential exists
  const existing = await db.queryOne<{ id: number }>(
    `SELECT id FROM collection_credentials WHERE service_name = ?`,
    [serviceName]
  );

  if (!existing) {
    return c.json({ error: 'Credential not found' }, 404);
  }

  // Build update query
  const updates: string[] = ['updated_at = datetime(\'now\')'];
  const params: unknown[] = [];

  if (body.username !== undefined) {
    updates.push('username = ?');
    params.push(body.username);
  }

  if (body.password !== undefined) {
    // In production, encrypt the password here
    updates.push('password = ?');
    params.push(body.password);
  }

  if (body.config !== undefined) {
    updates.push('config = ?');
    params.push(JSON.stringify(body.config));
  }

  if (body.enabled !== undefined) {
    updates.push('enabled = ?');
    params.push(body.enabled ? 1 : 0);
  }

  params.push(serviceName);

  await db.execute(
    `UPDATE collection_credentials SET ${updates.join(', ')} WHERE service_name = ?`,
    params
  );

  // Invalidate cache
  const cache = new CacheService(c.env.CACHE);
  await cache.delete('collection:credentials');

  return c.json({ message: 'Credential updated' });
});

/**
 * PUT /api/collection/status/:service_name
 * Enable/disable a collection service
 */
collection.put('/status/:service_name', async (c) => {
  const serviceName = c.req.param('service_name');
  const body = await c.req.json<{ enabled: boolean }>();

  const db = new DatabaseService(c.env.DB);

  await db.execute(
    `UPDATE collection_status 
     SET enabled = ?, status = ?, updated_at = datetime('now') 
     WHERE service_name = ?`,
    [body.enabled ? 1 : 0, body.enabled ? 'idle' : 'disabled', serviceName]
  );

  return c.json({ message: 'Status updated' });
});

/**
 * POST /api/collection/ingest
 * Ingest blacklist data from local agent
 * Requires X-API-Key header
 */
collection.post('/ingest', async (c) => {
  // Validate API key
  const apiKey = c.req.header('X-API-Key');
  if (!apiKey || apiKey !== c.env.INGEST_API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  const body = await c.req.json<{
    service_name: string;
    items: Array<{
      ip_address: string;
      threat_type?: string;
      severity?: string;
      source?: string;
      country_code?: string;
      first_seen?: string;
      last_seen?: string;
      description?: string;
      metadata?: Record<string, unknown>;
    }>;
    collection_date?: string;
  }>();

  const { service_name, items, collection_date } = body;

  if (!service_name || !items || !Array.isArray(items)) {
    return c.json({ error: 'service_name and items array required' }, 400);
  }

  const db = new DatabaseService(c.env.DB);
  const now = new Date().toISOString();
  const collectionDateStr = collection_date || now.split('T')[0];

  let inserted = 0;
  let updated = 0;
  let errors = 0;

  for (const item of items) {
    try {
      // Check if IP already exists (unique on ip_address + source)
      const existing = await db.queryOne<{ id: number }>(
        `SELECT id FROM blacklist_ips WHERE ip_address = ? AND source = ?`,
        [item.ip_address, item.source || service_name]
      );

      if (existing) {
        // Update existing record
        await db.execute(
          `UPDATE blacklist_ips SET
            last_seen = ?,
            reason = COALESCE(?, reason),
            category = COALESCE(?, category),
            confidence_level = COALESCE(?, confidence_level),
            detection_count = detection_count + 1,
            raw_data = COALESCE(?, raw_data),
            updated_at = ?
          WHERE id = ?`,
          [
            item.last_seen || now,
            item.threat_type,
            item.severity,
            item.metadata?.confidence_level || null,
            item.metadata ? JSON.stringify(item.metadata) : null,
            now,
            existing.id,
          ]
        );
        updated++;
      } else {
        // Insert new record - match actual D1 schema
        await db.execute(
          `INSERT INTO blacklist_ips (
            ip_address, reason, source, category, confidence_level,
            detection_count, is_active, country, detection_date, last_seen,
            created_at, updated_at, raw_data, data_source
          ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)`,
          [
            item.ip_address,
            item.threat_type || item.description || 'unknown',
            item.source || service_name,
            item.severity || 'unknown',
            item.metadata?.confidence_level || 80,
            1,
            item.country_code || null,
            item.first_seen || now,
            item.last_seen || now,
            now,
            now,
            item.metadata ? JSON.stringify(item.metadata) : '{}',
            service_name,
          ]
        );
        inserted++;
      }
    } catch (e) {
      console.error(`Failed to process IP ${item.ip_address}:`, e);
      errors++;
    }
  }

  // Record collection history
  await db.execute(
    `INSERT INTO collection_history (
      service_name, collection_date, items_collected, success, error_message, execution_time_ms, details
    ) VALUES (?, ?, ?, 1, NULL, 0, ?)`,
    [
      service_name,
      collectionDateStr,
      inserted + updated,
      JSON.stringify({ inserted, updated, errors, total: items.length }),
    ]
  );

  // Update collection status
  await db.execute(
    `UPDATE collection_status SET
      status = 'idle',
      last_run = ?,
      success_count = success_count + 1,
      updated_at = ?
    WHERE service_name = ?`,
    [now, now, service_name]
  );

  // Update credentials last_collection
  await db.execute(
    `UPDATE collection_credentials SET last_collection = ? WHERE service_name = ?`,
    [now, service_name]
  );

  // Invalidate cache
  const cache = new CacheService(c.env.CACHE);
  await cache.delete('stats:dashboard');
  await cache.delete('blacklist:list:*');

  return c.json({
    success: true,
    service_name,
    collection_date: collectionDateStr,
    stats: { inserted, updated, errors, total: items.length },
  });
});

export default collection;
