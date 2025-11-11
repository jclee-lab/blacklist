# Configuration File Location Guide

설정 파일들의 위치와 용도를 명확히 정의합니다.

## 📁 설정 파일 계층 구조

### 1. 마스터 설정 파일 (Master Configurations)

프로젝트의 유일한 진실 원천(Single Source of Truth)입니다.

#### VSCode 워크스페이스 설정
```
.vscode/
├── extensions.json    # 36개 권장 확장 목록
├── extensions/        # 오프라인 설치용 .vsix 파일 (98MB)
│   ├── eamodio.gitlens-2025.11.1016.vsix (8.0M)
│   ├── ms-python.vscode-pylance-2025.9.100.vsix (20M)
│   ├── tamasfe.even-better-toml-0.21.2.vsix (21M)
│   └── ... (총 36개 확장)
├── settings.json      # 작업공간 설정
├── launch.json        # 디버그 구성
├── tasks.json         # 작업 자동화
├── snippets/          # 코드 스니펫
└── README.md          # VSCode 설정 가이드
```

**용도**: 개발 환경 표준화 + 오프라인 설치 지원
**편집**: VSCode UI 또는 직접 수정
**배포**:
- 설정 파일: 패키징 시 자동 복사 (`scripts/package-dependencies.sh`)
- 확장 파일: Git으로 추적 (.vsix 파일, 총 98MB)

**오프라인 확장 업데이트**:
```bash
# 최신 버전 다운로드 (인터넷 연결 필요)
./scripts/download-vscode-extensions.sh

# 다운로드된 확장 확인
ls -lh .vscode/extensions/

# Git 커밋
git add .vscode/extensions/
git commit -m "chore: Update VSCode extensions"
```

#### Python 통합 의존성
```
requirements.txt       # 통합 Python 패키지 (59 lines, 47 packages)
```

**용도**: 전체 프로젝트 Python 의존성 통합
**생성**: app/, collector/, postgres/, redis/의 requirements 통합
**배포**: 패키징 시 자동 복사

#### Docker 오케스트레이션
```
docker-compose.yml          # 기본 구성
docker-compose.dev.yml      # 개발 환경 오버라이드
docker-compose.prod.yml     # 프로덕션 환경 오버라이드
docker-compose.offline.yml  # 오프라인/에어갭 환경
```

**용도**: 환경별 컨테이너 구성
**사용**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`

#### 환경 변수
```
.env.example           # 환경 변수 템플릿
.env                   # 실제 환경 변수 (gitignored)
```

**용도**: 민감한 정보 및 환경별 설정
**편집**: 직접 수정 (절대 Git에 커밋하지 말 것)

---

### 2. 서비스별 설정 파일 (Service-Specific Configurations)

각 마이크로서비스의 개별 의존성 정의입니다.

#### App (Flask 애플리케이션)
```
app/
├── requirements.txt     # Flask, SQLAlchemy, pytest, etc.
├── Dockerfile
└── entrypoint.sh
```

#### Collector (데이터 수집 서비스)
```
collector/
├── requirements.txt     # Requests, BeautifulSoup, Playwright, etc.
├── Dockerfile
└── (collection scripts)
```

#### PostgreSQL
```
postgres/
├── requirements.txt     # psycopg2-binary (필요 시)
├── Dockerfile
└── migrations/          # SQL 마이그레이션 파일
```

#### Redis
```
redis/
├── requirements.txt     # redis-py
└── Dockerfile
```

#### Frontend (Next.js)
```
frontend/
├── package.json
├── package-lock.json
├── .env.example
└── Dockerfile
```

**용도**: 각 서비스의 독립적인 의존성 관리
**편집**: 서비스별로 수정
**통합**: 루트의 requirements.txt로 자동 통합

---

### 3. 자동 생성 파일 (Auto-Generated Files)

패키징 또는 빌드 시 자동으로 생성됩니다. **직접 수정하지 마세요.**

#### 오프라인 패키지 (dist/dependencies/)
```
dist/dependencies/                    # gitignored
├── .vscode/                          # .vscode에서 복사
├── requirements.txt                  # requirements.txt에서 복사
├── python-packages/                  # pip download 결과
│   └── *.whl (93 files)
├── frontend-node_modules.tar.gz      # npm 패키지
├── package.json                      # frontend/package.json 복사
├── package-lock.json                 # frontend/package-lock.json 복사
├── install-offline.sh                # 자동 생성 스크립트
├── README.md                         # 자동 생성 문서
└── VSCODE-EXTENSIONS.md              # 자동 생성 확장 목록
```

**생성**: `make package-deps` 또는 `scripts/package-dependencies.sh`
**용도**: 오프라인/에어갭 서버 설치
**유효기간**: 재패키징 시까지

#### Docker 이미지 패키지 (dist/images/)
```
dist/images/                          # gitignored
├── blacklist-app_latest.tar.gz       (311MB)
├── blacklist-collector_latest.tar.gz (156MB)
├── blacklist-postgres_latest.tar.gz  (185MB)
├── blacklist-redis_latest.tar.gz     (28MB)
└── blacklist-frontend_latest.tar.gz  (135MB)
```

**생성**: `scripts/package-single-image.sh` 또는 CI/CD 파이프라인
**용도**: 오프라인 서버 Docker 이미지 전송

---

## 🔄 설정 파일 업데이트 워크플로

### 1. VSCode 설정 변경

#### A. 설정 파일 수정 (extensions.json, settings.json 등)
```bash
# 1. .vscode/ 파일 직접 수정
vim .vscode/extensions.json
vim .vscode/settings.json

# 2. Git 커밋
git add .vscode/
git commit -m "feat: update VSCode configuration"
git push

# 3. 오프라인 패키지 재생성 (필요 시)
make package-deps
```

#### B. VSCode 확장 업데이트 (오프라인 설치용)
```bash
# 1. 최신 버전 다운로드 (인터넷 연결 필요)
./scripts/download-vscode-extensions.sh

# 2. 다운로드 확인
ls -lh .vscode/extensions/
du -sh .vscode/extensions/

# 3. Git 커밋
git add .vscode/extensions/
git commit -m "chore: Update VSCode extensions to latest versions"
git push

# 4. 오프라인 서버에서 설치
cd .vscode/extensions
for ext in *.vsix; do
    code --install-extension "$ext" --force
done
```

### 2. Python 의존성 추가
```bash
# 1. 서비스별 requirements.txt 수정
vim app/requirements.txt

# 2. 루트 requirements.txt 재생성
cat app/requirements.txt \
    collector/requirements.txt \
    postgres/requirements.txt \
    redis/requirements.txt \
    | sort -u > requirements.txt

# 3. 중복 패키지 버전 충돌 해결 (수동)
vim requirements.txt

# 4. Git 커밋
git add requirements.txt app/requirements.txt
git commit -m "feat: add new Python dependency"
git push

# 5. 오프라인 패키지 재생성
make package-deps
```

### 3. Docker 구성 변경
```bash
# 1. docker-compose 파일 수정
vim docker-compose.yml

# 2. Git 커밋
git add docker-compose.yml
git commit -m "feat: update Docker configuration"
git push

# 3. 이미지 재빌드
make rebuild
```

---

## 🚫 중복 제거 규칙

### ✅ 유지해야 할 파일
- **서비스별 requirements.txt**: 각 서비스의 독립적인 의존성 관리
- **환경별 docker-compose**: 개발/프로덕션 환경 분리
- **frontend/.env.example**: 프론트엔드 전용 환경 변수

### ❌ 중복 생성 금지
- **dist/dependencies/** 디렉토리를 수동으로 생성하지 말 것
- **requirements.txt 복사본**을 여러 곳에 만들지 말 것
- **.vscode 디렉토리 복사본**을 만들지 말 것

### 🔄 자동 동기화
다음 파일들은 자동으로 동기화됩니다:
- `.vscode/` → `dist/dependencies/.vscode/` (패키징 시)
- `requirements.txt` → `dist/dependencies/requirements.txt` (패키징 시)
- `frontend/package.json` → `dist/dependencies/package.json` (패키징 시)

---

## 🛠️ 트러블슈팅

### 문제: VSCode 설정이 오프라인 패키지에 포함되지 않음
```bash
# 해결: 패키지 재생성
make package-deps

# 확인
tar -tzf dist/blacklist-dependencies-*.tar.gz | grep .vscode
```

### 문제: requirements.txt 버전 충돌
```bash
# 해결: 수동 deduplication
vim requirements.txt

# 중복된 패키지 제거, 최신 버전 유지
# 예: structlog==23.1.0 및 structlog==23.2.0 → structlog==23.2.0만 남김
```

### 문제: 서비스별 requirements와 통합 requirements 불일치
```bash
# 해결: 통합 재생성
cat app/requirements.txt \
    collector/requirements.txt \
    postgres/requirements.txt \
    redis/requirements.txt \
    | sort -u > requirements.txt

# 중복 해결 후 커밋
git add requirements.txt
git commit -m "sync: regenerate unified requirements"
```

---

## 📚 참고 문서

- **오프라인 패키징 가이드**: `IMAGE-PACKAGING-COMPLETE.md`
- **셋업 가이드**: `CLAUDE.md` (Quick Command Reference Card 섹션)
- **의존성 문서**: `dist/dependencies/README.md` (자동 생성)
- **VSCode 확장 목록**: `dist/dependencies/VSCODE-EXTENSIONS.md` (자동 생성)

---

**최종 업데이트**: 2025-11-11
**버전**: 1.0.0
