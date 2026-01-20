# API ROUTES KNOWLEDGE BASE

**Generated:** 2026-01-17
**Role:** JSON API Surface (Flask)
**Parent:** [../../AGENTS.md](../../AGENTS.md)

---

## OVERVIEW

JSON REST API 레이어. **Thin Handlers 원칙** — 라우트는 검증/파싱 → 서비스 호출 → 응답 포맷팅만 수행.

---

## STRUCTURE

```
api/
├── ip_management_api.py    # ⚠️ 1050L 복잡 (IP CRUD/bulk)
├── system_api.py           # 시스템 상태
├── dashboard_api.py        # 대시보드 통계
├── analytics.py            # 분석 API
├── database_api.py         # DB 유틸리티
├── migration.py            # 스키마 엔드포인트 (민감)
├── collection/             # 수집 제어
├── blacklist/              # 블랙리스트 핵심
├── fortinet/               # FortiManager 연동
└── monitoring/             # 모니터링/메트릭
```

---

## WHERE TO LOOK

| 작업 | 위치 | 비고 |
|------|------|------|
| **IP CRUD/Bulk** | `ip_management_api.py` | ⚠️ 복잡, 헬퍼 추가 권장 |
| **시스템 통계** | `system_api.py`, `dashboard_api.py` | 프론트엔드 계약 유지 |
| **수집 제어** | `collection/` | collector 서비스 위임 |
| **블랙리스트** | `blacklist/` | 핵심 위협 인텔 |
| **FortiManager** | `fortinet/` | 디바이스 연동 |

---

## HOW TO: API 엔드포인트 추가

### 1. Blueprint 생성

```python
# app/core/routes/api/<feature>_api.py
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint('<feature>_api', __name__, url_prefix='/api/<feature>')

@bp.route('/', methods=['GET'])
def list_items():
    # ✅ CORRECT: DI로 서비스 접근
    service = current_app.extensions['<feature>_service']
    return jsonify(service.get_all())

@bp.route('/', methods=['POST'])
def create_item():
    data = request.get_json()
    service = current_app.extensions['<feature>_service']
    result = service.create(data)
    return jsonify(result), 201
```

### 2. Blueprint 등록

```python
# app/core/app.py (create_app 함수 내)
from core.routes.api.<feature>_api import bp as <feature>_bp
app.register_blueprint(<feature>_bp)
```

### 3. 에러 처리

```python
from core.errors import APIError

@bp.route('/<int:id>', methods=['GET'])
def get_item(id):
    service = current_app.extensions['<feature>_service']
    item = service.get(id)
    if not item:
        raise APIError("Item not found", status_code=404)
    return jsonify(item)
```

### 4. 테스트 추가

```python
# tests/unit/app/routes/test_<feature>_api.py
```

---

## CONVENTIONS (규약)

| 규약 | 내용 |
|------|------|
| **DI** | `current_app.extensions['service']` 사용 |
| **응답 형식** | JSON 일관성 유지 (프론트엔드 계약) |
| **에러** | RFC 7807 형식 (`core/errors/` 사용) |
| **보안** | 변경 작업은 CSRF/인증 필수 |

---

## ANTI-PATTERNS (금지 사항)

| ❌ 금지 | ✅ 대안 | 이유 |
|---------|---------|------|
| 라우트에 비즈니스 로직 | 서비스 레이어 위임 | 관심사 분리 |
| `from core.services import X` | `current_app.extensions` | 순환 import |
| HTML 응답 혼용 | `/api/` = JSON only | 명확한 분리 |
| 개별 `jsonify` 에러 | `APIError` 사용 | 일관성 |
