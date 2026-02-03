# REGTECH Local Agent

Cloudflare D1에 REGTECH 데이터를 수집/푸시하는 로컬 에이전트.

## 왜 필요한가?

CF Browser Rendering은 미국 등 해외 PoP에서 실행되어 REGTECH(한국 금융보안원)에 접근이 차단됨.
WARP를 통해 로컬에서 접근 가능하므로, 로컬에서 수집 후 CF D1로 푸시하는 패턴 사용.

## 설정

```bash
cd agent
cp .env.example .env
# .env 파일 편집하여 CF_INGEST_API_KEY 설정
```

### CF_INGEST_API_KEY 확인

```bash
source ~/.env
CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_KEY" npx wrangler secret list
```

## 사용법

### 일회성 수집 (최근 1일)
```bash
python regtech_agent.py
```

### 전체 수집 (90일)
```bash
python regtech_agent.py --full
```

### 날짜 범위 지정
```bash
python regtech_agent.py --start-date 2024-01-01 --end-date 2024-01-31
```

### 데몬 모드 (6시간 간격)
```bash
python regtech_agent.py --daemon
```

## 아키텍처

```
┌────────────────────┐
│   Local Agent      │ ← WARP 사용 (한국 IP)
│  (This Script)     │
└─────────┬──────────┘
          │ 1. Authenticate & Collect
          ▼
┌────────────────────┐
│     REGTECH        │
│  (fsec.or.kr)      │
└────────────────────┘
          │
          │ 2. Transform & Push
          ▼
┌────────────────────┐
│   CF Worker API    │
│  /api/collection/  │
│     ingest         │
└─────────┬──────────┘
          │ 3. Store
          ▼
┌────────────────────┐
│   Cloudflare D1    │
│   blacklist_ips    │
└────────────────────┘
```

## 로그

`agent.log` 파일에 기록됨.

## 문제 해결

### REGTECH 인증 실패
- WARP 연결 확인
- 자격증명 확인 (D1에도 저장되어 있음)

### CF API 401 Unauthorized
- CF_INGEST_API_KEY 확인
- Worker 재배포 필요할 수 있음
