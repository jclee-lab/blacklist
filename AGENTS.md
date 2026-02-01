# AGENTS.md — Blacklist Intelligence Platform

**Generated:** 2026-01-20
**Commit:** f2e15ba
**Branch:** main

> **For AI Agents**: This file contains essential patterns and commands. Follow these strictly.

## CI/CD PIPELINE

GitLab CI primary. 9 stages, air-gap first architecture.

```
validate → lint → security → test → build → package → deploy → notify → cleanup
```

### Stages

| Stage | Jobs | Purpose |
|-------|------|---------|
| **validate** | `validate:environment` | Pipeline type, branch info |
| **lint** | `lint:python`, `lint:typescript`, `lint:dockerfile` | Ruff, ESLint, Hadolint |
| **security** | `security:python-scan`, `security:javascript-scan`, `security:secret-detection`, `security:container-scan` | pip-audit, npm audit, detect-secrets, Trivy |
| **test** | `test:backend-unit`, `test:backend-integration`, `test:frontend-unit`, `test:frontend-e2e` | Pytest + Playwright |
| **build** | `build:postgres`, `build:redis`, `build:collector`, `build:app`, `build:frontend` | Parallel Docker builds |
| **package** | `package:airgap-images` | Export tarballs → push to `airgap` branch |
| **deploy** | `deploy:local`, `deploy:airgap`, `deploy:rollback` | Manual deployment triggers |
| **notify** | `notify:slack` | Pipeline status to Slack |
| **cleanup** | `cleanup:registry`, `cleanup:docker` | Prune old images |

### Triggers

| Trigger | Pipeline Type | Stages Run |
|---------|---------------|------------|
| Push to `main`/`master` | `production` | All 9 stages |
| Merge Request | `merge_request` | lint + security + test only |
| Tag `v*` | `release` | All + GitLab Release creation |
| Schedule | `schedule` | Security scan only |

### Air-Gap Deployment

#### Push (CI creates package → pushes to `airgap` branch)

Automatic on `production`/`release` pipelines via `package:airgap-images` job:

1. Pull all 5 images from registry
2. `docker save` → gzip tarballs (parallel)
3. Create `dist/install.sh` + `airgap-deployment.tar.gz`
4. Force-push to `airgap` branch (replaces all content)

```bash
# Manual trigger (if needed)
git tag v1.0.0 && git push origin v1.0.0  # triggers release pipeline
```

#### Pull (deploy to air-gapped environment)

```bash
# Clone airgap branch (contains install.sh + images tarball)
git clone -b airgap git@gitlab.jclee.me:nextrade/blacklist.git
cd blacklist && ./install.sh
```

#### What's in the airgap branch

| File | Purpose |
|------|---------|
| `install.sh` | Loads images + starts services |
| `airgap-deployment.tar.gz` | All 5 images + docker-compose.yml |

### Key Variables

| Variable | Purpose |
|----------|---------|
| `CI_REGISTRY` | `registry.jclee.me` |
| `SLACK_WEBHOOK_URL` | Pipeline notifications |
| `LOCAL_DEPLOY_HOST` | SSH deploy target |
| `ROLLBACK_TAG` | Version for rollback job |

## COMMANDS

```bash
# Development
make dev                    # Start all services (hot reload)
make dev-app                # API only
make logs                   # View logs

# Testing
make test                   # All tests (backend + frontend)
make test-backend-unit      # Backend unit tests only
make test-frontend          # Frontend tests (Vitest)
make test-frontend-e2e      # E2E tests (Playwright)

# Single test (backend)
docker compose exec -T blacklist-app python -m pytest tests/unit -v -k "test_function_name"

# Single test (frontend)
cd frontend && npm run test -- --testNamePattern="test name"

# Linting
pre-commit run --all-files  # Python (Ruff + mypy)
cd frontend && npm run lint # TypeScript (ESLint + Prettier)

# Test markers (backend)
make test-security          # Security tests only
make test-db                # Database tests only
make test-api               # API tests only
```

## CODE STYLE

### Python (Backend)

| Rule | Value |
|------|-------|
| **Formatter** | Ruff |
| **Line length** | 120 chars |
| **Indent** | 4 spaces |
| **Quotes** | Double `"` |
| **Type hints** | Required (mypy enforced) |
| **Target** | Python 3.11 |

```python
# Import order (isort via Ruff)
import os                           # 1. stdlib
from typing import Any              # 1. stdlib

import structlog                    # 2. third-party

from app.core.utils import helper   # 3. first-party (app, collector)
```

### TypeScript (Frontend)

| Rule | Value |
|------|-------|
| **Framework** | Next.js 15 (App Router) |
| **Formatter** | Prettier |
| **Line length** | 100 chars |
| **Indent** | 2 spaces |
| **Quotes** | Single `'` |
| **Semicolons** | Required |
| **Trailing comma** | ES5 style |

## CRITICAL PATTERNS

### Dependency Injection (Python)

```python
# ✅ CORRECT: Access services via Flask extensions
from flask import current_app
blacklist_service = current_app.extensions['blacklist_service']
db = current_app.extensions['db_service']

# ❌ WRONG: Never import services directly
from app.core.services.blacklist_service import BlacklistService  # FORBIDDEN
service = BlacklistService()  # FORBIDDEN - breaks DI
```

### API Calls (Frontend)

```typescript
// ✅ CORRECT: Use the api proxy (lib/api.ts)
import { api } from '@/lib/api';
const data = await api.get('/blacklist');

// ❌ WRONG: Never use direct URLs
fetch('http://localhost:2542/api/blacklist');  // FORBIDDEN - env-dependent
```

### Error Handling (Python)

```python
# Use RFC 7807 standard errors
from app.core.utils.errors import APIError

raise APIError(status=400, code="INVALID_IP", message="Invalid IP format")

# Error code prefixes: AUTH_, VALID_, NOT_FOUND_, INTERNAL_
```

## ANTI-PATTERNS (NEVER DO)

| ❌ Forbidden | ✅ Alternative | Reason |
|--------------|----------------|--------|
| `from app.core.services import X` | `current_app.extensions['x']` | Circular imports |
| `BlacklistService()` | ServiceFactory DI | Breaks injection |
| `fetch('localhost:2542')` | `api.get('/path')` | Env-dependent |
| SQLAlchemy / Prisma | Raw SQL only | Project policy |
| `as any`, `@ts-ignore` | Proper types | Type safety |
| Hardcoded ports/hosts | Environment variables | Deployment |

## PROJECT STRUCTURE

```
app/                    # Flask API (Manual DI, Raw SQL)
├── core/routes/api/    # API endpoints
├── core/services/      # Business logic (via ServiceFactory)
└── run_app.py          # Entry point

frontend/               # Next.js 15 Dashboard
├── app/                # App Router pages
├── lib/api.ts          # API client (ALL calls go here)
└── components/         # React components

collector/              # ETL Service (independent)
tests/                  # Pytest + Playwright
postgres/migrations/    # Raw SQL migrations (no ORM)
```

## SERVICES

| Service | Port | Entry Point |
|---------|------|-------------|
| API | :2542 | `app/run_app.py` |
| Dashboard | :2543 | `frontend/app/page.tsx` |
| Collector | :8545 | `collector/run_collector.py` |

## TESTING CONVENTIONS

```python
# Test file naming: test_*.py
# Test markers: @pytest.mark.unit, @pytest.mark.integration, @pytest.mark.security

# Use MOCK_CREDENTIALS for auth tests (from tests/test_config.py)
# Access services via fixtures: app, client, db_service, redis_client
```

## SECURITY RULES

- **Never log**: tokens, passwords, API keys
- **Tests**: Use `MOCK_CREDENTIALS` only
- **Secrets**: Load from environment variables, never hardcode
- **Auth**: Bearer JWT via `Authorization` header

## SERVICE BOUNDARIES

- **No cross-imports** between app/, collector/, frontend/
- **Communication**: DB, Redis, HTTP only (no shared code)
- **Contracts**: See `docs/references/api-reference.md`

## KNOWN ISSUES (Fix Required)

### Hardcoded URLs (11 violations across 9 files)

| File | Line | Issue |
|------|------|-------|
| `app/core/routes/api/collection/utils.py` | 13 | Hardcoded collector URL |
| `app/core/routes/api/blacklist/collection.py` | 54 | Hardcoded collector URL |
| `app/core/services/blacklist_service.py` | 420, 462, 510 | Mixed localhost/container names |
| `collector/fortimanager_uploader.py` | 36, 77 | Hardcoded app URL |
| `frontend/next.config.ts` | 7 | Hardcoded API URL |

**Root cause**: docker-compose uses host network but code mixes `localhost:8545`, `blacklist-collector:8545`, `blacklist-app:443`.

**Fix**: Use environment variables (`COLLECTOR_URL`, `API_URL`).

---

## COMPLEXITY HOTSPOTS

Files requiring extra care when modifying:

| File | Lines | Risk | Notes |
|------|-------|------|-------|
| `app/core/routes/api/ip_management_api.py` | 1050 | HIGH | IP CRUD, complex validation |
| `collector/core/regtech_collector.py` | 922 | HIGH | Hardcoded URLs, magic numbers |
| `app/core/services/blacklist_service.py` | 820 | HIGH | Core logic, hardcoded URLs |
| `frontend/app/ip-management/IPManagementClient.tsx` | 893 | MEDIUM | Large React component |
| `collector/core/multi_source_collector.py` | 766 | MEDIUM | Mixed sync/async |

---

## NOTES

- SQLAlchemy is in requirements.txt but **usage is forbidden**
- Line length: Ruff(120) vs Prettier(100) — each applies to its domain
- Legacy `app/core/collectors/` was deleted — use `collector/` service
