#!/bin/bash
################################################################################
# 004-fix-http-to-https-permanent.sh
# HTTP 프로토콜을 HTTPS로 변경 (영구 수정)
#
# 문제:
#   1. http://blacklist-app:443 → https://blacklist-app (프로토콜 잘못됨)
#   2. http://localhost:443 → https://localhost (프로토콜 잘못됨)
#   3. session.mount("http://") 만 있음 → HTTPS 우선 추가
#
# 컨텍스트:
#   - Traefik reverse proxy 사용 환경
#   - 내부 컨테이너 간 통신도 HTTPS 프로토콜 사용
#   - 포트는 기본 HTTPS 포트 (443) 사용 (명시 불필요)
#
# 실행: 컨테이너 재시작 시 자동 적용 (entrypoint.sh)
# 버전: v3.3.9
################################################################################

set -euo pipefail

PATCH_NAME="004-fix-http-to-https-permanent"
echo "🔧 Applying patch: $PATCH_NAME"

# ==========================================
# Fix 1: collection_panel.py
# ==========================================
TARGET="/app/core/routes/collection_panel.py"
if [ -f "$TARGET" ]; then
    echo "  → Fixing $TARGET"

    # Backup
    cp "$TARGET" "${TARGET}.bak.${PATCH_NAME}" 2>/dev/null || true

    # http://blacklist-app:443 → https://blacklist-app (포트 제거)
    sed -i 's|http://blacklist-app:443|https://blacklist-app|g' "$TARGET"

    echo "    ✓ Fixed HTTP 443 → HTTPS (port removed)"
fi

# ==========================================
# Fix 2: fortimanager_push_service.py
# ==========================================
TARGET="/app/core/services/fortimanager_push_service.py"
if [ -f "$TARGET" ]; then
    echo "  → Fixing $TARGET"

    # Backup
    cp "$TARGET" "${TARGET}.bak.${PATCH_NAME}" 2>/dev/null || true

    # http://localhost:443 → https://localhost (포트 제거)
    sed -i 's|http://localhost:443|https://localhost|g' "$TARGET"

    echo "    ✓ Fixed HTTP 443 → HTTPS (port removed)"
fi

# ==========================================
# Fix 3: fortimanager_uploader.py
# ==========================================
TARGET="/app/collector/fortimanager_uploader.py"
if [ -f "$TARGET" ]; then
    echo "  → Fixing $TARGET"

    # Backup
    cp "$TARGET" "${TARGET}.bak.${PATCH_NAME}" 2>/dev/null || true

    # http://blacklist-app:443 → https://blacklist-app (포트 제거)
    sed -i 's|http://blacklist-app:443|https://blacklist-app|g' "$TARGET"

    echo "    ✓ Fixed HTTP 443 → HTTPS (port removed)"
fi

# ==========================================
# Fix 4: regtech_collector.py (HTTPS 우선)
# ==========================================
TARGET="/app/collector/core/regtech_collector.py"
if [ -f "$TARGET" ]; then
    echo "  → Fixing $TARGET"

    # Backup
    cp "$TARGET" "${TARGET}.bak.${PATCH_NAME}" 2>/dev/null || true

    # HTTPS 어댑터가 없으면 추가
    if ! grep -q 'self.session.mount("https://"' "$TARGET"; then
        # self.session.mount("http://", adapter) 라인 찾아서 그 위에 HTTPS 추가
        sed -i '/self\.session\.mount("http:\/\/", adapter)/i\        self.session.mount("https://", adapter)  # HTTPS 우선' "$TARGET"
        echo "    ✓ Added HTTPS adapter priority"
    else
        echo "    ⊙ HTTPS adapter already exists"
    fi
fi

echo "✅ Patch $PATCH_NAME applied successfully"
echo ""
