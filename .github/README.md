# GitHub/Gitea Configuration

**프로젝트**: Blacklist IP Management System
**버전**: 3.3.8
**목적**: GitHub/Gitea 통합 설정 및 자동화

---

## 📋 디렉토리 구조

```
.github/
├── README.md                      # 이 파일 - GitHub 설정 개요
├── deployment_trigger.txt         # 배포 트리거 파일
├── ISSUE_TEMPLATE/                # 이슈 템플릿
│   ├── bug_report.yml             # 버그 리포트
│   ├── feature_request.yml        # 기능 요청
│   ├── question.yml               # 질문
│   ├── quick-fix.yml              # 긴급 수정
│   └── config.yml                 # 템플릿 설정
├── scripts/                       # CI/CD 스크립트
│   └── validate-services.sh       # 서비스 검증
└── workflows/                     # GitHub Actions 워크플로우
    ├── README.md                  # 워크플로우 가이드
    ├── offline-package-build.yml  # 오프라인 패키지 빌드
    ├── docker-build-portainer-deploy.yml  # Docker 빌드 및 배포
    ├── xwiki-auto-sync.yml        # XWiki 문서 동기화
    └── cloudflare-workers-deploy.yml  # Cloudflare Workers 배포
```

---

## 🔄 자동화 워크플로우

### 1. 오프라인 패키지 빌드 (`offline-package-build.yml`)

**트리거**:
- Push to `main`, `release/**`
- Tag push (`v*`)
- Manual dispatch

**작업**:
1. Docker 이미지 빌드 (6 서비스)
2. 오프라인 패키지 생성 (blacklist.tar.gz + install.sh)
3. 체크섬 검증
4. Artifacts 업로드 (90일 보관)
5. 릴리즈 생성 (태그 푸시 시)
6. Latest 빌드 생성 (main 브랜치 푸시 시)

**Artifacts**:
- `blacklist-offline-v{version}.zip` (560MB)
  - blacklist.tar.gz
  - blacklist.tar.gz.sha256
  - install.sh

### 2. Docker 빌드 및 배포 (`docker-build-portainer-deploy.yml`)

**트리거**:
- Push to `main`, `develop`
- Tag push
- Manual dispatch

**작업**:
1. Docker 이미지 빌드
2. Container Registry에 푸시
3. Portainer API를 통한 자동 배포

### 3. XWiki 문서 동기화 (`xwiki-auto-sync.yml`)

**트리거**:
- Push to `main` (docs/ 디렉토리 변경 시)
- Manual dispatch

**작업**:
1. docs/ 디렉토리 변경 감지
2. XWiki API를 통한 문서 업로드
3. 자동 버전 관리

### 4. Cloudflare Workers 배포 (`cloudflare-workers-deploy.yml`)

**트리거**:
- Push to `main` (workers/ 디렉토리 변경 시)
- Manual dispatch

**작업**:
1. Cloudflare Workers 빌드
2. Cloudflare API를 통한 배포

---

## 🐛 이슈 템플릿

### 템플릿 종류

1. **Bug Report** (`bug_report.yml`)
   - 버그 재현 단계
   - 예상/실제 동작
   - 환경 정보

2. **Feature Request** (`feature_request.yml`)
   - 기능 설명
   - 사용 사례
   - 우선순위

3. **Question** (`question.yml`)
   - 질문 내용
   - 관련 문서
   - 컨텍스트

4. **Quick Fix** (`quick-fix.yml`)
   - 긴급 수정 요청
   - 영향 범위
   - 임시 해결책

### 사용 방법

```bash
# GitHub/Gitea 웹 UI에서:
Issues → New Issue → 템플릿 선택
```

---

## 🚀 배포 트리거

### 수동 배포 트리거 (`deployment_trigger.txt`)

**목적**: 코드 변경 없이 배포 워크플로우 강제 실행

**사용 방법**:
```bash
# 파일 수정 (내용은 중요하지 않음)
echo "deployment: $(date)" > .github/deployment_trigger.txt

# 커밋 및 푸시
git add .github/deployment_trigger.txt
git commit -m "trigger: Force container redeployment"
git push origin main
```

**언제 사용**:
- 외부 의존성 업데이트 (Docker base image)
- 환경 변수 변경 적용
- 캐시 클리어 및 재빌드

---

## 📜 스크립트

### `scripts/validate-services.sh`

**목적**: 서비스 헬스 체크 및 검증

**사용**:
```bash
bash .github/scripts/validate-services.sh
```

**검증 항목**:
- Docker 서비스 실행 상태
- Health check 엔드포인트
- 데이터베이스 연결
- API 응답 검증

---

## 🔑 필수 Secrets (GitHub/Gitea Settings)

### GitHub Actions Secrets

```
# Docker Registry
DOCKER_USERNAME           # Docker Hub 사용자명
DOCKER_PASSWORD           # Docker Hub 패스워드 또는 토큰
REGISTRY_HOST             # 컨테이너 레지스트리 호스트
REGISTRY_USER             # 레지스트리 사용자명
REGISTRY_PASSWORD         # 레지스트리 패스워드

# Portainer API (자동 배포)
PORTAINER_URL             # Portainer API URL
PORTAINER_API_KEY         # Portainer API 키

# XWiki Sync
XWIKI_URL                 # XWiki 인스턴스 URL
XWIKI_USERNAME            # XWiki 사용자명
XWIKI_PASSWORD            # XWiki 패스워드

# Cloudflare Workers
CLOUDFLARE_API_TOKEN      # Cloudflare API 토큰
CLOUDFLARE_ACCOUNT_ID     # Cloudflare 계정 ID

# Application (빌드 시 주입)
REGTECH_ID                # REGTECH 포털 ID
REGTECH_PW                # REGTECH 포털 비밀번호
REGTECH_BASE_URL          # REGTECH API URL
POSTGRES_PASSWORD         # PostgreSQL 비밀번호
GITHUB_TOKEN              # GitHub API 토큰 (자동 제공)
```

### Secrets 설정 방법

**GitHub**:
```
Repository Settings → Secrets and variables → Actions → New repository secret
```

**Gitea**:
```
Repository Settings → Secrets → Actions → Add Secret
```

---

## 🧪 로컬 테스트

### Act를 사용한 로컬 워크플로우 테스트

```bash
# Act 설치
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# 워크플로우 실행 (push 이벤트)
act push -W .github/workflows/offline-package-build.yml

# Secrets 파일 사용
act push --secret-file .secrets

# 특정 job만 실행
act push -j build-offline-package
```

### Docker Compose 로컬 검증

```bash
# 서비스 빌드 및 시작
docker compose up -d

# 헬스 체크
bash .github/scripts/validate-services.sh

# 로그 확인
docker compose logs -f
```

---

## 📊 워크플로우 모니터링

### GitHub Actions

```
Repository → Actions 탭
```

**상태 확인**:
- ✅ Success (성공)
- ❌ Failure (실패)
- ⏳ In Progress (진행 중)
- ⚠️ Skipped (건너뜀)

### Gitea Actions

```
Repository → Actions 탭
```

**러너 상태**:
```bash
# Gitea Runner 상태 확인
./act_runner status

# 로그 확인
journalctl -u act-runner -f
```

---

## 🐛 트러블슈팅

### 워크플로우 실패

**빌드 실패**:
```bash
# 로컬에서 재현
docker compose build --no-cache

# 이미지 정리
docker system prune -af
```

**Secrets 오류**:
```bash
# Secrets 확인 (값은 보이지 않음)
gh secret list

# Secrets 업데이트
gh secret set DOCKER_PASSWORD
```

**Artifacts 업로드 실패**:
- 파일 크기 확인 (GitHub: 2GB 제한)
- 스토리지 할당량 확인

### 배포 실패

**Portainer API 오류**:
```bash
# API 연결 테스트
curl -H "X-API-Key: $PORTAINER_API_KEY" \
  $PORTAINER_URL/api/stacks

# 스택 상태 확인
curl -H "X-API-Key: $PORTAINER_API_KEY" \
  $PORTAINER_URL/api/stacks/$STACK_ID
```

**컨테이너 재배포 안됨**:
```bash
# 수동 트리거
echo "deployment: $(date)" > .github/deployment_trigger.txt
git add .github/deployment_trigger.txt
git commit -m "trigger: Force redeployment"
git push
```

---

## 📚 참고 문서

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Gitea Actions Documentation](https://docs.gitea.com/next/usage/actions/overview)
- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)
- [Portainer API Documentation](https://docs.portainer.io/api/docs)

---

## 🔄 변경 이력

### v3.3.8 (2025-10-30)
- ✅ 오프라인 패키지 빌드 워크플로우 추가
- ✅ Latest 빌드 자동 생성 (main 브랜치)
- ✅ 자동 릴리즈 노트 생성
- ✅ Rate Limiting 구현

### v3.3.7 (2025-10-29)
- ✅ Traefik 오프라인 패키지
- ✅ Nginx 독립 배포
- ✅ Air-gap 환경 지원

### v3.3.6 (2025-10-28)
- ✅ FortiGate/FortiManager 통합 UI
- ✅ 세션 히스토리 관리
- ✅ 수집 로그 뷰어

---

**마지막 업데이트**: 2025-10-30
**유지보수**: Workflows는 정기적으로 업데이트 및 테스트 필요
