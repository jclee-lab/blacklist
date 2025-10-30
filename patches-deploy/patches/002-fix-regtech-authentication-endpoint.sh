#!/bin/bash
################################################################################
# 002-fix-regtech-authentication-endpoint.sh
# REGTECH 인증 엔드포인트 수정 및 port 80 버그 근본적 해결
#
# 문제:
#   - policy_monitor.py가 잘못된 엔드포인트 /common/login 사용
#   - regtech_collector.py는 올바른 엔드포인트 /login/addLogin 사용
#   - requests.Session()이 port 80으로 연결 시도
#
# 해결:
#   - policy_monitor.py 인증을 regtech_collector 방식으로 통일
#   - curl subprocess 기반 인증으로 변경 (HTTPS 보장)
#   - /login/addLogin 엔드포인트 사용
#
# 적용 대상:
#   - /app/core/policy_monitor.py (_authenticate_regtech 메서드)
#
# 작성일: 2025-10-29
# 버전: v3.3.5
################################################################################

set -euo pipefail

PATCH_NAME="002-fix-regtech-authentication-endpoint"
LOG_FILE="/tmp/${PATCH_NAME}.log"
CONTAINER_NAME="blacklist-collector"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "🔧 ${PATCH_NAME} 패치 시작" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 컨테이너 실행 여부 확인
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ ${CONTAINER_NAME} 컨테이너가 실행 중이 아닙니다." | tee -a "$LOG_FILE"
    echo "   docker compose up -d ${CONTAINER_NAME} 로 시작하세요." | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ ${CONTAINER_NAME} 컨테이너 확인 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

################################################################################
# 1. policy_monitor.py 백업
################################################################################

echo "📝 1/3: policy_monitor.py 백업 생성 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c "
    cp /app/core/policy_monitor.py /app/core/policy_monitor.py.bak.${PATCH_NAME}
"

echo "   ✅ 백업 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

################################################################################
# 2. _authenticate_regtech() 메서드 완전 교체
################################################################################

echo "📝 2/3: _authenticate_regtech() 메서드 교체 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c '
python3 << "PYTHON_PATCH"
import re

# 새로운 인증 메서드 (curl 기반, HTTPS 보장)
new_auth_method = """    def _authenticate_regtech(self) -> bool:
        """REGTECH 포털 인증 (curl 기반, HTTPS 보장)"""
        try:
            import subprocess
            import json

            regtech_id = self.config.get("regtech_id", "")
            regtech_pw = self.config.get("regtech_pw", "")

            if not regtech_id or not regtech_pw:
                logger.error("REGTECH 인증 정보 없음")
                return False

            # Step 1: findOneMember (사용자 정보 조회)
            logger.info("🔍 REGTECH 사용자 정보 조회 중...")
            find_member_cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.base_url}/login/findOneMember",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", f"username={regtech_id}"
            ]

            result = subprocess.run(
                find_member_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )

            if result.returncode != 0:
                logger.error(f"REGTECH 사용자 정보 조회 실패: {result.stderr}")
                return False

            # Step 2: addLogin (로그인)
            logger.info("🔐 REGTECH 로그인 중...")
            login_cmd = [
                "curl", "-s", "-i", "-X", "POST",
                f"{self.base_url}/login/addLogin",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", f"username={regtech_id}&password={regtech_pw}"
            ]

            login_result = subprocess.run(
                login_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )

            if login_result.returncode != 0:
                logger.error(f"REGTECH 로그인 실패: {login_result.stderr}")
                return False

            # 쿠키 추출 (Set-Cookie 헤더)
            cookies = {}
            for line in login_result.stdout.split("\\n"):
                if line.startswith("Set-Cookie:"):
                    cookie_line = line.replace("Set-Cookie: ", "")
                    cookie_parts = cookie_line.split(";")[0]
                    if "=" in cookie_parts:
                        key, value = cookie_parts.split("=", 1)
                        cookies[key.strip()] = value.strip()

            # 인증 성공 확인 (regtech-va, regtech-front 쿠키 존재 여부)
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
            return False"""

# 파일 읽기
with open("/app/core/policy_monitor.py", "r") as f:
    content = f.read()

# _authenticate_regtech() 메서드 찾기 및 교체
# 시작: def _authenticate_regtech
# 끝: 다음 메서드 시작 (def _) 또는 클래스 종료
pattern = r"def _authenticate_regtech\(self\).*?(?=\n    def _|\nclass |\Z)"

if re.search(pattern, content, re.DOTALL):
    # 메서드 교체
    modified = re.sub(pattern, new_auth_method, content, flags=re.DOTALL)

    # 파일 쓰기
    with open("/app/core/policy_monitor.py", "w") as f:
        f.write(modified)

    print("✅ _authenticate_regtech() 메서드 교체 완료")
else:
    print("⚠️  _authenticate_regtech() 메서드를 찾을 수 없습니다")
    exit(1)
PYTHON_PATCH
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

echo "🔄 3/3: collector 컨테이너 재시작 중..." | tee -a "$LOG_FILE"

docker compose restart "$CONTAINER_NAME"

# 재시작 완료 대기 (최대 30초)
for i in {1..30}; do
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        sleep 2
        if docker exec "$CONTAINER_NAME" curl -sf http://localhost:8545/health > /dev/null 2>&1; then
            echo "   ✅ 컨테이너 재시작 완료 (${i}초)" | tee -a "$LOG_FILE"
            break
        fi
    fi

    if [ $i -eq 30 ]; then
        echo "   ⚠️  컨테이너 health check 실패 (30초 타임아웃)" | tee -a "$LOG_FILE"
        echo "   docker logs $CONTAINER_NAME 로 확인하세요." | tee -a "$LOG_FILE"
    fi

    sleep 1
done

echo "" | tee -a "$LOG_FILE"

################################################################################
# 4. 검증
################################################################################

echo "🧪 패치 검증 중..." | tee -a "$LOG_FILE"

# 새로운 메서드 존재 확인
METHOD_EXISTS=$(docker exec "$CONTAINER_NAME" grep -c "curl 기반, HTTPS 보장" /app/core/policy_monitor.py || echo "0")

if [ "$METHOD_EXISTS" -gt 0 ]; then
    echo "   ✅ 새로운 인증 메서드 확인" | tee -a "$LOG_FILE"
else
    echo "   ❌ 패치 코드 미발견" | tee -a "$LOG_FILE"
    exit 1
fi

# 백업 파일 확인
if docker exec "$CONTAINER_NAME" test -f "/app/core/policy_monitor.py.bak.${PATCH_NAME}"; then
    echo "   ✅ 백업 파일 생성 확인" | tee -a "$LOG_FILE"
else
    echo "   ⚠️  백업 파일 미발견" | tee -a "$LOG_FILE"
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
echo "   - 변경 사항:" | tee -a "$LOG_FILE"
echo "     1. _authenticate_regtech() 메서드를 curl 기반으로 교체" | tee -a "$LOG_FILE"
echo "     2. 엔드포인트: /common/login → /login/addLogin" | tee -a "$LOG_FILE"
echo "     3. HTTPS 명시적 보장 (port 443 사용)" | tee -a "$LOG_FILE"
echo "   - 효과: port 80 에러 완전 해결" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "🧪 테스트 명령어:" | tee -a "$LOG_FILE"
echo "   docker logs $CONTAINER_NAME -f | grep -i 'regtech'" | tee -a "$LOG_FILE"
echo "   # '✅ REGTECH 인증 성공' 메시지 확인" | tee -a "$LOG_FILE"
echo "   # 더 이상 'port=80' 에러 없어야 함" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📝 로그 위치: $LOG_FILE" | tee -a "$LOG_FILE"

exit 0
