# ============================================================================
# Blacklist Redis Cache Service - Container Image
# ============================================================================
# Purpose: High-performance in-memory cache and rate limiting storage
# Version: 3.3.9
# Base Image: Redis 7.x on Alpine Linux
# Dependencies: None (standalone service)
# Used By: blacklist-app (Flask-Limiter), blacklist-collector (cache)
# ============================================================================
FROM redis:7-alpine

# ============================================================================
# Build Arguments (Secure Configuration)
# ============================================================================
ARG VERSION
ARG BUILD_DATE
ARG REDIS_PASSWORD
ARG REDIS_HOST
ARG REDIS_PORT
ARG REDIS_MAX_MEMORY
ARG REDIS_MAX_MEMORY_POLICY

# ============================================================================
# Container Metadata Labels
# ============================================================================
LABEL version=${VERSION}
LABEL build_date=${BUILD_DATE}
LABEL description="Redis 7 cache for Blacklist Management System v3.3.9"
LABEL maintainer="qws941"

# Removed Watchtower labels - Using Portainer-only deployment

# Container management labels (Portainer controlled)
LABEL com.docker.compose.project=blacklist
LABEL com.docker.compose.service=redis

# ============================================================================
# Environment Variables Configuration
# ============================================================================
# Redis Configuration:
# - Password: Optional authentication (if REDIS_PASSWORD set)
# - Max Memory: 256MB (default), eviction policy: allkeys-lru
# - Persistence: RDB snapshots (900s/1key, 300s/10keys, 60s/10000keys)
# - TCP Keep-Alive: 300s
# - Logging: notice level
#
# Performance Optimization:
# - vm.overcommit_memory = 1: Prevent OOM (Out of Memory) issues
# - net.core.somaxconn = 1024: Increase connection queue size
# ============================================================================
ENV REDIS_PASSWORD=${REDIS_PASSWORD} \
    REDIS_HOST=${REDIS_HOST:-blacklist-redis} \
    REDIS_PORT=${REDIS_PORT:-6379} \
    REDIS_MAX_MEMORY=${REDIS_MAX_MEMORY:-256mb} \
    REDIS_MAX_MEMORY_POLICY=${REDIS_MAX_MEMORY_POLICY:-allkeys-lru} \
    TZ=Asia/Seoul \
    # Performance settings
    REDIS_SAVE_FREQUENCY="900 1 300 10 60 10000" \
    REDIS_TCP_KEEPALIVE=300 \
    REDIS_TIMEOUT=0 \
    # Security settings
    REDIS_PROTECTED_MODE=yes \
    REDIS_BIND="127.0.0.1 ::1" \
    # Logging settings
    REDIS_LOGLEVEL=notice \
    REDIS_LOGFILE="/var/log/redis/redis-server.log"

# ============================================================================
# Redis Configuration File
# ============================================================================
# Custom redis.conf with:
# - Memory management (maxmemory, eviction policy)
# - Persistence settings (RDB snapshots, AOF)
# - Security settings (requirepass, protected mode)
# - Performance tuning (tcp-keepalive, timeout)
# ============================================================================
COPY redis.conf /usr/local/etc/redis/redis.conf

# ============================================================================
# System Optimization for Redis Performance
# ============================================================================
# Kernel parameters:
# - vm.overcommit_memory = 1: Allow memory overcommit (required for Redis)
# - net.core.somaxconn = 1024: Increase max backlog for TCP connections
#
# Note: These settings may require host-level sysctl configuration for full effect
# ============================================================================
RUN set -e && \
    echo "🔍 Optimizing system for Redis..." && \
    echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf && \
    echo 'net.core.somaxconn = 1024' >> /etc/sysctl.conf && \
    echo "✅ System optimization completed"

# ============================================================================
# Data Directory Configuration
# ============================================================================
# Create /data directory for RDB snapshots and AOF logs
# Set ownership to redis user for security
# ============================================================================
RUN mkdir -p /data && \
    chown redis:redis /data

# ============================================================================
# Build-Time Validation and Summary
# ============================================================================
RUN set -e && \
    echo "" && \
    echo "====================================" && \
    echo "📋 Redis Build Summary" && \
    echo "====================================" && \
    echo "Redis version: $(redis-server --version | head -1)" && \
    echo "Configuration: /usr/local/etc/redis/redis.conf" && \
    echo "====================================" && \
    echo "✅ Redis v3.3.9 embedded in image" && \
    echo "💾 Max memory: ${REDIS_MAX_MEMORY:-256mb}" && \
    echo "🔒 Eviction policy: ${REDIS_MAX_MEMORY_POLICY:-allkeys-lru}" && \
    echo "💾 Persistence: RDB snapshots enabled" && \
    echo "====================================" && \
    echo ""

# ============================================================================
# Volume Configuration
# ============================================================================
# /data: Persistent storage for RDB snapshots and AOF logs
# Ensures data survives container restarts
# ============================================================================
VOLUME ["/data"]

# ============================================================================
# Network Port Configuration
# ============================================================================
# Port 6379: Redis server (standard port)
# ============================================================================
EXPOSE 6379

# ============================================================================
# Health Check Configuration
# ============================================================================
# Redis PING command check
# - interval: 30s (check every 30 seconds)
# - timeout: 10s (fail if no response in 10s)
# - start-period: 5s (grace period for startup)
# - retries: 3 (mark unhealthy after 3 consecutive failures)
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD redis-cli ping || exit 1

# ============================================================================
# Default Command: Start Redis Server
# ============================================================================
# Use custom redis.conf for production configuration
# ============================================================================
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]