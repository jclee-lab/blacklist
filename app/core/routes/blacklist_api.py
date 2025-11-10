#!/usr/bin/env python3
"""
통합 최적화 API 라우트 - 효율적인 단일 엔드포인트 구조
모든 API 요청을 단일 블루프린트로 통합하여 성능 향상
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def rate_limit(limit_string):
    """Rate limiting decorator - uses app.limiter from app.py"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get limiter from current_app
            if hasattr(current_app, 'limiter'):
                limiter = current_app.limiter
                # Apply custom rate limit
                @limiter.limit(limit_string)
                def limited_route(*args, **kwargs):
                    return f(*args, **kwargs)
                return limited_route(*args, **kwargs)
            else:
                # Limiter not configured, proceed without rate limiting
                return f(*args, **kwargs)
        return decorated_function
    return decorator

# 단일 최적화 API 블루프린트
blacklist_api_bp = Blueprint("blacklist_api", __name__)


# Note: /health, /stats, /search routes are handled by statistics_api_bp


@blacklist_api_bp.route("/blacklist/list", methods=["GET"])
def get_blacklist_list():
    """블랙리스트 목록 조회 API"""
    try:
        from core.services.database_service import db_service

        # 페이지네이션 파라미터
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        offset = (page - 1) * per_page

        # 데이터베이스 조회 (parameterized query for security)
        blacklist_data = db_service.query(
            "SELECT * FROM blacklist_ips ORDER BY id DESC LIMIT %s OFFSET %s",
            (per_page, offset)
        )

        total_count = db_service.query("SELECT COUNT(*) as count FROM blacklist_ips")[0]["count"]

        return jsonify({
            "success": True,
            "data": blacklist_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Blacklist list API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@blacklist_api_bp.route("/blacklist/stats", methods=["GET"])
def get_blacklist_stats():
    """블랙리스트 통계 API"""
    try:
        from core.services.database_service import db_service

        # 통계 데이터 조회
        total_ips = db_service.query("SELECT COUNT(*) as count FROM blacklist_ips")[0]["count"]

        # 소스별 통계 (category 대신 source 사용)
        source_stats = db_service.query("""
            SELECT source, COUNT(*) as count
            FROM blacklist_ips
            GROUP BY source
        """)

        # 최근 업데이트
        recent_update = db_service.query("""
            SELECT MAX(created_at) as last_update
            FROM blacklist_ips
        """)[0]["last_update"]

        return jsonify({
            "success": True,
            "stats": {
                "total_ips": total_ips,
                "sources": source_stats,
                "last_update": recent_update
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Blacklist stats API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@blacklist_api_bp.route("/blacklist/check", methods=["POST", "GET"])
@rate_limit("1000 per hour; 100 per minute")  # Critical endpoint - high traffic expected
def check_ip_blacklist():
    """
    IP 블랙리스트 체크 API (Phase 1.1 & 1.2: 화이트리스트 우선 + 구조화된 로깅)
    
    POST /api/blacklist/check
    GET /api/blacklist/check?ip=1.2.3.4
    
    Returns:
        {
            "success": True,
            "ip": "1.2.3.4",
            "blocked": False,
            "reason": "whitelist",
            "metadata": {...}
        }
    """
    try:
        # IP 파라미터 가져오기
        if request.method == "POST":
            data = request.get_json() or {}
            ip = data.get("ip")
        else:
            ip = request.args.get("ip")
        
        if not ip:
            return jsonify({
                "success": False,
                "error": "IP address is required"
            }), 400
        
        # 새로운 check_blacklist 메서드 사용 (Phase 1.1 & 1.2 통합)
        from core.services.blacklist_service import service as blacklist_service
        
        result = blacklist_service.check_blacklist(ip)
        
        return jsonify({
            "success": True,
            "ip": ip,
            "blocked": result["blocked"],
            "reason": result["reason"],
            "metadata": result.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"IP check API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@blacklist_api_bp.route("/json", methods=["GET"])
def get_blacklist_json():
    """블랙리스트 데이터 JSON 조회 - JavaScript에서 호출"""
    try:
        from core.services.database_service import db_service

        # 페이지네이션 파라미터
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        offset = (page - 1) * per_page

        # 데이터베이스 연결 시도
        conn = db_service.get_connection()
        cursor = conn.cursor()

        # 전체 카운트
        cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
        total = cursor.fetchone()[0]

        # 데이터 조회
        cursor.execute("""
            SELECT ip_address, source, detection_date, updated_at, confidence_level
            FROM blacklist_ips
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))

        results = cursor.fetchall()
        cursor.close()
        db_service.return_connection(conn)

        return jsonify({
            "success": True,
            "data": [
                {
                    "ip_address": row[0],
                    "source": row[1],
                    "detection_date": row[2].isoformat() if row[2] else None,
                    "updated_at": row[3].isoformat() if row[3] else None,
                    "confidence_level": row[4]
                }
                for row in results
            ],
            "total": total,
            "page": page,
            "per_page": per_page
        })

    except Exception as e:
        logger.warning(f"Database not available, returning empty data: {e}")
        # 데이터베이스 연결 실패 시 빈 데이터 반환 (JavaScript 에러 방지)
        return jsonify({
            "success": True,
            "data": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "message": "Database not available - showing empty data"
        })


# DISABLED: Conflicts with multi_collection_api.py /api/collection/history
# Use multi_collection_api.py for all collection management
# @blacklist_api_bp.route("/collection/history", methods=["GET"])
# def get_collection_history():
#     """수집 히스토리 조회"""
#     try:
#         from core.services.database_service import db_service
#
#         conn = db_service.get_connection()
#         cursor = conn.cursor()
#
#         cursor.execute("""
#             SELECT
#                 service_name,
#                 collection_date,
#                 items_collected,
#                 success,
#                 error_message,
#                 execution_time_ms,
#                 collection_type
#             FROM collection_history
#             ORDER BY collection_date DESC
#             LIMIT 50
#         """)
#
#         results = cursor.fetchall()
#         cursor.close()
#         db_service.return_connection(conn)
#
#         return jsonify({
#             "success": True,
#             "data": [
#                 {
#                     "service_name": row[0],
#                     "collection_date": row[1].isoformat() if row[1] else None,
#                     "items_collected": row[2],
#                     "success": row[3],
#                     "error_message": row[4],
#                     "execution_time_ms": row[5],
#                     "collection_type": row[6],
#                     "timestamp": row[1].isoformat() if row[1] else None  # collection_date를 timestamp로 사용
#                 }
#                 for row in results
#             ]
#         })
#
#     except Exception as e:
#         logger.error(f"Collection history query failed: {e}")
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "data": []
#         }), 500


# Note: /collection/trigger route conflicts with existing routes, focusing on new endpoints only


# Note: /blacklist/active and /blacklist/json routes are handled by statistics_api_bp


@blacklist_api_bp.route("/collection/regtech/trigger", methods=["POST"])
@rate_limit("5 per hour")  # Resource-intensive operation
def trigger_regtech_collection():
    """REGTECH 수집 트리거 - 날짜 범위 지원"""
    try:
        import requests
        data = request.get_json() or {}

        # 컬렉터 서비스 호출 (내부 네트워크)
        collector_response = requests.post(
            "http://blacklist-collector:8545/trigger",
            timeout=30,
            json={
                "source": "regtech_api_trigger",
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date")
            }
        )

        if collector_response.status_code == 200:
            return jsonify({
                "success": True,
                "message": "REGTECH 수집이 시작되었습니다",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"컬렉터 서비스 오류: {collector_response.status_code}",
                "timestamp": datetime.now().isoformat()
            }), 502

    except Exception as e:
        logger.error(f"REGTECH collection trigger failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/system/containers", methods=["GET"])
def get_system_containers():
    """시스템 컨테이너 상태 조회"""
    try:
        import subprocess

        # Docker 컨테이너 상태 조회
        result = subprocess.run(
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    import json
                    containers.append(json.loads(line))

            return jsonify({
                "success": True,
                "containers": containers,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to get container status",
                "timestamp": datetime.now().isoformat()
            }), 500

    except Exception as e:
        logger.error(f"Container status query failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/credential/status", methods=["GET"])
def get_credential_status():
    """인증 상태 확인"""
    try:
        # REGTECH 인증 상태 확인
        import os
        regtech_id = os.getenv("REGTECH_ID")
        regtech_pw = os.getenv("REGTECH_PW")

        if regtech_id and regtech_pw:
            status = {
                "authenticated": True,
                "regtech_id": regtech_id[:3] + "*" * (len(regtech_id) - 3),
                "last_check": datetime.now().isoformat()
            }
        else:
            status = {
                "authenticated": False,
                "message": "REGTECH credentials not configured",
                "last_check": datetime.now().isoformat()
            }

        return jsonify({
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Credential status check failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# DISABLED: Conflicts with multi_collection_api.py /api/collection/status
# Use multi_collection_api.py for all collection management
# @blacklist_api_bp.route("/collection/status", methods=["GET"])
# def get_collection_status():
#     """수집 상태 조회 API - UI에서 요청하는 엔드포인트"""
#     try:
#         from core.services.database_service import db_service
#
#         # 최근 수집 내역 조회
#         recent_collections = db_service.query("""
#             SELECT service_name, collection_date, items_collected, success, error_message
#             FROM collection_history
#             ORDER BY collection_date DESC
#             LIMIT 5
#         """)
#
#         # 전체 통계
#         total_ips = db_service.query("SELECT COUNT(*) as count FROM blacklist_ips")[0]["count"]
#
#         # 수집 서비스별 상태
#         collection_status = {
#             "regtech": {
#                 "enabled": True,
#                 "last_run": None,
#                 "next_run": "Scheduled",
#                 "status": "ready"
#             }
#         }
#
#         # 최근 수집 데이터가 있으면 업데이트
#         if recent_collections:
#             for collection in recent_collections:
#                 service = collection["service_name"].lower()
#                 if service in collection_status:
#                     collection_status[service]["last_run"] = collection["collection_date"].isoformat() if collection["collection_date"] else None
#                     collection_status[service]["status"] = "success" if collection["success"] else "failed"
#                     if not collection["success"] and collection["error_message"]:
#                         collection_status[service]["last_error"] = collection["error_message"]
#
#         return jsonify({
#             "success": True,
#             "data": {
#                 "total_ips": total_ips,
#                 "services": collection_status,
#                 "recent_collections": [
#                     {
#                         "service_name": item["service_name"],
#                         "collection_date": item["collection_date"].isoformat() if item["collection_date"] else None,
#                         "items_collected": item["items_collected"],
#                         "success": item["success"],
#                         "error_message": item["error_message"]
#                     }
#                     for item in recent_collections
#                 ]
#             },
#             "timestamp": datetime.now().isoformat()
#         })
#
#     except Exception as e:
#         logger.error(f"Collection status query failed: {e}")
#         return jsonify({
#             "success": False,
#             "error": str(e),
#             "timestamp": datetime.now().isoformat()
#         }), 500


@blacklist_api_bp.route("/credentials/regtech", methods=["GET"])
def get_regtech_credentials():
    """REGTECH 인증 정보 조회 (프론트엔드가 요청하는 엔드포인트)"""
    try:
        import os
        regtech_id = os.getenv("REGTECH_ID")
        regtech_pw = os.getenv("REGTECH_PW")

        if regtech_id and regtech_pw:
            return jsonify({
                "success": True,
                "authenticated": True,
                "regtech_id": regtech_id[:3] + "*" * (len(regtech_id) - 3),
                "configured": True,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": True,
                "authenticated": False,
                "configured": False,
                "message": "REGTECH credentials not configured",
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"REGTECH credentials check failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/blacklist/manual-add", methods=["POST"])
@rate_limit("20 per hour; 5 per minute")  # State-changing operation
def manual_add_ip():
    """수동 IP 등록 API (블랙리스트)"""
    try:
        import re
        from core.services.database_service import db_service

        # 요청 데이터 검증
        data = request.get_json() or {}
        ip_address = data.get("ip_address", "").strip()
        country = data.get("country", "UNKNOWN").strip()
        notes = data.get("notes", "").strip()

        # IP 주소 필수 체크
        if not ip_address:
            return jsonify({
                "success": False,
                "error": "IP 주소는 필수 항목입니다"
            }), 400

        # IP 주소 형식 검증 (IPv4)
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, ip_address):
            return jsonify({
                "success": False,
                "error": "유효하지 않은 IP 주소 형식입니다"
            }), 400

        # 각 옥텟이 0-255 범위인지 확인
        octets = ip_address.split('.')
        for octet in octets:
            if int(octet) > 255:
                return jsonify({
                    "success": False,
                    "error": "IP 주소 범위가 올바르지 않습니다 (0-255)"
                }), 400

        # 중복 체크
        existing = db_service.query(
            "SELECT COUNT(*) as count FROM blacklist_ips WHERE ip_address = %s",
            (ip_address,)
        )
        if existing and existing[0]["count"] > 0:
            return jsonify({
                "success": False,
                "error": "이미 등록된 IP 주소입니다",
                "ip_address": ip_address
            }), 409

        # DB에 저장
        conn = db_service.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO blacklist_ips
            (ip_address, source, country, detection_date, last_seen, detection_count, created_at, updated_at)
            VALUES (%s, %s, %s, CURRENT_DATE, NOW(), 1, NOW(), NOW())
        """, (ip_address, "MANUAL", country))

        conn.commit()
        cursor.close()
        db_service.return_connection(conn)

        logger.info(f"✅ Manual IP added to blacklist: {ip_address} (country: {country})")

        return jsonify({
            "success": True,
            "message": "IP 주소가 성공적으로 등록되었습니다",
            "data": {
                "ip_address": ip_address,
                "source": "MANUAL",
                "country": country,
                "notes": notes,
                "created_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Manual IP add failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/whitelist/manual-add", methods=["POST"])
@rate_limit("20 per hour; 5 per minute")  # State-changing operation
def manual_add_whitelist_ip():
    """수동 IP 등록 API (화이트리스트)"""
    try:
        import re
        from core.services.database_service import db_service

        # 요청 데이터 검증
        data = request.get_json() or {}
        ip_address = data.get("ip_address", "").strip()
        country = data.get("country", "UNKNOWN").strip()
        reason = data.get("reason", "수동 등록").strip()

        # IP 주소 필수 체크
        if not ip_address:
            return jsonify({
                "success": False,
                "error": "IP 주소는 필수 항목입니다"
            }), 400

        # IP 주소 형식 검증 (IPv4)
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, ip_address):
            return jsonify({
                "success": False,
                "error": "유효하지 않은 IP 주소 형식입니다"
            }), 400

        # 각 옥텟이 0-255 범위인지 확인
        octets = ip_address.split('.')
        for octet in octets:
            if int(octet) > 255:
                return jsonify({
                    "success": False,
                    "error": "IP 주소 범위가 올바르지 않습니다 (0-255)"
                }), 400

        # 중복 체크
        existing = db_service.query(
            "SELECT COUNT(*) as count FROM whitelist_ips WHERE ip_address = %s",
            (ip_address,)
        )
        if existing and existing[0]["count"] > 0:
            return jsonify({
                "success": False,
                "error": "이미 화이트리스트에 등록된 IP 주소입니다",
                "ip_address": ip_address
            }), 409

        # DB에 저장
        conn = db_service.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO whitelist_ips
            (ip_address, source, country, reason, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (ip_address, "MANUAL", country, reason))

        conn.commit()
        cursor.close()
        db_service.return_connection(conn)

        logger.info(f"✅ Manual IP added to whitelist: {ip_address} (country: {country}, reason: {reason})")

        return jsonify({
            "success": True,
            "message": "IP 주소가 화이트리스트에 성공적으로 등록되었습니다",
            "data": {
                "ip_address": ip_address,
                "source": "MANUAL",
                "country": country,
                "reason": reason,
                "created_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Manual whitelist IP add failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/whitelist/list", methods=["GET"])
def get_whitelist_list():
    """화이트리스트 목록 조회 API"""
    try:
        from core.services.database_service import db_service

        # 페이지네이션 파라미터
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        offset = (page - 1) * per_page

        # 데이터베이스 조회 (parameterized query for security)
        whitelist_data = db_service.query(
            "SELECT * FROM whitelist_ips ORDER BY id DESC LIMIT %s OFFSET %s",
            (per_page, offset)
        )

        total_count = db_service.query("SELECT COUNT(*) as count FROM whitelist_ips")[0]["count"]

        return jsonify({
            "success": True,
            "data": whitelist_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Whitelist list API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@blacklist_api_bp.route("/database/tables", methods=["GET"])
def get_database_tables():
    """데이터베이스 테이블 현황 API - 상세 정보 포함"""
    try:
        from core.services.database_service import db_service

        # 새로운 show_database_tables() 메서드 사용 (컬럼 정보 및 샘플 데이터 포함)
        tables_info = db_service.show_database_tables()

        return jsonify({
            "success": tables_info.get("success", True),
            "tables": tables_info.get("tables", {}),
            "total_tables": tables_info.get("total_tables", 0),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Database tables API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/blacklist/batch/add", methods=["POST"])
@rate_limit("10 per hour; 2 per minute")  # Resource-intensive batch operation
def batch_add_blacklist():
    """Batch add multiple IPs to blacklist"""
    try:
        import re
        from core.services.database_service import db_service

        data = request.get_json() or {}
        ips = data.get("ips", [])
        reason = data.get("reason", "Batch import")
        country = data.get("country", "UNKNOWN")

        if not ips or not isinstance(ips, list):
            return jsonify({
                "success": False,
                "error": "IPs list is required"
            }), 400

        # Validate all IPs
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        valid_ips = []
        invalid_ips = []

        for ip in ips:
            if re.match(ip_pattern, str(ip).strip()):
                octets = str(ip).strip().split('.')
                if all(0 <= int(octet) <= 255 for octet in octets):
                    valid_ips.append(str(ip).strip())
                else:
                    invalid_ips.append(ip)
            else:
                invalid_ips.append(ip)

        # Batch insert valid IPs
        conn = db_service.get_connection()
        cursor = conn.cursor()

        added_count = 0
        duplicate_count = 0

        for ip in valid_ips:
            try:
                cursor.execute("""
                    INSERT INTO blacklist_ips
                    (ip_address, source, country, reason, detection_date, last_seen, detection_count, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE, NOW(), 1, NOW(), NOW())
                    ON CONFLICT (ip_address) DO NOTHING
                """, (ip, "BATCH", country, reason))
                if cursor.rowcount > 0:
                    added_count += 1
                else:
                    duplicate_count += 1
            except Exception as e:
                logger.warning(f"Failed to add IP {ip}: {e}")

        conn.commit()
        cursor.close()
        db_service.return_connection(conn)

        logger.info(f"✅ Batch added {added_count} IPs to blacklist")

        return jsonify({
            "success": True,
            "message": f"Batch operation completed",
            "summary": {
                "total_requested": len(ips),
                "added": added_count,
                "duplicates": duplicate_count,
                "invalid": len(invalid_ips)
            },
            "invalid_ips": invalid_ips,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Batch add failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/blacklist/batch/remove", methods=["POST"])
@rate_limit("10 per hour; 2 per minute")  # Resource-intensive batch operation
def batch_remove_blacklist():
    """Batch remove multiple IPs from blacklist"""
    try:
        from core.services.database_service import db_service

        data = request.get_json() or {}
        ips = data.get("ips", [])

        if not ips or not isinstance(ips, list):
            return jsonify({
                "success": False,
                "error": "IPs list is required"
            }), 400

        conn = db_service.get_connection()
        cursor = conn.cursor()

        removed_count = 0
        for ip in ips:
            try:
                cursor.execute("DELETE FROM blacklist_ips WHERE ip_address = %s", (str(ip).strip(),))
                removed_count += cursor.rowcount
            except Exception as e:
                logger.warning(f"Failed to remove IP {ip}: {e}")

        conn.commit()
        cursor.close()
        db_service.return_connection(conn)

        logger.info(f"✅ Batch removed {removed_count} IPs from blacklist")

        return jsonify({
            "success": True,
            "message": "Batch remove completed",
            "summary": {
                "total_requested": len(ips),
                "removed": removed_count
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Batch remove failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@blacklist_api_bp.route("/blacklist/batch/update", methods=["POST"])
@rate_limit("10 per hour; 2 per minute")  # Resource-intensive batch operation
def batch_update_blacklist():
    """Batch update multiple blacklist entries"""
    try:
        from core.services.database_service import db_service

        data = request.get_json() or {}
        ips = data.get("ips", [])
        reason = data.get("reason")
        country = data.get("country")

        if not ips or not isinstance(ips, list):
            return jsonify({
                "success": False,
                "error": "IPs list is required"
            }), 400

        if not reason and not country:
            return jsonify({
                "success": False,
                "error": "At least one field (reason or country) is required for update"
            }), 400

        conn = db_service.get_connection()
        cursor = conn.cursor()

        updated_count = 0
        for ip in ips:
            try:
                # Build dynamic UPDATE query
                update_fields = []
                update_values = []

                if reason:
                    update_fields.append("reason = %s")
                    update_values.append(reason)
                if country:
                    update_fields.append("country = %s")
                    update_values.append(country)

                update_fields.append("updated_at = NOW()")
                update_values.append(str(ip).strip())

                query = f"UPDATE blacklist_ips SET {', '.join(update_fields)} WHERE ip_address = %s"
                cursor.execute(query, tuple(update_values))
                updated_count += cursor.rowcount
            except Exception as e:
                logger.warning(f"Failed to update IP {ip}: {e}")

        conn.commit()
        cursor.close()
        db_service.return_connection(conn)

        logger.info(f"✅ Batch updated {updated_count} IPs in blacklist")

        return jsonify({
            "success": True,
            "message": "Batch update completed",
            "summary": {
                "total_requested": len(ips),
                "updated": updated_count
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Batch update failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# 에러 핸들러
@blacklist_api_bp.errorhandler(404)
def api_not_found(error):
    """API 404 핸들러"""
    return jsonify({
        "success": False,
        "error": "API endpoint not found",
        "available_endpoints": [
            "/api/collection/history",
            "/api/collection/regtech/trigger",
            "/api/system/containers",
            "/api/credential/status",
            "/api/credentials/regtech"
        ]
    }), 404


@blacklist_api_bp.errorhandler(500)
def api_server_error(error):
    """API 500 핸들러"""
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500