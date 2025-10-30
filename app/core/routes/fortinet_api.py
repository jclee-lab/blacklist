"""
FortiGate/FortiManager Integration API
Provides active IP lists and blocklists for FortiGate firewalls
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

fortinet_api_bp = Blueprint("fortinet_api", __name__, url_prefix="/api/fortinet")


@fortinet_api_bp.route("/active-ips", methods=["GET"])
def get_active_ips():
    """
    Get active blacklist IPs for FortiGate integration

    Query Parameters:
        limit (int): Number of IPs to return (default: 20, max: 1000)
        page (int): Page number for pagination (default: 1)

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "ip_address": "1.2.3.4",
                    "country": "CN",
                    "reason": "Malicious activity",
                    "confidence_level": 95,
                    "detection_date": "2025-10-20T...",
                    "removal_date": "2025-10-27T...",
                    "is_active": true
                },
                ...
            ],
            "total": 1234,
            "page": 1,
            "limit": 20
        }
    """
    try:
        from core.services.database_service import db_service

        # Get pagination parameters
        limit = min(int(request.args.get("limit", 20)), 1000)
        page = max(int(request.args.get("page", 1)), 1)
        offset = (page - 1) * limit

        # Query active blacklist IPs (excluding whitelisted)
        query = """
            SELECT
                b.id,
                b.ip_address,
                b.country,
                b.reason,
                b.confidence_level,
                b.detection_date,
                b.removal_date,
                b.is_active
            FROM blacklist_ips b
            WHERE b.is_active = true
              AND b.ip_address NOT IN (
                  SELECT ip_address
                  FROM whitelist_ips
                  WHERE is_active = true
              )
            ORDER BY b.confidence_level DESC, b.detection_date DESC
            LIMIT %s OFFSET %s
        """

        rows = db_service.query(query, (limit, offset))

        # Format results
        active_ips = []
        for row in rows:
            active_ips.append({
                "id": row["id"],
                "ip_address": row["ip_address"],
                "country": row["country"],
                "reason": row["reason"],
                "confidence_level": row["confidence_level"],
                "detection_date": row["detection_date"].isoformat() if row["detection_date"] else None,
                "removal_date": row["removal_date"].isoformat() if row["removal_date"] else None,
                "is_active": row["is_active"]
            })

        # Get total count
        count_query = """
            SELECT COUNT(*) as count
            FROM blacklist_ips b
            WHERE b.is_active = true
              AND b.ip_address NOT IN (
                  SELECT ip_address
                  FROM whitelist_ips
                  WHERE is_active = true
              )
        """
        total = db_service.query(count_query)[0]["count"]

        return jsonify({
            "success": True,
            "data": active_ips,
            "total": total,
            "page": page,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting active IPs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "total": 0
        }), 500


@fortinet_api_bp.route("/blocklist", methods=["GET"])
def get_blocklist():
    """
    Get FortiManager/FortiGate External Resource compatible blocklist

    Returns pure text/plain format (NOT JSON):
        1.2.3.4
        5.6.7.8
        9.10.11.12
        ...

    Compatible with:
    - FortiManager External Resource Connector (URL import)
    - FortiGate External Block List (EBL)
    - Threat Feed integration

    Query Parameters:
        format (str): "text" (default) or "json" (legacy)
    """
    try:
        from core.services.database_service import db_service
        from flask import Response

        # Get format parameter (default: text)
        output_format = request.args.get("format", "text")

        # Query active blacklist IPs (excluding whitelisted)
        query = """
            SELECT ip_address
            FROM blacklist_ips
            WHERE is_active = true
              AND ip_address NOT IN (
                  SELECT ip_address
                  FROM whitelist_ips
                  WHERE is_active = true
              )
            ORDER BY ip_address
        """

        rows = db_service.query(query)

        # Format as plain text IP list (FortiGate External Block List format)
        ip_list = [row["ip_address"] for row in rows]

        # Legacy JSON format (backward compatibility)
        if output_format == "json":
            blocklist_text = "\n".join(ip_list)
            return jsonify({
                "success": True,
                "blocklist": blocklist_text,
                "total": len(ip_list),
                "generated_at": datetime.now().isoformat()
            })

        # FortiManager/FortiGate compatible text/plain format (DEFAULT)
        blocklist_text = "\n".join(ip_list)

        return Response(
            blocklist_text,
            mimetype="text/plain",
            headers={
                "Content-Disposition": "inline; filename=blocklist.txt",
                "X-Total-IPs": str(len(ip_list)),
                "X-Generated-At": datetime.now().isoformat(),
                "X-Whitelist-Excluded": "true",
                "Cache-Control": "no-cache, must-revalidate"
            }
        )

    except Exception as e:
        logger.error(f"Error generating blocklist: {e}")
        return Response(
            f"# Error: {str(e)}\n",
            mimetype="text/plain",
            status=500
        )


@fortinet_api_bp.route("/active-sessions", methods=["GET"])
def get_active_sessions():
    """
    Get active threat sessions for monitoring

    Query Parameters:
        limit (int): Number of sessions to return (default: 50)
        hours (int): Time window in hours (default: 24)

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "ip_address": "1.2.3.4",
                    "country": "CN",
                    "session_status": "active",
                    "active_hours": 2.5,
                    "confidence_level": 95,
                    "detection_date": "2025-10-20T...",
                    "reason": "Port scanning"
                },
                ...
            ],
            "stats": {
                "total_sessions": 150,
                "active_count": 45,
                "last_hour": 12,
                "last_24h": 45,
                "unique_countries": 23
            }
        }
    """
    try:
        from core.services.database_service import db_service

        # Get parameters
        limit = min(int(request.args.get("limit", 50)), 500)
        hours = int(request.args.get("hours", 24))

        # Query recent active IPs (last N hours)
        query = """
            SELECT
                id,
                ip_address,
                country,
                reason,
                confidence_level,
                detection_date,
                removal_date,
                is_active,
                created_at,
                updated_at,
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - detection_date)) / 3600 as active_hours
            FROM blacklist_ips
            WHERE detection_date >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
            ORDER BY detection_date DESC
            LIMIT %s
        """

        rows = db_service.query(query, (hours, limit))

        # Format sessions
        sessions = []
        for row in rows:
            # Determine session status
            if row["is_active"]:
                session_status = "active"
            elif row["removal_date"] and row["removal_date"] <= datetime.now().date():
                session_status = "expired"
            else:
                session_status = "inactive"

            sessions.append({
                "id": row["id"],
                "ip_address": row["ip_address"],
                "country": row["country"],
                "reason": row["reason"],
                "confidence_level": row["confidence_level"],
                "detection_date": row["detection_date"].isoformat() if row["detection_date"] else None,
                "removal_date": row["removal_date"].isoformat() if row["removal_date"] else None,
                "is_active": row["is_active"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "active_hours": round(float(row["active_hours"]), 1) if row["active_hours"] else 0,
                "session_status": session_status
            })

        # Get statistics
        stats_query = """
            SELECT
                COUNT(*) as total_sessions,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                COUNT(CASE WHEN detection_date >= CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 1 END) as last_hour,
                COUNT(CASE WHEN detection_date >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h,
                COUNT(DISTINCT country) as unique_countries
            FROM blacklist_ips
            WHERE detection_date >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
        """

        stats_row = db_service.query(stats_query, (hours,))[0]

        stats = {
            "total_sessions": stats_row["total_sessions"],
            "active_count": stats_row["active_count"],
            "last_hour": stats_row["last_hour"],
            "last_24h": stats_row["last_24h"],
            "unique_countries": stats_row["unique_countries"]
        }

        return jsonify({
            "success": True,
            "data": sessions,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "stats": {
                "total_sessions": 0,
                "active_count": 0,
                "last_hour": 0,
                "last_24h": 0,
                "unique_countries": 0
            }
        }), 500


@fortinet_api_bp.route("/config", methods=["GET"])
def get_config():
    """
    Get FortiGate configuration information

    Returns:
        {
            "success": true,
            "config": {
                "external_blocklist_url": "https://blacklist.example.com/api/fortinet/blocklist",
                "update_interval": "hourly",
                "enabled": true
            }
        }
    """
    try:
        # This is a placeholder for FortiGate configuration
        # In production, this would pull from database or config file
        config = {
            "external_blocklist_url": request.url_root.rstrip('/') + "/api/fortinet/blocklist",
            "update_interval": "hourly",
            "enabled": True,
            "api_version": "1.0",
            "last_updated": datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "config": config
        })

    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@fortinet_api_bp.route("/threat-feed", methods=["GET"])
def get_threat_feed():
    """
    FortiGate Push API - Threat Feed Format (JSON)

    Official FortiGate REST API format for dynamic threat feed updates.
    Compatible with FortiGate 7.2+ Push API method.

    Query Parameters:
        command (str): Action type - "snapshot" (default), "add", "remove"
        format (str): Output format - "json" (default), "text"

    Returns (JSON format):
        {
            "commands": [
                {
                    "name": "ip",
                    "command": "snapshot",
                    "entries": [
                        "1.2.3.4",
                        "5.6.7.8",
                        ...
                    ]
                }
            ]
        }

    Returns (text format):
        1.2.3.4
        5.6.7.8
        ...

    Official FortiGate Threat Feed JSON Specification:
    - name: Resource name ("ip" for IP addresses, "fqdn" for domains)
    - command: "snapshot" (replace all), "add" (append), "remove" (delete)
    - entries: Array of IP addresses/domains as strings
    """
    try:
        from core.services.database_service import db_service

        # Get parameters
        command = request.args.get("command", "snapshot")  # snapshot, add, remove
        output_format = request.args.get("format", "json")  # json, text

        # Validate command
        if command not in ["snapshot", "add", "remove"]:
            return jsonify({
                "error": "Invalid command. Must be 'snapshot', 'add', or 'remove'"
            }), 400

        # Query active blacklist IPs (excluding whitelisted)
        query = """
            SELECT ip_address
            FROM blacklist_ips
            WHERE is_active = true
              AND ip_address NOT IN (
                  SELECT ip_address
                  FROM whitelist_ips
                  WHERE is_active = true
              )
            ORDER BY ip_address
        """

        rows = db_service.query(query)
        ip_list = [row["ip_address"] for row in rows]

        # Return plain text format (backward compatible)
        if output_format == "text":
            blocklist_text = "\n".join(ip_list)
            from flask import Response
            return Response(
                blocklist_text,
                mimetype="text/plain",
                headers={
                    "X-Total-IPs": str(len(ip_list)),
                    "X-Generated-At": datetime.now().isoformat()
                }
            )

        # Return FortiGate Push API JSON format
        threat_feed_json = {
            "commands": [
                {
                    "name": "ip",
                    "command": command,
                    "entries": ip_list
                }
            ]
        }

        return jsonify(threat_feed_json), 200, {
            "X-Total-IPs": str(len(ip_list)),
            "X-Generated-At": datetime.now().isoformat(),
            "Content-Type": "application/json"
        }

    except Exception as e:
        logger.error(f"Error generating threat feed: {e}")
        return jsonify({
            "error": str(e),
            "commands": []
        }), 500


@fortinet_api_bp.route("/json-connector", methods=["GET"])
def get_json_connector():
    """
    FortiGate JSON Connector Format (with metadata)

    Provides enriched threat intelligence with country, risk level, and reason.
    Use this for FortiGate External Connectors that support JSON format.

    Query Parameters:
        limit (int): Number of IPs to return (default: all)
        risk_level (str): Filter by risk level - "high", "medium", "low"
        country (str): Filter by country code (e.g., "CN", "RU")

    Returns:
        {
            "results": [
                {
                    "ip": "1.2.3.4",
                    "country": "CN",
                    "risk_level": "high",
                    "reason": "malicious_activity",
                    "confidence": 95,
                    "first_seen": "2025-10-20T10:00:00Z",
                    "last_updated": "2025-10-29T15:30:00Z"
                },
                ...
            ],
            "metadata": {
                "total": 1234,
                "filtered": 100,
                "generated_at": "2025-10-29T16:00:00Z",
                "version": "1.0"
            }
        }
    """
    try:
        from core.services.database_service import db_service

        # Get parameters
        limit = request.args.get("limit", type=int)
        risk_level = request.args.get("risk_level", "").lower()
        country_filter = request.args.get("country", "").upper()

        # Build query
        query = """
            SELECT
                b.ip_address,
                b.country,
                b.reason,
                b.confidence_level,
                b.detection_date,
                b.updated_at
            FROM blacklist_ips b
            WHERE b.is_active = true
              AND b.ip_address NOT IN (
                  SELECT ip_address
                  FROM whitelist_ips
                  WHERE is_active = true
              )
        """

        params = []

        # Risk level filter (confidence_level mapping)
        if risk_level == "high":
            query += " AND b.confidence_level >= 80"
        elif risk_level == "medium":
            query += " AND b.confidence_level >= 50 AND b.confidence_level < 80"
        elif risk_level == "low":
            query += " AND b.confidence_level < 50"

        # Country filter
        if country_filter:
            query += " AND b.country = %s"
            params.append(country_filter)

        query += " ORDER BY b.confidence_level DESC, b.detection_date DESC"

        # Limit
        if limit:
            query += " LIMIT %s"
            params.append(limit)

        rows = db_service.query(query, tuple(params) if params else None)

        # Get total count (before filters)
        total_query = """
            SELECT COUNT(*) as count
            FROM blacklist_ips
            WHERE is_active = true
              AND ip_address NOT IN (
                  SELECT ip_address
                  FROM whitelist_ips
                  WHERE is_active = true
              )
        """
        total_count = db_service.query(total_query)[0]["count"]

        # Format results
        results = []
        for row in rows:
            # Map confidence_level to risk_level
            confidence = row["confidence_level"] or 0
            if confidence >= 80:
                risk = "high"
            elif confidence >= 50:
                risk = "medium"
            else:
                risk = "low"

            results.append({
                "ip": row["ip_address"],
                "country": row["country"] or "unknown",
                "risk_level": risk,
                "reason": row["reason"] or "unspecified",
                "confidence": confidence,
                "first_seen": row["detection_date"].isoformat() if row["detection_date"] else None,
                "last_updated": row["updated_at"].isoformat() if row["updated_at"] else None
            })

        response = {
            "results": results,
            "metadata": {
                "total": total_count,
                "filtered": len(results),
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "filters": {
                    "risk_level": risk_level or "all",
                    "country": country_filter or "all",
                    "limit": limit or "none"
                }
            }
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error generating JSON connector data: {e}")
        return jsonify({
            "error": str(e),
            "results": [],
            "metadata": {
                "total": 0,
                "filtered": 0,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }), 500


@fortinet_api_bp.route("/health", methods=["GET"])
def fortinet_health():
    """
    Health check for FortiGate integration

    Returns:
        {
            "status": "healthy",
            "active_ips": 1234,
            "timestamp": "2025-10-20T..."
        }
    """
    try:
        from core.services.database_service import db_service

        # Quick check: count active IPs
        count_query = """
            SELECT COUNT(*) as count
            FROM blacklist_ips
            WHERE is_active = true
        """

        result = db_service.query(count_query)
        active_count = result[0]["count"] if result else 0

        return jsonify({
            "status": "healthy",
            "active_ips": active_count,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"FortiGate health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
