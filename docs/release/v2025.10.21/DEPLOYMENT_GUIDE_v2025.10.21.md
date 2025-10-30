# Blacklist Management Platform - Deployment Guide v2025.10.21

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Air-Gap Offline Installation](#air-gap-offline-installation)
3. [Internet-Connected Installation](#internet-connected-installation)
4. [Initial Configuration](#initial-configuration)
5. [Service Verification](#service-verification)
6. [Common Issues & Solutions](#common-issues--solutions)
7. [Production Deployment Checklist](#production-deployment-checklist)

---

## Prerequisites

### Required Software
- **Docker:** Version 20.10 or higher
- **Docker Compose:** Version 2.0 or higher
- **Operating System:** Linux (Ubuntu 20.04+, RHEL 8+, CentOS 8+)

### Verify Docker Installation
```bash
docker --version
# Expected: Docker version 20.10.x or higher

docker compose version
# Expected: Docker Compose version v2.x.x or higher
```

### Hardware Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB free space
- Network: 100Mbps

**Recommended:**
- CPU: 8 cores
- RAM: 16GB
- Disk: 50GB free space (allows database growth)
- Network: 1Gbps

### Network Requirements

**Outbound Access (for data collection):**
- `https://regtech.fsec.or.kr` (REGTECH API)
- `https://rest.secudium.net` (SECUDIUM API)

**Inbound Access (for web UI):**
- Port 443 (HTTPS)
- Port 80 (HTTP redirect to HTTPS)
- Port 2542 (API - optional, can be internal only)

---

## Air-Gap Offline Installation

Use this method for environments **without internet access**.

### Step 1: Transfer Offline Package

**On Internet-Connected Machine:**
```bash
# Verify package integrity
sha256sum blacklist-complete-offline-20251021_111759.tar.gz
# Expected: 5818f6afc30a92237a94d2c27838db9fd40e2582f657f0a3b79d8c0a17b3ad2a

# Verify checksum file
sha256sum -c blacklist-complete-offline-20251021_111759.tar.gz.sha256
# Expected: blacklist-complete-offline-20251021_111759.tar.gz: OK
```

**Transfer to Air-Gap Environment:**
```bash
# Option 1: USB Drive
sudo mount /dev/sdb1 /mnt/usb
cp blacklist-complete-offline-20251021_111759.tar.gz /mnt/usb/
cp blacklist-complete-offline-20251021_111759.tar.gz.sha256 /mnt/usb/
sudo umount /mnt/usb

# Option 2: SCP (if internal network exists)
scp blacklist-complete-offline-20251021_111759.tar.gz user@target:/opt/
scp blacklist-complete-offline-20251021_111759.tar.gz.sha256 user@target:/opt/

# Option 3: Physical media burn
# Use standard file transfer methods appropriate for your environment
```

### Step 2: Extract Package

**On Target Air-Gap System:**
```bash
# Navigate to transfer location
cd /opt  # or wherever package was transferred

# Verify checksum again after transfer
sha256sum -c blacklist-complete-offline-20251021_111759.tar.gz.sha256

# Extract package
tar -xzf blacklist-complete-offline-20251021_111759.tar.gz

# Navigate into extracted directory
cd blacklist-complete-offline-20251021_111759

# Verify contents
ls -lh
# Expected directories:
# - docker-images/
# - python-packages/
# - scripts/
# - configs/
```

### Step 3: Load Docker Images

**Automated Installation:**
```bash
# Run installation script (loads all 6 images + installs Python packages)
chmod +x install.sh
./install.sh

# Expected output:
# ✅ Loading blacklist-postgres:latest...
# ✅ Loading blacklist-redis:latest...
# ✅ Loading blacklist-collector:latest...
# ✅ Loading blacklist-app:latest...
# ✅ Loading blacklist-frontend:latest...
# ✅ Loading blacklist-nginx:latest...
# ✅ Installing Python packages for app...
# ✅ Installing Python packages for collector...
# ✅ All images loaded successfully!
```

**Manual Installation (if script fails):**
```bash
# Load Docker images one by one
docker load -i docker-images/blacklist-postgres.tar
docker load -i docker-images/blacklist-redis.tar
docker load -i docker-images/blacklist-collector.tar
docker load -i docker-images/blacklist-app.tar
docker load -i docker-images/blacklist-frontend.tar
docker load -i docker-images/blacklist-nginx.tar

# Verify all images loaded
docker images | grep blacklist
# Expected: 6 images listed (postgres, redis, collector, app, frontend, nginx)
```

### Step 4: Configure Environment

```bash
# Create environment file from template
cp .env.example .env

# Edit configuration
vim .env  # or nano .env
```

**Required Configuration (`.env`):**
```bash
# Database Password (CHANGE THIS!)
POSTGRES_PASSWORD=your_secure_password_here

# REGTECH Credentials (obtain from https://regtech.fsec.or.kr)
REGTECH_ID=your_regtech_username
REGTECH_PW=your_regtech_password

# SECUDIUM Credentials (obtain from SECUDIUM provider)
SECUDIUM_ID=your_secudium_username
SECUDIUM_PW=your_secudium_password

# Application Settings (optional, defaults provided)
FLASK_ENV=production
PORT=2542
```

### Step 5: Start Services

```bash
# Start all containers
docker compose up -d

# Expected output:
# ✅ Network blacklist_blacklist-network created
# ✅ Volume blacklist_postgres_data created
# ✅ Volume blacklist_redis_data created
# ✅ Container blacklist-postgres Starting
# ✅ Container blacklist-redis Starting
# ✅ Container blacklist-postgres Healthy
# ✅ Container blacklist-redis Healthy
# ✅ Container blacklist-collector Starting
# ✅ Container blacklist-collector Healthy
# ✅ Container blacklist-app Starting
# ✅ Container blacklist-app Healthy
# ✅ Container blacklist-frontend Starting
# ✅ Container blacklist-nginx Starting (may fail if port 443 in use)
```

### Step 6: Verify Installation

```bash
# Check container status
docker compose ps

# Expected: 5-6 containers running and healthy
# (nginx may fail if port 443 conflicts, this is non-critical)

# Test health endpoint
curl http://localhost:2542/health

# Expected response:
# {
#   "status": "healthy",
#   "mode": "full",
#   "timestamp": "2025-10-21T..."
# }

# Test web UI (replace with your server IP)
curl -I http://localhost:80
# Expected: HTTP/1.1 301 Moved Permanently (redirect to HTTPS)

# Check database connectivity
docker exec blacklist-postgres pg_isready -U postgres -d blacklist
# Expected: /var/run/postgresql:5432 - accepting connections
```

---

## Internet-Connected Installation

Use this method for environments **with internet access**.

### Step 1: Clone Repository (if available)

```bash
# If deploying from Git repository
git clone <repository-url> blacklist-platform
cd blacklist-platform

# Or download release package
wget https://<release-url>/blacklist-v2025.10.21.tar.gz
tar -xzf blacklist-v2025.10.21.tar.gz
cd blacklist-v2025.10.21
```

### Step 2: Build Docker Images

```bash
# Build all images using docker compose
docker compose build

# Or build individually
docker build -t blacklist-postgres:latest -f postgres/Dockerfile postgres/
docker build -t blacklist-redis:latest -f redis/Dockerfile redis/
docker build -t blacklist-collector:latest -f collector/Dockerfile collector/
docker build -t blacklist-app:latest -f app/Dockerfile app/
docker build -t blacklist-frontend:latest -f frontend/Dockerfile frontend/
docker build -t blacklist-nginx:latest -f nginx/Dockerfile nginx/

# Verify images
docker images | grep blacklist
```

### Step 3: Configure Environment

```bash
# Create .env file
cp .env.example .env
vim .env

# Set required values (same as air-gap installation)
# POSTGRES_PASSWORD, REGTECH_ID, REGTECH_PW, SECUDIUM_ID, SECUDIUM_PW
```

### Step 4: Start Services

```bash
docker compose up -d
```

### Step 5: Verify Installation

```bash
# Same verification steps as air-gap installation
docker compose ps
curl http://localhost:2542/health
```

---

## Initial Configuration

### Database Initialization

**Automatic Initialization:**
- Database schema is automatically created on first startup
- Located in: `postgres/init-scripts/00-complete-schema.sql`
- Includes: tables, indexes, views, triggers, functions

**Verify Initialization:**
```bash
# Connect to database
docker exec -it blacklist-postgres psql -U postgres -d blacklist

# Check tables
\dt

# Expected tables:
# - blacklist_ips
# - whitelist_ips
# - collection_credentials
# - collection_history
# - fortinet_export_history
# - system_settings

# Check initial data
SELECT COUNT(*) FROM blacklist_ips;
SELECT COUNT(*) FROM whitelist_ips;
SELECT COUNT(*) FROM collection_credentials;

# Exit psql
\q
```

### Collection Credentials Configuration

**Option 1: Via Web UI (Recommended)**
```bash
# 1. Access collection panel
open https://192.168.50.100/collection-panel/
# or: curl https://192.168.50.100/collection-panel/

# 2. Navigate to "Credential Management" section
# 3. Enter REGTECH credentials
# 4. Enter SECUDIUM credentials
# 5. Click "Save" for each

# 6. Verify credentials saved
curl http://localhost:2542/api/collection/credentials/REGTECH | jq
curl http://localhost:2542/api/collection/credentials/SECUDIUM | jq
```

**Option 2: Via Database (Advanced)**
```bash
# Connect to database
docker exec -it blacklist-postgres psql -U postgres -d blacklist

# Insert or update REGTECH credentials
INSERT INTO collection_credentials (service_name, username, password, api_url, is_active)
VALUES ('REGTECH', 'your_username', 'your_password', 'https://regtech.fsec.or.kr', true)
ON CONFLICT (service_name)
DO UPDATE SET username = EXCLUDED.username, password = EXCLUDED.password;

# Insert or update SECUDIUM credentials
INSERT INTO collection_credentials (service_name, username, password, api_url, is_active)
VALUES ('SECUDIUM', 'your_username', 'your_password', 'https://rest.secudium.net', true)
ON CONFLICT (service_name)
DO UPDATE SET username = EXCLUDED.username, password = EXCLUDED.password;

# Verify
SELECT service_name, username, api_url, is_active FROM collection_credentials;

\q
```

### First Data Collection

**Manual Collection Trigger:**
```bash
# Trigger REGTECH collection
curl -X POST http://localhost:2542/api/collection/regtech/trigger

# Expected response:
# {
#   "status": "started",
#   "message": "REGTECH collection started in background",
#   "timestamp": "2025-10-21T..."
# }

# Trigger SECUDIUM collection
curl -X POST http://localhost:2542/api/collection/trigger/SECUDIUM

# Monitor collection progress
docker compose logs -f blacklist-collector

# Check collection history (after ~3-5 minutes)
curl http://localhost:2542/api/collection/history | jq

# Verify blacklist data loaded
curl "http://localhost:2542/api/blacklist/check?ip=1.1.1.1" | jq
```

---

## Service Verification

### Container Health Checks

```bash
# All containers should show "healthy" status
docker compose ps

# Individual health checks
docker exec blacklist-postgres pg_isready -U postgres -d blacklist
docker exec blacklist-redis redis-cli ping
docker exec blacklist-collector curl -f http://localhost:8545/health
docker exec blacklist-app curl -f http://localhost:2542/health

# Check container logs for errors
docker compose logs blacklist-app | grep -i error
docker compose logs blacklist-collector | grep -i error
docker compose logs blacklist-postgres | grep -i error
```

### API Endpoint Verification

```bash
# Health check
curl http://localhost:2542/health | jq

# Blacklist check
curl "http://localhost:2542/api/blacklist/check?ip=8.8.8.8" | jq

# Collection history
curl http://localhost:2542/api/collection/history | jq

# FortiGate export
curl "http://localhost:2542/api/fortinet/active-ips?page=1&per_page=10" | jq

# Statistics
curl http://localhost:2542/api/stats | jq
```

### Web UI Verification

```bash
# Test main pages (replace IP with your server)
curl -I https://192.168.50.100/
curl -I https://192.168.50.100/dashboard
curl -I https://192.168.50.100/collection-panel/
curl -I https://192.168.50.100/statistics

# All should return HTTP 200
```

### Prometheus Metrics

```bash
# Check metrics endpoint
curl http://localhost:2542/metrics

# Expected output includes:
# - blacklist_whitelist_hits_total
# - blacklist_check_total
# - collection_success_total
# - database_connection_pool_size
```

---

## Common Issues & Solutions

### Issue 1: Port 443 Already in Use

**Symptoms:**
```
Error: Cannot start service blacklist-nginx:
Bind for 0.0.0.0:443 failed: port is already allocated
```

**Diagnosis:**
```bash
sudo lsof -i :443
# Shows which process is using port 443
```

**Solutions:**

**Option A: Use Alternative Port**
```bash
# Edit docker-compose.yml
vim docker-compose.yml

# Change nginx ports section:
# FROM:
#   ports:
#     - "443:443"
#     - "80:80"
# TO:
#   ports:
#     - "8443:443"
#     - "8080:80"

# Restart
docker compose up -d blacklist-nginx
```

**Option B: Stop Conflicting Service**
```bash
# If Traefik is running
docker stop traefik-gateway

# Then start nginx
docker compose up -d blacklist-nginx
```

**Option C: Access Without nginx (Temporary)**
```bash
# Frontend is still accessible on internal port
# Expose blacklist-frontend port temporarily:

# Edit docker-compose.yml
# Add to blacklist-frontend service:
#   ports:
#     - "3000:2543"

docker compose up -d blacklist-frontend

# Access via http://localhost:3000
```

### Issue 2: Database Connection Failed

**Symptoms:**
```
could not translate host name "blacklist-postgres" to address:
Name or service not known
```

**Diagnosis:**
```bash
# Check if postgres container is running
docker ps | grep blacklist-postgres

# Check if postgres is healthy
docker compose ps blacklist-postgres

# Inspect network
docker network inspect blacklist_blacklist-network
```

**Solution:**
```bash
# Restart all containers to recreate network
docker compose down
docker compose up -d

# Wait for postgres health check (45-90 seconds)
docker compose logs -f blacklist-postgres

# Verify connection
docker exec blacklist-postgres pg_isready -U postgres -d blacklist
```

### Issue 3: Collection Fails with Authentication Error

**Symptoms:**
```
REGTECH authentication failed: Invalid credentials
SECUDIUM token generation failed
```

**Diagnosis:**
```bash
# Check credentials in database
docker exec blacklist-postgres psql -U postgres -d blacklist -c \
  "SELECT service_name, username, api_url, is_active FROM collection_credentials;"

# Check environment variables
docker exec blacklist-collector env | grep -E "(REGTECH|SECUDIUM)"
```

**Solution:**
```bash
# Update credentials via API
curl -X PUT http://localhost:2542/api/collection/credentials/REGTECH \
  -H "Content-Type: application/json" \
  -d '{
    "username": "correct_username",
    "password": "correct_password",
    "is_active": true
  }'

# Or update in database directly
docker exec -it blacklist-postgres psql -U postgres -d blacklist
UPDATE collection_credentials
SET username='correct_user', password='correct_pass'
WHERE service_name='REGTECH';
\q

# Retry collection
curl -X POST http://localhost:2542/api/collection/regtech/trigger
```

### Issue 4: Web UI Shows "No Data"

**Symptoms:**
- Dashboard loads but shows 0 IPs
- Statistics page empty
- Collection history empty

**Diagnosis:**
```bash
# Check if database has data
docker exec blacklist-postgres psql -U postgres -d blacklist -c \
  "SELECT COUNT(*) as total,
          COUNT(*) FILTER (WHERE is_active=true) as active
   FROM blacklist_ips;"

# Check collection history
docker exec blacklist-postgres psql -U postgres -d blacklist -c \
  "SELECT service_name, collection_date, items_collected, success
   FROM collection_history
   ORDER BY collection_date DESC LIMIT 5;"
```

**Solution:**
```bash
# Trigger manual collection
curl -X POST http://localhost:2542/api/collection/regtech/trigger
curl -X POST http://localhost:2542/api/collection/trigger/SECUDIUM

# Monitor collector logs
docker compose logs -f blacklist-collector

# Wait 3-5 minutes for completion
sleep 300

# Verify data loaded
docker exec blacklist-postgres psql -U postgres -d blacklist -c \
  "SELECT COUNT(*) FROM blacklist_ips WHERE is_active=true;"
```

### Issue 5: Slow API Responses

**Symptoms:**
- API requests take >2 seconds
- Dashboard loading slow
- Database queries timing out

**Diagnosis:**
```bash
# Check Redis connection
docker exec blacklist-redis redis-cli ping
# Expected: PONG

# Check database connection pool
curl http://localhost:2542/metrics | grep "database_connection_pool"

# Check container resources
docker stats blacklist-app blacklist-postgres blacklist-redis
```

**Solution:**
```bash
# Restart Redis if not responding
docker compose restart blacklist-redis

# Check PostgreSQL performance
docker exec blacklist-postgres psql -U postgres -d blacklist -c \
  "SELECT schemaname, tablename, indexname
   FROM pg_indexes
   WHERE tablename IN ('blacklist_ips', 'whitelist_ips');"

# If indexes missing, rebuild database
docker compose down
docker volume rm blacklist_postgres_data
docker compose up -d
# Database will reinitialize with all indexes
```

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] **Hardware meets requirements** (4+ cores, 8GB+ RAM, 20GB+ disk)
- [ ] **Docker installed and tested** (version 20.10+)
- [ ] **Network ports available** (443, 80, optionally 2542)
- [ ] **Outbound HTTPS allowed** (for REGTECH/SECUDIUM APIs)
- [ ] **SSL certificates prepared** (for nginx HTTPS)
- [ ] **Credentials obtained** (REGTECH, SECUDIUM)
- [ ] **Offline package verified** (checksum matches)

### Deployment

- [ ] **Extract offline package** or clone repository
- [ ] **Load Docker images** (all 6 images loaded successfully)
- [ ] **Configure .env file** (all required variables set)
- [ ] **Start containers** (`docker compose up -d`)
- [ ] **Verify all containers healthy** (`docker compose ps`)
- [ ] **Database initialized** (schema created, tables exist)
- [ ] **Credentials configured** (via UI or database)
- [ ] **First collection successful** (REGTECH and/or SECUDIUM)

### Post-Deployment Verification

- [ ] **Health check passes** (`/health` returns healthy)
- [ ] **API endpoints working** (blacklist check, collection history)
- [ ] **Web UI accessible** (home, dashboard, collection panel, statistics)
- [ ] **Database has data** (blacklist_ips count > 0)
- [ ] **Whitelist priority works** (test with known IP)
- [ ] **FortiGate export works** (active IPs endpoint returns data)
- [ ] **Metrics endpoint working** (`/metrics` returns Prometheus data)
- [ ] **Logs collecting properly** (no critical errors in logs)

### Security Hardening

- [ ] **Change default passwords** (POSTGRES_PASSWORD)
- [ ] **Restrict external access** (firewall rules for ports 443, 80)
- [ ] **Enable HTTPS only** (HTTP redirects to HTTPS)
- [ ] **Rotate credentials** (REGTECH, SECUDIUM passwords)
- [ ] **Enable monitoring** (Grafana/Prometheus integration)
- [ ] **Configure backups** (database backup schedule)
- [ ] **Set up alerts** (collection failures, API errors)

### Operational Readiness

- [ ] **Backup procedure documented** (database backup/restore tested)
- [ ] **Monitoring configured** (Grafana dashboards created)
- [ ] **Alerting configured** (Slack/email notifications)
- [ ] **On-call procedures defined** (escalation path)
- [ ] **Runbook created** (common issues and solutions)
- [ ] **Team trained** (operations team familiar with system)

---

## Rollback Procedure

If deployment fails or issues arise:

### Quick Rollback

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: destroys data)
docker volume rm blacklist_postgres_data
docker volume rm blacklist_redis_data

# Restore from previous working version
# (load previous Docker images or restore database backup)

# Restart with previous version
docker compose up -d
```

### Database-Only Rollback

```bash
# Stop application containers (keep database running)
docker compose stop blacklist-app blacklist-collector blacklist-frontend

# Restore database from backup
cat backup_previous.sql | docker exec -i blacklist-postgres psql -U postgres -d blacklist

# Restart application containers
docker compose start blacklist-app blacklist-collector blacklist-frontend
```

---

## Next Steps

After successful deployment:

1. **Configure Automated Collections:**
   - Set collection schedule in collector configuration
   - Verify scheduled collections run successfully
   - Monitor collection_history table

2. **Integrate with Monitoring:**
   - Configure Prometheus scraping
   - Create Grafana dashboards
   - Set up alert rules

3. **Configure Whitelist:**
   - Add whitelisted IPs to whitelist
   - Test whitelist priority logic
   - Document whitelist management process

4. **Integrate with FortiGate:**
   - Configure FortiGate to pull blocklist
   - Test firewall rule application
   - Set up automated sync schedule

5. **Train Operations Team:**
   - Review API documentation
   - Practice common troubleshooting scenarios
   - Test backup and restore procedures

---

## Support

For issues during deployment:

1. **Check logs:** `docker compose logs <service-name>`
2. **Review this guide:** Common Issues & Solutions section
3. **Verify system health:** Run verification commands
4. **Consult documentation:** CLAUDE.md, README.md
5. **Check release notes:** Known issues documented

---

**END OF DEPLOYMENT GUIDE**
