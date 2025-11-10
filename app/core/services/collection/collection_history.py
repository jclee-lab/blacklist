"""
Collection History Manager
수집 이력 관리
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ...services.database_service import db_service

logger = logging.getLogger(__name__)


class CollectionHistoryManager:
    """수집 이력 관리 클래스"""

    def __init__(self):
        self.history_retention_days = 90  # 90일간 이력 보존

    def record_collection_history(
        self,
        collection_type: str,
        collected_count: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        additional_info: Dict[str, Any] = None,
    ) -> bool:
        """수집 이력 기록"""
        try:
            conn = db_service.get_connection()
            cursor = conn.cursor()

            # collection_history 테이블이 없으면 생성
            self._ensure_history_table_exists(cursor)

            cursor.execute(
                """
                INSERT INTO collection_history
                (collection_type, collected_count, start_date, end_date, additional_info, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    collection_type,
                    collected_count,
                    start_date,
                    end_date,
                    str(additional_info) if additional_info else None,
                    datetime.now(),
                ),
            )

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(
                f"Collection history recorded: {collection_type}, {collected_count} items"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record collection history: {e}")
            return False

    def _ensure_history_table_exists(self, cursor):
        """collection_history 테이블 존재 확인 및 생성"""
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS collection_history (
                    id SERIAL PRIMARY KEY,
                    collection_type VARCHAR(50) NOT NULL,
                    collected_count INTEGER DEFAULT 0,
                    start_date DATE,
                    end_date DATE,
                    additional_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        except Exception as e:
            logger.error(f"Failed to create collection_history table: {e}")

    def get_recent_history(
        self, collection_type: str = None, days: int = 30
    ) -> List[Dict[str, Any]]:
        """최근 수집 이력 조회"""
        try:
            conn = db_service.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT service_name, items_collected, collection_date, collection_date,
                       details, collection_date
                FROM collection_history
                WHERE collection_date >= %s
            """
            params = [datetime.now() - timedelta(days=days)]

            if collection_type:
                query += " AND service_name = %s"
                params.append(collection_type)

            query += " ORDER BY collection_date DESC LIMIT 100"

            cursor.execute(query, params)
            results = cursor.fetchall()

            history = []
            columns = [
                "service_name",
                "items_collected",
                "start_date",
                "end_date",
                "details",
                "collection_date",
            ]

            for row in results:
                history_item = dict(zip(columns, row))
                # 날짜 형식 변환
                for date_field in ["start_date", "end_date", "collection_date"]:
                    if history_item[date_field]:
                        history_item[date_field] = history_item[date_field].isoformat()
                history.append(history_item)

            cursor.close()
            conn.close()

            return history

        except Exception as e:
            logger.error(f"Failed to get collection history: {e}")
            return []

    def get_collection_statistics(self) -> Dict[str, Any]:
        """수집 통계 조회"""
        try:
            conn = db_service.get_connection()
            cursor = conn.cursor()

            stats = {
                "total_collections": 0,
                "total_collected_items": 0,
                "last_7_days": {},
                "by_type": {},
                "success_rate": 0.0,
            }

            # 전체 수집 횟수 및 아이템 수
            cursor.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(items_collected), 0)
                FROM collection_history
                WHERE collection_date >= %s
            """,
                (datetime.now() - timedelta(days=30),),
            )

            result = cursor.fetchone()
            if result:
                stats["total_collections"] = result[0]
                stats["total_collected_items"] = result[1]

            # 최근 7일간 일별 수집 현황
            cursor.execute(
                """
                SELECT DATE(collection_date) as collection_date,
                       COUNT(*) as collection_count,
                       COALESCE(SUM(items_collected), 0) as item_count
                FROM collection_history
                WHERE collection_date >= %s
                GROUP BY DATE(collection_date)
                ORDER BY collection_date DESC
            """,
                (datetime.now() - timedelta(days=7),),
            )

            for row in cursor.fetchall():
                date_str = row[0].isoformat() if row[0] else "unknown"
                stats["last_7_days"][date_str] = {
                    "collections": row[1],
                    "items": row[2],
                }

            # 수집 타입별 통계
            cursor.execute(
                """
                SELECT service_name,
                       COUNT(*) as collection_count,
                       COALESCE(SUM(items_collected), 0) as item_count,
                       MAX(collection_date) as last_collection
                FROM collection_history
                WHERE collection_date >= %s
                GROUP BY service_name
            """,
                (datetime.now() - timedelta(days=30),),
            )

            for row in cursor.fetchall():
                stats["by_type"][row[0]] = {
                    "collections": row[1],
                    "items": row[2],
                    "last_collection": row[3].isoformat() if row[3] else None,
                }

            cursor.close()
            conn.close()

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection statistics: {e}")
            return {
                "total_collections": 0,
                "total_collected_items": 0,
                "last_7_days": {},
                "by_type": {},
                "success_rate": 0.0,
            }

    def cleanup_old_history(self) -> int:
        """오래된 이력 정리"""
        try:
            conn = db_service.get_connection()
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=self.history_retention_days)

            cursor.execute(
                """
                DELETE FROM collection_history
                WHERE created_at < %s
            """,
                (cutoff_date,),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old history records")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old history: {e}")
            return 0


# Singleton instance
history_manager = CollectionHistoryManager()
