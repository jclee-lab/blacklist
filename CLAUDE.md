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
- **GitLab** (PRIMARY): https://gitlab.jclee.me/jclee/blacklist
  - ✅ Active development
  - ✅ CI/CD pipeline (`.gitlab-ci.yml`)
  - ✅ Container Registry (registry.jclee.me)
- **GitHub** (Mirror): https://github.com/qws941/blacklist
  - ℹ️ Read-only mirror
  - ❌ No CI/CD (GitHub Actions disabled)

**Note**: All development, CI/CD builds, and deployments happen through GitLab only.

---

## ⚡ Quick Command Reference Card

```bash
# Setup (first time only)
make setup                            # Complete dev environment setup
make setup-offline                    # Setup from offline packages
make package-deps                     # Package dependencies for offline

# Most Common Operations
make dev                              # Start development environment
make logs                             # View all logs
make db-shell                         # PostgreSQL shell
make test                             # Run full test suite
make health                           # Check all services

# Troubleshooting
docker logs blacklist-app             # App logs
docker logs blacklist-postgres | grep Migration  # Migration status
docker exec blacklist-redis redis-cli ping       # Redis health
curl http://localhost:2542/health     # API health check

# CI/CD
git push origin main                  # Trigger build pipeline
./scripts/package-single-image.sh blacklist-app  # Package for offline

# Database
make db-backup                        # Backup database
make db-restore BACKUP_FILE=...       # Restore from backup
```

---

## ⚡ Quick Command Reference Card

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
app/core/routes/              # API routes (18 blueprint modules)
app/core/services/            # Business logic (15 services)
app/core/collectors/          # Data collection modules
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

## ⚡ Essential Commands

### Setup & Installation (First Time Only)

```bash
# Complete automated setup (recommended for new developers)
make setup
# This will:
# - Create Python virtual environment (.venv)
# - Install Python dependencies (requirements.txt + requirements-dev.txt)
# - Install Node.js dependencies (frontend/package.json)
# - Install VSCode extensions (from .vscode/extensions.json)
# - Setup Git hooks
# - Create required directories (dist/images, backups, logs)
# - Copy .env template (if not exists)

# Or run setup script directly
./scripts/setup-dev-environment.sh

# Individual setup steps (if needed)
python3 -m venv .venv                 # Create virtual environment
source .venv/bin/activate             # Activate virtual environment
pip install -r requirements.txt       # Install Python dependencies
cd frontend && npm install            # Install frontend dependencies
```

### Offline/Air-Gapped Setup

**For deployment to servers without internet access:**

```bash
# Step 1: Package dependencies (on internet-connected server)
make package-deps
# This will:
# - Download Python packages (pip download)
# - Download Node.js packages (npm + tar.gz)
# - Create offline installation script
# - Create compressed archive: dist/blacklist-dependencies-YYYYMMDD-HHMMSS.tar.gz

# Step 2: Transfer to offline server
scp dist/blacklist-dependencies-*.tar.gz user@offline-server:/opt/blacklist/

# Step 3: Install on offline server
ssh offline-server
cd /opt/blacklist
tar -xzf blacklist-dependencies-*.tar.gz
make setup-offline
# This will:
# - Install Python packages from local archive
# - Install Node.js packages from local archive
# - Setup Git hooks
# - Create required directories
# - Copy .env template

# Or run setup script directly
./scripts/setup-offline.sh
```

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

### Quick Deploy to GitLab Registry

```bash
# Automated: Git push triggers CI/CD pipeline (builds + pushes to registry.jclee.me)
git add -A
git commit -m "feat: update application"
git push origin main

# Manual: Build and push all images to GitLab registry
./scripts/build-and-push-gitlab.sh

# Manual: Build and push to GitHub Container Registry
./scripts/build-and-push-ghcr.sh

# Check pipeline status
# Visit: https://gitlab.jclee.me/jclee/blacklist/-/pipelines
```

### Testing

**Pytest Configuration** (`pytest.ini`):
- Coverage requirement: 80%+
- Test markers: `unit`, `integration`, `e2e`, `slow`, `db`, `security`, `api`, `cache`
- Coverage reports: `htmlcov/`, `coverage.xml`

**Test Statistics**:
- **Unit Tests**: 13+ test files (226.8 KB total)
  - `test_blacklist_service*.py` (4 variants)
  - `test_encryption.py` (17.9 KB) - AES-256 encryption tests
  - `test_redis_cache.py` (15.6 KB)
  - `test_regtech_data_deep.py` (23.4 KB)
  - `test_secudium_collector.py` (19.6 KB)
  - `test_settings_service_deep.py` (26.6 KB)
  - Plus: collectors/, services/, middleware/, monitoring/, common/, utils/

- **Integration Tests**: `tests/integration/` (13.9 KB)
  - API endpoint testing
  - Service integration tests

- **Security Tests**: `tests/security/`
  - CSRF protection validation
  - Rate limiting enforcement
  - SQL injection prevention

**Test Execution**:
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=core --cov-report=html

# By marker (recommended)
python -m pytest -m unit              # Unit tests only
python -m pytest -m integration       # Integration tests
python -m pytest -m security          # Security tests (CSRF, rate limiting)
python -m pytest -m db                # Database tests
python -m pytest -m api               # API endpoint tests
python -m pytest -m cache             # Redis cache tests
python -m pytest -m slow              # Long-running tests

# By directory
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/security/ -v

# Single test file
python -m pytest tests/unit/test_database.py -v

# Parallel execution (faster)
python -m pytest -n auto

# Verbose with output
python -m pytest -v -s
```

**Pytest Test Markers** (`pytest.ini`):

Test organization uses markers for selective execution:
- `@pytest.mark.unit` - Fast unit tests (mocked dependencies)
- `@pytest.mark.integration` - Integration tests (real database/Redis)
- `@pytest.mark.security` - Security tests (CSRF, rate limiting, SQL injection)
- `@pytest.mark.db` - Database-specific tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.cache` - Redis cache tests
- `@pytest.mark.slow` - Long-running tests (collection simulations)
- `@pytest.mark.e2e` - End-to-end workflow tests

**Usage Examples**:
```bash
# Run only fast unit tests
python -m pytest -m "unit and not slow" -v

# Run database and API tests together
python -m pytest -m "db or api" -v

# Exclude slow tests
python -m pytest -m "not slow" -v

# Run all integration tests except slow ones
python -m pytest -m "integration and not slow" -v
```

**Makefile Commands**:
```bash
make test                     # Run comprehensive test suite
make test-endpoints           # Test API endpoints only
```

**Manual whitelist/blacklist tests**:
```bash
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

### FortiGate/FortiManager Integration

```bash
# Update blacklist on FortiManager
./scripts/fortimanager-update-blacklist.sh

# Install policy to all managed devices
./scripts/install-fmg-policy-to-all-devices.sh

# Push to FortiGate firewalls
./scripts/push-to-fortigates.sh

# Manage credentials
./scripts/manage-credentials.sh

# Enable auto-upload
./scripts/enable-fmg-auto-install.sh
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

### Common Utilities (2025-11-08)

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

**Critical Behavior**: PostgreSQL automatically runs all migrations on **every container restart**, not just the first time. This prevents the common "DB schema lost on restart" problem.

**How It Works**:
1. Custom entrypoint (`postgres/docker-entrypoint-custom.sh`) wraps the official PostgreSQL startup
2. Executes all `.sql` files in `postgres/migrations/` directory in alphanumeric order
3. All migrations use idempotent patterns (`IF NOT EXISTS`, `IF EXISTS`)
4. After migrations complete, starts PostgreSQL normally

**Migration Example** (`postgres/migrations/V001__init_schema.sql`):
```sql
CREATE TABLE IF NOT EXISTS blacklist_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    ...
);

ALTER TABLE collection_credentials
ADD COLUMN IF NOT EXISTS is_encrypted BOOLEAN DEFAULT FALSE;
```

**Key Benefit**: `make restart` is safe - your schema always matches the migration files.

### Flask Application Factory Pattern

**Location**: `app/core/app.py::create_app()`

**Key Components**:
- CSRF Protection via Flask-WTF
- Redis-backed rate limiting (Flask-Limiter)
- Security headers middleware
- Structured logging with correlation IDs
- Blueprint-based route organization

### Route Organization (18 Blueprint Modules)

**Location**: `app/core/routes/`

**Structure**:
```
routes/
├── api/                      # RESTful API endpoints
│   ├── core_api.py           # Health, stats, monitoring
│   ├── ip_management_api.py  # Blacklist/whitelist operations
│   ├── collection_api.py     # Collection triggers
│   ├── system_api.py         # System management
│   └── database_api.py       # Database operations
├── web/                      # Web UI routes
│   └── web_routes.py         # HTML pages
├── blacklist_api.py (32.3 KB) # Main blacklist operations
├── whitelist_api.py          # VIP protection (Phase 1)
├── collection_panel.py (23.2 KB)  # Collection control panel
├── fortinet_api.py (20.6 KB) # FortiGate/FortiManager integration
├── statistics_api.py (29.7 KB)    # Statistics endpoints
├── settings_routes.py (14.3 KB)   # Settings management
├── regtech_admin_routes.py (25.1 KB) # REGTECH admin panel
├── multi_collection_api.py (19.4 KB) # Multi-source orchestration
├── migration_routes.py       # Data migration tools
├── proxy_routes.py           # Frontend proxy
└── websocket_routes.py       # WebSocket real-time updates
```

**Blueprint Pattern**:
- Each file defines a Flask Blueprint
- Blueprints registered in `app.py::create_app()`
- Centralized route organization by feature
- CSRF and rate limiting applied per blueprint

**Example**:
```python
# app/core/routes/api/ip_management_api.py
from flask import Blueprint

ip_management_bp = Blueprint('ip_management', __name__)

@ip_management_bp.route('/api/blacklist/check', methods=['GET'])
@app.limiter.limit("50 per minute")
def check_ip():
    # Implementation
    pass
```

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

### Prometheus Metrics & Observability

**Location**: `app/core/app.py` (metrics exported at `/api/monitoring/metrics`)

**Key Metrics Tracked**:
- `blacklist_whitelist_hits_total` - Whitelist match counter
- `blacklist_decisions_total{decision="allow|block"}` - Decision metrics
- `blacklist_check_duration_seconds` - IP check latency histogram
- `redis_cache_hits_total` - Cache performance
- `database_connection_pool_size` - Connection pool metrics
- `collection_success_total` - Collection success rate by source
- `collection_error_total{source="regtech|secudium"}` - Error tracking

**Structured Logging**:
- JSON-based event logging with correlation IDs
- Event metadata: `ip_address`, `decision`, `source`, `timestamp`
- Log aggregation via Loki (if configured)

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

**Error Recovery**:
- Exponential backoff on persistent failures
- Automatic retry with configurable max attempts
- Error logging to `collection_logs` table
- Health monitoring via `/api/collection/status`

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
│   │   ├── routes/               # API endpoints by feature (18 modules)
│   │   │   ├── api/              # RESTful API routes
│   │   │   │   ├── core_api.py   # Health, stats, monitoring
│   │   │   │   ├── ip_management_api.py  # Blacklist/whitelist
│   │   │   │   ├── collection_api.py     # Collection triggers
│   │   │   │   ├── system_api.py         # System management
│   │   │   │   └── database_api.py       # Database operations
│   │   │   ├── blacklist_api.py (32.3 KB)  # Core blacklist endpoints
│   │   │   ├── whitelist_api.py            # VIP protection (Phase 1)
│   │   │   ├── statistics_api.py (29.7 KB) # Analytics & reporting
│   │   │   ├── collection_panel.py (23.2 KB)  # Collection UI & settings
│   │   │   ├── regtech_admin_routes.py (25.1 KB)  # REGTECH admin panel
│   │   │   ├── settings_routes.py (14.3 KB)  # System settings UI
│   │   │   ├── fortinet_api.py (20.6 KB)   # FortiManager integration
│   │   │   ├── multi_collection_api.py (19.4 KB)  # Multi-source orchestration
│   │   │   ├── migration_routes.py         # Data migration tools
│   │   │   ├── proxy_routes.py             # Frontend proxy
│   │   │   ├── websocket_routes.py         # WebSocket real-time updates
│   │   │   └── web/                        # Web UI routes
│   │   │       └── web_routes.py
│   │   ├── services/             # Business logic (15 services)
│   │   │   ├── database_service.py (13.7 KB)  # Core DB operations
│   │   │   ├── blacklist_service.py (33.9 KB)  # IP filtering logic
│   │   │   ├── secure_credential_service.py (17.2 KB)  # Encrypted credentials
│   │   │   ├── collection_service.py (19.4 KB)  # Collection orchestration
│   │   │   ├── analytics_service.py (10.9 KB)  # Analytics & reporting
│   │   │   ├── scheduler_service.py (9.9 KB)  # Collection scheduling
│   │   │   ├── settings_service.py (13.9 KB)  # System settings
│   │   │   ├── regtech_config_service.py (14.5 KB)  # REGTECH config
│   │   │   ├── fortimanager_push_service.py (6.9 KB)  # FortiManager
│   │   │   ├── secudium_collector_service.py (10.6 KB)  # SECUDIUM
│   │   │   ├── scoring_service.py (5.3 KB)  # Risk scoring
│   │   │   ├── expiry_service.py (7.3 KB)  # IP expiration
│   │   │   ├── credential_service.py (15.3 KB)  # Credential management
│   │   │   └── ab_test_service.py (3.8 KB)  # A/B testing
│   │   ├── collectors/           # Data collection modules
│   │   │   ├── unified_collector.py  # Multi-source collector
│   │   │   └── regtech_auth.py       # REGTECH authentication
│   │   ├── models/               # SQLAlchemy models
│   │   ├── database/             # DB schema & utilities
│   │   ├── utils/                # Helper utilities
│   │   ├── static/               # CSS, JS, images
│   │   └── templates/            # Jinja2 templates
│   ├── Dockerfile                # Multi-stage build with docs
│   ├── entrypoint.sh             # Container startup script
│   ├── requirements.txt          # Python dependencies
│   └── run_app.py                # Direct Python execution
│
├── collector/                    # REGTECH/SECUDIUM data collection
│   ├── core/                     # Core collection logic (138.8 KB)
│   │   ├── regtech_collector.py (44.7 KB)  # REGTECH API client
│   │   ├── multi_source_collector.py (27.2 KB)  # Multi-source aggregation
│   │   ├── database.py (20.4 KB)           # DB operations with retry
│   │   ├── policy_monitor.py (19.0 KB)     # Policy change detection
│   │   ├── data_quality_manager.py (16.7 KB)  # Data validation
│   │   └── rate_limiter.py (10.9 KB)       # API rate limiting
│   ├── monitoring_scheduler.py (19.6 KB)   # Auto-collection orchestrator
│   ├── fortimanager_uploader.py            # FortiManager integration
│   ├── collector/                # Collection modules
│   │   └── health_server.py      # Health endpoint
│   ├── api/                      # Additional APIs
│   ├── utils/                    # Utilities
│   ├── requirements.txt          # Collector Python dependencies
│   ├── Dockerfile                # Multi-stage collector image
│   └── RATE-LIMITING.md          # Rate limiting documentation
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
│   │   ├── 000_init_complete_schema.sql  (18.8 KB)
│   │   ├── V001__verify_schema.sql       (5.8 KB)
│   │   └── V002__secure_credentials.sql  (8.2 KB)
│   └── SCHEMA-DEPENDENCY.md      # Schema documentation
│
├── redis/
│   └── Dockerfile                # Redis 7 with persistence
│
├── scripts/                      # Automation scripts (32 files)
│   ├── package-single-image.sh   # Single image packaging (recommended)
│   ├── package-all-sequential.sh # Sequential all images
│   ├── comprehensive_test.py     # Test runner
│   └── (FortiManager scripts)    # FortiGate integration tools
│
├── tests/                        # Pytest test suite
│   ├── unit/                     # Unit tests (226.8 KB total)
│   │   ├── test_blacklist_service*.py  # 4 variants
│   │   ├── test_encryption.py (17.9 KB)
│   │   ├── test_redis_cache.py (15.6 KB)
│   │   ├── test_regtech_data_deep.py (23.4 KB)
│   │   ├── test_secudium_collector.py (19.6 KB)
│   │   ├── test_settings_service_deep.py (26.6 KB)
│   │   ├── services/             # Service layer tests
│   │   ├── collectors/           # Collector tests
│   │   ├── middleware/           # Middleware tests
│   │   ├── monitoring/           # Monitoring tests
│   │   ├── common/               # Common utilities tests
│   │   └── utils/                # Utility tests
│   ├── integration/              # Integration tests (13.9 KB)
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

**Route Organization** (`app/core/routes/` - 18 modules):

**API Routes** (`api/`):
- `core_api.py` - Health, stats, monitoring
- `ip_management_api.py` - Blacklist/whitelist operations
- `collection_api.py` - Collection triggers
- `system_api.py` - System management
- `database_api.py` - Database operations

**Feature Routes** (root):
- `blacklist_api.py` (32.3 KB) - Core blacklist endpoints
- `whitelist_api.py` - VIP protection API (Phase 1)
- `statistics_api.py` (29.7 KB) - Analytics & reporting
- `collection_panel.py` (23.2 KB) - Collection UI & settings
- `regtech_admin_routes.py` (25.1 KB) - REGTECH admin panel
- `settings_routes.py` (14.3 KB) - System settings UI
- `fortinet_api.py` (20.6 KB) - FortiManager integration
- `multi_collection_api.py` (19.4 KB) - Multi-source orchestration
- `migration_routes.py` - Data migration tools
- `proxy_routes.py` - Frontend proxy
- `websocket_routes.py` - WebSocket real-time updates

**Web UI** (`web/`):
- `web_routes.py` - Frontend UI routes

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

### Running Tests

**Pytest Configuration** (`pytest.ini`):
- Coverage requirement: 80%+
- Test markers: `unit`, `integration`, `e2e`, `slow`, `db`, `security`, `api`, `cache`
- Coverage reports: `htmlcov/`, `coverage.xml`

**Test Statistics**:
- **Unit Tests**: 13+ test files (226.8 KB)
  - `test_blacklist_service*.py` (4 variants)
  - `test_encryption.py` (17.9 KB) - AES-256 encryption
  - `test_redis_cache.py` (15.6 KB)
  - `test_regtech_data_deep.py` (23.4 KB)
  - `test_secudium_collector.py` (19.6 KB)
  - `test_settings_service_deep.py` (26.6 KB)
  - Plus: collectors/, services/, middleware/, monitoring/, common/, utils/

- **Integration Tests**: `tests/integration/` (13.9 KB)
  - API endpoint testing
  - Service integration tests

- **Security Tests**: `tests/security/`
  - CSRF protection validation
  - Rate limiting enforcement
  - SQL injection prevention

**Test Execution**:
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=core --cov-report=html

# Specific categories
python -m pytest -m unit              # Unit tests
python -m pytest -m integration       # Integration tests
python -m pytest -m security          # Security tests (CSRF, rate limiting)
python -m pytest -m db                # Database tests
python -m pytest -m slow              # Long-running tests

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

### 🔒 Air-Gapped Deployment Model (2025-11-09)

**Environment**: Air-gapped (offline deployment)
**Workflow**: Build → Package → Transfer → Load → Deploy

**Key Principle**: NO automatic deployment. Build artifacts (Docker images) are packaged as .tar.gz files, physically transferred to air-gapped servers, then manually loaded and deployed.

### GitLab CI/CD Pipeline (Air-Gapped Build)

**Status**: ✅ Active (GitLab only, no GitHub Actions)
**Pipeline**: `.gitlab-ci.yml`
**Registry**: registry.jclee.me (GitLab Container Registry)
**Pipeline URL**: https://gitlab.jclee.me/jclee/blacklist/-/pipelines

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
Manual offline transfer required (see Air-Gapped Deployment Workflow)
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
- `processed_reports` - Deduplication tracking for SECUDIUM reports

**Indexes** (for performance):
```sql
CREATE INDEX idx_blacklist_ip ON blacklist_ips(ip_address);
CREATE INDEX idx_whitelist_ip ON whitelist_ips(ip_address);
CREATE INDEX idx_collection_date ON collection_logs(collection_date);
```

**Security Views**:
- `credential_security_status` - Expiry monitoring and status

---

## 🔍 Common Development Patterns

### Adding New API Endpoint

**Example**: Add IP lookup endpoint

```python
# Step 1: Create route in app/core/routes/api/ip_management_api.py
from flask import Blueprint, jsonify, request
from core.services.blacklist_service import blacklist_service

ip_management_bp = Blueprint('ip_management', __name__)

@ip_management_bp.route('/api/ip/lookup/<ip>', methods=['GET'])
@app.limiter.limit("50 per minute")  # Rate limit
def lookup_ip(ip):
    """Look up IP information"""
    # Validation
    if not validate_ip(ip):
        return jsonify({'error': 'Invalid IP'}), 400

    # Business logic (service layer)
    result = blacklist_service.lookup(ip)

    return jsonify(result), 200

# Step 2: Register blueprint in app/core/app.py::create_app()
from routes.api.ip_management_api import ip_management_bp
app.register_blueprint(ip_management_bp)

# Step 3: Add tests in tests/integration/api/test_ip_management.py
@pytest.mark.api
@pytest.mark.integration
def test_lookup_ip(client):
    response = client.get('/api/ip/lookup/1.2.3.4')
    assert response.status_code == 200
    assert 'ip_address' in response.json
```

### Adding Database Service

**Example**: Add user management service

```python
# Step 1: Create service in app/core/services/user_service.py
from services.database_service import db_service

class UserService:
    def __init__(self):
        self.db = db_service

    def get_user(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        return self.db.execute_query(query, (user_id,))

# Singleton pattern (in app.py)
user_service = UserService()

# Step 2: Use in routes
from services.user_service import user_service
user = user_service.get_user(123)
```

### Common Utilities (2025-11-08)

**Database Utilities** (`app/core/utils/db_utils.py`):
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

**Redis Caching** (`app/core/utils/cache_utils.py`):
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
# Access settings UI: https://blacklist.nxtd.co.kr/settings

# Trigger manual collection
curl -X POST https://blacklist.nxtd.co.kr/collection-panel/trigger \
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

## 🔍 Common Debugging Workflows

### 1. Container Won't Start

**Symptoms**: `docker-compose up -d` fails or container exits immediately

**Debug Steps**:
```bash
# 1. Check container status
docker-compose ps

# 2. View container logs (last 50 lines)
docker-compose logs --tail=50 blacklist-app
docker-compose logs --tail=50 blacklist-postgres

# 3. Check for port conflicts
netstat -tulpn | grep -E '2542|5432|6379|8545'

# 4. Verify environment variables
docker-compose config | grep -A5 environment

# 5. Test database connectivity
docker exec blacklist-postgres pg_isready -U postgres

# 6. Check disk space
df -h
docker system df
```

### 2. Database Connection Failures

**Symptoms**: "Connection refused" or "Connection timeout" errors

**Debug Steps**:
```bash
# 1. Verify PostgreSQL is running
docker-compose ps blacklist-postgres

# 2. Check PostgreSQL logs for errors
docker logs blacklist-postgres | tail -50

# 3. Test connection from app container
docker exec blacklist-app psql -h blacklist-postgres -U postgres -d blacklist -c "SELECT 1"

# 4. Verify network connectivity
docker network inspect blacklist-network

# 5. Check connection pool status
curl http://localhost:2542/api/monitoring/metrics | grep pool
```

### 3. Collection Service Not Running

**Symptoms**: No new data being collected, collector health check fails

**Debug Steps**:
```bash
# 1. Check collector service status
docker-compose ps blacklist-collector

# 2. View collector logs (look for errors)
docker logs blacklist-collector --tail=100

# 3. Check collector health endpoint
curl http://localhost:8545/health

# 4. Verify REGTECH credentials are configured
docker exec blacklist-app python -c "from core.services.credential_service import CredentialService; print(CredentialService.get_credentials('regtech'))"

# 5. Check collection schedule status
curl http://localhost:2542/api/collection/status | jq

# 6. Manually trigger collection (for testing)
curl -X POST http://localhost:2542/api/collection/regtech/trigger \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-11-01", "end_date": "2025-11-10"}'
```

### 4. Rate Limiting Issues

**Symptoms**: "429 Too Many Requests" errors

**Debug Steps**:
```bash
# 1. Check Redis connection
docker exec blacklist-redis redis-cli ping

# 2. View current rate limit keys
docker exec blacklist-redis redis-cli keys "LIMITER*"

# 3. Check specific IP rate limit
docker exec blacklist-redis redis-cli GET "LIMITER:192.168.1.100"

# 4. Clear rate limits for testing (development only)
docker exec blacklist-redis redis-cli FLUSHDB

# 5. Verify rate limit configuration
grep -r "limiter.limit" app/core/routes/
```

### 5. CI/CD Pipeline Failures

**Symptoms**: Build fails, tests don't pass, image push errors

**Debug Steps**:
```bash
# 1. Check pipeline status
# Visit: https://gitlab.jclee.me/jclee/blacklist/-/pipelines

# 2. Download job artifacts
curl -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
  https://gitlab.jclee.me/api/v4/projects/<id>/jobs/<job_id>/artifacts/download

# 3. Reproduce build locally
docker build -t test-build -f app/Dockerfile app/

# 4. Run tests locally
make test

# 5. Check GitLab runner status
# Visit: https://gitlab.jclee.me/jclee/blacklist/-/settings/ci_cd#runners

# 6. View job logs
# Visit: https://gitlab.jclee.me/jclee/blacklist/-/jobs/<job_id>
```

### 6. Memory or Performance Issues

**Symptoms**: Slow response times, high memory usage, container OOM kills

**Debug Steps**:
```bash
# 1. Check resource usage
docker stats --no-stream

# 2. View connection pool metrics
curl http://localhost:2542/api/monitoring/metrics | grep -E "pool|connection"

# 3. Check Redis memory usage
docker exec blacklist-redis redis-cli INFO memory

# 4. Analyze slow queries
docker exec blacklist-postgres psql -U postgres -d blacklist -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10"

# 5. Profile Flask app (development only)
# Add profiling middleware in app/core/app.py

# 6. Check for memory leaks
docker exec blacklist-app python -c "import psutil; print(psutil.virtual_memory())"
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

## 📚 Additional Resources

**Documentation**:
- `README.md` - Comprehensive project overview
- `CHANGELOG.md` - Version history
- `IMAGE-PACKAGING-COMPLETE.md` - Offline deployment guide
- `scripts/PACKAGING-GUIDE.md` - Detailed packaging instructions
- `postgres/SCHEMA-DEPENDENCY.md` - Database schema documentation
- `collector/README.md` - Collection service details
- `collector/RATE-LIMITING.md` - Rate limiting documentation
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

**Version**: 3.3.9
**Last Updated**: 2025-11-10
**Maintainer**: jclee
