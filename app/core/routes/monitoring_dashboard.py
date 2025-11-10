"""
고도화된 모니터링 대시보드
REGTECH 데이터 수집 진위성 확인 UI 포함
"""

from flask import Blueprint, render_template, jsonify
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

monitoring_dashboard_bp = Blueprint(
    "monitoring_dashboard", __name__, url_prefix="/dashboard"
)

# Template moved to external file: src/templates/dashboard.html


@monitoring_dashboard_bp.route("/")
def monitoring_dashboard():
    """고도화된 대시보드 페이지"""
    from core.services.database_service import db_service
    from core.services.collection_service import collection_service

    try:
        # Get dashboard data
        stats = db_service.get_blacklist_stats()
        collection_stats = collection_service.get_collection_stats()

        template_data = {
            "total_ips": stats.get("total_ips", 0),
            "active_ips": stats.get("active_ips", 0),
            "last_update": stats.get("last_update", "없음"),
            "collection_count": collection_stats.get("total_collections", 0),
            "version": "2.0.0",
        }

        return render_template("dashboard.html", **template_data)

    except Exception as e:
        logger.error(f"Enhanced dashboard data loading failed: {e}")
        return render_template(
            "dashboard.html",
            total_ips=0,
            active_ips=0,
            last_update="없음",
            collection_count=0,
            version="2.0.0",
        )


@monitoring_dashboard_bp.route("/api/dashboard-data")
def dashboard_data_api():
    """대시보드 데이터 API"""
    try:
        from ..services.database_service import db_service

        # 실제 데이터베이스에서 통계 가져오기
        stats = db_service.get_dashboard_stats()

        return jsonify(
            {
                "success": True,
                "total_ips": stats.get("total_count", 0),
                "regtech_count": stats.get("regtech_count", 0),
                "last_collection": stats.get("last_updated", "확인 중..."),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Dashboard data API error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "total_ips": 0,
                    "regtech_count": 0,
                    "last_collection": "오류",
                }
            ),
            500,
        )
