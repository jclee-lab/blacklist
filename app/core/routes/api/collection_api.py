"""수집 관련 API 엔드포인트
데이터 수집 상태, 통계, 동기화 API
"""

from . import api_bp
from flask import jsonify, request
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# 부모 패키지에서 api_bp 임포트


@api_bp.route("/collection/status", methods=["GET"])
def get_collection_status():
    """수집 상태 조회"""
    try:
        from ...services.collection_service import collection_service

        status = collection_service.get_status()
        return jsonify({"success": True, "data": status})

    except Exception as e:
        logger.error(f"Collection status error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/collection/stats", methods=["GET"])
def get_collection_stats():
    """수집 통계"""
    try:
        import os
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # 오늘 수집 통계
        today = datetime.now().date()
        cursor.execute(
            """
            SELECT COALESCE(SUM(items_collected), 0) as today_collected
            FROM collection_history
            WHERE DATE(timestamp) = %s AND success = true
        """,
            (today,),
        )
        today_result = cursor.fetchone()
        today_collected = today_result["today_collected"] if today_result else 0

        # 주간 수집 통계
        week_ago = today - timedelta(days=7)
        cursor.execute(
            """
            SELECT COALESCE(SUM(items_collected), 0) as week_collected
            FROM collection_history
            WHERE DATE(timestamp) >= %s AND success = true
        """,
            (week_ago,),
        )
        week_result = cursor.fetchone()
        week_collected = week_result["week_collected"] if week_result else 0

        # 월간 수집 통계
        month_ago = today - timedelta(days=30)
        cursor.execute(
            """
            SELECT COALESCE(SUM(items_collected), 0) as month_collected
            FROM collection_history
            WHERE DATE(timestamp) >= %s AND success = true
        """,
            (month_ago,),
        )
        month_result = cursor.fetchone()
        month_collected = month_result["month_collected"] if month_result else 0

        # 소스별 수집 통계
        cursor.execute(
            """
            SELECT source_name,
                   COALESCE(SUM(items_collected), 0) as total_collected,
                   COUNT(*) as collection_count,
                   MAX(timestamp) as last_collection
            FROM collection_history
            WHERE success = true AND timestamp >= %s
            GROUP BY source_name
            ORDER BY total_collected DESC
        """,
            (week_ago,),
        )
        source_stats = {}
        for row in cursor.fetchall():
            source_stats[row["source_name"]] = {
                "total_collected": row["total_collected"],
                "collection_count": row["collection_count"],
                "last_collection": (
                    row["last_collection"].isoformat()
                    if row["last_collection"]
                    else None
                ),
            }

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "today_collected": today_collected,
                "week_collected": week_collected,
                "month_collected": month_collected,
                "source_stats": source_stats,
            }
        )

    except Exception as e:
        logger.error(f"Collection stats error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "today_collected": 0,
                    "week_collected": 0,
                    "month_collected": 0,
                    "source_stats": {},
                    "error": str(e),
                }
            ),
            500,
        )


@api_bp.route("/collection/trigger", methods=["POST"])
def trigger_collection():
    """수집 트리거"""
    try:
        from ...services.collection_service import collection_service

        # 요청 데이터 파싱
        data = request.get_json() if request.get_json() else {}
        source = data.get("source", "regtech")

        result = collection_service.trigger_collection(source)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Collection trigger error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/sync/collector", methods=["GET"])
def sync_with_collector():
    """컬렉터와 데이터 동기화 상태 확인"""
    try:
        from ...services.blacklist_service import service

        result = service.sync_with_collector()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Collector sync check failed: {e}")
        return (
            jsonify({"success": False, "error": str(e), "collector_status": "error"}),
            500,
        )


@api_bp.route("/data/refresh", methods=["POST"])
def force_data_refresh():
    """강제 데이터 새로고침"""
    try:
        from ...services.collection_service import collection_service

        result = collection_service.force_refresh()
        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Force data refresh error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/collection/config/update", methods=["POST"])
def update_collection_config():
    """
    Update collection configuration
    Body: {"interval": 7200, "enabled": true, ...} (all optional)
    """
    try:
        from ...services.settings_service import settings_service

        data = request.get_json() or {}

        if not data:
            return jsonify({
                "success": False,
                "error": "No configuration data provided",
                "error_code": "NO_DATA"
            }), 400

        updated_keys = []
        failed_keys = []

        # Update each configuration key
        for key, value in data.items():
            # Prefix keys with 'collection_' for categorization
            setting_key = f"collection_{key}"

            try:
                success = settings_service.set_setting(setting_key, value)
                if success:
                    updated_keys.append(key)
                    logger.info(f"Updated collection config: {key}={value}")
                else:
                    failed_keys.append(key)
                    logger.warning(f"Failed to update collection config: {key}")
            except Exception as e:
                failed_keys.append(key)
                logger.error(f"Error updating collection config {key}: {e}")

        # Return response based on results
        if len(failed_keys) == 0:
            return jsonify({
                "success": True,
                "message": "Collection configuration updated successfully",
                "updated": updated_keys,
                "timestamp": datetime.now().isoformat()
            })
        elif len(updated_keys) > 0:
            # Partial success
            return jsonify({
                "success": False,
                "message": "Collection configuration partially updated",
                "updated": updated_keys,
                "failed": failed_keys,
                "timestamp": datetime.now().isoformat()
            }), 500
        else:
            # Total failure
            return jsonify({
                "success": False,
                "error": "Failed to update collection configuration",
                "failed": failed_keys,
                "timestamp": datetime.now().isoformat()
            }), 500

    except Exception as e:
        logger.error(f"Collection config update error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
