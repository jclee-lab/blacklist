#!/bin/bash
set -euo pipefail

PATCH_NAME="005-fix-regtech-credentials-from-db"
LOG_FILE="/tmp/${PATCH_NAME}.log"
CONTAINER_NAME="blacklist-collector"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee "$LOG_FILE"
echo "🔧 ${PATCH_NAME} 패치 시작" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 컨테이너 확인
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ ${CONTAINER_NAME} 컨테이너가 실행 중이 아닙니다." | tee -a "$LOG_FILE"
    exit 1
fi

echo "✅ ${CONTAINER_NAME} 컨테이너 확인 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 백업
echo "📝 Step 1/3: 백업 생성 중..." | tee -a "$LOG_FILE"
docker exec "$CONTAINER_NAME" bash -c "cp /app/collector/monitoring_scheduler.py /app/collector/monitoring_scheduler.py.bak.${PATCH_NAME}"
echo "   ✅ 백업 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# monitoring_scheduler.py 수정
echo "📝 Step 2/3: REGTECH credentials를 DB에서 읽도록 수정 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" python3 << 'EOF'
import re

with open('/app/collector/monitoring_scheduler.py', 'r') as f:
    content = f.read()

# Find the _initialize_collectors method and modify REGTECH initialization
old_pattern = r'''            # REGTECH collector \(always available\)
            self\.collectors\['REGTECH'\] = \{
                'instance': REGTECHPolicyMonitor\(self\.config\.to_dict\(\)\),
                'type': 'monitor',
                'last_run': None,
                'next_run': None,
                'run_count': 0,
                'error_count': 0,
                'enabled': True,
                'interval': 86400  # 24 hours \(daily\)
            \}
            logger\.info\("REGTECH collector initialized"\)'''

new_code = '''            # REGTECH collector - load credentials from database
            regtech_creds = self._get_collector_credentials('REGTECH')

            # Build config dictionary with database credentials if available
            regtech_config = self.config.to_dict()
            if regtech_creds and regtech_creds.get('enabled'):
                regtech_config['regtech_id'] = regtech_creds['username']
                regtech_config['regtech_pw'] = regtech_creds['password']
                logger.info("REGTECH credentials loaded from database")
            else:
                logger.warning("REGTECH credentials not found in database, using env vars (if set)")

            self.collectors['REGTECH'] = {
                'instance': REGTECHPolicyMonitor(regtech_config),
                'type': 'monitor',
                'last_run': regtech_creds.get('last_collection') if regtech_creds else None,
                'next_run': None,
                'run_count': 0,
                'error_count': 0,
                'enabled': regtech_creds.get('enabled', True) if regtech_creds else True,
                'interval': regtech_creds.get('collection_interval', 86400) if regtech_creds else 86400
            }
            logger.info("REGTECH collector initialized")'''

modified = re.sub(old_pattern, new_code, content)

if modified == content:
    print("❌ 패치 패턴이 일치하지 않습니다. 이미 패치되었거나 코드가 변경되었습니다.")
    exit(1)

with open('/app/collector/monitoring_scheduler.py', 'w') as f:
    f.write(modified)

print("✅ monitoring_scheduler.py 수정 완료")
EOF

if [ $? -ne 0 ]; then
    echo "   ❌ 패치 실패" | tee -a "$LOG_FILE"
    exit 1
fi

echo "   ✅ monitoring_scheduler.py 수정 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 컨테이너 재시작
echo "🔄 Step 3/3: 컨테이너 재시작 중..." | tee -a "$LOG_FILE"
docker compose restart "$CONTAINER_NAME" > /dev/null 2>&1

# 재시작 대기
for i in {1..30}; do
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        sleep 2
        if docker exec "$CONTAINER_NAME" curl -sf http://localhost:8545/health > /dev/null 2>&1; then
            echo "   ✅ 컨테이너 재시작 완료 (${i}초)" | tee -a "$LOG_FILE"
            break
        fi
    fi

    if [ $i -eq 30 ]; then
        echo "   ⚠️  Health check 실패 (30초 타임아웃)" | tee -a "$LOG_FILE"
    fi

    sleep 1
done

echo "" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "✅ ${PATCH_NAME} 패치 완료" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "📋 패치 요약:" | tee -a "$LOG_FILE"
echo "   ✅ REGTECH가 SECUDIUM처럼 DB에서 credentials 읽도록 수정" | tee -a "$LOG_FILE"
echo "   ✅ Web UI에서 설정한 credentials가 이제 실제로 사용됨" | tee -a "$LOG_FILE"
echo "   ✅ enabled 플래그와 collection_interval도 DB에서 읽음" | tee -a "$LOG_FILE"

exit 0
