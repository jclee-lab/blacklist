"""
Database Schema and Table Browser API
Provides database schema information and table browsing functionality
"""

from flask import Blueprint, jsonify, request
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

logger = logging.getLogger(__name__)

database_api_bp = Blueprint('database_api', __name__, url_prefix='/api/database')


@database_api_bp.route('/schema', methods=['GET'])
def get_database_schema():
    """Query database schema information"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # Query table list and row counts
        cursor.execute("""
            SELECT
                table_name as name,
                (SELECT COUNT(*) FROM information_schema.columns
                 WHERE table_name = t.table_name AND table_schema = 'public') as column_count,
                pg_class.reltuples::bigint as row_count
            FROM information_schema.tables t
            LEFT JOIN pg_class ON pg_class.relname = t.table_name
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "tables": tables,
            "total": len(tables)
        })

    except Exception as e:
        logger.error(f"Schema query error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@database_api_bp.route('/table/<table_name>', methods=['GET'])
def get_table_data(table_name: str):
    """Query specific table data with pagination support"""
    try:
        # SQL Injection prevention: only allow whitelisted tables
        allowed_tables = [
            'blacklist_ips', 'whitelist_ips', 'collection_credentials',
            'collection_history', 'collection_status', 'system_logs',
            'monitoring_data', 'pipeline_metrics', 'collection_metrics'
        ]

        if table_name not in allowed_tables:
            return jsonify({
                "success": False,
                "error": "Table not allowed"
            }), 403

        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = (page - 1) * limit

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # Total row count (using sql.Identifier for safe table name interpolation)
        cursor.execute(
            sql.SQL("SELECT COUNT(*) as total FROM {}").format(
                sql.Identifier(table_name)
            )
        )
        total = cursor.fetchone()['total']

        # Column list (filter hidden columns for UI)
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))

        # Hide specified columns from UI
        hidden_columns = ['created_at', 'registered_at', 'confidence_level', 'updated_at']
        all_columns = [row['column_name'] for row in cursor.fetchall()]
        columns = [col for col in all_columns if col not in hidden_columns]

        # Query data (using sql.Identifier for safe table name)
        cursor.execute(
            sql.SQL("""
                SELECT * FROM {}
                ORDER BY
                    CASE WHEN EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = %s AND column_name = 'created_at'
                    ) THEN created_at END DESC,
                    CASE WHEN EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = %s AND column_name = 'id'
                    ) THEN id END DESC
                LIMIT %s OFFSET %s
            """).format(sql.Identifier(table_name)),
            (table_name, table_name, limit, offset)
        )

        data = cursor.fetchall()

        # Convert data for JSON serialization and filter hidden columns
        serialized_data = []
        for row in data:
            row_dict = dict(row)
            # Remove hidden columns from response
            for hidden_col in hidden_columns:
                row_dict.pop(hidden_col, None)
            # Convert datetime objects to ISO format
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
                # JSONB fields remain as dict
            serialized_data.append(row_dict)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "table_name": table_name,
            "columns": columns,
            "data": serialized_data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        })

    except Exception as e:
        logger.error(f"Table data query error for {table_name}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@database_api_bp.route('/table/<table_name>/column/<column_name>', methods=['GET'])
def get_column_stats(table_name: str, column_name: str):
    """Get statistics for specific column"""
    try:
        allowed_tables = [
            'blacklist_ips', 'whitelist_ips', 'collection_credentials',
            'collection_history', 'collection_status', 'system_logs',
            'monitoring_data', 'pipeline_metrics', 'collection_metrics'
        ]

        if table_name not in allowed_tables:
            return jsonify({
                "success": False,
                "error": "Table not allowed"
            }), 403

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

        cursor = conn.cursor()

        # Column statistics (using sql.Identifier for safe interpolation)
        cursor.execute(
            sql.SQL("""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT({}) as non_null_count,
                    COUNT(DISTINCT {}) as distinct_count
                FROM {}
            """).format(
                sql.Identifier(column_name),
                sql.Identifier(column_name),
                sql.Identifier(table_name)
            )
        )

        stats = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "table_name": table_name,
            "column_name": column_name,
            "stats": stats
        })

    except Exception as e:
        logger.error(f"Column stats error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
