/**
 * Blacklist API - Main Entry Point
 * Cloudflare Workers + Hono.js
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { prettyJSON } from 'hono/pretty-json';
import { secureHeaders } from 'hono/secure-headers';

import type { Env, CollectionJob } from './types/index.js';
import blacklistRoutes from './routes/blacklist.js';
import statsRoutes from './routes/stats.js';
import collectionRoutes from './routes/collection.js';
import healthRoutes from './routes/health.js';
import { DatabaseService } from './services/database.js';
import { RegtechCollector } from './services/collector.js';
import puppeteer from '@cloudflare/puppeteer';

// Create Hono app
const app = new Hono<{ Bindings: Env }>();

// ============================================================
// Middleware
// ============================================================

// CORS
app.use('*', async (c, next) => {
  const corsMiddleware = cors({
    origin: c.env.CORS_ORIGINS?.split(',') || ['*'],
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
    maxAge: 86400,
  });
  return corsMiddleware(c, next);
});

// Security headers
app.use('*', secureHeaders());

// JSON formatting (development only)
app.use('*', async (c, next) => {
  if (c.env.ENVIRONMENT !== 'production') {
    return prettyJSON()(c, next);
  }
  return next();
});

// Logger (development only)
app.use('*', async (c, next) => {
  if (c.env.ENVIRONMENT !== 'production') {
    return logger()(c, next);
  }
  return next();
});

// ============================================================
// Routes
// ============================================================

// Mount route modules
app.route('/api/blacklist', blacklistRoutes);
app.route('/api/stats', statsRoutes);
app.route('/api/collection', collectionRoutes);
app.route('/health', healthRoutes);

// Root endpoint
app.get('/', (c) => {
  return c.json({
    name: 'Blacklist API',
    version: c.env.API_VERSION || '1.0.0',
    environment: c.env.ENVIRONMENT || 'unknown',
    docs: '/health',
  });
});

// API info endpoint
app.get('/api', (c) => {
  return c.json({
    endpoints: [
      'GET /api/blacklist/list',
      'GET /api/blacklist/search',
      'GET /api/blacklist/sources',
      'GET /api/blacklist/categories',
      'GET /api/blacklist/countries',
      'GET /api/blacklist/:ip',
      'GET /api/blacklist/fortinet/format',
      'GET /api/stats',
      'GET /api/stats/collection',
      'GET /api/stats/timeline',
      'GET /api/collection/status',
      'POST /api/collection/trigger',
      'GET /api/collection/history',
      'GET /api/collection/credentials',
      'PUT /api/collection/credentials/:service_name',
      'PUT /api/collection/status/:service_name',
      'GET /health',
      'GET /health/ready',
      'GET /health/live',
    ],
  });
});

// ============================================================
// Debug: REGTECH Page Capture
// ============================================================

app.get('/debug/regtech', async (c) => {
  const browser = await puppeteer.launch(c.env.BROWSER);
  try {
    const page = await browser.newPage();
    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );
    
    // First visit main page
    await page.goto('https://regtech.fsec.or.kr', {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });
    
    const mainUrl = page.url();
    const mainBody = await page.evaluate(`document.body?.innerText?.substring(0, 500) || ''`);
    
    // Try navigating to /user/login
    await page.goto('https://regtech.fsec.or.kr/user/login', {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });
    
    const loginUrl = page.url();
    const loginBody = await page.evaluate(`document.body?.innerText?.substring(0, 500) || ''`);
    const inputCount = await page.evaluate(`document.querySelectorAll('input').length`);
    
    return c.json({
      mainUrl,
      mainBodyPreview: mainBody,
      loginUrl,
      loginBodyPreview: loginBody,
      inputCount,
    });
  } catch (e) {
    return c.json({ error: String(e) });
  } finally {
    await browser.close();
  }
});

// ============================================================
// Error Handling
// ============================================================

app.onError((err, c) => {
  console.error('Unhandled error:', err);

  // RFC 7807 Problem Details
  return c.json(
    {
      type: 'about:blank',
      title: 'Internal Server Error',
      status: 500,
      detail: c.env.ENVIRONMENT === 'production' ? 'An unexpected error occurred' : err.message,
      instance: c.req.url,
    },
    500
  );
});

app.notFound((c) => {
  return c.json(
    {
      type: 'about:blank',
      title: 'Not Found',
      status: 404,
      detail: `Path ${c.req.path} not found`,
      instance: c.req.url,
    },
    404
  );
});

// ============================================================
// Exports
// ============================================================

export default {
  /**
   * HTTP fetch handler
   */
  fetch: app.fetch,

  /**
   * Scheduled (Cron) handler
   */
  async scheduled(event: ScheduledEvent, env: Env, _ctx: ExecutionContext): Promise<void> {
    console.log(`Cron triggered: ${event.cron} at ${new Date(event.scheduledTime).toISOString()}`);

    switch (event.cron) {
      case '0 */6 * * *':
        // REGTECH collection every 6 hours
        const regtechJob: CollectionJob = {
          service_name: 'REGTECH',
          triggered_by: 'cron',
          timestamp: new Date().toISOString(),
        };
        await env.COLLECTION_QUEUE.send(regtechJob);
        console.log('REGTECH collection job queued');
        break;

      case '0 0 * * *':
        // Daily cleanup
        const db = new DatabaseService(env.DB);
        const result = await db.execute(
          `UPDATE blacklist_ips 
           SET is_active = 0 
           WHERE last_seen < datetime('now', '-30 days') AND is_active = 1`
        );
        console.log(`Daily cleanup: ${result.meta?.changes ?? 0} IPs marked inactive`);
        break;

      case '*/5 * * * *':
        // Health check (just log)
        console.log('Health check cron executed');
        break;

      default:
        console.log(`Unknown cron: ${event.cron}`);
    }
  },

  /**
   * Queue consumer handler
   */
  async queue(batch: MessageBatch<CollectionJob>, env: Env): Promise<void> {
    console.log(`Processing ${batch.messages.length} collection jobs`);

    const db = new DatabaseService(env.DB);

    for (const message of batch.messages) {
      const job = message.body;
      const startTime = Date.now();

      console.log(`Processing job: ${job.service_name} (${job.triggered_by})`);

      try {
        // Update status to running
        await db.execute(
          `UPDATE collection_status SET status = 'running', updated_at = datetime('now') WHERE service_name = ?`,
          [job.service_name]
        );

        let itemsCollected = 0;

        if (job.service_name === 'REGTECH') {
          const collector = new RegtechCollector(env);
          const result = await collector.collect();
          
          if (!result.success) {
            throw new Error(result.error || 'REGTECH collection failed');
          }
          
          itemsCollected = result.itemsCollected;
          console.log(`REGTECH: Collected ${itemsCollected} items in ${result.duration}ms`);
        }

        const executionTime = Date.now() - startTime;

        // Log success
        await db.execute(
          `INSERT INTO collection_history (service_name, collection_date, items_collected, success, execution_time_ms, details)
           VALUES (?, datetime('now'), ?, 1, ?, ?)`,
          [job.service_name, itemsCollected, executionTime, JSON.stringify({ triggered_by: job.triggered_by })]
        );

        // Update status
        await db.execute(
          `UPDATE collection_status 
           SET status = 'idle', last_run = datetime('now'), success_count = success_count + 1, updated_at = datetime('now')
           WHERE service_name = ?`,
          [job.service_name]
        );

        message.ack();
        console.log(`Job completed: ${job.service_name} in ${executionTime}ms`);
      } catch (error) {
        const executionTime = Date.now() - startTime;
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';

        console.error(`Job failed: ${job.service_name}`, error);

        // Log failure
        await db.execute(
          `INSERT INTO collection_history (service_name, collection_date, items_collected, success, error_message, execution_time_ms, details)
           VALUES (?, datetime('now'), 0, 0, ?, ?, ?)`,
          [job.service_name, errorMessage, executionTime, JSON.stringify({ triggered_by: job.triggered_by })]
        );

        // Update status
        await db.execute(
          `UPDATE collection_status 
           SET status = 'error', error_count = error_count + 1, updated_at = datetime('now')
           WHERE service_name = ?`,
          [job.service_name]
        );

        // Retry logic handled by Cloudflare Queues
        message.retry();
      }
    }
  },
};
