# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Project Overview

**REGTECH Blacklist Intelligence Platform** - A Flask-based threat intelligence platform for collecting, managing, and analyzing IP blacklist data from Korean Financial Security Institute (REGTECH). Features automated collection pipelines, real-time monitoring, whitelist/blacklist management, and **air-gapped deployment** with GitLab CI/CD build automation.

**Architecture**: Microservices (5 independent containers)
- `blacklist-app` - Flask application (Port 2542)
- `blacklist-collector` - REGTECH collection service (Port 8545)
- `blacklist-postgres` - PostgreSQL 15 database (auto-migration on restart)
- `blacklist-redis` - Redis 7 cache
- `blacklist-frontend` - Next.js frontend (Port 2543)

**Repository**: GitLab (https://gitlab.jclee.me/jclee/blacklist)

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

### Common Utilities (NEW - 2025-11-08)

**Location**: `app/core/utils/`

**Database Utilities** (`db_utils.py`):
- Context manager for database connections
- Query execution helpers (`execute_query`, `execute_write`)
- Table existence checker
- Centralized DB configuration

**Cache Utilities** (`cache_utils.py`):
- `CacheManager` class for Redis operations
- `@cached` decorator for function result caching
- Pattern-based cache clearing
- JSON serialization/deserialization

**Benefits**:
- Eliminates code duplication across services
- Standardizes database connection handling
- Centralizes error handling patterns
- Improves maintainability and testability

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

### Flask Application Factory Pattern

**Location**: `app/core/app.py::create_app()`

**Key Components**:
- CSRF Protection via Flask-WTF
- Redis-backed rate limiting (Flask-Limiter)
- Security headers middleware
- Structured logging with correlation IDs
- Blueprint-based route organization

**Critical Services** (Singleton Pattern):
- `DatabaseService` - Connection pooling, whitelist priority checks
- `SecureCredentialService` - AES-256 encrypted credential storage
- `BlacklistService` - IP filtering with Redis caching

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

### Microservices Communication

**Network**: `blacklist-network` (bridge driver)

**Service Discovery** (Docker DNS):
- App → Postgres: `blacklist-postgres:5432`
- App → Redis: `blacklist-redis:6379`
- Frontend → App: `blacklist-app:2542`
- Collector → Postgres/Redis: Internal hostnames

**External Access**: Only frontend exposed via Traefik reverse proxy

**Health Check Chain**:
```
Traefik → Frontend :2543 → App :2542 → Postgres :5432
                                      → Redis :6379
                                      → Collector :8545
```

---

## 📁 Directory Structure

```
blacklist/
├── app/                          # Flask application
│   ├── core/
│   │   ├── app.py                # Flask factory with CSRF/rate limiting
│   │   ├── routes/               # API endpoints by feature
│   │   │   ├── api/              # RESTful API routes
│   │   │   │   ├── core_api.py   # Health, stats, monitoring
│   │   │   │   ├── ip_management_api.py  # Blacklist/whitelist
│   │   │   │   ├── collection_api.py     # Collection triggers
│   │   │   │   └── system_api.py         # System management
│   │   │   └── web/              # Web UI routes
│   │   ├── services/             # Business logic (database, redis, credentials)
│   │   │   ├── database_service.py       # Core DB operations
│   │   │   ├── secure_credential_service.py  # Encrypted credentials
│   │   │   ├── blacklist_service.py      # IP filtering logic
│   │   │   └── collection/               # Collection orchestration
│   │   ├── collectors/           # Data collection modules
│   │   │   ├── unified_collector.py  # Multi-source collector
│   │   │   └── regtech_auth.py       # REGTECH authentication
│   │   └── models/               # SQLAlchemy models
│   ├── templates/                # Jinja2 templates
│   └── Dockerfile                # Multi-stage build with docs
│
├── collector/                    # REGTECH/SECUDIUM data collection
│   ├── monitoring_scheduler.py   # Auto-collection orchestrator
│   ├── collector/                # Collection modules
│   │   ├── monitoring_scheduler.py  # Cron-based scheduler
│   │   └── health_server.py         # Health endpoint
│   ├── core/                     # Core collection logic
│   │   ├── regtech_collector.py     # REGTECH API client
│   │   ├── multi_source_collector.py  # Multi-source aggregation
│   │   └── rate_limiter.py          # API rate limiting
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
│   ├── comprehensive_test.py     # Test runner
│   └── (FortiManager scripts)    # FortiGate integration tools
│
├── tests/                        # Pytest test suite
│   ├── unit/                     # Unit tests
│   │   ├── services/             # Service layer tests
│   │   ├── collectors/           # Collector tests
│   │   └── utils/                # Utility tests
│   ├── integration/              # Integration tests
│   │   ├── api/                  # API endpoint tests
│   │   └── services/             # Service integration tests
│   ├── security/                 # CSRF, rate limiting tests
│   ├── conftest.py               # Pytest fixtures
│   └── pytest.ini                # 80%+ coverage requirement
│
├── dist/images/                  # Packaged Docker images (gitignored)
├── docker-compose.yml            # Base orchestration
├── docker-compose.prod.yml       # Production overrides
├── docker-compose.dev.yml        # Development overrides
├── Makefile                      # Development commands
└── .gitlab-ci.yml                # GitLab CI/CD pipeline
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

**Blueprint Organization**:
```python
# app/core/routes/api/
core_api.py          # Health, stats, monitoring
ip_management_api.py # Blacklist/whitelist operations
collection_api.py    # Collection triggers
system_api.py        # System management
```

**Steps**:
1. Add route in appropriate blueprint file
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

**Adding New Data Source**:
1. Create collector in `collector/core/` or `app/core/collectors/`
2. Implement base collector interface
3. Add authentication logic
4. Register in `unified_collector.py`
5. Add tests in `tests/unit/collectors/`

**Rate Limiting**: Use `collector/core/rate_limiter.py` for API compliance

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
python -m pytest -m db                # Database tests

# Single test file
python -m pytest tests/unit/test_database.py -v

# Run tests in parallel (faster)
python -m pytest -n auto
```

**Test Fixtures** (`tests/conftest.py`):
- `app` - Flask application instance
- `client` - Flask test client
- `db_session` - Database session
- `redis_client` - Redis client
- `mock_credentials` - Mock credential data

---

## 🚀 Deployment & CI/CD

### 🔒 Air-Gapped Deployment Model (2025-11-09)

**Environment**: Air-gapped (offline deployment)
**Workflow**: Build → Package → Transfer → Load → Deploy

### GitLab CI/CD Pipeline (Air-Gapped Build)

**Workflow**: `.gitlab-ci.yml`

**Pipeline Visualization**:
```
┌─────────────┐
│  VALIDATE   │ ← Environment checks
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────┐
│  SECURITY (Parallel)                            │
├─────────────┬─────────────┬─────────────────────┤
│ Python Scan │  JS Scan    │  Run Tests         │
│ (safety)    │ (npm audit) │ (pytest + coverage)│
└──────┬──────┴──────┬──────┴──────┬──────────────┘
       │             │             │
       └──────┬──────┴──────┬──────┘
              │             │
       ┌──────▼─────────────▼──────────────────────┐
       │  BUILD (Parallel - 5 containers)          │
       ├──────┬──────┬──────┬──────┬───────────────┤
       │ Post │ Redis│ Coll │ App  │ Frontend      │
       │ gres │      │ ector│      │               │
       └──┬───┴───┬──┴───┬──┴───┬──┴───┬───────────┘
          │       │      │      │      │
          └───────┴──────┴──────┴──────┘
                      │
               ┌──────▼──────┐
               │ PUSH IMAGES │
               │  (Registry) │
               └──────┬──────┘
                      │
               ┌──────▼──────┐
               │   CLEANUP   │
               │  (Manual)   │
               └─────────────┘

⚠️  NO AUTOMATIC DEPLOYMENT
Manual offline transfer required (see below)
```

**Pipeline Stages**:
1. **Validate** - Environment checks
2. **Security** - Python (safety) + JavaScript (npm audit) + pytest
   - Blocks pipeline on **critical** vulnerabilities
   - jq-based severity filtering
   - Coverage reports (Cobertura format)
3. **Build** - Parallel Docker builds for all 5 containers
   - 20m timeout with retry (max 2)
   - Docker daemon readiness check
   - BuildKit optimization (`DOCKER_BUILDKIT=1`)
   - Cache from previous builds
   - Push to GitLab Container Registry
4. **Cleanup** - Registry maintenance (manual)
   - Old image cleanup
   - Scheduled cleanup jobs

**Triggers**:
- Auto: Push to `main`/`master` branch
- Auto: Merge request events
- Manual: Anytime via GitLab UI

**Key Features**:
- ✅ Parallel builds (5 containers simultaneously)
- ✅ Build cache optimization with `DOCKER_BUILDKIT=1`
- ✅ **Critical vulnerability blocking** (pipeline fails on critical CVEs)
- ✅ Automatic registry push
- ✅ No automatic deployment (air-gapped security)

### Air-Gapped Deployment Workflow

**Step 1: Automated Build (Internet-Connected Server)**
```bash
# GitLab CI/CD automatically builds images on git push
git add -A
git commit -m "feat: update application"
git push origin main

# Pipeline runs:
# - Validate environment
# - Security scans (Python/JS)
# - Build 5 containers in parallel
# - Push to registry.jclee.me
```

**Step 2: Package Images (Internet-Connected Server)**
```bash
# Login to build server
ssh builder-server

# Package single image (1-7 minutes)
cd /path/to/blacklist
./scripts/package-single-image.sh blacklist-app

# Or package all images (sequential, 10-15 minutes)
./scripts/package-all-sequential.sh

# Verify packages
ls -lh dist/images/
# Output:
# blacklist-postgres_latest.tar.gz  (185MB)
# blacklist-redis_latest.tar.gz     (28MB)
# blacklist-collector_latest.tar.gz (156MB)
# blacklist-app_latest.tar.gz       (311MB)
# blacklist-frontend_latest.tar.gz  (135MB)
# Total: ~815MB (66% compression from 2.4GB)
```

**Step 3: Transfer to Air-Gapped Server**
```bash
# Option A: Physical media (USB/external HDD)
cp dist/images/*.tar.gz /media/usb/
# → Physically transport to air-gapped server

# Option B: Secure file transfer (if temporary connection allowed)
scp dist/images/*.tar.gz airgap-server:/opt/blacklist/images/
```

**Step 4: Load Images (Air-Gapped Server)**
```bash
# SSH to air-gapped server
ssh airgap-server

cd /opt/blacklist/images

# Load all images
for f in *.tar.gz; do
    echo "[LOAD] Loading $f..."
    gunzip -c "$f" | docker load
done

# Verify loaded images
docker images | grep blacklist
```

**Step 5: Deploy Services (Air-Gapped Server)**
```bash
cd /opt/blacklist

# Pull is not needed (images already loaded locally)
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Health check
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:2542/health
```

**Step 6: Verify Deployment**
```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Test database
docker exec blacklist-postgres psql -U postgres -d blacklist -c "\dt"

# Test API
curl http://localhost:2542/api/stats | jq

# Check logs
docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

**Build Stability Enhancements**:

**Security Stage Resilience**:
- Python scan: 3-attempt retry for `pip install safety` (5s delay)
- JavaScript scan: 3-attempt retry for `npm audit` (5s delay)
- Test stage: 3-attempt retry for `pip install -r requirements.txt` (5s delay)
- Job-level retry: max 2 retries on `runner_system_failure`, `stuck_or_timeout_failure`, `script_failure`

**Docker Build Resilience**:
- App Dockerfile: 3-attempt retry for `pip install` (10s delay between attempts)
- Frontend Dockerfile: 3-attempt retry for `npm ci` in both deps and builder stages (10s delay)
- Prevents transient network failures from failing builds

**Failure Recovery**:
- All stages gracefully degrade on network issues
- Retries use exponential backoff to avoid overwhelming services
- Critical failures trigger pipeline failure (security vulnerabilities)
- Non-critical failures log warnings but allow pipeline to continue

---

### CI/CD Common Operations (Air-Gapped)

#### 1. Trigger Build Pipeline

```bash
# Via GitLab UI
# 1. Navigate to: https://gitlab.jclee.me/jclee/blacklist/-/pipelines
# 2. Click "Run Pipeline" button
# 3. Select branch: main/master
# 4. Click "Run pipeline"

# Via Git push (automatic trigger)
git add -A
git commit -m "feat: update application"
git push origin main
```

#### 2. Monitor Build Progress

```bash
# Real-time pipeline monitoring
https://gitlab.jclee.me/jclee/blacklist/-/pipelines

# View specific job logs
https://gitlab.jclee.me/jclee/blacklist/-/jobs/<job_id>

# Check build artifacts
https://gitlab.jclee.me/jclee/blacklist/-/jobs/<job_id>/artifacts
```

#### 3. Package and Transfer Images

```bash
# After successful build, package images
ssh builder-server
cd /path/to/blacklist

# Package all images
./scripts/package-all-sequential.sh

# Transfer to air-gapped server
# Option A: USB/external media
cp dist/images/*.tar.gz /media/usb/

# Option B: Temporary secure transfer
scp dist/images/*.tar.gz airgap-server:/opt/blacklist/images/
```

#### 4. Deploy to Air-Gapped Server

```bash
# SSH to air-gapped server
ssh airgap-server
cd /opt/blacklist/images

# Load images
for f in *.tar.gz; do
    gunzip -c "$f" | docker load
done

# Deploy
cd /opt/blacklist
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose ps
curl http://localhost:2542/health
```

#### 5. Rollback on Air-Gapped Server

```bash
# List available images
docker images | grep blacklist

# Tag previous version as latest
docker tag blacklist-app:<previous-commit-sha> blacklist-app:latest
docker tag blacklist-postgres:<previous-commit-sha> blacklist-postgres:latest
# ... repeat for all services

# Restart services
cd /opt/blacklist
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Verify rollback
curl http://localhost:2542/health
```

---

### Environment Variables Setup

**Required GitLab CI/CD Variables** (Settings → CI/CD → Variables):

| Variable | Type | Protected | Masked | Value Example | Purpose |
|----------|------|-----------|--------|---------------|---------|
| `GITLAB_API_TOKEN` | Variable | ✅ | ✅ | `glpat-xxxxxxxxxxxx` | Registry cleanup |
| `POSTGRES_PASSWORD` | Variable | ✅ | ✅ | `<secure-password>` | Database password |
| `FLASK_SECRET_KEY` | Variable | ✅ | ✅ | `<64-char-hex>` | Flask session key |
| `REGTECH_ID` | Variable | ✅ | ❌ | `your-regtech-username` | REGTECH auth |
| `REGTECH_PW` | Variable | ✅ | ✅ | `your-regtech-password` | REGTECH auth |

**Removed Variables** (no longer needed for air-gapped deployment):
- ❌ `SSH_PRIVATE_KEY` - No SSH deployment
- ❌ `SSH_KNOWN_HOSTS` - No SSH deployment
- ❌ `DEPLOY_HOST` - No automatic deployment
- ❌ `DEPLOY_USER` - No automatic deployment
- ❌ `DEV_DEPLOY_HOST` - No automatic deployment

**How to add variables**:
```bash
# Via GitLab UI
# 1. Navigate to: https://gitlab.jclee.me/jclee/blacklist/-/settings/ci_cd
# 2. Expand "Variables" section
# 3. Click "Add variable"
# 4. Fill in key, value, and flags
# 5. Click "Add variable"
```

**Generate Secret Keys**:
```bash
# FLASK_SECRET_KEY (64-character hex)
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### Troubleshooting CI/CD

#### Build Stage Failures

**Problem**: Docker build timeout or failure
```bash
# Symptoms
Error: failed to solve: executor failed running [/bin/sh -c pip install -r requirements.txt]
ERROR: Job failed: exit code 1

# Solutions
1. Check Dockerfile syntax (app/Dockerfile, collector/Dockerfile)
2. Verify requirements.txt has no broken dependencies
3. Increase timeout in .gitlab-ci.yml (current: 20m)
4. Check Docker daemon logs in job output
5. Retry build (automatic retry max 2 times)
```

**Problem**: "No space left on device"
```bash
# Solutions
# 1. SSH to GitLab runner
ssh runner-host

# 2. Clean Docker resources
docker system prune -af --volumes
docker builder prune -af

# 3. Check disk usage
df -h
du -sh /var/lib/docker/*
```

#### Registry/Build Failures

**Problem**: Registry push failure
```bash
# Symptoms
Error: failed to push registry.jclee.me/jclee/blacklist/blacklist-app:latest

# Solutions
1. Check GitLab Container Registry is enabled
2. Verify CI_REGISTRY_PASSWORD is valid
3. Check registry disk space:
   ssh gitlab-server
   df -h | grep registry
4. Check registry logs:
   docker logs gitlab-registry
```

**Problem**: Image packaging failure
```bash
# Symptoms
./scripts/package-single-image.sh fails with "Image not found"

# Solutions
1. Verify images exist in registry:
   docker images | grep blacklist
2. Pull from registry first:
   echo "$CI_REGISTRY_PASSWORD" | docker login registry.jclee.me -u gitlab-ci-token --password-stdin
   docker pull registry.jclee.me/jclee/blacklist/blacklist-app:latest
3. Check dist/images/ directory permissions:
   mkdir -p dist/images
   chmod 755 dist/images
```

#### Air-Gapped Deployment Failures

**Problem**: Image load failure on air-gapped server
```bash
# Symptoms
Error loading image: invalid tar header

# Solutions
1. Verify .tar.gz integrity:
   gunzip -t blacklist-app_latest.tar.gz
2. Check file corruption during transfer:
   md5sum blacklist-app_latest.tar.gz  # Compare with source
3. Re-package image with verification:
   ./scripts/package-single-image.sh blacklist-app
```

**Problem**: Container startup failure after load
```bash
# Symptoms
docker-compose up -d fails with "image not found"

# Solutions
1. List loaded images:
   docker images | grep blacklist
2. Check image tags match docker-compose.yml:
   grep "image:" docker-compose.prod.yml
3. Re-tag images if needed:
   docker tag blacklist-app:latest registry.jclee.me/jclee/blacklist/blacklist-app:latest
```

#### Security Stage Failures

**Problem**: Critical vulnerabilities block pipeline
```bash
# Symptoms
[FAIL] Pipeline blocked due to critical security vulnerabilities

# Solutions
1. Review safety-report.json artifact
2. Update vulnerable packages in requirements.txt:
   pip install --upgrade <package>
   pip freeze > requirements.txt
3. If false positive, add to .safety-policy.yml (create if needed)
4. Commit and push updated requirements.txt
```

---

### CI/CD Best Practices

#### 1. **Pre-commit Checks**
```bash
# Run local tests before pushing
make test                          # Run full test suite
python -m pytest tests/ -v         # Run pytest
docker-compose build               # Test builds locally

# Lint and format
black app/core/**/*.py             # Python formatting
flake8 app/core                    # Python linting
```

#### 2. **Branch Strategy**
```bash
# Development workflow
git checkout -b feature/new-feature
# ... make changes ...
git add -A
git commit -m "feat: add new feature"
git push origin feature/new-feature
# Create merge request → triggers build pipeline

# Production build
git checkout main
git merge feature/new-feature
git push origin main              # Triggers auto-build (not deployment)
```

#### 3. **Build Monitoring**
```bash
# Monitor build pipeline
watch -n 5 'curl -sf https://gitlab.jclee.me/api/v4/projects/<id>/pipelines?ref=main'

# Check registry for built images
curl -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
  https://gitlab.jclee.me/api/v4/projects/<id>/registry/repositories

# Download build artifacts
curl -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
  https://gitlab.jclee.me/api/v4/projects/<id>/jobs/<job_id>/artifacts
```

#### 4. **Emergency Procedures**
```bash
# If build pipeline is stuck/frozen
# 1. Cancel current pipeline:
#    GitLab UI → Pipelines → Cancel

# 2. Check runner status:
#    Settings → CI/CD → Runners

# 3. Retry failed job:
#    Click retry button on failed job

# If air-gapped production is down
# 1. SSH to air-gapped server
# 2. Check container logs:
#    docker-compose -f docker-compose.prod.yml logs -f
# 3. Rollback to previous image version (see "Rollback" above)
# 4. Restore from backups if needed
```

---

### Pipeline Optimization Tips

#### Reduce Build Time
```yaml
# Current optimizations in .gitlab-ci.yml
- DOCKER_BUILDKIT=1              # BuildKit for faster builds
- --cache-from ${IMAGE}:latest   # Layer caching
- Parallel builds (5 jobs)       # Build all containers simultaneously

# Additional improvements (optional)
- Use multi-stage builds         # Already implemented
- Pre-build base images          # Consider for future
- Increase runner resources      # If available
```

#### Reduce Registry Size
```bash
# Schedule cleanup job weekly
# Settings → CI/CD → Schedules
# Add schedule: "0 2 * * 0" (Every Sunday 2 AM)
# Target branch: main
# Variables: PIPELINE_SCHEDULE=cleanup

# Manual cleanup
# Trigger cleanup:registry job from GitLab UI
```

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
docker-compose -f docker-compose.prod.yml up -d
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

**Rate Limit Headers**:
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699564800
```

---

## 🔒 Security Features

### CSRF & Rate Limiting

**CSRF Protection** (`Flask-WTF`):
- Enabled for all POST/PUT/DELETE
- Token required in form data or headers
- Exemptions: Health checks, metrics endpoints

**Implementation**:
```python
# app/core/app.py
csrf = CSRFProtect()
csrf.init_app(app)
csrf.exempt(health_bp)  # Exempt health checks
```

**Rate Limiting** (`Flask-Limiter`):
- Redis-backed distributed rate limiting
- Prevents brute force attacks
- Returns `X-RateLimit-*` headers
- Configurable per-endpoint limits

### Database Schema

**Core Tables**:
- `blacklist_ips` - IP blacklist with country, detection dates
- `whitelist_ips` - VIP/Admin IP protection (priority over blacklist)
- `collection_credentials` - Encrypted authentication storage (AES-256)
- `credential_audit_log` - Credential change tracking
- `collection_logs` - Collection history and status

**Indexes** (for performance):
```sql
CREATE INDEX idx_blacklist_ip ON blacklist_ips(ip_address);
CREATE INDEX idx_whitelist_ip ON whitelist_ips(ip_address);
CREATE INDEX idx_collection_date ON collection_logs(collection_date);
```

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

# Check rate limit for specific IP
docker exec blacklist-redis redis-cli GET "LIMITER:192.168.1.100"

# Temporarily disable (development only)
# Set FLASK_ENV=development in .env
```

### Health Check Failures

**GitLab CI/CD Pipeline**:
```bash
# Check verification logs
gitlab-ci.yml → verify:production stage

# Manual health check
curl -f https://blacklist.nxtd.co.kr/health

# Full diagnostic
curl -s https://blacklist.nxtd.co.kr/api/monitoring/metrics | jq
```

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
- Application: https://blacklist.nxtd.co.kr
- Health Check: https://blacklist.nxtd.co.kr/health
- Collection Panel: https://blacklist.nxtd.co.kr/collection-panel

**Infrastructure**:
- Container Registry: https://registry.jclee.me
- GitLab: https://gitlab.jclee.me/jclee/blacklist
- GitLab CI/CD: https://gitlab.jclee.me/jclee/blacklist/-/pipelines

---

**Version**: 3.4.1 (CI/CD Stability Enhanced)
**Last Updated**: 2025-11-09
**Maintainer**: jclee
