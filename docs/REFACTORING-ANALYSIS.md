# 파일 구조 리팩토링 의존성 분석

**날짜**: 2025-11-11
**브랜치**: feature/file-structure-refactoring

---

## 현재 Routes 구조 및 Blueprint 매핑

### API Blueprints (app.py에 등록됨)

| 파일명 | Blueprint 이름 | URL Prefix | 위치 |
|--------|----------------|------------|------|
| `statistics_api.py` | `statistics_api_bp` | `/api` | 루트 레벨 ❌ |
| `blacklist_api.py` | `blacklist_api_bp` | `/api` | 루트 레벨 ❌ |
| `database_api.py` | `database_api_bp` | - | api/ ✅ |
| `ip_management_api.py` | `ip_management_api_bp` | - | api/ ✅ |
| `fortinet_api.py` | `fortinet_api_bp` | `/api/fortinet` | 루트 레벨 ❌ |
| `multi_collection_api.py` | `multi_collection_bp` | - | 루트 레벨 ❌ |

### Web UI Blueprints

| 파일명 | Blueprint 이름 | URL Prefix | 위치 |
|--------|----------------|------------|------|
| `web_routes.py` | `web_bp` | - | 루트 레벨 ⚠️ |
| `regtech_admin_routes.py` | `regtech_admin_bp` | `/admin` | 루트 레벨 ❌ |
| `settings_routes.py` | `settings_bp` | - | 루트 레벨 ❌ |
| `collection_panel.py` | `collection_bp` | `/collection-panel` | 루트 레벨 ❌ |
| `collection_routes_simple.py` | `collection_simple_bp` | `/collection` | 루트 레벨 ❌ |
| `monitoring_dashboard.py` | `monitoring_dashboard_bp` | - | 루트 레벨 ❌ |

### 특수 Blueprints

| 파일명 | Blueprint 이름 | URL Prefix | 위치 |
|--------|----------------|------------|------|
| `proxy_routes.py` | `proxy_bp` | - | 루트 레벨 ❌ |
| `detection_analytics.py` | `detection_bp` | `/analytics` | 루트 레벨 ❌ |
| `migration_routes.py` | `migration_bp` | `/api/migration` | 루트 레벨 ❌ |

---

## 리팩토링 계획

### Phase 2: Routes 재구조화 (간소화 구조 채택)

#### 이동 계획

**API Routes** (→ `routes/api/`):
```
blacklist_api.py         → api/blacklist.py
statistics_api.py        → api/statistics.py
fortinet_api.py          → api/fortinet.py
multi_collection_api.py  → api/collection.py
migration_routes.py      → api/migration.py
detection_analytics.py   → api/analytics.py
```

**Web UI Routes** (→ `routes/web/`):
```
web_routes.py            → web/dashboard.py (통합)
regtech_admin_routes.py  → web/admin.py
settings_routes.py       → web/settings.py
collection_panel.py      → web/collection_panel.py
monitoring_dashboard.py  → web/monitoring.py
```

**기타**:
```
collection_routes_simple.py → 삭제 (collection_panel.py와 중복)
proxy_routes.py          → 유지 (routes/proxy.py)
websocket_routes.py      → 유지 (routes/websocket.py)
```

---

## 백업 파일 제거 완료

### 제거된 파일 (2025-11-11)
- ✅ `app/core/routes/multi_collection_api.py.bak.20251028-105310`
- ✅ `app/core/routes/multi_collection_api.py.bak.20251028-105336`

---

## 다음 단계

1. ✅ Git 브랜치 생성 완료
2. ✅ 백업 파일 제거 완료
3. ✅ 의존성 분석 완료
4. ⏭️ **다음**: Routes 디렉토리 구조 생성 및 파일 이동

---

**작성자**: Claude Code (AI Assistant)
**참고 문서**: `docs/FILE-STRUCTURE-REFACTORING-GUIDE.md`
