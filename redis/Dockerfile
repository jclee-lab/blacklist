# 🔄 Blacklist Redis Cache Service
FROM redis:7-alpine

# Build arguments for secure configuration (종속성 해결)
ARG VERSION
ARG BUILD_DATE
ARG REDIS_PASSWORD
ARG REDIS_HOST
ARG REDIS_PORT
ARG REDIS_MAX_MEMORY
ARG REDIS_MAX_MEMORY_POLICY

LABEL version=${VERSION}
LABEL build_date=${BUILD_DATE}
LABEL description="Redis 7 cache for Blacklist Management System"
LABEL maintainer="qws941"

# Removed Watchtower labels - Using Portainer-only deployment

# Container management labels (Portainer controlled)
LABEL com.docker.compose.project=blacklist
LABEL com.docker.compose.service=redis

# Set environment variables from build arguments (종속성 해결)
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

# Copy Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# System optimization for Redis performance
RUN echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf && \
    echo 'net.core.somaxconn = 1024' >> /etc/sysctl.conf

# Create Redis data directory
RUN mkdir -p /data && \
    chown redis:redis /data

# Define volume for Redis data persistence
VOLUME ["/data"]

# Expose Redis port (표준 포트 사용)
EXPOSE 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD redis-cli ping || exit 1

# Use custom configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]