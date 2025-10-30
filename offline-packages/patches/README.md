# Runtime Patches

**Runtime patches for deployed Blacklist systems** - Apply fixes without Docker image rebuild.

## 🚀 Auto-Patching (v3.3.8+)

**컨테이너 재부팅 시 자동으로 적용됩니다!**

- **스마트 감지**: 적용 안된 패치만 실행
- **추적 파일**: `/app/.applied_patches` (성공한 패치 기록)
- **실행 순서**: 파일명 순 (005, 006, 007...)
- **통계**: Applied/Skipped/Failed 카운트 표시

**사용법**:
```bash
# 1. 컨테이너 시작/재시작 (자동 패치 적용)
docker compose restart blacklist-app

# 2. 로그 확인
docker logs blacklist-app | grep -A 15 "Entrypoint"

# 3. 패치 히스토리 확인
docker exec blacklist-app cat /app/.applied_patches
```

**Example Output** (첫 실행):
```
🔍 Scanning patches: 3 total
  → Applying: 001-upgrade-entrypoint-smart-detection.sh
  ✓ 001-upgrade-entrypoint-smart-detection.sh applied successfully
  → Applying: 002-migrate-to-traefik.sh
  ✓ 002-migrate-to-traefik.sh applied successfully
  → Applying: 003-fix-credential-initialization.sh
  ✓ 003-fix-credential-initialization.sh applied successfully
✓ Summary: Applied: 3 | Skipped: 0 | Failed: 0
📋 Total patches in history: 3
```

**Example Output** (재부팅 시):
```
🔍 Scanning patches: 3 total
  ⊙ 001-upgrade-entrypoint-smart-detection.sh (already applied, skipping)
  ⊙ 002-migrate-to-traefik.sh (already applied, skipping)
  ⊙ 003-fix-credential-initialization.sh (already applied, skipping)
✓ Summary: Applied: 0 | Skipped: 3 | Failed: 0
📋 Total patches in history: 3
```

---

## Available Patches

### 000-upgrade-entrypoint-smart-detection.sh (v3.3.8+) ⚠️ MUST RUN FIRST

**Purpose**: 기존 배포된 시스템에 스마트 패치 감지 시스템 업그레이드

**Priority**: 최우선 실행 (다른 모든 패치가 작동하려면 이 패치가 먼저 필요)

**Problem**:
1. 구버전 entrypoint.sh는 모든 패치를 매번 재실행
2. 불필요한 CPU/시간 소모, 복잡한 로그

**Solution**:
1. entrypoint.sh를 스마트 감지 버전으로 교체
2. 패치 추적 파일 생성 (`/app/.applied_patches`)
3. Applied/Skipped/Failed 통계 표시

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app

# Manual execution (기존 배포 시스템에서 수동 실행)
bash offline-packages/patches/000-air-gap-fix-all.sh
```

**What it does**:
1. ✅ HTTPS 포트 통일 (config.py, monitoring_scheduler.py, secudium_api.py)
2. ✅ Monitoring scheduler HTTPS 설정
3. ✅ SECUDIUM URL 및 경로 수정
4. ✅ DB 마이그레이션 013 (notify trigger)
5. ✅ DB 마이그레이션 014 (source column)
6. ✅ REGTECH 인증 엔드포인트 수정
7. ✅ Collection interval 설정
8. ✅ 서비스 재시작 및 검증

**Post-Patch Steps**:
```bash
# 1. Check logs
docker logs blacklist-app | grep "Air-Gap"

# 2. Verify fixes (6 checks)
# - Containers running
# - Database connection
# - API health
# - Migration 013 (notify trigger)
# - Migration 014 (source column)
# - HTTPS configuration

# 3. Test collection
curl -X POST http://localhost:2542/api/collection/regtech/trigger
```

**Expected Results**:
- ✅ All services using HTTPS protocol
- ✅ Database migrations applied
- ✅ REGTECH authentication working
- ✅ Collection interval set to 3600s
- ✅ Verification: 6/6 checks passed

**⚠️ Important Notes**:
- **Runs FIRST** (000 prefix for highest priority)
- Auto-detects PostgreSQL password (.env or defaults)
- 3 retry attempts on service restart
- Detailed progress logging
- Safe to re-run (idempotent operations)

---

### 001-upgrade-entrypoint-smart-detection.sh (v3.3.8+)

**Purpose**: 기존 배포된 시스템에 스마트 패치 감지 시스템 업그레이드

**Problem**:
1. 구버전 entrypoint.sh는 모든 패치를 매번 재실행
2. 불필요한 CPU/시간 소모, 복잡한 로그

**Solution**:
1. entrypoint.sh를 스마트 감지 버전으로 교체
2. 패치 추적 파일 생성 (`/app/.applied_patches`)
3. Applied/Skipped/Failed 통계 표시

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app

# Manual execution (기존 배포 시스템에서 수동 실행)
docker exec blacklist-app bash /patches/000-upgrade-entrypoint-smart-detection.sh
docker compose restart blacklist-app  # 재시작 필수!
```

**What it does**:
1. ✅ Check if already patched (idempotency: `is_patch_applied()` function check)
2. ✅ Backup original entrypoint.sh to `/tmp/patch-001-backup/`
3. ✅ Replace entrypoint.sh with smart detection version
4. ✅ Set executable permissions (chmod +x)
5. ✅ Verify smart detection functions present

**Post-Patch Steps**:
```bash
# CRITICAL: Restart container to apply new entrypoint
docker compose restart blacklist-app

# Verify smart detection working
docker logs blacklist-app | grep "Scanning patches"
# Expected: Applied: X | Skipped: Y | Failed: 0

# Check patch history
docker exec blacklist-app cat /app/.applied_patches
```

**Expected Results**:
- ✅ `/app/entrypoint.sh` contains `is_patch_applied()` function
- ✅ `/app/entrypoint.sh` contains `APPLIED_PATCHES_FILE` variable
- ✅ Executable permissions set (755)
- ✅ Next restart: Smart detection active
- ✅ Patches show "already applied, skipping" on re-run

**⚠️ Important Notes**:
- **Takes effect on NEXT container restart** (not immediate)
- Must restart container after patch execution
- Compatible with all existing patches (002, 003)
- Tracking file: `/app/.applied_patches` (persistent)

**Testing**:
```bash
# 1. Apply patch
docker exec blacklist-app bash /patches/000-upgrade-entrypoint-smart-detection.sh

# 2. Restart container (REQUIRED)
docker compose restart blacklist-app

# 3. First run - all patches applied
docker logs blacklist-app | grep "Summary"
# Expected: Applied: 6 | Skipped: 0 | Failed: 0

# 4. Restart again - all patches skipped
docker compose restart blacklist-app
docker logs blacklist-app | grep "Summary"
# Expected: Applied: 0 | Skipped: 6 | Failed: 0

# 5. View history
docker exec blacklist-app cat /app/.applied_patches
# 000-upgrade-entrypoint-smart-detection.sh
# 001-air-gap-fix-all.sh
# 002-master-regtech-fix.sh
# 003-migrate-to-traefik.sh
# 004-fix-credential-initialization.sh
# 005-fix-http-to-https-permanent.sh
```

---

### 001-air-gap-fix-all.sh (v3.3.9) ⚠️ MASTER AIR-GAP FIX

**Purpose**: Air-gap 환경 종합 수정 (all-in-one comprehensive fix)

**Problem**:
1. Air-gap 환경에서 HTTPS 포트 설정 오류 (8443 사용)
2. Monitoring scheduler HTTP 프로토콜 사용
3. SECUDIUM URL 및 파일 경로 오류
4. 데이터베이스 마이그레이션 누락 (013, 014)
5. REGTECH 인증 설정 문제
6. Collection interval 미설정

**Solution**:
1. HTTPS 포트 통일 (모든 서비스 443 포트 사용)
2. Monitoring scheduler HTTPS URL 변경
3. SECUDIUM 설정 수정
4. DB 마이그레이션 자동 적용 (013_notify_trigger, 014_source_column)
5. REGTECH 인증 엔드포인트 수정
6. Collection interval 3600초(1시간) 설정

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app

# Manual execution
bash offline-packages/patches/001-air-gap-fix-all.sh
```

**What it does**:
1. ✅ HTTPS 포트 통일 (config.py, monitoring_scheduler.py, secudium_api.py)
2. ✅ Monitoring scheduler HTTPS 설정
3. ✅ SECUDIUM URL 및 경로 수정
4. ✅ DB 마이그레이션 013 (notify trigger)
5. ✅ DB 마이그레이션 014 (source column)
6. ✅ REGTECH 인증 엔드포인트 수정
7. ✅ Collection interval 설정
8. ✅ 서비스 재시작 및 검증 (6 checks)

**Expected Results**:
- ✅ All services using HTTPS protocol
- ✅ Database migrations applied
- ✅ REGTECH authentication working
- ✅ Collection interval set to 3600s
- ✅ Verification: 6/6 checks passed

---

### 002-master-regtech-fix.sh (v3.3.9) ⚠️ MASTER REGTECH FIX

**Purpose**: REGTECH 인증 종합 수정 (authentication comprehensive fix)

**Problem**:
1. REGTECH 인증 엔드포인트 포트 오류
2. 인증 순서 문제 (findOneMember → addLogin)

**Solution**:
1. REGTECH 인증 URL 수정 (포트 제거)
2. Two-stage 인증 순서 확인

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app

# Manual execution
bash offline-packages/patches/002-master-regtech-fix.sh
```

---

### 003-migrate-to-traefik.sh (v3.3.8)

**Problem**:
1. nginx 기반 배포에서 Traefik 기반으로 전환 필요
2. HTTPS-only (443 포트) 설정으로 간소화
3. Traefik labels 최적화 (15+ lines → 6 lines)

**Solution**:
1. docker-compose.yml에 Traefik 설정 추가
2. blacklist-frontend에 traefik-public 네트워크 연결
3. HTTPS-only labels 설정 (HTTP redirect 제거)

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app

# Manual execution
docker exec blacklist-app bash /patches/002-migrate-to-traefik.sh
```

**What it does**:
1. ✅ Backup docker-compose.yml to `/tmp/patch-002-backup/`
2. ✅ Add traefik-public network definition
3. ✅ Add traefik-public to blacklist-frontend networks
4. ✅ Add Traefik labels (6 lines, HTTPS-only)
5. ✅ Verify changes (labels + network present)

**Post-Patch Steps**:
```bash
# 1. Create traefik-public network
docker network create traefik-public

# 2. Ensure Traefik is running
docker ps | grep traefik

# 3. Restart services
docker compose restart blacklist-frontend

# 4. Test access
curl -k https://blacklist.nxtd.co.kr
```

**Expected Results**:
- ✅ docker-compose.yml has traefik-public network
- ✅ blacklist-frontend has Traefik labels
- ✅ HTTPS-only configuration (port 443)
- ✅ nginx container can be stopped (optional)

---

### 004-fix-credential-initialization.sh (v3.3.8)

**Purpose**: Credential 초기화 UX 개선

**Problem**:
1. 초기에 credential 정보가 없을 때 "REGTECH 인증 정보 없음" 경고 메시지가 계속 출력됨
2. 인증 정보가 없는 상태에서도 설정 UI가 정상 동작해야 함

**Solution**:
1. `secure_credential_service.py` - 인증 정보 없을 때 warning 대신 debug 로그 사용
2. `monitoring_scheduler.py` - credentials 조회 시 조용히 None 반환
3. `collection_panel.py` - credentials 없을 때 기본값으로 초기화

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app

# Manual execution
docker exec blacklist-app bash /patches/004-fix-credential-initialization.sh
```

**What it does**:
1. ✅ Backup original files to `/tmp/patch-003-backup-*`
2. ✅ Modify `secure_credential_service.py` (logger.warning → logger.debug)
3. ✅ Verify `collection_panel.py` returns proper defaults
4. ✅ Restart Flask application
5. ✅ Test credentials API endpoint
6. ✅ Verify no warning logs for uninitialized credentials

**Testing**:
```bash
# 1. Open collection panel
https://blacklist.nxtd.co.kr/collection-panel

# 2. Verify no errors in UI (credentials form should load)

# 3. Check logs (should be clean, no warnings)
docker logs blacklist-app --tail 50 | grep -i credential
```

**Expected Results**:
- ✅ Collection panel loads without errors
- ✅ Empty credential form displays correctly
- ✅ No "인증 정보 없음" warning logs
- ✅ Scheduler starts silently without credentials
- ✅ Users can save credentials via UI

---

### 005-fix-http-to-https-permanent.sh (v3.3.9)

**Purpose**: HTTP 프로토콜을 HTTPS로 변경 (Traefik 환경)

**Context**:
- Traefik reverse proxy 사용 환경
- 내부 컨테이너 간 통신도 HTTPS 프로토콜 사용
- 포트는 기본 HTTPS 포트 (443) 사용 (명시 불필요)

**Problem**:
1. `http://blacklist-app:443` → 프로토콜 잘못됨 (HTTP가 아닌 HTTPS)
2. `http://localhost:443` → 프로토콜 잘못됨
3. `session.mount("http://")` 만 있음 → HTTPS 우선 추가 필요

**Solution**:
1. `collection_panel.py`: `http://blacklist-app:443` → `https://blacklist-app` (포트 제거)
2. `fortimanager_push_service.py`: `http://localhost:443` → `https://localhost` (포트 제거)
3. `fortimanager_uploader.py`: `http://blacklist-app:443` → `https://blacklist-app`
4. `regtech_collector.py`: HTTPS adapter 우선 추가

**Usage**:
```bash
# Auto-patching (컨테이너 재시작 시 자동 적용)
docker compose restart blacklist-app
```

**What it does**:
1. ✅ Backup files with `.bak.004-fix-http-to-https-permanent` suffix
2. ✅ Fix HTTP 443 → HTTPS (port removed) in collection_panel.py
3. ✅ Fix HTTP 443 → HTTPS in fortimanager_push_service.py
4. ✅ Fix HTTP 443 → HTTPS in fortimanager_uploader.py
5. ✅ Add HTTPS adapter priority in regtech_collector.py

**Expected Results**:
- ✅ All internal communication uses HTTPS protocol
- ✅ No port numbers in HTTPS URLs (default 443)
- ✅ HTTPS adapter mounted before HTTP adapter

---

## Patch Development Guide

**Creating new patches**:

```bash
# 1. Create patch script
vi offline-packages/patches/006-your-patch-name.sh

# 2. Follow template structure:
#!/bin/bash
set -euo pipefail

# Color codes, logging functions
# Backup files
# Apply patches
# Verification
# Restart services
# Test

# 3. Make executable
chmod +x offline-packages/patches/004-your-patch-name.sh

# 4. Test in container
docker exec blacklist-app bash /patches/004-your-patch-name.sh

# 5. Update this README
```

**Best Practices**:
- ✅ Always backup original files
- ✅ Use sed/awk for surgical code changes
- ✅ Verify changes before restart
- ✅ Test API endpoints after restart
- ✅ Provide rollback instructions
- ✅ Log all changes clearly

**Rollback**:
```bash
# Restore from backup
BACKUP_DIR=$(ls -td /tmp/patch-003-backup-* | head -1)
docker exec blacklist-app cp $BACKUP_DIR/secure_credential_service.py /app/core/services/
docker exec blacklist-app cp $BACKUP_DIR/collection_panel.py /app/core/routes/
docker compose restart blacklist-app
```

---

## Version History

| Patch | Version | Date | Description |
|-------|---------|------|-------------|
| 000 | 3.3.8+ | 2025-10-30 | **Smart patch system** (MUST run first) |
| 001 | 3.3.9 | 2025-10-30 | **Master air-gap fix** (all-in-one comprehensive) |
| 002 | 3.3.9 | 2025-10-30 | **Master REGTECH fix** (authentication) |
| 003 | 3.3.8 | 2025-10-30 | Migrate to Traefik reverse proxy |
| 004 | 3.3.8 | 2025-10-30 | Fix credential initialization issues |
| 005 | 3.3.9 | 2025-10-30 | Fix HTTP 443 → HTTPS (Traefik compatible) |

---

**Maintained by**: Claude Code
**Last Updated**: 2025-10-30
