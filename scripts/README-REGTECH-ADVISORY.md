# REGTECH 보안 권고사항 다운로드 스크립트

**URL**: https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryView

**용도**: 리눅스 서버 대상 점검도구 및 보안 권고사항 다운로드

---

## 🚀 Quick Start

### 기본 사용법

```bash
# CSV 다운로드 (기본)
python scripts/download-regtech-advisory.py

# JSON 다운로드
python scripts/download-regtech-advisory.py --format json

# CSV + JSON 둘 다
python scripts/download-regtech-advisory.py --format both

# 출력 디렉토리 지정
python scripts/download-regtech-advisory.py --output ./advisory_data
```

### 인증이 필요한 경우

```bash
# 환경변수 사용 (권장)
export REGTECH_ID=your_id
export REGTECH_PW=your_password
python scripts/download-regtech-advisory.py

# 커맨드라인 옵션
python scripts/download-regtech-advisory.py --username your_id --password your_password
```

---

## 📋 출력 형식

### CSV 출력 (regtech_advisory.csv)

```csv
id,title,createdAt,severity,targetOS,description,fileUrl
1,"리눅스 서버 보안 점검","2025-10-30","HIGH","Linux","...","/files/..."
2,"취약점 패치 권고","2025-10-29","MEDIUM","Linux","...","/files/..."
```

### JSON 출력 (regtech_advisory.json)

```json
[
  {
    "id": 1,
    "title": "리눅스 서버 보안 점검",
    "createdAt": "2025-10-30",
    "severity": "HIGH",
    "targetOS": "Linux",
    "description": "...",
    "fileUrl": "/files/..."
  }
]
```

---

## 🔧 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--format` | `csv` | 출력 포맷 (`csv`, `json`, `both`) |
| `--output` | `./regtech_advisory` | 출력 디렉토리 |
| `--max-pages` | `10` | 최대 페이지 수 |
| `--username` | - | REGTECH ID (또는 `REGTECH_ID` 환경변수) |
| `--password` | - | REGTECH 비밀번호 (또는 `REGTECH_PW` 환경변수) |

---

## 📁 출력 구조

```
regtech_advisory/
├── regtech_advisory.csv          # CSV 출력
├── regtech_advisory.json         # JSON 출력
├── advisory_1_20251030.pdf       # 첨부파일 1
├── advisory_2_20251030.zip       # 첨부파일 2
└── ...
```

---

## ⚠️ 중요 사항

### 1. 실제 API 구조 확인 필요

**현재 스크립트는 일반적인 REST API 패턴을 기반으로 작성되었습니다.**

실제 REGTECH 사이트에 접속 가능해지면 다음을 확인하여 수정해야 합니다:

```bash
# 브라우저 개발자 도구 → Network 탭에서 확인
1. 실제 API endpoint URL
2. Request parameters (page, size, sort 등)
3. Response JSON 구조
4. Authentication 방식
```

### 2. API Endpoint 수정 (필요 시)

**Line 67-83**: `fetch_advisory_list()` 함수에서 실제 API URL로 수정

```python
# 현재 (추정):
url = f"{self.base_url}/api/fcti/securityAdvisory/list"

# 실제 확인 후 수정 예시:
url = f"{self.base_url}/api/v1/advisories"
url = f"{self.base_url}/fcti/advisory/getList.json"
```

### 3. Response 구조 수정 (필요 시)

**Line 72-79**: JSON response 파싱 로직 수정

```python
# 실제 response 구조에 맞게 수정
if 'data' in resp.json():         # 또는
    return resp.json()['data']     # 'items', 'results' 등
```

---

## 🔍 실제 API 구조 확인 방법

### 방법 1: 브라우저 개발자 도구

1. https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryView 접속
2. F12 → Network 탭
3. 페이지 새로고침 또는 페이지네이션 클릭
4. XHR/Fetch 필터링
5. Request URL, Payload, Response 확인

### 방법 2: curl로 테스트

```bash
# 메인 페이지 HTML 확인
curl -s "https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryView" | less

# API endpoint 테스트 (추정)
curl -s "https://regtech.fsec.or.kr/api/fcti/securityAdvisory/list?page=1&size=10"

# 인증 필요 시
curl -s "https://regtech.fsec.or.kr/api/fcti/securityAdvisory/list" \
  -H "Cookie: SESSION=..." \
  -H "X-CSRF-TOKEN: ..."
```

### 방법 3: Python requests로 테스트

```python
import requests

# 세션 생성
session = requests.Session()

# 1. 페이지 접속 (쿠키 수집)
resp = session.get("https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryView")
print(resp.status_code)

# 2. API 호출 시도
resp = session.get("https://regtech.fsec.or.kr/api/fcti/securityAdvisory/list")
print(resp.json())  # 또는 resp.text
```

---

## 🛠️ 트러블슈팅

### "No advisory data retrieved"

**원인**: API endpoint가 잘못되었거나 인증 필요

**해결**:
1. 브라우저에서 실제 API URL 확인
2. 인증이 필요한 경우 `--username`, `--password` 제공
3. `fetch_advisory_list()` 함수의 URL 수정

### "HTML response received"

**원인**: API가 아닌 HTML 페이지 반환

**해결**:
- JSP/HTML 페이지인 경우 BeautifulSoup으로 파싱 필요
- 또는 실제 JSON API endpoint 찾기

```python
# HTML 파싱 예시
from bs4 import BeautifulSoup

soup = BeautifulSoup(resp.text, 'html.parser')
table = soup.find('table', {'id': 'advisory-table'})
# ... 테이블 파싱 로직
```

### "Authentication failed"

**원인**: REGTECH 인증 방식이 다름

**해결**:
- 기존 `regtech_auth.py` 참고
- `authenticate()` 함수 수정

---

## 📚 참고 코드

**기존 REGTECH 인증 코드**: `collector/api/regtech_auth.py`

```python
# Two-stage authentication
# 1. findOneMember (사용자 확인)
# 2. addLogin (세션 생성)
```

**기존 Excel 다운로드 코드**: `collector/collector/monitoring_scheduler.py`

---

## 🚀 실제 사용 예시 (접속 가능해지면)

```bash
# 1. 실제 API 확인 (브라우저 F12)
# → API URL: /api/v1/advisories/list

# 2. 스크립트 수정 (line 67)
# url = f"{self.base_url}/api/v1/advisories/list"

# 3. 실행
export REGTECH_ID=your_id
export REGTECH_PW=your_password
python scripts/download-regtech-advisory.py --format both

# 4. 결과 확인
ls -lh regtech_advisory/
cat regtech_advisory/regtech_advisory.json | jq .
```

---

**작성일**: 2025-10-30
**버전**: 1.0.0
**상태**: ⚠️ 템플릿 (실제 API 구조 확인 필요)

**실제 REGTECH 사이트 접속 가능해지면 API 구조 확인 후 수정 필수!**
