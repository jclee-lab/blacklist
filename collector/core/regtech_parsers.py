"""
REGTECH 파싱 유틸리티
날짜, IP, 국가코드, HTML 파싱 함수

Created: 2026-01-05 (Technical Debt Resolution)
Extracted from: regtech_collector.py
"""

import logging
import ipaddress
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_date(date_str: Any) -> Optional[str]:
    """날짜 문자열 파싱 - 향상된 처리 및 로깅"""
    if not date_str:
        return None

    logger.debug(f"📅 날짜 파싱 시도: '{date_str}' (타입: {type(date_str)})")

    date_str_clean = str(date_str).strip()

    date_formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y%m%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
    ]

    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str_clean, fmt)
            result = parsed_date.strftime("%Y-%m-%d")
            logger.debug(f"✅ 날짜 파싱 성공: '{date_str}' -> '{result}' (형식: {fmt})")
            return result
        except ValueError:
            continue

    logger.warning(f"❌ 날짜 파싱 실패: '{date_str}' - 지원되지 않는 형식")
    return None


def is_valid_ip(ip_str: str) -> bool:
    """IP 주소 유효성 검사 - 향상된 검증"""
    try:
        ip_obj = ipaddress.ip_address(ip_str.strip())

        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
            return False

        return True

    except ValueError:
        return False


def normalize_country_code(country_value: Any) -> Optional[str]:
    """국가 코드 정규화"""
    if not country_value:
        return None

    country_str = str(country_value).upper().strip()

    country_mapping = {
        "KR": "KR",
        "KOREA": "KR",
        "한국": "KR",
        "US": "US",
        "USA": "US",
        "UNITED STATES": "US",
        "CN": "CN",
        "CHINA": "CN",
        "중국": "CN",
        "JP": "JP",
        "JAPAN": "JP",
        "일본": "JP",
    }

    return country_mapping.get(
        country_str, country_str[:2] if len(country_str) >= 2 else None
    )


def extract_country_info(cell_texts: List[str]) -> Optional[str]:
    """HTML 테이블 행에서 국가 정보 추출"""
    if not cell_texts:
        return None

    country_patterns = {
        "KR": ["KR", "Korea", "한국", "South Korea", "Republic of Korea"],
        "US": ["US", "USA", "United States", "미국", "America"],
        "CN": ["CN", "China", "중국", "CHN"],
        "JP": ["JP", "Japan", "일본", "JPN"],
        "RU": ["RU", "Russia", "러시아", "Russian"],
        "DE": ["DE", "Germany", "독일", "German"],
        "FR": ["FR", "France", "프랑스", "French"],
        "GB": ["GB", "UK", "United Kingdom", "영국", "Britain"],
        "IN": ["IN", "India", "인도", "Indian"],
    }

    for cell_text in cell_texts:
        if not cell_text or len(cell_text.strip()) < 2:
            continue

        cell_upper = cell_text.upper().strip()

        for country_code, patterns in country_patterns.items():
            for pattern in patterns:
                if pattern.upper() in cell_upper:
                    logger.debug(f"✅ 국가 정보 발견: '{cell_text}' -> {country_code}")
                    return country_code

        if len(cell_text.strip()) == 2 and cell_text.strip().isalpha():
            country_code = cell_text.strip().upper()
            logger.debug(f"✅ 국가 코드 발견: {country_code}")
            return country_code

    return None


def determine_confidence(item: Dict[str, Any]) -> int:
    """신뢰도 결정 - 향상된 평가"""
    base_confidence = 80

    threat_level = str(item.get("threatLevel", "medium")).lower()
    threat_adjustments = {"critical": 15, "high": 10, "medium": 0, "low": -10}

    confidence = base_confidence + threat_adjustments.get(threat_level, 0)

    if item.get("verified"):
        confidence += 5
    if item.get("reportCount", 0) > 10:
        confidence += 5

    return max(10, min(100, confidence))


def parse_html_response(html_content: str) -> List[Dict[str, Any]]:
    """HTML 응답에서 블랙리스트 IP 데이터 추출"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        collected_data = []

        rows = soup.find_all("tr")
        logger.info(f"🔍 Total {len(rows)} table rows found")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            ip_text = cells[0].get_text(strip=True)
            if not is_valid_ip(ip_text):
                continue

            try:
                ip_address = ip_text
                country = cells[1].get_text(strip=True)

                reason_cell = cells[2]
                reason_link = reason_cell.find("a")
                if reason_link:
                    reason = reason_link.get_text(strip=True)
                else:
                    reason = reason_cell.get_text(strip=True)

                detection_date = parse_date(cells[3].get_text(strip=True))
                removal_date = (
                    parse_date(cells[4].get_text(strip=True))
                    if len(cells) > 4
                    else None
                )

                if not reason or reason == "-":
                    reason = "REGTECH Suspicious IP"

                item = {
                    "ip_address": ip_address,
                    "source": "REGTECH",
                    "reason": reason,
                    "confidence_level": 85,
                    "detection_count": 1,
                    "is_active": True,
                    "detection_date": detection_date,
                    "removal_date": removal_date,
                    "last_seen": datetime.now(),
                    "country": country,
                    "raw_data": {
                        "row_data": [c.get_text(strip=True) for c in cells[:6]],
                        "collection_timestamp": datetime.now().isoformat(),
                    },
                }
                collected_data.append(item)
                logger.debug(f"✅ Extracted: {ip_address} ({reason})")

            except Exception as row_err:
                logger.warning(f"⚠️ Row parse error: {row_err}")

        logger.info(f"📄 HTML parse complete: {len(collected_data)} IPs extracted")
        return collected_data

    except Exception as e:
        logger.error(f"❌ HTML parse fatal error: {e}")
        return []
