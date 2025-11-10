"""웹 인터페이스 라우트 - 직접 구현
메인 웹 블루프린트와 모든 라우트를 직접 정의
"""

from flask import Blueprint, jsonify, render_template, request, Response, current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 메인 웹 블루프린트 생성
web_bp = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
def index():
    """메인페이지 - 위협 정보 관리 시스템 대시보드"""
    try:
        # 고급 UI 자동 리다이렉트 (선택사항)
        user_agent = request.headers.get('User-Agent', '').lower()

        # 기본 템플릿 데이터
        template_data = {
            "page_title": "Blacklist Management Platform",
            "service_status": "operational",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat(),
            "ui_fix": True,
        }

        return render_template("index.html", **template_data)

    except Exception as e:
        logger.error(f"Index page rendering failed: {e}")
        # Fallback to basic UI
        try:
            return render_template("index.html", **{
                "page_title": "위협 정보 관리 시스템 (Basic)",
                "service_status": "operational",
                "version": "3.1.2",
                "timestamp": datetime.now().isoformat(),
                "ui_fix": True,
            })
        except:
            return jsonify(
                {
                    "status": "success",
                    "message": "Blacklist Homepage Working!",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                }
            )


# Old code with fallback - now replaced
def _old_template_based_index():
    try:
        # 기본 템플릿 데이터
        template_data = {
            "page_title": "위협 정보 관리 시스템",
            "service_status": "operational",
            "version": "3.1.2",  # UI Fix version
            "timestamp": datetime.now().isoformat(),
            "ui_fix": True,
        }

        return render_template("index.html", **template_data)

    except Exception as e:
        logger.error(f"Index page rendering failed: {e}")
        # Fallback to JSON if template fails
        return jsonify(
            {
                "status": "success",
                "message": "Blacklist Homepage Working!",
                "timestamp": datetime.now().isoformat(),
                "service": "blacklist-app",
                "version": "3.1.1",
                "automation": "enabled",
                "error": f"Template rendering failed: {str(e)}"
            }
        )


@web_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """대시보드 페이지"""
    try:
        # Mock data for dashboard template
        source_distribution = {
            "REGTECH": {"count": 120000, "percentage": 85},
            "Manual": {"count": 15000, "percentage": 10},
            "External": {"count": 7105, "percentage": 5}
        }

        return render_template("monitoring/dashboard.html",
                             page_title="대시보드",
                             timestamp=datetime.now().isoformat(),
                             source_distribution=source_distribution,
                             total_ips=142105,
                             active_ips=138432,
                             recent_additions=5432)
    except Exception as e:
        logger.error(f"Dashboard page rendering failed: {e}")
        return jsonify({"error": "Dashboard template not found", "message": str(e)}), 500


@web_bp.route("/search", methods=["GET"])
def blacklist_search():
    """IP 검색 페이지"""
    try:
        return render_template("blacklist_search.html",
                             page_title="IP 검색",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Search page rendering failed: {e}")
        return jsonify({"error": "Search template not found", "message": str(e)}), 500


@web_bp.route("/data-management", methods=["GET"])
def data_management():
    """데이터 관리 페이지"""
    try:
        return render_template("data_management.html",
                             page_title="데이터 관리",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Data management page rendering failed: {e}")
        return jsonify({"error": "Data management template not found", "message": str(e)}), 500


@web_bp.route("/database-tables", methods=["GET"])
def database_tables():
    """데이터베이스 테이블 현황"""
    try:
        return render_template("database_tables.html",
                             page_title="데이터베이스 테이블",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Database tables page rendering failed: {e}")
        return jsonify({"error": "Database tables template not found", "message": str(e)}), 500


@web_bp.route("/system-logs", methods=["GET"])
def system_logs():
    """시스템 로그 페이지"""
    try:
        return render_template("system_logs.html",
                             page_title="시스템 로그",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"System logs page rendering failed: {e}")
        return jsonify({"error": "System logs template not found", "message": str(e)}), 500


@web_bp.route("/dashboard2", methods=["GET"])
def dashboard_page():
    """대시보드 (Alternative)"""
    try:
        template_data = {
            "page_title": "Blacklist Management Platform",
            "service_status": "operational",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat(),
        }
        return render_template("monitoring/dashboard.html", **template_data)
    except Exception as e:
        logger.error(f"Dashboard rendering failed: {e}")
        return jsonify({
            "error": "Dashboard template not found",
            "message": str(e),
            "fallback": "basic UI available at /"
        }), 500


@web_bp.route("/data-table", methods=["GET"])
def data_table():
    """데이터 테이블"""
    try:
        return render_template("data_table.html",
                             page_title="데이터 테이블",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Data table page rendering failed: {e}")
        return jsonify({"error": "Data table template not found", "message": str(e)}), 500


@web_bp.route("/test-simple", methods=["GET"])
def test_simple():
    """Simple test route with minimal code"""
    return "TEST WORKING"


@web_bp.route("/statistics", methods=["GET"])
def statistics_page():
    """통계 페이지"""
    try:
        return render_template("statistics.html",
                             page_title="통계",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Statistics page rendering failed: {e}")
        # Fallback to JSON response if template not found
        return jsonify({
            "page": "Statistics",
            "message": "Statistics page",
            "timestamp": datetime.now().isoformat()
        }), 200


@web_bp.route("/collection", methods=["GET"])
def collection():
    """데이터 수집 관리 페이지 - REGTECH & SECUDIUM 통합 카드 뷰"""
    from core.services.collection_service import collection_service

    try:
        stats = collection_service.get_collection_stats()
        history = collection_service.get_collection_history()

        return render_template("collection.html",
                             page_title="데이터 수집 관리",
                             timestamp=datetime.now().isoformat(),
                             total_collections=stats.get("total_collections", 0),
                             success_rate=stats.get("success_rate", 0),
                             last_collection_time=stats.get("last_collection_time", "없음"),
                             active_collections=stats.get("active_collections", 0),
                             collection_history=history)
    except Exception as e:
        logger.error(f"Collection page rendering failed: {e}")
        # Fallback with empty data
        return render_template("collection.html",
                             page_title="데이터 수집 관리",
                             timestamp=datetime.now().isoformat(),
                             total_collections=0,
                             success_rate=0,
                             last_collection_time="없음",
                             active_collections=0,
                             collection_history=[])


@web_bp.route("/collection-control", methods=["GET"])
def collection_control():
    """수집 제어 페이지"""
    try:
        return render_template("collection_control.html",
                             page_title="수집 제어",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Collection control page rendering failed: {e}")
        return jsonify({"error": "Collection control template not found", "message": str(e)}), 500


@web_bp.route("/collection-history", methods=["GET"])
def collection_history():
    """수집 내역 페이지"""
    try:
        return render_template("collection_history.html",
                             page_title="수집 내역",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Collection history page rendering failed: {e}")
        return jsonify({"error": "Collection history template not found", "message": str(e)}), 500


@web_bp.route("/regtech-setup", methods=["GET"])
def regtech_setup():
    """REGTECH 설정 페이지"""
    try:
        return render_template("regtech_setup.html",
                             page_title="REGTECH 설정",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"REGTECH setup page rendering failed: {e}")
        return jsonify({"error": "REGTECH setup template not found", "message": str(e)}), 500


@web_bp.route("/connection-status", methods=["GET"])
def connection_status():
    """연결 상태 페이지"""
    try:
        return render_template("connection_status.html",
                             page_title="연결 상태",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Connection status page rendering failed: {e}")
        return jsonify({"error": "Connection status template not found", "message": str(e)}), 500


@web_bp.route("/docker/logs", methods=["GET"])
def docker_logs():
    """Docker 로그 페이지"""
    try:
        return render_template("docker_logs.html",
                             page_title="Docker 로그",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Docker logs page rendering failed: {e}")
        return jsonify({"error": "Docker logs template not found", "message": str(e)}), 500


@web_bp.route("/data", methods=["GET"])
def data_page():
    """데이터 테이블 페이지"""
    try:
        return render_template("data_table.html",
                             page_title="데이터 테이블",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Data table page rendering failed: {e}")
        return jsonify({"error": "Data table template not found", "message": str(e)}), 500


@web_bp.route("/debug/routes", methods=["GET"])
def debug_routes():
    """디버그: 등록된 모든 라우트 확인"""
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append(
            {
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "rule": str(rule),
            }
        )
    return jsonify({"status": "success", "routes": routes, "total_routes": len(routes)})


@web_bp.route("/integrations", methods=["GET"])
def integrations():
    """FortiGate/FortiManager 통합 관리 페이지"""
    try:
        return render_template("integrations.html",
                             page_title="FortiGate/FortiManager 통합",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Integrations page rendering failed: {e}")
        return jsonify({"error": "Integrations template not found", "message": str(e)}), 500


@web_bp.route("/sessions", methods=["GET"])
def sessions():
    """활성 세션 히스토리 관리 페이지"""
    try:
        return render_template("sessions.html",
                             page_title="세션 히스토리",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Sessions page rendering failed: {e}")
        return jsonify({"error": "Sessions template not found", "message": str(e)}), 500


@web_bp.route("/collection-logs", methods=["GET"])
def collection_logs():
    """수집 로그 뷰어 페이지"""
    try:
        return render_template("collection_logs.html",
                             page_title="수집 로그",
                             timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Collection logs page rendering failed: {e}")
        return jsonify({"error": "Collection logs template not found", "message": str(e)}), 500
