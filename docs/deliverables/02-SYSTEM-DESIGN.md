# 시스템 설계서 (System Design)

**프로젝트명:** REGTECH 블랙리스트 인텔리전스 플랫폼  
**버전:** 3.5.11  
**작성일:** 2026-01-15  
**문서번호:** DES-REGTECH-2026-001

---

## 1. 시스템 개요

### 1.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Internet / Air-Gap Zone                        │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Traefik v3 (Reverse Proxy)                       │
│                            Port: 80, 443                                 │
│                         SSL Termination, Routing                         │
└─────────────────────────────────────────────────────────────────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Flask API     │     │   Collector     │
│   Next.js 15    │     │   REST API      │     │   ETL Service   │
│   Port: 2543    │     │   Port: 2542    │     │   Port: 8545    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
           │                    │    │                    │
           │                    │    │                    │
           └────────────────────┼────┼────────────────────┘
                                │    │
                    ┌───────────┘    └───────────┐
                    ▼                            ▼
          ┌─────────────────┐          ┌─────────────────┐
          │  PostgreSQL 15  │          │    Redis 7      │
          │   Port: 5432    │          │   Port: 6379    │
          │   (Data Store)  │          │   (Cache)       │
          └─────────────────┘          └─────────────────┘
```

### 1.2 설계 원칙

| 원칙 | 설명 | 구현 방식 |
|------|------|----------|
| **Air-Gap First** | 폐쇄망 환경 우선 설계 | Git LFS를 Docker Registry로 활용 |
| **Manual DI** | 수동 의존성 주입 | ServiceFactory 패턴, No global state |
| **Raw SQL Only** | ORM 사용 금지 | SQLAlchemy/Prisma 배제, Raw SQL 사용 |
| **Shared-Nothing** | 서비스 간 코드 공유 금지 | DB/Redis/HTTP로만 통신 |
| **Proxy Mandate** | API 프록시 강제 | Frontend는 lib/api.ts 통해서만 API 호출 |

---

## 2. 서비스 아키텍처

### 2.1 Frontend Service (Next.js 15)

```
frontend/
├── app/                    # App Router (Server Components)
│   ├── page.tsx           # Dashboard
│   ├── ip-management/     # IP 관리
│   ├── collection/        # 수집 관리
│   ├── fortinet/          # Fortinet 연동
│   ├── settings/          # 설정
│   └── database/          # DB 관리
├── components/
│   ├── ui/                # Radix UI Primitives
│   └── features/          # 도메인 컴포넌트
├── lib/
│   └── api.ts             # API Client (필수)
└── types/
    └── index.ts           # TypeScript 인터페이스
```

**기술 스택:**
- Next.js 15.x (App Router)
- React 19.x
- TypeScript 5.x
- Tailwind CSS v4
- React Query (서버 상태)
- Zustand (클라이언트 상태)

### 2.2 Backend API Service (Flask)

```
app/
├── core/
│   ├── routes/
│   │   ├── api/           # JSON API 엔드포인트
│   │   │   ├── dashboard_api.py
│   │   │   ├── ip_management_api.py
│   │   │   ├── collection/
│   │   │   ├── fortinet/
│   │   │   └── database_api.py
│   │   └── web/           # Legacy HTML 라우트
│   ├── services/          # 비즈니스 로직
│   │   ├── service_factory.py
│   │   ├── database_service.py
│   │   ├── blacklist_service.py
│   │   ├── credential_service.py
│   │   └── fortimanager_service.py
│   └── utils/             # 유틸리티
│       ├── encryption.py
│       └── validators.py
└── run_app.py             # Entry Point
```

**기술 스택:**
- Flask 3.x
- Python 3.11+
- psycopg2 (PostgreSQL)
- redis-py
- APScheduler

### 2.3 Collector Service

```
collector/
├── api/                   # 외부 소스 어댑터
│   ├── regtech_api.py     # REGTECH (curl)
│   └── osint_apis.py      # OSINT 소스들
├── core/                  # ETL 로직
│   ├── regtech_collector.py
│   ├── multi_source_collector.py
│   └── authentication.py
├── collector/             # 오케스트레이션
│   ├── run_collector.py
│   ├── scheduler.py
│   └── health_server.py
└── utils/
```

**기술 스택:**
- Python 3.11+
- Requests/httpx
- BeautifulSoup4
- pandas (Excel 파싱)

---

## 3. 데이터베이스 설계

### 3.1 ER 다이어그램

```
┌─────────────────────┐     ┌─────────────────────┐
│   blacklist_ips     │     │   whitelist_ips     │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ ip_address          │     │ ip_address          │
│ source              │     │ reason              │
│ threat_type         │     │ added_by            │
│ is_active           │     │ created_at          │
│ raw_data (JSONB)    │     │ updated_at          │
│ created_at          │     └─────────────────────┘
│ updated_at          │
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ collection_credentials│   │  collection_history │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ service_name        │     │ service_name        │
│ encrypted_data      │     │ status              │
│ created_at          │     │ collected_count     │
│ updated_at          │     │ error_message       │
└─────────────────────┘     │ started_at          │
                            │ completed_at        │
                            └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│  collection_status  │     │   monitoring_data   │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ service_name        │     │ metric_name         │
│ is_running          │     │ value               │
│ last_run            │     │ timestamp           │
│ next_run            │     └─────────────────────┘
└─────────────────────┘
```

### 3.2 주요 테이블

| 테이블 | 용도 | 주요 컬럼 |
|--------|------|----------|
| `blacklist_ips` | 위협 IP 저장 | ip_address, source, threat_type, is_active, raw_data |
| `whitelist_ips` | 신뢰 IP 저장 | ip_address, reason, added_by |
| `collection_credentials` | 암호화 인증정보 | service_name, encrypted_data |
| `collection_history` | 수집 이력 | service_name, status, collected_count |
| `collection_status` | 수집 상태 | service_name, is_running, last_run |
| `monitoring_data` | 모니터링 데이터 | metric_name, value, timestamp |

### 3.3 뷰 (Views)

| 뷰 | 용도 |
|----|------|
| `unified_ip_list` | 블랙+화이트 IP 통합 |
| `active_blacklist` | 활성 블랙리스트 필터링 |
| `fortinet_active_ips` | FortiGate 연동용 |
| `collection_statistics` | 수집 통계 집계 |
| `ip_priority_check` | IP 우선순위 확인 |

### 3.4 인덱스

```sql
-- 성능 최적화 인덱스
CREATE INDEX idx_blacklist_ip ON blacklist_ips(ip_address);
CREATE INDEX idx_blacklist_source ON blacklist_ips(source);
CREATE INDEX idx_blacklist_active ON blacklist_ips(is_active);
CREATE INDEX idx_blacklist_created ON blacklist_ips(created_at DESC);
CREATE INDEX idx_whitelist_ip ON whitelist_ips(ip_address);
CREATE INDEX idx_history_service ON collection_history(service_name);
CREATE INDEX idx_history_status ON collection_history(status);
```

---

## 4. 서비스 레이어 설계

### 4.1 Service Factory (DI Container)

```python
class ServiceFactory:
    """Manual Dependency Injection Container"""
    
    @staticmethod
    def initialize(app: Flask) -> None:
        # 초기화 순서 중요!
        app.extensions['database'] = DatabaseService()
        app.extensions['blacklist'] = BlacklistService(app.extensions['database'])
        app.extensions['analytics'] = AnalyticsService(app.extensions['database'])
        app.extensions['collection'] = CollectionService(app.extensions['database'])
        app.extensions['scheduler'] = SchedulerService(app.extensions['collection'])
        app.extensions['fortimanager'] = FortiManagerService(app.extensions['database'])
        app.extensions['credential'] = CredentialService(app.extensions['database'])
```

### 4.2 서비스 의존성

```
DatabaseService (기반)
    │
    ├── BlacklistService
    ├── AnalyticsService
    ├── CollectionService ──→ SchedulerService
    ├── FortiManagerService
    └── CredentialService
```

### 4.3 핵심 서비스

| 서비스 | 책임 | 코드량 |
|--------|------|--------|
| `DatabaseService` | Raw SQL, 연결 풀 관리 | 400L |
| `BlacklistService` | IP CRUD, 검색, 캐싱 | 813L |
| `CredentialService` | Fernet 암호화, PBKDF2 | 300L |
| `AnalyticsService` | 통계, 집계 | 250L |
| `FortiManagerService` | FortiGate 연동 | 350L |
| `CollectionService` | 수집 오케스트레이션 | 500L |
| `SchedulerService` | 백그라운드 작업 | 200L |

---

## 5. 보안 설계

### 5.1 인증 및 권한

```
┌─────────────────────────────────────────────┐
│              Security Layer                  │
├─────────────────────────────────────────────┤
│  Flask-Login (Session-based Auth)           │
│  CSRF Token (WTForms)                       │
│  API Token (Bearer Auth)                    │
├─────────────────────────────────────────────┤
│  Rate Limiting (Redis-based)                │
│  - 100 req/min per IP                       │
│  - 1000 req/hour per User                   │
├─────────────────────────────────────────────┤
│  Security Headers                           │
│  - HSTS                                     │
│  - X-Content-Type-Options: nosniff          │
│  - X-Frame-Options: DENY                    │
└─────────────────────────────────────────────┘
```

### 5.2 자격증명 암호화

```python
# 암호화 흐름
Plain Text → PBKDF2 (Key Derivation) → Fernet (AES-128-CBC) → Base64 → DB

# 구성 요소
- Algorithm: Fernet (AES-128-CBC + HMAC-SHA256)
- Key Derivation: PBKDF2 with salt
- Salt: b'blacklist-regtech-salt-2025'
- Master Key: CREDENTIAL_MASTER_KEY.txt (환경 외부)
```

---

## 6. 배포 설계

### 6.1 배포 모드

| 모드 | 설명 | 네트워크 |
|------|------|----------|
| **Air-Gap** | 폐쇄망 오프라인 | 없음 |
| **NAS** | WARP 프록시 | 프록시 |
| **Dev** | 로컬 개발 | 인터넷 |

### 6.2 Air-Gap 배포 흐름

```
Build Phase:
  Docker Build → Registry Push → Pull → docker save → gzip

Package Phase:
  dist/images/*.tar.gz → Git LFS → airgap branch push

Deploy Phase:
  git clone -b airgap → git lfs pull → deploy-airgap.sh → docker load → docker compose up
```

### 6.3 컨테이너 구성

| 컨테이너 | 이미지 | 포트 | 리소스 |
|----------|--------|------|--------|
| blacklist-frontend | node:20-alpine | 2543 | 512MB |
| blacklist-app | python:3.11-slim | 2542 | 1GB |
| blacklist-collector | python:3.11-slim | 8545 | 512MB |
| blacklist-postgres | postgres:15-alpine | 5432 | 2GB |
| blacklist-redis | redis:7-alpine | 6379 | 256MB |
| traefik | traefik:v3.0 | 80, 443 | 128MB |

---

## 7. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0 | 2026-01-15 | Sisyphus | 초기 작성 |

