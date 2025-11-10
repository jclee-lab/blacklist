# CI/CD Infrastructure - Synology NAS Docker

**Version**: 3.3.9
**Last Updated**: 2025-11-08
**Infrastructure**: Synology NAS (192.168.50.215) + GitHub Actions + Portainer

---

## 📋 Overview

Blacklist 프로젝트는 **GitHub Actions** 기반 CI/CD 파이프라인과 **Synology NAS** Docker 환경을 활용한 자동화된 배포 시스템을 사용합니다.

### Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│  GitHub Repo    │      │  GitHub Actions  │      │  Synology NAS       │
│  (gitlab.jclee) │─────▶│  (CI/CD Runner)  │─────▶│  (Docker Registry)  │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
                                  │                           │
                                  │                           │
                                  ▼                           ▼
                         ┌──────────────────┐      ┌─────────────────────┐
                         │  Security Scan   │      │  Portainer Stack    │
                         │  - Python safety │      │  - 5 Containers     │
                         │  - npm audit     │      │  - Auto-pull        │
                         │  - pytest        │      │  - Health checks    │
                         └──────────────────┘      └─────────────────────┘
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **GitHub Actions** | CI/CD 파이프라인 실행 | `.github/workflows/docker-build-portainer-deploy.yml` |
| **Docker Registry** | 이미지 저장소 | `registry.jclee.me` (Synology NAS) |
| **Portainer** | 컨테이너 오케스트레이션 | `portainer.jclee.me` |
| **Traefik** | 리버스 프록시 & SSL | `traefik-public` network |
| **Production** | 운영 환경 | `blacklist.nxtd.co.kr` |

---

## 🚀 CI/CD Pipeline

### Workflow: `docker-build-portainer-deploy.yml`

**Trigger**:
- Push to `master` branch
- Changes in: `app/`, `collector/`, `postgres/`, `redis/`, `Dockerfile*`, `docker-compose.yml`
- Manual dispatch: `workflow_dispatch`

### Pipeline Stages

#### Stage 0: 🔒 Security Scan

**Purpose**: 취약점 검사 및 코드 품질 검증

**Steps**:
1. **Python Security Scan** (safety)
   - `app/requirements.txt` 스캔
   - `collector/requirements.txt` 스캔
   - JSON 리포트 생성 및 업로드

2. **JavaScript Security Scan** (npm audit)
   - `frontend/package.json` 스캔
   - `worker/package.json` 스캔
   - Moderate 이상 취약점 검사

3. **Unit Tests** (pytest)
   - Coverage: 80%+ 목표
   - `pytest --cov=core --cov-report=xml`
   - Codecov 업로드

**Outputs**:
- `security-reports` artifact (30일 보관)
- `coverage.xml` (Codecov)

---

#### Stage 1: 🏗️ Build & Push Images

**Purpose**: Docker 이미지 병렬 빌드 및 레지스트리 푸시

**Strategy**:
```yaml
strategy:
  fail-fast: false
  max-parallel: 4  # 4개 컴포넌트 동시 빌드
  matrix:
    component: [postgres, redis, collector, app]
```

**Build Matrix**:

| Component | Context | Dockerfile | Image Tag |
|-----------|---------|------------|-----------|
| **postgres** | `./postgres` | `./postgres/Dockerfile` | `registry.jclee.me/blacklist-postgres:latest` |
| **redis** | `./redis` | `./redis/Dockerfile` | `registry.jclee.me/blacklist-redis:latest` |
| **collector** | `./collector` | `./collector/Dockerfile` | `registry.jclee.me/blacklist-collector:latest` |
| **app** | `./app` | `./app/Dockerfile` | `registry.jclee.me/blacklist-app:latest` |

**Build Process**:
1. **Checkout Code**
2. **Setup Docker Buildx** (multi-platform 지원)
3. **Login to Registry** (Synology NAS)
4. **Build Docker Image** (병렬 빌드)
   - Platform: `linux/amd64`
   - Cache: `--cache-from` (이전 빌드 재사용)
   - BuildKit: `BUILDKIT_INLINE_CACHE=1`
   - Tags: `latest`, `{commit-sha}`
5. **Push to Registry** (백그라운드 병렬 푸시)
   - `latest` 태그 푸시
   - `{commit-sha}` 태그 푸시
   - 동시 진행으로 시간 단축

**Optimizations**:
- ✅ 병렬 빌드 (4개 컴포넌트 동시)
- ✅ 빌드 캐시 재사용
- ✅ 멀티스테이지 Dockerfile
- ✅ 백그라운드 병렬 푸시

**Execution Time**:
- 단일 컴포넌트: ~3-5분
- 병렬 빌드: ~5-7분 (전체)

---

#### Stage 2: 🚀 Deploy via Webhook

**Purpose**: Portainer 웹훅 트리거 및 배포 검증

**Steps**:

1. **Trigger Portainer Webhook**
   ```bash
   curl -X POST "$PORTAINER_WEBHOOK_URL" \
     --connect-timeout 30 \
     --max-time 60
   ```
   - 최대 3회 재시도
   - 10초 간격
   - HTTP 200/204 성공

2. **Wait for Deployment**
   - 60초 대기 (컨테이너 시작 시간)

3. **Health Check**
   ```bash
   curl "$PRD_URL/health"
   # Expected: {"status":"healthy"}
   ```
   - 최대 10회 재시도
   - 15초 간격
   - `/api/stats` 기능 검증

4. **Deployment Success**
   - 배포 완료 메시지
   - 운영 URL 확인

**Webhook Configuration**:
- **URL**: `https://portainer.jclee.me/api/stacks/webhooks/{webhook-id}`
- **Secret**: GitHub Secrets `PORTAINER_WEBHOOK_URL`
- **Behavior**:
  - 레지스트리에서 최신 이미지 pull
  - 컨테이너 재시작
  - Health check 대기

---

## 🐳 Docker Infrastructure

### Synology NAS Configuration

**Host**: `192.168.50.215`

**Services Running on NAS**:
- **Docker Registry** (`registry.jclee.me`)
  - Port: 5000 (internal)
  - HTTPS: Traefik managed
  - Storage: Synology volume

- **Portainer** (`portainer.jclee.me`)
  - Port: 9443 (HTTPS)
  - Webhook endpoint for CI/CD

- **Traefik** (reverse proxy)
  - HTTP: 80 → 443 redirect
  - HTTPS: 443 (Let's Encrypt SSL)
  - Network: `traefik-public`

### Docker Compose Stack

**File**: `docker-compose.yml`

**Networks**:
```yaml
networks:
  blacklist-network:    # Internal communication
    driver: bridge
  traefik-public:       # External access (HTTPS)
    external: true
```

**Volumes**:
```yaml
volumes:
  postgres_data:    # PostgreSQL database
  redis_data:       # Redis cache
  collector_data:   # Collection data
  app_logs:         # Application logs
  app_uploads:      # File uploads
```

**Containers** (5 services):

#### 1. blacklist-postgres
```yaml
image: blacklist-postgres:offline
environment:
  POSTGRES_DB: blacklist
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
volumes:
  - postgres_data:/var/lib/postgresql/data
  - ./postgres/migrations:/migrations:ro  # Auto-migration
healthcheck:
  test: pg_isready -U postgres -d blacklist
  interval: 30s
  start_period: 40s
```

**Features**:
- ✅ Auto-migrating PostgreSQL (runs migrations on restart)
- ✅ Idempotent SQL migrations (`IF NOT EXISTS`)
- ✅ Health check with pg_isready

#### 2. blacklist-redis
```yaml
image: blacklist-redis:offline
volumes:
  - redis_data:/data
healthcheck:
  test: redis-cli ping
  interval: 30s
```

**Features**:
- ✅ Persistent data storage
- ✅ Redis PING health check

#### 3. blacklist-collector
```yaml
image: blacklist-collector:offline
environment:
  POSTGRES_HOST: blacklist-postgres
  REDIS_HOST: blacklist-redis
  HEALTH_CHECK_PORT: 8545
  COLLECTION_INTERVAL: 86400  # 24 hours
volumes:
  - collector_data:/app/data
  - app_logs:/app/logs
healthcheck:
  test: curl -f http://localhost:8545/health
  start_period: 40s
```

**Features**:
- ✅ Automated REGTECH/SECUDIUM collection
- ✅ Health check API (port 8545)
- ✅ 24시간 주기 자동 수집

#### 4. blacklist-app
```yaml
image: blacklist-app:offline
environment:
  FLASK_ENV: production
  PORT: 2542
  SSL_ENABLED: "false"  # Traefik handles SSL
volumes:
  - app_logs:/app/logs
  - app_uploads:/app/uploads
healthcheck:
  test: curl -f http://localhost:2542/health
  start_period: 90s
```

**Features**:
- ✅ Flask application
- ✅ CSRF protection
- ✅ Rate limiting (Redis-backed)
- ✅ Security headers

#### 5. blacklist-frontend
```yaml
image: blacklist-frontend:offline
environment:
  NODE_ENV: production
  NEXT_PUBLIC_API_URL: http://blacklist-app:2542
networks:
  - blacklist-network
  - traefik-public  # External access
labels:
  # Traefik configuration
  - "traefik.enable=true"
  - "traefik.http.routers.blacklist.rule=Host(`blacklist.nxtd.co.kr`)"
  - "traefik.http.routers.blacklist.entrypoints=websecure"
  - "traefik.http.routers.blacklist.tls=true"
```

**Features**:
- ✅ Next.js frontend
- ✅ HTTPS via Traefik
- ✅ Automatic SSL certificates

---

## 🔐 Secrets Management

### GitHub Secrets

**Required Secrets**:
```bash
REGISTRY_HOST=registry.jclee.me
REGISTRY_USER={username}
REGISTRY_PASSWORD={password}
PRD_URL=https://blacklist.nxtd.co.kr
PORTAINER_WEBHOOK_URL=https://portainer.jclee.me/api/stacks/webhooks/{id}
```

**Where Used**:
- `REGISTRY_*`: Docker image push/pull authentication
- `PRD_URL`: Health check endpoint
- `PORTAINER_WEBHOOK_URL`: Deployment trigger

### Environment Variables

**Development** (`.env` file):
```bash
# Database
POSTGRES_PASSWORD=postgres

# REGTECH Authentication
REGTECH_ID={username}
REGTECH_PW={password}
REGTECH_BASE_URL=https://regtech.fsec.or.kr

# Flask Security
FLASK_SECRET_KEY={generated_with_secrets.token_hex(32)}

# Redis
REDIS_HOST=blacklist-redis
REDIS_PORT=6379
```

**Production** (docker-compose.yml):
- Environment variables embedded in `docker-compose.yml`
- Credentials encrypted in database (see `secure_credential_service`)

---

## 📊 Monitoring & Observability

### Health Checks

**Endpoints**:
- `https://blacklist.nxtd.co.kr/health` - Main application
- `http://blacklist-app:2542/health` - Internal app health
- `http://blacklist-collector:8545/health` - Collector health

**Health Check Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T12:00:00Z",
  "version": "3.3.9",
  "database": "connected",
  "redis": "connected"
}
```

### Container Health

**Docker Healthcheck Configuration**:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts
- **Start Period**:
  - postgres: 40s
  - redis: 20s
  - collector: 40s
  - app: 90s (longest startup time)

**Check Status**:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
# Expected: healthy (30s) for all containers
```

### Logs

**Access Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f blacklist-app
docker-compose logs -f blacklist-collector

# Last 100 lines
docker-compose logs --tail=100 blacklist-app
```

**Log Volumes**:
- `app_logs:/app/logs` - Application logs
- `collector_data:/app/data` - Collection logs

---

## 🔄 Deployment Workflow

### Automated Deployment

**Full Workflow**:
```
1. Developer pushes code to master
   ↓
2. GitHub Actions triggered
   ↓
3. Security scans (Python + JS)
   ↓
4. Unit tests (pytest)
   ↓
5. Build 4 Docker images (parallel)
   ↓
6. Push to registry.jclee.me (parallel)
   ↓
7. Trigger Portainer webhook
   ↓
8. Portainer pulls latest images
   ↓
9. Containers restart (rolling update)
   ↓
10. Health checks (max 10 retries)
   ↓
11. Deployment success notification
```

**Execution Time**:
- Security Scan: ~3-5 minutes
- Build & Push: ~5-7 minutes (parallel)
- Deployment: ~2-3 minutes
- **Total**: ~10-15 minutes

### Manual Deployment

**Scenario 1: Deploy without CI/CD**

```bash
# 1. Build images locally
docker-compose build

# 2. Tag images
docker tag blacklist-app:latest registry.jclee.me/blacklist-app:latest

# 3. Push to registry
docker push registry.jclee.me/blacklist-app:latest

# 4. Pull on production
docker pull registry.jclee.me/blacklist-app:latest

# 5. Restart services
docker-compose up -d
```

**Scenario 2: Rollback to previous version**

```bash
# 1. Find previous commit SHA
git log --oneline | head -5

# 2. Pull previous image
docker pull registry.jclee.me/blacklist-app:{commit-sha}

# 3. Tag as latest
docker tag registry.jclee.me/blacklist-app:{commit-sha} blacklist-app:latest

# 4. Restart
docker-compose up -d blacklist-app
```

**Scenario 3: Hotfix deployment**

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-fix

# 2. Make changes and commit
git commit -m "fix: critical security patch"

# 3. Merge to master
git checkout master
git merge hotfix/critical-fix

# 4. Push (triggers CI/CD)
git push origin master

# 5. Monitor deployment
watch -n 5 'curl -s https://blacklist.nxtd.co.kr/health | jq'
```

---

## 🛠️ Troubleshooting

### Issue: Build Failed in CI/CD

**Symptoms**: GitHub Actions job fails at build stage

**Diagnosis**:
```bash
# Check workflow run logs
# Go to: https://github.com/{repo}/actions

# Common errors:
# - "image not found" → Docker context issue
# - "authentication failed" → Registry credentials
# - "build timeout" → Large image size
```

**Solutions**:

1. **Docker context issue**:
   ```yaml
   # Fix in workflow
   context: ./app  # Ensure correct path
   dockerfile: ./app/Dockerfile
   ```

2. **Registry authentication**:
   ```bash
   # Verify secrets in GitHub
   # Settings → Secrets → Actions
   # Check: REGISTRY_HOST, REGISTRY_USER, REGISTRY_PASSWORD
   ```

3. **Build timeout**:
   ```yaml
   # Increase timeout in workflow
   timeout-minutes: 30  # Default: 360 (6 hours)
   ```

---

### Issue: Portainer Webhook Failed

**Symptoms**: Deployment triggered but containers not updated

**Diagnosis**:
```bash
# Check webhook response in GitHub Actions logs
# Look for: HTTP 204 (success) or error codes

# Common errors:
# - HTTP 404 → Webhook URL incorrect
# - HTTP 401 → Authentication failed
# - HTTP 500 → Portainer server error
```

**Solutions**:

1. **Verify webhook URL**:
   ```bash
   # Portainer → Stacks → blacklist → Webhook
   # Copy URL and update GitHub Secret
   # Format: https://portainer.jclee.me/api/stacks/webhooks/{id}
   ```

2. **Test webhook manually**:
   ```bash
   curl -X POST "https://portainer.jclee.me/api/stacks/webhooks/{id}"
   # Expected: HTTP 204 No Content
   ```

3. **Check Portainer logs**:
   ```bash
   docker logs portainer
   # Look for webhook trigger events
   ```

---

### Issue: Health Check Timeout

**Symptoms**: Deployment fails at health check stage

**Diagnosis**:
```bash
# Check container status
docker ps -a

# Check container logs
docker logs blacklist-app

# Test health endpoint
curl https://blacklist.nxtd.co.kr/health
```

**Solutions**:

1. **Container not running**:
   ```bash
   # Check why container stopped
   docker logs blacklist-app

   # Common issues:
   # - Database connection failed
   # - Redis connection failed
   # - Port already in use
   ```

2. **Database connection failed**:
   ```bash
   # Check postgres health
   docker exec blacklist-postgres pg_isready -U postgres

   # Test connection from app
   docker exec blacklist-app psql -h blacklist-postgres -U postgres -d blacklist -c "SELECT 1"
   ```

3. **Health endpoint not responding**:
   ```bash
   # Check if app is listening on port
   docker exec blacklist-app netstat -tlnp | grep 2542

   # Test internal health
   docker exec blacklist-app curl http://localhost:2542/health
   ```

---

### Issue: Image Pull Failed

**Symptoms**: Portainer cannot pull latest images

**Diagnosis**:
```bash
# Check registry status
curl https://registry.jclee.me/v2/_catalog

# Check image tags
curl https://registry.jclee.me/v2/blacklist-app/tags/list
```

**Solutions**:

1. **Registry unreachable**:
   ```bash
   # Check Synology NAS
   ssh admin@192.168.50.215
   docker ps | grep registry
   ```

2. **Image not pushed**:
   ```bash
   # Check GitHub Actions logs
   # Verify: "Push to Registry" step completed

   # Manually push if needed
   docker push registry.jclee.me/blacklist-app:latest
   ```

3. **Authentication issue**:
   ```bash
   # Update Portainer registry credentials
   # Portainer → Registries → Edit
   # Username: {REGISTRY_USER}
   # Password: {REGISTRY_PASSWORD}
   ```

---

## 📈 Performance Metrics

### Build Performance

**Parallel Build Strategy**:
- **Components**: 4 (postgres, redis, collector, app)
- **Max Parallel**: 4 (all build simultaneously)
- **Build Time**:
  - postgres: ~2-3 minutes
  - redis: ~1-2 minutes
  - collector: ~4-5 minutes (largest)
  - app: ~3-4 minutes
- **Total (Parallel)**: ~5-7 minutes (vs ~15 minutes sequential)

**Optimization Techniques**:
- ✅ BuildKit cache reuse
- ✅ Multi-stage Dockerfiles
- ✅ Parallel push (latest + commit-sha)
- ✅ Docker layer caching

### Deployment Performance

**Deployment Metrics**:
- **Webhook Trigger**: < 5 seconds
- **Image Pull**: ~30-60 seconds (depends on image size)
- **Container Restart**: ~30-45 seconds
- **Health Check**: ~15-30 seconds
- **Total Downtime**: ~1-2 minutes (rolling update)

### Image Sizes

| Image | Size (Uncompressed) | Size (Compressed) | Reduction |
|-------|---------------------|-------------------|-----------|
| **blacklist-postgres** | 261MB | 101MB | 61.9% |
| **blacklist-redis** | 39MB | 17MB | 60.3% |
| **blacklist-collector** | 1.45GB | 486MB | 67.8% |
| **blacklist-app** | 439MB | 144MB | 68.4% |
| **blacklist-frontend** | 201MB | 67MB | 67.4% |
| **Total** | ~2.4GB | ~815MB | 66% |

---

## 🔧 Maintenance

### Registry Cleanup

**Remove old images**:
```bash
# SSH to Synology NAS
ssh admin@192.168.50.215

# List images
docker exec registry registry garbage-collect /etc/docker/registry/config.yml

# Prune dangling images
docker image prune -f
```

### Log Rotation

**Container logs**:
```bash
# Configure in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Database Backup

**Automated backup** (recommended):
```bash
# Add to crontab
0 2 * * * docker exec blacklist-postgres pg_dump -U postgres blacklist > /backup/blacklist_$(date +\%Y\%m\%d).sql
```

**Manual backup**:
```bash
# Backup
docker exec blacklist-postgres pg_dump -U postgres blacklist > blacklist_backup.sql

# Restore
docker exec -i blacklist-postgres psql -U postgres blacklist < blacklist_backup.sql
```

---

## 📚 References

**Related Documentation**:
- `CLAUDE.md` - Project development guide
- `README.md` - Project overview
- `docs/IMAGE-PACKAGING-COMPLETE.md` - Offline deployment guide
- `.github/workflows/docker-build-portainer-deploy.yml` - CI/CD workflow

**External Resources**:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker BuildKit](https://docs.docker.com/build/buildkit/)
- [Portainer Documentation](https://docs.portainer.io/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

---

**Last Updated**: 2025-11-08
**Maintainer**: jclee
**Infrastructure Version**: 3.3.9
