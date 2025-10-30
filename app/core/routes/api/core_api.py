"""핵심 API 엔드포인트
문서화, 헬스체크 등 기본 API
"""

from . import api_bp
from flask import jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 부모 패키지에서 api_bp 임포트


@api_bp.route("/docs", methods=["GET"])
def api_documentation():
    """API 문서"""
    return jsonify(
        {
            "message": "API Documentation",
            "dashboard_url": "/",
            "note": "Visit / or /dashboard for the web interface",
            "api_endpoints": {
                "health": "/health",
                "stats": "/api/stats",
                "blacklist": "/api/blacklist/active",
                "fortigate": "/api/fortigate",
                "collection": "/api/collection/status",
            },
        }
    )


@api_bp.route("/health", methods=["GET"])
def service_status():
    """서비스 상태 조회"""
    try:
        from ...services.blacklist_service import service

        stats = service.get_system_stats()

        return jsonify(
            {
                "success": True,
                "data": {
                    "service_status": "running",
                    "database_connected": True,
                    "cache_available": True,
                    "total_ips": stats.get("total_ips", 0),
                    "active_ips": stats.get("active_ips", 0),
                    "last_updated": datetime.utcnow().isoformat(),
                },
            }
        )
    except Exception as e:
        logger.error(f"Service status error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
