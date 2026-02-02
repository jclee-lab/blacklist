# AGENTS.md — Blacklist Intelligence Platform

**Generated:** 2026-01-20
**Commit:** f2e15ba
**Branch:** main

> **For AI Agents**: This file contains essential patterns and commands. Follow these strictly.

## CI/CD PIPELINE

GitHub Actions. Auto-release on tag push.

### Release Workflow (`.github/workflows/release.yml`)

Triggered on tag push `v*`. Creates GitHub Release with airgap bundle.

| Job | Purpose |
|-----|---------|
| **build** | Build all 5 Docker images (frontend, app, collector, postgres, redis) |
| **package** | Create airgap bundle (`blacklist-vX.X.X-airgap.tar.gz`) |
| **release** | Upload to GitHub Releases with changelog |

### Creating a Release

```bash
# 1. Update VERSION and CHANGELOG.md
echo "3.6.0" > VERSION

# 2. Commit, tag, push
git add VERSION CHANGELOG.md
git commit -m "chore: release v3.6.0"
git tag -a v3.6.0 -m "Release v3.6.0"
git push origin master v3.6.0

# 3. GitHub Actions automatically creates release
```

### Air-Gap Deployment

```bash
# Option 1: GitHub CLI (requires gh installed)
gh release download v3.6.0 --repo jclee-homelab/blacklist

# Option 2: curl - latest version auto-detect (jq required)
TAG=$(curl -s "https://api.github.com/repos/jclee-homelab/blacklist/releases/latest" | jq -r ".tag_name")
curl -#L "https://github.com/jclee-homelab/blacklist/releases/download/$TAG/blacklist-$TAG-airgap.tar.gz" -o "blacklist-$TAG-airgap.tar.gz"

# Option 3: curl - latest version (no jq)
TAG=$(curl -s "https://api.github.com/repos/jclee-homelab/blacklist/releases/latest" | grep "tag_name" | sed -E 's/.*"([^"]+)".*/\1/')
curl -#L "https://github.com/jclee-homelab/blacklist/releases/download/$TAG/blacklist-$TAG-airgap.tar.gz" -o "blacklist-$TAG-airgap.tar.gz"

# Option 4: via SSH jump host
ssh jump3 'TAG=$(curl -s "https://api.github.com/repos/jclee-homelab/blacklist/releases/latest" | jq -r ".tag_name") && \
  curl -#L "https://github.com/jclee-homelab/blacklist/releases/download/$TAG/blacklist-$TAG-airgap.tar.gz" -o "blacklist-$TAG-airgap.tar.gz"'

# Option 5: PowerShell (Windows)
$TAG = (Invoke-RestMethod "https://api.github.com/repos/jclee-homelab/blacklist/releases/latest").tag_name
Invoke-WebRequest "https://github.com/jclee-homelab/blacklist/releases/download/$TAG/blacklist-$TAG-airgap.tar.gz" -OutFile "blacklist-$TAG-airgap.tar.gz"

# Deploy
tar -xzf blacklist-$TAG-airgap.tar.gz
./install.sh
```

### Release Assets

| File | Purpose |
|------|---------|
| `blacklist-vX.X.X-airgap.tar.gz` | All 5 Docker images + docker-compose.yml + install.sh |
| `blacklist-vX.X.X-airgap.tar.gz.sha256` | Checksum for verification |

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
