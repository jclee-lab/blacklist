# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **⚠️ Repository Migration Notice**: This project has migrated from GitHub to GitLab (https://gitlab.jclee.me/jclee/blacklist). All CI/CD pipelines, container registry, and development workflows now use GitLab infrastructure.

---

## 🎯 Project Overview

**REGTECH Blacklist Intelligence Platform** - A Flask-based threat intelligence platform for collecting, managing, and analyzing IP blacklist data from Korean Financial Security Institute (REGTECH). Features automated collection pipelines, real-time monitoring, whitelist/blacklist management, and **air-gapped deployment** with GitLab CI/CD build automation.

**Architecture**: Microservices (5 independent containers)
- `blacklist-app` - Flask application (Port 2542)
- `blacklist-collector` - REGTECH collection service (Port 8545)
- `blacklist-postgres` - PostgreSQL 15 database (auto-migration on restart)
- `blacklist-redis` - Redis 7 cache
- `blacklist-frontend` - Next.js frontend (Port 2543)

**Repository Status**:
- **GitLab** (PRIMARY): https://gitlab.jclee.me/jclee/blacklist - Active development, CI/CD, Container Registry
- **GitHub** (Mirror): https://github.com/qws941/blacklist - Read-only mirror, no CI/CD

---

## ⚡ Quick Command Reference

### Most Common Operations
```bash
# Development
make dev                              # Start development environment
make logs                             # View all logs
make logs-app                         # App logs only
make health                           # Check all services

# Testing
make test                             # Run full test suite
python -m pytest -m unit              # Unit tests only
python -m pytest -m api               # API tests only
python -m pytest -m security          # Security tests

# Database
make db-shell                         # PostgreSQL shell
make db-backup                        # Backup database
make db-restore BACKUP_FILE=...       # Restore from backup

# Troubleshooting
docker logs blacklist-app             # App logs
docker logs blacklist-postgres | grep Migration  # Migration status
docker exec blacklist-redis redis-cli ping       # Redis health
curl http://localhost:2542/health     # API health check

# CI/CD
git push origin main                  # Trigger build pipeline
./scripts/package-single-image.sh blacklist-app  # Package for offline
```

### Key Project Locations
```bash
# Source code
app/core/routes/api/          # API routes (11 modules)
app/core/routes/web/          # Web UI routes (8 modules)
app/core/services/            # Business logic (15 services)
collector/core/               # Collection logic (6 modules, 138.8 KB)

# Tests
tests/unit/                   # Unit tests (226.8 KB, 13+ files)
tests/integration/            # Integration tests
tests/security/               # Security tests (CSRF, rate limiting)

# Configuration
docker-compose.yml            # Production config (symlink to .prod.yml)
.gitlab-ci.yml                # CI/CD pipeline (air-gapped build)
postgres/migrations/          # Auto-applied migrations
```

### Key Files
```bash
app/core/app.py               # Flask factory (CSRF, rate limiting)
app/core/services/database_service.py  # DB connection pool
app/core/services/blacklist_service.py # IP filtering logic
collector/monitoring_scheduler.py      # Auto-collection orchestrator
Makefile                      # Development commands
```

---

## 🏗️ Architecture & Key Patterns

### Auto-Migrating Database System

**Critical Behavior**: PostgreSQL automatically runs all migrations on **every container restart**, not just the first time. This prevents the common "DB schema lost on restart" problem.

**How It Works**:
1. Custom entrypoint (`postgres/docker-entrypoint-custom.sh`) wraps the official PostgreSQL startup
2. Executes all `.sql` files in `postgres/migrations/` directory in alphanumeric order
3. All migrations use idempotent patterns (`IF NOT EXISTS`, `IF EXISTS`)
4. After migrations complete, starts PostgreSQL normally

**Key Benefit**: `make restart` is safe - your schema always matches the migration files.

### Flask Application Factory Pattern

**Location**: `app/core/app.py::create_app()`

**Key Components**:
- CSRF Protection via Flask-WTF
- Redis-backed rate limiting (Flask-Limiter)
- Security headers middleware
- Structured logging with correlation IDs
- Blueprint-based route organization

### Route Organization (Updated 2025-11-12)

**Location**: `app/core/routes/`

**API Routes** (`api/` - 11 modules):
- `analytics.py` - Detection analytics & reporting (16.5 KB)
- `blacklist.py` - Core blacklist operations (33.1 KB)
- `collection.py` - Collection orchestration (19.9 KB)
- `collection_api.py` - Collection triggers (8.5 KB)
- `core_api.py` - Health, stats, monitoring (1.6 KB)
- `database_api.py` - Database operations (7.8 KB)
- `fortinet.py` - FortiGate/FortiManager integration (21.0 KB)
- `ip_management_api.py` - Blacklist/whitelist operations (19.2 KB)
- `migration.py` - Data migration tools (8.9 KB)
- `statistics.py` - Statistics endpoints (30.5 KB)
- `system_api.py` - System management (14.3 KB)

**Web UI Routes** (`web/` - 8 modules):
- `admin.py` - REGTECH admin panel (25.7 KB)
- `admin_routes.py` - Admin UI operations (9.9 KB)
- `api_routes.py` - Web API bridge (15.9 KB)
- `collection_panel.py` - Collection control panel (23.8 KB)
- `collection_routes.py` - Collection UI (8.4 KB)
- `dashboard_routes.py` - Dashboard views (5.9 KB)
- `monitoring.py` - Monitoring dashboard (2.6 KB)
- `settings.py` - System settings UI (14.6 KB)

**Blueprint Pattern**:
- Each file defines a Flask Blueprint
- Blueprints registered in `app.py::create_app()`
- Centralized route organization by feature
- CSRF and rate limiting applied per blueprint

### Service Layer Architecture

**Location**: `app/core/services/` (15 services)

**Core Infrastructure Services**:
- `database_service.py` (13.7 KB) - Connection pooling with exponential backoff retry, whitelist priority
- `blacklist_service.py` (33.9 KB) - IP filtering, Redis caching, Prometheus metrics
- `secure_credential_service.py` (17.2 KB) - AES-256-GCM encryption, audit logging

**Collection & Integration Services**:
- `collection_service.py` (19.4 KB) - Collection orchestration, error tracking
- `scheduler_service.py` (9.9 KB) - Collection scheduling, database-driven config
- `regtech_config_service.py` (14.5 KB) - REGTECH configuration management
- `secudium_collector_service.py` (10.6 KB) - SECUDIUM browser automation
- `fortimanager_push_service.py` (6.9 KB) - FortiManager integration

**Business Logic Services**:
- `analytics_service.py` (10.9 KB) - Analytics, reporting, statistics
- `scoring_service.py` (5.3 KB) - Risk scoring, threat classification
- `expiry_service.py` (7.3 KB) - IP expiration handling, TTL management
- `credential_service.py` (15.3 KB) - Credential CRUD operations
- `settings_service.py` (13.9 KB) - System settings persistence
- `ab_test_service.py` (3.8 KB) - A/B testing utilities

**Connection Pooling Details**:
- ThreadedConnectionPool (3-8 connections)
- Exponential backoff retry: 2s, 4s, 8s, 16s, ... (max 10 attempts)
- Automatic test connection before returning pool
- Per-request retry for connection acquisition

### Priority-Based IP Filtering

**Whitelist → Blacklist Logic** (`app/core/services/database_service.py`):
1. Check whitelist table first (VIP/Admin protection)
2. If found → ALLOW (return immediately)
3. If not found → Check blacklist table
4. If found in blacklist → BLOCK

**Performance Optimization**:
- Redis caching for frequently checked IPs
- Database connection pooling
- Prepared statement reuse

### Multi-Source Collection Orchestration

**Pattern**: `CollectorScheduler` (collector/monitoring_scheduler.py)

**Architecture**:
```
CollectorScheduler (Main Orchestrator)
├── REGTECH Collector Thread
│   ├── Monitoring collection (daily)
│   ├── Policy collection (configurable)
│   └── Excel/CSV parsing with binary fallback
├── SECUDIUM Collector Thread
│   ├── Browser automation (Playwright)
│   ├── Report deduplication (processed_reports table)
│   └── Multi-page download handling
└── Future Source Threads (extensible)
```

**Key Features**:
- Database-driven configuration (per-source enable/disable)
- Independent thread scheduling per source
- Configurable intervals: hourly, daily, weekly
- Error count tracking with adaptive retry intervals
- Statistics per source (success/failure tracking)
- Graceful shutdown with daemon thread management

### Common Utilities (2025-11-08)

**Location**: `app/core/utils/`

**Database Utilities** (`db_utils.py`):
```python
from utils.db_utils import execute_query, execute_write

# Query with context manager
result = execute_query(
    "SELECT * FROM blacklist_ips WHERE country = %s",
    ('CN',)
)

# Write operation
execute_write(
    "INSERT INTO whitelist_ips (ip_address, reason) VALUES (%s, %s)",
    ('192.168.1.100', 'VIP customer')
)
```

**Redis Caching** (`cache_utils.py`):
```python
from utils.cache_utils import CacheManager, cached

cache = CacheManager()

# Manual cache
cache.set('key', {'data': 'value'}, expire=3600)
data = cache.get('key')

# Decorator-based caching
@cached(expire=300)
def expensive_operation(param):
    # Heavy computation
    return result
```

**Benefits**:
- Eliminates code duplication across services
- Standardizes database connection handling
- Centralizes error handling patterns
- Improves maintainability and testability

---

## 🔧 Development Workflow

### Local Development Setup

1. **Clone repository**:
   ```bash
   git clone git@gitlab.jclee.me:jclee/blacklist.git
   cd blacklist
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start services**:
   ```bash
   make dev
   ```

4. **Verify deployment**:
   ```bash
   curl http://localhost:2542/health
   make health
   ```

### Adding New Features

#### 1. Database Changes

**Process**:
- Create new migration in `postgres/migrations/V00N__description.sql`
- Use idempotent patterns: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- Test locally: `make restart` (migrations run automatically)
- Verify: `make db-shell` → `\dt` and `\d table_name`

**Migration Naming Convention**:
- Format: `V###__description.sql`
- Examples: `V001__init_schema.sql`, `V002__secure_credentials.sql`
- Always use ascending numbers

#### 2. API Endpoints

**Steps**:
1. Add route in appropriate blueprint file (`api/` or `web/`)
2. Implement service logic in `app/core/services/`
3. Add tests in `tests/integration/api/`
4. Apply rate limiting: `@app.limiter.limit("10 per minute")`
5. Add CSRF protection for POST/PUT/DELETE

**Example**:
```python
# app/core/routes/api/ip_management_api.py
@ip_management_bp.route('/api/blacklist/check', methods=['GET'])
@app.limiter.limit("50 per minute")
def check_ip():
    # Implementation
    pass
```

#### 3. Collection Modules

**Core Collection Logic** (`collector/core/` - 138.8 KB):
- `regtech_collector.py` (44.7 KB) - REGTECH API client, two-stage auth
- `multi_source_collector.py` (27.2 KB) - Multi-source aggregation
- `database.py` (20.4 KB) - DB operations with retry logic
- `policy_monitor.py` (19.0 KB) - Policy change detection
- `data_quality_manager.py` (16.7 KB) - Data validation, duplicate detection
- `rate_limiter.py` (10.9 KB) - Token bucket algorithm, API compliance

**Adding New Data Source**:
1. Create collector in `collector/core/`
2. Implement base collector interface (see `regtech_collector.py` pattern)
3. Add authentication logic
4. Register in `monitoring_scheduler.py` CollectorScheduler
5. Add configuration to `collection_credentials` table
6. Add tests in `tests/unit/collectors/`

**Rate Limiting**: All collectors use `collector/core/rate_limiter.py` for API compliance

#### 4. Security Considerations

**Required**:
- All POST/PUT/DELETE endpoints require CSRF tokens (Flask-WTF)
- Apply rate limits to prevent abuse
- Validate all user input with `validators.py`
- Use parameterized queries (SQLAlchemy ORM prevents SQL injection)
- Store credentials encrypted via `secure_credential_service`

**Security Headers** (automatically applied):
```python
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

### Testing

**Pytest Configuration** (`pytest.ini`):
- Coverage requirement: 80%+
- Test markers: `unit`, `integration`, `e2e`, `slow`, `db`, `security`, `api`, `cache`
- Coverage reports: `htmlcov/`, `coverage.xml`

**Test Execution**:
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=core --cov-report=html

# By marker
python -m pytest -m unit              # Unit tests only
python -m pytest -m integration       # Integration tests
python -m pytest -m security          # Security tests (CSRF, rate limiting)
python -m pytest -m db                # Database tests
python -m pytest -m api               # API endpoint tests
python -m pytest -m cache             # Redis cache tests
python -m pytest -m slow              # Long-running tests

# Single test file
python -m pytest tests/unit/test_database.py -v

# Parallel execution (faster)
python -m pytest -n auto
```

**Usage Examples**:
```bash
# Run only fast unit tests
python -m pytest -m "unit and not slow" -v

# Run database and API tests together
python -m pytest -m "db or api" -v

# Exclude slow tests
python -m pytest -m "not slow" -v
```

---

## 🚀 Deployment & CI/CD

### Air-Gapped Deployment Model

**Environment**: Air-gapped (offline deployment)
**Workflow**: Build → Package → Transfer → Load → Deploy

**Key Principle**: NO automatic deployment. Build artifacts (Docker images) are packaged as .tar.gz files, physically transferred to air-gapped servers, then manually loaded and deployed.

### GitLab CI/CD Pipeline

**Status**: ✅ Active (GitLab only, no GitHub Actions)
**Pipeline**: `.gitlab-ci.yml`
**Registry**: registry.jclee.me (GitLab Container Registry)
**Pipeline URL**: https://gitlab.jclee.me/jclee/blacklist/-/pipelines

**Pipeline Stages**:
1. **Validate** - Environment checks
2. **Security** - Python (safety) + JavaScript (npm audit) + pytest
   - Blocks pipeline on **critical** vulnerabilities
   - Coverage reports (Cobertura format)
3. **Build** - Parallel Docker builds for all 5 containers
   - 20m timeout with retry (max 2)
   - BuildKit optimization (`DOCKER_BUILDKIT=1`)
   - Push to GitLab Container Registry
4. **Cleanup** - Registry maintenance (manual)

**Auto-triggers**:
- Push to `main` or `master` branch
- Merge request events
- Manual pipeline runs (GitLab UI)

**Key Features**:
- ✅ Air-gapped deployment (build → package → transfer → load)
- ✅ Security blocking on critical vulnerabilities
- ✅ Parallel container builds (5 simultaneous)
- ✅ Retry logic for transient failures
- ❌ No automatic deployment (manual offline transfer required)

### Quick Deployment Steps

**Step 1: Trigger Build**
```bash
git add -A
git commit -m "feat: update application"
git push origin main  # Auto-triggers GitLab CI/CD
```

**Step 2: Package Images**
```bash
# After build succeeds
./scripts/package-single-image.sh blacklist-app
# Or package all: ./scripts/package-all-sequential.sh
```

**Step 3: Transfer to Air-Gapped Server**
```bash
# Physical media (USB/external HDD)
cp dist/images/*.tar.gz /media/usb/

# Or secure file transfer (if temporary connection allowed)
scp dist/images/*.tar.gz airgap-server:/opt/blacklist/images/
```

**Step 4: Load & Deploy on Air-Gapped Server**
```bash
# Load images
cd /opt/blacklist/images
for f in *.tar.gz; do gunzip -c "$f" | docker load; done

# Deploy
cd /opt/blacklist
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose ps
curl http://localhost:2542/health
```

**For detailed deployment guide**: See `docs/DEPLOYMENT-AIRGAP.md`

---

## 🔍 Common Debugging Workflows

### 1. Container Won't Start

```bash
# Check status and logs
docker-compose ps
docker-compose logs --tail=50 blacklist-app

# Check port conflicts
netstat -tulpn | grep -E '2542|5432|6379|8545'

# Test database connectivity
docker exec blacklist-postgres pg_isready -U postgres
```

### 2. Database Connection Failures

```bash
# Verify PostgreSQL is running
docker-compose ps blacklist-postgres

# Test connection from app container
docker exec blacklist-app psql -h blacklist-postgres -U postgres -d blacklist -c "SELECT 1"

# Check connection pool status
curl http://localhost:2542/api/monitoring/metrics | grep pool
```

### 3. Collection Service Not Running

```bash
# Check collector status and logs
docker-compose ps blacklist-collector
docker logs blacklist-collector --tail=100

# Check collector health
curl http://localhost:8545/health

# Manually trigger collection
curl -X POST http://localhost:2542/api/collection/regtech/trigger \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-11-01", "end_date": "2025-11-10"}'
```

### 4. Rate Limiting Issues

```bash
# Check Redis connection
docker exec blacklist-redis redis-cli ping

# View rate limit keys
docker exec blacklist-redis redis-cli keys "LIMITER*"

# Clear rate limits (development only)
docker exec blacklist-redis redis-cli FLUSHDB
```

---

## ⚠️ Common Pitfalls & Tips

### Development

1. **Database Schema Changes**
   - ❌ DON'T modify schema directly in database
   - ✅ DO create idempotent migration in `postgres/migrations/V00N__*.sql`
   - ✅ Test with `make restart` (migrations run automatically)

2. **Service Layer Changes**
   - ❌ DON'T create duplicate service classes
   - ✅ DO check if existing service can be extended
   - ✅ Use singleton pattern via `app.extensions` dictionary

3. **Testing**
   - ❌ DON'T skip pytest markers (coverage won't track correctly)
   - ✅ DO use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
   - ✅ Maintain 80%+ coverage (enforced by CI/CD)

4. **CSRF Protection**
   - ❌ DON'T disable CSRF globally
   - ✅ DO exempt specific blueprints: `csrf.exempt(blueprint)`
   - ✅ Include CSRF token in forms/headers for POST/PUT/DELETE

5. **Rate Limiting**
   - ❌ DON'T bypass rate limits in production
   - ✅ DO use `FLASK_ENV=development` to disable in local dev
   - ✅ Adjust per-endpoint limits with `@app.limiter.limit("N per minute")`

### Deployment

1. **Air-Gapped Deployment**
   - ❌ DON'T assume automatic deployment after CI/CD build
   - ✅ DO manually package images after build succeeds
   - ✅ Verify checksums after transferring to air-gapped server

2. **Container Restart**
   - ❌ DON'T worry about losing database schema (auto-migration handles it)
   - ✅ DO check logs after restart: `docker logs blacklist-postgres | grep Migration`

3. **Credentials**
   - ❌ DON'T store credentials in code or docker-compose.yml
   - ✅ DO use encrypted storage via `SecureCredentialService`
   - ✅ Manage via UI: `https://blacklist.nxtd.co.kr/settings`

---

## 📝 Code Style & Best Practices

### Python

- **Style**: Follow PEP 8
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style docstrings for public functions/classes
- **Imports**: Organize as stdlib, third-party, local
- **Line Length**: 100 characters (not strict 79)

**Example**:
```python
from typing import Optional, List
import logging

def check_ip_status(ip_address: str) -> Optional[dict]:
    """Check if IP is blocked or whitelisted.

    Args:
        ip_address: IP address to check

    Returns:
        Status dict with 'is_blocked' and 'reason' keys, or None if not found
    """
    pass
```

### Testing

- **Coverage**: 80%+ minimum (enforced by pytest)
- **Markers**: Use pytest markers for test categorization
- **Fixtures**: Prefer fixtures over setup/teardown
- **Assertions**: Use descriptive assertion messages

### Security

- **Credentials**: No hardcoded credentials (use environment variables)
- **SQL**: Use SQLAlchemy ORM (prevents SQL injection)
- **Input Validation**: Validate all user input with `validators.py`
- **Encryption**: Use `secure_credential_service` for sensitive data

### Database

- **Migrations**: Idempotent with `IF NOT EXISTS` patterns
- **Indexes**: Add indexes for frequently queried columns
- **Constraints**: Use database constraints (UNIQUE, NOT NULL, FOREIGN KEY)

---

## 🌐 Inter-Session Communication (TS IPC)

**NEW**: The project now supports inter-session communication via TS (Tmux Session Manager) IPC system.

**Quick Commands** (from global config):
```bash
# Send message to Claude in specific session
ipc blacklist "review this code"
ts ipc chat blacklist "analyze this feature"

# Broadcast to all sessions
ts ipc broadcast "✅ Build complete"
```

**Documentation**: See `~/.claude/docs/TS-IPC-COMMAND-GUIDE.md`

---

## 📚 Additional Resources

**Documentation**:
- `README.md` - Comprehensive project overview
- `CLAUDE.md` - AI development guide (this file)
- `docs/DEPLOYMENT-AIRGAP.md` - Air-gapped deployment guide
- `docs/CICD-TROUBLESHOOTING.md` - CI/CD troubleshooting
- `docs/TESTING-GUIDE.md` - Comprehensive testing guide
- `docs/API-REFERENCE.md` - Complete API documentation
- `CONFIGURATION-GUIDE.md` - Configuration file locations
- `CHANGELOG.md` - Version history
- `postgres/SCHEMA-DEPENDENCY.md` - Database schema documentation
- `collector/README.md` - Collection service details
- `collector/RATE-LIMITING.md` - Rate limiting documentation

**Production URLs**:
- Application: https://blacklist.nxtd.co.kr
- Health Check: https://blacklist.nxtd.co.kr/health
- Collection Panel: https://blacklist.nxtd.co.kr/collection-panel

**Infrastructure**:
- Container Registry: https://registry.jclee.me
- GitLab: https://gitlab.jclee.me/jclee/blacklist
- GitLab CI/CD: https://gitlab.jclee.me/jclee/blacklist/-/pipelines

---

**Version**: 3.4.0
**Last Updated**: 2025-11-12 (Route structure updated, condensed for AI performance)
**Maintainer**: jclee
