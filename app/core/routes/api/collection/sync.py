"""
Collection API Sync Operations
Handles synchronization and data refresh
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, g, current_app
from core.exceptions import InternalServerError

logger = logging.getLogger(__name__)

collection_sync_bp = Blueprint("collection_sync", __name__)


@collection_sync_bp.route("/sync/collector", methods=["GET"])
def sync_with_collector():
    """
    Sync with collector service
    """
    try:
        blacklist_service = current_app.extensions["blacklist_service"]

        result = blacklist_service.sync_with_collector()

        return jsonify(
            {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat(),
                "request_id": g.request_id,
            }
        ), 200

    except Exception as e:
        logger.error(f"Collector sync check failed: {e}", exc_info=True)
        raise InternalServerError(
            message="Failed to sync with collector service",
            details={"error_type": type(e).__name__},
        )


@collection_sync_bp.route("/data/refresh", methods=["POST"])
def force_data_refresh():
    """
    Force data refresh
    """
    try:
        collection_service = current_app.extensions["collection_service"]

        result = collection_service.force_refresh()

        return jsonify(
            {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat(),
                "request_id": g.request_id,
            }
        ), 200

    except Exception as e:
        logger.error(f"Force data refresh error: {e}", exc_info=True)
        raise InternalServerError(
            message="Failed to force data refresh",
            details={"error_type": type(e).__name__},
        )
