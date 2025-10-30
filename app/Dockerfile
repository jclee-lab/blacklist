# 🚀 Blacklist Flask Application - Container Image
# Multi-stage build for production optimization

# Stage 1: Python dependencies and application
FROM python:3.11-slim-bullseye as python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with retry logic
RUN for i in 1 2 3; do \
    apt-get update && apt-get install -y \
        gcc \
        g++ \
        libpq-dev \
        curl \
        && break || sleep 10; \
    done \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements from current directory
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure templates are copied to correct location for Flask
COPY templates /app/templates

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy runtime patches (auto-applied on container start)
COPY ../offline-packages/patches /app/patches
RUN chmod +x /app/patches/*.sh

# Create logs directory
RUN mkdir -p logs

# Stage 2: Production image
FROM python:3.11-slim-bullseye as production

# Build arguments for secure credential passing (GitHub Secrets → Docker)
ARG VERSION
ARG BUILD_NUMBER
ARG VCS_REF
ARG BUILDTIME

# Container labels and metadata
LABEL version=${VERSION:-unknown}
LABEL build_number=${BUILD_NUMBER:-0}
LABEL vcs_ref=${VCS_REF:-unknown}
LABEL buildtime=${BUILDTIME:-unknown}
LABEL description="Flask Blacklist Management System"
LABEL maintainer="qws941"

# Removed Watchtower labels - Using Portainer-based deployment

# Container management labels (Portainer controlled)
LABEL com.docker.compose.project=blacklist
LABEL com.docker.compose.service=app

# Application Secrets
ARG REGTECH_ID
ARG REGTECH_PW
ARG REGTECH_BASE_URL

# Database Configuration
ARG POSTGRES_HOST
ARG POSTGRES_PORT
ARG POSTGRES_DB
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD

# Redis Configuration
ARG REDIS_HOST
ARG REDIS_PORT

# Application URLs
ARG PRD_URL
ARG DEV_URL

# GitHub Integration
ARG GITHUB_TOKEN
ARG GITHUB_REPO_OWNER
ARG GITHUB_REPO_NAME

# Registry Configuration
ARG REGISTRY_HOST
ARG REGISTRY_USER
ARG REGISTRY_PASSWORD

# Environment Configuration
ARG FLASK_ENV
ARG TIMEZONE

# Copy Python dependencies from previous stage
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Set work directory and copy application
WORKDIR /app
COPY --from=python-base /app .

# Copy entrypoint script and set permissions (before switching to app user)
COPY --from=python-base /app/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy runtime patches from build stage
COPY --from=python-base /app/patches /app/patches
RUN chmod +x /app/patches/*.sh && chown -R app:app /app

# Set environment variables from build arguments (secure credential passing)
ENV VERSION=${VERSION:-unknown} \
    BUILD_NUMBER=${BUILD_NUMBER:-0} \
    VCS_REF=${VCS_REF:-unknown} \
    BUILDTIME=${BUILDTIME:-unknown} \
    # Application Configuration
    FLASK_ENV=${FLASK_ENV:-production} \
    PORT=2542 \
    PYTHONPATH=/app \
    TZ=Asia/Seoul \
    # Application Secrets
    REGTECH_ID=${REGTECH_ID} \
    REGTECH_PW=${REGTECH_PW} \
    REGTECH_BASE_URL=${REGTECH_BASE_URL:-https://regtech.fsec.or.kr} \
    # Database Configuration (종속성 해결)
    POSTGRES_HOST=${POSTGRES_HOST:-blacklist-postgres} \
    POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    POSTGRES_DB=${POSTGRES_DB:-blacklist} \
    POSTGRES_USER=${POSTGRES_USER:-postgres} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    # Redis Configuration (종속성 해결)
    REDIS_HOST=${REDIS_HOST:-blacklist-redis} \
    REDIS_PORT=${REDIS_PORT:-6379} \
    # Application URLs
    PRD_URL=${PRD_URL:-https://blacklist.jclee.me} \
    DEV_URL=${DEV_URL:-https://blacklist-dev.jclee.me} \
    # GitHub Integration
    GITHUB_TOKEN=${GITHUB_TOKEN} \
    GITHUB_REPO_OWNER=${GITHUB_REPO_OWNER:-qws941} \
    GITHUB_REPO_NAME=${GITHUB_REPO_NAME:-blacklist} \
    # Registry Configuration
    REGISTRY_HOST=${REGISTRY_HOST:-registry.jclee.me} \
    REGISTRY_USER=${REGISTRY_USER:-admin} \
    REGISTRY_PASSWORD=${REGISTRY_PASSWORD}

# Create required directories (static already copied from build stage)
RUN mkdir -p logs uploads cache

# Verify templates and static files are accessible
RUN echo "🔍 Verifying application files..." && \
    echo "📋 Templates: $(find /app/templates -name "*.html" -type f 2>/dev/null | wc -l) files" && \
    echo "📦 Static CSS: $(find /app/static/css -type f 2>/dev/null | wc -l) files" && \
    echo "📦 Static JS: $(find /app/static/js -type f 2>/dev/null | wc -l) files" && \
    ls -la /app/templates/ 2>/dev/null | head -10 || echo "⚠️ Templates verification incomplete" && \
    ls -la /app/static/ 2>/dev/null || echo "⚠️ Static files verification incomplete"

# Define volumes for persistent data
VOLUME ["/app/uploads", "/app/logs", "/app/cache"]

# Switch to non-root user
USER app

# Stay in /app working directory where files are copied
WORKDIR /app

# Health check with force restart capability
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2542/health || exit 1

# Container deployment via Portainer API (no auto-update dependency)

# Expose port
EXPOSE 2542

# Use entrypoint for auto-patching on container start
ENTRYPOINT ["/app/entrypoint.sh"]