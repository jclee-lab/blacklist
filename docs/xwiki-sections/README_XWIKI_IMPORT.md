# XWiki 자동 Import 가이드 v2.0

## 🎯 개요

일반 사용자 계정으로 XWiki에 **블랙리스트 문서를 자동으로 생성**하는 가이드입니다.

**✨ 주요 기능:**
- ✅ 관리자 권한 불필요 (Edit 권한만 있으면 됨)
- ✅ 크로스 플랫폼 지원 (Linux/macOS/Windows)
- ✅ 경로 추적 (디렉토리 이동 과정 표시)
- ✅ 실시간 생성 진행상황 (파일명 + 섹션 설명)
- ✅ 시각적 트리 구조 출력
- ✅ 파일 크기 및 라인 수 표시
- ✅ 권한 문제 자동 해결 가이드

---

## 📋 사전 준비

### 1️⃣ 필수 도구 설치

**Linux/macOS:**
```bash
# jq (JSON 처리)
sudo yum install jq -y        # RHEL/CentOS
# 또는
sudo apt install jq -y        # Ubuntu

# curl (HTTP 클라이언트 - 보통 기본 설치됨)
which curl || sudo yum install curl -y
```

**Windows:**
- PowerShell 5.1 이상 (기본 설치됨)
- 추가 도구 불필요 (`Invoke-WebRequest` 내장)

### 2️⃣ XWiki 계정 정보 확인

- **XWiki URL**: 예) `http://wiki.company.com:8080`
- **사용자명**: 본인의 XWiki 계정
- **비밀번호**: 본인의 XWiki 비밀번호

---

## ✅ Step 1: 권한 확인

먼저 페이지 생성 권한이 있는지 확인합니다:

```bash
cd /home/jclee/app/blacklist/docs/xwiki-sections

# 기본 설정 (localhost)
./check-xwiki-permissions.sh

# 커스텀 설정
XWIKI_URL="http://your-wiki.com:8080" \
XWIKI_USER="your_username" \
XWIKI_PASS="your_password" \
SPACE="Main" \
./check-xwiki-permissions.sh
```

### 결과 해석

#### ✅ 성공 (HTTP 200/201)
```
✅ 성공: your_username는 Main에 페이지를 생성할 수 있습니다!
   HTTP Code: 201

✅ 자동 생성 스크립트를 실행할 수 있습니다:
   XWIKI_USER=your_username XWIKI_PASS='***' ./create-xwiki-pages.sh
```
→ **Step 2로 진행하세요!**

#### ❌ 권한 부족 (HTTP 403)
```
❌ 실패: 권한 부족 (HTTP 403)
   your_username는 Main에 페이지를 생성할 권한이 없습니다.
```

**해결 방법 2가지:**

**방법 A) 관리자에게 권한 요청**
1. XWiki 관리자에게 연락
2. `Main` Space (또는 원하는 Space)에 **Edit 권한** 요청
3. 관리자 작업:
   - XWiki → Administration → Rights
   - Space: `Main` 선택
   - Users: `your_username` 추가
   - Rights: **Edit** 체크
   - 저장

**방법 B) 개인 Space 사용 (권장)**
```bash
# 본인 이름의 개인 Space는 자동으로 Edit 권한 보유
SPACE="XWiki.your_username" ./check-xwiki-permissions.sh

# 성공 시 개인 Space에 생성
PARENT_SPACE="XWiki.your_username" \
PARENT_PAGE="Blacklist" \
./create-xwiki-pages.sh
```

#### ❌ 인증 실패 (HTTP 401)
```
❌ 실패: 인증 오류 (HTTP 401)
   사용자명 또는 비밀번호가 잘못되었습니다.
```
→ 사용자명과 비밀번호 확인

---

## 🚀 Step 2: 자동 생성 실행

권한 확인이 완료되면 자동 생성 스크립트를 실행합니다.

### Linux/macOS (Bash)

#### 기본 사용 (Main Space)

```bash
cd /home/jclee/app/blacklist/docs/xwiki-sections

XWIKI_URL="http://your-wiki.com:8080" \
XWIKI_USER="your_username" \
XWIKI_PASS="your_password" \
PARENT_PAGE="Blacklist" \
./xwiki-import.sh
```

#### 개인 Space 사용

```bash
XWIKI_URL="http://your-wiki.com:8080" \
XWIKI_USER="your_username" \
XWIKI_PASS="your_password" \
PARENT_SPACE="XWiki.your_username" \
PARENT_PAGE="Blacklist" \
./xwiki-import.sh
```

### Windows (PowerShell)

#### 기본 사용 (Main Space)

```powershell
cd C:\path\to\xwiki-sections

$env:XWIKI_URL = "http://your-wiki.com:8080"
$env:XWIKI_USER = "your_username"
$env:XWIKI_PASS = "your_password"
$env:PARENT_PAGE = "Blacklist"
.\xwiki-import.ps1
```

#### 개인 Space 사용

```powershell
$env:XWIKI_URL = "http://your-wiki.com:8080"
$env:XWIKI_USER = "your_username"
$env:XWIKI_PASS = "your_password"
$env:PARENT_SPACE = "XWiki.your_username"
$env:PARENT_PAGE = "Blacklist"
.\xwiki-import.ps1
```

#### 도움말

```powershell
Get-Help .\xwiki-import.ps1 -Full
```

### 전체 옵션

**Bash:**
```bash
XWIKI_URL="http://wiki.company.com:8080"    # XWiki URL
XWIKI_USER="jclee"                           # 사용자명
XWIKI_PASS="MyP@ssw0rd"                      # 비밀번호
WIKI_NAME="xwiki"                            # Wiki 이름 (기본: xwiki)
PARENT_SPACE="Main"                          # 부모 Space (기본: Main)
PARENT_PAGE="BlacklistSystem"                # 부모 페이지 이름
./xwiki-import.sh
```

**PowerShell:**
```powershell
$env:XWIKI_URL = "http://wiki.company.com:8080"   # XWiki URL
$env:XWIKI_USER = "jclee"                         # 사용자명
$env:XWIKI_PASS = "MyP@ssw0rd"                    # 비밀번호
$env:WIKI_NAME = "xwiki"                          # Wiki 이름 (기본: xwiki)
$env:PARENT_SPACE = "Main"                        # 부모 Space (기본: Main)
$env:PARENT_PAGE = "BlacklistSystem"              # 부모 페이지 이름
.\xwiki-import.ps1
```

---

## 📊 생성되는 구조

```
Main.BlacklistSystem (부모 페이지 - 통합 문서)
├── Main.BlacklistSystem.Index             (0. 목차)
├── Main.BlacklistSystem.Deployment        (1. 설치 및 배포)
├── Main.BlacklistSystem.Architecture      (2. 시스템 아키텍처)
├── Main.BlacklistSystem.API               (3. API 사용법)
├── Main.BlacklistSystem.Diagrams          (4. 다이어그램 모음)
├── Main.BlacklistSystem.Upgrade           (5. 업그레이드 가이드)
├── Main.BlacklistSystem.Security          (6. 보안 설정)
├── Main.BlacklistSystem.Troubleshooting   (7. 문제 해결)
└── Main.BlacklistSystem.Appendix          (8. 부록)
```

**총 10개 페이지 생성** (부모 1 + 자식 9)

---

## 📌 실행 예시 (v2.0)

```bash
$ cd /home/jclee/app/blacklist/docs/xwiki-sections

$ XWIKI_URL="http://wiki.mycompany.com:8080" \
  XWIKI_USER="jclee" \
  XWIKI_PASS="MySecretPassword" \
  PARENT_PAGE="Blacklist" \
  ./xwiki-import.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ██╗  ██╗██╗    ██╗██╗██╗  ██╗██╗
  ╚██╗██╔╝██║    ██║██║██║ ██╔╝██║
   ╚███╔╝ ██║ █╗ ██║██║█████╔╝ ██║
   ██╔██╗ ██║███╗██║██║██╔═██╗ ██║
  ██╔╝ ██╗╚███╔███╔╝██║██║  ██╗██║
  ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚═╝

  블랙리스트 문서 자동 Import 스크립트
  권한 체크 + 페이지 생성 통합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[INFO] XWiki URL: http://wiki.mycompany.com:8080
[INFO] Wiki Name: xwiki
[INFO] 사용자: jclee
[INFO] 대상 Space: Main
[INFO] 부모 페이지: Blacklist

[INFO] 📂 스크립트 위치: /home/jclee/app/blacklist/docs/xwiki-sections
[INFO] 📂 현재 디렉토리: /home/jclee
[INFO] 📂 디렉토리 이동: /home/jclee → /home/jclee/app/blacklist/docs/xwiki-sections
[✓] 📂 작업 디렉토리: /home/jclee/app/blacklist/docs/xwiki-sections

[STEP] STEP 1/4: XWiki 연결 확인

[✓] XWiki 연결 성공

[STEP] STEP 2/4: 권한 확인

[✓] 권한 확인 완료!
[INFO] 사용자 'jclee'는 'Main'에 페이지를 생성할 수 있습니다.

[STEP] STEP 3/4: 부모 페이지 생성

📄 Main.Blacklist
[INFO] 📂 통합 파일 경로: /home/jclee/app/blacklist/docs/XWIKI_COMPLETE_SINGLE_PAGE.txt
[INFO] 📄 파일 크기: 72K (2962 줄)

[✓] 블랙리스트 관리 시스템 (Blacklist Management System)

[STEP] STEP 4/4: 하위 페이지 생성 (9개)

📂 Main.Blacklist

   ├── 📑 목차 (Index) ← 00-index.txt ✓ // 전체 문서 목차
   ├── 🚀 1. 설치 및 배포 (Deployment) ← 01-deployment.txt ✓ // 오프라인 패키지 설치, Docker 배포
   ├── 🏗️  2. 시스템 아키텍처 (Architecture) ← 02-architecture.txt ✓ // 5개 컨테이너 구성, 차단 로직, ERD
   ├── 📡 3. API 사용법 (API) ← 03-api.txt ✓ // REST API 엔드포인트, 요청/응답 예시
   ├── 📊 4. 다이어그램 모음 (Diagrams) ← 04-diagrams.txt ✓ // 네트워크 토폴로지, 시퀀스 다이어그램
   ├── 🔄 5. 업그레이드 가이드 (Upgrade) ← 05-upgrade.txt ✓ // 블루-그린 배포, DB 마이그레이션, 롤백
   ├── 🔐 6. 보안 설정 (Security) ← 06-security.txt ✓ // 방화벽, SELinux, PostgreSQL 보안
   ├── 🔧 7. 문제 해결 (Troubleshooting) ← 07-troubleshooting.txt ✓ // 일반적인 오류 해결 방법
   └── 📝 8. 부록 (Appendix) ← 08-appendix.txt ✓ // 포트 목록, 명령어 모음, 체크리스트

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[✓] 작업 완료!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[INFO] 생성 성공: 10개 페이지

[INFO] 📄 접속 URL:
  http://wiki.mycompany.com:8080/bin/view/Main/Blacklist

[INFO] 📊 생성된 페이지 구조 (XWiki 경로):

  Main.Blacklist (부모 - 통합 문서 72KB)
  ├── Main.Blacklist.Index (1.7K) // 전체 문서 목차
  ├── Main.Blacklist.Deployment (5.9K) // 오프라인 패키지 설치, Docker 배포
  ├── Main.Blacklist.Architecture (10K) // 5개 컨테이너 구성, 차단 로직, ERD
  ├── Main.Blacklist.API (11K) // REST API 엔드포인트, 요청/응답 예시
  ├── Main.Blacklist.Diagrams (6.5K) // 네트워크 토폴로지, 시퀀스 다이어그램
  ├── Main.Blacklist.Upgrade (9.2K) // 블루-그린 배포, DB 마이그레이션, 롤백
  ├── Main.Blacklist.Security (7.5K) // 방화벽, SELinux, PostgreSQL 보안
  ├── Main.Blacklist.Troubleshooting (15K) // 일반적인 오류 해결 방법
  └── Main.Blacklist.Appendix (4.9K) // 포트 목록, 명령어 모음, 체크리스트

[⚠] ⚠️  PlantUML Macro 설치 필요 (다이어그램 13개):
  http://wiki.mycompany.com:8080/bin/admin/XWiki/XWikiPreferences?section=Extensions
  검색: 'PlantUML Macro' → Install
```

---

## 🎨 Step 3: PlantUML 설치 (다이어그램 렌더링)

문서에는 **13개의 PlantUML 다이어그램**이 포함되어 있습니다.

### 설치 방법

1. XWiki 관리자 로그인
2. **Administration** → **Extensions**
3. 검색: `PlantUML Macro`
4. **Install** 클릭
5. 페이지 새로고침

### 설치 확인

PlantUML 설치 전:
```
{{plantuml}}
@startuml
...
@enduml
{{/plantuml}}
```
→ 코드가 그대로 보임

PlantUML 설치 후:
```
[시각적 다이어그램 렌더링]
```
→ 아름다운 다이어그램으로 표시

---

## 📊 새로운 기능 (v2.0)

### 🔍 경로 추적
스크립트가 실행되는 디렉토리를 명확히 표시합니다:
```
[INFO] 📂 스크립트 위치: /home/jclee/app/blacklist/docs/xwiki-sections
[INFO] 📂 현재 디렉토리: /home/jclee
[INFO] 📂 디렉토리 이동: /home/jclee → /home/jclee/app/blacklist/docs/xwiki-sections
```

### 📄 파일 정보 표시
업로드하는 파일의 크기와 라인 수를 표시합니다:
```
[INFO] 📂 통합 파일 경로: .../XWIKI_COMPLETE_SINGLE_PAGE.txt
[INFO] 📄 파일 크기: 72K (2962 줄)
```

### 📝 섹션 설명
각 페이지가 무엇을 다루는지 한눈에 볼 수 있습니다:
```
├── 🚀 1. 설치 및 배포 (Deployment) ← 01-deployment.txt ✓
    // 오프라인 패키지 설치, Docker 배포
```

### 📊 최종 구조 요약
파일 크기와 함께 전체 구조를 보여줍니다:
```
Main.Blacklist (부모 - 통합 문서 72KB)
├── Main.Blacklist.Architecture (10K) // 5개 컨테이너 구성, 차단 로직, ERD
├── Main.Blacklist.Upgrade (9.2K) // 블루-그린 배포, DB 마이그레이션, 롤백
```

---

## 🔧 문제 해결

### 1. "jq: command not found"

```bash
# RHEL/CentOS
sudo yum install jq -y

# Ubuntu/Debian
sudo apt install jq -y
```

### 2. "Connection refused"

```bash
# XWiki가 실행 중인지 확인
curl http://localhost:8080/xwiki

# 포트 확인
netstat -tlnp | grep 8080
```

### 3. "401 Unauthorized"

- 사용자명 또는 비밀번호 오류
- XWiki 계정이 잠겼거나 비활성화됨
- XWiki 웹 UI로 로그인 테스트

### 4. "403 Forbidden"

- Edit 권한 없음
- **해결**: 관리자에게 권한 요청 또는 개인 Space 사용

### 5. "페이지가 깨져 보임"

- PlantUML Macro 미설치
- **해결**: Step 3 참조

---

## 📚 참고 자료

- **XWiki REST API 공식 문서**: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI
- **XWiki 권한 관리**: https://www.xwiki.org/xwiki/bin/view/Documentation/AdminGuide/Access%20Rights/
- **PlantUML Extension**: https://extensions.xwiki.org/xwiki/bin/view/Extension/PlantUML%20Macro

---

## 🆘 도움이 필요하신가요?

**Bash:**
```bash
# 통합 스크립트 도움말
./xwiki-import.sh --help

# 권한만 체크
./xwiki-import.sh --check-only

# 권한 체크 스킵 (강제 실행)
./xwiki-import.sh --force
```

**PowerShell:**
```powershell
# 통합 스크립트 도움말
Get-Help .\xwiki-import.ps1 -Full

# 권한만 체크
.\xwiki-import.ps1 -CheckOnly

# 권한 체크 스킵 (강제 실행)
.\xwiki-import.ps1 -Force
```

**작성: 정보보안팀**
