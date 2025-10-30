FROM postgres:15-alpine

# Build metadata and labels
ARG VERSION
ARG BUILD_DATE
ARG POSTGRES_DB
ARG POSTGRES_USER  
ARG POSTGRES_PASSWORD

LABEL version=${VERSION}
LABEL build_date=${BUILD_DATE}
LABEL description="PostgreSQL 15 database for Blacklist Management System"
LABEL maintainer="qws941"

# Removed Watchtower labels - Using Portainer-only deployment

# Container management labels (Portainer controlled)
LABEL com.docker.compose.project=blacklist
LABEL com.docker.compose.service=postgres

# PostgreSQL configuration with secure credentials from build args (종속성 해결)
ENV POSTGRES_DB=${POSTGRES_DB:-blacklist} \
    POSTGRES_USER=${POSTGRES_USER:-postgres} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256 --auth-local=scram-sha-256" \
    TZ=Asia/Seoul \
    # Performance settings
    POSTGRES_MAX_CONNECTIONS=200 \
    POSTGRES_SHARED_BUFFERS=512MB \
    POSTGRES_EFFECTIVE_CACHE_SIZE=2GB \
    POSTGRES_WORK_MEM=16MB \
    POSTGRES_MAINTENANCE_WORK_MEM=128MB \
    # Security settings
    POSTGRES_AUTH_METHOD=scram-sha-256 \
    POSTGRES_HOST_AUTH_METHOD=scram-sha-256 \
    # Logging settings
    POSTGRES_LOG_STATEMENT=mod \
    POSTGRES_LOG_MIN_DURATION=1000

# PostgreSQL performance and data integrity configuration optimization
RUN echo "# Performance and Data Integrity Settings" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "shared_preload_libraries = 'pg_stat_statements'" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "pg_stat_statements.track = all" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "max_connections = 200" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "shared_buffers = 512MB" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "effective_cache_size = 2GB" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "work_mem = 16MB" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "maintenance_work_mem = 128MB" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "# Connection and Transaction Settings" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "default_transaction_isolation = 'read committed'" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "statement_timeout = 30000" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "idle_in_transaction_session_timeout = 60000" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "# Data Integrity and Consistency" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "fsync = on" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "synchronous_commit = on" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "wal_sync_method = fdatasync" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "checkpoint_completion_target = 0.9" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "# Logging for Data Issues Debugging" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "log_statement = 'mod'" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "log_min_duration_statement = 1000" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "log_lock_waits = on" >> /usr/local/share/postgresql/postgresql.conf.sample && \
    echo "log_temp_files = 0" >> /usr/local/share/postgresql/postgresql.conf.sample

# Copy initialization scripts (executed in alphabetical order)
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Ensure migration scripts have proper permissions and naming
RUN chmod +x /docker-entrypoint-initdb.d/*.sql && \
    ls -la /docker-entrypoint-initdb.d/ && \
    echo "📋 초기화 스크립트 목록:" && \
    ls -1 /docker-entrypoint-initdb.d/*.sql && \
    echo "✅ 스키마 v3.0.0 이미지에 포함됨" && \
    # 스키마 파일 크기 확인
    stat -c "📊 완전한 스키마 크기: %s bytes" /docker-entrypoint-initdb.d/00-complete-schema.sql 2>/dev/null || echo "⚠️ 스키마 파일이 이미 init-scripts에 포함됨"

# Data directory volume configuration
VOLUME ["/var/lib/postgresql/data"]

# Expose PostgreSQL port (표준 포트 사용)
EXPOSE 5432

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1