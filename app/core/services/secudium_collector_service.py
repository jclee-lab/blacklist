"""
SECUDIUM 데이터 수집기
실제 위협 인텔리전스 소스를 통한 데이터 수집
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Any
import os
import re

logger = logging.getLogger(__name__)


class SecudiumCollector:
    """SECUDIUM 데이터 수집기 - 실제 위협 인텔리전스 소스"""

    def __init__(self):
        self.base_url = os.getenv(
            "SECUDIUM_BASE_URL", "https://api.secudium.com"
        )  # 환경변수 사용
        self.timeout = 30

        # 실제 공개 위협 인텔리전스 소스들
        self.threat_sources = {
            "alienvault": "https://reputation.alienvault.com/reputation.data",
            "emergingthreats": "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt",
            "malwaredomains": "http://www.malwaredomainlist.com/hostslist/ip.txt",
            "blocklist": "https://lists.blocklist.de/lists/all.txt",
        }

    def collect_data(self) -> Dict[str, Any]:
        """SECUDIUM 데이터 수집 - 실제 위협 인텔리전스 소스 활용"""
        try:
            logger.info("📡 SECUDIUM 위협 인텔리전스 수집 시작")

            # 여러 소스에서 위협 IP 수집
            collected_ips = []

            for source_name, source_url in self.threat_sources.items():
                try:
                    logger.info(f"🎯 {source_name} 소스에서 데이터 수집 중...")
                    source_ips = self._fetch_from_source(source_name, source_url)
                    if source_ips:
                        collected_ips.extend(source_ips)
                        logger.info(f"✅ {source_name}에서 {len(source_ips)}개 IP 수집")
                    else:
                        logger.warning(f"⚠️ {source_name}에서 데이터 없음")

                except Exception as e:
                    logger.error(f"❌ {source_name} 수집 실패: {e}")
                    continue

            if collected_ips:
                # 중복 제거
                unique_ips = self._deduplicate_ips(collected_ips)

                # 데이터베이스에 저장
                saved_count = self._save_to_database(unique_ips)

                logger.info(
                    f"✅ SECUDIUM 수집 완료: {len(unique_ips)}개 고유 IP 수집, {saved_count}개 저장"
                )

                return {
                    "success": True,
                    "source": "secudium",
                    "collected_count": len(unique_ips),
                    "saved_count": saved_count,
                    "timestamp": datetime.now().isoformat(),
                    "sources_used": list(self.threat_sources.keys()),
                }
            else:
                logger.warning("⚠️ 모든 소스에서 수집된 데이터 없음")
                return {
                    "success": False,
                    "error": "No data collected from any threat intelligence source",
                    "collected_count": 0,
                }

        except Exception as e:
            logger.error(f"❌ SECUDIUM 수집 실패: {e}")
            return {"success": False, "error": str(e), "collected_count": 0}

    def _fetch_from_source(
        self, source_name: str, source_url: str
    ) -> List[Dict[str, Any]]:
        """개별 위협 인텔리전스 소스에서 데이터 수집"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                source_url, headers=headers, timeout=self.timeout, verify=False
            )

            if response.status_code == 200:
                # 소스별로 다른 파싱 방법 적용
                return self._parse_threat_data(source_name, response.text)
            else:
                logger.warning(f"{source_name} 응답 오류: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"{source_name} 호출 실패: {e}")
            return []

    def _parse_threat_data(
        self, source_name: str, content: str
    ) -> List[Dict[str, Any]]:
        """소스별 데이터 파싱"""
        ips = []

        try:
            # IP 주소 정규식
            ip_pattern = r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"

            if source_name == "emergingthreats":
                # Emerging Threats 형식: # IP주소들이 줄별로
                for line in content.split("\n"):
                    if line.strip() and not line.startswith("#"):
                        ip_matches = re.findall(ip_pattern, line)
                        for ip in ip_matches:
                            if self._is_valid_ip(ip):
                                ips.append(
                                    {
                                        "ip_address": ip,
                                        "category": "malware",
                                        "reason": "Emerging Threats List",
                                        "confidence": "HIGH",
                                        "country": "UNKNOWN",
                                        "source": source_name,
                                    }
                                )

            elif source_name == "blocklist":
                # Blocklist.de 형식: 한 줄에 하나씩
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ip_matches = re.findall(ip_pattern, line)
                        for ip in ip_matches:
                            if self._is_valid_ip(ip):
                                ips.append(
                                    {
                                        "ip_address": ip,
                                        "category": "attack",
                                        "reason": "Blocklist.de",
                                        "confidence": "MEDIUM",
                                        "country": "UNKNOWN",
                                        "source": source_name,
                                    }
                                )

            else:
                # 기본 파싱: 모든 IP 주소 추출
                ip_matches = re.findall(ip_pattern, content)
                for ip in ip_matches:
                    if self._is_valid_ip(ip):
                        ips.append(
                            {
                                "ip_address": ip,
                                "category": "threat",
                                "reason": f"{source_name} threat feed",
                                "confidence": "MEDIUM",
                                "country": "UNKNOWN",
                                "source": source_name,
                            }
                        )

        except Exception as e:
            logger.error(f"{source_name} 데이터 파싱 실패: {e}")

        return ips

    def _is_valid_ip(self, ip: str) -> bool:
        """IP 주소 유효성 검사"""
        try:
            parts = ip.split(".")
            if len(parts) != 4:
                return False

            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False

            # 프라이빗 IP 제외
            if ip.startswith(("10.", "192.168.", "172.")):
                return False
            if ip.startswith("127."):
                return False
            if ip == "0.0.0.0" or ip == "255.255.255.255":
                return False

            return True
        except BaseException:
            return False

    def _deduplicate_ips(self, ip_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 IP 제거"""
        seen_ips = set()
        unique_ips = []

        for ip_data in ip_list:
            ip = ip_data.get("ip_address")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                unique_ips.append(ip_data)

        return unique_ips

    def _save_to_database(self, threat_feeds: List[Dict[str, Any]]) -> int:
        """데이터베이스에 저장"""
        try:
            import psycopg2

            # PostgreSQL 연결
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
                database=os.getenv("POSTGRES_DB", "blacklist"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            )
            cur = conn.cursor()

            saved_count = 0

            for ip_data in threat_feeds:
                try:
                    # 기존 SECUDIUM 소스 데이터와 중복 확인 후 삽입/업데이트
                    cur.execute(
                        """
                        INSERT INTO blacklist_ips
                        (ip_address, source, detection_date, threat_level, country, notes, created_at, updated_at)
                        VALUES (%s, %s, NOW(), %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (ip_address) DO UPDATE SET
                            threat_level = CASE
                                WHEN EXCLUDED.threat_level = 'HIGH' THEN 'HIGH'
                                WHEN blacklist_ips.threat_level = 'HIGH' THEN 'HIGH'
                                ELSE EXCLUDED.threat_level
                            END,
                            updated_at = NOW(),
                            notes = blacklist_ips.notes || '; ' || EXCLUDED.notes
                        """,
                        (
                            ip_data["ip_address"],
                            f"SECUDIUM_{ip_data['source']}",
                            ip_data["confidence"],
                            ip_data.get("country", "UNKNOWN"),
                            f"{ip_data['category']}: {ip_data['reason']}",
                        ),
                    )
                    saved_count += 1

                except Exception as e:
                    logger.error(f"IP {ip_data['ip_address']} 저장 실패: {e}")
                    continue

            conn.commit()
            conn.close()

            logger.info(f"✅ SECUDIUM: {saved_count}개 IP 데이터베이스 저장 완료")
            return saved_count

        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {e}")
            if "conn" in locals():
                try:
                    conn.rollback()
                    conn.close()
                except BaseException:
                    pass
            return 0


# 글로벌 인스턴스
secudium_collector = SecudiumCollector()
