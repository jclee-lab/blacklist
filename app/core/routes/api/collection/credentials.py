"""
Collection API Credentials Operations
Handles credential management
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, g, current_app
from core.exceptions import (
    ValidationError,
    BadRequestError,
    NotFoundError,
    DatabaseError,
)
from .utils import (
    call_collector_api,
    interval_seconds_to_string,
    interval_string_to_seconds,
)

logger = logging.getLogger(__name__)

collection_credentials_bp = Blueprint("collection_credentials", __name__)


@collection_credentials_bp.route("/credentials", methods=["GET"])
def list_credentials():
    """List all available credential sources"""
    secure_credential_service = current_app.extensions.get("secure_credential_service")
    if not secure_credential_service:
        from core.services.secure_credential_service import secure_credential_service

    sources = ["REGTECH"]
    result = []

    for source in sources:
        try:
            creds = secure_credential_service.get_credentials(source)
            result.append({
                "source": source,
                "configured": creds is not None,
                "enabled": creds.get("enabled", False) if creds else False,
            })
        except Exception:
            result.append({"source": source, "configured": False, "enabled": False})

    return jsonify({
        "success": True,
        "data": result,
        "timestamp": datetime.now().isoformat(),
        "request_id": g.request_id,
    })


@collection_credentials_bp.route("/credentials/<source>", methods=["GET", "PUT"])
def manage_credentials(source: str):
    """
    Get or update collection credentials
    """
    source_upper = source.upper()

    # Validate source parameter - only REGTECH is supported
    if source_upper != "REGTECH":
        raise ValidationError(
            message=f"Invalid source: {source}. Must be 'regtech'",
            field="source",
            details={
                "provided_value": source,
                "allowed_values": ["regtech"],
            },
        )

    # Use secure_credential_service for all operations (via dependency injection)
    secure_credential_service = current_app.extensions.get("secure_credential_service")

    # Fallback to direct import if not in extensions (should be there)
    if not secure_credential_service:
        from core.services.secure_credential_service import secure_credential_service

    try:
        if request.method == "GET":
            # Get credentials via secure service
            credentials = secure_credential_service.get_credentials(source_upper)

            if not credentials:
                raise NotFoundError(
                    message=f"Credentials not found for {source_upper}",
                    resource="collection_credentials",
                    details={"source": source_upper},
                )

            return jsonify(
                {
                    "success": True,
                    "data": {
                        "service_name": credentials["service_name"],
                        "username": credentials["username"],
                        "password": "***masked***",
                        "enabled": credentials.get("enabled", True),
                        "collection_interval": interval_seconds_to_string(
                            credentials.get("collection_interval", 86400)
                        ),
                        "last_collection": credentials["last_collection"].isoformat()
                        if credentials.get("last_collection")
                        else None,
                    },
                    "timestamp": datetime.now().isoformat(),
                    "request_id": g.request_id,
                }
            )

        elif request.method == "PUT":
            # Update credentials
            data = request.get_json()
            if not data:
                raise BadRequestError(
                    message="Missing request body",
                    details={"field": "body"},
                )

            # Validate required fields
            username = data.get("username")
            password = data.get("password")
            enabled = data.get("enabled", True)
            collection_interval = data.get("collection_interval", "daily")

            if not username:
                raise BadRequestError(
                    message="Username is required",
                    details={"field": "username"},
                )

            # Convert interval to seconds
            interval_seconds = interval_string_to_seconds(collection_interval)

            # Determine if we have a new password provided
            has_new_password = password and password != "***masked***"

            if has_new_password:
                success = secure_credential_service.save_credentials(
                    service_name=source_upper,
                    username=username,
                    password=password,
                    config={},
                    enabled=enabled,
                    collection_interval=interval_seconds,
                )

                if not success:
                    raise DatabaseError(
                        message=f"Failed to save credentials securely for {source_upper}",
                    )
            else:
                current_creds = secure_credential_service.get_credentials(source_upper)
                if not current_creds:
                    raise NotFoundError(
                        message=f"Credentials not found for {source_upper}. Please provide a password to create new credentials.",
                        resource="collection_credentials",
                        details={"source": source_upper},
                    )

                success = secure_credential_service.update_credential_settings(
                    service_name=source_upper,
                    username=username,
                    enabled=enabled,
                    collection_interval=interval_seconds,
                )

                if not success:
                    raise DatabaseError(
                        message=f"Failed to update credential settings for {source_upper}",
                    )

            logger.info(f"✅ Updated credentials for {source_upper}")

            # Restart scheduler to pick up new credentials
            restart_result = call_collector_api("/api/scheduler/restart", method="POST")

            return jsonify(
                {
                    "success": True,
                    "data": {
                        "message": f"Credentials updated for {source_upper}",
                        "scheduler_restart": restart_result.get("success", False),
                    },
                    "timestamp": datetime.now().isoformat(),
                    "request_id": g.request_id,
                }
            )

        else:
            return jsonify({"success": False, "error": "Method not allowed"}), 405

    except (NotFoundError, ValidationError, BadRequestError):
        # Re-raise known exceptions to be handled by error handlers
        raise
    except Exception as e:
        logger.error(f"Error managing credentials: {e}", exc_info=True)
        raise DatabaseError(
            message=f"Failed to manage credentials for {source_upper}: {type(e).__name__}",
        )


@collection_credentials_bp.route("/credentials/<source>/test", methods=["POST"])
def test_credentials(source: str):
    """
    Test credentials for a specific source
    """
    from core.exceptions import ForbiddenError, ServiceUnavailableError

    source_upper = source.upper()

    # Validate source parameter - only REGTECH is supported
    if source_upper != "REGTECH":
        raise ValidationError(
            message=f"Invalid source: {source}. Must be 'regtech'",
            field="source",
            details={
                "provided_value": source,
                "allowed_values": ["regtech"],
            },
        )

    # Call collector service to test authentication
    result = call_collector_api(f"/api/test-auth/{source_upper}", method="POST")

    # Check if API call failed (connection error)
    if result.get("success") is False and "Cannot connect" in result.get("error", ""):
        raise ServiceUnavailableError(
            service="Collector", details={"source": source_upper}
        )

    # Success - authentication successful
    if result.get("success"):
        return jsonify(
            {
                "success": True,
                "data": {"status": "connected", "message": "인증 성공"},
                "timestamp": datetime.now().isoformat(),
                "request_id": g.request_id,
            }
        ), 200

    # Authentication failed - check if account is locked
    error_msg = result.get("error", "").lower()
    error_code = result.get("error_code", "")

    if (
        "잠긴" in str(error_msg)
        or "locked" in str(error_msg)
        or error_code == "user.is.locked"
    ):
        # Account locked - return 403 Forbidden
        raise ForbiddenError(
            message="계정이 잠겼습니다",
            details={"source": source_upper, "error_code": error_code},
        )
    else:
        # Authentication failed - return as successful test result with failure status
        error_detail = result.get("error", "알 수 없는 오류")
        return jsonify(
            {
                "success": True,  # Test completed successfully (auth failed as expected)
                "data": {
                    "status": "failed",
                    "message": f"{source_upper} 인증 실패"
                    if error_detail == "인증 실패"
                    else f"인증 실패: {error_detail}",
                    "error_code": error_code,
                },
                "timestamp": datetime.now().isoformat(),
                "request_id": g.request_id,
            }
        ), 200
