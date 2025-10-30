"""
Enhanced Collection API
넓은 범위 수집을 위한 확장된 수집 API
"""

import asyncio
from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time

from collector.core.multi_source_collector import multi_source_collector, SourceType
from collector.config import CollectorConfig

logger = logging.getLogger(__name__)

# 블루프린트 생성
enhanced_api = Blueprint("enhanced_collection", __name__)


@enhanced_api.route("/multi-source/collect", methods=["POST"])
def multi_source_collection():
    """다중 소스 넓은 범위 수집 API"""
    try:
        # 요청 파라미터
        params = request.get_json() or {}

        max_ips_per_source = params.get("max_ips_per_source", 50000)
        parallel_sources = params.get("parallel_sources", 5)
        date_range_days = params.get("date_range_days", 7)
        enabled_sources = params.get("enabled_sources", [])  # 특정 소스만 활성화

        logger.info(
            f"🚀 다중 소스 수집 시작: {max_ips_per_source:,}개/소스, {parallel_sources}개 병렬"
        )

        # 소스 활성화 설정
        if enabled_sources:
            # 모든 소스 비활성화 후 선택된 소스만 활성화
            for source_id, config in multi_source_collector.sources.items():
                config.enabled = any(
                    source_type in source_id for source_type in enabled_sources
                )

        # 비동기 수집 실행 (동기 래퍼)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            collection_result = loop.run_until_complete(
                multi_source_collector.collect_from_all_sources(
                    max_ips_per_source=max_ips_per_source,
                    parallel_sources=parallel_sources,
                    date_range_days=date_range_days,
                )
            )
        finally:
            loop.close()

        # 결과 처리
        if collection_result.get("success"):
            collected_data = collection_result.get("data", [])

            # 데이터베이스 저장 (기존 collector와 통합)
            saved_count = 0
            try:
                from collector.database import CollectorDatabase

                db = CollectorDatabase()

                for item in collected_data:
                    if db.save_blacklist_ip(item):
                        saved_count += 1

                logger.info(f"💾 데이터베이스 저장: {saved_count}/{len(collected_data)}개")

            except Exception as db_error:
                logger.error(f"❌ 데이터베이스 저장 오류: {db_error}")

            # 성공 응답
            return jsonify(
                {
                    "success": True,
                    "message": f"다중 소스 수집 완료: {collection_result['total_collected']:,}개 IP",
                    "total_collected": collection_result["total_collected"],
                    "unique_ips": collection_result["unique_ips"],
                    "sources_successful": collection_result["sources_successful"],
                    "sources_attempted": collection_result["sources_attempted"],
                    "collection_time": collection_result["collection_time_seconds"],
                    "saved_to_db": saved_count,
                    "source_breakdown": collection_result["source_breakdown"],
                    "timestamp": collection_result["timestamp"],
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "다중 소스 수집 실패",
                        "details": collection_result,
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"❌ 다중 소스 수집 API 오류: {e}")
        return jsonify({"success": False, "error": f"수집 중 오류 발생: {str(e)}"}), 500


@enhanced_api.route("/sources/status", methods=["GET"])
def get_sources_status():
    """위협 정보 소스 상태 조회"""
    try:
        status = multi_source_collector.get_source_status()
        return jsonify(
            {"success": True, "data": status, "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        logger.error(f"❌ 소스 상태 조회 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@enhanced_api.route("/sources/configure", methods=["POST"])
def configure_sources():
    """소스 설정 변경"""
    try:
        config_data = request.get_json()

        # 소스 활성화/비활성화
        if "enable_sources" in config_data:
            for source_type in config_data["enable_sources"]:
                multi_source_collector.enable_source(source_type, True)

        if "disable_sources" in config_data:
            for source_type in config_data["disable_sources"]:
                multi_source_collector.enable_source(source_type, False)

        # 사용자 정의 소스 추가
        if "add_custom_source" in config_data:
            custom = config_data["add_custom_source"]
            success = multi_source_collector.add_custom_source(
                name=custom["name"],
                url=custom["url"],
                source_type=SourceType.CUSTOM_API,
                api_key=custom.get("api_key"),
                headers=custom.get("headers"),
                confidence_boost=custom.get("confidence_boost", 0),
            )

            if not success:
                return jsonify({"success": False, "error": "사용자 정의 소스 추가 실패"}), 400

        return jsonify(
            {
                "success": True,
                "message": "소스 설정 변경 완료",
                "new_status": multi_source_collector.get_source_status(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 소스 설정 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@enhanced_api.route("/collection/wide-range", methods=["POST"])
def wide_range_collection():
    """넓은 범위 수집 - 최대 성능 모드"""
    try:
        params = request.get_json() or {}

        # 넓은 범위 수집 설정
        max_total_ips = params.get("max_total_ips", 500000)  # 총 50만개
        aggressive_mode = params.get("aggressive_mode", False)
        date_range_days = params.get("date_range_days", 30)  # 30일 범위

        logger.info(f"🌍 넓은 범위 수집 시작: 최대 {max_total_ips:,}개 IP")

        collection_start = time.time()

        # 1단계: 모든 고우선순위 소스 수집
        high_priority_sources = ["regtech", "threatfox", "feodo", "urlhaus"]

        # 2단계: 중간 우선순위 소스 수집
        medium_priority_sources = ["phishtank", "openphish"]

        total_collected = []
        stage_results = {}

        # 1단계 실행
        logger.info("🎯 1단계: 고우선순위 소스 수집")
        stage1_result = _execute_collection_stage(
            high_priority_sources,
            max_total_ips // 2,  # 절반을 1단계에 할당
            8,  # 병렬 처리
            date_range_days,
        )
        total_collected.extend(stage1_result["data"])
        stage_results["stage1"] = stage1_result

        # 2단계 실행 (남은 할당량이 있는 경우)
        remaining_quota = max_total_ips - len(total_collected)
        if remaining_quota > 0:
            logger.info("🎯 2단계: 중간 우선순위 소스 수집")
            stage2_result = _execute_collection_stage(
                medium_priority_sources, remaining_quota, 4, date_range_days  # 병렬 처리
            )
            total_collected.extend(stage2_result["data"])
            stage_results["stage2"] = stage2_result

        # 중복 제거 및 최종 처리
        final_data = multi_source_collector._deduplicate_and_enhance(total_collected)

        # 데이터베이스 저장
        saved_count = 0
        try:
            from collector.database import CollectorDatabase

            db = CollectorDatabase()

            # 배치 저장 최적화
            batch_size = 1000
            for i in range(0, len(final_data), batch_size):
                batch = final_data[i : i + batch_size]
                for item in batch:
                    if db.save_blacklist_ip(item):
                        saved_count += 1

                if i + batch_size < len(final_data):
                    logger.info(f"💾 배치 저장 진행: {i+batch_size}/{len(final_data)}")

        except Exception as db_error:
            logger.error(f"❌ 데이터베이스 저장 오류: {db_error}")

        collection_time = time.time() - collection_start

        # 지리적 분포 분석
        geo_distribution = _analyze_geographical_distribution(final_data)

        # 위협 카테고리 분포
        category_distribution = _analyze_category_distribution(final_data)

        return jsonify(
            {
                "success": True,
                "message": f"넓은 범위 수집 완료: {len(final_data):,}개 고유 IP",
                "collection_summary": {
                    "total_unique_ips": len(final_data),
                    "total_raw_collected": len(total_collected),
                    "deduplication_rate": round(
                        (1 - len(final_data) / max(len(total_collected), 1)) * 100, 2
                    ),
                    "collection_time_seconds": round(collection_time, 2),
                    "ips_per_second": round(len(final_data) / collection_time, 2)
                    if collection_time > 0
                    else 0,
                    "saved_to_database": saved_count,
                    "save_success_rate": round(saved_count / len(final_data) * 100, 2)
                    if final_data
                    else 0,
                },
                "stage_results": stage_results,
                "geographical_distribution": geo_distribution,
                "category_distribution": category_distribution,
                "data_quality_metrics": {
                    "multi_source_confirmations": len(
                        [ip for ip in final_data if ip.get("multi_source", False)]
                    ),
                    "average_confidence": round(
                        sum(ip.get("confidence_level", 0) for ip in final_data)
                        / len(final_data),
                        2,
                    )
                    if final_data
                    else 0,
                    "active_threats": len(
                        [ip for ip in final_data if ip.get("is_active", True)]
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 넓은 범위 수집 오류: {e}")
        return jsonify({"success": False, "error": f"넓은 범위 수집 실패: {str(e)}"}), 500


def _execute_collection_stage(
    source_types: List[str], max_ips: int, parallel_count: int, date_range_days: int
) -> Dict[str, Any]:
    """수집 단계 실행"""
    try:
        # 선택된 소스만 활성화
        for source_id, config in multi_source_collector.sources.items():
            config.enabled = any(
                source_type in source_id.lower() for source_type in source_types
            )

        # 비동기 수집 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                multi_source_collector.collect_from_all_sources(
                    max_ips_per_source=max_ips // len(source_types)
                    if source_types
                    else max_ips,
                    parallel_sources=parallel_count,
                    date_range_days=date_range_days,
                )
            )
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ 수집 단계 실행 오류: {e}")
        return {"success": False, "error": str(e), "data": []}


def _analyze_geographical_distribution(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """지리적 분포 분석"""
    geo_counts = {}

    for item in data:
        country = item.get("country") or "Unknown"
        geo_counts[country] = geo_counts.get(country, 0) + 1

    # 상위 10개 국가
    sorted_geo = sorted(geo_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return dict(sorted_geo)


def _analyze_category_distribution(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """위협 카테고리 분포 분석"""
    category_counts = {}

    for item in data:
        category = item.get("category", "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1

    return category_counts


@enhanced_api.route("/collection/real-time", methods=["POST"])
def real_time_collection():
    """실시간 수집 모드"""
    try:
        params = request.get_json() or {}

        # 실시간 수집 설정
        duration_minutes = params.get("duration_minutes", 60)  # 1시간
        collection_interval = params.get("interval_seconds", 300)  # 5분마다

        logger.info(f"⏰ 실시간 수집 시작: {duration_minutes}분간, {collection_interval}초 간격")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        real_time_results = []
        total_collected = 0

        # 스케줄링된 수집 (데모용 - 실제로는 백그라운드 태스크 필요)
        current_time = datetime.now()

        if current_time < end_time:
            # 현재 시점 수집 실행
            current_result = _execute_collection_stage(
                ["regtech", "threatfox"],  # 실시간 피드 소스
                10000,  # 실시간 모드는 적은 수량
                3,  # 낮은 병렬성
                1,  # 최근 1일
            )

            if current_result.get("success"):
                batch_collected = len(current_result.get("data", []))
                total_collected += batch_collected

                real_time_results.append(
                    {
                        "timestamp": current_time.isoformat(),
                        "collected_count": batch_collected,
                        "sources": current_result.get("sources_successful", 0),
                    }
                )

        return jsonify(
            {
                "success": True,
                "message": f"실시간 수집 완료: {total_collected:,}개 IP",
                "real_time_summary": {
                    "duration_minutes": duration_minutes,
                    "total_collected": total_collected,
                    "collection_batches": len(real_time_results),
                    "average_per_batch": round(
                        total_collected / max(len(real_time_results), 1), 2
                    ),
                },
                "batch_results": real_time_results,
                "next_collection": (
                    datetime.now() + timedelta(seconds=collection_interval)
                ).isoformat(),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 실시간 수집 오류: {e}")
        return jsonify({"success": False, "error": f"실시간 수집 실패: {str(e)}"}), 500


@enhanced_api.route("/analytics/collection-performance", methods=["GET"])
def collection_performance_analytics():
    """수집 성능 분석"""
    try:
        # 수집 통계
        stats = multi_source_collector.collection_stats

        # 성능 메트릭 계산
        recent_collections = stats.get("collection_history", [])[-10:]  # 최근 10회

        if recent_collections:
            avg_collection_time = sum(
                c.get("collection_time", 0) for c in recent_collections
            ) / len(recent_collections)
            avg_ips_collected = sum(
                c.get("total_collected", 0) for c in recent_collections
            ) / len(recent_collections)
            avg_sources_used = sum(
                c.get("sources_used", 0) for c in recent_collections
            ) / len(recent_collections)
        else:
            avg_collection_time = 0
            avg_ips_collected = 0
            avg_sources_used = 0

        # 소스별 성능
        source_performance = {}
        for source_id, config in multi_source_collector.sources.items():
            if config.enabled:
                source_performance[config.name] = {
                    "priority": config.priority,
                    "rate_limit": config.rate_limit,
                    "confidence_boost": config.confidence_boost,
                    "estimated_daily_capacity": int(
                        86400 / (1.0 / config.rate_limit)
                    ),  # 일일 예상 수집량
                }

        return jsonify(
            {
                "success": True,
                "performance_metrics": {
                    "average_collection_time_seconds": round(avg_collection_time, 2),
                    "average_ips_per_collection": round(avg_ips_collected, 2),
                    "average_sources_per_collection": round(avg_sources_used, 2),
                    "total_lifetime_collected": stats.get("total_collected", 0),
                    "collection_efficiency": round(
                        avg_ips_collected / max(avg_collection_time, 1), 2
                    ),
                },
                "source_performance": source_performance,
                "recent_collections": recent_collections,
                "recommendations": _generate_performance_recommendations(
                    stats, source_performance
                ),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 성능 분석 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _generate_performance_recommendations(
    stats: Dict, source_performance: Dict
) -> List[str]:
    """성능 최적화 권장사항 생성"""
    recommendations = []

    # 수집 이력 분석
    recent_collections = stats.get("collection_history", [])
    if len(recent_collections) >= 3:
        recent_times = [c.get("collection_time", 0) for c in recent_collections[-3:]]
        avg_time = sum(recent_times) / len(recent_times)

        if avg_time > 120:  # 2분 이상
            recommendations.append("수집 시간이 길어지고 있습니다. 병렬 처리 수를 늘리거나 소스별 최대 수집량을 조정하세요.")

        if avg_time < 30:  # 30초 미만
            recommendations.append("수집이 빠르게 완료됩니다. 더 많은 소스를 활성화하거나 수집량을 늘릴 수 있습니다.")

    # 활성 소스 수 분석
    active_sources = len([s for s in source_performance.values()])
    if active_sources < 3:
        recommendations.append("활성화된 소스가 적습니다. 더 넓은 범위의 위협 정보를 위해 추가 소스를 활성화하세요.")
    elif active_sources > 7:
        recommendations.append("많은 소스가 활성화되어 있습니다. 성능을 위해 우선순위가 낮은 소스를 비활성화할 수 있습니다.")

    # 기본 권장사항
    if not recommendations:
        recommendations.append("현재 수집 성능이 양호합니다. 정기적인 모니터링을 통해 성능을 유지하세요.")

    return recommendations
