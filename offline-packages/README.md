# Offline Deployment Packages

## 📦 Quick Start (2-File Method)

**Simplest deployment - only need 2 files:**

```bash
# 1. Copy to target machine
scp blacklist.tar.gz install.sh user@target:/path/

# 2. Install (with network validation)
bash install.sh

# 3. Air-gap install (skip network checks)
bash install.sh --skip-network-check
```

---

## 📁 Directory Structure

### Root Level (Main Deployment)
- `blacklist.tar.gz` (813M) - Main deployment package (6 Docker images)
- `blacklist.tar.gz.sha256` - Checksum for integrity verification
- `install.sh` (20K) - Automated installation script
- `docker-compose.yml` - Reference configuration

### packages/ (Alternative Deployments)
- `blacklist-nginx.tar.gz` (834M) - All-in-one with nginx (no Traefik)
- `traefik-offline.tar.gz` (48M) - Separate Traefik deployment
- `install-nginx.sh` - Nginx deployment installer
- `install-traefik.sh` - Traefik deployment installer
- Checksums (*.sha256)

### scripts/ (Utilities)
- `air-gap-fix-all.sh` - Comprehensive air-gap environment fixes
- `fix-all-http-to-https.sh` - HTTP to HTTPS migration
- `fix-https-ports.sh` - HTTPS port configuration
- `manual-trigger-guide.sh` - Interactive collection trigger
- `verify-fortigate-connection.sh` - FortiGate connectivity test

### patches/ (Runtime Fixes)
- `patch-master.sh` - Patch orchestrator (auto/interactive mode)
- `000-master-regtech-fix.sh` - REGTECH authentication fix
- `001-005-*.sh` - Individual patches
- See `patches/README.md` for details

### docs/ (Documentation)
- `TRAEFIK-INSTALL-GUIDE.md` - Traefik deployment guide
- `TRAEFIK-QUICKSTART.txt` - Quick reference

---

## 🚀 Installation Methods

### Method 1: Standard (Recommended)
```bash
bash install.sh
# - Validates REGTECH/SECUDIUM connectivity
# - Automatic health checks
# - 6 API endpoint validations
```

### Method 2: Air-Gap
```bash
bash install.sh --skip-network-check
# - Skips external API validation
# - For isolated environments
```

### Method 3: Nginx (No Traefik)
```bash
tar -xzf packages/blacklist-nginx.tar.gz
cd blacklist-nginx/
bash install-nginx.sh
```

### Method 4: Traefik First
```bash
# Step 1: Deploy Traefik
tar -xzf packages/traefik-offline.tar.gz
cd traefik-offline/
mkdir -p certs/ssl && cp nxtd.{crt,key} certs/ssl/
bash install-traefik.sh

# Step 2: Deploy Blacklist (with Traefik labels)
cd ..
bash install.sh
```

---

## 📝 Package Contents

### blacklist.tar.gz (Main Package)
- **Docker Images** (6): app, collector, postgres, redis, frontend, nginx
- **Database**: 14 SQL migrations
- **Configuration**: docker-compose.yml, .env.example
- **Total Size**: 1.7GB → 813MB compressed

### blacklist-nginx.tar.gz (Nginx Bundle)
- All-in-one deployment with nginx
- No Traefik dependency
- Port 443/80 direct exposure
- **Total Size**: 834MB

### traefik-offline.tar.gz (Traefik Only)
- Separate reverse proxy deployment
- NXTD certificate support
- Multi-service routing
- **Total Size**: 48MB

---

## 🔧 Runtime Patches

Apply fixes without image rebuild:

```bash
cd patches/

# Auto mode (production)
bash patch-master.sh --auto

# Interactive mode
bash patch-master.sh
# → [1] Run all patches
# → [4] Verify system
```

**Available patches:**
- Database migrations (013-014)
- CSRF exemptions
- REGTECH authentication fixes
- Air-gap compatibility

---

## ✅ Verification

```bash
# Integrity check
sha256sum -c blacklist.tar.gz.sha256

# Post-install validation
curl http://localhost:2542/health
docker compose ps
```

---

## 📊 File Sizes

| File | Size | Purpose |
|------|------|---------|
| blacklist.tar.gz | 813M | Main package |
| blacklist-nginx.tar.gz | 834M | Nginx bundle |
| traefik-offline.tar.gz | 48M | Traefik only |
| install.sh | 20K | Installer |

**Total offline capability**: ~1.7GB (all packages combined)

---

## 🆕 Recent Updates (v3.3.8)

- ✅ Smart patch detection (skip already-applied)
- ✅ Traefik HTTPS-only configuration
- ✅ Credential initialization UX improvements
- ✅ Air-gap environment fixes
- ✅ Monitoring scheduler HTTPS support

---

**Version**: 3.3.8
**Last Updated**: 2025-10-30
**Maintainer**: jclee
