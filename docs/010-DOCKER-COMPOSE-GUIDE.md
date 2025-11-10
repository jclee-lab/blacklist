# Docker Compose Environment Guide

**Last Updated**: 2025-11-08
**Version**: 3.3.9

---

## Overview

This project uses **environment-specific docker-compose files** to support different deployment scenarios:

| File | Environment | Domain | Purpose |
|------|-------------|--------|---------|
| `docker-compose.prod.yml` | Production | blacklist.nxtd.co.kr | Production deployment (default) |
| `docker-compose.dev.yml` | Development | blacklist.jclee.me | Local development with live reload |
| `docker-compose.offline.yml` | Offline | N/A | Offline package builds |
| `docker-compose.yml` | **Symlink** | → prod | Default file (points to production) |

---

## Quick Start

### Development Environment

**Use Case**: Local development with source code hot reload

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

**URL**: https://blacklist.jclee.me

**Features**:
- ✅ Source code mounted for live reload
- ✅ Debug mode enabled (`FLASK_DEBUG=true`)
- ✅ Port 2542 exposed for local access
- ✅ Default passwords allowed (development only!)
- ✅ Builds from local source code

### Production Environment

**Use Case**: Production deployment on blacklist.nxtd.co.kr

```bash
# Start production environment (default)
docker-compose up -d

# Or explicitly specify production file
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**URL**: https://blacklist.nxtd.co.kr

**Features**:
- ✅ Pre-built images from registry.jclee.me
- ✅ Production security settings
- ✅ No source code mounts
- ✅ Strict environment variable requirements
- ✅ Health checks enabled

### Offline Package Build

**Use Case**: Building offline deployment packages

```bash
# Build offline package
docker-compose -f docker-compose.offline.yml build

# Create offline images
docker-compose -f docker-compose.offline.yml up -d
```

**Features**:
- ✅ Uses `:offline` tagged images
- ✅ `pull_policy: never` (no registry pulls)
- ✅ Self-contained deployment

---

## Environment Variables

### Development Environment (docker-compose.dev.yml)

**Optional** (defaults provided):

```bash
# Database (defaults to 'postgres')
POSTGRES_PASSWORD=postgres

# Flask (defaults to 'dev-secret-key-change-me')
FLASK_SECRET_KEY=dev-secret-key-change-me

# Collection credentials (optional)
REGTECH_ID=your_regtech_username
REGTECH_PW=your_regtech_password
SECUDIUM_ID=your_secudium_username
SECUDIUM_PW=your_secudium_password
```

**Note**: Development allows insecure defaults for convenience. **NEVER use these in production!**

### Production Environment (docker-compose.prod.yml)

**Required** (no defaults):

```bash
# Database - REQUIRED
POSTGRES_PASSWORD=<secure_random_password>

# Flask - REQUIRED
FLASK_SECRET_KEY=<generated_with_secrets.token_hex(32)>

# Collection credentials - REQUIRED for collector service
REGTECH_ID=<production_regtech_username>
REGTECH_PW=<production_regtech_password>
SECUDIUM_ID=<production_secudium_username>
SECUDIUM_PW=<production_secudium_password>
```

**Generate Secure Secrets**:
```bash
# Generate Flask secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate PostgreSQL password
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Service Configuration Differences

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **Base Image** | Build from source | Registry images |
| **Source Code** | Volume mounted | Baked into image |
| **Hot Reload** | ✅ Enabled | ❌ Disabled |
| **FLASK_ENV** | `development` | `production` |
| **FLASK_DEBUG** | `true` | `false` |
| **Port Exposure** | `2542:2542` exposed | No exposed ports |
| **Environment Vars** | Defaults allowed | Strict requirements |
| **Traefik Router** | `blacklist-dev` | `blacklist-prod` |
| **Domain** | blacklist.jclee.me | blacklist.nxtd.co.kr |

### Container Details

#### Development (docker-compose.dev.yml)

```yaml
blacklist-app:
  build:
    context: ./app
    dockerfile: Dockerfile
  environment:
    FLASK_ENV: development
    FLASK_DEBUG: "true"
    PORT: 2542
  volumes:
    - ./app:/app:ro  # Source code hot reload
  ports:
    - "2542:2542"  # Direct access for debugging
```

#### Production (docker-compose.prod.yml)

```yaml
blacklist-app:
  image: registry.jclee.me/blacklist-app:latest
  environment:
    FLASK_ENV: production
    FLASK_DEBUG: "false"
    PORT: 2542
  volumes:
    - app_logs:/app/logs  # Logs only, no source code
  # No exposed ports (Traefik handles routing)
```

---

## Traefik Reverse Proxy Configuration

Both environments use Traefik for HTTPS termination and routing:

### Development (blacklist.jclee.me)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik-public"
  - "traefik.http.routers.blacklist-dev.rule=Host(`blacklist.jclee.me`)"
  - "traefik.http.routers.blacklist-dev.entrypoints=websecure"
  - "traefik.http.routers.blacklist-dev.tls=true"
  - "traefik.http.services.blacklist-frontend-dev.loadbalancer.server.port=2543"
```

### Production (blacklist.nxtd.co.kr)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik-public"
  - "traefik.http.routers.blacklist-prod.rule=Host(`blacklist.nxtd.co.kr`)"
  - "traefik.http.routers.blacklist-prod.entrypoints=websecure"
  - "traefik.http.routers.blacklist-prod.tls=true"
  - "traefik.http.services.blacklist-frontend-prod.loadbalancer.server.port=2543"
```

**Key Differences**:
- Router name: `blacklist-dev` vs `blacklist-prod`
- Host: `blacklist.jclee.me` vs `blacklist.nxtd.co.kr`
- Network: Both use `traefik-public` external network

---

## Migration from Old Structure

### What Changed (2025-11-08)

**Before**:
```
blacklist/
└── docker-compose.yml  # Single file for all environments
```

**After**:
```
blacklist/
├── docker-compose.yml          # Symlink → docker-compose.prod.yml (default)
├── docker-compose.prod.yml     # Production (blacklist.nxtd.co.kr)
├── docker-compose.dev.yml      # Development (blacklist.jclee.me)
└── docker-compose.offline.yml  # Offline package builds
```

### Migration Steps

1. **Update Git Repository**:
   ```bash
   git pull origin main
   ```

2. **For Development Workflow**:
   ```bash
   # Stop old services
   docker-compose down

   # Start with development file
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **For Production Deployment**:
   ```bash
   # Stop old services
   docker-compose down

   # Set production environment variables
   export POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

   # Start with production file (or use default)
   docker-compose up -d
   ```

4. **Update CI/CD Pipelines**:
   - Production: `docker-compose up -d` (uses symlink → prod)
   - Development: `docker-compose -f docker-compose.dev.yml up -d`

---

## Common Workflows

### Development: Start Services with Live Reload

```bash
# Start development environment
cd ~/app/blacklist
docker-compose -f docker-compose.dev.yml up -d

# Verify services
docker-compose -f docker-compose.dev.yml ps

# Watch logs
docker-compose -f docker-compose.dev.yml logs -f blacklist-app

# Make code changes (auto-reload applies)
vim app/core/routes/blacklist_routes.py

# Restart if needed
docker-compose -f docker-compose.dev.yml restart blacklist-app
```

### Production: Deploy New Version

```bash
# Pull latest images from registry
docker-compose pull

# Restart services with new images
docker-compose up -d

# Verify health
curl -sf https://blacklist.nxtd.co.kr/health
```

### Production: Manual Build and Deploy

```bash
# Build images locally
docker-compose -f docker-compose.prod.yml build

# Tag for registry
docker tag blacklist-app:latest registry.jclee.me/blacklist-app:latest

# Push to registry
docker push registry.jclee.me/blacklist-app:latest

# Deploy
docker-compose up -d
```

### Offline: Create Deployment Package

```bash
# Build offline images
docker-compose -f docker-compose.offline.yml build

# Tag as offline
docker tag blacklist-app:latest blacklist-app:offline

# Save images to tarball
docker save \
  blacklist-app:offline \
  blacklist-collector:offline \
  blacklist-postgres:offline \
  blacklist-redis:offline \
  blacklist-frontend:offline \
  -o blacklist-offline-images.tar

# Copy to deployment server
scp blacklist-offline-images.tar user@server:/opt/blacklist/

# On deployment server
docker load -i blacklist-offline-images.tar
docker-compose -f docker-compose.offline.yml up -d
```

---

## Health Checks

All environments include container health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:2542/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 90s
```

**Verify Health**:
```bash
# Check container health status
docker-compose ps

# Test health endpoint (development)
curl -sf http://localhost:2542/health

# Test health endpoint (production)
curl -sf https://blacklist.nxtd.co.kr/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "services": {
    "app": "running",
    "collector": "running",
    "frontend": "running"
  }
}
```

---

## Troubleshooting

### Development: Port Already in Use

```bash
# Check what's using port 2542
lsof -i :2542

# Kill the process or use different port
docker-compose -f docker-compose.dev.yml down
```

### Production: Missing Environment Variables

```bash
# Error: POSTGRES_PASSWORD not set
# Solution: Set in .env or export
echo "POSTGRES_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
echo "FLASK_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env

# Restart services
docker-compose up -d
```

### Development: Source Code Changes Not Reflecting

```bash
# Verify volume mount
docker-compose -f docker-compose.dev.yml exec blacklist-app ls -la /app

# Restart service
docker-compose -f docker-compose.dev.yml restart blacklist-app

# Rebuild if needed
docker-compose -f docker-compose.dev.yml build --no-cache blacklist-app
docker-compose -f docker-compose.dev.yml up -d
```

### Production: Image Pull Failures

```bash
# Check registry access
docker login registry.jclee.me

# Pull images manually
docker pull registry.jclee.me/blacklist-app:latest

# Use local build as fallback
docker-compose -f docker-compose.dev.yml build
docker tag blacklist-app:latest registry.jclee.me/blacklist-app:latest
```

---

## Security Best Practices

### Development

- ✅ Use `.env.development` for local secrets
- ✅ Never commit credentials to Git
- ✅ Rotate development passwords periodically
- ❌ Do NOT expose port 2542 to public network

### Production

- ✅ Use strong, randomly generated passwords
- ✅ Store secrets in environment variables or secret manager
- ✅ Enable Traefik TLS termination
- ✅ Verify health checks pass before deploying
- ❌ Never use default passwords
- ❌ Never expose internal ports directly

---

## CI/CD Integration

### GitHub Actions Workflow

**Production Deployment** (`.github/workflows/docker-build-portainer-deploy.yml`):

```yaml
# Triggered on push to main branch
on:
  push:
    branches: [main, master]
    paths:
      - 'app/**'
      - 'collector/**'
      - 'postgres/**'
      - 'redis/**'
      - 'frontend/**'
      - 'docker-compose.prod.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Build and push images
        run: |
          docker-compose -f docker-compose.prod.yml build
          docker-compose -f docker-compose.prod.yml push

      - name: Deploy via Portainer webhook
        run: |
          curl -X POST "${{ secrets.PORTAINER_WEBHOOK_URL }}"
```

**Development Testing**:
```yaml
# Test with development environment
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Start development services
        run: docker-compose -f docker-compose.dev.yml up -d

      - name: Run tests
        run: pytest tests/
```

---

## References

- **CI/CD Documentation**: `docs/CICD-INFRASTRUCTURE.md`
- **CI/CD Stabilization**: `docs/CICD-STABILIZATION-REPORT.md`
- **FortiManager Integration**: `docs/FORTIMANAGER-INTEGRATION.md`
- **Image Packaging**: `docs/IMAGE-PACKAGING-COMPLETE.md`
- **Project README**: `README.md`

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-08 | 3.3.9 | Created environment-specific compose files (dev/prod/offline) |
| 2025-11-08 | 3.3.9 | Renamed docker-compose.yml → docker-compose.offline.yml |
| 2025-11-08 | 3.3.9 | Created docker-compose.yml symlink → docker-compose.prod.yml |
| 2025-11-08 | 3.3.9 | Documented multi-environment structure and usage |

---

**Maintainer**: jclee
**License**: MIT
**Version**: 3.3.9
