# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Project Overview

**REGTECH Blacklist Intelligence Platform** - A Flask-based threat intelligence platform for collecting, managing, and analyzing IP blacklist data from Korean Financial Security Institute (REGTECH). Features automated collection pipelines, real-time monitoring, whitelist/blacklist management, and production deployment with Portainer API control.

**Architecture**: Microservices (4 independent containers)
- `blacklist-app` - Flask application (Port 2542)
- `blacklist-collector` - REGTECH collection service (Port 8545)
- `blacklist-postgres` - PostgreSQL 15 database
- `blacklist-redis` - Redis 7 cache
- `blacklist-frontend` - Next.js frontend (Port 2543)

**Repository Status**: Migrated to GitLab (https://gitlab.jclee.me/jclee/blacklist)

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
make db-backup BACKUP_FILE=backups/blacklist_20251107_120000.sql

# Container shell access
make shell-app         # Flask app container
make shell-db          # PostgreSQL container
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

## 🏗️ Architecture & Code Structure

### Directory Layout

```
blacklist/
├── app/                          # Flask application (Main app)
│   ├── core/                     # Core business logic
│   │   ├── app.py                # Flask app factory
│   │   ├── auth_manager.py       # Authentication
│   │   ├── collectors/           # Data collection modules
│   │   ├── routes/               # API endpoints
│   │   ├── services/             # Business services
│   │   └── models/               # Database models
│   ├── templates/                # Jinja2 templates
│   ├── static/                   # Static assets
│   ├── utils/                    # Utility functions
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # App container image
│
├── collector/                    # REGTECH collection service
│   ├── collector/                # Collection logic
│   ├── api/                      # Health check API
│   ├── core/                     # Core utilities
│   ├── monitoring_scheduler.py   # Scheduler service
│   ├── fortimanager_uploader.py  # FortiManager integration
│   └── Dockerfile                # Collector container image
│
├── frontend/                     # Next.js frontend
│   ├── app/                      # Next.js pages
│   ├── components/               # React components
│   ├── hooks/                    # Custom React hooks
│   └── Dockerfile                # Frontend container image
│
├── postgres/                     # PostgreSQL configuration
│   ├── Dockerfile                # Postgres container image
│   └── migrations/               # Schema migrations
│
├── redis/                        # Redis configuration
│   └── Dockerfile                # Redis container image
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── security/                 # Security tests
│   ├── conftest.py               # Pytest fixtures
│   └── test_config.py            # Test configuration
│
├── scripts/                      # Automation scripts
│   ├── comprehensive_test.py     # Test runner
│   ├── verify_endpoints.py       # API endpoint tests
│   └── (FortiManager scripts)    # FortiGate/FortiManager tools
│
├── docker-compose.yml            # Container orchestration
├── Makefile                      # Development commands
└── pytest.ini                    # Pytest configuration
```

### Key Components

#### Flask Application (`app/`)
- **Entry Point**: `app/run_app.py` - Application startup
- **Factory**: `app/core/app.py` - Flask app factory with security configuration
- **Routes**: `app/core/routes/` - API endpoints organized by feature
- **Services**: `app/core/services/` - Business logic layer
  - `database_service.py` - PostgreSQL operations
  - `redis_service.py` - Cache operations
  - `secure_credential_service.py` - Encrypted credential storage
- **Security**:
  - CSRF protection via Flask-WTF
  - Rate limiting via Flask-Limiter (Redis-backed)
  - Security headers (HSTS, CSP, X-Frame-Options)

#### Collector Service (`collector/`)
- **Scheduler**: `monitoring_scheduler.py` - Auto-collection orchestrator
- **Collections**: `collector/` - REGTECH/SECUDIUM data fetchers
- **Health Check**: `api/health_check.py` - Service health API (Port 8545)

#### Database Schema
- **blacklist_ips**: IP blacklist with country, detection dates
- **whitelist_ips**: VIP/Admin IP protection (priority over blacklist)
- **collection_credentials**: Encrypted authentication storage
- **collection_logs**: Collection history and status

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

### Running Tests

**Pytest Configuration** (`pytest.ini`):
- Coverage requirement: 80%+
- Test markers: `unit`, `integration`, `e2e`, `db`, `security`, `api`, `cache`
- Coverage reports: `htmlcov/`, `coverage.xml`

**Test Execution**:
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=core --cov-report=html

# Specific test categories
python -m pytest -m unit              # Unit tests
python -m pytest -m integration       # Integration tests
python -m pytest -m security          # Security tests (CSRF, rate limiting)

# Single test file
python -m pytest tests/unit/test_database.py -v

# Run tests in parallel (faster)
python -m pytest -n auto
```

### Adding New Features

1. **Database Changes**:
   - Update models in `app/core/models/`
   - Create migration in `postgres/migrations/`
   - Test migration locally: `make db-shell`

2. **API Endpoints**:
   - Add route in `app/core/routes/`
   - Implement service in `app/core/services/`
   - Add tests in `tests/integration/api/`
   - Apply rate limiting decorator: `@app.limiter.limit("10 per minute")`

3. **Security Considerations**:
   - All POST/PUT/DELETE endpoints require CSRF tokens
   - Apply rate limits to prevent abuse
   - Validate all user input
   - Use parameterized queries (no SQL injection)
   - Store credentials encrypted (use `secure_credential_service`)

### Code Style

- **Python**: Follow PEP 8
- **Type Hints**: Required for all functions
- **Docstrings**: Required for all public functions/classes
- **Testing**: 80%+ coverage minimum
- **Security**: No hardcoded credentials (use environment variables)

---

## 🚀 Deployment & CI/CD

### GitHub Actions Pipeline

**Workflow**: `.github/workflows/docker-build-portainer-deploy.yml`

**Pipeline Stages**:
1. **Security Scan** - Python (safety) + JavaScript (npm audit)
2. **Build Images** - Multi-stage Docker builds for all containers
3. **Push to Registry** - Push to `registry.jclee.me`
4. **Deploy via Portainer** - API-controlled deployment
5. **Health Check** - Verify deployment success
6. **Rollback** - Auto-rollback on failure

**Trigger**:
- Push to `master` branch
- Changes in: `app/`, `collector/`, `postgres/`, `redis/`, `Dockerfile*`, `docker-compose.yml`
- Manual dispatch: `workflow_dispatch`

### Container Registry

**Registry**: `registry.jclee.me`

**Images**:
- `blacklist-app:latest`
- `blacklist-collector:latest`
- `blacklist-postgres:latest`
- `blacklist-redis:latest`
- `blacklist-frontend:latest`

### Environment Variables

**Required**:
```bash
# Database
POSTGRES_PASSWORD=<secure_password>

# REGTECH Authentication
REGTECH_ID=<regtech_username>
REGTECH_PW=<regtech_password>
REGTECH_BASE_URL=https://regtech.fsec.or.kr

# SECUDIUM Authentication (Optional)
SECUDIUM_ID=<secudium_username>
SECUDIUM_PW=<secudium_password>
SECUDIUM_BASE_URL=https://rest.secudium.net

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

**Custom Limits** (apply in routes):
```python
@app.route('/api/sensitive')
@app.limiter.limit("10 per minute")
def sensitive_endpoint():
    pass
```

---

## 🔒 Security Features

### Phase 1.3: CSRF & Rate Limiting

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

### Priority-Based IP Filtering

**Logic**: Whitelist → Blacklist
1. Check whitelist first (VIP protection)
2. If found in whitelist → ALLOW
3. If not in whitelist → Check blacklist
4. If found in blacklist → BLOCK

**Prometheus Metrics**:
- `blacklist_decisions_total{decision="allowed|blocked"}`
- `blacklist_whitelist_hits_total`

---

## 🛠️ Troubleshooting

### Common Issues

#### Container Not Starting
```bash
# Check container logs
docker logs blacklist-app
docker logs blacklist-postgres

# Check health status
make health

# Restart services
make restart
```

#### Database Connection Errors
```bash
# Verify PostgreSQL is running
docker exec blacklist-postgres pg_isready -U postgres

# Check database logs
make logs-db

# Test connection
make db-shell
```

#### Collection Not Working
```bash
# Check collector logs
make logs-collector

# Verify credentials
# Access settings UI: https://blacklist.jclee.me/settings
# Or use API: POST /collection-panel/api/save-credentials

# Trigger manual collection
curl -X POST https://blacklist.jclee.me/collection-panel/trigger \
  -H "Content-Type: application/json" \
  -d '{"source": "regtech", "start_date": "2025-01-01", "end_date": "2025-01-10"}'
```

#### Rate Limit Errors
```bash
# Check Redis connection
docker exec blacklist-redis redis-cli ping

# Verify rate limit storage
docker exec blacklist-redis redis-cli keys "LIMITER*"

# Temporarily disable rate limits (development only)
# Set FLASK_ENV=development in .env
```

### Performance Optimization

**Database**:
- Ensure indexes on `ip_address` columns
- Use connection pooling (SQLAlchemy)
- Regular VACUUM ANALYZE

**Redis Cache**:
- Use for frequently accessed data
- Set appropriate TTL values
- Monitor cache hit rate

**Flask App**:
- Enable Gzip compression (already configured)
- Use pagination for large result sets
- Optimize database queries (use EXPLAIN)

---

## 📝 Additional Resources

**Documentation**:
- `README.md` - Comprehensive project overview
- `CHANGELOG.md` - Version history
- `collector/README.md` - Collection service details
- `collector/RATE-LIMITING.md` - Rate limiting documentation
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
**Last Updated**: 2025-11-07
**Maintainer**: jclee
