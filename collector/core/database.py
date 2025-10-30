"""
Database service for collector
데이터베이스 연결 및 관리 서비스
"""

import logging
import psycopg2
import time
import ipaddress
import base64
import json
import os
from datetime import datetime, timedelta
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from collector.config import CollectorConfig
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class DatabaseService:
    """고성능 데이터베이스 서비스 클래스 - 최적화된 배치 처리 및 캐싱"""

    def __init__(self):
        self.pool: Optional[SimpleConnectionPool] = None
        self._ip_cache: Dict[str, bool] = {}  # IP 존재 여부 캐시
        self._cache_max_size = 1000000  # 캐시 최대 크기 (100만개로 대폭 증가)
        self._batch_buffer: List[Dict[str, Any]] = []  # 배치 버퍼
        self._cipher_suite = None
        self._setup_decryption()
        self._initialize_connection_pool()

    def _setup_decryption(self):
        """암호화 키 설정 (복호화용)"""
        try:
            # 환경변수에서 마스터 키 획득 (app과 동일한 키 사용)
            master_key = os.getenv("CREDENTIAL_MASTER_KEY")
            if not master_key:
                master_key = "default-blacklist-credential-master-key-2025"

            # Salt (app과 동일)
            salt = b'blacklist-regtech-salt-2025'

            # PBKDF2를 사용한 키 파생
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._cipher_suite = Fernet(key)

            logger.info("🔐 복호화 시스템 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 복호화 시스템 초기화 실패: {e}")
            self._cipher_suite = None

    def _decrypt_password(self, encrypted_data: str) -> str:
        """암호화된 비밀번호 복호화"""
        try:
            if not self._cipher_suite:
                logger.error("❌ 복호화 시스템이 초기화되지 않음")
                return encrypted_data

            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = self._cipher_suite.decrypt(decoded)
            decrypted_json = decrypted.decode()

            # JSON 파싱하여 password 추출
            credential_data = json.loads(decrypted_json)
            return credential_data.get("password", "")
        except Exception as e:
            logger.error(f"❌ 비밀번호 복호화 실패: {e}")
            return encrypted_data

    def _initialize_connection_pool(self):
        """연결 풀 초기화 - 고성능 설정"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=2,  # 최소 연결 수 증가
                maxconn=20,  # 최대 연결 수 증가
                host=CollectorConfig.POSTGRES_HOST,
                port=CollectorConfig.POSTGRES_PORT,
                database=CollectorConfig.POSTGRES_DB,
                user=CollectorConfig.POSTGRES_USER,
                password=CollectorConfig.POSTGRES_PASSWORD,
                # 성능 최적화 파라미터
                **{
                    "connect_timeout": 10,
                    "application_name": "blacklist_collector_optimized",
                },
            )
            logger.info("✅ 고성능 데이터베이스 연결 풀 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 풀 초기화 실패: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """최적화된 연결 풀에서 연결 가져오기"""
        conn = None
        try:
            conn = self.pool.getconn()
            # 성능 최적화 설정
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"데이터베이스 연결 오류: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False

    def get_collection_credentials(self, service_name: str) -> Optional[Dict[str, str]]:
        """수집 서비스 인증 정보 조회 - 암호화된 비밀번호 자동 복호화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT username, password, encrypted
                    FROM collection_credentials
                    WHERE service_name = %s AND is_active = TRUE
                """,
                    (service_name,),
                )
                result = cursor.fetchone()
                cursor.close()

                if result:
                    username, password, encrypted = result

                    # 암호화된 경우 복호화
                    if encrypted and password:
                        logger.info(f"🔐 {service_name} 암호화된 비밀번호 복호화 중...")
                        decrypted_password = self._decrypt_password(password)
                        return {"username": username, "password": decrypted_password}
                    else:
                        # 평문인 경우 그대로 반환
                        return {"username": username, "password": password}

                return None
        except Exception as e:
            logger.error(f"인증 정보 조회 실패 {service_name}: {e}")
            return None

    def save_blacklist_ips(self, ip_data: List[Dict[str, Any]]) -> int:
        """최적화된 블랙리스트 IP 데이터 저장 - 대용량 배치 처리"""
        if not ip_data:
            return 0

        saved_count = 0
        processing_start = time.time()

        try:
            logger.info(f"🚀 대용량 배치 처리 시작: {len(ip_data)}개 IP")

            # 1단계: 사설 IP 및 오탐 필터링
            filtered_ips, excluded_count = self._filter_invalid_ips(ip_data)
            logger.info(f"🛡️ 오탐 필터링 완료: {excluded_count}개 제외 (사설 IP, 잘못된 형식 등)")

            if not filtered_ips:
                logger.warning("⚠️ 필터링 후 유효한 IP가 없습니다")
                return 0

            # 2단계: 메모리 최적화된 중복 제거
            unique_ips = self._memory_optimized_dedup(filtered_ips)
            logger.info(f"📊 중복 제거 완료: {len(unique_ips)}개 고유 IP")

            # 3단계: 데이터베이스 기존 IP 배치 확인
            existing_ips = self._batch_check_existing_ips(
                [item["ip_address"] for item in unique_ips]
            )
            new_ips = [
                item for item in unique_ips if item["ip_address"] not in existing_ips
            ]
            logger.info(f"📊 신규 IP 필터링: {len(new_ips)}개 신규 IP")

            if not new_ips:
                logger.info("✅ 처리할 신규 IP가 없습니다")
                return 0

            # 4단계: 대용량 배치 삽입
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 배치 처리 최적화 (트랜잭션 전에 설정)
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET maintenance_work_mem = '256MB'")
                cursor.execute("SET synchronous_commit = off")

                # 트랜잭션 시작
                cursor.execute("BEGIN")

                # 대용량 배치 처리 (청크 단위)
                chunk_size = CollectorConfig.BATCH_SIZE
                total_chunks = (len(new_ips) + chunk_size - 1) // chunk_size

                for chunk_idx, chunk in enumerate(
                    self._get_batches(new_ips, chunk_size)
                ):
                    chunk_saved = self._optimized_batch_insert(cursor, chunk)
                    saved_count += chunk_saved

                    # 진행 상황 로깅
                    if chunk_idx % 10 == 0:
                        logger.info(f"📈 처리 진행률: {chunk_idx+1}/{total_chunks} 청크 완료")

                # 커밋 전 최종 검증
                cursor.execute(
                    "SELECT COUNT(*) FROM blacklist_ips WHERE created_at >= %s",
                    (datetime.now() - timedelta(minutes=5),),
                )
                recent_count = cursor.fetchone()[0]

                conn.commit()
                cursor.close()

                processing_time = time.time() - processing_start
                logger.info(
                    f"✅ 대용량 배치 처리 완료: {saved_count}개 IP 저장 ({processing_time:.2f}초)"
                )

        except Exception as e:
            logger.error(f"❌ 대용량 배치 처리 실패: {e}")

        return saved_count

    def _filter_invalid_ips(self, ip_data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
        """
        사설 IP 및 오탐 IP 필터링

        제외 대상:
        - 사설 IP 대역 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
        - Loopback (127.0.0.0/8)
        - Link-local (169.254.0.0/16)
        - 잘못된 IP 형식
        - Reserved IP
        """
        valid_ips = []
        excluded_count = 0

        for item in ip_data:
            ip_str = item.get("ip_address")
            if not ip_str:
                excluded_count += 1
                continue

            try:
                ip = ipaddress.ip_address(ip_str)

                # 사설 IP, Loopback, Link-local, Reserved 제외
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    excluded_count += 1
                    logger.debug(f"🚫 제외된 IP: {ip_str} (사설/예약 대역)")
                    continue

                # 유효한 공인 IP
                valid_ips.append(item)

            except ValueError:
                # 잘못된 IP 형식
                excluded_count += 1
                logger.debug(f"🚫 제외된 IP: {ip_str} (잘못된 형식)")
                continue

        logger.info(f"📊 IP 필터링: {len(valid_ips)}개 유효, {excluded_count}개 제외")
        return valid_ips, excluded_count

    def _memory_optimized_dedup(
        self, ip_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """메모리 최적화된 중복 제거 - 대용량 데이터 지원"""
        seen_ips = set()
        unique_data = []

        # 메모리 효율적인 중복 제거
        for item in ip_data:
            ip_addr = item.get("ip_address")
            if ip_addr and ip_addr not in seen_ips:
                seen_ips.add(ip_addr)
                unique_data.append(item)

                # 메모리 사용량 제한
                if len(unique_data) >= self._cache_max_size:
                    logger.warning(f"⚠️ 메모리 제한에 도달: {len(unique_data)}개 IP로 제한")
                    break

        return unique_data

    def _batch_check_existing_ips(self, ip_addresses: List[str]) -> set:
        """배치로 기존 IP 존재 여부 확인 - 성능 최적화"""
        if not ip_addresses:
            return set()

        existing_ips = set()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 대용량 IN 절 최적화
                batch_size = 1000
                for batch in self._get_batches(ip_addresses, batch_size):
                    placeholders = ",".join(["%s"] * len(batch))
                    query = f"""
                        SELECT DISTINCT ip_address 
                        FROM blacklist_ips 
                        WHERE ip_address IN ({placeholders})
                    """
                    cursor.execute(query, batch)
                    results = cursor.fetchall()
                    existing_ips.update(row[0] for row in results)

                cursor.close()

        except Exception as e:
            logger.error(f"기존 IP 확인 실패: {e}")

        return existing_ips

    def _get_batches(self, data: List[Any], batch_size: int):
        """메모리 효율적인 배치 분할"""
        for i in range(0, len(data), batch_size):
            yield data[i : i + batch_size]

    def _optimized_batch_insert(self, cursor, batch: List[Dict[str, Any]]) -> int:
        """최적화된 배치 삽입 - 직접 executemany 사용"""
        if not batch:
            return 0

        # 바로 fallback 메서드 사용 (COPY는 ON CONFLICT 지원 안함)
        return self._fallback_batch_insert(cursor, batch)

    def _fallback_batch_insert(self, cursor, batch: List[Dict[str, Any]]) -> int:
        """대체 배치 삽입 방식 - executemany (raw_data JSONB 포함)"""
        values = []
        for item in batch:
            # raw_data를 JSON 문자열로 변환
            raw_data_value = item.get("raw_data")
            if raw_data_value and isinstance(raw_data_value, dict):
                raw_data_json = json.dumps(raw_data_value, ensure_ascii=False)
            elif isinstance(raw_data_value, str):
                raw_data_json = raw_data_value
            else:
                # raw_data가 없으면 원본 item에서 관련 데이터 추출하여 저장
                raw_data_json = json.dumps({
                    "ip_address": item.get("ip_address"),
                    "country": item.get("country"),
                    "reason": item.get("reason"),
                    "detection_date": str(item.get("detection_date")) if item.get("detection_date") else None,
                    "removal_date": str(item.get("removal_date")) if item.get("removal_date") else None,
                    "confidence_level": item.get("confidence_level"),
                    "collection_timestamp": datetime.now().isoformat(),
                }, ensure_ascii=False)

            values.append(
                (
                    item.get("ip_address"),
                    item.get("reason", "Blacklist IP"),
                    item.get("source", "COLLECTOR"),
                    self._convert_confidence_to_int(item.get("confidence_level", 50)),
                    item.get("detection_count", 1),
                    item.get("last_seen", datetime.now()),
                    item.get("is_active", True),
                    datetime.now(),
                    datetime.now(),
                    self._convert_date_string(item.get("detection_date")),
                    self._convert_date_string(item.get("removal_date")),
                    item.get("country"),
                    raw_data_json,  # raw_data JSONB 추가
                )
            )

        try:
            cursor.executemany(
                """
                INSERT INTO blacklist_ips
                (ip_address, reason, source, confidence_level,
                 detection_count, last_seen, is_active, created_at, updated_at,
                 detection_date, removal_date, country, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ip_address, source) DO UPDATE SET
                    detection_count = blacklist_ips.detection_count + 1,
                    last_seen = EXCLUDED.last_seen,
                    updated_at = EXCLUDED.updated_at,
                    reason = EXCLUDED.reason,
                    country = COALESCE(EXCLUDED.country, blacklist_ips.country),
                    raw_data = EXCLUDED.raw_data
            """,
                values,
            )
            return cursor.rowcount
        except Exception as e:
            logger.error(f"배치 삽입 실패: {e}")
            return 0

    def _convert_confidence_to_int(self, confidence_value) -> int:
        """신뢰도 값을 정수로 변환"""
        if isinstance(confidence_value, int):
            return confidence_value
        elif isinstance(confidence_value, str):
            confidence_mapping = {
                "high": 90,
                "medium": 50,
                "low": 10,
                "critical": 95,
                "unknown": 5,
            }
            return confidence_mapping.get(confidence_value.lower(), 50)
        return 50

    def _convert_date_string(self, date_str):
        """날짜 문자열을 date 객체로 변환"""
        if not date_str or not isinstance(date_str, str):
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None

    def record_collection_history(
        self,
        source: str,
        success: bool,
        items_collected: int,
        execution_time_ms: int,
        error_message: str = None,
    ):
        """수집 히스토리 기록"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO collection_history
                    (service_name, success, items_collected, execution_time_ms, 
                     error_message, collection_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        source.lower(),
                        success,
                        items_collected,
                        execution_time_ms,
                        error_message,
                        datetime.now(),
                    ),
                )
                conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"수집 히스토리 기록 실패: {e}")

    def get_total_ip_count(self) -> int:
        """전체 IP 개수 반환 - 최초 수집 여부 확인용"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
                result = cursor.fetchone()
                cursor.close()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"총 IP 개수 조회 실패: {e}")
            return 0

    def get_collection_stats(self) -> Dict[str, Any]:
        """고성능 수집 통계 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 병렬 통계 쿼리 최적화
                cursor.execute(
                    """
                    WITH stats AS (
                        SELECT 
                            COUNT(*) as total_ips,
                            COUNT(*) FILTER (WHERE is_active = true) as active_ips,
                            MAX(created_at) as latest_collection
                        FROM blacklist_ips
                    ),
                    source_stats AS (
                        SELECT json_object_agg(source, cnt) as source_breakdown
                        FROM (
                            SELECT source, COUNT(*) as cnt 
                            FROM blacklist_ips 
                            GROUP BY source
                        ) s
                    )
                    SELECT s.total_ips, s.active_ips, s.latest_collection, 
                           ss.source_breakdown
                    FROM stats s CROSS JOIN source_stats ss
                """
                )

                result = cursor.fetchone()
                cursor.close()

                if result:
                    return {
                        "total_ips": result[0],
                        "active_ips": result[1],
                        "latest_collection": result[2],
                        "source_breakdown": result[3] or {},
                        "cache_size": len(self._ip_cache),
                        "performance_mode": "optimized",
                    }

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")

        return {}


# 전역 인스턴스
db_service = DatabaseService()
