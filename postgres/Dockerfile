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

# ============================================================================
# SCHEMA INITIALIZATION (v3.0.0)
# ============================================================================
# Copy initialization scripts (executed in alphabetical order)
# Execution order:
#   1. 00-complete-schema.sql       - Full schema definition (10 tables)
#   2. 00-schema-check.sql          - Auto-fix missing columns
#   3. 01-credentials.sql           - Default credentials
#   4. 02-migrate-pipeline-metrics.sql - Pipeline metrics
#   5. 03-fix-collection-metrics.sql   - Collection metrics
#   6. 04-fix-schema-patch.sql         - Schema patches
#   7. 08_collection_credentials_extended.sql - Extended credentials
#   8. 09_add_data_source_columns.sql  - Data source columns
# ============================================================================

COPY init-scripts/ /docker-entrypoint-initdb.d/

# ============================================================================
# Custom Entrypoint for Always-Run Migrations
# ============================================================================
# Copy custom entrypoint that runs migrations on every restart
COPY docker-entrypoint-custom.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-custom.sh

# Validate schema files and set permissions
RUN set -e && \
    echo "🔍 Validating schema files..." && \
    # Check required schema files exist
    test -f /docker-entrypoint-initdb.d/00-complete-schema.sql || (echo "❌ Missing 00-complete-schema.sql" && exit 1) && \
    test -f /docker-entrypoint-initdb.d/00-schema-check.sql || (echo "❌ Missing 00-schema-check.sql" && exit 1) && \
    # Set execute permissions
    chmod +x /docker-entrypoint-initdb.d/*.sql && \
    # Display schema summary
    echo "" && \
    echo "📋 Schema Initialization Scripts:" && \
    ls -1 /docker-entrypoint-initdb.d/*.sql | nl && \
    echo "" && \
    echo "✅ Schema v3.0.0 embedded in image" && \
    echo "📊 Main schema size: $(stat -c %s /docker-entrypoint-initdb.d/00-complete-schema.sql) bytes" && \
    echo "🔢 Total tables: 10 (blacklist_ips, whitelist_ips, collection_*, monitoring_*, etc.)" && \
    echo "📇 Total indexes: 33+" && \
    echo "👁️  Total views: 7" && \
    echo "⚙️  Auto-migration: Enabled (runs on every restart)" && \
    echo "🔄 Custom entrypoint: /usr/local/bin/docker-entrypoint-custom.sh" && \
    echo ""

# Data directory volume configuration
VOLUME ["/var/lib/postgresql/data"]

# Expose PostgreSQL port (표준 포트 사용)
EXPOSE 5432

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

# ============================================================================
# Entrypoint Configuration
# ============================================================================
# Use custom entrypoint that wraps official postgres entrypoint
# - Runs migrations from /migrations directory on every start
# - Then starts PostgreSQL normally
# ============================================================================
ENTRYPOINT ["docker-entrypoint-custom.sh"]
CMD ["postgres"]