# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Project Overview

**REGTECH Blacklist Intelligence Platform** - A Flask-based threat intelligence platform for collecting, managing, and analyzing IP blacklist data from Korean Financial Security Institute (REGTECH). Features automated collection pipelines, real-time monitoring, whitelist/blacklist management, and production deployment with Portainer API control.

**Architecture**: Microservices (5 independent containers)
- `blacklist-app` - Flask application (Port 2542)
- `blacklist-collector` - REGTECH collection service (Port 8545)
- `blacklist-postgres` - PostgreSQL 15 database (auto-migration on restart)
- `blacklist-redis` - Redis 7 cache
- `blacklist-frontend` - Next.js frontend (Port 2543)

**Repository**: Migrated to GitLab (https://gitlab.jclee.me/jclee/blacklist)

---

## ⚡ Essential Commands

### Development

```bash
# Start development environment with live reload
make dev

# Start production environment
make prod

# Build all Docker images
make build

# Rebuild from scratch (no cache)
make rebuild

# View logs
make logs              # All services
make logs-app          # Flask app only
make logs-collector    # Collector only
make logs-db           # PostgreSQL only

# Stop all services
make down

# Restart services
make restart

# Health check
make health

# Show all available commands
make help
```

### Testing

```bash
# Run comprehensive test suite
make test

# Run specific test types
python -m pytest tests/ -v                    # All pytest tests
python -m pytest tests/unit/ -v               # Unit tests only
python -m pytest tests/integration/ -v        # Integration tests
python -m pytest tests/security/ -v           # Security tests
python -m pytest -m "db" -v                   # Database tests
python -m pytest -m "api" -v                  # API tests

# Test with coverage
python -m pytest --cov=core --cov-report=html

# Manual whitelist/blacklist tests
./tests/test_whitelist.sh
```

### Database Management

```bash
# Connect to PostgreSQL
make db-shell

# Backup database
make db-backup

# Restore from backup
make db-restore BACKUP_FILE=backups/blacklist_20251107_120000.sql

# Container shell access
make shell-app         # Flask app container
make shell-db          # PostgreSQL container
```

### Image Packaging (Offline Deployment)

```bash
# Package single image (recommended - stable and fast)
./scripts/package-single-image.sh blacklist-app

# List available services
./scripts/package-single-image.sh

# Package all images sequentially
./scripts/package-all-sequential.sh

# View packaged images
ls -lh dist/images/
```

### Deployment

```bash
# Deploy to production (build + start + health check)
make deploy

# CI/CD build
make ci-build

# View detailed status
make status

# Project information
make info
```

---

## 🏗️ Architecture & Key Patterns

### Auto-Migrating Database System

**Critical Pattern**: PostgreSQL runs migrations on EVERY container restart (not just first time).

**Implementation**:
- **Custom Entrypoint**: `postgres/docker-entrypoint-custom.sh` wraps official postgres entrypoint
- **Migration Directory**: `postgres/migrations/*.sql` mounted read-only into container
- **Execution Flow**:
  1. Start postgres in background
  2. Wait for readiness (30 attempts, 1s each)
  3. Run all `V*.sql` files in order
  4. Shutdown background instance
  5. Start postgres normally via official entrypoint

**Idempotent Migrations**: All SQL uses `IF NOT EXISTS` / `IF EXISTS` patterns.

**Example Migration**:
```sql
-- V001__init_schema.sql
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    ...
);

-- V002__secure_credentials.sql
ALTER TABLE collection_credentials
ADD COLUMN IF NOT EXISTS is_encrypted BOOLEAN DEFAULT FALSE;
```

**Why This Pattern**: Ensures schema consistency across container restarts, prevents "DB schema lost on restart" issues.

### Priority-Based IP Filtering

**Whitelist → Blacklist Logic**:
1. Check whitelist table first (VIP/Admin protection)
2. If found → ALLOW (return immediately)
3. If not found → Check blacklist table
4. If found in blacklist → BLOCK

**Implementation**: `app/core/services/database_service.py`

### Microservices Communication

**Network**: `blacklist-network` (bridge driver)

**Service Discovery**:
- App → Postgres: `blacklist-postgres:5432`
- App → Redis: `blacklist-redis:6379`
- Frontend → App: `blacklist-app:2542`
- Collector → Postgres/Redis: Internal hostnames

**External Access**: Only frontend exposed via Traefik reverse proxy

---

## 📁 Directory Structure

```
blacklist/
├── app/                          # Flask application
│   ├── core/
│   │   ├── app.py                # Flask factory with CSRF/rate limiting
│   │   ├── routes/               # API endpoints by feature
│   │   ├── services/             # Business logic (database, redis, credentials)
│   │   └── models/               # SQLAlchemy models
│   ├── templates/                # Jinja2 templates
│   └── Dockerfile                # Multi-stage build with docs
│
├── collector/                    # REGTECH/SECUDIUM data collection
│   ├── monitoring_scheduler.py   # Auto-collection orchestrator
│   ├── collector/                # Collection modules
│   ├── api/health_check.py       # Health endpoint (Port 8545)
│   └── Dockerfile                # Multi-stage build with docs
│
├── frontend/                     # Next.js React frontend
│   ├── app/                      # Next.js 13+ app directory
│   ├── components/               # React components
│   └── Dockerfile                # Multi-stage build with docs
│
├── postgres/                     # PostgreSQL with auto-migrations
│   ├── Dockerfile                # Installs psql + dependencies
│   ├── docker-entrypoint-custom.sh  # Migration wrapper
│   ├── migrations/               # Idempotent SQL migrations
│   │   ├── V001__init_schema.sql
│   │   └── V002__secure_credentials.sql
│   └── SCHEMA-DEPENDENCY.md      # Schema documentation
│
├── redis/
│   └── Dockerfile                # Redis 7 with persistence
│
├── scripts/                      # Automation scripts
│   ├── package-single-image.sh   # Single image packaging (recommended)
│   ├── package-all-sequential.sh # Sequential all images
│   ├── package-images.sh         # Full automation with manifest
│   ├── comprehensive_test.py     # Test runner
│   └── (FortiManager scripts)    # FortiGate integration tools
│
├── tests/                        # Pytest test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── security/                 # CSRF, rate limiting tests
│   ├── conftest.py               # Fixtures
│   └── pytest.ini                # 80%+ coverage requirement
│
├── dist/images/                  # Packaged Docker images (gitignored)
├── docker-compose.yml            # Base orchestration
├── Makefile                      # Development commands
└── IMAGE-PACKAGING-COMPLETE.md   # Packaging documentation
```

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

1. **Database Changes**:
   - Create new migration in `postgres/migrations/V00N__description.sql`
   - Use idempotent patterns: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
   - Test locally: `make restart` (migrations run automatically)
   - Verify: `make db-shell` → `\dt` and `\d table_name`

2. **API Endpoints**:
   - Add route in `app/core/routes/`
   - Implement service in `app/core/services/`
   - Add tests in `tests/integration/api/`
   - Apply rate limiting: `@app.limiter.limit("10 per minute")`
   - Add CSRF protection for POST/PUT/DELETE

3. **Security Considerations**:
   - All POST/PUT/DELETE endpoints require CSRF tokens (Flask-WTF)
   - Apply rate limits to prevent abuse
   - Validate all user input
   - Use parameterized queries (SQLAlchemy ORM prevents SQL injection)
   - Store credentials encrypted via `secure_credential_service`

### Running Tests

**Pytest Configuration** (`pytest.ini`):
- Coverage requirement: 80%+
- Test markers: `unit`, `integration`, `e2e`, `db`, `security`, `api`, `cache`
- Coverage reports: `htmlcov/`, `coverage.xml`

**Test Execution**:
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=core --cov-report=html

# Specific categories
python -m pytest -m unit              # Unit tests
python -m pytest -m integration       # Integration tests
python -m pytest -m security          # Security tests (CSRF, rate limiting)

# Single test file
python -m pytest tests/unit/test_database.py -v

# Run tests in parallel (faster)
python -m pytest -n auto
```

---

## 🚀 Deployment & CI/CD

### GitHub Actions Pipeline

**Workflow**: `.github/workflows/docker-build-portainer-deploy.yml`

**Pipeline Stages**:
1. **Security Scan** - Python (safety) + JavaScript (npm audit)
2. **Build Images** - Multi-stage Docker builds for all containers
3. **Push to Registry** - `registry.jclee.me`
4. **Deploy via Portainer** - API-controlled deployment
5. **Health Check** - Verify deployment success
6. **Rollback** - Auto-rollback on failure

**Triggers**:
- Push to `master` branch
- Changes in: `app/`, `collector/`, `postgres/`, `redis/`, `frontend/`, `Dockerfile*`, `docker-compose.yml`
- Manual dispatch: `workflow_dispatch`

### Offline Deployment (Image Packaging)

**Use Case**: Deploy to servers without internet access or air-gapped environments.

**Packaging Commands**:
```bash
# Single image (recommended - stable, 1-7 min)
./scripts/package-single-image.sh blacklist-app

# All images sequentially
./scripts/package-all-sequential.sh

# Check packaged files
ls -lh dist/images/
```

**Deployment Workflow**:
```bash
# 1. Package on dev server
./scripts/package-single-image.sh blacklist-app

# 2. Transfer to production
scp dist/images/*.tar.gz user@prod-server:/opt/blacklist/

# 3. Load on production
ssh prod-server
cd /opt/blacklist
for f in *.tar.gz; do
    gunzip -c "$f" | docker load
done

# 4. Start services
docker-compose up -d
```

**Compression Efficiency**: ~66% reduction (2.4GB → 815MB total)

### Environment Variables

**Required**:
```bash
# Database
POSTGRES_PASSWORD=<secure_password>

# REGTECH Authentication
REGTECH_ID=<regtech_username>
REGTECH_PW=<regtech_password>
REGTECH_BASE_URL=https://regtech.fsec.or.kr

# Flask Security
FLASK_SECRET_KEY=<generated_with_secrets.token_hex(32)>

# Redis
REDIS_HOST=blacklist-redis
REDIS_PORT=6379
```

**Generate Secret Key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📚 API Reference

### Core Endpoints

#### Health & Monitoring
```bash
GET  /health                          # System health check
GET  /api/stats                       # System statistics
GET  /api/monitoring/metrics          # Prometheus metrics
GET  /api/monitoring/dashboard        # Dashboard data
```

#### Blacklist Management
```bash
GET  /api/blacklist/check?ip=1.2.3.4  # Check IP status (whitelist priority)
POST /api/blacklist/check             # Check IP (JSON body)
POST /api/blacklist/manual-add        # Add IP to blacklist
GET  /api/blacklist/list              # Paginated blacklist
GET  /api/blacklist/json              # Full blacklist (JSON)
```

#### Whitelist Management (VIP Protection)
```bash
POST /api/whitelist/manual-add        # Add VIP/Admin IP
GET  /api/whitelist/list              # List whitelisted IPs
```

#### Collection Management
```bash
GET  /api/collection/status           # Collection status
GET  /api/collection/history          # Collection history
POST /api/collection/regtech/trigger  # Trigger manual collection
```

### Rate Limiting

**Global Limits**:
- 200 requests per day
- 50 requests per hour

**Exemptions**:
- Health checks (`/health`, `/metrics`)
- Internal container traffic (172.x.x.x)
- Localhost requests

**Custom Limits**:
```python
@app.route('/api/sensitive')
@app.limiter.limit("10 per minute")
def sensitive_endpoint():
    pass
```

---

## 🔒 Security Features

### CSRF & Rate Limiting

**CSRF Protection**:
- Enabled via Flask-WTF (`CSRFProtect`)
- All POST/PUT/DELETE require CSRF token
- Exemptions: Health checks, metrics endpoints

**Rate Limiting**:
- Redis-backed distributed rate limiting
- Prevents brute force attacks
- Returns `X-RateLimit-*` headers

**Security Headers**:
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`

### Database Schema

**Core Tables**:
- `blacklist_ips` - IP blacklist with country, detection dates
- `whitelist_ips` - VIP/Admin IP protection (priority over blacklist)
- `collection_credentials` - Encrypted authentication storage (AES-256)
- `credential_audit_log` - Credential change tracking
- `collection_logs` - Collection history and status

**Security Views**:
- `credential_security_status` - Expiry monitoring and status

---

## 🛠️ Troubleshooting

### Container Not Starting
```bash
# Check container logs
docker logs blacklist-app
docker logs blacklist-postgres

# Check health status
make health

# Restart services
make restart
```

### Database Migration Issues
```bash
# Check migration logs
docker logs blacklist-postgres | grep "Migration"

# Verify migrations ran
make db-shell
# Then: SELECT * FROM schema_migrations;

# Force re-run migrations
make down
make up
```

### Collection Not Working
```bash
# Check collector logs
make logs-collector

# Verify credentials
# Access settings UI: https://blacklist.jclee.me/settings

# Trigger manual collection
curl -X POST https://blacklist.jclee.me/collection-panel/trigger \
  -H "Content-Type: application/json" \
  -d '{"source": "regtech", "start_date": "2025-01-01", "end_date": "2025-01-10"}'
```

### Rate Limit Errors
```bash
# Check Redis connection
docker exec blacklist-redis redis-cli ping

# Verify rate limit storage
docker exec blacklist-redis redis-cli keys "LIMITER*"

# Temporarily disable (development only)
# Set FLASK_ENV=development in .env
```

---

## 📝 Code Style & Best Practices

- **Python**: Follow PEP 8, use type hints for all functions
- **Docstrings**: Required for all public functions/classes
- **Testing**: 80%+ coverage minimum
- **Security**: No hardcoded credentials (use environment variables)
- **Database**: Use idempotent migrations with `IF NOT EXISTS` patterns
- **API**: Apply rate limiting and CSRF protection appropriately

---

## 📚 Additional Resources

**Documentation**:
- `README.md` - Comprehensive project overview
- `CHANGELOG.md` - Version history
- `IMAGE-PACKAGING-COMPLETE.md` - Offline deployment guide
- `scripts/PACKAGING-GUIDE.md` - Detailed packaging instructions
- `postgres/SCHEMA-DEPENDENCY.md` - Database schema documentation
- `collector/README.md` - Collection service details
- `tests/INTEGRATION_TEST_REPORT_*.md` - Test reports

**Production URLs**:
- Application: https://blacklist.jclee.me
- Health Check: https://blacklist.jclee.me/health
- Collection Panel: https://blacklist.jclee.me/collection-panel

**Infrastructure**:
- Container Registry: https://registry.jclee.me
- Portainer: https://portainer.jclee.me
- GitLab: https://gitlab.jclee.me/jclee/blacklist

---

**Version**: 3.3.9
**Last Updated**: 2025-11-08
**Maintainer**: jclee
