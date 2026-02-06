# COLLECTOR KNOWLEDGE BASE

**Generated:** 2026-02-06
**Role:** ETL 서비스 (데이터 수집)
**Parent:** [../AGENTS.md](../AGENTS.md)

---

## OVERVIEW

독립 ETL 서비스. 외부 소스에서 블랙리스트 데이터 수집, 정규화, DB 저장.
**app/과 완전 분리** — 별도 DB 커넥션 풀, 별도 프로세스.

---

## STRUCTURE

```
collector/
├── run_collector.py        # 진입점 (Port 8545)
├── config.py               # 환경 설정
├── scheduler.py            # 수집 스케줄링
├── scheduler_api.py        # 스케줄러 REST API
├── health_server.py        # 헬스 체크 서버
├── monitoring_scheduler.py # 모니터링 스케줄
└── core/                   # 수집 로직
    ├── database.py         # 독립 DB 풀
    ├── regtech_collector.py    # REGTECH 수집기 (922L)
    └── multi_source_collector.py # 멀티소스 수집기 (766L)
```

---

## WHERE TO LOOK

| 작업 | 위치 | 비고 |
|------|------|------|
| **수집 로직 수정** | `core/regtech_collector.py` | 메인 수집기 |
| **새 소스 추가** | `core/multi_source_collector.py` | 멀티소스 패턴 |
| **스케줄 변경** | `scheduler.py` | cron 형식 |
| **설정 변경** | `config.py` | 환경변수 기반 |
| **헬스체크** | `health_server.py` | K8s liveness/readiness |

---

## HOW TO: 새 수집 소스 추가

### 1. 수집기 클래스 생성

```python
# core/my_source_collector.py
from collector.core.database import CollectorDatabase

class MySourceCollector:
    def __init__(self, db: CollectorDatabase):
        self.db = db
    
    def collect(self) -> list[dict]:
        """외부 소스에서 데이터 수집"""
        raw_data = self._fetch_from_source()
        normalized = self._normalize(raw_data)
        return normalized
    
    def _fetch_from_source(self) -> list:
        # HTTP 호출 등 외부 통신
        pass
    
    def _normalize(self, raw: list) -> list[dict]:
        # 표준 형식으로 변환
        return [{'ip': item['address'], 'source': 'MY_SOURCE'} for item in raw]
```

### 2. 스케줄러에 등록

```python
# scheduler.py
from collector.core.my_source_collector import MySourceCollector

def schedule_my_source():
    collector = MySourceCollector(db)
    data = collector.collect()
    db.insert_blacklist(data)
```

### 3. API 엔드포인트 추가 (선택)

```python
# scheduler_api.py
@app.route('/api/force-collection/MY_SOURCE', methods=['POST'])
def force_my_source():
    schedule_my_source()
    return jsonify({'status': 'triggered'})
```

---

## CONVENTIONS (규약)

| 규약 | 내용 |
|------|------|
| **DB 접근** | `core/database.py` 독립 풀 사용 |
| **비동기** | 메인 스레드 블로킹 금지 |
| **재시도** | Exponential backoff 필수 |
| **로깅** | 구조화된 JSON 로그 |
| **격리** | `app/` 코드 import 금지 |

---

## ANTI-PATTERNS (금지 사항)

| ❌ 금지 | ✅ 대안 | 이유 |
|---------|---------|------|
| `from app.* import` | 독립 구현 | 서비스 경계 위반 |
| `time.sleep()` 루프 | APScheduler 사용 | 메인 스레드 블로킹 |
| 무한 재시도 | Backoff + 최대 횟수 | 리소스 고갈 |
| 동기 HTTP 대량 호출 | `aiohttp` / ThreadPool | 성능 |
| Hardcoded URLs | 환경변수 | Docker 호환성 |
| Mixed sync/async | 일관된 패턴 선택 | 데드락 위험 |

---

## KNOWN ISSUES (수정 필요)

### Hardcoded URLs (2 violations)

| 파일 | 라인 | 문제 |
|------|------|------|
| `fortimanager_uploader.py` | 36, 77 | Hardcoded app URL |

### Async 패턴 이슈

| 파일 | Lines | 문제 |
|------|-------|------|
| `core/regtech_collector.py` | 922 | Magic numbers, hardcoded URLs |
| `core/multi_source_collector.py` | 766 | Mixed sync/async, 데드락 위험 |
| `scheduler.py` | 603 | `time.sleep()` 블로킹 |

**수정 방향**: 환경변수 사용, 일관된 async 패턴

---

## COMMUNICATION

### 외부에서 수집 트리거

```bash
# HTTP API (컨테이너 내부에서)
curl -X POST http://blacklist-collector:8545/api/force-collection/REGTECH

# 결과 확인 (DB)
SELECT * FROM collection_history ORDER BY collected_at DESC LIMIT 1;
```

### 헬스체크

```bash
curl http://blacklist-collector:8545/health
# {"status": "healthy", "scheduler": "running"}
```

---

## KEY FILES (핵심 파일)

| 파일 | Lines | 역할 | 주의사항 |
|------|-------|------|---------|
| `core/regtech_collector.py` | 922L | REGTECH 수집 | ⚠️ 복잡 |
| `core/multi_source_collector.py` | 766L | 멀티소스 | ⚠️ 복잡 |
| `scheduler.py` | 200L | 스케줄링 | APScheduler 기반 |
| `config.py` | 100L | 설정 | 환경변수 |

---

## NOTES

- **독립 서비스**: `app/`과 코드 공유 없음. DB/Redis로만 통신.
- **레거시 제거**: `app/core/collectors/`는 **삭제됨** (8bcad163)
- **테스트**: `tests/unit/collector/`, `tests/integration/collector/` 참조
