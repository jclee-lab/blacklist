# APP KNOWLEDGE BASE

**Generated:** 2026-02-06
**Role:** Core Flask API Service
**Parent:** [../AGENTS.md](../AGENTS.md)

---

## OVERVIEW

Flask REST API 서비스. Next.js 대시보드에 JSON API 제공, 레거시 Jinja2 Admin UI 유지.
**Manual DI 철학** — 복잡한 Flask 환경에서 순환 의존성 방지.

---

## STRUCTURE

```
app/
├── run_app.py              # 진입점 (Port 2542)
├── core/
│   ├── app.py              # Application Factory
│   ├── services/           # 서비스 레이어 (16+ services)
│   │   └── service_factory.py  # DI 컨테이너
│   ├── routes/
│   │   ├── api/            # JSON API (RFC 7807)
│   │   └── web/            # HTML (Legacy Admin)
│   └── database/           # Raw SQL 인프라
├── templates/              # Jinja2 템플릿 (Legacy)
└── static/                 # 정적 자산 (Legacy)
```

---

## WHERE TO LOOK

| 작업 | 위치 | 참조 |
|------|------|------|
| **API 엔드포인트 추가** | `core/routes/api/` | → HOW TO 섹션 |
| **비즈니스 로직 추가** | `core/services/` | → `services/AGENTS.md` |
| **서비스 초기화 순서** | `core/services/service_factory.py` | 의존성 순서 중요 |
| **DB 쿼리** | `core/database/` | Raw SQL만 허용 |
| **Legacy Admin** | `templates/`, `routes/web/` | 수정 최소화 권장 |

---

## HOW TO: API 엔드포인트 추가

### 1. 라우트 파일 생성/수정

```python
# core/routes/api/my_feature_api.py
from flask import Blueprint, jsonify, current_app

bp = Blueprint('my_feature', __name__, url_prefix='/api/my-feature')

@bp.route('/', methods=['GET'])
def list_items():
    # ✅ CORRECT: current_app.extensions로 서비스 접근
    my_service = current_app.extensions['my_service']
    
    items = my_service.get_all()
    return jsonify({'items': items})
```

### 2. Blueprint 등록

```python
# core/routes/__init__.py
from .api import my_feature_api

def register_blueprints(app):
    # ... 기존 등록 ...
    app.register_blueprint(my_feature_api.bp)
```

### 3. 서비스가 필요한 경우

```python
# core/services/my_service.py
class MyService:
    def __init__(self, db_service):
        self.db = db_service
    
    def get_all(self):
        return self.db.query("SELECT * FROM my_table")

# core/services/service_factory.py 에 추가
def _init_my_service(self):
    self.my_service = MyService(self.db_service)
    self.app.extensions['my_service'] = self.my_service
```

---

## CONVENTIONS (규약)

| 규약 | 내용 |
|------|------|
| **DI 접근** | `current_app.extensions['service_name']` 사용 |
| **SQL** | Raw SQL만 (ORM 금지) |
| **라우트 분리** | `api/` = JSON, `web/` = HTML (혼용 금지) |
| **에러 응답** | RFC 7807 형식 (JSON API) |
| **보안** | `web/` CSRF 필수, `api/` Bearer/Session 토큰 |

---

## ANTI-PATTERNS (금지 사항)

| ❌ 금지 | ✅ 대안 | 이유 |
|---------|---------|------|
| `from app.core.services import X` | `current_app.extensions['x']` | 순환 import |
| `BlacklistService()` | ServiceFactory 사용 | DI 패턴 위반 |
| `from run_app import app` | `current_app` 프록시 | 전역 객체 금지 |
| SQL 문자열 연결 | 파라미터화 쿼리 | SQL Injection |
| `app/core/main.py` 복원 | — | **삭제됨** |
| Hardcoded URLs | 환경변수 사용 | Docker 호환성 |

---

## KNOWN ISSUES (수정 필요)

### Hardcoded URLs (5 violations)

| 파일 | 라인 | 문제 |
|------|------|------|
| `routes/api/collection/utils.py` | 13 | Hardcoded collector URL |
| `routes/api/blacklist/collection.py` | 54 | Hardcoded collector URL |
| `services/blacklist_service.py` | 420, 462, 510 | localhost/container 혼용 |

**수정 방향**: `COLLECTOR_URL` 환경변수 사용

---

## KEY FILES (핵심 파일)

| 파일 | Lines | 역할 | 주의사항 |
|------|-------|------|---------|
| `routes/api/ip_management_api.py` | 1050L | IP 관리 API | ⚠️ 복잡, 테스트 필수 |
| `services/blacklist_service.py` | 820L | 블랙리스트 로직 | ⚠️ 복잡 |
| `services/service_factory.py` | 400L | DI 컨테이너 | 초기화 순서 중요 |
| `core/app.py` | 200L | Factory | 설정 로드 |

---

## MIGRATION STATUS

> **✅ COMPLETED: `app/core/collectors/` 삭제됨**
> 
> 수집 로직은 독립 `collector/` 서비스로 이전.
> 수집 트리거:
> 1. **HTTP**: `http://blacklist-collector:8545/api/force-collection/REGTECH`
> 2. **DB**: `collection_history` 테이블에서 결과 조회

---

## NOTES

- **서비스 초기화 순서**: `service_factory.py`의 `_init_*` 메서드 순서가 중요
- **테스트**: `tests/unit/app/`, `tests/integration/app/` 참조
- **복잡한 파일**: 수정 전 관련 테스트 확인 권장
