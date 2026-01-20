"""
REGTECH Excel 다운로드 및 파싱
대량 데이터 수집을 위한 Excel 처리 모듈

Created: 2026-01-05 (Technical Debt Resolution)
Extracted from: regtech_collector.py
"""

import logging
import os
import subprocess
import urllib.parse
from typing import List, Dict, Any, Optional
import pandas as pd

from .regtech_parsers import parse_date, is_valid_ip

logger = logging.getLogger(__name__)


def download_excel_data(
    session,
    rate_limiter,
    proxy_url: Optional[str],
    base_url: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    """Excel 다운로드를 통한 대량 데이터 수집 (최대 3개월)"""
    try:
        download_url = f"{base_url}/fcti/securityAdvisory/advisoryListDownloadXlsx"

        request_data = {
            "tabSort": "blacklist",
            "excelDownload": "blacklist,",
            "startDate": start_date,
            "endDate": end_date,
            "findCondition": "all",
            "findKeyword": "",
            "excelDown": "blacklist",
        }

        headers = {
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://regtech.fsec.or.kr",
            "Referer": "https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryList",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        if not rate_limiter.wait_if_needed():
            logger.warning("⚠️ Rate Limiter 대기 실패")
            return []

        headers_list = []
        for k, v in headers.items():
            headers_list.extend(["-H", f"{k}: {v}"])

        cookie_header = "; ".join([f"{c.name}={c.value}" for c in session.cookies])
        if cookie_header:
            headers_list.extend(["-H", f"Cookie: {cookie_header}"])

        curl_cmd = (
            [
                "curl",
                "-s",
                "-X",
                "POST",
                download_url,
                "-o",
                "/tmp/regtech_data.xlsx",
            ]
            + headers_list
            + [
                "--data",
                urllib.parse.urlencode(request_data),
            ]
        )

        if proxy_url:
            curl_cmd.extend(["--proxy", proxy_url])

        logger.info(f"📥 Excel 다운로드 시작: {start_date} ~ {end_date}")

        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.error(f"❌ Excel 다운로드 실패: {result.stderr}")
            return []

        if not os.path.exists("/tmp/regtech_data.xlsx"):
            logger.error("❌ Excel 파일이 생성되지 않음")
            return []

        file_size = os.path.getsize("/tmp/regtech_data.xlsx")
        logger.info(f"📊 Excel 파일 크기: {file_size} bytes")

        if file_size < 1000:
            with open(
                "/tmp/regtech_data.xlsx", "r", encoding="utf-8", errors="ignore"
            ) as f:
                content = f.read(500)
                logger.warning(f"⚠️ 작은 파일 내용: {content[:200]}")
            return []

        return parse_excel_file("/tmp/regtech_data.xlsx")

    except Exception as e:
        logger.error(f"❌ Excel 다운로드 중 오류: {e}")
        return []


def parse_excel_file(file_path: str) -> List[Dict[str, Any]]:
    """Excel 파일 파싱"""
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        logger.info(f"📋 Excel 컬럼: {list(df.columns)}")
        logger.info(f"📋 Excel 행 수: {len(df)}")

        collected_data = []
        ip_column = None

        for col in df.columns:
            col_lower = str(col).lower()
            if "ip" in col_lower or "addr" in col_lower:
                ip_column = col
                break

        if not ip_column and len(df.columns) > 0:
            ip_column = df.columns[0]

        if ip_column is None:
            logger.error("❌ IP 컬럼을 찾을 수 없음")
            return []

        for _, row in df.iterrows():
            ip_value = str(row.get(ip_column, "")).strip()
            if not is_valid_ip(ip_value):
                continue

            country = ""
            reason = "REGTECH Excel Import"
            detection_date = None
            removal_date = None

            for col in df.columns:
                col_lower = str(col).lower()
                val = row.get(col)
                if pd.isna(val):
                    continue
                val_str = str(val).strip()

                if "국가" in col or "country" in col_lower:
                    country = val_str[:2].upper() if len(val_str) >= 2 else val_str
                elif "사유" in col or "reason" in col_lower or "이유" in col:
                    reason = val_str
                elif "탐지" in col or "등록" in col or "detect" in col_lower:
                    detection_date = parse_date(val_str)
                elif "해제" in col or "삭제" in col or "remov" in col_lower:
                    removal_date = parse_date(val_str)

            item = {
                "ip_address": ip_value,
                "source": "REGTECH",
                "reason": reason,
                "country": country,
                "detection_date": detection_date,
                "removal_date": removal_date,
                "is_active": True,
                "raw_data": {"excel_import": True},
            }
            collected_data.append(item)

        logger.info(f"✅ Excel에서 {len(collected_data)}개 IP 추출")
        return collected_data

    except Exception as e:
        logger.error(f"❌ Excel 파싱 실패: {e}")
        return []
