# Blacklist 프로젝트 고도화 계획

**작성일**: 2025-10-21
**기준 버전**: v3.3.1 (예정)
**목표**: 오프라인 패키지 품질 개선 및 프로덕션 안정성 확보

---

## 📊 현재 상태 평가

| 영역 | 현재 점수 | 목표 점수 | 격차 |
|------|----------|----------|------|
| **스크립트 구조** | 82/100 | 95/100 | -13 |
| **Git LFS 보안** | 75/100 | 90/100 | -15 |
| **XWiki 통합** | 95/100 | 98/100 | -3 |
| **전반적 품질** | 78/100 | 95/100 | -17 |
| **총합** | **82.5/100** | **94.5/100** | **-12** |

**발견된 이슈**: 13개 (3 Critical, 4 High, 4 Medium, 2 Low)

---

## 🎯 Phase 1: Critical Fixes (Week 1 - 즉시 실행)

**목표**: 보안 취약점 및 배포 실패 원인 제거
**소요 시간**: 37분
**담당**: DevOps/개발팀
**우선순위**: 🔴 **최고**

### Task 1.1: .env 파일 보안 강화 (2분)

**문제**: 실제 비밀번호가 포함된 `.env` 파일이 오프라인 패키지에 노출

**작업**:
```bash
# 파일: scripts/create-complete-offline-package.sh
# Line 78 수정

rsync -a --exclude='node_modules' \
          --exclude='.git' \
          --exclude='.env' \              # ← 추가
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          /home/jclee/app/blacklist/ "${PACKAGE_DIR}/source/"
```

**검증**:
```bash
# 패키지 재생성 후 확인
tar -tzf blacklist-complete-offline-*.tar.gz | grep "\.env$"
# 결과: .env.example만 있어야 함
```

**영향**: 보안 취약점 완전 제거

---

### Task 1.2: SECUDIUM 자격증명 템플릿 추가 (5분)

**문제**: `.env.example`에 SECUDIUM 자격증명 누락 → 신규 배포 시 SECUDIUM 수집 실패

**작업**:
```bash
# 파일: .env.example
# Line 8 이후 추가

# SECUDIUM Authentication (Threat Intelligence Provider)
SECUDIUM_ID=your_secudium_username
SECUDIUM_PW=your_secudium_password
SECUDIUM_BASE_URL=https://rest.secudium.net
```

**검증**:
```bash
# 오프라인 패키지 설치 후 확인
grep -q "SECUDIUM_ID" .env.example && echo "OK" || echo "FAIL"
```

**영향**: 듀얼 소스 수집 정상 작동

---

### Task 1.3: 버전 추적 시스템 구현 (30분)

**문제**: 패키지 버전 추적 불가, 문서 간 버전 불일치

**작업 1: VERSION 파일 생성**
```bash
# /home/jclee/app/blacklist/VERSION
echo "3.3.1" > VERSION
git add VERSION
```

**작업 2: 스크립트 수정**
```bash
# 파일: scripts/create-complete-offline-package.sh
# Line 50 수정

# 기존
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="blacklist-complete-offline-${TIMESTAMP}"

# 변경 후
VERSION=$(cat "${PROJECT_ROOT}/VERSION" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="blacklist-complete-offline-v${VERSION}-${TIMESTAMP}"
```

**작업 3: PACKAGE_INFO.json 업데이트**
```bash
# Line 590-620 수정
cat > "${PACKAGE_DIR}/PACKAGE_INFO.json" <<EOF
{
  "package_name": "Blacklist Platform Complete Offline Package",
  "version": "${VERSION}",
  "build_date": "$(date +%Y-%m-%d)",
  "build_timestamp": "${TIMESTAMP}",
  "components": {
    "docker_images": 6,
    "python_packages": "app + collector",
    "nodejs_packages": "worker node_modules",
    "documentation": "XWiki + guides"
  },
  "requirements": {
    "docker": "20.10+",
    "docker_compose": "2.0+",
    "disk_space": "30GB"
  }
}
EOF
```

**작업 4: 문서 통합**
```bash
# 모든 문서에서 버전 동적 참조
# docs/README.md, 사용법.md 등
sed -i "s/v3.3.0 Final/v${VERSION}/g" offline-packages/docs/*.md
```

**검증**:
```bash
# 패키지 이름 확인
ls -1 offline-packages/blacklist-complete-offline-v3.3.1-*.tar.gz

# PACKAGE_INFO.json 확인
tar -xzf blacklist-complete-offline-v3.3.1-*.tar.gz \
  --strip-components=1 \
  */PACKAGE_INFO.json
jq '.version' PACKAGE_INFO.json
# 출력: "3.3.1"
```

**영향**: 패키지 추적성 확보, 호환성 관리 가능

---

### Phase 1 완료 기준

- [ ] 오프라인 패키지에서 `.env` 파일 제외 확인
- [ ] `.env.example`에 SECUDIUM 자격증명 존재
- [ ] VERSION 파일 생성 및 Git 추적
- [ ] 패키지 이름에 버전 포함 (v3.3.1)
- [ ] PACKAGE_INFO.json에 정확한 버전 기록
- [ ] 신규 패키지 생성 및 검증 완료

**측정 지표**:
- 보안 취약점: 1 → 0
- 배포 성공률: Unknown → 95%+
- 버전 추적: 없음 → 완벽

---

## 🟠 Phase 2: Installation Robustness (Week 2)

**목표**: 설치 안정성 및 사용자 경험 향상
**소요 시간**: 3시간
**담당**: DevOps팀
**우선순위**: 🟠 **높음**

### Task 2.1: 사전 검증 시스템 (1시간)

**문제**: Docker 데몬 미실행, 디스크 부족, 포트 충돌 시 설치 실패

**작업**: `install.sh` 생성 시 사전 검증 추가

```bash
# 파일: scripts/create-complete-offline-package.sh
# install.sh 생성 부분 (line 420-440) 수정

cat > "${PACKAGE_DIR}/install.sh" <<'INSTALL_SCRIPT'
#!/bin/bash
set -euo pipefail

# 로깅 함수들...
log_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_warning() { echo -e "\033[33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# ========================================
# Pre-flight Checks (NEW)
# ========================================
log_info "=== Pre-flight Checks ==="

# 1. Docker daemon 확인
if ! docker info &>/dev/null; then
    log_error "Docker daemon is not running"
    log_error "  Start Docker: sudo systemctl start docker"
    log_error "  Enable on boot: sudo systemctl enable docker"
    exit 1
fi
log_success "✓ Docker daemon is running"

# 2. Docker Compose 확인
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed"
    log_error "  Install: https://docs.docker.com/compose/install/"
    exit 1
fi
COMPOSE_VERSION=$(docker-compose version --short)
log_success "✓ Docker Compose ${COMPOSE_VERSION} is available"

# 3. 디스크 공간 확인 (30GB 필요)
AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
REQUIRED_GB=30
if [ "${AVAILABLE_GB}" -lt "${REQUIRED_GB}" ]; then
    log_error "Insufficient disk space"
    log_error "  Available: ${AVAILABLE_GB}GB"
    log_error "  Required: ${REQUIRED_GB}GB"
    log_error "  Free up space or use different installation directory"
    exit 1
fi
log_success "✓ Disk space: ${AVAILABLE_GB}GB available (${REQUIRED_GB}GB required)"

# 4. 포트 충돌 확인
PORTS=(2542 2543 5432 6379 443 80)
CONFLICTS=0
for PORT in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":${PORT} "; then
        log_warning "Port ${PORT} is in use - may cause conflicts"
        CONFLICTS=$((CONFLICTS + 1))
    fi
done

if [ "${CONFLICTS}" -gt 0 ]; then
    log_warning "Found ${CONFLICTS} port conflicts"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi
else
    log_success "✓ No port conflicts detected"
fi

# 5. 네트워크 대역 확인 (172.25.0.0/16)
if docker network ls | grep -q blacklist-network; then
    log_warning "blacklist-network already exists - will be recreated"
fi

log_success "=== Pre-flight checks passed ==="
echo

# 기존 설치 단계들...
INSTALL_SCRIPT
```

**검증**:
```bash
# 테스트 케이스 1: Docker 미실행
sudo systemctl stop docker
./install.sh
# 예상: "Docker daemon is not running" 에러

# 테스트 케이스 2: 디스크 부족 시뮬레이션
# (작은 파티션에서 테스트)

# 테스트 케이스 3: 포트 충돌
nc -l 2542 &  # 2542 포트 점유
./install.sh
# 예상: Port 2542 warning 표시
```

---

### Task 2.2: 진행 상황 표시기 (30분)

**문제**: Docker 이미지 로드 시 5-10분 동안 출력 없음 → 사용자가 멈춘 것으로 오해

**작업**: `01-load-docker-images.sh` 생성 시 진행 표시 추가

```bash
# 파일: scripts/create-complete-offline-package.sh
# 01-load-docker-images.sh 생성 부분 수정

cat > "${PACKAGE_DIR}/scripts/01-load-docker-images.sh" <<'LOAD_SCRIPT'
#!/bin/bash

# ... 기존 코드 ...

# 진행 상황 표시 함수 추가
show_progress() {
    local image_file="$1"
    local image_name=$(basename "$image_file" .tar)

    echo "  📦 Loading ${image_name}..."

    # 백그라운드에서 docker load 실행
    docker load -i "$image_file" > /tmp/docker_load_output.log 2>&1 &
    local pid=$!

    # 프로세스 실행 중 점 표시
    local dots=0
    while kill -0 $pid 2>/dev/null; do
        echo -n "."
        sleep 1
        dots=$((dots + 1))

        # 10초마다 상태 메시지
        if [ $((dots % 10)) -eq 0 ]; then
            echo -n " (${dots}s)"
        fi
    done

    wait $pid
    local exit_code=$?

    echo ""  # 새 줄

    if [ $exit_code -eq 0 ]; then
        # 로드된 이미지 정보 추출
        loaded_image=$(grep "Loaded image" /tmp/docker_load_output.log | tail -1)
        echo "    ✓ $loaded_image"
    else
        echo "    ✗ Failed to load ${image_name}"
        cat /tmp/docker_load_output.log
        return $exit_code
    fi

    return 0
}

# 이미지 로드 (진행 표시 적용)
for image_tar in ../docker-images/*.tar; do
    if [ -f "$image_tar" ]; then
        show_progress "$image_tar" || exit 1
    fi
done

LOAD_SCRIPT
```

**예상 출력**:
```
📦 Loading blacklist-app...
...........(10s)...........(20s)...........(30s)
    ✓ Loaded image: blacklist-app:offline

📦 Loading blacklist-collector...
...........(10s)...........(20s)
    ✓ Loaded image: blacklist-collector:offline
```

---

### Task 2.3: 설치 롤백 메커니즘 (1시간)

**작업**: `install.sh`에 에러 트랩 추가

```bash
# install.sh 상단에 추가
cleanup_on_error() {
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo
        log_error "============================================"
        log_error "Installation failed with error code: ${exit_code}"
        log_error "============================================"
        echo

        log_info "Starting rollback..."
        cd scripts 2>/dev/null || true

        # 1. 실행 중인 컨테이너 중지
        if docker-compose ps 2>/dev/null | grep -q "Up"; then
            log_info "Stopping containers..."
            docker-compose down 2>/dev/null || true
        fi

        # 2. 로드된 Docker 이미지 제거 여부 확인
        LOADED_IMAGES=$(docker images | grep -c "blacklist-" || echo 0)
        if [ "$LOADED_IMAGES" -gt 0 ]; then
            echo
            log_warning "Found ${LOADED_IMAGES} loaded Docker images"
            log_info "These images consume ~1.6GB disk space"
            echo
            read -p "Remove loaded Docker images? (y/N): " -n 1 -r
            echo

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Removing Docker images..."
                docker images | grep blacklist | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
                log_success "Docker images removed"
            else
                log_info "Docker images kept (can be removed later with 'docker rmi')"
            fi
        fi

        # 3. 네트워크 제거
        if docker network ls | grep -q blacklist-network; then
            docker network rm blacklist-network 2>/dev/null || true
        fi

        echo
        log_info "============================================"
        log_info "Rollback complete"
        log_info "Check error messages above for details"
        log_info "============================================"
    fi
}

# 에러 트랩 설정
trap cleanup_on_error EXIT
```

---

### Task 2.4: 설치 후 헬스 체크 (30분)

**작업**: `05-start-services.sh`에 헬스 체크 추가

```bash
# 파일: scripts/create-complete-offline-package.sh
# 05-start-services.sh 생성 부분 수정

cat >> "${PACKAGE_DIR}/scripts/05-start-services.sh" <<'HEALTH_CHECK'

# ========================================
# Health Check (NEW)
# ========================================
log_info "=== Validating Service Health ==="

RETRIES=30
WAIT_SECONDS=2
EXPECTED_HEALTHY=6

log_info "Waiting for services to become healthy..."
log_info "  Expected: ${EXPECTED_HEALTHY} healthy services"
log_info "  Timeout: $((RETRIES * WAIT_SECONDS)) seconds"
echo

while [ $RETRIES -gt 0 ]; do
    HEALTHY=$(docker-compose ps 2>/dev/null | grep -c "healthy" || echo 0)

    if [ "$HEALTHY" -eq "$EXPECTED_HEALTHY" ]; then
        echo
        log_success "All ${EXPECTED_HEALTHY} services are healthy!"
        break
    fi

    # 진행 표시
    echo -n "."
    if [ $((30 - RETRIES)) -gt 0 ] && [ $(((30 - RETRIES) % 10)) -eq 0 ]; then
        echo -n " (${HEALTHY}/${EXPECTED_HEALTHY} healthy)"
    fi

    sleep $WAIT_SECONDS
    RETRIES=$((RETRIES - 1))
done

echo

if [ $RETRIES -eq 0 ]; then
    log_error "Health check timeout!"
    log_error "Only ${HEALTHY}/${EXPECTED_HEALTHY} services are healthy"
    echo
    log_info "Current service status:"
    docker-compose ps
    echo
    log_error "Check logs: docker-compose logs -f"
    exit 1
fi

# API 엔드포인트 헬스 체크
log_info "Testing API endpoint..."

API_RETRIES=10
while [ $API_RETRIES -gt 0 ]; do
    if curl -sf http://localhost:2542/health > /dev/null 2>&1; then
        log_success "✓ API health check passed"
        break
    fi
    sleep 1
    API_RETRIES=$((API_RETRIES - 1))
done

if [ $API_RETRIES -eq 0 ]; then
    log_error "API health check failed"
    log_error "URL: http://localhost:2542/health"
    exit 1
fi

# 최종 상태 출력
echo
log_success "============================================"
log_success "Installation completed successfully!"
log_success "============================================"
echo
log_info "Service URLs:"
log_info "  Frontend: https://localhost (or http://localhost:80)"
log_info "  API:      http://localhost:2542"
log_info "  Health:   http://localhost:2542/health"
echo
log_info "Useful commands:"
log_info "  View logs:    docker-compose logs -f"
log_info "  Stop:         docker-compose down"
log_info "  Restart:      docker-compose restart"
log_info "  Status:       docker-compose ps"
echo

HEALTH_CHECK
```

---

### Phase 2 완료 기준

- [ ] install.sh에 사전 검증 로직 추가
- [ ] Docker 이미지 로드 시 진행 표시
- [ ] 설치 실패 시 자동 롤백 작동
- [ ] 설치 완료 후 자동 헬스 체크
- [ ] 모든 서비스 healthy 상태 확인
- [ ] API 엔드포인트 응답 확인

**측정 지표**:
- 설치 성공률: Unknown → 95%+
- 평균 설치 시간: Unknown → <5분
- 설치 실패 복구: 수동 → 자동

---

## 🟡 Phase 3: Documentation & Dependency (Week 3-4)

**목표**: 문서 일관성 및 에어갭 환경 완전 지원
**소요 시간**: 4.5시간
**담당**: 문서팀/DevOps
**우선순위**: 🟡 **중간**

### Task 3.1: 문서 버전 통합 (2시간)

**작업 내용**:
1. 템플릿 기반 문서 생성
2. 빌드 시 동적 변수 치환
3. 모든 문서 검증 스크립트

```bash
# 새 파일: scripts/generate-docs.sh
#!/bin/bash

VERSION=$(cat VERSION)
PACKAGE_SIZE=$(du -h offline-packages/*.tar.gz | cut -f1)
BUILD_DATE=$(date +%Y-%m-%d)

# 템플릿에서 문서 생성
for template in docs/templates/*.md.template; do
    output="${template%.template}"

    sed -e "s/{{VERSION}}/${VERSION}/g" \
        -e "s/{{PACKAGE_SIZE}}/${PACKAGE_SIZE}/g" \
        -e "s/{{BUILD_DATE}}/${BUILD_DATE}/g" \
        "$template" > "$output"
done
```

---

### Task 3.2: 체크섬 검증 추가 (30분)

```bash
# install.sh에 추가 (Step 1 전)
log_info "Verifying package integrity..."
cd ..

CHECKSUM_FILE="$(basename $PWD).tar.gz.sha256"

if [ -f "$CHECKSUM_FILE" ]; then
    if sha256sum -c "$CHECKSUM_FILE" 2>/dev/null; then
        log_success "✓ Checksum verification passed"
    else
        log_error "Checksum mismatch!"
        log_error "Package may be corrupted during transfer"
        log_error "Re-download the package or check file integrity"
        exit 1
    fi
else
    log_warning "No checksum file found - skipping verification"
    log_warning "Recommended: Always verify checksums in production"
fi

cd scripts
```

---

### Task 3.3: pip 설치 프로그램 번들 (1시간)

에어갭 환경에서 pip가 없는 경우 대비

---

### Task 3.4: 문서 인덱스 페이지 (1시간)

XWiki 문서 구조 개선

---

## 🟢 Phase 4: Optimization (Optional)

**목표**: 성능 최적화 및 CI/CD 자동화
**소요 시간**: 7시간+
**담당**: DevOps/개발팀
**우선순위**: 🟢 **낮음**

### Task 4.1: Collector 이미지 최적화 (3시간)

Multi-stage build 적용으로 650MB → 450MB 감소

---

### Task 4.2: 자동 테스팅 파이프라인 (4시간)

```bash
# scripts/test-package-installation.sh
#!/bin/bash
# 오프라인 패키지 자동 검증
```

---

## 📅 전체 일정

| Phase | 주차 | 소요 시간 | 주요 작업 | 완료 기준 |
|-------|------|----------|----------|----------|
| **Phase 1** | Week 1 | 37분 | Critical 보안/구성 | 3개 이슈 해결 |
| **Phase 2** | Week 2 | 3시간 | 설치 안정성 | 4개 이슈 해결 |
| **Phase 3** | Week 3-4 | 4.5시간 | 문서/종속성 | 4개 이슈 해결 |
| **Phase 4** | 선택적 | 7시간+ | 최적화/자동화 | 2개 이슈 해결 |

**총 소요 시간**: 15시간 (Phase 1-3 기준)

---

## 🎯 성공 메트릭

| 메트릭 | 현재 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|------|---------|---------|---------|---------|
| **보안 점수** | 75 | 90 | 90 | 90 | 95 |
| **설치 성공률** | ? | 90% | 95% | 98% | 99% |
| **평균 설치 시간** | ? | ? | <5분 | <4분 | <3분 |
| **문서 일관성** | 60% | 70% | 70% | 100% | 100% |
| **패키지 크기** | 701MB | 701MB | 701MB | 701MB | 550MB |

---

## 📋 다음 단계

### 즉시 실행 (오늘)

**Phase 1 Quick Wins (37분)**:
```bash
# 1. .env 제외 (2분)
vim scripts/create-complete-offline-package.sh
# Line 78: --exclude='.env' 추가

# 2. SECUDIUM 자격증명 (5분)
vim .env.example
# SECUDIUM_ID, SECUDIUM_PW 추가

# 3. VERSION 파일 (30분)
echo "3.3.1" > VERSION
git add VERSION
# 스크립트 수정...

# 4. 패키지 재생성 및 검증
bash scripts/create-complete-offline-package.sh
```

### Week 2 계획

Phase 2 작업 착수

### Week 3-4 계획

Phase 3 작업 + Phase 2 피드백 반영

---

**문서 버전**: v1.0
**최종 업데이트**: 2025-10-21
**작성자**: Claude Code (Sonnet 4.5) + Grok 4
