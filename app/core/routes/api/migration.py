"""
데이터베이스 마이그레이션 및 정리 라우트
"""

import logging
import os
from flask import Blueprint, jsonify, request, render_template
from ...database.connection import get_db_connection

logger = logging.getLogger(__name__)

migration_bp = Blueprint("migration", __name__, url_prefix="/api/migration")


@migration_bp.route("/cleanup-secudium", methods=["POST"])
def cleanup_secudium_data():
    """SECUDIUM 가짜 데이터 정리"""
    try:
        # 보안을 위한 간단한 확인
        auth_key = request.headers.get("X-Migration-Key")
        expected_key = os.getenv("MIGRATION_KEY", "cleanup-2025-09-03")

        if auth_key != expected_key:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 삭제 전 현재 상태 확인
                cur.execute(
                    "SELECT COUNT(*) as total, string_agg(DISTINCT source, ', ') as sources FROM blacklist_ips"
                )
                before_stats = cur.fetchone()

                logger.info(f"정리 전 상태: {before_stats[0]}개 IP, 소스: {before_stats[1]}")

                # SECUDIUM 관련 데이터 삭제
                cur.execute(
                    """
                    DELETE FROM blacklist_ips
                    WHERE source LIKE '%secudium%'
                       OR source LIKE '%SECUDIUM%'
                       OR source LIKE 'SECUDIUM_%'
                """
                )
                deleted_ips = cur.rowcount

                cur.execute(
                    """
                    DELETE FROM collection_stats
                    WHERE source = 'secudium'
                       OR source = 'SECUDIUM'
                """
                )
                deleted_stats = cur.rowcount

                cur.execute(
                    """
                    DELETE FROM collection_credentials
                    WHERE service_name = 'SECUDIUM'
                       OR service_name = 'secudium'
                """
                )
                deleted_creds = cur.rowcount

                # 정리 후 상태 확인
                cur.execute(
                    "SELECT COUNT(*) as total, string_agg(DISTINCT source, ', ') as sources FROM blacklist_ips"
                )
                after_stats = cur.fetchone()

                conn.commit()

                logger.info(f"정리 완료: {deleted_ips}개 IP 삭제, {after_stats[0]}개 IP 남음")

                return jsonify(
                    {
                        "success": True,
                        "deleted": {
                            "ips": deleted_ips,
                            "stats": deleted_stats,
                            "credentials": deleted_creds,
                        },
                        "before": {
                            "total_ips": before_stats[0],
                            "sources": before_stats[1],
                        },
                        "after": {
                            "total_ips": after_stats[0],
                            "sources": after_stats[1],
                        },
                    }
                )

    except Exception as e:
        logger.error(f"SECUDIUM 데이터 정리 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@migration_bp.route("/regtech-test-collection", methods=["POST"])
def test_regtech_collection():
    """REGTECH 수집 테스트"""
    try:
        from ..services.collection_service import collection_service

        logger.info("🧪 REGTECH 수집 테스트 시작")

        # REGTECH 수집 실행
        result = collection_service.trigger_collection("regtech")

        if result.get("success"):
            logger.info(f"✅ REGTECH 테스트 수집 성공: {result}")
            return jsonify(
                {
                    "success": True,
                    "message": "REGTECH 수집 테스트 완료",
                    "result": result,
                }
            )
        else:
            logger.warning(f"❌ REGTECH 테스트 수집 실패: {result}")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "REGTECH 수집 실패",
                        "error": result.get("error"),
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"REGTECH 테스트 수집 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@migration_bp.route("/reset-all-data", methods=["POST"])
def reset_all_data():
    """전체 수집 데이터 초기화"""
    try:
        # 보안을 위한 간단한 확인
        auth_key = request.headers.get("X-Migration-Key")
        expected_key = os.getenv("MIGRATION_KEY", "cleanup-2025-09-03")

        if auth_key != expected_key:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 삭제 전 현재 상태 확인
                cur.execute(
                    "SELECT COUNT(*) as total, string_agg(DISTINCT source, ', ') as sources FROM blacklist_ips"
                )
                before_stats = cur.fetchone()

                logger.info(
                    f"전체 초기화 전 상태: {before_stats[0]}개 IP, 소스: {before_stats[1]}"
                )

                # 1. 모든 IP 데이터 삭제
                cur.execute("DELETE FROM blacklist_ips")
                deleted_ips = cur.rowcount

                # 2. 모든 수집 통계 삭제
                cur.execute("DELETE FROM collection_stats")
                deleted_stats = cur.rowcount

                # 3. 모든 수집 기록 삭제
                cur.execute("DELETE FROM collection_history")
                deleted_history = cur.rowcount

                # 4. 테이블 최적화
                cur.execute("VACUUM ANALYZE blacklist_ips")
                cur.execute("VACUUM ANALYZE collection_stats")
                cur.execute("VACUUM ANALYZE collection_history")

                # 5. 시퀀스 리셋 (ID가 1부터 다시 시작)
                cur.execute("ALTER SEQUENCE blacklist_ips_id_seq RESTART WITH 1")

                conn.commit()

                logger.info(
                    f"전체 초기화 완료: {deleted_ips}개 IP, {deleted_stats}개 통계, {deleted_history}개 기록 삭제"
                )

                return jsonify(
                    {
                        "success": True,
                        "message": "전체 데이터 초기화 완료",
                        "deleted": {
                            "ips": deleted_ips,
                            "stats": deleted_stats,
                            "history": deleted_history,
                        },
                        "before_count": before_stats[0],
                        "after_count": 0,
                    }
                )

    except Exception as e:
        logger.error(f"전체 데이터 초기화 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@migration_bp.route("/status", methods=["GET"])
def migration_status():
    """현재 데이터 상태 확인"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 전체 통계
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_ips,
                        COUNT(CASE WHEN source = 'regtech' THEN 1 END) as regtech_count,
                        COUNT(CASE WHEN source LIKE '%secudium%' THEN 1 END) as secudium_count,
                        string_agg(DISTINCT source, ', ') as all_sources
                    FROM blacklist_ips
                """
                )
                stats = cur.fetchone()

                return jsonify(
                    {
                        "success": True,
                        "stats": {
                            "total_ips": stats[0],
                            "regtech_count": stats[1],
                            "secudium_count": stats[2],
                            "all_sources": stats[3],
                        },
                        "clean_state": stats[2] == 0,  # SECUDIUM 데이터가 없으면 clean
                    }
                )

    except Exception as e:
        logger.error(f"상태 확인 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@migration_bp.route("/test-page", methods=["GET"])
def collection_test_page():
    """수집 테스트 관리 페이지"""
    return render_template("collection_test.html")
