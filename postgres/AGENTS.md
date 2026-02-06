# POSTGRES KNOWLEDGE BASE

**Generated:** 2026-02-06
**Role:** Database Schema & Migrations
**Parent:** [../AGENTS.md](../AGENTS.md)

---

## OVERVIEW

PostgreSQL 15 with Raw SQL only. **ORM forbidden** — SQLAlchemy/Prisma not allowed.
Migrations are sequential numbered SQL files.

---

## STRUCTURE

```
postgres/
├── Dockerfile              # PostgreSQL 15 + extensions
├── initdb/                 # Initial schema (run on fresh DB)
│   ├── 01-extensions.sql   # pg_trgm, uuid-ossp
│   ├── 02-schema.sql       # Core tables
│   └── 03-migrations.sql   # Migration tracking table
└── migrations/             # Incremental changes
    ├── 001_add_data_source_column.sql
    ├── 002_add_missing_columns.sql
    └── 003_add_display_order.sql
```

---

## HOW TO: Add Migration

### 1. Create migration file

```sql
-- migrations/004_add_new_column.sql
-- Migration: Add new column to blacklist table
-- Date: 2026-02-01

ALTER TABLE blacklist ADD COLUMN new_column VARCHAR(255);

-- Add index if needed
CREATE INDEX idx_blacklist_new_column ON blacklist(new_column);
```

### 2. Naming convention

```
{NNN}_{description}.sql
```
- `NNN`: Three-digit sequential number (001, 002, ...)
- `description`: Snake_case description

### 3. Apply migration

```bash
# Development (via docker compose)
docker compose exec blacklist-db psql -U blacklist -d blacklist -f /migrations/004_add_new_column.sql

# Or restart containers (initdb applies all migrations)
docker compose down && docker compose up -d
```

---

## CONVENTIONS

| Convention | Description |
|------------|-------------|
| **SQL only** | No ORM, no query builders |
| **Parameterized queries** | Always use `%s` placeholders |
| **Sequential numbering** | Never skip numbers |
| **Idempotent** | Use `IF NOT EXISTS` where possible |
| **Comments** | Include migration purpose at top |

---

## ANTI-PATTERNS

| ❌ Forbidden | ✅ Alternative | Reason |
|--------------|----------------|--------|
| SQLAlchemy models | Raw SQL | Project policy |
| Prisma schema | Raw SQL | Project policy |
| String concatenation | Parameterized queries | SQL Injection |
| `DROP TABLE` in migration | Add columns only | Data loss |
| Renaming without backward compat | Add new + deprecate old | Breaking change |

---

## INITDB SEQUENCE

On fresh database (container first start):

```
1. 01-extensions.sql  → Load pg_trgm, uuid-ossp
2. 02-schema.sql      → Create core tables
3. 03-migrations.sql  → Create migration tracking
4. migrations/*.sql   → Apply all migrations in order
```

---

## CORE TABLES

| Table | Purpose |
|-------|---------|
| `blacklist` | IP/domain blacklist entries |
| `collection_history` | ETL collection logs |
| `users` | Admin users |
| `credentials` | Encrypted API keys |
| `sources` | Data source configurations |

---

## NOTES

- **Backups**: Handled by infrastructure, not application
- **Connection pool**: Managed by `app/core/services/database_service.py`
- **Schema changes**: Require PR review, test in staging first
