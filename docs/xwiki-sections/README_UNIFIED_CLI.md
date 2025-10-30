# XWiki 문서 관리 통합 CLI 도구 v3.0

## 🎯 개요

**하나의 도구로 모든 XWiki 문서 관리 작업을 수행**할 수 있는 Python 기반 크로스플랫폼 CLI 도구입니다.

### ✨ v3.0 주요 개선사항

| 구분 | v2.0 (레거시) | v3.0 (통합 CLI) |
|------|---------------|-----------------|
| **스크립트 수** | 5개 (Bash + PowerShell) | **1개** (Python) |
| **플랫폼** | Linux/macOS (Bash), Windows (PS) | **Windows/Linux/macOS** |
| **의존성** | curl, jq, bash/ps | **Python 3.7+, curl** |
| **기능 통합** | 분산 (각 스크립트별) | **통합** (서브커맨드) |
| **에러 처리** | 제한적 | **상세 (해결 방법 제시)** |
| **유지보수** | 어려움 (2개 언어) | **쉬움** (단일 코드베이스) |

---

## 📋 사전 준비

### 1️⃣ 필수 요구사항

```bash
# Python 3.7 이상
python3 --version

# curl (보통 기본 설치됨)
curl --version

# jq (선택적, 디버깅용)
sudo yum install jq -y  # RHEL/CentOS
# 또는
sudo apt install jq -y  # Ubuntu/Debian
```

### 2️⃣ XWiki 계정 정보

- **XWiki URL**: 예) `http://wiki.company.com:8080`
- **사용자명**: 본인의 XWiki 계정
- **비밀번호**: 본인의 XWiki 비밀번호
- **필수 권한**: 대상 Space에 **Edit** 권한

---

## 🚀 빠른 시작

### 방법 1: 대화형 모드 (추천 - 초보자용)

스크립트가 단계별로 정보를 물어봅니다:

```bash
cd /home/jclee/app/blacklist/docs/xwiki-sections

# 대화형 생성
python3 xwiki-manager.py create

# 실행 예시:
XWiki URL [http://localhost:8080]: http://wiki.mycompany.com:8080
사용자명 [admin]: jclee
비밀번호: ********
Wiki 이름 [xwiki]: xwiki
부모 Space [Main]: Main
부모 페이지명 [Blacklist]: Blacklist

# 자동으로 권한 체크 후 페이지 생성
```

### 방법 2: 배치 모드 (자동화용)

환경 변수로 모든 설정을 전달:

```bash
cd /home/jclee/app/blacklist/docs/xwiki-sections

# 환경 변수 설정
export XWIKI_URL="http://wiki.mycompany.com:8080"
export XWIKI_USER="jclee"
export XWIKI_PASS="MySecretPassword"
export PARENT_SPACE="Main"
export PARENT_PAGE="Blacklist"

# 배치 실행 (대화형 입력 없음)
python3 xwiki-manager.py create --batch
```

### 방법 3: 한 줄 명령 (CI/CD 파이프라인용)

```bash
XWIKI_URL="http://wiki.mycompany.com:8080" \
XWIKI_USER="jclee" \
XWIKI_PASS="MyPass" \
PARENT_PAGE="Blacklist" \
python3 xwiki-manager.py create --batch
```

---

## 📌 주요 기능 (서브커맨드)

### 1️⃣ `create` - 페이지 생성

모든 문서 페이지를 XWiki에 자동 생성합니다.

**옵션:**
- `--batch`: 대화형 입력 없이 환경 변수만 사용
- `--force`: 권한 체크 건너뛰기 (위험!)

**예시:**
```bash
# 대화형
python3 xwiki-manager.py create

# 배치 모드
python3 xwiki-manager.py create --batch

# 권한 체크 없이 강제 실행
python3 xwiki-manager.py create --force
```

---

### 2️⃣ `check` - 권한 확인

페이지 생성 권한이 있는지만 확인합니다 (페이지 생성 안 함).

**예시:**
```bash
# 기본 체크 (localhost)
python3 xwiki-manager.py check

# 커스텀 서버 체크
XWIKI_URL="http://wiki.mycompany.com:8080" \
XWIKI_USER="jclee" \
XWIKI_PASS="MyPass" \
python3 xwiki-manager.py check
```

**출력 예시:**
```
✅ 권한 확인 완료
ℹ  사용자 'jclee'는 'Main'에 페이지를 생성할 수 있습니다

✓ 자동 생성 스크립트를 실행할 수 있습니다:
  python xwiki-manager.py create
```

---

### 3️⃣ `validate` - 파일 검증

섹션 파일(00-08.txt)과 통합 파일이 모두 존재하는지 확인합니다.

**예시:**
```bash
python3 xwiki-manager.py validate
```

**출력 예시:**
```
📂 파일 검증
────────────────────────────────────────────────────────────
✓ 통합 파일: XWIKI_COMPLETE_SINGLE_PAGE.txt (72.0KB, 2962줄)
✓ 00-index.txt (1.7KB, 58줄)
✓ 01-deployment.txt (5.9KB, 198줄)
✓ 02-architecture.txt (10.0KB, 348줄)
...
────────────────────────────────────────────────────────────
✓ 모든 파일이 준비되었습니다
```

---

### 4️⃣ `list` - 페이지 목록

생성될 페이지 구조를 미리 확인합니다.

**예시:**
```bash
python3 xwiki-manager.py list
```

**출력 예시:**
```
생성될 페이지 구조
────────────────────────────────────────────────────────────
Main.Blacklist (부모 페이지 - 통합 문서)
  ├── 📑 목차 (Index)
      파일: 00-index.txt
      설명: 전체 문서 목차
  ├── 🚀 1. 설치 및 배포 (Deployment)
      파일: 01-deployment.txt
      설명: 오프라인 패키지 설치, Docker 배포
  ...
────────────────────────────────────────────────────────────
총 10개 페이지
```

---

## 🎨 사용 시나리오

### 시나리오 1: 첫 설치 (초보자)

```bash
cd /home/jclee/app/blacklist/docs/xwiki-sections

# 1단계: 파일 검증
python3 xwiki-manager.py validate

# 2단계: 권한 확인
python3 xwiki-manager.py check

# 3단계: 대화형 생성
python3 xwiki-manager.py create
```

### 시나리오 2: 빠른 배포 (숙련자)

```bash
# 한 번에 실행
XWIKI_URL=http://wiki.mycompany.com:8080 \
XWIKI_USER=jclee \
XWIKI_PASS='MyPass' \
PARENT_PAGE=Blacklist \
python3 xwiki-manager.py create --batch
```

### 시나리오 3: CI/CD 파이프라인

```yaml
# .gitlab-ci.yml 예시
deploy-xwiki-docs:
  stage: deploy
  script:
    - cd docs/xwiki-sections
    - |
      XWIKI_URL=${XWIKI_URL} \
      XWIKI_USER=${XWIKI_USER} \
      XWIKI_PASS=${XWIKI_PASS} \
      PARENT_SPACE=Documentation \
      PARENT_PAGE=Blacklist_v${CI_COMMIT_TAG} \
      python3 xwiki-manager.py create --batch --force
  only:
    - tags
```

### 시나리오 4: 개인 Space 사용 (권한 문제 해결)

```bash
# Main에 권한이 없을 때 → 개인 Space 사용
XWIKI_USER=jclee \
XWIKI_PASS='MyPass' \
PARENT_SPACE='XWiki.jclee' \
PARENT_PAGE='Blacklist' \
python3 xwiki-manager.py create --batch

# 생성 위치: XWiki.jclee.Blacklist
```

---

## 🔧 문제 해결

### 1. "curl이 설치되지 않았습니다"

```bash
# RHEL/CentOS
sudo yum install curl -y

# Ubuntu/Debian
sudo apt install curl -y

# macOS
brew install curl
```

### 2. "Python 3.7 이상 필요"

```bash
# Python 버전 확인
python3 --version

# RHEL 8/9 (이미 설치됨)
sudo yum install python3 -y

# Ubuntu
sudo apt install python3 -y
```

### 3. "권한 부족 (HTTP 403)"

**원인:** 대상 Space에 Edit 권한 없음

**해결 방법 A) 관리자에게 권한 요청**
1. XWiki 관리자 연락
2. Administration → Rights
3. Space 'Main' 선택
4. Users: 본인 계정 추가
5. Rights: **Edit** 체크

**해결 방법 B) 개인 Space 사용 (권장)**
```bash
PARENT_SPACE='XWiki.your_username' \
PARENT_PAGE='Blacklist' \
python3 xwiki-manager.py create
```

### 4. "인증 실패 (HTTP 401)"

- 사용자명/비밀번호 오타 확인
- XWiki 웹 UI로 로그인 테스트
- 계정 잠금/비활성화 여부 확인

### 5. "XWiki 연결 실패"

```bash
# XWiki 실행 여부 확인
curl http://localhost:8080/xwiki

# 포트 확인
netstat -tlnp | grep 8080
# 또는
ss -tlnp | grep 8080
```

---

## 📊 생성되는 구조

```
Main.Blacklist (부모 페이지 - 통합 문서 72KB)
├── Main.Blacklist.Index (1.7K) // 전체 문서 목차
├── Main.Blacklist.Deployment (5.9K) // 오프라인 패키지 설치, Docker 배포
├── Main.Blacklist.Architecture (10K) // 5개 컨테이너 구성, 차단 로직, ERD
├── Main.Blacklist.API (11K) // REST API 엔드포인트, 요청/응답 예시
├── Main.Blacklist.Diagrams (6.5K) // 네트워크 토폴로지, 시퀀스 다이어그램
├── Main.Blacklist.Upgrade (9.2K) // 블루-그린 배포, DB 마이그레이션, 롤백
├── Main.Blacklist.Security (7.5K) // 방화벽, SELinux, PostgreSQL 보안
├── Main.Blacklist.Troubleshooting (15K) // 일반적인 오류 해결 방법
└── Main.Blacklist.Appendix (4.9K) // 포트 목록, 명령어 모음, 체크리스트
```

**총 10개 페이지** (부모 1 + 자식 9)

---

## 🎨 PlantUML 설치 (다이어그램 렌더링)

문서에는 **13개의 PlantUML 다이어그램**이 포함되어 있습니다.

### 설치 방법

1. XWiki 관리자로 로그인
2. **Administration** → **Extensions**
3. 검색: `PlantUML Macro`
4. **Install** 클릭
5. 페이지 새로고침

---

## 🆚 v2.0 레거시 스크립트와 비교

| 기능 | v2.0 (레거시) | v3.0 (통합 CLI) |
|------|---------------|-----------------|
| **페이지 생성** | `xwiki-import.sh` / `xwiki-import.ps1` | `python3 xwiki-manager.py create` |
| **권한 체크** | `check-xwiki-permissions.sh` | `python3 xwiki-manager.py check` |
| **파일 검증** | 수동 확인 | `python3 xwiki-manager.py validate` |
| **페이지 목록** | README 참조 | `python3 xwiki-manager.py list` |
| **크로스플랫폼** | Bash(Linux) + PowerShell(Windows) | **Python (모든 OS)** |
| **에러 메시지** | 제한적 | **상세 + 해결 방법** |
| **유지보수** | 2개 언어, 5개 파일 | **1개 언어, 1개 파일** |

### 마이그레이션 가이드

**기존 (v2.0):**
```bash
./xwiki-import.sh
```

**새로운 (v3.0):**
```bash
python3 xwiki-manager.py create
```

**환경 변수는 동일하게 사용 가능:**
```bash
XWIKI_URL=... XWIKI_USER=... XWIKI_PASS=... python3 xwiki-manager.py create --batch
```

---

## 📚 참고 자료

- **XWiki REST API**: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI
- **XWiki 권한 관리**: https://www.xwiki.org/xwiki/bin/view/Documentation/AdminGuide/Access%20Rights/
- **PlantUML Extension**: https://extensions.xwiki.org/xwiki/bin/view/Extension/PlantUML%20Macro

---

## 🆘 도움말

### 전체 도움말

```bash
python3 xwiki-manager.py --help
```

### 서브커맨드 도움말

```bash
python3 xwiki-manager.py create --help
python3 xwiki-manager.py check --help
python3 xwiki-manager.py validate --help
python3 xwiki-manager.py list --help
```

---

## 📝 변경 이력

### v3.0 (2025-10-14) - 통합 CLI 버전

**추가:**
- ✅ Python 기반 크로스플랫폼 CLI
- ✅ 서브커맨드 구조 (create/check/validate/list)
- ✅ 배치 모드 (`--batch`)
- ✅ 파일 검증 기능
- ✅ 상세한 에러 메시지 및 해결 방법
- ✅ 진행 상황 시각화

**개선:**
- ✅ 5개 스크립트 → 1개 통합 도구
- ✅ Bash/PowerShell 분리 → Python 단일 코드베이스
- ✅ 수동 권한 체크 → 자동 통합

**Deprecated:**
- ⚠️ `create-xwiki-pages.sh` (→ `xwiki-manager.py create`)
- ⚠️ `xwiki-import.sh` (→ `xwiki-manager.py create`)
- ⚠️ `xwiki-import.ps1` (→ `xwiki-manager.py create`)
- ⚠️ `check-xwiki-permissions.sh` (→ `xwiki-manager.py check`)

### v2.0 (2024-10) - Bash/PowerShell 버전

- 권한 체크 + 페이지 생성 통합 (Bash)
- Windows PowerShell 지원 추가
- 경로 추적 및 파일 정보 표시

### v1.0 (2024-09) - 초기 버전

- 기본 페이지 생성 (Bash)
- 관리자 권한 필요

---

**작성: 정보보안팀**
**최종 업데이트: 2025-10-14**
