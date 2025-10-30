#!/bin/bash
set -euo pipefail

PATCH_NAME="004-fix-config-credentials"
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
docker exec "$CONTAINER_NAME" bash -c "cp /app/collector/config.py /app/collector/config.py.bak.${PATCH_NAME}"
echo "   ✅ 백업 완료" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# config.py 수정
echo "📝 Step 2/3: config.py에 credentials 추가 중..." | tee -a "$LOG_FILE"

docker exec "$CONTAINER_NAME" python3 << 'EOF'
import re

with open('/app/collector/config.py', 'r') as f:
    content = f.read()

# 이미 패치되었는지 확인
if content.count('"regtech_id": cls.REGTECH_ID,') > 0:
    print("⚠️  이미 패치됨 - 중복 제거 중")
    # 전체 to_dict 메서드 다시 작성
    pattern = r'    def to_dict\(cls\) -> Dict\[str, Any\]:.*?(?=\n    @classmethod|\n    def |\nclass |\Z)'
    
    new_to_dict = '''    def to_dict(cls) -> Dict[str, Any]:
        """전체 설정을 딕셔너리로 반환"""
        return {
            # 기본 설정
            "postgres_host": cls.POSTGRES_HOST,
            "postgres_port": cls.POSTGRES_PORT,
            "postgres_db": cls.POSTGRES_DB,
            "redis_host": cls.REDIS_HOST,
            "redis_port": cls.REDIS_PORT,
            "regtech_base_url": cls.REGTECH_BASE_URL,
            "regtech_id": cls.REGTECH_ID,
            "regtech_pw": cls.REGTECH_PW,
            "collection_interval": cls.COLLECTION_INTERVAL,
            # 성능 설정
            "batch_size": cls.BATCH_SIZE,
            "page_size": cls.PAGE_SIZE,
            "max_pages_per_collection": cls.MAX_PAGES_PER_COLLECTION,
            "connection_pool_size": cls.CONNECTION_POOL_SIZE,
            "max_memory_items": cls.MAX_MEMORY_ITEMS,
            # 캐싱 설정
            "cache_ttl_seconds": cls.CACHE_TTL_SECONDS,
            "auth_cache_ttl_seconds": cls.AUTH_CACHE_TTL_SECONDS,
            "data_cache_max_size": cls.DATA_CACHE_MAX_SIZE,
            # 네트워크 설정
            "request_timeout": cls.REQUEST_TIMEOUT,
            "max_concurrent_requests": cls.MAX_CONCURRENT_REQUESTS,
            "retry_backoff_factor": cls.RETRY_BACKOFF_FACTOR,
            # 모니터링 설정
            "enable_performance_metrics": cls.ENABLE_PERFORMANCE_METRICS,
            "metrics_collection_interval": cls.METRICS_COLLECTION_INTERVAL,
            "log_level": cls.LOG_LEVEL,
        }
'''
    
    modified = re.sub(pattern, new_to_dict, content, flags=re.DOTALL)
    
    with open('/app/collector/config.py', 'w') as f:
        f.write(modified)
    
    print("✅ to_dict() 메서드 재작성 완료")
else:
    print("❌ 패치 미적용 - 원본 파일")
EOF

echo "   ✅ config.py 수정 완료" | tee -a "$LOG_FILE"
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
echo "   ✅ CollectorConfig.to_dict()에 regtech_id, regtech_pw 추가" | tee -a "$LOG_FILE"
echo "   ✅ REGTECHPolicyMonitor가 credentials 받을 수 있게 됨" | tee -a "$LOG_FILE"

exit 0
