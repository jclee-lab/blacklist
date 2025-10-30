"""
Multi-Source Threat Intelligence Collector
다중 소스 위협 정보 수집기 - 넓은 범위 수집을 위한 통합 시스템
"""

import logging
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time
import json

from collector.core.regtech_collector import regtech_collector
from collector.config import CollectorConfig

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """위협 정보 소스 타입"""

    REGTECH = "regtech"  # 한국 금융보안원
    ABUSE_CH = "abuse_ch"  # Abuse.ch 위협 피드
    MALWARE_BAZAAR = "malware_bazaar"  # Malware Bazaar
    URLHAUS = "urlhaus"  # URLhaus
    PHISHTANK = "phishtank"  # PhishTank
    OPENPHISH = "openphish"  # OpenPhish
    VIRUSTOTAL = "virustotal"  # VirusTotal
    ALIENVAULT = "alienvault"  # AlienVault OTX
    THREATFOX = "threatfox"  # ThreatFox
    FEODO = "feodo"  # Feodo Tracker
    CUSTOM_API = "custom_api"  # 사용자 정의 API
    RSS_FEED = "rss_feed"  # RSS 피드
    CSV_FILE = "csv_file"  # CSV 파일
    JSON_API = "json_api"  # JSON API


@dataclass
class SourceConfig:
    """소스 설정"""

    source_type: SourceType
    name: str
    url: str
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    enabled: bool = True
    priority: int = 1  # 1=최고, 5=최저
    rate_limit: float = 1.0  # 초당 요청 수
    timeout: int = 30
    retry_count: int = 3
    data_format: str = "json"  # json, xml, csv, text
    ip_field: str = "ip"
    date_field: Optional[str] = None
    reason_field: Optional[str] = None
    confidence_boost: int = 0  # 신뢰도 추가점
    category: str = "malicious"


class MultiSourceCollector:
    """다중 소스 위협 정보 수집기"""

    def __init__(self):
        self.sources: Dict[str, SourceConfig] = {}
        self.collection_stats = {
            "total_sources": 0,
            "active_sources": 0,
            "total_collected": 0,
            "collection_history": [],
        }
        self._setup_default_sources()

    def _setup_default_sources(self):
        """기본 위협 정보 소스 설정"""

        # 1. 기존 REGTECH (최고 우선순위)
        self.add_source(
            SourceConfig(
                source_type=SourceType.REGTECH,
                name="한국 금융보안원 REGTECH",
                url="https://regtech.fsec.or.kr",
                priority=1,
                rate_limit=0.5,
                confidence_boost=20,
            )
        )

        # 2. Abuse.ch URLhaus (URL 기반 위협)
        self.add_source(
            SourceConfig(
                source_type=SourceType.URLHAUS,
                name="URLhaus Malware URLs",
                url="https://urlhaus-api.abuse.ch/v1/payloads/recent/",
                priority=2,
                rate_limit=2.0,
                data_format="json",
                ip_field="url_host",
                confidence_boost=15,
            )
        )

        # 3. ThreatFox IOCs
        self.add_source(
            SourceConfig(
                source_type=SourceType.THREATFOX,
                name="ThreatFox IOCs",
                url="https://threatfox-api.abuse.ch/api/v1/",
                priority=2,
                rate_limit=2.0,
                data_format="json",
                ip_field="ioc",
                confidence_boost=15,
            )
        )

        # 4. Feodo Tracker (봇넷 C&C)
        self.add_source(
            SourceConfig(
                source_type=SourceType.FEODO,
                name="Feodo Tracker Botnet C&C",
                url="https://feodotracker.abuse.ch/downloads/ipblocklist_recommended.txt",
                priority=2,
                rate_limit=1.0,
                data_format="text",
                confidence_boost=18,
                category="botnet",
            )
        )

        # 5. PhishTank (피싱)
        self.add_source(
            SourceConfig(
                source_type=SourceType.PHISHTANK,
                name="PhishTank Phishing URLs",
                url="http://data.phishtank.com/data/online-valid.json",
                priority=3,
                rate_limit=0.2,  # 제한적
                data_format="json",
                ip_field="url",
                confidence_boost=10,
                category="phishing",
            )
        )

        # 6. OpenPhish
        self.add_source(
            SourceConfig(
                source_type=SourceType.OPENPHISH,
                name="OpenPhish Feed",
                url="https://openphish.com/feed.txt",
                priority=3,
                rate_limit=1.0,
                data_format="text",
                confidence_boost=8,
                category="phishing",
            )
        )

        # 7. Custom API 예시 (사용자 확장 가능)
        self.add_source(
            SourceConfig(
                source_type=SourceType.CUSTOM_API,
                name="Custom Threat Feed",
                url="https://example.com/threat-feed",
                priority=4,
                enabled=False,  # 기본 비활성화
                rate_limit=1.0,
                headers={"X-API-Key": "YOUR_API_KEY"},
                confidence_boost=5,
            )
        )

        logger.info(f"📋 기본 위협 정보 소스 {len(self.sources)}개 설정 완료")

    def add_source(self, source_config: SourceConfig):
        """새 소스 추가"""
        source_id = (
            f"{source_config.source_type.value}_{source_config.name.replace(' ', '_')}"
        )
        self.sources[source_id] = source_config

        if source_config.enabled:
            self.collection_stats["active_sources"] += 1
        self.collection_stats["total_sources"] += 1

        logger.info(
            f"➕ 위협 정보 소스 추가: {source_config.name} ({source_config.source_type.value})"
        )

    async def collect_from_all_sources(
        self,
        max_ips_per_source: int = 50000,
        parallel_sources: int = 5,
        date_range_days: int = 7,
    ) -> Dict[str, Any]:
        """모든 활성화된 소스에서 병렬 수집"""

        collection_start = time.time()
        logger.info(f"🚀 다중 소스 넓은 범위 수집 시작")
        logger.info(f"📊 설정: 소스당 최대 {max_ips_per_source:,}개, 병렬 {parallel_sources}개")

        # 활성화된 소스 필터링 및 우선순위 정렬
        active_sources = [
            (source_id, config)
            for source_id, config in self.sources.items()
            if config.enabled
        ]
        active_sources.sort(key=lambda x: x[1].priority)

        collected_results = {}
        total_collected = 0

        # 병렬 수집 실행
        semaphore = asyncio.Semaphore(parallel_sources)

        async def collect_from_source(source_id: str, config: SourceConfig):
            async with semaphore:
                try:
                    logger.info(f"🔄 소스 수집 시작: {config.name}")

                    if config.source_type == SourceType.REGTECH:
                        # 기존 REGTECH 수집기 사용
                        result = await self._collect_regtech_async(
                            max_ips_per_source, date_range_days
                        )
                    else:
                        # 새로운 소스 수집
                        result = await self._collect_from_external_source(
                            source_id, config, max_ips_per_source
                        )

                    collected_results[source_id] = result
                    logger.info(f"✅ {config.name}: {len(result.get('data', []))}개 수집")

                    return result

                except Exception as e:
                    logger.error(f"❌ {config.name} 수집 실패: {e}")
                    collected_results[source_id] = {
                        "success": False,
                        "error": str(e),
                        "data": [],
                    }
                    return {"success": False, "error": str(e), "data": []}

        # 모든 소스에서 병렬 수집
        tasks = [
            collect_from_source(source_id, config)
            for source_id, config in active_sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 통합 및 중복 제거
        all_collected_data = []
        source_stats = {}

        for (source_id, config), result in zip(active_sources, results):
            if isinstance(result, Exception):
                logger.error(f"❌ {config.name} 수집 예외: {result}")
                source_stats[source_id] = {"collected": 0, "error": str(result)}
                continue

            if isinstance(result, dict) and result.get("success"):
                source_data = result.get("data", [])
                all_collected_data.extend(source_data)
                source_stats[source_id] = {
                    "collected": len(source_data),
                    "source_name": config.name,
                    "confidence_boost": config.confidence_boost,
                }
            else:
                error_msg = (
                    result.get("error", "알 수 없는 오류")
                    if isinstance(result, dict)
                    else str(result)
                )
                source_stats[source_id] = {"collected": 0, "error": error_msg}

        # 중복 제거 및 데이터 품질 향상
        unique_data = self._deduplicate_and_enhance(all_collected_data)
        total_collected = len(unique_data)

        collection_time = time.time() - collection_start

        # 수집 결과 통계
        collection_result = {
            "success": True,
            "total_collected": total_collected,
            "unique_ips": len(set(item.get("ip_address") for item in unique_data)),
            "sources_attempted": len(active_sources),
            "sources_successful": len(
                [s for s in source_stats.values() if "error" not in s]
            ),
            "collection_time_seconds": round(collection_time, 2),
            "source_breakdown": source_stats,
            "data": unique_data,
            "timestamp": datetime.now().isoformat(),
        }

        # 수집 이력 업데이트
        self.collection_stats["total_collected"] += total_collected
        self.collection_stats["collection_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "total_collected": total_collected,
                "sources_used": len(active_sources),
                "collection_time": collection_time,
            }
        )

        logger.info(f"🎯 다중 소스 수집 완료: {total_collected:,}개 IP, {collection_time:.2f}초")
        return collection_result

    async def _collect_regtech_async(
        self, max_ips: int, date_range_days: int
    ) -> Dict[str, Any]:
        """REGTECH 비동기 수집"""
        loop = asyncio.get_event_loop()

        def sync_collect():
            try:
                # 기존 인증 확인
                if not regtech_collector.authenticated:
                    username = CollectorConfig.REGTECH_ID
                    password = CollectorConfig.REGTECH_PW
                    if not regtech_collector.authenticate(username, password):
                        return {"success": False, "error": "REGTECH 인증 실패", "data": []}

                # 날짜 범위 계산
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (
                    datetime.now() - timedelta(days=date_range_days)
                ).strftime("%Y-%m-%d")

                # 데이터 수집
                collected_data = regtech_collector.collect_blacklist_data(
                    page_size=2000,
                    start_date=start_date,
                    end_date=end_date,
                    max_pages=max_ips // 2000 + 1,
                )

                # 최대 개수 제한
                if len(collected_data) > max_ips:
                    collected_data = collected_data[:max_ips]

                return {
                    "success": True,
                    "data": collected_data,
                    "source": "REGTECH",
                    "collection_params": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "max_pages": max_ips // 2000 + 1,
                    },
                }

            except Exception as e:
                return {"success": False, "error": str(e), "data": []}

        return await loop.run_in_executor(None, sync_collect)

    async def _collect_from_external_source(
        self, source_id: str, config: SourceConfig, max_ips: int
    ) -> Dict[str, Any]:
        """외부 소스에서 데이터 수집"""
        import aiohttp

        try:
            # Rate limiting
            await asyncio.sleep(1.0 / config.rate_limit)

            headers = config.headers or {}
            params = config.params or {}

            timeout = aiohttp.ClientTimeout(total=config.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                if config.source_type == SourceType.THREATFOX:
                    # ThreatFox API 특별 처리
                    post_data = {"query": "get_iocs", "days": 7}
                    async with session.post(
                        config.url, json=post_data, headers=headers
                    ) as response:
                        data = await response.json()
                        return self._parse_threatfox_data(data, config, max_ips)

                elif config.data_format == "text":
                    # 텍스트 기반 피드 (Feodo, OpenPhish 등)
                    async with session.get(
                        config.url, headers=headers, params=params
                    ) as response:
                        text_data = await response.text()
                        return self._parse_text_feed(text_data, config, max_ips)

                elif config.data_format == "json":
                    # JSON 기반 피드
                    async with session.get(
                        config.url, headers=headers, params=params
                    ) as response:
                        json_data = await response.json()
                        return self._parse_json_feed(json_data, config, max_ips)

                else:
                    return {
                        "success": False,
                        "error": f"지원하지 않는 데이터 형식: {config.data_format}",
                        "data": [],
                    }

        except Exception as e:
            logger.error(f"❌ {config.name} 수집 오류: {e}")
            return {"success": False, "error": str(e), "data": []}

    def _parse_threatfox_data(
        self, data: Dict, config: SourceConfig, max_ips: int
    ) -> Dict[str, Any]:
        """ThreatFox 데이터 파싱"""
        collected_ips = []

        try:
            if data.get("query_status") == "ok":
                iocs = data.get("data", [])

                for ioc_data in iocs[:max_ips]:
                    ioc_value = ioc_data.get("ioc")
                    ioc_type = ioc_data.get("ioc_type", "")

                    # IP 주소만 필터링
                    if ioc_type in ["ip:port", "ip"] and self._is_valid_ip(
                        ioc_value.split(":")[0]
                    ):
                        ip_address = ioc_value.split(":")[0]

                        collected_ips.append(
                            {
                                "ip_address": ip_address,
                                "source": config.name,
                                "reason": ioc_data.get("threat_type", "ThreatFox IOC"),
                                "category": self._determine_category_from_threat_type(
                                    ioc_data.get("threat_type", "")
                                ),
                                "confidence_level": 70 + config.confidence_boost,
                                "detection_count": 1,
                                "is_active": True,
                                "last_seen": datetime.now(),
                                "detection_date": ioc_data.get("first_seen", "")[:10]
                                if ioc_data.get("first_seen")
                                else None,
                                "malware_family": ioc_data.get("malware", ""),
                                "threat_type": ioc_data.get("threat_type", ""),
                            }
                        )

            return {"success": True, "data": collected_ips}

        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def _parse_text_feed(
        self, text_data: str, config: SourceConfig, max_ips: int
    ) -> Dict[str, Any]:
        """텍스트 피드 파싱 (IP 목록)"""
        collected_ips = []

        try:
            lines = text_data.strip().split("\n")
            ip_count = 0

            for line in lines:
                if ip_count >= max_ips:
                    break

                line = line.strip()

                # 주석이나 빈 줄 건너뛰기
                if not line or line.startswith("#") or line.startswith("//"):
                    continue

                # URL에서 호스트 추출 (OpenPhish의 경우)
                if line.startswith("http"):
                    try:
                        from urllib.parse import urlparse

                        parsed = urlparse(line)
                        potential_ip = parsed.hostname
                    except:
                        potential_ip = line
                else:
                    potential_ip = line.split(":")[0]  # 포트 제거

                if self._is_valid_ip(potential_ip):
                    collected_ips.append(
                        {
                            "ip_address": potential_ip,
                            "source": config.name,
                            "reason": f"{config.name} 위협 목록",
                            "category": config.category,
                            "confidence_level": 65 + config.confidence_boost,
                            "detection_count": 1,
                            "is_active": True,
                            "last_seen": datetime.now(),
                            "original_entry": line,
                        }
                    )
                    ip_count += 1

            return {"success": True, "data": collected_ips}

        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def _parse_json_feed(
        self, json_data: Any, config: SourceConfig, max_ips: int
    ) -> Dict[str, Any]:
        """JSON 피드 파싱"""
        collected_ips = []

        try:
            # 데이터 구조 분석
            if isinstance(json_data, list):
                data_items = json_data
            elif isinstance(json_data, dict):
                # 일반적인 JSON 구조들 시도
                data_items = (
                    json_data.get("data")
                    or json_data.get("results")
                    or json_data.get("items")
                    or json_data.get("entries")
                    or [json_data]
                )
            else:
                data_items = []

            ip_count = 0
            for item in data_items:
                if ip_count >= max_ips:
                    break

                if not isinstance(item, dict):
                    continue

                # IP 주소 추출
                ip_address = None
                for field in [
                    config.ip_field,
                    "ip",
                    "ip_address",
                    "host",
                    "target",
                    "url",
                ]:
                    if field in item:
                        ip_candidate = str(item[field])

                        # URL에서 호스트 추출
                        if ip_candidate.startswith("http"):
                            try:
                                from urllib.parse import urlparse

                                parsed = urlparse(ip_candidate)
                                ip_candidate = parsed.hostname
                            except:
                                continue

                        if self._is_valid_ip(ip_candidate):
                            ip_address = ip_candidate
                            break

                if ip_address:
                    # 추가 정보 추출
                    reason = item.get(
                        config.reason_field or "description", f"{config.name} 위협"
                    )
                    detection_date = item.get(config.date_field or "date", "")

                    collected_ips.append(
                        {
                            "ip_address": ip_address,
                            "source": config.name,
                            "reason": reason,
                            "category": config.category,
                            "confidence_level": 60 + config.confidence_boost,
                            "detection_count": 1,
                            "is_active": True,
                            "last_seen": datetime.now(),
                            "detection_date": detection_date[:10]
                            if detection_date
                            else None,
                            "raw_data": json.dumps(item)[:500],  # 원본 데이터 일부
                        }
                    )
                    ip_count += 1

            return {"success": True, "data": collected_ips}

        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def _determine_category_from_threat_type(self, threat_type: str) -> str:
        """위협 타입에서 카테고리 결정"""
        threat_lower = threat_type.lower()

        if any(keyword in threat_lower for keyword in ["botnet", "c2", "command"]):
            return "botnet"
        elif any(keyword in threat_lower for keyword in ["phishing", "phish"]):
            return "phishing"
        elif any(keyword in threat_lower for keyword in ["malware", "trojan", "rat"]):
            return "malware"
        elif any(keyword in threat_lower for keyword in ["spam", "bulk"]):
            return "spam"
        else:
            return "malicious"

    def _is_valid_ip(self, ip_str: str) -> bool:
        """IP 주소 유효성 검사"""
        try:
            import ipaddress

            if not ip_str:
                return False

            ip_obj = ipaddress.ip_address(ip_str.strip())

            # 사설 IP 및 특수 IP 필터링
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
                return False

            return True

        except ValueError:
            return False

    def _deduplicate_and_enhance(
        self, all_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """중복 제거 및 데이터 품질 향상"""

        # IP 주소별 그룹화
        ip_groups = {}
        for item in all_data:
            ip = item.get("ip_address")
            if ip:
                if ip not in ip_groups:
                    ip_groups[ip] = []
                ip_groups[ip].append(item)

        enhanced_data = []

        for ip, items in ip_groups.items():
            if len(items) == 1:
                # 단일 소스
                enhanced_data.append(items[0])
            else:
                # 다중 소스 - 정보 병합
                merged_item = self._merge_multiple_sources(items)
                enhanced_data.append(merged_item)

        return enhanced_data

    def _merge_multiple_sources(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """다중 소스 정보 병합"""
        # 기준 아이템 (가장 높은 신뢰도)
        base_item = max(items, key=lambda x: x.get("confidence_level", 0))

        # 소스 목록
        sources = [item.get("source", "Unknown") for item in items]

        # 탐지 횟수 합계
        total_detections = sum(item.get("detection_count", 1) for item in items)

        # 평균 신뢰도 (가중평균)
        total_confidence = sum(item.get("confidence_level", 0) for item in items)
        avg_confidence = min(
            100, int(total_confidence / len(items)) + len(items) * 2
        )  # 다중 소스 보너스

        # 가장 상세한 이유
        best_reason = max(items, key=lambda x: len(x.get("reason", "")))["reason"]

        # 가장 이른 탐지일
        detection_dates = [
            item.get("detection_date") for item in items if item.get("detection_date")
        ]
        earliest_date = min(detection_dates) if detection_dates else None

        # 병합된 아이템
        merged = base_item.copy()
        merged.update(
            {
                "source": f"Multi-Source ({len(sources)}개)",
                "sources": sources,
                "reason": best_reason,
                "confidence_level": avg_confidence,
                "detection_count": total_detections,
                "detection_date": earliest_date,
                "multi_source": True,
                "source_count": len(sources),
            }
        )

        return merged

    def get_source_status(self) -> Dict[str, Any]:
        """소스 상태 정보"""
        active_sources = []
        inactive_sources = []

        for source_id, config in self.sources.items():
            source_info = {
                "id": source_id,
                "name": config.name,
                "type": config.source_type.value,
                "priority": config.priority,
                "rate_limit": config.rate_limit,
                "confidence_boost": config.confidence_boost,
            }

            if config.enabled:
                active_sources.append(source_info)
            else:
                inactive_sources.append(source_info)

        return {
            "total_sources": len(self.sources),
            "active_sources": len(active_sources),
            "inactive_sources": len(inactive_sources),
            "active_source_list": active_sources,
            "inactive_source_list": inactive_sources,
            "collection_stats": self.collection_stats,
        }

    def enable_source(self, source_type: str, enabled: bool = True):
        """소스 활성화/비활성화"""
        for source_id, config in self.sources.items():
            if source_type.lower() in source_id.lower():
                config.enabled = enabled
                logger.info(
                    f"{'✅' if enabled else '❌'} 소스 {config.name} {'활성화' if enabled else '비활성화'}"
                )
                return True
        return False

    def add_custom_source(
        self,
        name: str,
        url: str,
        source_type: SourceType = SourceType.CUSTOM_API,
        **kwargs,
    ) -> bool:
        """사용자 정의 소스 추가"""
        try:
            config = SourceConfig(source_type=source_type, name=name, url=url, **kwargs)
            self.add_source(config)
            return True
        except Exception as e:
            logger.error(f"❌ 사용자 정의 소스 추가 실패: {e}")
            return False


# 전역 인스턴스
multi_source_collector = MultiSourceCollector()
