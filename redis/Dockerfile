# Redis 7 - Blacklist Intelligence Platform (cache-only, no persistence)
FROM redis:7-alpine

LABEL maintainer="NextRade <dev@jclee.me>"
LABEL description="Redis 7 for Blacklist Intelligence Platform"

ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.title="blacklist-redis"

RUN mkdir -p /usr/local/etc/redis && \
    printf '%s\n' \
        "bind 127.0.0.1" \
        "port 6379" \
        "protected-mode yes" \
        "maxmemory 256mb" \
        "maxmemory-policy allkeys-lru" \
        "appendonly no" \
        "save \"\"" \
        "tcp-keepalive 300" \
        "timeout 0" \
    > /usr/local/etc/redis/redis.conf

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD redis-cli ping | grep -q PONG || exit 1

EXPOSE 6379

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
