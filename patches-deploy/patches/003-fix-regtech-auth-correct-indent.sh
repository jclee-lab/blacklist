#!/bin/bash
################################################################################
# 003-fix-regtech-auth-correct-indent.sh
# REGTECH 인증 메서드 교체 (들여쓰기 수정 버전)
#
# 문제:
#   - policy_monitor.py의 _authenticate_regtech() 메서드가 port 80 사용
#   - 잘못된 엔드포인트 /common/login 사용
#
# 해결:
#   - curl 기반 인증으로 교체 (HTTPS 보장)
#   - 올바른 엔드포인트 /login/addLogin 사용
#   - 정확한 들여쓰기 유지 (4 spaces)
#
# 작성일: 2025-10-29
# 버전: v3.3.5
################################################################################

set -euo pipefail

PATCH_NAME="003-fix-regtech-auth-correct-indent"
LOG_FILE="/tmp/${PATCH_NAME}.log"
CONTAINER_NAME="blacklist-collector"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee "$LOG_FILE"
echo "🔧 ${PATCH_NAME} 패치 시작" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 컨테이너 실행 여부 확인
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ ${CONTAINER_NAME} 컨테이너가 실행 중이 아닙니다." | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ ${CONTAINER_NAME} 컨테이너 확인 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

################################################################################
# 1. 백업
################################################################################

echo "📝 Step 1/3: 백업 생성 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c "
    cp /app/core/policy_monitor.py /app/core/policy_monitor.py.bak.${PATCH_NAME}
"

echo "   ✅ 백업 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

################################################################################
# 2. 메서드 교체 (정확한 들여쓰기)
################################################################################

echo "📝 Step 2/3: _authenticate_regtech() 메서드 교체 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c '
python3 << "EOF"
import re

# 파일 읽기
with open("/app/core/policy_monitor.py", "r") as f:
    content = f.read()

# 이미 패치되었는지 확인
if "curl 기반, HTTPS 보장" in content:
    print("⚠️  이미 패치됨 (건너뜀)")
    exit(0)

# 기존 _authenticate_regtech() 메서드 찾기 및 삭제
# 시작: "def _authenticate_regtech(self)"
# 끝: 다음 메서드 시작 또는 클래스 종료
pattern = r"    def _authenticate_regtech\(self\) -> bool:.*?(?=\n    def |$)"

if not re.search(pattern, content, re.DOTALL):
    print("❌ _authenticate_regtech() 메서드를 찾을 수 없습니다")
    exit(1)

# 새로운 메서드 (4 spaces 들여쓰기)
new_method = """    def _authenticate_regtech(self) -> bool:
        \"\"\"REGTECH 포털 인증 (curl 기반, HTTPS 보장)\"\"\"
        try:
            import subprocess

            regtech_id = self.config.get("regtech_id", "")
            regtech_pw = self.config.get("regtech_pw", "")

            if not regtech_id or not regtech_pw:
                logger.error("REGTECH 인증 정보 없음")
                return False

            # Step 1: findOneMember
            logger.info("🔍 REGTECH 사용자 정보 조회 중...")
            find_cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.base_url}/login/findOneMember",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", f"username={regtech_id}"
            ]

            result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=20)
            if result.returncode != 0:
                logger.error(f"REGTECH 사용자 정보 조회 실패: {result.stderr}")
                return False

            # Step 2: addLogin
            logger.info("🔐 REGTECH 로그인 중...")
            login_cmd = [
                "curl", "-s", "-i", "-X", "POST",
                f"{self.base_url}/login/addLogin",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", f"username={regtech_id}&password={regtech_pw}"
            ]

            login_result = subprocess.run(login_cmd, capture_output=True, text=True, timeout=20)
            if login_result.returncode != 0:
                logger.error(f"REGTECH 로그인 실패: {login_result.stderr}")
                return False

            # 쿠키 추출
            cookies = {}
            for line in login_result.stdout.split("\\\\n"):
                if line.startswith("Set-Cookie:"):
                    cookie_line = line.replace("Set-Cookie: ", "")
                    cookie_parts = cookie_line.split(";")[0]
                    if "=" in cookie_parts:
                        key, value = cookie_parts.split("=", 1)
                        cookies[key.strip()] = value.strip()

            # 인증 성공 확인
            if "regtech-va" in cookies and "regtech-front" in cookies:
                logger.info(f"✅ REGTECH 인증 성공 (쿠키: {len(cookies)}개)")

                # 세션 쿠키 업데이트
                for key, value in cookies.items():
                    self.session.cookies.set(key, value)

                return True
            else:
                logger.error("REGTECH 인증 실패 (쿠키 없음)")
                return False

        except subprocess.TimeoutExpired:
            logger.error("REGTECH 인증 타임아웃 (20초)")
            return False
        except Exception as e:
            logger.error(f"REGTECH 인증 중 오류: {e}")
            return False
"""

# 메서드 교체
modified = re.sub(pattern, new_method, content, flags=re.DOTALL)

# 파일 쓰기
with open("/app/core/policy_monitor.py", "w") as f:
    f.write(modified)

print("✅ _authenticate_regtech() 메서드 교체 완료")
EOF
'

if [ $? -eq 0 ]; then
    echo "   ✅ 메서드 교체 완료" | tee -a "$LOG_FILE"
else
    echo "   ❌ 메서드 교체 실패" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"

################################################################################
# 3. 컨테이너 재시작
################################################################################

echo "🔄 Step 3/3: 컨테이너 재시작 중..." | tee -a "$LOG_FILE"

docker compose restart "$CONTAINER_NAME" > /dev/null 2>&1

# 재시작 완료 대기
for i in {1..30}; do
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        sleep 2

        # health check
        if docker exec "$CONTAINER_NAME" curl -sf http://localhost:8545/health > /dev/null 2>&1; then
            echo "   ✅ 컨테이너 재시작 완료 (${i}초)" | tee -a "$LOG_FILE"
            break
        fi
    fi

    if [ $i -eq 30 ]; then
        echo "   ⚠️  Health check 실패 (30초 타임아웃)" | tee -a "$LOG_FILE"
        echo "   docker logs $CONTAINER_NAME 로 확인하세요." | tee -a "$LOG_FILE"
    fi

    sleep 1
done

echo "" | tee -a "$LOG_FILE"

################################################################################
# 4. 검증
################################################################################

echo "🧪 패치 검증 중..." | tee -a "$LOG_FILE"

# 구문 에러 확인
SYNTAX_ERROR=$(docker logs "$CONTAINER_NAME" 2>&1 | grep -c "IndentationError\|SyntaxError" || echo "0")

if [ "$SYNTAX_ERROR" -gt 0 ]; then
    echo "   ❌ 구문 에러 발견!" | tee -a "$LOG_FILE"
    echo "   백업 복구 중..." | tee -a "$LOG_FILE"
    docker exec "$CONTAINER_NAME" cp "/app/core/policy_monitor.py.bak.${PATCH_NAME}" /app/core/policy_monitor.py
    docker compose restart "$CONTAINER_NAME" > /dev/null 2>&1
    exit 1
else
    echo "   ✅ 구문 에러 없음" | tee -a "$LOG_FILE"
fi

# 패치 코드 확인
PATCH_FOUND=$(docker exec "$CONTAINER_NAME" grep -c "curl 기반, HTTPS 보장" /app/core/policy_monitor.py || echo "0")

if [ "$PATCH_FOUND" -gt 0 ]; then
    echo "   ✅ 패치 코드 존재 확인" | tee -a "$LOG_FILE"
else
    echo "   ❌ 패치 코드 미발견" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

################################################################################
# 5. 완료
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "✅ ${PATCH_NAME} 패치 완료" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📋 패치 요약:" | tee -a "$LOG_FILE"
echo "   ✅ _authenticate_regtech() curl 기반으로 교체" | tee -a "$LOG_FILE"
echo "   ✅ 엔드포인트: /common/login → /login/addLogin" | tee -a "$LOG_FILE"
echo "   ✅ HTTPS 명시적 보장 (port 443)" | tee -a "$LOG_FILE"
echo "   ✅ 정확한 들여쓰기 유지" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "🧪 테스트:" | tee -a "$LOG_FILE"
echo "   docker logs $CONTAINER_NAME -f | grep -i 'regtech'" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📝 로그: $LOG_FILE" | tee -a "$LOG_FILE"

exit 0
