/**
 * Cache Service
 * KV wrapper with TTL and JSON serialization
 */

import type { KVNamespace } from '@cloudflare/workers-types';

export class CacheService {
  constructor(private kv: KVNamespace) {}

  /**
   * Get a value from cache
   */
  async get<T>(key: string): Promise<T | null> {
    const value = await this.kv.get(key, 'text');
    if (!value) return null;

    try {
      return JSON.parse(value) as T;
    } catch {
      return value as unknown as T;
    }
  }

  /**
   * Set a value in cache with optional TTL (seconds)
   */
  async set<T>(key: string, value: T, ttlSeconds?: number): Promise<void> {
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    const options = ttlSeconds ? { expirationTtl: ttlSeconds } : undefined;
    await this.kv.put(key, serialized, options);
  }

  /**
   * Delete a value from cache
   */
  async delete(key: string): Promise<void> {
    await this.kv.delete(key);
  }

  /**
   * Delete multiple keys by prefix
   */
  async deleteByPrefix(prefix: string): Promise<void> {
    const list = await this.kv.list({ prefix });
    const deletePromises = list.keys.map((key) => this.kv.delete(key.name));
    await Promise.all(deletePromises);
  }

  /**
   * Get or set pattern (cache-aside)
   */
  async getOrSet<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttlSeconds?: number
  ): Promise<T> {
    const cached = await this.get<T>(key);
    if (cached !== null) return cached;

    const fresh = await fetcher();
    await this.set(key, fresh, ttlSeconds);
    return fresh;
  }

  /**
   * List all keys with optional prefix
   */
  async listKeys(prefix?: string): Promise<string[]> {
    const list = await this.kv.list({ prefix });
    return list.keys.map((key) => key.name);
  }

  /**
   * Check if a key exists
   */
  async exists(key: string): Promise<boolean> {
    const value = await this.kv.get(key);
    return value !== null;
  }

  /**
   * Increment a numeric value (atomic using metadata)
   * Note: KV doesn't support atomic increment, this is best-effort
   */
  async increment(key: string, by: number = 1): Promise<number> {
    const current = await this.get<number>(key);
    const newValue = (current ?? 0) + by;
    await this.set(key, newValue);
    return newValue;
  }
}

/**
 * Rate limiter using KV
 */
export class RateLimiter {
  constructor(
    private kv: KVNamespace,
    private prefix: string = 'ratelimit'
  ) {}

  /**
   * Check if request is allowed under rate limit
   * Returns remaining requests or -1 if limit exceeded
   */
  async check(
    identifier: string,
    maxRequests: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
    const key = `${this.prefix}:${identifier}`;
    const now = Math.floor(Date.now() / 1000);
    const windowStart = now - (now % windowSeconds);
    const windowKey = `${key}:${windowStart}`;

    const countStr = await this.kv.get(windowKey);
    const count = countStr ? parseInt(countStr, 10) : 0;

    if (count >= maxRequests) {
      return {
        allowed: false,
        remaining: 0,
        resetAt: windowStart + windowSeconds,
      };
    }

    // Increment counter
    await this.kv.put(windowKey, String(count + 1), {
      expirationTtl: windowSeconds * 2, // Keep for 2 windows
    });

    return {
      allowed: true,
      remaining: maxRequests - count - 1,
      resetAt: windowStart + windowSeconds,
    };
  }
}
