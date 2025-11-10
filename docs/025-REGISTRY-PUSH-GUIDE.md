# Docker Image Registry Push Guide

Complete guide for building and pushing Docker images to various container registries.

---

## 📦 Available Registries

### 1. Private Registry (registry.jclee.me) - **Recommended**
- **URL**: https://registry.jclee.me
- **Usage**: Production deployment via Portainer
- **Advantages**: Full control, fast access, already integrated

### 2. GitLab Container Registry
- **URL**: https://registry.gitlab.jclee.me
- **Project**: jclee/blacklist
- **Advantages**: Integrated with GitLab CI/CD, free unlimited storage

### 3. GitHub Container Registry (GHCR)
- **URL**: ghcr.io
- **Project**: qws941/blacklist
- **Advantages**: Public access, GitHub integration

---

## 🚀 Quick Start

### Method 1: Private Registry (registry.jclee.me)

```bash
# 1. Login to registry
docker login registry.jclee.me

# 2. Build and push all images
./scripts/build-and-push.sh

# 3. Or push single component
./scripts/build-and-push.sh app

# 4. Force rebuild without cache
./scripts/build-and-push.sh all --no-cache
```

### Method 2: GitLab Container Registry

```bash
# 1. Create GitLab Personal Access Token
# https://gitlab.jclee.me/-/profile/personal_access_tokens
# Scopes: read_registry, write_registry

# 2. Export credentials
export GITLAB_USER=jclee
export GITLAB_TOKEN=<your-token>

# 3. Login to GitLab registry
echo $GITLAB_TOKEN | docker login registry.gitlab.jclee.me -u $GITLAB_USER --password-stdin

# 4. Build and push
./scripts/build-and-push-gitlab.sh

# 5. View in GitLab
# https://gitlab.jclee.me/jclee/blacklist/container_registry
```

### Method 3: GitHub Container Registry (GHCR)

```bash
# 1. Create GitHub Personal Access Token
# https://github.com/settings/tokens/new
# Scopes: write:packages, read:packages

# 2. Export credentials
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx

# 3. Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u qws941 --password-stdin

# 4. Build and push
./scripts/build-and-push-ghcr.sh

# 5. View in GitHub
# https://github.com/qws941?tab=packages
```

### Method 4: Automated CI/CD (GitHub Actions)

```bash
# Simply push to GitHub - CI/CD handles everything
git add .
git commit -m "feat: update application"
git push github main

# Monitor pipeline
# https://github.com/qws941/blacklist/actions
```

---

## 📋 Available Scripts

| Script | Registry | Description |
|--------|----------|-------------|
| `build-and-push.sh` | registry.jclee.me | Private registry (production) |
| `build-and-push-gitlab.sh` | registry.gitlab.jclee.me | GitLab container registry |
| `build-and-push-ghcr.sh` | ghcr.io | GitHub container registry |

### Script Usage

```bash
# All scripts support the same options:

# Build all components
./scripts/build-and-push.sh

# Build single component
./scripts/build-and-push.sh app
./scripts/build-and-push.sh postgres
./scripts/build-and-push.sh redis
./scripts/build-and-push.sh collector
./scripts/build-and-push.sh frontend

# Force rebuild (no cache)
./scripts/build-and-push.sh all --no-cache
./scripts/build-and-push.sh app --no-cache

# Show help
./scripts/build-and-push.sh --help
```

---

## 🔧 Registry Configuration

### Private Registry (registry.jclee.me)

**Login**:
```bash
docker login registry.jclee.me
# Username: admin
# Password: <registry-password>
```

**Image Names**:
```
registry.jclee.me/blacklist-postgres:latest
registry.jclee.me/blacklist-redis:latest
registry.jclee.me/blacklist-collector:latest
registry.jclee.me/blacklist-app:latest
registry.jclee.me/blacklist-frontend:latest
```

**docker-compose.yml**:
```yaml
services:
  blacklist-app:
    image: registry.jclee.me/blacklist-app:latest
```

### GitLab Container Registry

**Login**:
```bash
export GITLAB_USER=jclee
export GITLAB_TOKEN=<your-token>
echo $GITLAB_TOKEN | docker login registry.gitlab.jclee.me -u $GITLAB_USER --password-stdin
```

**Image Names**:
```
registry.gitlab.jclee.me/jclee/blacklist/blacklist-postgres:latest
registry.gitlab.jclee.me/jclee/blacklist/blacklist-redis:latest
registry.gitlab.jclee.me/jclee/blacklist/blacklist-collector:latest
registry.gitlab.jclee.me/jclee/blacklist/blacklist-app:latest
registry.gitlab.jclee.me/jclee/blacklist/blacklist-frontend:latest
```

**docker-compose.yml**:
```yaml
services:
  blacklist-app:
    image: registry.gitlab.jclee.me/jclee/blacklist/blacklist-app:latest
```

### GitHub Container Registry (GHCR)

**Login**:
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
echo $GITHUB_TOKEN | docker login ghcr.io -u qws941 --password-stdin
```

**Image Names**:
```
ghcr.io/qws941/blacklist-postgres:latest
ghcr.io/qws941/blacklist-redis:latest
ghcr.io/qws941/blacklist-collector:latest
ghcr.io/qws941/blacklist-app:latest
ghcr.io/qws941/blacklist-frontend:latest
```

**docker-compose.yml**:
```yaml
services:
  blacklist-app:
    image: ghcr.io/qws941/blacklist-app:latest
```

---

## 🏗️ Build Process

### Components Built

1. **blacklist-postgres** - PostgreSQL 15 with auto-migrations
2. **blacklist-redis** - Redis 7 cache server
3. **blacklist-collector** - REGTECH/SECUDIUM data collector
4. **blacklist-app** - Flask backend application
5. **blacklist-frontend** - Next.js frontend (if exists)

### Build Features

- **Multi-stage builds**: Optimized image sizes
- **Layer caching**: Faster rebuilds
- **Platform**: linux/amd64 (production compatible)
- **Labels**: OCI-compliant metadata
- **Tags**:
  - `latest` - Always points to newest version
  - `<commit-hash>` - Specific commit version (e.g., `a1b2c3d4`)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/docker-build-portainer-deploy.yml`

**Triggers**:
- Push to `main` or `master` branch
- Changes in: `app/`, `collector/`, `postgres/`, `redis/`, `frontend/`, `Dockerfile*`
- Manual dispatch: `workflow_dispatch`

**Pipeline Stages**:
```
1. Security Scan (safety, npm audit)
   ↓
2. Run Tests (pytest with coverage)
   ↓
3. Build Images (parallel matrix build)
   ↓
4. Push to Registry (registry.jclee.me)
   ↓
5. Deploy via Portainer Webhook
   ↓
6. Health Check (verify deployment)
```

**View Pipeline**:
```bash
# Push to GitHub to trigger
git push github main

# Monitor at:
# https://github.com/qws941/blacklist/actions
```

---

## 📊 Registry Comparison

| Feature | registry.jclee.me | GitLab Registry | GHCR |
|---------|-------------------|-----------------|------|
| **Access** | Private | Private/Public | Public |
| **Storage** | Limited | Unlimited | Unlimited |
| **Speed** | Fast (local) | Fast (local) | Moderate |
| **Integration** | Portainer | GitLab CI/CD | GitHub Actions |
| **Cost** | Free | Free | Free |
| **Recommended For** | Production | GitLab users | Open source |

---

## 🔍 Troubleshooting

### Login Failed

```bash
# Check credentials
docker login registry.jclee.me
docker login registry.gitlab.jclee.me -u $GITLAB_USER
docker login ghcr.io -u qws941

# Verify stored credentials
cat ~/.docker/config.json | jq '.auths'
```

### Push Failed

```bash
# Check image exists locally
docker images | grep blacklist

# Verify tag format
docker images registry.jclee.me/blacklist-app

# Manual push
docker push registry.jclee.me/blacklist-app:latest
```

### Registry Unreachable

```bash
# Test connectivity
curl -I https://registry.jclee.me/v2/
curl -I https://registry.gitlab.jclee.me/v2/
curl -I https://ghcr.io/v2/

# Check DNS
nslookup registry.jclee.me
ping registry.jclee.me
```

### Build Failed

```bash
# Check Dockerfile syntax
docker build -f app/Dockerfile app/

# View detailed logs
./scripts/build-and-push.sh app 2>&1 | tee build.log

# Clean build cache
docker builder prune -a
```

---

## 📝 Best Practices

### 1. Version Tagging Strategy

```bash
# Always tag with both latest and commit hash
docker tag app:build registry.jclee.me/blacklist-app:latest
docker tag app:build registry.jclee.me/blacklist-app:$(git rev-parse --short HEAD)

# For releases, add semantic version
docker tag app:build registry.jclee.me/blacklist-app:v3.3.9
```

### 2. Image Size Optimization

- Use multi-stage builds
- Minimize layers
- Use `.dockerignore`
- Remove build dependencies in final stage

### 3. Security

- Never commit registry credentials
- Use environment variables
- Rotate tokens regularly
- Enable vulnerability scanning

### 4. Automation

- Use CI/CD for production
- Manual builds for testing only
- Always verify after push
- Monitor build times

---

## 🎯 Quick Reference

### Push to Production (registry.jclee.me)

```bash
# Quick deploy
./scripts/build-and-push.sh && \
curl -X POST https://portainer.jclee.me/api/webhooks/xxx
```

### Switch Registry in docker-compose.yml

```bash
# From private registry to GitLab
sed -i 's|registry.jclee.me/|registry.gitlab.jclee.me/jclee/blacklist/|g' docker-compose.yml

# From GitLab to GHCR
sed -i 's|registry.gitlab.jclee.me/jclee/blacklist/|ghcr.io/qws941/|g' docker-compose.yml
```

### Pull Latest Images

```bash
# From current registry
docker-compose pull

# Force pull (ignore cache)
docker-compose pull --no-cache

# Pull specific service
docker-compose pull blacklist-app
```

---

## 📚 Additional Resources

- **GitHub Actions**: `.github/workflows/docker-build-portainer-deploy.yml`
- **Dockerfile Examples**: `app/Dockerfile`, `collector/Dockerfile`, `postgres/Dockerfile`
- **Portainer Deployment**: `README.md` Section "Portainer Webhook"
- **Offline Packaging**: `IMAGE-PACKAGING-COMPLETE.md`

---

**Last Updated**: 2025-11-08
**Version**: 3.3.9
