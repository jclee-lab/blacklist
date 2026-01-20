# ============================================================================
# Blacklist Data Collector Service - Container Image
# ============================================================================
# Purpose: REGTECH/SECUDIUM automated data collection service
# Version: 3.3.9
# Architecture: Single-stage build with Playwright headless browser
# Dependencies: PostgreSQL 15, Redis 7, Python 3.9
# ============================================================================
FROM python:3.9-slim

# ============================================================================
# Build Arguments (Secure Credential Injection)
# ============================================================================
# Passed from GitHub Secrets → Docker build → Environment variables
ARG VERSION
ARG BUILD_DATE
ARG GIT_COMMIT
# Database configuration (dependency: blacklist-postgres)
ARG POSTGRES_HOST
ARG POSTGRES_PORT
ARG POSTGRES_DB
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
# Redis configuration (dependency: blacklist-redis)
ARG REDIS_HOST
ARG REDIS_PORT
# REGTECH API credentials
ARG REGTECH_ID
ARG REGTECH_PW
ARG REGTECH_BASE_URL

# ============================================================================
# Container Metadata Labels
# ============================================================================
LABEL version=${VERSION}
LABEL build_date=${BUILD_DATE}
LABEL git.commit=${GIT_COMMIT:-unknown}
LABEL description="Blacklist Data Collector Service v3.3.9"
LABEL maintainer="qws941"

# Removed Watchtower labels - Using Portainer-based deployment

# Container management labels (Portainer controlled)
LABEL com.docker.compose.project=blacklist
LABEL com.docker.compose.service=collector

# Working directory
WORKDIR /app

# ============================================================================
# System Dependencies Installation
# ============================================================================
# Install system packages for:
# 1. PostgreSQL client (postgresql-client)
# 2. Playwright browser dependencies (libnss3, libnspr4, etc.)
# 3. Build tools (gcc, libpq-dev) for Python package compilation
# 4. Utilities (curl, wget, vim) for debugging
#
# Playwright Dependencies Required:
# - libnss3, libnspr4: Network Security Services
# - libatk*, libcups2, libdrm2: Rendering libraries
# - libxkbcommon0, libxcomposite1, libxdamage1: X11 support
# - libgbm1, libpango-1.0-0, libcairo2: Graphics
# - libasound2, libatspi2.0-0: Audio/Accessibility
# ============================================================================
RUN set -e && \
    echo "🔍 Installing system dependencies..." && \
    apt-get update && apt-get install -y \
        postgresql-client \
        curl \
        wget \
        vim \
        gcc \
        libpq-dev \
        # Playwright dependencies for headless browser (Chromium)
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        && rm -rf /var/lib/apt/lists/* && \
    echo "✅ System dependencies installed"

# ============================================================================
# Python Dependencies Installation
# ============================================================================
# Key dependencies (from requirements.txt):
# - playwright: Headless browser automation for REGTECH web scraping
# - psycopg2-binary: PostgreSQL database adapter
# - redis: Redis cache client
# - requests, beautifulsoup4: HTTP client and HTML parsing
# - APScheduler: Scheduled collection tasks
# ============================================================================
COPY collector/requirements.txt .

# Install Python dependencies with progress logging
RUN set -e && \
    echo "🔍 Installing Python dependencies..." && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "✅ Python dependencies installed" && \
    echo "📦 Installed packages:" && \
    pip list | head -20

# ============================================================================
# Collector Source Code
# ============================================================================
# Flattened structure copy
# 1. Copy core packages to root /app (siblings to collector)
COPY collector/core/ /app/core/
COPY collector/utils/ /app/utils/

# 2. Copy collector service files to /app/collector
# This preserves the 'collector' package namespace
COPY collector/*.py /app/collector/

# ============================================================================
# Environment Variables Configuration
# ============================================================================
# Service Dependencies:
# - blacklist-postgres: Database storage (POSTGRES_*)
# - blacklist-redis: Cache and rate limiting (REDIS_*)
# - regtech.fsec.or.kr: External data source (REGTECH_*)
# ============================================================================
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    # Database Configuration (dependency: blacklist-postgres)
    POSTGRES_HOST=${POSTGRES_HOST:-blacklist-postgres} \
    POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    POSTGRES_DB=${POSTGRES_DB:-blacklist} \
    POSTGRES_USER=${POSTGRES_USER:-postgres} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    # Redis Configuration (dependency: blacklist-redis)
    REDIS_HOST=${REDIS_HOST:-blacklist-redis} \
    REDIS_PORT=${REDIS_PORT:-6379} \
    # REGTECH API Configuration
    REGTECH_ID=${REGTECH_ID} \
    REGTECH_PW=${REGTECH_PW} \
    REGTECH_BASE_URL=${REGTECH_BASE_URL:-https://regtech.fsec.or.kr} \
    # Collector specific settings
    COLLECTOR_PORT=8545 \
    LOG_LEVEL=INFO

# Create logs directory
RUN mkdir -p /app/logs

# Set execution permissions for collector scripts
RUN chmod +x /app/collector/run_collector.py

# ============================================================================
# Build-Time Validation and Summary
# ============================================================================
RUN set -e && \
    echo "" && \
    echo "====================================" && \
    echo "📋 Collector Build Summary" && \
    echo "====================================" && \
    echo "Collector modules: $(find /app/collector -name "*.py" -type f 2>/dev/null | wc -l) files" && \
    echo "Core utilities: $(find /app/core -name "*.py" -type f 2>/dev/null | wc -l) files" && \
    echo "API endpoints: $(find /app/api -name "*.py" -type f 2>/dev/null | wc -l) files" && \
    echo "====================================" && \
    echo "✅ Collector v3.3.9 embedded in image" && \
    echo "🌐 Playwright Chromium: Installed" && \
    echo "🔗 Dependencies: PostgreSQL 15, Redis 7" && \
    echo "📡 Data sources: REGTECH, SECUDIUM" && \
    echo "====================================" && \
    echo ""

# ============================================================================
# Network Port Configuration
# ============================================================================
# Port 8545: Health check and status API
# ============================================================================
EXPOSE 8545

# ============================================================================
# Health Check Configuration
# ============================================================================
# HTTP health check endpoint: GET /health
# - interval: 30s (check every 30 seconds)
# - timeout: 10s (fail if no response in 10s)
# - start-period: 10s (grace period for startup)
# - retries: 3 (mark unhealthy after 3 consecutive failures)
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8545/health || exit 1

# ============================================================================
# Default Command: Run Collector
# ============================================================================
# run_collector.py responsibilities:
# - Orchestrate Scheduler + Health Server
# - Manage process lifecycle
# ============================================================================
CMD ["python", "-m", "collector.run_collector"]