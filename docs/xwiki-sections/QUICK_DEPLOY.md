# ⚡ XWiki 자동 배포 빠른 가이드

## 🎯 가장 쉬운 방법 선택

---

## 방법 1: XAR 파일 업로드 (30초, 클릭만)

### 1단계: XWiki 관리자 페이지 열기
브라우저에서 이 주소 접속:
```
http://your-xwiki.com:8080/xwiki/bin/admin/XWiki/XWikiPreferences?section=Import
```

### 2단계: XAR 파일 업로드
1. **Choose file** 버튼 클릭
2. `blacklist-docs.xar` 파일 선택 (이 폴더에 있음)
3. **Upload** 버튼 클릭

### 3단계: Import 실행
1. **"Import as backup package"** 체크박스 선택 ✅
2. **Import** 버튼 클릭
3. 확인 팝업에서 **Import** 다시 클릭

### 완료! 🎉
```
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist
```
접속하면 12개 페이지 모두 자동 생성됨

---

## 방법 2: REST API 자동 배포 (1분, 스크립트 실행)

### 사용 조건
- Python 3 설치됨
- XWiki 접속 가능
- 편집 권한 있는 계정

### 1단계: 환경변수 설정
```bash
export XWIKI_URL="http://your-xwiki.com:8080"
export XWIKI_USER="your_username"
export XWIKI_PASS="your_password"
```

### 2단계: 자동 배포 실행
```bash
# 기본 배포 (순차)
python3 xwiki-manager.py create --batch

# 또는 고급 배포 (병렬, 빠름)
python3 xwiki-deploy-advanced.py deploy --method rest --parallel
```

### 완료! 🎉
1분 후 12개 페이지 모두 생성됨

---

## 방법 3: GitHub Actions 자동 배포 (완전 자동화)

### 설정 방법 (1회만)

**1단계: GitHub Secrets 등록**
```
Repository → Settings → Secrets and variables → Actions → New repository secret

추가할 Secrets:
- XWIKI_URL: http://your-xwiki.com:8080
- XWIKI_USER: your_username
- XWIKI_PASS: your_password
```

**2단계: Workflow 파일 확인**
`.github/workflows/xwiki-auto-sync.yml` 이미 있음 ✅

**3단계: 자동 배포 트리거**

**방법 A: Git Push로 자동 배포**
```bash
# 문서 수정 후 Git push하면 자동 배포
git add .
git commit -m "Update XWiki docs"
git push origin master
```
→ GitHub Actions가 자동으로 XWiki에 배포

**방법 B: 수동 트리거**
```
GitHub → Actions → XWiki Documentation Auto-Sync → Run workflow
```
→ 버튼 클릭으로 즉시 배포

**방법 C: 스케줄 자동 배포**
- 매주 일요일 00:00 UTC 자동 배포 (이미 설정됨)
- `.github/workflows/xwiki-auto-sync.yml` 파일의 `cron` 설정

---

## 📊 방법 비교

| 방법 | 시간 | 자동화 | 권한 | 추천 상황 |
|------|------|--------|------|----------|
| **XAR Upload** | 30초 | ❌ 수동 | 관리자 필요 | **1회성 배포** |
| **REST API** | 1분 | ⚡ 스크립트 | 편집 권한 | **수동 업데이트** |
| **GitHub Actions** | 자동 | ✅ 완전 자동 | 편집 권한 | **지속적 업데이트** |

---

## 🚀 추천 시나리오

### 시나리오 1: 처음 배포 (신규)
```
→ XAR Upload (방법 1)
이유: 가장 빠르고 쉬움 (30초)
```

### 시나리오 2: 문서 수정 후 재배포
```
→ GitHub Actions (방법 3)
이유: Git push만 하면 자동 배포
```

### 시나리오 3: CLI 환경에서 즉시 배포
```
→ REST API (방법 2)
이유: 스크립트 한 줄로 즉시 배포
```

---

## 🔧 실전 예제

### 예제 1: 로컬에서 REST API 배포
```bash
cd /home/jclee/app/blacklist/docs/xwiki-sections

# 환경변수 설정
export XWIKI_URL="http://192.168.1.100:8080"
export XWIKI_USER="admin"
export XWIKI_PASS="admin123"

# 배포 실행
python3 xwiki-manager.py create --batch

# 결과 확인
curl http://192.168.1.100:8080/xwiki/bin/view/Main/Blacklist
```

### 예제 2: GitHub Actions로 자동 배포
```bash
# 1. 문서 수정
vim 01-deployment.txt

# 2. Git commit & push
git add 01-deployment.txt
git commit -m "Update deployment guide"
git push origin master

# 3. GitHub Actions 자동 실행 (1분 후 완료)
# https://github.com/your-org/blacklist/actions

# 4. 결과 확인
curl http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Deployment
```

### 예제 3: XAR 파일 업로드
```bash
# 1. XAR 파일 재생성 (문서 수정 시)
python3 xwiki-deploy-advanced.py package --output blacklist-docs.xar

# 2. 브라우저에서 업로드
# http://your-xwiki.com:8080/xwiki/bin/admin/XWiki/XWikiPreferences?section=Import
# → Choose file → blacklist-docs.xar → Upload → Import

# 3. 완료!
```

---

## 🎯 단계별 자동 배포 설정

### STEP 1: XAR 파일 생성 (이미 완료 ✅)
```bash
ls -lh blacklist-docs.xar
# -rw-r--r-- 1 user user 40K Oct 15 04:18 blacklist-docs.xar
```

### STEP 2: 배포 방법 선택
```
관리자 권한 있음? → XAR Upload (가장 쉬움)
CLI 접근 가능? → REST API (스크립트)
GitHub 사용? → GitHub Actions (완전 자동)
```

### STEP 3: 환경변수 설정 (REST API / GitHub Actions만)
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export XWIKI_URL="http://your-xwiki.com:8080"
export XWIKI_USER="your_username"
export XWIKI_PASS="your_password"

source ~/.bashrc
```

### STEP 4: 배포 실행
```bash
# XAR: 브라우저에서 수동 업로드

# REST API: 스크립트 실행
python3 xwiki-manager.py create --batch

# GitHub Actions: Git push
git push origin master
```

### STEP 5: 확인
```bash
curl http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist
```

---

## 📞 문제 해결

### XAR Upload 실패
```
원인: 관리자 권한 없음
해결: REST API 방법 사용 (방법 2)
```

### REST API 401 Unauthorized
```bash
# 환경변수 확인
echo $XWIKI_USER
echo $XWIKI_PASS

# 재설정
export XWIKI_USER="correct_username"
export XWIKI_PASS="correct_password"
```

### GitHub Actions 실패
```
원인: Secrets 미설정
해결: GitHub → Settings → Secrets → XWIKI_URL, XWIKI_USER, XWIKI_PASS 추가
```

---

## 🎉 결론

**가장 쉬운 자동 배포:**
1. **첫 배포**: XAR Upload (30초, 클릭만)
2. **정기 업데이트**: GitHub Actions (Git push만)
3. **긴급 배포**: REST API (스크립트 1줄)

**파일 위치:**
- XAR 파일: `blacklist-docs.xar` (이 폴더)
- REST API 스크립트: `xwiki-manager.py`, `xwiki-deploy-advanced.py`
- GitHub Actions: `.github/workflows/xwiki-auto-sync.yml`

**지금 바로 실행:**
```bash
# 가장 간단한 방법
python3 xwiki-manager.py create --batch
```

---

**생성일**: 2025-10-15
**업데이트**: 2025-10-15
**버전**: 1.0
