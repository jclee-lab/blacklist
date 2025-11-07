# 🛡️ REGTECH Blacklist Intelligence Platform

> **⚠️ REPOSITORY MIGRATED**
>
> This repository has been migrated to **GitLab**: https://gitlab.jclee.me/jclee/blacklist
>
> Please update your remotes and use the GitLab repository for all future work.
>
> ```bash
> git remote set-url origin git@gitlab.jclee.me:jclee/blacklist.git
> ```

[![🚀 Deploy Pipeline](https://github.com/qws941/blacklist/actions/workflows/deploy.yml/badge.svg)](https://github.com/qws941/blacklist/actions/workflows/deploy.yml)
[![🔍 Operational Analysis](https://github.com/qws941/blacklist/actions/workflows/operational-log-analysis.yml/badge.svg)](https://github.com/qws941/blacklist/actions/workflows/operational-log-analysis.yml)
[![🤖 Claude AI Integration](https://img.shields.io/badge/Claude%20AI-Automated-blue)](https://claude.ai/code)
[![Docker](https://img.shields.io/badge/Docker-Independent%20Containers-blue)](https://registry.jclee.me)
[![Portainer](https://img.shields.io/badge/Portainer-API%20Controlled-green)](https://portainer.jclee.me)

A comprehensive Flask-based threat intelligence platform that collects, manages, and analyzes IP blacklist data from the Korean Financial Security Institute (REGTECH). Features automated collection pipelines, real-time monitoring, comprehensive API/web interfaces, and production-ready deployment with intelligent container orchestration.

## 🚀 Quick Start

### Clone Repository (Gitea)

**IMPORTANT:** The repository uses Git LFS for the 701MB offline package. CloudFlare bypass is required:

```bash
# Step 1: Setup CloudFlare bypass (required for LFS downloads >100MB)
sudo bash -c 'echo "221.153.20.249 git.jclee.me" >> /etc/hosts'

# Step 2: Disable SSL verification (self-signed certificate when using direct IP)
git config --global http.sslVerify false

# Step 3: Clone latest version only (recommended - faster)
GIT_SSL_NO_VERIFY=1 git clone --depth 1 ssh://git@git.jclee.me:2223/gitadmin/blacklist.git
cd blacklist

# Step 4: Verify LFS file downloaded (should be 701MB, not 134 bytes)
ls -lh offline-packages/*.tar.gz
sha256sum -c offline-packages/*.sha256  # Verify integrity

# Full history clone (if needed)
GIT_SSL_NO_VERIFY=1 git clone ssh://git@git.jclee.me:2223/gitadmin/blacklist.git
```

**Why these steps?**
- `/etc/hosts` entry bypasses CloudFlare's 100MB upload/download limit
- SSL verification must be disabled as direct IP connection uses Traefik's self-signed certificate
- LFS files download automatically during clone (no `git lfs pull` needed)

### Start Services
```bash
# Development environment with live reload
make dev

# Production environment
make prod

# View all service logs
make logs

# Run comprehensive tests
make test

# Check service health
make health

# Stop all services
make down

# Get help with all commands
make help
```

For detailed setup instructions, see the [Installation Guide](#-installation) below.

## 📁 Project Structure

For a comprehensive guide to the project's file organization and purpose of each directory/file, see [FILE_ORGANIZATION.md](FILE_ORGANIZATION.md).

## 🌟 Key Features

### 🔄 **Automated Data Collection**
- **REGTECH Integration**: Direct connection to Korean Financial Security Institute portal
- **Excel Processing**: Advanced pandas-based parsing with binary fallback
- **Scheduling**: Configurable collection intervals with smart retry mechanisms
- **Authentication**: Secure two-stage authentication (findOneMember → addLogin)

### 📊 **Intelligence Dashboard**
- **Real-time Statistics**: Live metrics and collection status
- **Interactive Web UI**: Bootstrap-based responsive interface
- **API Endpoints**: RESTful APIs for external integration
- **Search & Filter**: Advanced IP search with multiple criteria

### 🛡️ **Phase 1: VIP Protection & Observability** (✅ Completed 2025-10-03)
- **Whitelist Priority Check**: VIP customer IP protection with automatic precedence
- **Whitelist Management**: Complete whitelist table and manual IP registration
- **Structured Logging**: JSON-formatted decision tracking with structlog
- **Prometheus Metrics**: Real-time metrics for decisions and whitelist hits
- **API Endpoints**: `/api/blacklist/check` for verification, `/api/whitelist/manual-add` for registration
- **Documentation**: [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) - Full implementation details

### 🎯 **Manual IP Management** (✅ Completed 2025-10-03)
- **Blacklist Registration**: Manual IP addition with validation and duplicate checking
- **Whitelist Registration**: VIP/Admin IP protection with priority enforcement
- **Automated Tests**: Comprehensive integration tests for both lists
- **API Documentation**: Complete cURL, Python, Shell script examples
- **Priority Logic**: Whitelist always takes precedence over blacklist

### 🏗️ **Production Architecture**
- **Independent Containers**: Flask app, PostgreSQL 15, Redis 7
- **Portainer API Control**: Complete container lifecycle management
- **Health Monitoring**: Comprehensive health checks with auto-restart
- **Instant Rollback**: Automatic rollback to stable versions on failure

### 🤖 **AI-Powered Operations**
- **Claude Code Action**: 5 specialized AI workflows for CI/CD automation
- **Automated Issue Resolution**: AI-powered failure analysis and fixes
- **Error Monitoring**: Automatic GitHub issue creation with context
- **Performance Optimization**: AI-driven system optimization

## 🚀 Live System

- **🌐 Production URL**: [https://blacklist.jclee.me](https://blacklist.jclee.me)
- **📊 Health Check**: [https://blacklist.jclee.me/health](https://blacklist.jclee.me/health)
- **📈 System Stats**: [https://blacklist.jclee.me/api/stats](https://blacklist.jclee.me/api/stats)
- **🔧 Collection Control**: [https://blacklist.jclee.me/collection-control](https://blacklist.jclee.me/collection-control)

## 🏗️ Architecture Overview

### Independent Container System (October 2025)
```
Registry: registry.jclee.me
├── 🐳 blacklist-app:latest        # Flask Application (Port 2542)
│   ├── Whitelist Management API
│   ├── Blacklist Management API
│   └── Priority-based IP Filtering
├── 🔧 blacklist-collector:latest  # REGTECH Collection Service (Port 8545, internal)
├── 🗄️ blacklist-postgres:latest   # PostgreSQL 15 (Port 5432, internal)
│   ├── whitelist_ips table
│   └── blacklist_ips table
└── 🔄 blacklist-redis:latest      # Redis 7 Cache (Port 6379, internal)

Network: blacklist-network (Bridge)
Deployment: Portainer API + GitHub Actions
External Access: nginx-proxy (https://blacklist.jclee.me)
```

## ⚡ Quick Start

### 🐳 Production Deployment (Recommended)
```bash
# Clone repository
git clone https://github.com/qws941/blacklist.git
cd blacklist

# 통합 자동 배포 (Unified Auto Deploy)
git add -A && git commit -m "feat: 새로운 기능 추가" && git push origin master
```

### 📦 Air-Gap Deployment (Offline Environment)
For air-gap environments without internet access:

```bash
# Step 1: Create offline package (on internet-connected machine)
bash create-complete-offline-package.sh

# Step 2: Transfer to air-gap environment
# Copy blacklist-offline-YYYYMMDD_HHMMSS.tar.gz to target system

# Step 3: Install on air-gap system (Docker required)
tar -xzf blacklist-offline-*.tar.gz
cd blacklist-offline-*/
bash install.sh  # Automated installation

# Step 4: Verify deployment
docker-compose ps
curl http://localhost:2542/health
```

**Package Contents:**
- ✅ Complete source code
- ✅ Pre-packaged Node.js dependencies (316MB)
- ✅ Docker build scripts
- ✅ Python dependency installation scripts
- ✅ Comprehensive documentation

**Requirements:** Docker only (no internet, no pip required)

**Documentation:**
- 📖 [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Quick installation guide
- 📦 [PACKAGE_DELIVERY_REPORT.md](PACKAGE_DELIVERY_REPORT.md) - Detailed package documentation
- ✅ [VALIDATION_REPORT.md](VALIDATION_REPORT.md) - Package validation results

### 🏠 Local Development
```bash
# Build independent containers
docker build -t blacklist-app:local src/
docker build -t blacklist-postgres:local postgres/
docker build -t blacklist-redis:local redis/

# Create network
docker network create blacklist-network

# Start services
docker run -d --name postgres --network blacklist-network \
  -e POSTGRES_PASSWORD=postgres blacklist-postgres:local

docker run -d --name redis --network blacklist-network \
  blacklist-redis:local

docker run -d --name app --network blacklist-network \
  -p 2542:2542 \
  -e POSTGRES_HOST=postgres \
  -e REDIS_HOST=redis \
  blacklist-app:local

# Access application
curl http://localhost:2542/health
```

## 🔧 Configuration

### Required Environment Variables
```bash
# Database Configuration
POSTGRES_HOST=blacklist-postgres
POSTGRES_PORT=2544
POSTGRES_DB=blacklist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

# Redis Configuration
REDIS_HOST=blacklist-redis
REDIS_PORT=2543
REDIS_PASSWORD=your_redis_password

# REGTECH Authentication
REGTECH_ID=your_regtech_username
REGTECH_PW=your_regtech_password
REGTECH_BASE_URL=https://regtech.fsec.or.kr

# Application Settings
FLASK_ENV=production
PORT=2542
SECRET_KEY=your_secret_key

# GitHub Integration (Error Monitoring)
GITHUB_TOKEN=your_github_token
GITHUB_REPO_OWNER=qws941
GITHUB_REPO_NAME=blacklist

# Claude Code Action Integration
CLAUDE_CODE_OAUTH_TOKEN=your_oauth_token
```

### 🔐 Credential Management

**⚠️ IMPORTANT**: Credentials can be managed via **UI (recommended)** or environment variables.

#### Method 1: Web UI (Recommended - Encrypted Storage)

**Integrated Collection Panel**: https://blacklist.nxtd.co.kr/collection-panel

**Steps**:
1. Access the collection panel: `https://blacklist.nxtd.co.kr/collection-panel`
2. Navigate to "인증정보 설정" (Credential Settings) section
3. Enter REGTECH credentials:
   - Username: Your REGTECH account ID
   - Password: Your REGTECH password
4. (Optional) Enter SECUDIUM credentials:
   - Username: Your SECUDIUM account ID
   - Password: Your SECUDIUM password
5. Click "저장" (Save) button
6. Credentials are **encrypted** and stored in `collection_credentials` table
7. Auto-collection scheduler starts automatically

**Benefits**:
- ✅ Encrypted storage via `secure_credential_service`
- ✅ No direct database access needed
- ✅ Real-time statistics dashboard
- ✅ Manual collection trigger
- ✅ Collection logs viewer

**Alternative UI**: https://blacklist.nxtd.co.kr/settings (Settings Management)

#### Method 2: API-Based Configuration

```bash
# Save credentials via API (encrypted)
curl -X POST https://blacklist.nxtd.co.kr/collection-panel/api/save-credentials \
  -H "Content-Type: application/json" \
  -d '{
    "regtech_username": "your_regtech_id",
    "regtech_password": "your_regtech_password",
    "secudium_username": "your_secudium_id",
    "secudium_password": "your_secudium_password"
  }'

# Verify credentials saved
curl https://blacklist.nxtd.co.kr/collection-panel/api/load-credentials

# Trigger manual collection
curl -X POST https://blacklist.nxtd.co.kr/collection-panel/trigger \
  -H "Content-Type: application/json" \
  -d '{"source": "regtech", "start_date": "2025-01-01", "end_date": "2025-01-10"}'
```

#### Method 3: Environment Variables (Backup Method)

**Use Case**: Offline deployment or automated scripts

**Setup**:
```bash
# Edit .env file
vi .env

# Add credentials
REGTECH_ID=your_regtech_username
REGTECH_PW=your_regtech_password
SECUDIUM_ID=your_secudium_username  # Optional
SECUDIUM_PW=your_secudium_password  # Optional

# Restart services
docker compose restart blacklist-app blacklist-collector
```

**⚠️ Security Note**: Environment variables are stored in plaintext. Use UI method for production.

#### Credential Storage Comparison

| Method | Security | Ease of Use | Auto-Start | Use Case |
|--------|----------|-------------|------------|----------|
| **Web UI** | ✅ Encrypted | ✅ Easy | ✅ Yes | Production (Recommended) |
| **API** | ✅ Encrypted | ⚠️ Moderate | ✅ Yes | Automation/Scripts |
| **Environment Variables** | ❌ Plaintext | ✅ Easy | ⚠️ Manual | Offline/Development |

## 📖 API Documentation

### Core Endpoints

#### 🏥 Health & Status
```bash
GET /health                     # System health check
GET /api/stats                  # System statistics
GET /api/monitoring/metrics     # Prometheus-style metrics
GET /api/monitoring/dashboard   # Real-time dashboard data
```

#### 🗃️ Data Management
```bash
GET /api/search/{ip}           # Search specific IP
GET /api/blacklist/json        # Blacklist data (JSON)
GET /api/blacklist/active      # Active blacklist (plain text)
GET /api/blacklist/list        # Paginated blacklist (with pagination)
```

#### 🛡️ IP Blacklist & Whitelist Management
```bash
# Blacklist Check (Priority: Whitelist → Blacklist)
GET  /api/blacklist/check?ip=1.2.3.4        # Check if IP is blocked
POST /api/blacklist/check                   # Check IP (JSON body)

# Manual Blacklist Registration
POST /api/blacklist/manual-add              # Add IP to blacklist
{
  "ip_address": "1.2.3.4",
  "country": "CN",
  "notes": "Malicious activity detected"
}

# Manual Whitelist Registration (VIP Protection)
POST /api/whitelist/manual-add              # Add IP to whitelist
{
  "ip_address": "192.168.1.100",
  "country": "KR",
  "reason": "VIP customer IP"
}

# Whitelist Management
GET  /api/whitelist/list?page=1&per_page=50 # List all whitelisted IPs
```

#### 🔄 Collection Management
```bash
GET /api/collection/status     # Collection status
GET /api/collection/history    # Collection history
POST /api/collection/regtech/trigger  # Trigger REGTECH collection
```

## 🤖 AI-Powered CI/CD & Advanced Deployment System

### 🚀 **Enhanced Deployment System (2025.09.21)**

#### **4가지 핵심 기능 (4 Core Features)**

##### 1. 🔍 **Git 추적 (Git Tracking)**
- **실시간 변경사항 감지**: 커밋되지 않은 변경사항과 원격 저장소 차이점 자동 감지
- **스마트 상태 분석**: Git dirty state, branch differences, uncommitted files 종합 분석
- **자동 빌드 트리거**: 변경사항 감지 시 자동 빌드 파이프라인 실행

```bash
# Git 상태 모니터링
./scripts/git-watcher.sh --monitor       # 지속적 모니터링 모드
./scripts/git-watcher.sh --check         # 일회성 상태 확인
./scripts/git-watcher.sh --auto-build    # 변경 감지 시 자동 빌드
```

##### 2. 🏗️ **자동 빌드 (Automatic Build)**
- **인텔리전트 빌드**: Git 상태 기반 자동 Docker 이미지 빌드
- **병렬 빌드 지원**: 다중 컨테이너 동시 빌드로 시간 단축
- **빌드 캐시 최적화**: Docker layer 캐싱 및 증분 빌드

```bash
# 향상된 빌드 시스템
./scripts/build-all.sh --parallel --push    # 병렬 빌드 + 레지스트리 푸시
./scripts/build-all.sh --auto               # Git 변경사항 기반 자동 빌드
./scripts/build-all.sh --cleanup            # 빌드 후 자동 정리
```

##### 3. 🏷️ **버전 관리 (Version Management)**
- **Git 기반 태깅**: 커밋 해시, 브랜치, 태그 기반 정확한 버전 추적
- **시맨틱 버저닝**: 자동 버전 증가 및 태그 관리
- **더티 상태 감지**: 커밋되지 않은 변경사항 자동 표기

```bash
# 정교한 버전 관리
./scripts/version-manager.sh --generate     # 현재 Git 상태 기반 버전 생성
./scripts/version-manager.sh --tag          # 자동 태그 생성 및 적용
./scripts/version-manager.sh --history      # 버전 히스토리 조회
```

##### 4. ⚡ **강제 업데이트 (Force Update)**
- **Portainer API 통합**: 최신 이미지 강제 풀링 및 컨테이너 재시작
- **롤링 업데이트**: 무중단 서비스 업데이트
- **헬스체크 통합**: 업데이트 후 자동 상태 검증

```bash
# 강제 업데이트 전략
./scripts/force-update.sh --rolling         # 롤링 업데이트 (권장)
./scripts/force-update.sh --all-at-once     # 전체 동시 업데이트
./scripts/force-update.sh --selective app   # 특정 서비스만 업데이트
```

#### **🎯 통합 배포 오케스트레이터**

모든 기능을 통합한 인텔리전트 배포 시스템:

```bash
# 완전 자동화 모드
./scripts/deployment-orchestrator.sh --auto

# 수동 제어 모드
./scripts/deployment-orchestrator.sh --manual

# CI/CD 파이프라인 모드
./scripts/deployment-orchestrator.sh --cicd
```

**자동화 파이프라인 흐름:**
```
Git 변경사항 감지 → 버전 생성 → 자동 빌드 → 이미지 푸시 → 강제 업데이트 → 헬스체크 → 상태 리포트
```

### Claude Code Action Workflows

#### 🔧 **Auto-Fix System** (`claude-ci-auto-fix.yml`)
- Automatic failure detection and resolution
- Docker build fixes, dependency resolution
- Test failure analysis and corrections

#### 🔍 **Failure Analyzer** (`claude-failure-analyzer.yml`)
- Advanced log collection and pattern analysis
- Automatic issue categorization and GitHub issue creation
- Slack notifications for immediate alerts

#### 📝 **PR Review** (`claude-pr-review.yml`)
- Security, performance, and code quality analysis
- Blueprint architecture optimization
- Statistical reporting and improvement suggestions

### Legacy Deployment Pipeline
```yaml
# Traditional deployment flow
GitHub Push → Build Images → Registry Push → Portainer Deploy → Health Check → Rollback (if needed)
```

### Enhanced Deployment Pipeline (NEW)
```yaml
# Advanced deployment flow with 4 core features
Git Changes Detection → Version Generation → Auto Build → Force Update → Health Verification → Status Report
```

## 🔒 Security Features

### Authentication & Authorization
- **Environment Variables**: All credentials stored securely
- **GitHub Secrets**: Production credential management
- **Two-stage Authentication**: REGTECH portal integration
- **JWT Tokens**: Secure API authentication

### Container Security
- **Non-root Execution**: Security-first container design
- **Multi-stage Builds**: Minimal production images
- **Network Isolation**: Bridge network for container communication
- **Health Checks**: Comprehensive container monitoring

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

### Development Setup
```bash
# Clone and setup
git clone https://github.com/qws941/blacklist.git
cd blacklist

# Install dependencies
cd src && pip install -r requirements.txt

# Setup database
python -c "from core.services.database_service import db_service; db_service.create_tables()"

# Run development server
python run_app.py
```

### 🧪 Testing

#### Comprehensive Test Suite
```bash
# Run all tests
make test

# Run specific test suites
python tests/run_all_tests.py                    # All tests
python -m pytest tests/ -v                       # Python tests only
npm test                                         # JavaScript UI tests
```

#### Whitelist & Blacklist Integration Tests
```bash
# Run comprehensive whitelist tests
chmod +x tests/test_whitelist.sh
./tests/test_whitelist.sh

# Manual API testing examples
# Add IP to whitelist
curl -X POST http://localhost:2542/api/whitelist/manual-add \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "192.168.1.100", "country": "KR", "reason": "VIP customer"}'

# Check if IP is blocked (whitelist priority)
curl -s "http://localhost:2542/api/blacklist/check?ip=192.168.1.100" | jq

# List all whitelisted IPs
curl -s "http://localhost:2542/api/whitelist/list?page=1&per_page=50" | jq
```

## 🔄 Recent Updates (October 2025)

### 📦 **Air-Gap Deployment Package** (✅ 2025-10-09)
- **Offline Package Creation**: Complete air-gap deployment capability for isolated environments
- **Package Size**: 100MB (blacklist-offline-no-docker-*.tar.gz)
- **Contents**:
  - Complete source code (4 microservices)
  - Pre-packaged Node.js dependencies (316MB, 117 packages)
  - Automated installation scripts (7 scripts)
  - Docker build scripts for target environment
  - Python dependency installation automation
  - Comprehensive documentation (3 guides)
- **Requirements**: Docker only (no internet, no pip/Python on host required)
- **Installation**: One-command automated setup (`bash install.sh`)
- **Documentation**:
  - `INSTALLATION_GUIDE.md` - Quick installation guide (2.1KB)
  - `PACKAGE_DELIVERY_REPORT.md` - Detailed package documentation (9.5KB)
  - `VALIDATION_REPORT.md` - Package validation results (8.1KB)
  - `CLAUDE.md` - Enhanced with air-gap deployment instructions (312 lines)
- **Validation**: All 8 verification checks passed (scripts, dependencies, structure, documentation)
- **Use Case**: Secure environments, military/government deployments, isolated networks

### 🎯 **Phase 1 Whitelist Implementation** (✅ 2025-10-03)
- **Whitelist Table**: Complete PostgreSQL schema with unique constraints and indexes
- **Manual IP Registration**: Both blacklist and whitelist manual registration APIs
- **Priority Logic**: Whitelist check takes precedence over blacklist (VIP protection)
- **Automated Tests**: Comprehensive integration test suite (`tests/test_whitelist.sh`)
- **API Endpoints**:
  - `POST /api/whitelist/manual-add` - Add VIP/Admin IPs
  - `GET /api/whitelist/list` - List all whitelisted IPs with pagination
  - `POST /api/blacklist/manual-add` - Manual blacklist registration
- **Documentation**: Complete Appendix F in XWiki documentation (300+ lines)
- **Prometheus Metrics**: `blacklist_whitelist_hits_total`, `blacklist_decisions_total`
- **Structured Logging**: Event-based decision tracking with metadata

## 🔄 Recent Updates (September 2025)

### 🎯 **Major Enhancements**
- **Independent Container Architecture**: Complete restructure for Portainer API control
- **AI-Powered CI/CD**: 5 specialized Claude workflows for automation
- **Enhanced Database Schema**: New fields for country, detection dates
- **Error Monitoring**: Automatic GitHub issue creation with AI analysis
- **Port Standardization**: App(2542), Redis(2543), PostgreSQL(2544)

### 🐛 **Critical Fixes**
- **Portainer API Integration**: Fixed token authentication issues
- **Template Recovery**: Emergency UI recovery with Bootstrap templates
- **Container Startup**: Simplified direct execution pattern
- **Health Monitoring**: Comprehensive validation scripts

## 🤝 Contributing

### Issue Reporting
Use our enhanced issue templates:
- 🐛 **Bug Report**: System issues and problems
- ✨ **Feature Request**: New functionality proposals
- ❓ **Question**: Usage and support inquiries

### Code Standards
- **Python**: Black formatting, Flake8 linting, type hints
- **Docker**: Multi-stage builds, non-root execution
- **Security**: Environment variables, no hardcoded secrets
- **Testing**: 80% coverage minimum

## 📞 Support & Resources

### 🔗 **Quick Links**
- **Production System**: [blacklist.jclee.me](https://blacklist.jclee.me)
- **System Status**: [blacklist.jclee.me/health](https://blacklist.jclee.me/health)
- **GitHub Repository**: [github.com/qws941/blacklist](https://github.com/qws941/blacklist)

### 🏗️ **Infrastructure**
- **Docker Registry**: [registry.jclee.me](https://registry.jclee.me)
- **Container Management**: [portainer.jclee.me](https://portainer.jclee.me)
- **CI/CD Monitoring**: GitHub Actions workflows

## 📄 License

This project is licensed under the MIT License.

---

## 🎯 Version Information

- **Current Version**: 3.1.0 (October 2025)
- **Architecture**: Independent Container System (4 containers)
- **Deployment**: Portainer API + GitHub Actions + Air-Gap Package
- **AI Integration**: Claude Code Action (5 workflows)
- **Database**: PostgreSQL 15 with whitelist/blacklist tables
- **Cache**: Redis 7 with optimized configuration
- **New Features**:
  - Whitelist management with priority-based filtering
  - Manual IP registration (blacklist/whitelist)
  - Air-gap deployment package (offline environments)

---

<div align="center">

**🛡️ REGTECH Blacklist Intelligence Platform**  
*Powered by AI automation and intelligent container orchestration*

[![GitHub](https://img.shields.io/badge/GitHub-qws941/blacklist-blue)](https://github.com/qws941/blacklist)
[![Docker](https://img.shields.io/badge/Docker-registry.jclee.me-blue)](https://registry.jclee.me)
[![Live](https://img.shields.io/badge/Live-blacklist.jclee.me-green)](https://blacklist.jclee.me)

*Built with ❤️ for cybersecurity professionals*

</div>

# Recent Updates History

## Phase 1 화이트리스트 구현 완료 (2025-10-03)
- **기능**: VIP 고객 IP 보호를 위한 화이트리스트 시스템 구현
- **구현 내용**:
  - PostgreSQL `whitelist_ips` 테이블 추가 (unique constraints, indexes)
  - 화이트리스트 수동 등록 API: `POST /api/whitelist/manual-add`
  - 화이트리스트 목록 조회 API: `GET /api/whitelist/list`
  - 블랙리스트 수동 등록 API: `POST /api/blacklist/manual-add`
  - 우선순위 로직: 화이트리스트 → 블랙리스트 순서
- **테스트**: 통합 테스트 스크립트 (`tests/test_whitelist.sh`) 200+ 라인
- **문서화**: XWiki Appendix F (300+ 라인, Mermaid 다이어그램 포함)
- **메트릭**: Prometheus 메트릭 및 구조화된 로깅 추가
- **패키지**: production-install.tar.gz 재생성 (483 MB)

## UI 안정화 (2025-09-24)
- **문제**: UI 요소들이 날아다니는 애니메이션 효과로 인한 사용성 저하
- **해결**: 모든 `transform`, `transition`, `hover` 애니메이션 효과 제거
- **결과**: 정적이고 안정적인 사용자 인터페이스로 개선
- **적용 위치**: 컨테이너 내부 `/app/templates/*.html` 파일들

## Git 저장소 정리 (2025-09-24)
- **Basedir 정책**: `.git`, `.github`, `.serena`, `docker-compose.yml`, `CLAUDE.md`, `README.md`만 허용
- **제거된 항목**: `app/`, `src/`, `collector/`, `postgres/`, `redis/` 등 모든 소스 디렉토리
- **서비스 운영**: 컨테이너 기반으로 정상 운영 중 (https://blacklist.jclee.me)

---

**Version History:**
- **v3.1.0** (2025-10-09): Air-Gap 배포 패키지 (오프라인 환경 지원, 100MB 패키지)
- **v3.0.0** (2025-10-03): Phase 1 화이트리스트 시스템 구현
- **v2.4.1** (2025-09-24): UI 안정화 및 백엔드 최적화
- **v2.4.0** (2025-09-20): Schema Migration 및 Database 동기화
- **v2.3.0** (2025-09-17): 독립 컨테이너 아키텍처 전환
