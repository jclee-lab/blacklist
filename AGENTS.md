# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-21  
**Commit:** 317bc5b  
**Branch:** airgap

## OVERVIEW

IP Blacklist Management Platform. Collects malicious IPs from external sources (REGTECH, SECUDIUM), stores in PostgreSQL, serves via REST API, and can push to FortiGate firewalls.

## STRUCTURE

```
blacklist/
├── app/                    # Flask API (port 2542)
│   └── core/routes/api/    # Blueprint routes
├── collector/              # IP collection service (port 8545)
│   └── sources/            # REGTECH, SECUDIUM adapters
├── frontend/               # Next.js 15 + Tailwind v4 (port 443)
├── deploy/                 # Docker/airgap deployment
│   └── airgap/             # Offline install package
├── images/                 # Docker image tarballs
├── postgres/               # DB init scripts
├── docker-compose.yml      # 5 services, network_mode: host
└── install.sh              # Airgap installer
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `app/core/routes/api/` | Flask Blueprint pattern |
| Add IP source | `collector/sources/` | Implement `BaseSource` |
| Frontend page | `frontend/app/{route}/` | See `frontend/AGENTS.md` |
| DB schema | `postgres/init.sql` | Also `app/core/services/db_service.py` |
| Docker config | `docker-compose.yml` | All services on host network |
| Airgap build | `deploy/airgap/`, `install.sh` | Creates tarball with images |

## SERVICES

| Service | Port | Image | Purpose |
|---------|------|-------|---------|
| blacklist-postgres | 5432 | postgres:15 | Data storage |
| blacklist-redis | 6379 | redis:7 | Caching, rate limiting |
| blacklist-collector | 8545 | blacklist-collector | IP collection from sources |
| blacklist-app | 2542 | blacklist-app | REST API |
| blacklist-frontend | 443 | blacklist-frontend | Web UI (HTTPS) |

## API ROUTES

| Prefix | File | Purpose |
|--------|------|---------|
| `/api/blacklist/` | `blacklist/core.py` | IP list, stats, export |
| `/api/collection/` | `collection/` | Sources, credentials, force-collect |
| `/api/fortinet/` | `fortinet/` | FortiGate device management |
| `/api/ip-management/` | `ip_management/` | Manual IP CRUD |
| `/api/database/` | `database/` | Table browser |
| `/api/settings/` | `settings/` | System config |

## CONVENTIONS

- **network_mode: host** - All Docker services share host network
- **Fernet encryption** - Credentials encrypted with `CREDENTIAL_MASTER_KEY`
- **Rate limiting** - Decorators on API routes
- **Pagination** - `page` (1-based), `per_page` (max 1000)
- **Error handling** - `ValidationError`, `BadRequestError`, `DatabaseError` classes
- **No tests** - Project lacks test coverage

## ANTI-PATTERNS

| Forbidden | Reason |
|-----------|--------|
| Direct DB access in routes | Use `db_service` from `app.extensions` |
| Hardcoded credentials | Use `collection_credentials` table |
| localhost URLs in frontend | Use relative paths, API proxied |
| Bind mounts in prod | Use Docker named volumes |

## CREDENTIALS

Stored in `collection_credentials` table:

| Source | Username | Notes |
|--------|----------|-------|
| REGTECH | nextrade | Password: `Sprtmxm1@3` (plaintext, `encrypted=false`) |
| SECUDIUM | - | Configured separately |

**Encryption note:** App encrypts, but Collector has different key derivation. Store with `encrypted=false` for Collector to read.

## COMMANDS

```bash
# Development
docker compose up -d                    # Start all services
docker compose logs -f blacklist-app    # Watch API logs
docker compose build blacklist-app --no-cache  # Rebuild after code change

# Collection
curl -X POST http://localhost:8545/api/force-collection/REGTECH

# Airgap package
./install.sh --skip-ssl                 # Install without SSL cert gen
tar czvf blacklist-airgap.tar.gz install.sh docker-compose.yml images/

# Database
docker exec -it blacklist-postgres psql -U postgres blacklist
```

## KNOWN ISSUES

| Issue | Status | Workaround |
|-------|--------|------------|
| Credential encryption mismatch | Known | Store with `encrypted=false` |
| SSL certs required for frontend | Fixed | Baked into Docker image |
| `fortigate_devices` table missing | Create on first use | See `postgres/init.sql` |

## NOTES

- Airgap tarball: 664MB with 5 Docker images
- Fresh install has empty DB - must trigger collection or restore dump
- Frontend crashes without SSL certs in `/app/ssl/`
