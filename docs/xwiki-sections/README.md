# XWiki 문서 템플릿

**Blacklist Platform XWiki 통합 문서 - 섹션별 템플릿 파일**

---

## 📚 문서 구조

이 폴더는 XWiki에 업로드할 **11개 섹션의 문서 템플릿**을 포함합니다.

### 문서 섹션 목록

| 파일명 | 제목 | 크기 | 설명 |
|--------|------|------|------|
| `00-index.txt` | 목차 | 1.9KB | 전체 문서 인덱스 |
| `01-deployment.txt` | 배포 가이드 | 6.1KB | 설치 및 배포 절차 |
| `02-architecture.txt` | 아키텍처 | 11KB | 시스템 아키텍처 상세 |
| `03-api.txt` | API 문서 | 11KB | REST API 레퍼런스 |
| `03-api-auto.txt` | API 자동 생성 | 9.5KB | 자동 생성된 API 문서 |
| `04-diagrams.txt` | 다이어그램 | 6.6KB | 시스템 다이어그램 |
| `04-diagrams-mermaid.txt` | Mermaid 다이어그램 | 11KB | Mermaid 형식 다이어그램 |
| `05-upgrade.txt` | 업그레이드 | 9.4KB | 업그레이드 절차 |
| `06-security.txt` | 보안 | 7.7KB | 보안 설정 가이드 |
| `07-troubleshooting.txt` | 문제 해결 | 15KB | 트러블슈팅 가이드 |
| `08-appendix.txt` | 부록 | 5.1KB | 추가 참고 자료 |
| `09-dashboard.txt` | 대시보드 | 6.8KB | 대시보드 사용법 |
| `10-monitoring.txt` | 모니터링 | 11KB | 모니터링 설정 |

---

## 🚀 XWiki 배포 방법

### ⚠️ 권한에 따른 배포 방법 선택

#### ✅ **관리자 권한 있음**
- 옵션 1 (자동 배포) 또는 옵션 3 (XAR Import) 사용
- 가장 빠르고 편리함

#### ⚠️ **관리자 권한 없음** (일반 사용자)
- **옵션 2 (수동 업로드) 사용 - 권한 불필요**
- 소요 시간: 약 10-15분

---

### 옵션 1: 자동 배포 (🔒 Admin API Key 필요)

XWiki 자동 배포 스크립트 사용:

```bash
# XWiki 관리자 API Key 필요
python3 xwiki-manager.py --deploy

# 또는 PowerShell (Windows)
.\Deploy-XWiki.ps1
```

### 옵션 2: 수동 업로드 (✅ 권한 불필요 - 추천)

**일반 사용자도 가능한 방법:**

1. XWiki 로그인 (일반 사용자 계정)
2. **Create → Page** 선택
   - 좌측 메뉴 또는 URL: `http://xwiki-domain/xwiki/bin/create/Main/`
3. 각 섹션별로 반복:
   - 페이지 제목 입력: `01. Deployment Guide` 등
   - 에디터에서 Wiki 또는 WYSIWYG 모드 선택
   - `docs/xwiki-sections/01-deployment.txt` 파일 열기
   - 내용 전체 복사 (Ctrl+A, Ctrl+C)
   - XWiki 에디터에 붙여넣기 (Ctrl+V)
   - **Save & View** 클릭
4. 11개 섹션 모두 반복 (`00-index.txt` ~ `10-monitoring.txt`)

**소요 시간:** 약 10-15분 (페이지당 1-2분)

### 옵션 3: XAR 패키지 Import (🔒 Admin 권한 필요)

**가장 빠른 방법 (30초) - 관리자만 가능:**

```bash
# XWiki Administration → Import → blacklist-docs.xar 선택

1. XWiki Admin 페이지 접속
   http://xwiki-domain/xwiki/bin/admin/XWiki/XWikiPreferences?section=Import

2. XAR 파일 업로드
   - Choose file → blacklist-docs.xar → Upload

3. Import 옵션 설정
   - ✅ Import as backup package
   - ✅ Preserve document history
   - Target space: Main
   - Import 클릭

결과: 12개 페이지 자동 생성 (계층 구조 포함)
```

**관리자 권한 없으면:**
- XAR 파일을 관리자에게 전달하여 Import 요청
- 또는 옵션 2 (수동 업로드) 사용

---

## 📖 상세 가이드

자세한 배포 방법은 다음 문서 참조:

- `QUICK_DEPLOY.md` - 빠른 배포 가이드
- `README_XWIKI_IMPORT.md` - XWiki Import 상세 가이드
- `XWIKI_DEPLOYMENT_VISUAL.md` - 시각적 배포 가이드
- `MANUAL_COPYPASTE_GUIDE.md` - 수동 복사/붙여넣기 가이드

---

## 🔧 관련 스크립트

- `xwiki-manager.py` - 통합 XWiki 관리 도구 (Python)
- `Deploy-XWiki.ps1` - 자동 배포 스크립트 (PowerShell)
- `create-xwiki-pages.sh` - 페이지 생성 스크립트 (Bash)
- `xwiki-import.sh` - REST API 기반 import (Bash)

---

**버전:** 3.0
**최종 업데이트:** 2025-10-21
**패키지:** Blacklist Complete Offline Package
