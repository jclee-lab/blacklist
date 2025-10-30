#!/bin/bash
# 수동 수집 트리거 가이드
# 에어갭 환경에서 REGTECH/SECUDIUM 수집 강제 실행

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 수동 수집 트리거 가이드"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 방법 1: API를 통한 수집 (가장 간단)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "방법 1: API 호출 (권장)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  REGTECH 수집:"
echo "   curl -X POST http://localhost:2542/api/collection/regtech/trigger"
echo ""
echo "2️⃣  SECUDIUM 수집:"
echo "   curl -X POST http://localhost:2542/api/collection/trigger/SECUDIUM"
echo ""
echo "3️⃣  전체 수집:"
echo "   curl -X POST http://localhost:2542/collection-panel/trigger \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"source\": \"all\"}'"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 방법 2: Collector 컨테이너 직접 호출
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "방법 2: Collector 직접 실행"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Collector 컨테이너 내부에서 Python 스크립트 직접 실행:"
echo ""
echo "docker exec blacklist-collector python /app/run_collection.py --source regtech"
echo "docker exec blacklist-collector python /app/run_collection.py --source secudium"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 방법 3: 스케줄러 강제 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "방법 3: 스케줄러 강제 실행 (일일 자동 수집 테스트)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "docker exec blacklist-collector python /app/monitoring_scheduler.py"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 실행 예제 (대화형)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "실행하시겠습니까?"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1) REGTECH 수집 실행"
echo "2) SECUDIUM 수집 실행"
echo "3) 전체 수집 실행"
echo "4) 스케줄러 강제 실행"
echo "5) 수집 상태 확인"
echo "6) 로그 확인"
echo "0) 종료"
echo ""

read -r -p "선택 (0-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 REGTECH 수집 시작..."
        curl -X POST http://localhost:2542/api/collection/regtech/trigger
        echo ""
        ;;
    2)
        echo ""
        echo "🚀 SECUDIUM 수집 시작..."
        curl -X POST http://localhost:2542/api/collection/trigger/SECUDIUM
        echo ""
        ;;
    3)
        echo ""
        echo "🚀 전체 수집 시작..."
        curl -X POST http://localhost:2542/collection-panel/trigger \
          -H "Content-Type: application/json" \
          -d '{"source": "all"}'
        echo ""
        ;;
    4)
        echo ""
        echo "🚀 스케줄러 강제 실행..."
        docker exec blacklist-collector python /app/monitoring_scheduler.py
        ;;
    5)
        echo ""
        echo "📊 수집 상태 확인..."
        curl -s http://localhost:2542/api/collection/status | jq '.'
        echo ""
        ;;
    6)
        echo ""
        echo "📝 Collector 로그 (최근 50줄):"
        docker logs --tail 50 blacklist-collector
        echo ""
        ;;
    0)
        echo "종료합니다."
        exit 0
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 결과 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "결과 확인 방법"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  실시간 로그:"
echo "   docker logs -f blacklist-collector"
echo ""
echo "2️⃣  수집 상태 API:"
echo "   curl http://localhost:2542/api/collection/status"
echo ""
echo "3️⃣  수집 이력:"
echo "   curl http://localhost:2542/api/collection/history"
echo ""
echo "4️⃣  통계:"
echo "   curl http://localhost:2542/api/statistics"
echo ""
echo "5️⃣  데이터베이스 확인:"
echo "   docker exec blacklist-postgres psql -U postgres -d blacklist -c 'SELECT COUNT(*) FROM blacklist_ips;'"
echo ""
