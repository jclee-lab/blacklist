# PostgreSQL Schema Dependency & Initialization Order

## 📋 Initialization Script Execution Order

PostgreSQL executes scripts in `/docker-entrypoint-initdb.d/` in **alphabetical order**.

### Execution Sequence

```
postgres/init-scripts/
├── 00-complete-schema.sql       (1) ← Core schema definition
├── 00-schema-check.sql          (2) ← Auto-validation & fixes
├── 01-credentials.sql           (3) ← Default credentials
├── 02-migrate-pipeline-metrics.sql (4) ← Pipeline metrics migration
├── 03-fix-collection-metrics.sql   (5) ← Collection metrics fixes
├── 04-fix-schema-patch.sql         (6) ← Schema patches
├── 08_collection_credentials_extended.sql (7) ← Extended credentials
└── 09_add_data_source_columns.sql  (8) ← Data source columns
```

---

## 🔗 Dependency Graph

```
00-complete-schema.sql (Base Schema)
    ├── 10 Tables Created
    │   ├── blacklist_ips
    │   ├── whitelist_ips
    │   ├── collection_credentials
    │   ├── collection_history
    │   ├── monitoring_data
    │   ├── system_logs
    │   ├── collection_status
    │   ├── pipeline_metrics
    │   ├── collection_metrics
    │   └── collection_stats
    │
    ├── 33+ Indexes
    ├── 7 Views
    ├── 2 Functions
    └── 4 Triggers

↓ (depends on tables)

00-schema-check.sql (Validation)
    ├── Validates data_source columns
    ├── Creates helper functions
    └── Reports schema status

↓ (depends on tables)

01-credentials.sql
    ├── Inserts default REGTECH credentials
    └── Inserts default SECUDIUM credentials

↓ (depends on tables)

02-migrate-pipeline-metrics.sql
    └── Migrates pipeline_metrics data

↓ (depends on tables)

03-fix-collection-metrics.sql
    └── Fixes collection_metrics issues

↓ (depends on tables)

04-fix-schema-patch.sql
    └── Applies additional schema patches

↓ (depends on collection_credentials)

08_collection_credentials_extended.sql
    └── Extends collection_credentials table

↓ (depends on blacklist_ips, whitelist_ips)

09_add_data_source_columns.sql
    └── Adds data_source columns (idempotent)
```

---

## 📦 Table Dependencies

### Core Tables (No Dependencies)
- `blacklist_ips` - Standalone
- `whitelist_ips` - Standalone
- `collection_credentials` - Standalone

### Logging Tables (No Foreign Keys)
- `collection_history` - References `collection_credentials` by name (VARCHAR)
- `monitoring_data` - Standalone
- `system_logs` - Standalone

### Status Tables
- `collection_status` - References `collection_credentials` by name (VARCHAR)

### Metrics Tables
- `pipeline_metrics` - Standalone (composite PK)
- `collection_metrics` - References services by name
- `collection_stats` - Standalone

---

## 🔐 Schema Integrity Checks

### Required Constraints
1. **IP Format Validation**
   ```sql
   CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$')
   ```

2. **Date Logic Validation**
   ```sql
   CHECK (removal_date IS NULL OR detection_date <= removal_date)
   ```

3. **Service Name Format**
   ```sql
   CHECK (service_name ~ '^[A-Z_]+$')
   ```

4. **Non-Negative Counters**
   ```sql
   CHECK (collected_count >= 0)
   CHECK (error_count >= 0 AND success_count >= 0)
   ```

---

## 🚨 Critical Notes

### When Init Scripts Execute
- ✅ **First-time startup**: When `/var/lib/postgresql/data` is **empty**
- ❌ **Container restart**: Scripts **NOT executed** (data already exists)
- ✅ **Volume deletion**: `docker-compose down -v` → Scripts re-executed

### Schema Update Strategy
1. **Development**: Delete volume → Rebuild
   ```bash
   docker-compose down -v
   make deploy
   ```

2. **Production**: Use migration scripts in `postgres/migrations/`
   ```bash
   docker exec blacklist-postgres psql -U postgres -d blacklist < migration.sql
   ```

### Idempotency
All scripts use:
- `CREATE TABLE IF NOT EXISTS`
- `CREATE INDEX IF NOT EXISTS`
- `ALTER TABLE ... IF NOT EXISTS`
- `DO $$ IF NOT EXISTS ... END $$`

---

## 📊 Schema Version

**Current Version**: 3.0.0
**Total Lines**: 520+ (00-complete-schema.sql)
**Last Updated**: 2025-10-29

---

## 🔍 Validation Commands

### Check Schema Completeness
```sql
-- Count tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
-- Expected: 10

-- Count indexes
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';
-- Expected: 33+

-- Count views
SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';
-- Expected: 7
```

### Check Required Columns
```sql
-- Validate data_source column exists
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'data_source' AND table_schema = 'public';
-- Expected: blacklist_ips, whitelist_ips
```

---

**Document Version**: 1.0
**Author**: Blacklist System Team
**Date**: 2025-11-08
