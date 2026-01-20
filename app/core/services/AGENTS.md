# SERVICE LAYER KNOWLEDGE BASE

**Generated:** 2026-01-17
**Role:** Business Logic & DI Container
**Parent:** [../../AGENTS.md](../../AGENTS.md)

---

## OVERVIEW

비즈니스 로직 중심. **Manual DI 패턴** — `ServiceFactory`가 16+ 서비스의 의존성 주입 관리.
**Constraint**: 순환 Import 엄금.

---

## STRUCTURE

```
services/
├── service_factory.py      # DI Orchestrator (초기화 순서 정의)
├── database_service.py     # Infra: Raw SQL + ThreadedConnectionPool
├── blacklist_service.py    # Core: IP 로직 + Redis 캐싱 (820L ⚠️)
├── credential_service.py   # Security: Fernet + PBKDF2
├── scheduler_service.py    # Background Jobs (5s 시작 지연)
├── analytics_service.py    # Statistics & Aggregation
├── fortimanager_service.py # Device Integration
└── collection/             # 수집 관련 서비스
    └── regtech_data.py     # HTML scraping (621L)
```

---

## LIFECYCLE (초기화 순서 - 엄격)

```
1. Infra       → database_service
2. Dependents  → blacklist_service, analytics_service
3. Collection  → collection_service, scheduler_service
4. Integration → fortimanager_service
5. Config      → credential_service
6. Business    → scoring_service
```

⚠️ **순서 변경 금지** — 의존성 그래프 기반 순서.

---

## HOW TO: 새 서비스 추가

### 1. 서비스 클래스 생성

```python
# app/core/services/my_service.py
from typing import Any

class MyService:
    def __init__(self, db_service, redis_service=None):
        self.db = db_service
        self.redis = redis_service
    
    def get_all(self) -> list[dict]:
        return self.db.query("SELECT * FROM my_table")
    
    def create(self, data: dict) -> dict:
        # 비즈니스 로직 구현
        result = self.db.execute(
            "INSERT INTO my_table (name) VALUES (%s) RETURNING id",
            (data['name'],)
        )
        return {'id': result['id'], **data}
```

### 2. ServiceFactory에 등록

```python
# app/core/services/service_factory.py
class ServiceFactory:
    def __init__(self, app):
        self.app = app
        # ... 기존 초기화 ...
        self._init_my_service()  # 순서 중요!
    
    def _init_my_service(self):
        from core.services.my_service import MyService
        self.my_service = MyService(self.db_service)
        self.app.extensions['my_service'] = self.my_service
```

### 3. 라우트에서 사용

```python
# app/core/routes/api/my_api.py
@bp.route('/')
def list_items():
    service = current_app.extensions['my_service']
    return jsonify(service.get_all())
```

---

## CONVENTIONS (규약)

| 규약 | 내용 |
|------|------|
| **접근** | `current_app.extensions['service_name']` |
| **DB** | Raw SQL via `database_service.query()` (ORM 금지) |
| **복원력** | DB 연결에 Exponential Backoff |
| **캐싱** | Redis 사용 시 TTL 필수 |

---

## ANTI-PATTERNS (금지 사항)

| ❌ 금지 | ✅ 대안 | 이유 |
|---------|---------|------|
| `BlacklistService()` | ServiceFactory 등록 | DI 패턴 |
| `from services import X` | `current_app.extensions` | 순환 import |
| SQLAlchemy/Prisma | Raw SQL | 프로젝트 정책 |
| 서비스 간 직접 호출 | ServiceFactory 주입 | 결합도 |

---

## KEY FILES (핵심 파일)

| 파일 | Lines | 역할 | 주의 |
|------|-------|------|------|
| `service_factory.py` | 400L | DI 컨테이너 | 순서 변경 주의 |
| `blacklist_service.py` | 820L | IP 비즈니스 로직 | ⚠️ 복잡 |
| `database_service.py` | 300L | DB 인프라 | 커넥션 풀 |
