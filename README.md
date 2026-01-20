# 🛡️ REGTECH Blacklist Intelligence Platform

> **✅ REPOSITORY MIGRATED TO GITLAB**
>
> This repository is actively maintained on **GitLab**: `https://gitlab.<YOUR_DOMAIN>/nextrade/blacklist`
>
> ```bash
> # Optimized SSH Clone (Port 2022)
> git clone git@gitlab.<YOUR_DOMAIN>:nextrade/blacklist.git
> ```

[![🤖 OpenCode AI Integration](https://img.shields.io/badge/OpenCode%20AI-Automated-blue)](https://OpenCode.ai/code)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A comprehensive Flask-based threat intelligence platform that collects, manages, and analyzes IP blacklist data from the **Korean Financial Security Institute (REGTECH)**. Features automated collection pipelines, real-time monitoring, comprehensive API/web interfaces, and production-ready deployment with **Traefik v3** orchestration.

## 🚀 Quick Start

### Optimized SSH Clone
The repository is optimized for SSH access via port **2022**. If you have configured your SSH global settings as provided, you can clone using:

```bash
# 1. Clone with LFS support (important for images)
git clone git@gitlab.<YOUR_DOMAIN>:nextrade/blacklist.git
cd blacklist

# 2. Ensure LFS binaries are downloaded
git lfs install
git lfs pull
```

### Start Services (Production-ready)
```bash
# Start all services with Traefik v3 orchestration
make dev

# View all service logs
make logs

# Check service health
make health

# Stop all services
make down
```

## 🛠️ Development Workflow

### Hot Reload Development

Code changes automatically reflect in running containers:

```bash
# Start with hot reload (rebuilds changed images + mounts source)
make dev

# Quick rebuild single service
make dev-app       # Backend API only
make dev-frontend  # Frontend only

# Start without rebuild (faster, uses cached images)
make dev-no-build

# Production-like (no hot reload, no source mounts)
make dev-prod
```

### What Gets Hot-Reloaded

| Service | Hot Reload | Rebuild Required |
|---------|------------|------------------|
| **app** | `app/core/`, `app/run_app.py` | `requirements.txt`, Dockerfile |
| **collector** | `collector/core/`, `run_collector.py` | `requirements.txt`, Dockerfile |
| **frontend** | `app/`, `components/`, `lib/` | `package.json`, Dockerfile |

### First-Time Setup

```bash
# Generate SSL certificates for local HTTPS
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/server.key -out ssl/server.crt \
  -subj "/CN=localhost"
chmod 644 ssl/server.key

# Start development environment
make dev
```

## 🌟 Key Features

### 🔄 **Automated REGTECH Data Collection**
- **REGTECH Integration**: Direct connection to Korean Financial Security Institute portal.
- **Excel Processing**: Advanced pandas-based parsing for threat intelligence.
- **Scheduling**: Automated collection intervals with smart retry mechanisms.
- **Authentication**: Secure two-stage encrypted authentication.

### 📊 **Intelligence Dashboard**
- **Real-time Statistics**: Live metrics, IP counts, and collection history.
- **FortiGate Integration**: Real-time **Request Logs** (Pull Logs) from security devices.
- **Redis Caching**: High-performance API responses using Redis-backed caching.
- **Interactive Web UI**: Next.js 15 based modern frontend.

### 📦 **Air-Gap Deployment (v3.1)**
- **Self-contained Package**: `blacklist-airgap-v3.tar.gz` includes all 6 Docker images.
- **Traefik v3 Integration**: Modern reverse proxy with automated SSL (.pem) support.
- **Bind Mounts**: Local data persistence in `dist/data/` for easier backups.
- **One-click Deploy**: `./deploy-airgap.sh` automates image loading and container startup.

## 🏗️ Architecture Overview

```
https://blacklist.<YOUR_DOMAIN>
  ↓
Traefik v3.0 (Reverse Proxy / SSL)
  ↓
├── 🐳 blacklist-frontend (Next.js 15, Port 2543)
├── 🐳 blacklist-app (Flask API, Port 2542)
├── 🐳 blacklist-collector (REGTECH Collector, Port 8545)
├── 🗄️ blacklist-postgres (PostgreSQL 15)
└── 🔄 blacklist-redis (Redis 7 Cache)
```

## 📦 Air-Gap Deployment (Offline)

For environments without internet access:

```bash
# 1. Download/Transfer package
# blacklist-airgap-v3.tar.gz (approx. 854MB)

# 2. Extract and Deploy
tar -xzf blacklist-airgap-v3.tar.gz
cd dist
chmod +x deploy-airgap.sh
./deploy-airgap.sh
```

**Requirements:** Docker & Docker Compose V2 only.

## 🔧 Configuration

### 🔐 Credential Management
Credentials for REGTECH are managed securely via the Web UI:
1. Access: `https://blacklist.<YOUR_DOMAIN>/settings`
2. Navigate to **인증정보 설정** (Credential Settings).
3. Credentials are **AES-256-GCM encrypted** using the `CREDENTIAL_MASTER_KEY.txt`.

## 📖 API Documentation

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/api/stats` | GET | Dashboard statistics (Cached) |
| `/api/blacklist/list` | GET | Paginated threat intelligence data |
| `/api/fortinet/pull-logs` | GET | FortiGate device request history |
| `/api/monitoring/metrics` | GET | Internal performance metrics |

---

## 🎯 Version Information
- **Current Version**: 3.1.0 (December 2025)
- **Status**: Production Stable
- **Maintenance**: SECUDIUM support removed; REGTECH focus.

<div align="center">
  Built with ❤️ for cybersecurity professionals.
</div>
