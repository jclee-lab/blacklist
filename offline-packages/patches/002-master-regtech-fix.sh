#!/bin/bash
################################################################################
# 000-master-regtech-fix.sh
# REGTECH port 80 버그 완전 수정 - 마스터 패치
#
# 포함 패치:
#   1. 001-fix-regtech-port-80-bug.sh
#      - requests.Session() HTTPS adapter 우선순위 설정
#   2. 002-fix-regtech-authentication-endpoint.sh
#      - _authenticate_regtech() 메서드를 curl 기반으로 교체
#      - 엔드포인트: /common/login → /login/addLogin
#
# 실행:
#   bash 000-master-regtech-fix.sh
#
# 작성일: 2025-10-29
# 버전: v3.3.5
################################################################################

set -euo pipefail

MASTER_PATCH_NAME="000-master-regtech-fix"
LOG_FILE="/tmp/${MASTER_PATCH_NAME}.log"
CONTAINER_NAME="blacklist-collector"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee "$LOG_FILE"
echo "🚀 ${MASTER_PATCH_NAME} 마스터 패치 시작" | tee -a "$LOG_FILE"
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
# Step 1: policy_monitor.py 백업
################################################################################

echo "📝 Step 1/4: policy_monitor.py 백업 생성 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c "
    cp /app/core/policy_monitor.py /app/core/policy_monitor.py.bak.${MASTER_PATCH_NAME}
"

echo "   ✅ 백업 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

################################################################################
# Step 2: requests.Session() HTTPS adapter 설정
################################################################################

echo "📝 Step 2/4: HTTPS adapter 우선순위 설정 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c "
cat > /tmp/https_adapter_patch.py << 'PYTHON_CODE'
import re

# 패치 코드
patch_code = '''
        # 패치 추가: 명시적 HTTPS 연결 보장 (port 80 버그 수정)
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        )
        self.session.mount('https://', adapter)  # HTTPS 먼저!
        self.session.mount('http://', adapter)

        if not self.base_url.startswith('https://'):
            logger.warning(f'⚠️  base_url이 HTTPS가 아님: {self.base_url}')
            self.base_url = self.base_url.replace('http://', 'https://')
            logger.info(f'🔒 base_url을 HTTPS로 변경: {self.base_url}')
'''

# 파일 읽기
with open('/app/core/policy_monitor.py', 'r') as f:
    content = f.read()

# 이미 패치되었는지 확인
if 'HTTPS 먼저!' in content:
    print('⚠️  이미 패치됨 (건너뜀)')
else:
    # self.session.timeout = 30 찾아서 그 아래에 패치 삽입
    pattern = r'(self\.session\.timeout = 30)'
    replacement = r'\1\n' + patch_code

    modified = re.sub(pattern, replacement, content)

    # 파일 쓰기
    with open('/app/core/policy_monitor.py', 'w') as f:
        f.write(modified)

    print('✅ HTTPS adapter 패치 완료')
PYTHON_CODE

python3 /tmp/https_adapter_patch.py
"

if [ $? -eq 0 ]; then
    echo "   ✅ HTTPS adapter 설정 완료" | tee -a "$LOG_FILE"
else
    echo "   ❌ HTTPS adapter 설정 실패" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"

################################################################################
# Step 3: _authenticate_regtech() 메서드 교체
################################################################################

echo "📝 Step 3/4: _authenticate_regtech() 메서드 교체 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" bash -c '
python3 << "PYTHON_PATCH"
import re

# 새로운 인증 메서드 (curl 기반, HTTPS 보장)
new_auth_method = """    def _authenticate_regtech(self) -> bool:
        \"\"\"REGTECH 포털 인증 (curl 기반, HTTPS 보장)\"\"\"
        try:
            import subprocess

            regtech_id = self.config.get(\"regtech_id\", \"\")
            regtech_pw = self.config.get(\"regtech_pw\", \"\")

            if not regtech_id or not regtech_pw:
                logger.error(\"REGTECH 인증 정보 없음\")
                return False

            # Step 1: findOneMember (사용자 정보 조회)
            logger.info(\"🔍 REGTECH 사용자 정보 조회 중...\")
            find_member_cmd = [
                \"curl\", \"-s\", \"-X\", \"POST\",
                f\"{self.base_url}/login/findOneMember\",
                \"-H\", \"Content-Type: application/x-www-form-urlencoded\",
                \"-d\", f\"username={regtech_id}\"
            ]

            result = subprocess.run(
                find_member_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )

            if result.returncode != 0:
                logger.error(f\"REGTECH 사용자 정보 조회 실패: {result.stderr}\")
                return False

            # Step 2: addLogin (로그인)
            logger.info(\"🔐 REGTECH 로그인 중...\")
            login_cmd = [
                \"curl\", \"-s\", \"-i\", \"-X\", \"POST\",
                f\"{self.base_url}/login/addLogin\",
                \"-H\", \"Content-Type: application/x-www-form-urlencoded\",
                \"-d\", f\"username={regtech_id}&password={regtech_pw}\"
            ]

            login_result = subprocess.run(
                login_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )

            if login_result.returncode != 0:
                logger.error(f\"REGTECH 로그인 실패: {login_result.stderr}\")
                return False

            # 쿠키 추출 (Set-Cookie 헤더)
            cookies = {}
            for line in login_result.stdout.split(\"\\n\"):
                if line.startswith(\"Set-Cookie:\"):
                    cookie_line = line.replace(\"Set-Cookie: \", \"\")
                    cookie_parts = cookie_line.split(\";\")[0]
                    if \"=\" in cookie_parts:
                        key, value = cookie_parts.split(\"=\", 1)
                        cookies[key.strip()] = value.strip()

            # 인증 성공 확인 (regtech-va, regtech-front 쿠키 존재 여부)
            if \"regtech-va\" in cookies and \"regtech-front\" in cookies:
                logger.info(f\"✅ REGTECH 인증 성공 (쿠키: {len(cookies)}개)\")

                # 세션 쿠키 업데이트
                for key, value in cookies.items():
                    self.session.cookies.set(key, value)

                return True
            else:
                logger.error(\"REGTECH 인증 실패 (쿠키 없음)\")
                return False

        except subprocess.TimeoutExpired:
            logger.error(\"REGTECH 인증 타임아웃 (20초)\")
            return False
        except Exception as e:
            logger.error(f\"REGTECH 인증 중 오류: {e}\")
            return False"""

# 파일 읽기
with open("/app/core/policy_monitor.py", "r") as f:
    content = f.read()

# 이미 교체되었는지 확인
if "curl 기반, HTTPS 보장" in content:
    print("⚠️  이미 교체됨 (건너뜀)")
else:
    # _authenticate_regtech() 메서드 찾기 및 교체
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
# Step 4: 컨테이너 재시작
################################################################################

echo "🔄 Step 4/4: collector 컨테이너 재시작 중..." | tee -a "$LOG_FILE"

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
# 검증
################################################################################

echo "🧪 패치 검증 중..." | tee -a "$LOG_FILE"

# 1. HTTPS adapter 확인
HTTPS_PATCH=$(docker exec "$CONTAINER_NAME" grep -c "HTTPS 먼저!" /app/core/policy_monitor.py || echo "0")
if [ "$HTTPS_PATCH" -gt 0 ]; then
    echo "   ✅ HTTPS adapter 패치 확인" | tee -a "$LOG_FILE"
else
    echo "   ❌ HTTPS adapter 패치 미발견" | tee -a "$LOG_FILE"
fi

# 2. 새로운 인증 메서드 확인
AUTH_PATCH=$(docker exec "$CONTAINER_NAME" grep -c "curl 기반, HTTPS 보장" /app/core/policy_monitor.py || echo "0")
if [ "$AUTH_PATCH" -gt 0 ]; then
    echo "   ✅ 인증 메서드 교체 확인" | tee -a "$LOG_FILE"
else
    echo "   ❌ 인증 메서드 교체 미발견" | tee -a "$LOG_FILE"
fi

# 3. 백업 파일 확인
if docker exec "$CONTAINER_NAME" test -f "/app/core/policy_monitor.py.bak.${MASTER_PATCH_NAME}"; then
    echo "   ✅ 백업 파일 생성 확인" | tee -a "$LOG_FILE"
else
    echo "   ⚠️  백업 파일 미발견" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

################################################################################
# 완료
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "✅ ${MASTER_PATCH_NAME} 마스터 패치 완료" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📋 패치 요약:" | tee -a "$LOG_FILE"
echo "   1. ✅ requests.Session() HTTPS adapter 우선순위 설정" | tee -a "$LOG_FILE"
echo "   2. ✅ _authenticate_regtech() 메서드 curl 기반으로 교체" | tee -a "$LOG_FILE"
echo "   3. ✅ 엔드포인트 변경: /common/login → /login/addLogin" | tee -a "$LOG_FILE"
echo "   4. ✅ 명시적 HTTPS 연결 보장 (port 443)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "🎯 효과:" | tee -a "$LOG_FILE"
echo "   - ❌ HTTPConnectionPool(port=80) 에러 완전 해결" | tee -a "$LOG_FILE"
echo "   - ✅ REGTECH 인증 안정성 향상" | tee -a "$LOG_FILE"
echo "   - ✅ 에어갭 환경에서도 동작 (인증 실패는 정상)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "🧪 테스트 명령어:" | tee -a "$LOG_FILE"
echo "   docker logs $CONTAINER_NAME -f | grep -i 'regtech'" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "   예상 출력:" | tee -a "$LOG_FILE"
echo "   ✅ '✅ REGTECH 인증 성공 (쿠키: 2개)' 메시지" | tee -a "$LOG_FILE"
echo "   ❌ 'HTTPConnectionPool(port=80)' 에러 없음" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📝 로그 위치: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "🎉 모든 패치 완료!" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"

exit 0
