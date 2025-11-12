"""
블랙리스트 통합 서비스
모든 블랙리스트 관련 비즈니스 로직을 처리하는 서비스 클래스
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..utils.version import get_app_version
import structlog
import redis
import json

# Phase 2.2: Prometheus 메트릭 (Claude-Gemini 합의안)
from ..monitoring.metrics import blacklist_decisions_total, blacklist_whitelist_hits_total

# 구조화된 로깅 설정
logger = structlog.get_logger(__name__)
standard_logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """시스템 헬스 상태"""

    status: str  # healthy, degraded, stopped
    version: str
    timestamp: datetime
    components: Dict[str, Any]


class BlacklistService:
    """통합 블랙리스트 서비스 with Redis caching"""

    def __init__(self):
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "blacklist"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        }
        self._components = {"regtech": True, "database": True, "redis": False}

        # Redis 캐시 초기화
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "blacklist-redis"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Redis 연결 테스트
            self.redis_client.ping()
            self._components["redis"] = True
            standard_logger.info("✅ Redis cache initialized successfully")
        except Exception as e:
            standard_logger.warning(f"⚠️ Redis cache unavailable (will use DB only): {e}")
            self.redis_client = None

        # 캐시 TTL 설정 (5분 = 300초)
        self.cache_ttl = 300

    def log_decision(self, ip: str, decision: str, reason: str, metadata: Optional[Dict[str, Any]] = None):
        """블랙리스트 판단 결정 로깅 (Phase 1.2: 핀포인트 로깅)"""
        log_data = {
            "ip": ip,
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            log_data.update(metadata)

        # Phase 2.2: Prometheus 메트릭 증가 (Claude-Gemini 합의안)
        blacklist_decisions_total.labels(decision=decision, reason=reason).inc()

        logger.info(
            "blacklist_decision",
            **log_data
        )

    def is_whitelisted(self, ip: str) -> bool:
        """화이트리스트 체크 with Redis caching (Phase 1.1: VIP 고객 IP 보호)"""
        cache_key = f"whitelist:{ip}"

        try:
            # 1. Redis 캐시 확인
            if self.redis_client:
                try:
                    cached = self.redis_client.get(cache_key)
                    if cached is not None:
                        is_whitelisted = cached == "true"
                        if is_whitelisted:
                            blacklist_whitelist_hits_total.labels(ip_type="vip").inc()
                            self.log_decision(ip, "ALLOWED", "whitelist", {"whitelist_hit": True, "cache_hit": True})
                        return is_whitelisted
                except Exception as redis_err:
                    standard_logger.warning(f"Redis cache read failed: {redis_err}")

            # 2. 캐시 미스 - DB 조회
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) as count FROM whitelist_ips
                WHERE ip_address = %s
                """,
                (ip,)
            )

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            is_whitelisted = result["count"] > 0 if result else False

            # 3. Redis 캐시에 저장 (TTL 5분)
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, self.cache_ttl, "true" if is_whitelisted else "false")
                except Exception as redis_err:
                    standard_logger.warning(f"Redis cache write failed: {redis_err}")

            if is_whitelisted:
                blacklist_whitelist_hits_total.labels(ip_type="vip").inc()
                self.log_decision(ip, "ALLOWED", "whitelist", {"whitelist_hit": True, "cache_hit": False})

            return is_whitelisted

        except Exception as e:
            standard_logger.warning(f"Whitelist check failed for {ip}: {e}")
            return False

    def _create_whitelist_table(self):
        """화이트리스트 테이블 생성"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whitelist_ips (
                    id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL,
                    reason VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ip_address)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            standard_logger.info("Whitelist table created successfully")
            
        except Exception as e:
            standard_logger.error(f"Failed to create whitelist table: {e}")

    def check_blacklist(self, ip: str) -> Dict[str, Any]:
        """
        블랙리스트 체크 with Redis caching (Phase 1.1: 화이트리스트 우선 체크 추가)

        Returns:
            {
                "blocked": bool,
                "reason": str,
                "metadata": dict
            }
        """
        cache_key = f"blacklist:{ip}"

        try:
            # Phase 1.1: 화이트리스트 우선 체크 (캐싱됨)
            if self.is_whitelisted(ip):
                return {
                    "blocked": False,
                    "reason": "whitelist",
                    "metadata": {"source": "whitelist", "priority": "high"}
                }

            # 1. Redis 캐시 확인
            if self.redis_client:
                try:
                    cached = self.redis_client.get(cache_key)
                    if cached:
                        result = json.loads(cached)
                        result["metadata"]["cache_hit"] = True

                        if result["blocked"]:
                            self.log_decision(ip, "BLOCKED", result["reason"], {**result["metadata"], "cache_hit": True})
                        else:
                            self.log_decision(ip, "ALLOWED", result["reason"], {"cache_hit": True})

                        return result
                except Exception as redis_err:
                    standard_logger.warning(f"Redis cache read failed: {redis_err}")

            # 2. 캐시 미스 - DB 조회
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ip_address, reason, source, detection_count
                FROM blacklist_ips
                WHERE ip_address = %s AND is_active = true
                """,
                (ip,)
            )

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                reason = result["reason"] or "blacklisted"
                source = result["source"] or "unknown"
                detection_count = result["detection_count"] or 1

                response = {
                    "blocked": True,
                    "reason": reason,
                    "metadata": {
                        "source": source,
                        "detection_count": detection_count,
                        "cache_hit": False
                    }
                }

                self.log_decision(
                    ip,
                    "BLOCKED",
                    reason,
                    {
                        "source": source,
                        "detection_count": detection_count,
                        "blacklist_match": True,
                        "cache_hit": False
                    }
                )
            else:
                response = {
                    "blocked": False,
                    "reason": "not_in_blacklist",
                    "metadata": {"checked": True, "cache_hit": False}
                }

                self.log_decision(ip, "ALLOWED", "not_in_blacklist", {"cache_hit": False})

            # 3. Redis 캐시에 저장 (TTL 5분)
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(response))
                except Exception as redis_err:
                    standard_logger.warning(f"Redis cache write failed: {redis_err}")

            return response

        except Exception as e:
            standard_logger.error(f"Blacklist check failed for {ip}: {e}")
            self.log_decision(ip, "ERROR", str(e), {"error": True})

            return {
                "blocked": False,
                "reason": "error",
                "metadata": {"error": str(e)}
            }

    def get_db_connection(self):
        """데이터베이스 연결 획득"""
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )

    def get_health(self) -> HealthStatus:
        """시스템 헬스 상태 반환 with Redis status"""
        try:
            # Database health check
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM blacklist_ips")
            ip_count = cursor.fetchone()["count"]
            cursor.close()
            conn.close()

            # Redis health check
            redis_status = "unavailable"
            if self.redis_client:
                try:
                    self.redis_client.ping()
                    redis_status = "healthy"
                except Exception:
                    redis_status = "degraded"

            components = {
                "database": {"status": "healthy", "ip_count": ip_count},
                "redis": {"status": redis_status, "enabled": self._components["redis"]},
                "regtech": {"status": "healthy", "enabled": True},
            }

            overall_status = "healthy" if redis_status in ["healthy", "unavailable"] else "degraded"

            return HealthStatus(
                status=overall_status,
                version=get_app_version(),
                timestamp=datetime.now(),
                components=components,
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthStatus(
                status="degraded",
                version=get_app_version(),
                timestamp=datetime.now(),
                components={"error": str(e)},
            )

    def get_collection_status(self) -> Dict[str, Any]:
        """수집 상태 반환"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 소스별 통계
            cursor.execute(
                """
                SELECT source, COUNT(*) as count, MAX(last_seen) as last_seen
                FROM blacklist_ips
                GROUP BY source
            """
            )
            sources = cursor.fetchall()

            cursor.close()
            conn.close()

            status = {
                "collection_enabled": True,
                "sources": {},
                "total_ips": sum(s["count"] for s in sources),
                "last_updated": datetime.now().isoformat(),
            }

            for source in sources:
                status["sources"][source["source"].lower()] = {
                    "total_ips": source["count"],
                    "last_seen": (
                        source["last_seen"].isoformat() if source["last_seen"] else None
                    ),
                    "enabled": True,
                }

            return status
        except Exception as e:
            logger.error(f"Collection status check failed: {e}")
            return {"error": str(e), "collection_enabled": False}

    async def get_active_blacklist(self, format_type: str = "text") -> Dict[str, Any]:
        """활성 블랙리스트 조회"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            if format_type == "enhanced":
                # blacklist_ips_with_auto_inactive view 사용 - 해제일 자동 체크
                cursor.execute(
                    """
                    SELECT ip_address, reason, source,
                           is_active, last_seen, detection_count
                    FROM blacklist_ips_with_auto_inactive
                    WHERE is_active = true
                    ORDER BY last_seen DESC
                """
                )
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    item = {
                        "ip_address": row[0],
                        "reason": row[1],
                        "source": row[2],
                        "is_active": row[3],
                        "last_seen": row[4].isoformat() if row[4] else None,
                        "detection_count": row[5] if len(row) > 5 else 0,
                    }
                    data.append(item)

            elif format_type == "fortigate":
                # blacklist_ips_with_auto_inactive view 사용 - 해제일 자동 체크
                cursor.execute(
                    "SELECT ip_address FROM blacklist_ips_with_auto_inactive WHERE is_active = true"
                )
                ips = [row[0] for row in cursor.fetchall()]
                data = {
                    "entries": [{"ip": ip, "action": "block"} for ip in ips],
                    "total": len(ips),
                    "format": "fortigate_external_connector",
                }
            else:  # text format
                # blacklist_ips_with_auto_inactive view 사용 - 해제일 자동 체크
                cursor.execute(
                    "SELECT ip_address FROM blacklist_ips_with_auto_inactive WHERE is_active = true"
                )
                data = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Active blacklist retrieval failed: {e}")
            return {"success": False, "error": str(e)}

    def get_active_blacklist_ips(self) -> List[str]:
        """활성 블랙리스트 IP 목록 반환 (동기 메서드) - 해제일 기준 자동 필터링"""
        try:
            logger.info("🔥 Starting get_active_blacklist_ips")
            conn = self.get_db_connection()
            logger.info("🔥 Database connection established")
            cursor = conn.cursor()
            logger.info("🔥 Cursor created")

            # blacklist_ips_with_auto_inactive view 사용 - 해제일 자동 체크
            cursor.execute(
                "SELECT ip_address FROM blacklist_ips_with_auto_inactive WHERE is_active = true ORDER BY created_at DESC"
            )
            logger.info("🔥 Query executed")
            results = cursor.fetchall()
            logger.info(f"🔥 Raw results count: {len(results)}")
            logger.info(f"🔥 First few results: {results[:3] if results else 'None'}")

            ips = [str(row["ip_address"]) for row in results]  # RealDictCursor 사용
            logger.info(f"🔥 Processed IPs count: {len(ips)}")

            cursor.close()
            conn.close()
            logger.info("🔥 Connection closed")

            logger.info(f"Retrieved {len(ips)} active IPs")
            return ips

        except Exception as e:
            logger.error(f"get_active_blacklist_ips error: {e}")
            logger.error(f"🔥 Exception type: {type(e)}")
            logger.error(f"🔥 Exception args: {e.args}")
            return []

    def format_for_fortigate(self, ips: List[str]) -> Dict[str, Any]:
        """FortiGate 형식으로 변환"""
        try:
            return {
                "entries": [{"ip": ip, "action": "block"} for ip in ips],
                "total": len(ips),
                "format": "fortigate_external_connector",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"FortiGate format error: {e}")
            return {"entries": [], "total": 0, "error": str(e)}

    def search_ip(self, ip: str) -> Dict[str, Any]:
        """IP 검색"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ip_address, reason, source,
                       is_active, last_seen, detection_count
                FROM blacklist_ips
                WHERE ip_address = %s
            """,
                (ip,),
            )

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                data = {
                    "ip_address": result[0],
                    "reason": result[1],
                    "source": result[2],
                    "is_active": result[3],
                    "last_seen": result[4].isoformat() if result[4] else None,
                    "detection_count": result[5] if len(result) > 5 else 0,
                }

                return {
                    "success": True,
                    "found": True,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "success": True,
                    "found": False,
                    "data": None,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"IP search failed for {ip}: {e}")
            return {"success": False, "error": str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """시스템 통계"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 전체 통계
            cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
            total_ips = cursor.fetchone()[0]

            # blacklist_ips_with_auto_inactive view 사용 - 해제일 자동 체크
            cursor.execute("SELECT COUNT(*) FROM blacklist_ips_with_auto_inactive WHERE is_active = true")
            active_ips = cursor.fetchone()[0]

            # 소스별 통계
            cursor.execute(
                """
                SELECT source, COUNT(*) as count FROM blacklist_ips GROUP BY source
            """
            )
            sources = {}
            for row in cursor.fetchall():
                sources[row[0]] = {  # source
                    "count": row[1],  # count
                }

            # Category statistics removed (column deleted)
            categories = {}

            cursor.close()
            conn.close()

            statistics = {
                "total_ips": total_ips,
                "active_ips": active_ips,
                "sources": sources,
                "categories": categories,
                "last_updated": datetime.now().isoformat(),
            }

            return {"success": True, "statistics": statistics}

        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            return {"success": False, "error": str(e)}

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 조회 (동기식) - API 호환성을 위한 메서드"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 전체 통계
            cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
            total_ips = cursor.fetchone()[0]

            # blacklist_ips_with_auto_inactive view 사용 - 해제일 자동 체크
            cursor.execute("SELECT COUNT(*) FROM blacklist_ips_with_auto_inactive WHERE is_active = true")
            active_ips = cursor.fetchone()[0]

            # 소스별 통계
            cursor.execute(
                """
                SELECT source, COUNT(*) as count FROM blacklist_ips GROUP BY source
            """
            )
            sources = {}
            for row in cursor.fetchall():
                sources[row[0]] = {  # source
                    "count": row[1],  # count
                }

            # Category statistics removed (column deleted)
            categories = {}

            cursor.close()
            conn.close()

            return {
                "success": True,
                "total_ips": total_ips,
                "active_ips": active_ips,
                "sources": sources,
                "categories": categories,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"System stats retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_ips": 0,
                "active_ips": 0,
                "sources": {},
                "categories": {},
            }

    async def enable_collection(self) -> Dict[str, Any]:
        """수집 시스템 활성화"""
        try:
            # 실제 구현에서는 수집 프로세스를 시작
            logger.info("Collection system enabled")
            return {
                "success": True,
                "message": "수집 시스템이 활성화되었습니다",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Collection enable failed: {e}")
            return {"success": False, "error": str(e)}

    async def disable_collection(self) -> Dict[str, Any]:
        """수집 시스템 비활성화"""
        try:
            # 실제 구현에서는 수집 프로세스를 중지
            logger.info("Collection system disabled")
            return {
                "success": True,
                "message": "수집 시스템이 비활성화되었습니다",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Collection disable failed: {e}")
            return {"success": False, "error": str(e)}

    async def collect_all_data(self, force: bool = False) -> Dict[str, Any]:
        """REGTECH 소스에서 데이터 수집 (SECUDIUM 제거됨)"""
        results = {}

        # REGTECH 수집 (유일하게 지원되는 소스)
        regtech_result = await self._collect_regtech_data(force)
        results["regtech"] = regtech_result

        success_count = sum(1 for r in results.values() if r.get("success", False))

        return {
            "success": success_count > 0,
            "results": results,
            "summary": {
                "total_sources": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
            },
        }

    async def _collect_regtech_data(self, force: bool = False) -> Dict[str, Any]:
        """REGTECH 데이터 수집"""
        try:
            # 실제 REGTECH API 호출
            from ..collectors.regtech_collector_core import RegtechCollector
            from ..collectors.unified_collector import CollectionConfig

            config = CollectionConfig()
            collector = RegtechCollector(config)
            result = collector.collect_from_web()

            if result.get("success"):
                collected_count = result.get("count", 0)
                logger.info(f"✅ REGTECH 실제 데이터 수집: {collected_count}개")
            else:
                logger.error(f"❌ REGTECH 수집 실패: {result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": result.get("error", "REGTECH collection failed"),
                }

            logger.info(f"REGTECH collection completed: {collected_count} IPs")
            return {
                "success": True,
                "collected": collected_count,
                "message": "REGTECH 수집 완료",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"REGTECH collection failed: {e}")
            return {"success": False, "error": str(e)}

    # SECUDIUM 지원 제거됨 - REGTECH만 지원

    def sync_with_collector(self) -> Dict[str, Any]:
        """컬렉터에서 데이터 동기화 - 같은 DB를 공유하므로 실제로는 상태만 확인"""
        try:
            import requests

            # 컬렉터 헬스 체크
            try:
                collector_url = "http://blacklist-collector:8545"
                health_response = requests.get(f"{collector_url}/health", timeout=5)
                collector_healthy = health_response.status_code == 200
            except BaseException:
                collector_healthy = False

            # 현재 데이터베이스 상태 (메인앱과 컬렉터 모두 같은 DB 사용)
            stats = self.get_system_stats()

            return {
                "success": True,
                "collector_status": "healthy" if collector_healthy else "unreachable",
                "total_ips": stats.get("total_ips", 0),
                "active_ips": stats.get("active_ips", 0),
                "database_shared": True,
                "message": f"총 {stats.get('total_ips', 0)}개 IP (활성: {stats.get('active_ips', 0)}개)",
                "note": "메인앱과 컬렉터는 같은 데이터베이스를 공유합니다",
            }

        except Exception as e:
            logger.error(f"동기화 상태 확인 실패: {e}")
            return {"success": False, "error": str(e), "collector_status": "error"}

    def force_schema_fix(self) -> Dict[str, Any]:
        """강제 스키마 수정 - is_active 컬럼 추가"""
        try:
            from .database_service import db_service

            with db_service.get_connection() as conn:
                cursor = conn.cursor()

                # is_active 컬럼 추가 (없으면)
                try:
                    cursor.execute(
                        """
                        ALTER TABLE blacklist_ips ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                    """
                    )
                    conn.commit()
                    added_is_active = True
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column name" in str(e):
                        added_is_active = False
                    else:
                        raise e

                # country 컬럼 추가 (없으면)
                try:
                    cursor.execute(
                        """
                        ALTER TABLE blacklist_ips ADD COLUMN country VARCHAR(10);
                    """
                    )
                    conn.commit()
                    added_country = True
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column name" in str(e):
                        added_country = False
                    else:
                        raise e

                # detection_date 컬럼 추가 (없으면)
                try:
                    cursor.execute(
                        """
                        ALTER TABLE blacklist_ips ADD COLUMN detection_date DATE;
                    """
                    )
                    conn.commit()
                    added_detection_date = True
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column name" in str(e):
                        added_detection_date = False
                    else:
                        raise e

                # removal_date 컬럼 추가 (없으면)
                try:
                    cursor.execute(
                        """
                        ALTER TABLE blacklist_ips ADD COLUMN removal_date DATE;
                    """
                    )
                    conn.commit()
                    added_removal_date = True
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column name" in str(e):
                        added_removal_date = False
                    else:
                        raise e

                cursor.close()

                return {
                    "success": True,
                    "message": "스키마 강제 수정 완료",
                    "added_columns": {
                        "is_active": added_is_active,
                        "country": added_country,
                        "detection_date": added_detection_date,
                        "removal_date": added_removal_date,
                    },
                }

        except Exception as e:
            logger.error(f"스키마 강제 수정 실패: {e}")
            return {"success": False, "error": str(e)}

    def force_data_refresh(self) -> Dict[str, Any]:
        """강제 데이터 새로고침 - 컬렉터에서 데이터 복사"""
        try:
            import requests

            # 1단계: 컬렉터에서 모든 IP 데이터 가져오기
            collector_url = "http://blacklist-collector:8545"
            try:
                # 컬렉터에서 JSON 데이터 가져오기
                data_response = requests.get(f"{collector_url}/api/data", timeout=30)

                if data_response.status_code == 200:
                    collector_data = data_response.json()

                    # 2단계: 메인 앱 데이터베이스에 복사
                    copied_count = self._copy_data_from_collector(collector_data)

                    return {
                        "success": True,
                        "message": f"컬렉터에서 {copied_count}개 IP 데이터를 복사했습니다",
                        "copied_count": copied_count,
                        "source": "collector_data_copy",
                    }
                else:
                    logger.warning(f"컬렉터 데이터 API 실패: {data_response.status_code}")
                    return self._fallback_direct_collection()

            except requests.exceptions.RequestException as e:
                logger.warning(f"컬렉터 연결 실패: {e}")
                return self._fallback_direct_collection()

        except Exception as e:
            logger.error(f"강제 데이터 새로고침 실패: {e}")
            return {"success": False, "error": str(e)}

    def _copy_data_from_collector(self, collector_data) -> int:
        """컬렉터 데이터를 메인 앱 DB에 복사"""
        copied_count = 0

        try:
            from .database_service import db_service

            with db_service.get_connection() as conn:
                cursor = conn.cursor()

                # 기존 데이터 비활성화 (중복 방지)
                cursor.execute(
                    "UPDATE blacklist_ips SET is_active = false WHERE source = 'REGTECH'"
                )

                # 새 데이터 삽입
                for ip_data in collector_data.get("data", []):
                    try:
                        cursor.execute(
                            """
                            INSERT INTO blacklist_ips
                            (ip_address, reason, source, country, detection_date,
                             is_active, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (ip_address, source) DO UPDATE SET
                            is_active = EXCLUDED.is_active,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                            (
                                ip_data.get("ip_address"),
                                ip_data.get("reason", ""),
                                "REGTECH",
                                ip_data.get("country"),
                                ip_data.get("detection_date"),
                                True,
                            ),
                        )
                        copied_count += 1
                    except Exception as insert_error:
                        logger.warning(
                            f"IP 삽입 실패 {ip_data.get('ip_address')}: {insert_error}"
                        )
                        continue

                conn.commit()
                cursor.close()

        except Exception as e:
            logger.error(f"데이터 복사 실패: {e}")

        return copied_count

    def _fallback_direct_collection(self) -> Dict[str, Any]:
        """폴백: 메인 앱에서 직접 REGTECH 수집"""
        logger.info("컬렉터 사용 불가, 메인 앱에서 직접 수집 시도")
        return {
            "success": False,
            "error": "컬렉터 연결 실패 및 직접 수집 미구현",
            "fallback_attempted": True,
            "suggestion": "수동으로 REGTECH 포털에서 데이터를 다운로드하세요",
        }


# 전역 서비스 인스턴스
service = BlacklistService()
