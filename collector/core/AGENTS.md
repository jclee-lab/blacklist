# COLLECTOR CORE KNOWLEDGE BASE

**Generated:** 2026-02-06
**Role:** ETL Pipeline & Data Normalization
**Parent:** [../AGENTS.md](../AGENTS.md)

---

## OVERVIEW

핵심 데이터 수집 로직. **모듈형 ETL** — Rate Limiting, 데이터 정규화 지원.

---

## STRUCTURE

```
core/
├── regtech_collector.py      # 메인 ETL 오케스트레이터 (922L ⚠️)
├── regtech_parsers.py        # HTML/JSON 파싱 (추출 모듈)
├── regtech_excel.py          # Excel 처리 (추출 모듈)
├── multi_source_collector.py # 10+ 외부 피드, async (766L ⚠️)
├── database.py               # 독립 DB 풀 (maxconn=20)
├── authentication.py         # 자격증명 복호화 (Fernet)
└── data_normalizer.py        # IP 형식 표준화
```

---

## KEY COMPONENTS

| File | Purpose | Complexity |
|------|---------|------------|
| `regtech_collector.py` | Multi-stage auth, JWT refresh | ⚠️ High |
| `regtech_parsers.py` | HTML table + JSON parsing | Medium |
| `regtech_excel.py` | pandas Excel extraction | Medium |
| `multi_source_collector.py` | Async semaphore, URLhaus/PhishTank | ⚠️ High |

---

## HOW TO: 새 파서 추가

### 1. 파서 함수 작성

```python
# core/regtech_parsers.py
def parse_new_format(html_content: str) -> list[dict]:
    """새 형식 HTML 파싱"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    for row in soup.select('table.data tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            results.append({
                'ip': cells[0].text.strip(),
                'source': 'NEW_SOURCE',
                'category': cells[1].text.strip()
            })
    
    return results
```

### 2. Collector에서 사용

```python
# core/regtech_collector.py
from collector.core.regtech_parsers import parse_new_format

class RegtechCollector:
    def _collect_new_source(self):
        html = self._fetch_page(self.urls['new_source'])
        data = parse_new_format(html)
        self._save_to_db(data)
```

---

## CONVENTIONS (규약)

| 규약 | 내용 |
|------|------|
| **모듈화** | 파싱 → `regtech_parsers.py`, Excel → `regtech_excel.py` |
| **Rate Limit** | DB 기반 소스별 간격 설정 |
| **Idempotency** | `ON CONFLICT DO UPDATE` 필수 |
| **Error Recovery** | 소스 실패 시 Exponential Backoff |

---

## ANTI-PATTERNS (금지 사항)

| ❌ 금지 | ✅ 대안 | 이유 |
|---------|---------|------|
| Collector 내 파싱 로직 | 별도 파서 모듈 | 관심사 분리 |
| 직접 DB 쓰기 | 트랜잭션 컨텍스트 | 원자성 |
| 하드코딩 간격 | DB `SourceConfig` | 유연성 |
| 동기 HTTP 대량 호출 | `aiohttp` / ThreadPool | 성능 |
