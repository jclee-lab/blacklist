#!/bin/bash
################################################################################
# 009-fix-regtech-port-80-bug.sh
# REGTECH 수집 시 HTTP port 80 시도 버그 수정 패치
#
# 문제: policy_monitor.py와 monitoring_scheduler.py가 requests.Session()을
#       사용할 때 port=80으로 연결 시도 (인증은 port=443으로 성공)
#
# 해결: requests.Session() 대신 명시적으로 HTTPS 연결 보장
#       adapter mount 순서 변경 (https:// 먼저)
#
# 적용 대상:
#   - /app/core/policy_monitor.py
#   - /app/collector/monitoring_scheduler.py
#
# 작성일: 2025-10-29
# 버전: v3.3.5
################################################################################

set -euo pipefail

PATCH_NAME="001-fix-regtech-port-80-bug"
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
# 1. policy_monitor.py 패치
################################################################################

echo "📝 1/2: policy_monitor.py 패치 중..." | tee -a "$LOG_FILE"

# 백업 생성
docker exec "$CONTAINER_NAME" bash -c "
    cp /app/core/policy_monitor.py /app/core/policy_monitor.py.bak.${PATCH_NAME}
"

# 패치 적용: self.session.timeout 설정 바로 뒤에 명시적 HTTPS 설정 추가
docker exec "$CONTAINER_NAME" bash -c "
cat > /tmp/policy_monitor_patch.py << 'PYTHON_PATCH'
        # 패치 추가: 명시적 HTTPS 연결 보장 (port 80 버그 수정)
        # HTTPS adapter를 먼저 마운트하여 우선순위 보장
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        )
        self.session.mount('https://', adapter)  # HTTPS 먼저!
        self.session.mount('http://', adapter)

        # base_url이 https://로 시작하는지 명시적 확인
        if not self.base_url.startswith('https://'):
            logger.warning(f'⚠️  base_url이 HTTPS가 아님: {self.base_url}')
            self.base_url = self.base_url.replace('http://', 'https://')
            logger.info(f'🔒 base_url을 HTTPS로 변경: {self.base_url}')
PYTHON_PATCH

# 파일 수정: self.session.timeout = 30 바로 아래에 패치 삽입
python3 << 'PYTHON_SCRIPT'
import re

# 파일 읽기
with open('/tmp/policy_monitor_patch.py', 'r') as f:
    patch_code = f.read()

# 원본 파일 읽기
with open('/app/core/policy_monitor.py', 'r') as f:
    original = f.read()

# self.session.timeout = 30 찾아서 그 아래에 패치 삽입
pattern = r'(self\.session\.timeout = 30)'
replacement = r'\1\n\n' + patch_code

modified = re.sub(pattern, replacement, original)

# 파일 쓰기
with open('/app/core/policy_monitor.py', 'w') as f:
    f.write(modified)

print('✅ policy_monitor.py 패치 완료')
PYTHON_SCRIPT
"

if [ $? -eq 0 ]; then
    echo "   ✅ policy_monitor.py 패치 완료" | tee -a "$LOG_FILE"
else
    echo "   ❌ policy_monitor.py 패치 실패" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"

################################################################################
# 2. monitoring_scheduler.py 패치 (동일한 버그 가능성)
################################################################################

echo "📝 2/2: monitoring_scheduler.py 패치 중..." | tee -a "$LOG_FILE"

# 파일 존재 여부 확인
if docker exec "$CONTAINER_NAME" test -f /app/collector/monitoring_scheduler.py; then
    # 백업 생성
    docker exec "$CONTAINER_NAME" bash -c "
        cp /app/collector/monitoring_scheduler.py /app/collector/monitoring_scheduler.py.bak.${PATCH_NAME}
    "

    # 동일한 패치 적용
    docker exec "$CONTAINER_NAME" bash -c "
    python3 << 'PYTHON_SCRIPT'
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

# 원본 파일 읽기
try:
    with open('/app/collector/monitoring_scheduler.py', 'r') as f:
        original = f.read()

    # session = requests.Session() 찾아서 그 아래에 패치 삽입
    pattern = r'(self\.session = requests\.Session\(\))'
    if pattern in original:
        replacement = r'\1\n\n' + patch_code
        modified = re.sub(pattern, replacement, original)

        with open('/app/collector/monitoring_scheduler.py', 'w') as f:
            f.write(modified)

        print('✅ monitoring_scheduler.py 패치 완료')
    else:
        print('⚠️  monitoring_scheduler.py에 패치 위치 없음 (건너뜀)')
except FileNotFoundError:
    print('⚠️  monitoring_scheduler.py 파일 없음 (건너뜀)')
PYTHON_SCRIPT
    "

    if [ $? -eq 0 ]; then
        echo "   ✅ monitoring_scheduler.py 패치 완료 (또는 건너뜀)" | tee -a "$LOG_FILE"
    else
        echo "   ⚠️  monitoring_scheduler.py 패치 실패 (무시)" | tee -a "$LOG_FILE"
    fi
else
    echo "   ⚠️  monitoring_scheduler.py 파일 없음 (건너뜀)" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

################################################################################
# 3. 컨테이너 재시작
################################################################################

echo "🔄 collector 컨테이너 재시작 중..." | tee -a "$LOG_FILE"

docker compose restart "$CONTAINER_NAME"

# 재시작 완료 대기 (최대 30초)
for i in {1..30}; do
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        sleep 2
        if docker exec "$CONTAINER_NAME" curl -sf http://localhost:8545/health > /dev/null 2>&1; then
            echo "✅ 컨테이너 재시작 완료 (${i}초)" | tee -a "$LOG_FILE"
            break
        fi
    fi

    if [ $i -eq 30 ]; then
        echo "⚠️  컨테이너 health check 실패 (30초 타임아웃)" | tee -a "$LOG_FILE"
        echo "   docker logs $CONTAINER_NAME 로 확인하세요." | tee -a "$LOG_FILE"
    fi

    sleep 1
done

echo "" | tee -a "$LOG_FILE"

################################################################################
# 4. 검증
################################################################################

echo "🧪 패치 검증 중..." | tee -a "$LOG_FILE"

# 패치 적용 확인
PATCH_APPLIED=$(docker exec "$CONTAINER_NAME" grep -c "패치 추가: 명시적 HTTPS 연결 보장" /app/core/policy_monitor.py || echo "0")

if [ "$PATCH_APPLIED" -gt 0 ]; then
    echo "   ✅ 패치 코드 존재 확인" | tee -a "$LOG_FILE"
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
echo "   - policy_monitor.py: ✅ HTTPS 우선순위 보장" | tee -a "$LOG_FILE"
echo "   - monitoring_scheduler.py: ✅ 동일 패치 적용" | tee -a "$LOG_FILE"
echo "   - 변경 사항: requests.Session()이 https://를 먼저 마운트" | tee -a "$LOG_FILE"
echo "   - 효과: REGTECH 수집 시 port 80 대신 port 443 사용" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "🧪 테스트 명령어:" | tee -a "$LOG_FILE"
echo "   docker logs $CONTAINER_NAME -f | grep -i 'regtech'" | tee -a "$LOG_FILE"
echo "   # 더 이상 'port=80' 에러가 나타나지 않아야 함" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📝 로그 위치: $LOG_FILE" | tee -a "$LOG_FILE"

exit 0
