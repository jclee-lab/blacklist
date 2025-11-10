"""
IP Management CRUD API
화이트리스트 및 블랙리스트 CRUD 관리 API
"""

from flask import Blueprint, jsonify, request
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

logger = logging.getLogger(__name__)

ip_management_api_bp = Blueprint('ip_management_api', __name__, url_prefix='/api/ip')


def get_db_connection():
    """데이터베이스 연결 생성"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "blacklist"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        cursor_factory=RealDictCursor,
    )


# ============================================================================
# 통합 IP 리스트 조회 (Unified View)
# ============================================================================

@ip_management_api_bp.route('/unified', methods=['GET'])
def get_unified_ip_list():
    """통합 IP 리스트 조회 (화이트리스트 + 블랙리스트)"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = (page - 1) * limit

        list_type = request.args.get('type')  # 'whitelist', 'blacklist', or None for all
        search_ip = request.args.get('ip')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        where_clauses = []
        params = []

        if list_type in ['whitelist', 'blacklist']:
            where_clauses.append("list_type = %s")
            params.append(list_type)

        if search_ip:
            where_clauses.append("ip_address LIKE %s")
            params.append(f"%{search_ip}%")

        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

        # Count total (extracted query for clarity)
        count_query = f"SELECT COUNT(*) as total FROM unified_ip_list WHERE {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get data (extracted query for clarity)
        query_params = params + [limit, offset]
        data_query = f"""
            SELECT
                list_type, id, ip_address, reason, source,
                confidence_level, detection_count, is_active,
                country, detection_date, removal_date, last_seen,
                created_at, updated_at
            FROM unified_ip_list
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, query_params)

        data = cursor.fetchall()

        # Serialize datetime fields
        serialized_data = []
        for row in data:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            serialized_data.append(row_dict)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": serialized_data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        })

    except Exception as e:
        logger.error(f"Unified IP list query error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# 화이트리스트 CRUD
# ============================================================================

@ip_management_api_bp.route('/whitelist', methods=['GET'])
def get_whitelist():
    """화이트리스트 조회"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # Count total
        cursor.execute("SELECT COUNT(*) as total FROM whitelist_ips")
        total = cursor.fetchone()['total']

        # Get data
        cursor.execute("""
            SELECT id, ip_address, reason, source, country, created_at, updated_at
            FROM whitelist_ips
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        data = cursor.fetchall()

        # Serialize
        serialized_data = []
        for row in data:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            serialized_data.append(row_dict)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": serialized_data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        })

    except Exception as e:
        logger.error(f"Whitelist query error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ip_management_api_bp.route('/whitelist', methods=['POST'])
def create_whitelist():
    """화이트리스트 추가"""
    try:
        data = request.get_json()

        if not data or 'ip_address' not in data:
            return jsonify({"success": False, "error": "ip_address is required"}), 400

        ip_address = data['ip_address']
        reason = data.get('reason', 'VIP Protection')
        source = data.get('source', 'MANUAL')
        country = data.get('country')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert
        cursor.execute("""
            INSERT INTO whitelist_ips (ip_address, reason, source, country, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ip_address, source) DO UPDATE SET
                reason = EXCLUDED.reason,
                country = COALESCE(EXCLUDED.country, whitelist_ips.country),
                updated_at = EXCLUDED.updated_at
            RETURNING id, ip_address, reason, source, country, created_at, updated_at
        """, (ip_address, reason, source, country, datetime.now(), datetime.now()))

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        # Serialize
        result_dict = dict(result)
        for key, value in result_dict.items():
            if hasattr(value, 'isoformat'):
                result_dict[key] = value.isoformat()

        return jsonify({
            "success": True,
            "data": result_dict,
            "message": "화이트리스트에 추가되었습니다."
        }), 201

    except Exception as e:
        logger.error(f"Whitelist creation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ip_management_api_bp.route('/whitelist/<int:id>', methods=['PUT'])
def update_whitelist(id: int):
    """화이트리스트 수정"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build update query
        update_fields = []
        params = []

        if 'ip_address' in data:
            update_fields.append("ip_address = %s")
            params.append(data['ip_address'])
        if 'reason' in data:
            update_fields.append("reason = %s")
            params.append(data['reason'])
        if 'source' in data:
            update_fields.append("source = %s")
            params.append(data['source'])
        if 'country' in data:
            update_fields.append("country = %s")
            params.append(data['country'])

        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(id)

        update_sql = ", ".join(update_fields)

        cursor.execute(f"""
            UPDATE whitelist_ips
            SET {update_sql}
            WHERE id = %s
            RETURNING id, ip_address, reason, source, country, created_at, updated_at
        """, params)

        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        # Serialize
        result_dict = dict(result)
        for key, value in result_dict.items():
            if hasattr(value, 'isoformat'):
                result_dict[key] = value.isoformat()

        return jsonify({
            "success": True,
            "data": result_dict,
            "message": "화이트리스트가 수정되었습니다."
        })

    except Exception as e:
        logger.error(f"Whitelist update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ip_management_api_bp.route('/whitelist/<int:id>', methods=['DELETE'])
def delete_whitelist(id: int):
    """화이트리스트 삭제"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM whitelist_ips WHERE id = %s RETURNING ip_address", (id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"화이트리스트에서 {result['ip_address']}가 삭제되었습니다."
        })

    except Exception as e:
        logger.error(f"Whitelist deletion error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# 블랙리스트 CRUD
# ============================================================================

@ip_management_api_bp.route('/blacklist', methods=['GET'])
def get_blacklist():
    """블랙리스트 조회"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # Count total
        cursor.execute("SELECT COUNT(*) as total FROM blacklist_ips_with_auto_inactive")
        total = cursor.fetchone()['total']

        # Get data
        cursor.execute("""
            SELECT id, ip_address, reason, source, confidence_level,
                   detection_count, is_active, country, detection_date,
                   removal_date, last_seen, created_at, updated_at
            FROM blacklist_ips_with_auto_inactive
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        data = cursor.fetchall()

        # Serialize
        serialized_data = []
        for row in data:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            serialized_data.append(row_dict)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": serialized_data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        })

    except Exception as e:
        logger.error(f"Blacklist query error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ip_management_api_bp.route('/blacklist', methods=['POST'])
def create_blacklist():
    """블랙리스트 추가"""
    try:
        data = request.get_json()

        if not data or 'ip_address' not in data:
            return jsonify({"success": False, "error": "ip_address is required"}), 400

        ip_address = data['ip_address']
        reason = data.get('reason', 'Malicious Activity')
        source = data.get('source', 'MANUAL')
        confidence_level = data.get('confidence_level', 50)
        detection_count = data.get('detection_count', 1)
        is_active = data.get('is_active', True)
        country = data.get('country')
        detection_date = data.get('detection_date')
        removal_date = data.get('removal_date')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert
        cursor.execute("""
            INSERT INTO blacklist_ips
            (ip_address, reason, source, confidence_level, detection_count,
             is_active, country, detection_date, removal_date, last_seen,
             created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ip_address, source) DO UPDATE SET
                reason = EXCLUDED.reason,
                confidence_level = EXCLUDED.confidence_level,
                detection_count = blacklist_ips.detection_count + 1,
                is_active = EXCLUDED.is_active,
                country = COALESCE(EXCLUDED.country, blacklist_ips.country),
                detection_date = EXCLUDED.detection_date,
                removal_date = EXCLUDED.removal_date,
                last_seen = EXCLUDED.last_seen,
                updated_at = EXCLUDED.updated_at
            RETURNING id, ip_address, reason, source, confidence_level,
                      detection_count, is_active, country, detection_date,
                      removal_date, last_seen, created_at, updated_at
        """, (ip_address, reason, source, confidence_level, detection_count,
              is_active, country, detection_date, removal_date, datetime.now(),
              datetime.now(), datetime.now()))

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        # Serialize
        result_dict = dict(result)
        for key, value in result_dict.items():
            if hasattr(value, 'isoformat'):
                result_dict[key] = value.isoformat()

        return jsonify({
            "success": True,
            "data": result_dict,
            "message": "블랙리스트에 추가되었습니다."
        }), 201

    except Exception as e:
        logger.error(f"Blacklist creation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ip_management_api_bp.route('/blacklist/<int:id>', methods=['PUT'])
def update_blacklist(id: int):
    """블랙리스트 수정"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build update query
        update_fields = []
        params = []

        if 'ip_address' in data:
            update_fields.append("ip_address = %s")
            params.append(data['ip_address'])
        if 'reason' in data:
            update_fields.append("reason = %s")
            params.append(data['reason'])
        if 'source' in data:
            update_fields.append("source = %s")
            params.append(data['source'])
        if 'confidence_level' in data:
            update_fields.append("confidence_level = %s")
            params.append(data['confidence_level'])
        if 'is_active' in data:
            update_fields.append("is_active = %s")
            params.append(data['is_active'])
        if 'country' in data:
            update_fields.append("country = %s")
            params.append(data['country'])
        if 'detection_date' in data:
            update_fields.append("detection_date = %s")
            params.append(data['detection_date'])
        if 'removal_date' in data:
            update_fields.append("removal_date = %s")
            params.append(data['removal_date'])

        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(id)

        update_sql = ", ".join(update_fields)

        cursor.execute(f"""
            UPDATE blacklist_ips
            SET {update_sql}
            WHERE id = %s
            RETURNING id, ip_address, reason, source, confidence_level,
                      detection_count, is_active, country, detection_date,
                      removal_date, last_seen, created_at, updated_at
        """, params)

        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        # Serialize
        result_dict = dict(result)
        for key, value in result_dict.items():
            if hasattr(value, 'isoformat'):
                result_dict[key] = value.isoformat()

        return jsonify({
            "success": True,
            "data": result_dict,
            "message": "블랙리스트가 수정되었습니다."
        })

    except Exception as e:
        logger.error(f"Blacklist update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ip_management_api_bp.route('/blacklist/<int:id>', methods=['DELETE'])
def delete_blacklist(id: int):
    """블랙리스트 삭제"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM blacklist_ips WHERE id = %s RETURNING ip_address", (id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"블랙리스트에서 {result['ip_address']}가 삭제되었습니다."
        })

    except Exception as e:
        logger.error(f"Blacklist deletion error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# 통계 및 유틸리티
# ============================================================================

@ip_management_api_bp.route('/statistics', methods=['GET'])
def get_ip_statistics():
    """통합 통계"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM unified_ip_statistics ORDER BY list_type, source")
        stats = cursor.fetchall()

        # Serialize
        serialized_stats = []
        for row in stats:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            serialized_stats.append(row_dict)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "statistics": serialized_stats
        })

    except Exception as e:
        logger.error(f"Statistics query error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
