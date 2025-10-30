"""시스템 관리 API 엔드포인트
통계, 로그, 데이터베이스 관리 API
"""

from . import api_bp
from flask import jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 부모 패키지에서 api_bp 임포트


@api_bp.route("/monitoring/dashboard", methods=["GET"])
def get_monitoring_dashboard():
    """모니터링 대시보드 데이터 API"""
    try:
        import os
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # 직접 DB 연결로 통계 조회
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # 기본 통계
        cursor.execute("SELECT COUNT(*) as total_ips FROM blacklist_ips")
        total_result = cursor.fetchone()
        total_ips = total_result["total_ips"] if total_result else 0

        cursor.execute(
            "SELECT COUNT(*) as active_ips FROM blacklist_ips WHERE is_active = true"
        )
        active_result = cursor.fetchone()
        active_ips = active_result["active_ips"] if active_result else 0

        # 최근 수집 정보
        cursor.execute(
            """
            SELECT service_name, collection_date, items_collected, success
            FROM collection_history
            ORDER BY collection_date DESC
            LIMIT 5
        """
        )
        recent_collections = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(
            {
                "success": True,
                "dashboard": {
                    "total_ips": total_ips,
                    "active_ips": active_ips,
                    "recent_collections": [
                        {
                            "service": row["service_name"],
                            "date": row["collection_date"].isoformat()
                            if row["collection_date"]
                            else None,
                            "items": row["items_collected"],
                            "success": row["success"],
                        }
                        for row in recent_collections
                    ],
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Monitoring dashboard error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/system-stats", methods=["GET"])
def get_system_stats():
    """시스템 통계"""
    try:
        import os
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # 직접 DB 연결로 통계 조회
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # 기본 IP 통계: total, active 구분 (detection_date 컬럼 사용하지 않음)
        cursor.execute("SELECT COUNT(*) as total_ips FROM blacklist_ips")
        total_result = cursor.fetchone()
        total_ips = total_result["total_ips"] if total_result else 0

        # Active IP: is_active = true인 IP (간단한 조건)
        cursor.execute(
            "SELECT COUNT(*) as active_ips FROM blacklist_ips WHERE is_active = true"
        )
        active_result = cursor.fetchone()
        active_ips = active_result["active_ips"] if active_result else 0

        # Expired IP: is_active = false인 IP
        cursor.execute(
            "SELECT COUNT(*) as expired_ips FROM blacklist_ips WHERE is_active = false"
        )
        expired_result = cursor.fetchone()
        expired_ips = expired_result["expired_ips"] if expired_result else 0

        # 소스별 분포
        cursor.execute(
            """
            SELECT source, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM blacklist_ips), 0), 1) as percentage
            FROM blacklist_ips
            WHERE source IS NOT NULL
            GROUP BY source
            ORDER BY count DESC
        """
        )
        source_results = cursor.fetchall()

        source_distribution = {}
        for row in source_results:
            source_distribution[row["source"]] = {
                "count": row["count"],
                "percentage": float(row["percentage"]) if row["percentage"] else 0,
            }

        # 최근 업데이트 시간
        cursor.execute("SELECT MAX(created_at) as last_update FROM blacklist_ips")
        update_result = cursor.fetchone()
        last_update = (
            update_result["last_update"].isoformat()
            if update_result and update_result["last_update"]
            else "데이터 없음"
        )

        cursor.close()
        conn.close()

        stats = {
            "success": True,
            "total_ips": total_ips,
            "active_ips": active_ips,
            "expired_ips": expired_ips,
            "ip_status": {
                "total": total_ips,
                "active": active_ips,  # 활성 IP
                "expired": expired_ips,  # 비활성 IP
                "percentage_active": round(
                    (active_ips / total_ips * 100) if total_ips > 0 else 0, 1
                ),
            },
            "source_distribution": source_distribution,
            "last_update": last_update,
            "monthly_data": [],  # 추후 구현
        }

        return jsonify(stats)

    except Exception as e:
        logger.error(f"System stats error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "total_ips": 0,
                    "active_ips": 0,
                    "expired_ips": 0,
                    "ip_status": {
                        "total": 0,
                        "active": 0,
                        "expired": 0,
                        "percentage_active": 0,
                    },
                    "source_distribution": {},
                    "last_update": "데이터 없음",
                    "error": str(e),
                }
            ),
            500,
        )


@api_bp.route("/chart/data", methods=["GET"])
def get_chart_data():
    """차트용 데이터"""
    try:
        import os
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from datetime import datetime, timedelta

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # 일별 수집 통계 (최근 30일)
        cursor.execute(
            """
            SELECT DATE(timestamp) as date,
                   COALESCE(SUM(items_collected), 0) as collected
            FROM collection_history
            WHERE timestamp >= %s AND success = true
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """,
            (datetime.now() - timedelta(days=30),),
        )

        daily_data = []
        for row in cursor.fetchall():
            daily_data.append(
                {
                    "date": row["date"].isoformat() if row["date"] else "",
                    "collected": row["collected"],
                }
            )

        cursor.close()
        conn.close()

        return jsonify({"success": True, "daily_collection": daily_data})

    except Exception as e:
        logger.error(f"Chart data error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/logs", methods=["GET"])
def get_system_logs():
    """시스템 로그 조회"""
    try:
        import os

        # 로그 파일 읽기 (최근 100줄)
        log_file = "/app/logs/app.log"
        if not os.path.exists(log_file):
            return jsonify({"success": True, "logs": ["로그 파일을 찾을 수 없습니다."]})

        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 최근 100줄만 반환
        recent_logs = lines[-100:] if len(lines) > 100 else lines

        return jsonify(
            {"success": True, "logs": [line.strip() for line in recent_logs]}
        )

    except Exception as e:
        logger.error(f"System logs error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/auth/status", methods=["GET"])
def get_auth_status():
    """인증 상태 확인"""
    try:
        from ...services.regtech_config_service import regtech_config_service

        # REGTECH 자격증명 상태 확인
        credentials = regtech_config_service.get_credentials()
        has_credentials = bool(credentials and credentials.get("regtech_id"))

        return jsonify(
            {
                "success": True,
                "has_regtech_credentials": has_credentials,
                "regtech_configured": has_credentials,
            }
        )

    except Exception as e:
        logger.error(f"Auth status error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/reset-database", methods=["POST"])
def reset_database():
    """데이터베이스 초기화 (긴급 복구용)"""
    try:
        # 보안 헤더 확인
        auth_key = request.headers.get("X-Admin-Key")
        if auth_key != "emergency-reset-2024":
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        from ...services.database_service import db_service

        # 모든 데이터 삭제
        db_service.execute_query("DELETE FROM blacklist_ips")
        db_service.execute_query("DELETE FROM collection_history")
        db_service.execute_query("DELETE FROM collection_stats")

        # 시퀀스 리셋
        db_service.execute_query("ALTER SEQUENCE blacklist_ips_id_seq RESTART WITH 1")

        logger.warning("🚨 데이터베이스 초기화 실행됨 - 모든 데이터 삭제")

        return jsonify(
            {
                "success": True,
                "message": "데이터베이스 초기화 완료",
                "deleted_tables": [
                    "blacklist_ips",
                    "collection_history",
                    "collection_stats",
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Database reset error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/database/schema", methods=["GET"])
def get_database_schema():
    """데이터베이스 스키마 정보"""
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

        # 테이블 정보 조회
        cursor.execute(
            """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        )

        schema_info = {}
        for row in cursor.fetchall():
            table = row["table_name"]
            if table not in schema_info:
                schema_info[table] = []

            schema_info[table].append(
                {
                    "column": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                }
            )

        cursor.close()
        conn.close()

        return jsonify({"success": True, "schema": schema_info})

    except Exception as e:
        logger.error(f"Database schema error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/database/schema/update", methods=["POST"])
def update_database_schema():
    """데이터베이스 스키마 업데이트"""
    try:
        from ...services.database_service import db_service

        # 스키마 업데이트 실행
        result = db_service.update_schema()

        return jsonify({"success": True, "message": "스키마 업데이트 완료", "result": result})

    except Exception as e:
        logger.error(f"Schema update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/database/schema/fix", methods=["POST"])
def fix_schema_force():
    """강제 스키마 수정"""
    try:
        from ...services.database_service import db_service

        # 강제 스키마 수정
        queries = [
            "ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS country VARCHAR(10)",
            "ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS detection_date DATE",
            "ALTER TABLE blacklist_ips ADD COLUMN IF NOT EXISTS removal_date DATE",
        ]

        for query in queries:
            db_service.execute_query(query)

        return jsonify({"success": True, "message": "스키마 강제 수정 완료"})

    except Exception as e:
        logger.error(f"Force schema fix error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
