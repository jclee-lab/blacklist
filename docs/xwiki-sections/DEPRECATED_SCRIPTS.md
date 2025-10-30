# ⚠️ 레거시 스크립트 Deprecated 공지

## 📢 중요 공지

v3.0부터 **모든 XWiki 문서 생성 기능이 통합 CLI 도구로 이전**되었습니다.

기존의 5개 스크립트는 **더 이상 유지보수되지 않으며**, 향후 버전에서 제거될 예정입니다.

---

## 🗑️ Deprecated 스크립트 목록

| 파일명 | 상태 | 대체 명령 | 제거 예정 |
|--------|------|-----------|-----------|
| `create-xwiki-pages.sh` | ⚠️ **DEPRECATED** | `python3 xwiki-manager.py create` | v4.0 |
| `xwiki-import.sh` | ⚠️ **DEPRECATED** | `python3 xwiki-manager.py create` | v4.0 |
| `xwiki-import.ps1` | ⚠️ **DEPRECATED** | `python3 xwiki-manager.py create` | v4.0 |
| `check-xwiki-permissions.sh` | ⚠️ **DEPRECATED** | `python3 xwiki-manager.py check` | v4.0 |
| `test-xwiki-import-v2.sh` | ⚠️ **DEPRECATED** | `python3 xwiki-manager.py validate` | v4.0 |

---

## 🔄 마이그레이션 가이드

### 1. 페이지 생성

**기존 (Bash):**
```bash
XWIKI_URL=http://wiki.example.com:8080 \
XWIKI_USER=jclee \
XWIKI_PASS=mypass \
PARENT_PAGE=Blacklist \
./xwiki-import.sh
```

**새로운 (Python):**
```bash
XWIKI_URL=http://wiki.example.com:8080 \
XWIKI_USER=jclee \
XWIKI_PASS=mypass \
PARENT_PAGE=Blacklist \
python3 xwiki-manager.py create --batch
```

---

### 2. 권한 체크

**기존 (Bash):**
```bash
./check-xwiki-permissions.sh
```

**새로운 (Python):**
```bash
python3 xwiki-manager.py check
```

---

### 3. 파일 검증

**기존:** 수동 확인

**새로운 (Python):**
```bash
python3 xwiki-manager.py validate
```

---

### 4. 페이지 목록

**기존:** README 문서 참조

**새로운 (Python):**
```bash
python3 xwiki-manager.py list
```

---

## ✅ v3.0 통합 CLI 도구의 장점

| 기능 | 레거시 (v2.0) | 통합 CLI (v3.0) |
|------|---------------|-----------------|
| **스크립트 수** | 5개 | **1개** ✅ |
| **플랫폼** | Linux + Windows 분리 | **크로스플랫폼** ✅ |
| **에러 처리** | 제한적 | **상세 + 해결 방법** ✅ |
| **파일 검증** | ❌ | **자동 검증** ✅ |
| **진행 상황** | 텍스트 | **시각적 트리** ✅ |
| **유지보수** | 어려움 (2개 언어) | **쉬움** (단일 언어) ✅ |

---

## 📚 새로운 문서

**통합 CLI 도구 가이드:**
- `README_UNIFIED_CLI.md` - 전체 사용법
- `xwiki-manager.py --help` - CLI 내장 도움말

**기존 문서 (참고용):**
- `README_XWIKI_IMPORT.md` - v2.0 레거시 가이드 (archived)

---

## ⏰ 지원 종료 일정

| 버전 | 날짜 | 변경 사항 |
|------|------|-----------|
| **v3.0** | 2025-10-14 | 통합 CLI 출시, 레거시 스크립트 Deprecated 선언 |
| **v3.x** | 2025-10 ~ 2025-12 | 레거시 스크립트 유지 (경고 메시지 표시) |
| **v4.0** | 2026-01 (예정) | 레거시 스크립트 완전 제거 |

---

## 🆘 도움이 필요하신가요?

**통합 CLI 도구 사용법:**
```bash
python3 xwiki-manager.py --help
python3 xwiki-manager.py create --help
```

**상세 가이드:**
```bash
cat README_UNIFIED_CLI.md
```

**문의:**
- 정보보안팀
- Email: security@company.com

---

**최종 업데이트: 2025-10-14**
