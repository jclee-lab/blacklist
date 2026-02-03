/**
 * Health Routes
 * /health endpoint
 */

import { Hono } from 'hono';
import type { Env, HealthResponse } from '../types/index.js';
import { DatabaseService } from '../services/database.js';
import { CacheService } from '../services/cache.js';

const health = new Hono<{ Bindings: Env }>();

/**
 * GET /health
 * Health check endpoint
 */
health.get('/', async (c) => {
  const db = new DatabaseService(c.env.DB);
  const cache = new CacheService(c.env.CACHE);

  let dbHealthy = false;
  let cacheHealthy = false;

  // Check database
  try {
    await db.queryOne<{ result: number }>('SELECT 1 as result');
    dbHealthy = true;
  } catch {
    dbHealthy = false;
  }

  // Check cache
  try {
    await cache.set('health:check', Date.now(), 60);
    const value = await cache.get<number>('health:check');
    cacheHealthy = value !== null;
  } catch {
    cacheHealthy = false;
  }

  const status = dbHealthy && cacheHealthy ? 'healthy' : dbHealthy ? 'degraded' : 'unhealthy';
  const httpStatus = status === 'healthy' ? 200 : status === 'degraded' ? 200 : 503;

  const response: HealthResponse = {
    status,
    version: c.env.API_VERSION || '1.0.0',
    environment: c.env.ENVIRONMENT || 'unknown',
    timestamp: new Date().toISOString(),
    checks: {
      database: dbHealthy,
      cache: cacheHealthy,
    },
  };

  return c.json(response, httpStatus);
});

/**
 * GET /health/ready
 * Readiness check (for load balancer)
 */
health.get('/ready', async (c) => {
  const db = new DatabaseService(c.env.DB);

  try {
    // Quick database check
    await db.queryOne<{ result: number }>('SELECT 1 as result');
    return c.json({ ready: true }, 200);
  } catch {
    return c.json({ ready: false }, 503);
  }
});

/**
 * GET /health/live
 * Liveness check (for orchestrator)
 */
health.get('/live', (c) => {
  return c.json({ alive: true }, 200);
});

export default health;
