# XWiki 배포 권한 가이드

**Generated:** 2025-10-21
**Version:** 1.0
**Status:** ✅ COMPLETE

---

## 📋 개요

XWiki 문서 배포 시 **사용자 권한에 따라 사용 가능한 방법이 다릅니다**.

이 가이드는 권한 상황별 최적의 배포 방법을 안내합니다.

---

## ⚠️ 권한 확인

### XWiki 관리자(Admin) 권한 확인 방법

```
1. XWiki 로그인
2. 우측 상단 프로필 아이콘 클릭
3. "Administer Wiki" 메뉴가 보이는가?
   - ✅ 보임 → 관리자 권한 있음
   - ❌ 안 보임 → 일반 사용자 권한
```

---

## 🚀 권한별 배포 방법

### ✅ 관리자 권한 있음

**추천 방법: XAR Import (가장 빠름)**

소요 시간: **30초**

#### Step 1: XAR 파일 준비
```bash
# 오프라인 패키지에서
offline-packages/docs/xwiki-sections/blacklist-docs.xar (40KB)

# 또는 소스에서
docs/xwiki-sections/blacklist-docs.xar
```

#### Step 2: XWiki Admin 페이지 접속
```
http://your-xwiki-domain:8080/xwiki/bin/admin/XWiki/XWikiPreferences?section=Import
```

#### Step 3: XAR 업로드
1. "Choose file" 클릭
2. `blacklist-docs.xar` 선택
3. "Upload" 클릭

#### Step 4: Import 옵션 설정
```
✅ Import as backup package
✅ Preserve document history
Target space: Main (또는 원하는 space)
```

#### Step 5: Import 실행
```
"Import" 버튼 클릭

결과:
- 12개 페이지 자동 생성
- 계층 구조 자동 설정
  - Blacklist Documentation (부모)
    - 00. Index (자식)
    - 01. Deployment Guide (자식)
    - ... (총 11개 자식 페이지)
```

---

### ⚠️ 관리자 권한 없음 (일반 사용자)

**추천 방법: 수동 복사/붙여넣기**

소요 시간: **10-15분**

#### 장점
- ✅ 관리자 권한 불필요
- ✅ 일반 사용자 계정만 있으면 OK
- ✅ 혼자서 완료 가능

#### 단점
- ⏱️ 시간이 걸림 (11개 페이지 × 1-2분)
- 🔄 반복 작업

#### 상세 단계

**Step 1: 템플릿 파일 준비**
```bash
# 오프라인 패키지에서
cd offline-packages/docs/xwiki-sections/

# 또는 소스에서
cd docs/xwiki-sections/

# 11개 .txt 파일 확인
ls -1 *.txt
00-index.txt
01-deployment.txt
02-architecture.txt
03-api.txt
03-api-auto.txt
04-diagrams.txt
04-diagrams-mermaid.txt
05-upgrade.txt
06-security.txt
07-troubleshooting.txt
08-appendix.txt
09-dashboard.txt (있다면)
10-monitoring.txt (있다면)
```

**Step 2: XWiki 로그인**
```
http://your-xwiki-domain:8080/xwiki

일반 사용자 계정으로 로그인
```

**Step 3: 첫 번째 페이지 생성 (00-index.txt)**

1. **페이지 생성 시작**
   - 좌측 메뉴: "Create" → "Page"
   - 또는 URL 직접 접속: `http://xwiki-domain/xwiki/bin/create/Main/`

2. **페이지 정보 입력**
   ```
   Page title: 00. Index
   (또는 "Blacklist Documentation Index")

   Parent: 없음 (첫 페이지이므로)
   Location: Main space (기본값)
   ```

3. **템플릿 선택**
   ```
   Template: Blank (빈 페이지)
   ```

4. **Create 클릭**

5. **내용 붙여넣기**
   ```
   a. 로컬에서 00-index.txt 파일 열기
   b. 내용 전체 선택 (Ctrl+A)
   c. 복사 (Ctrl+C)
   d. XWiki 에디터로 이동
   e. Wiki 모드 선택 (Source 또는 Wiki 탭)
   f. 붙여넣기 (Ctrl+V)
   ```

6. **저장**
   ```
   하단 "Save & View" 버튼 클릭
   ```

**Step 4: 나머지 페이지 생성 (01-deployment.txt ~ 10-monitoring.txt)**

각 파일마다 Step 3 반복:

| 순서 | 파일명 | 페이지 제목 | 예상 시간 |
|------|--------|------------|----------|
| 1 | 00-index.txt | 00. Index | 2분 |
| 2 | 01-deployment.txt | 01. Deployment Guide | 1분 |
| 3 | 02-architecture.txt | 02. System Architecture | 1분 |
| 4 | 03-api.txt | 03. API Reference | 1분 |
| 5 | 03-api-auto.txt | 03. API Auto-generated | 1분 |
| 6 | 04-diagrams.txt | 04. System Diagrams | 1분 |
| 7 | 04-diagrams-mermaid.txt | 04. Mermaid Diagrams | 1분 |
| 8 | 05-upgrade.txt | 05. Upgrade Procedures | 1분 |
| 9 | 06-security.txt | 06. Security Guide | 1분 |
| 10 | 07-troubleshooting.txt | 07. Troubleshooting | 1분 |
| 11 | 08-appendix.txt | 08. Appendix | 1분 |
| 12 | 09-dashboard.txt | 09. Dashboard Usage | 1분 (선택) |
| 13 | 10-monitoring.txt | 10. Monitoring Setup | 1분 (선택) |

**Step 5: 계층 구조 설정 (선택 사항)**

페이지 간 부모-자식 관계 설정:

```
1. 각 페이지 편집 (Edit 버튼)
2. 상단 "Page Settings" 또는 "..." 메뉴
3. "Parent" 설정
   - 00-index 페이지를 부모로 설정
4. Save
```

**완료!**

---

### 🔄 대안: 관리자에게 요청

소요 시간: **30초** (관리자 작업 시간)

#### 방법

**Step 1: XAR 파일 전달**
```bash
# 이메일 또는 파일 공유로 전달
blacklist-docs.xar (40KB)
```

**Step 2: 요청 메시지 예시**
```
안녕하세요,

XWiki 문서 import를 요청드립니다.

첨부 파일: blacklist-docs.xar (40KB)
Import 위치: Main space
Import 옵션:
- Import as backup package: ✅
- Preserve document history: ✅

감사합니다.
```

**Step 3: 관리자 작업**
관리자가 XAR Import 수행 (30초 소요)

**Step 4: 확인**
XWiki에서 페이지 생성 확인

---

## 🔧 자동화 스크립트 (Admin API Key 필요)

관리자 API Key가 있으면 스크립트로 자동 배포 가능:

### Python 스크립트
```bash
python3 xwiki-manager.py --deploy
```

### PowerShell 스크립트 (Windows)
```powershell
.\Deploy-XWiki.ps1
```

### Bash 스크립트
```bash
bash create-xwiki-pages.sh
```

**요구 사항:**
- XWiki 관리자 계정
- API Key 생성 (`XWiki Admin → Applications → REST`)
- 환경 변수 설정:
  ```bash
  export XWIKI_URL="http://your-xwiki-domain:8080"
  export XWIKI_USER="admin"
  export XWIKI_PASSWORD="your-password"
  ```

---

## 📊 배포 방법 비교

| 방법 | 권한 요구 | 소요 시간 | 난이도 | 자동화 | 추천 상황 |
|------|----------|----------|--------|--------|----------|
| **XAR Import** | 🔒 Admin | 30초 | 쉬움 | ✅ 완전 자동 | 관리자 권한 있음 |
| **자동 스크립트** | 🔒 Admin API | 1분 | 중간 | ✅ 완전 자동 | 반복 배포 필요 |
| **수동 복사** | ✅ 일반 사용자 | 10-15분 | 쉬움 | ❌ 수동 | 관리자 권한 없음 |
| **관리자 요청** | ⚠️ 관리자 필요 | 30초 | 쉬움 | ✅ 관리자 작업 | 일회성 배포 |

---

## ❓ FAQ

### Q1: XAR Import 메뉴가 안 보여요
**A:** 관리자 권한이 필요합니다. 수동 복사/붙여넣기 방법을 사용하세요.

### Q2: 수동 복사 시 페이지 제목은 어떻게 하나요?
**A:** 파일명에서 `.txt` 제거하고 의미 있는 제목 사용
- `01-deployment.txt` → `01. Deployment Guide`
- `02-architecture.txt` → `02. System Architecture`

### Q3: Wiki 문법이 깨져 보여요
**A:** 에디터 모드를 "Wiki" 또는 "Source"로 변경하세요.
- WYSIWYG 모드는 HTML로 변환할 수 있음
- Wiki/Source 모드가 정확함

### Q4: 계층 구조는 필수인가요?
**A:** 선택 사항입니다. 페이지만 생성해도 문서는 정상 작동합니다.
계층 구조는 탐색 편의를 위한 것입니다.

### Q5: 오프라인 환경에서도 가능한가요?
**A:** 네, 모든 방법이 가능합니다.
- XAR 파일과 .txt 템플릿이 오프라인 패키지에 포함되어 있습니다.
- XWiki 서버만 접속 가능하면 OK

### Q6: 나중에 내용을 업데이트하려면?
**A:**
- **관리자:** 새 XAR 파일로 재import (기존 페이지 덮어쓰기)
- **일반 사용자:** 각 페이지 편집 (Edit 버튼)하여 내용 수정

### Q7: 한글이 깨져요
**A:** XWiki 인코딩 설정 확인:
```
XWiki Admin → Content → General
Encoding: UTF-8 설정 확인
```

---

## 📝 체크리스트

### XAR Import 방식 (관리자)
- [ ] XWiki 관리자 권한 확인
- [ ] blacklist-docs.xar 파일 준비
- [ ] XWiki Admin → Import 페이지 접속
- [ ] XAR 파일 업로드
- [ ] Import 옵션 설정 (backup package, preserve history)
- [ ] Import 실행
- [ ] 12개 페이지 생성 확인
- [ ] 계층 구조 확인

### 수동 복사/붙여넣기 방식 (일반 사용자)
- [ ] .txt 템플릿 파일 11개 준비
- [ ] XWiki 일반 사용자 계정 로그인
- [ ] 00-index.txt 페이지 생성
- [ ] 01-deployment.txt 페이지 생성
- [ ] 02-architecture.txt 페이지 생성
- [ ] 03-api.txt 페이지 생성
- [ ] 03-api-auto.txt 페이지 생성
- [ ] 04-diagrams.txt 페이지 생성
- [ ] 04-diagrams-mermaid.txt 페이지 생성
- [ ] 05-upgrade.txt 페이지 생성
- [ ] 06-security.txt 페이지 생성
- [ ] 07-troubleshooting.txt 페이지 생성
- [ ] 08-appendix.txt 페이지 생성
- [ ] (선택) 09-dashboard.txt 페이지 생성
- [ ] (선택) 10-monitoring.txt 페이지 생성
- [ ] 모든 페이지 내용 확인
- [ ] (선택) 계층 구조 설정

---

## 🔗 관련 문서

### XWiki 템플릿 파일
- `docs/xwiki-sections/*.txt` - 11개 섹션 템플릿
- `docs/xwiki-sections/blacklist-docs.xar` - XAR 패키지 (40KB)

### 배포 스크립트
- `xwiki-manager.py` - Python 통합 관리 도구
- `Deploy-XWiki.ps1` - PowerShell 자동 배포
- `create-xwiki-pages.sh` - Bash 페이지 생성
- `xwiki-import.sh` - REST API import

### 상세 가이드
- `XAR_IMPORT_GUIDE.md` - XAR import 상세 설명
- `MANUAL_COPYPASTE_GUIDE.md` - 수동 복사 상세 가이드
- `README_XWIKI_IMPORT.md` - Import 기술 문서

---

## ✅ 결론

**권한에 따른 최적 방법:**

| 상황 | 추천 방법 | 소요 시간 |
|------|----------|----------|
| 관리자 권한 있음 | XAR Import | 30초 |
| 관리자 권한 없음 | 수동 복사/붙여넣기 | 10-15분 |
| 관리자와 협력 가능 | 관리자에게 요청 | 30초 |
| 반복 배포 필요 | 자동 스크립트 | 1분 |

**핵심:**
- 관리자 권한이 없어도 문서 배포 가능 ✅
- 수동 방법이 번거로워도 확실하고 안전 ✅
- 오프라인 환경에서도 모든 방법 사용 가능 ✅

---

**생성일:** 2025-10-21
**버전:** 1.0
**관련 커밋:** b3d70bb
**상태:** ✅ COMPLETE
