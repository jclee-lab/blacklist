# 🛡️ Blacklist Intelligence Platform

[![GitHub Release](https://img.shields.io/github/v/release/jclee-homelab/blacklist)](https://github.com/jclee-homelab/blacklist/releases/latest)
[![Docker](https://img.shields.io/badge/Docker-5%20Images-blue)](#architecture)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Wiki](https://img.shields.io/badge/Docs-Wiki-orange)](https://github.com/jclee-homelab/blacklist/wiki)

Threat intelligence platform for collecting, managing, and analyzing IP blacklist data from the **Korean Financial Security Institute (REGTECH)**.

## Features

| Feature | Description |
|---------|-------------|
| **REGTECH Integration** | Automated data collection from Korean Financial Security Institute |
| **Real-time Dashboard** | Next.js 15 frontend with live metrics and FortiGate logs |
| **Air-Gap Deployment** | Self-contained Docker bundles for offline environments |
| **Secure Credentials** | AES-256-GCM encrypted authentication |

## Quick Start

### Download & Install

```bash
# GitHub CLI
gh release download --repo jclee-homelab/blacklist
tar -xzf blacklist-*.tar.gz && ./install.sh

# curl (auto-detect latest)
TAG=$(curl -s "https://api.github.com/repos/jclee-homelab/blacklist/releases/latest" | jq -r ".tag_name")
curl -#L "https://github.com/jclee-homelab/blacklist/releases/download/$TAG/blacklist-$TAG-airgap.tar.gz" -o "blacklist-$TAG-airgap.tar.gz"

# PowerShell (direct internet access)
$TAG = (Invoke-RestMethod "https://api.github.com/repos/jclee-homelab/blacklist/releases/latest").tag_name
curl.exe -sL "https://github.com/jclee-homelab/blacklist/releases/download/$TAG/blacklist-$TAG-airgap.tar.gz" -o "blacklist-$TAG-airgap.tar.gz"

# PowerShell (air-gapped network via jump host)
.\download.ps1
```

### Development

```bash
make dev          # Start all services (hot reload)
make logs         # View logs
make down         # Stop services
```

## Architecture

```
https://blacklist.<YOUR_DOMAIN>
  │
  ├─ Traefik v3.0 (Reverse Proxy / SSL)
  │
  ├─ blacklist-frontend   (Next.js 15)     :2543
  ├─ blacklist-app        (Flask API)      :2542
  ├─ blacklist-collector  (REGTECH ETL)    :8545
  ├─ blacklist-postgres   (PostgreSQL 15)  :5432
  └─ blacklist-redis      (Redis 7)        :6379
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/stats` | Dashboard statistics |
| `GET /api/blacklist/list` | Paginated blacklist data |
| `GET /api/collection/status` | Collector status |

Full documentation: [API Reference](https://github.com/jclee-homelab/blacklist/wiki/API-Reference)

## Documentation

- [Installation Guide](https://github.com/jclee-homelab/blacklist/wiki/Installation)
- [Air-Gap Deployment](https://github.com/jclee-homelab/blacklist/wiki/Air-Gap-Deployment)
- [Development Guide](https://github.com/jclee-homelab/blacklist/wiki/Development)
- [Configuration](https://github.com/jclee-homelab/blacklist/wiki/Configuration)
- [Troubleshooting](https://github.com/jclee-homelab/blacklist/wiki/Troubleshooting)

## Version

**v3.5.10** (February 2026) - Production Stable

[Releases](https://github.com/jclee-homelab/blacklist/releases) · [Changelog](CHANGELOG.md)
