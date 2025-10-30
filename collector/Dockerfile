FROM python:3.9-slim

# Build arguments for environment variable injection
ARG VERSION
ARG BUILD_DATE
ARG POSTGRES_HOST
ARG POSTGRES_PORT
ARG POSTGRES_DB
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG REDIS_HOST
ARG REDIS_PORT
ARG REGTECH_ID
ARG REGTECH_PW
ARG REGTECH_BASE_URL

# Metadata labels
LABEL version=${VERSION}
LABEL build_date=${BUILD_DATE}
LABEL description="Blacklist Data Collector Service"
LABEL maintainer="qws941"

# Removed Watchtower labels - Using Portainer-based deployment

# Container management labels
LABEL com.docker.compose.project=blacklist
LABEL com.docker.compose.service=collector

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 의존성 설치
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    wget \
    vim \
    gcc \
    libpq-dev \
    # Playwright dependencies for headless browser
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
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치 (chromium만 설치 - 용량 절약)
# install-deps 제거 (시스템 패키지는 이미 설치됨)
RUN playwright install chromium

# collector 소스 코드 복사
COPY collector/ ./collector/
COPY core/ ./core/
COPY utils/ ./utils/
COPY api/ ./api/

# 환경 변수 설정 (종속성 해결)
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    # Database Configuration
    POSTGRES_HOST=${POSTGRES_HOST:-blacklist-postgres} \
    POSTGRES_PORT=${POSTGRES_PORT:-5432} \
    POSTGRES_DB=${POSTGRES_DB:-blacklist} \
    POSTGRES_USER=${POSTGRES_USER:-postgres} \
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
    # Redis Configuration
    REDIS_HOST=${REDIS_HOST:-blacklist-redis} \
    REDIS_PORT=${REDIS_PORT:-6379} \
    # REGTECH Configuration
    REGTECH_ID=${REGTECH_ID} \
    REGTECH_PW=${REGTECH_PW} \
    REGTECH_BASE_URL=${REGTECH_BASE_URL:-https://regtech.fsec.or.kr} \
    # Collector specific settings
    COLLECTOR_PORT=8545 \
    LOG_LEVEL=INFO

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# collector 스크립트 실행 권한 부여
RUN chmod +x /app/collector/run_collector.py

# 포트 노출
EXPOSE 8545

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8545/health || exit 1

# 기본 실행 명령 (Multi-collector scheduler)
CMD ["python", "/app/collector/monitoring_scheduler.py"]