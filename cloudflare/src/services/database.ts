/**
 * Database Service
 * D1 wrapper with query helpers and transaction support
 */

import type { D1Database, D1Result } from '@cloudflare/workers-types';
import type { PaginationParams, PaginatedResponse } from '../types/index.js';

export class DatabaseService {
  constructor(private db: D1Database) {}

  /**
   * Execute a SELECT query and return all results
   */
  async query<T>(sql: string, params: unknown[] = []): Promise<T[]> {
    const stmt = this.db.prepare(sql);
    const bound = params.length > 0 ? stmt.bind(...params) : stmt;
    const result = await bound.all<T>();
    return result.results ?? [];
  }

  /**
   * Execute a SELECT query and return the first result
   */
  async queryOne<T>(sql: string, params: unknown[] = []): Promise<T | null> {
    const stmt = this.db.prepare(sql);
    const bound = params.length > 0 ? stmt.bind(...params) : stmt;
    const result = await bound.first<T>();
    return result ?? null;
  }

  /**
   * Execute an INSERT/UPDATE/DELETE and return the result
   */
  async execute(sql: string, params: unknown[] = []): Promise<D1Result> {
    const stmt = this.db.prepare(sql);
    const bound = params.length > 0 ? stmt.bind(...params) : stmt;
    return bound.run();
  }

  /**
   * Execute multiple statements in a batch (transaction-like)
   */
  async batch(statements: { sql: string; params?: unknown[] }[]): Promise<D1Result[]> {
    const prepared = statements.map(({ sql, params }) => {
      const stmt = this.db.prepare(sql);
      return params && params.length > 0 ? stmt.bind(...params) : stmt;
    });
    return this.db.batch(prepared);
  }

  /**
   * Paginated query helper
   */
  async queryPaginated<T>(
    sql: string,
    countSql: string,
    params: unknown[],
    pagination: PaginationParams
  ): Promise<PaginatedResponse<T>> {
    // Get total count
    const countResult = await this.queryOne<{ count: number }>(countSql, params);
    const total = countResult?.count ?? 0;

    // Get paginated data
    const paginatedSql = `${sql} LIMIT ? OFFSET ?`;
    const data = await this.query<T>(paginatedSql, [...params, pagination.limit, pagination.offset]);

    const totalPages = Math.ceil(total / pagination.limit);

    return {
      data,
      pagination: {
        page: pagination.page,
        limit: pagination.limit,
        total,
        total_pages: totalPages,
        has_next: pagination.page < totalPages,
        has_prev: pagination.page > 1,
      },
    };
  }

  /**
   * Upsert helper (INSERT OR REPLACE)
   */
  async upsert(
    table: string,
    data: Record<string, unknown>,
    conflictColumns: string[]
  ): Promise<D1Result> {
    const columns = Object.keys(data);
    const values = Object.values(data);
    const placeholders = columns.map(() => '?').join(', ');
    const updateSet = columns
      .filter((col) => !conflictColumns.includes(col))
      .map((col) => `${col} = excluded.${col}`)
      .join(', ');

    const sql = `
      INSERT INTO ${table} (${columns.join(', ')})
      VALUES (${placeholders})
      ON CONFLICT (${conflictColumns.join(', ')})
      DO UPDATE SET ${updateSet}, updated_at = datetime('now')
    `;

    return this.execute(sql, values);
  }

  /**
   * Batch upsert for bulk operations
   */
  async batchUpsert(
    table: string,
    dataArray: Record<string, unknown>[],
    conflictColumns: string[]
  ): Promise<D1Result[]> {
    if (dataArray.length === 0) return [];

    const columns = Object.keys(dataArray[0]);
    const updateSet = columns
      .filter((col) => !conflictColumns.includes(col))
      .map((col) => `${col} = excluded.${col}`)
      .join(', ');

    const statements = dataArray.map((data) => {
      const values = Object.values(data);
      const placeholders = columns.map(() => '?').join(', ');

      return {
        sql: `
          INSERT INTO ${table} (${columns.join(', ')})
          VALUES (${placeholders})
          ON CONFLICT (${conflictColumns.join(', ')})
          DO UPDATE SET ${updateSet}, updated_at = datetime('now')
        `,
        params: values,
      };
    });

    return this.batch(statements);
  }
}

/**
 * Parse pagination from request query params
 */
export function parsePagination(url: URL): PaginationParams {
  const page = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10));
  const limit = Math.min(1000, Math.max(1, parseInt(url.searchParams.get('limit') || '100', 10)));
  const offset = (page - 1) * limit;

  return { page, limit, offset };
}
