"""
REGTECH Collector Service
REGTECH 포털에서 블랙리스트 IP 수집

Refactored: 2026-01-05 (Technical Debt Resolution)
- Extracted: regtech_parsers.py (파싱 유틸리티)
- Extracted: regtech_excel.py (Excel 다운로드/파싱)
"""

import logging
import requests
from requests.adapters import HTTPAdapter
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from collector.config import CollectorConfig
from core.rate_limiter import regtech_rate_limiter, auth_rate_limiter
from core.regtech_parsers import (
    parse_html_response,
)
from core.regtech_excel import download_excel_data

logger = logging.getLogger(__name__)


class RegtechCollector:
    """고성능 REGTECH 수집기 클래스 - 최적화된 수집 및 처리"""

    def __init__(self):
        self.base_url = CollectorConfig.REGTECH_BASE_URL
        self.session = requests.Session()

        self.proxy_url = os.getenv("WARP_PROXY_URL")
        if self.proxy_url:
            self.session.proxies = {"http": self.proxy_url, "https": self.proxy_url}
            logger.info(f"🌐 WARP 프록시 활성화: {self.proxy_url}")

        # 성능 최적화 설정
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/login/loginForm",
            }
        )

        # 세션 최적화
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=3, pool_block=False)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.authenticated = False
        self._data_cache = {}
        self._auth_cache = {}
        self._cache_ttl = 3600
        self._jwt_expiry: Optional[float] = None
        self._last_credentials: Optional[tuple] = None

        self.rate_limiter = regtech_rate_limiter
        self.auth_rate_limiter = auth_rate_limiter
        logger.info("🚦 Rate Limiter 통합: API 차단 방지 활성화")

    def _find_member(self, username: str) -> Optional[str]:
        """사용자 ID로 내부 member_id 조회 (1단계 인증)"""
        try:
            url = f"{self.base_url}/login/findOneMember"
            data = {"username": username}

            logger.info(f"🔍 사용자 조회 시도: {username}")
            response = self.session.post(url, json=data, timeout=10)

            if response.status_code == 200:
                try:
                    result = response.json()
                    if isinstance(result, dict) and "id" in result:
                        member_id = str(result["id"])
                        logger.info(f"✅ 사용자 조회 성공: {member_id}")
                        return member_id
                    else:
                        logger.warning(f"⚠️ 사용자 조회 응답 형식 오류: {result}")
                except Exception as json_err:
                    logger.error(f"❌ JSON 파싱 오류: {json_err}")
                    logger.error(f"📄 응답 내용(앞부분): {response.text[:500]}")
            else:
                logger.warning(f"⚠️ 사용자 조회 실패: {response.status_code}")
                logger.warning(f"📄 응답 내용: {response.text[:200]}")

            return None
        except Exception as e:
            logger.error(f"❌ 사용자 조회 중 오류: {e}")
            return None

    def authenticate(self, username: str, password: str) -> bool:
        """REGTECH 2단계 인증: findOneMember → addLogin"""
        auth_key = f"{username}:{hash(password)}"
        self._last_credentials = (username, password)

        if auth_key in self._auth_cache:
            cache_time, is_valid = self._auth_cache[auth_key]
            if time.time() - cache_time < self._cache_ttl and is_valid:
                if self._is_jwt_valid():
                    self.authenticated = True
                    logger.info("✅ 캐시된 REGTECH 인증 사용")
                    return True
                else:
                    logger.info("🔄 JWT 만료 - 재인증 필요")

        if not self.auth_rate_limiter.wait_if_needed():
            logger.warning("🔒 인증 Rate Limiter 차단 (잠금 상태)")
            return False

        self.session.cookies.clear()

        if self.proxy_url:
            self.session.proxies = {
                "http": self.proxy_url,
                "https": self.proxy_url,
            }

        import urllib.parse

        logger.info(f"🔐 REGTECH 로그인 시도: {username}")

        try:
            # Step 0: loginForm GET (세션 쿠키 획득)
            self.session.get(f"{self.base_url}/login/loginForm", timeout=30)

            # Step 1: findOneMember (회원 검증 AJAX - 실제 브라우저 흐름)
            verify_payload = urllib.parse.urlencode({"memberId": username, "memberPw": password})
            logger.info("📤 Step 1: /member/findOneMember 회원 검증")

            verify_response = self.session.post(
                f"{self.base_url}/member/findOneMember",
                data=verify_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )

            logger.info(f"📊 Step 1 응답: Status={verify_response.status_code}")

            if verify_response.status_code != 200:
                logger.warning(f"⚠️ 회원 검증 실패: HTTP {verify_response.status_code}")
                self.auth_rate_limiter.on_failure(error_code=verify_response.status_code)
                self._auth_cache[auth_key] = (time.time(), False)
                logger.error("❌ REGTECH 인증 실패")
                return False

            # Step 2: addLogin (실제 로그인 form submit)
            login_payload = {
                "username": username,
                "password": password,
                "login_error": "",
                "smsTimeExcess": "N",
                "txId": "",
                "token": "",
                "memberId": "",
            }
            encoded_data = urllib.parse.urlencode(login_payload)
            logger.info("📤 Step 2: /login/addLogin 로그인 요청")

            response = self.session.post(
                f"{self.base_url}/login/addLogin",
                data=encoded_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                allow_redirects=False,
            )

            status_code = response.status_code
            location = response.headers.get("Location", "")
            jwt_cookie = None

            for cookie in response.cookies:
                if cookie.name == "regtech-va" and cookie.value:
                    jwt_cookie = cookie.value
                    self.session.cookies.set("regtech-va", jwt_cookie, domain="regtech.fsec.or.kr")
                elif cookie.name == "regtech-front" and cookie.value:
                    self.session.cookies.set("regtech-front", cookie.value, domain="regtech.fsec.or.kr")

            logger.info(f"📊 Step 2 응답: Status={status_code}, Location={location}, JWT={jwt_cookie is not None}")

            if status_code == 302 and (jwt_cookie or "/main/main" in location):
                self.authenticated = True
                logger.info("✅ REGTECH 인증 성공")
                logger.info(f"🍪 총 세션 쿠키: {len(self.session.cookies)}개")
                self._auth_cache[auth_key] = (time.time(), True)
                self._jwt_expiry = time.time() + 3600  # 1시간 유효 (REGTECH 기본)
                self.auth_rate_limiter.on_success()
                return True
            else:
                logger.warning(f"⚠️ 인증 실패: {status_code}, Location: {location}")
                self.auth_rate_limiter.on_failure(error_code=status_code if status_code >= 400 else None)

        except Exception as e:
            logger.error(f"❌ 인증 오류: {e}")
            self.auth_rate_limiter.on_failure()

        self._auth_cache[auth_key] = (time.time(), False)
        logger.error("❌ REGTECH 인증 실패")
        return False

    def _is_jwt_valid(self) -> bool:
        """Check if current JWT token is still valid (5분 여유)"""
        if not self._jwt_expiry:
            return False
        # 5분 여유두고 만료 체크
        return time.time() < (self._jwt_expiry - 300)

    def _ensure_authenticated(self) -> bool:
        """Ensure valid authentication, re-auth if needed"""
        if self.authenticated and self._is_jwt_valid():
            return True
        if self._last_credentials:
            logger.info("🔄 세션 만료 - 자동 재인증 시도")
            return self.authenticate(*self._last_credentials)
        logger.warning("⚠️ 저장된 인증 정보 없음 - 재인증 필요")
        return False

    def collect_blacklist_data(
        self,
        page_size: int = 2000,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_pages: int = 100,
    ) -> List[Dict[str, Any]]:
        """스마트 다단계 날짜 범위 블랙리스트 데이터 수집 - Excel 우선"""
        if not self._ensure_authenticated():
            logger.error("❌ 인증되지 않은 상태에서 수집 시도")
            return []

        collection_start = time.time()

        # Excel 수집 비활성화 옵션 (환경변수)
        disable_excel = os.getenv("DISABLE_EXCEL_COLLECTION", "false").lower() == "true"

        if start_date and end_date and not disable_excel:
            logger.info(f"📥 Excel 다운로드 시도: {start_date} ~ {end_date}")
            excel_data = self._download_excel_data(start_date, end_date)

            # Excel 데이터 최신성 검증
            is_excel_stale = False
            if excel_data:
                # 데이터의 최대 탐지일 확인 (None 제외, 문자열만)
                valid_dates = []
                for item in excel_data:
                    d = item.get("detection_date")
                    if d and isinstance(d, str):
                        valid_dates.append(d)

                max_date_str = max(valid_dates) if valid_dates else None

                if max_date_str:
                    try:
                        max_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
                        today = datetime.now().date()
                        # 데이터가 3일 이상 오래된 경우 Stale로 판단
                        if (today - max_date).days > 3:
                            is_excel_stale = True
                            logger.warning(f"⚠️ Excel 데이터가 오래됨 (최신: {max_date_str}). HTML 수집으로 전환합니다.")
                    except Exception:
                        pass

            if excel_data and not is_excel_stale:
                collection_time = time.time() - collection_start
                logger.info(f"✅ Excel 수집 완료: {len(excel_data)}개 IP ({collection_time:.2f}초)")
                return self._post_process_collected_data(excel_data)

            if not is_excel_stale:
                logger.warning("⚠️ Excel 다운로드 실패, HTML 페이지네이션으로 전환")

        collected_data = []
        date_strategies = self._generate_date_strategies(start_date, end_date)

        try:
            logger.info(f"🚀 스마트 REGTECH 데이터 수집 시작 (페이지 크기: {page_size}, 최대 페이지: {max_pages})")
            logger.info(f"📅 날짜 전략 수: {len(date_strategies)}개")

            for strategy_idx, (strategy_name, start_dt, end_dt) in enumerate(date_strategies, 1):
                logger.info(f"🔄 전략 {strategy_idx}/{len(date_strategies)}: {strategy_name} ({start_dt} ~ {end_dt})")

                if start_dt and end_dt:
                    excel_data = self._download_excel_data(start_dt, end_dt)
                    if excel_data:
                        logger.info(f"✅ 전략 {strategy_name} Excel 성공: {len(excel_data)}개 IP")
                        collected_data.extend(excel_data)
                        break

                strategy_data = []
                for page_num in range(1, max_pages + 1):
                    page_data = self._collect_single_page(page_num, page_size, start_dt, end_dt)

                    if not page_data:
                        logger.info(f"📄 전략 {strategy_name} 페이지 {page_num}: 데이터 없음")
                        break

                    strategy_data.extend(page_data)
                    logger.info(f"📄 전략 {strategy_name} 페이지 {page_num}: {len(page_data)}개 IP 수집")

                    if len(strategy_data) >= 10000000:
                        logger.warning("⚠️ 메모리 한계 도달 (1000만개), 현재 전략 중단")
                        break

                if strategy_data:
                    logger.info(f"✅ 전략 {strategy_name} 성공: {len(strategy_data)}개 IP 수집")
                    collected_data.extend(strategy_data)
                    break
                else:
                    logger.warning(f"⚠️ 전략 {strategy_name} 실패: 데이터 없음")

            collection_time = time.time() - collection_start
            logger.info(f"✅ 스마트 REGTECH 수집 완료: {len(collected_data)}개 IP ({collection_time:.2f}초)")

            self._record_collection_performance(collected_data, date_strategies, collection_time)

            return self._post_process_collected_data(collected_data)

        except Exception as e:
            logger.error(f"❌ REGTECH 데이터 수집 중 오류: {e}")
            return collected_data

    def _generate_date_strategies(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[tuple]:
        """스마트 날짜 범위 전략 생성 - 데이터 가용성 최적화"""
        strategies = []

        # 날짜 필터 없이 전체 수집 모드 (REGTECH 웹사이트는 날짜 없을 때 전체 데이터 반환)
        if start_date is None and end_date is None:
            strategies.append(("전체 데이터", None, None))
            logger.info("📋 전체 데이터 수집 모드 활성화 (날짜 필터 없음)")
            return strategies

        today = datetime.now()

        # 기본 날짜 설정
        if not end_date:
            end_date = today.strftime("%Y-%m-%d")

        # 전략 1: 최근 1일 (일일 데이터 - 정기 수집용)
        recent_start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        strategies.append(("최근 1일 일일", recent_start, end_date))

        # 전략 2: 최근 90일 (분기 데이터 - 초기 수집용)
        quarter_start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        strategies.append(("최근 90일 분기", quarter_start, end_date))

        # 전략 3: 사용자 지정 범위 (있는 경우)
        if start_date:
            strategies.insert(0, ("사용자 지정", start_date, end_date))

        logger.info(f"📋 생성된 날짜 전략: {[s[0] for s in strategies]}")
        return strategies

    def _record_collection_performance(self, collected_data: List[Dict], strategies: List[tuple], duration: float):
        """수집 성과 기록 및 분석"""
        performance_log = {
            "timestamp": datetime.now().isoformat(),
            "total_strategies": len(strategies),
            "successful_collection": len(collected_data) > 0,
            "data_count": len(collected_data),
            "duration_seconds": round(duration, 2),
            "strategies_tried": [s[0] for s in strategies],
            "success_rate": (1 if len(collected_data) > 0 else 0) / len(strategies),
        }

        logger.info(f"📊 수집 성과: {performance_log}")

        # 성과 데이터를 캐시에 저장 (향후 최적화용)
        self._performance_cache = getattr(self, "_performance_cache", [])
        self._performance_cache.append(performance_log)

        # 최근 10개 성과만 유지
        if len(self._performance_cache) > 10:
            self._performance_cache = self._performance_cache[-10:]

    def _download_excel_data(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Excel 다운로드를 통한 대량 데이터 수집 (최대 3개월)

        Delegates to regtech_excel.download_excel_data()
        """
        return download_excel_data(
            session=self.session,
            rate_limiter=self.rate_limiter,
            proxy_url=self.proxy_url,
            base_url=self.base_url,
            start_date=start_date,
            end_date=end_date,
        )

    def _collect_single_page(
        self,
        page_num: int,
        page_size: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """HAR 분석 기반 단일 페이지 데이터 수집 - 실제 프로토콜 구현"""
        try:
            # HAR 분석에서 확인된 실제 엔드포인트
            # tabSort를 URL 파라미터로도 추가하여 서버가 확실히 인식하도록 함
            data_url = f"{self.base_url}/fcti/securityAdvisory/advisoryList?tabSort=blacklist"

            # 캐시 키 생성
            cache_key = f"page_{page_num}_{page_size}_{start_date}_{end_date}_blacklist"
            if cache_key in self._data_cache:
                cache_time, cached_data = self._data_cache[cache_key]
                if time.time() - cache_time < 60:  # 1분 캐시
                    logger.info(f"📦 페이지 {page_num} 캐시 사용")
                    return cached_data

            # UI에 맞춰 파라미터 조정
            request_data = {
                "page": str(page_num - 1),
                "tabSort": "blacklist",
                "excelDownload": "",
                "cveId": "",
                "ipId": "",
                "estId": "",
                "startDate": start_date or "",
                "endDate": end_date or "",
                "findCondition": "all",
                "findKeyword": "",
                "excelDown": "blacklist",
                "size": "50",
            }

            # HAR 분석에서 확인된 정확한 헤더
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://regtech.fsec.or.kr",
                "Pragma": "no-cache",
                "Referer": "https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryList",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            }

            logger.info(f"🔄 HAR 기반 데이터 수집: 페이지 {page_num}, 크기 {page_size}")

            # Rate Limiting 적용 (API 차단 방지)
            if not self.rate_limiter.wait_if_needed():
                logger.warning(f"⚠️ 페이지 {page_num} Rate Limiter 대기 실패. 수집 중단.")
                return []

            # 쿠키 확인 로그
            cookie_count = len(self.session.cookies)
            has_jwt = any(c.name == "regtech-va" for c in self.session.cookies)
            logger.info(f"🍪 요청 쿠키 상태: {cookie_count}개, JWT 존재: {has_jwt}")

            import subprocess
            import json
            import urllib.parse

            headers_list = []
            for k, v in headers.items():
                headers_list.extend(["-H", f"{k}: {v}"])

            cookie_header = "; ".join([f"{c.name}={c.value}" for c in self.session.cookies])
            if cookie_header:
                headers_list.extend(["-H", f"Cookie: {cookie_header}"])

            # data_json = json.dumps(request_data)

            curl_cmd = (
                ["curl", "-s", "-X", "POST", data_url]
                + headers_list
                + [
                    "-H",
                    "Content-Type: application/x-www-form-urlencoded",
                    "--data",
                    urllib.parse.urlencode(request_data),
                ]
            )

            if self.proxy_url:
                curl_cmd.extend(["--proxy", self.proxy_url])

            encoded_data = urllib.parse.urlencode(request_data)
            logger.info(f"🔍 데이터 수집 curl 실행: {data_url} | page={page_num - 1}")
            logger.debug(f"📤 POST 데이터: {encoded_data}")

            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                logger.error(f"❌ curl 실행 실패: {result.stderr}")
                self.rate_limiter.on_failure()
                return []

            response_text = result.stdout
            logger.info(f"📊 응답 길이: {len(response_text)}")

            try:
                with open("/tmp/regtech_debug.html", "w", encoding="utf-8") as f:
                    f.write(response_text)
                logger.info("💾 디버그 HTML 저장 완료: /tmp/regtech_debug.html")
            except Exception as e:
                logger.warning(f"⚠️ 디버그 HTML 저장 실패: {e}")

            try:

                class MockResponse:
                    def __init__(self, text, status_code):
                        self.text = text
                        self.status_code = status_code

                    def json(self):
                        return json.loads(self.text)

                response = MockResponse(response_text, 200)

            except Exception as e:
                logger.error(f"❌ 응답 객체 생성 실패: {e}")
                return []

            logger.info("📊 응답 처리 시작...")

            if response.status_code == 200:
                page_data = self._parse_response_data(response)

                # 결과 캐시
                self._data_cache[cache_key] = (time.time(), page_data)

                # Rate Limiter 성공 피드백
                self.rate_limiter.on_success()

                logger.info(f"✅ 페이지 {page_num} 수집 완료: {len(page_data)}개 항목")
                return page_data
            else:
                logger.warning(f"⚠️ 페이지 {page_num} 요청 실패: {response.status_code}")

                # Rate Limiter 실패 피드백
                self.rate_limiter.on_failure(error_code=response.status_code)

                return []

        except Exception as e:
            logger.error(f"❌ 페이지 {page_num} 수집 실패: {e}")

            # Rate Limiter 실패 피드백
            self.rate_limiter.on_failure()

            return []

    def _parse_response_data(self, response) -> List[Dict[str, Any]]:
        """응답 데이터 파싱 - 최적화된 처리"""
        try:
            # JSON 파싱 시도
            json_data = response.json()

            if isinstance(json_data, dict) and "data" in json_data:
                raw_data = json_data["data"]
            elif isinstance(json_data, list):
                raw_data = json_data
            else:
                logger.warning("⚠️ 예상하지 못한 JSON 응답 형식")
                return self._parse_html_response(response.text)

            # 병렬 처리 최적화
            processed_data = []
            for item in raw_data:
                processed_item = self._process_regtech_item(item)
                if processed_item:
                    processed_data.append(processed_item)

            return processed_data

        except json.JSONDecodeError:
            logger.info("📄 JSON 파싱 실패, HTML 파싱으로 전환")
            return self._parse_html_response(response.text)
        except Exception as e:
            logger.error(f"❌ 응답 파싱 실패: {e}")
            return []

    def _post_process_collected_data(self, collected_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """수집된 데이터 후처리 - 최적화 및 정제"""
        if not collected_data:
            return []

        logger.info(f"🔧 수집 데이터 후처리 시작: {len(collected_data)}개 항목")

        # 1. IP 주소 유효성 검사 및 정제
        valid_data = []
        for item in collected_data:
            ip_addr = item.get("ip_address", "").strip()
            if self._is_valid_ip(ip_addr):
                # IP 정규화
                item["ip_address"] = ip_addr
                valid_data.append(item)

        # 2. 중복 제거 (메모리 효율적)
        unique_data = self._fast_deduplication(valid_data)

        # 3. 데이터 품질 향상
        enhanced_data = []
        for item in unique_data:
            enhanced_item = self._enhance_data_quality(item)
            enhanced_data.append(enhanced_item)

        logger.info(f"✅ 후처리 완료: {len(enhanced_data)}개 고품질 IP")
        return enhanced_data

    def _fast_deduplication(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """고속 중복 제거"""
        seen_ips = set()
        unique_data = []

        for item in data:
            ip_key = f"{item.get('ip_address')}:{item.get('source', 'REGTECH')}"
            if ip_key not in seen_ips:
                seen_ips.add(ip_key)
                unique_data.append(item)

        return unique_data

    def _enhance_data_quality(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 품질 향상 - 해제일 기준 활성 상태 로직 적용"""

        # 해제일 추출
        removal_date = self._parse_date(item.get("removal_date"))

        # 활성 상태 결정 (removal_date 기반)
        is_active = True
        if removal_date:
            # 해제일이 오늘보다 이전이면 비활성화
            today = datetime.now().date()
            if isinstance(removal_date, str):
                removal_date_obj = datetime.strptime(removal_date, "%Y-%m-%d").date()
            else:
                removal_date_obj = removal_date.date() if hasattr(removal_date, "date") else removal_date

            if removal_date_obj < today:
                is_active = False
                logger.info(
                    f"🔴 [품질향상] IP {item.get('ip_address')} 비활성화: 해제일 {removal_date_obj} < 오늘 {today}"
                )

        # 기본값 설정 및 데이터 정제 - 원본 reason 우선 보존
        original_reason = item.get("reason", "")
        if not original_reason or original_reason in [
            "REGTECH HTML Parse",
            "REGTECH Blacklist",
        ]:
            # 추가 필드에서 의미 있는 내용 찾기
            for alt_field in [
                "contents",
                "detail",
                "description",
                "threat_desc",
                "block_reason",
            ]:
                alt_content = item.get(alt_field, "").strip()
                if alt_content and len(alt_content) > 5:  # 의미 있는 길이
                    original_reason = alt_content
                    break
            if not original_reason:
                original_reason = "REGTECH 위협 IP"

        enhanced_item = {
            "ip_address": item.get("ip_address", "").strip(),
            "source": "REGTECH",
            "reason": original_reason,
            "confidence_level": self._determine_confidence(item),
            "detection_count": 1,
            "is_active": is_active,  # 해제일 기준 로직 적용
            "last_seen": datetime.now(),
            "country": self._normalize_country_code(item.get("country")),
            "detection_date": self._parse_date(item.get("detection_date")),
            "removal_date": removal_date,
            # 추가 메타데이터
            "collection_timestamp": datetime.now().isoformat(),
            "data_source_version": "optimized_v2.0",
        }

        return enhanced_item

    def _normalize_country_code(self, country_value) -> Optional[str]:
        """국가 코드 정규화"""
        if not country_value:
            return None

        country_str = str(country_value).upper().strip()

        # 일반적인 국가 코드 매핑
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

        return country_mapping.get(country_str, country_str[:2] if len(country_str) >= 2 else None)

    def _process_regtech_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """REGTECH 데이터 항목 처리 - 최적화"""
        try:
            # IP 주소 추출 - 다양한 필드명 지원
            ip_fields = ["ipAddr", "ip_address", "ip", "IP", "target_ip"]
            ip_address = None

            for field in ip_fields:
                if field in item and item[field]:
                    ip_address = str(item[field]).strip()
                    break

            if not ip_address or not self._is_valid_ip(ip_address):
                return None

            # 원본 데이터 로깅 및 검증
            logger.info(f"🔍 원본 REGTECH 데이터: {item}")

            # 탐지일/해제일 필드 확인
            detection_fields = [
                "regDt",
                "detectionDate",
                "reg_dt",
                "detect_dt",
                "created_dt",
            ]
            removal_fields = ["delDt", "removalDate", "del_dt", "remove_dt", "end_dt"]
            reason_fields = [
                "blockReason",
                "reason",
                "block_reason",
                "description",
                "content",
            ]

            detection_date = None
            removal_date = None
            detection_reason = "REGTECH Blacklist"

            # 탐지일 추출
            for field in detection_fields:
                if field in item and item[field]:
                    detection_date = self._parse_date(item[field])
                    logger.info(f"✅ 탐지일 발견: {field} = {item[field]} -> {detection_date}")
                    break

            # 해제일 추출
            for field in removal_fields:
                if field in item and item[field]:
                    removal_date = self._parse_date(item[field])
                    logger.info(f"✅ 해제일 발견: {field} = {item[field]} -> {removal_date}")
                    break

            # 탐지내용 추출 - 원본 raw data 우선
            for field in reason_fields:
                if field in item and item[field]:
                    raw_reason = str(item[field]).strip()
                    if raw_reason and raw_reason not in [
                        "REGTECH HTML Parse",
                        "REGTECH Blacklist",
                        "",
                    ]:
                        detection_reason = raw_reason
                        logger.info(f"✅ 원본 탐지내용 발견: {field} = {detection_reason}")
                        break
                    elif raw_reason:
                        # 기본값보다는 의미 있는 내용이면 사용
                        detection_reason = raw_reason
                        logger.info(f"📝 기본 탐지내용 사용: {field} = {detection_reason}")

            # 추가 필드에서 더 자세한 내용 찾기
            additional_content_fields = [
                "contents",
                "detail",
                "description",
                "threat_desc",
                "attack_info",
                "malware_name",
            ]
            for field in additional_content_fields:
                if field in item and item[field]:
                    additional_content = str(item[field]).strip()
                    if additional_content and len(additional_content) > len(detection_reason):
                        detection_reason = additional_content
                        logger.info(f"✅ 상세 탐지내용 발견: {field} = {detection_reason}")
                        break

            # 활성 상태 결정 (removal_date 기반)
            is_active = True
            if removal_date:
                # 해제일이 오늘보다 이전이면 비활성화 (오늘 해제되는 IP는 활성 유지)
                today = datetime.now().date()
                if isinstance(removal_date, str):
                    removal_date_obj = datetime.strptime(removal_date, "%Y-%m-%d").date()
                else:
                    removal_date_obj = removal_date.date() if hasattr(removal_date, "date") else removal_date

                if removal_date_obj < today:
                    is_active = False
                    logger.info(f"🔴 IP {ip_address} 비활성화: 해제일 {removal_date_obj} < 오늘 {today}")

            processed_item = {
                "ip_address": ip_address,
                "source": "REGTECH",
                "reason": detection_reason,
                "confidence_level": self._determine_confidence(item),
                "detection_count": 1,
                "is_active": is_active,
                "last_seen": datetime.now(),
                "country": item.get("country") or item.get("countryCode"),
                "detection_date": detection_date,
                "removal_date": removal_date,
                "raw_data": {
                    "api_response": item,
                    "collection_timestamp": datetime.now().isoformat(),
                },
            }

            return processed_item

        except Exception as e:
            logger.debug(f"항목 처리 중 오류 (무시): {e}")
            return None

    def _determine_confidence(self, item: Dict[str, Any]) -> int:
        """신뢰도 결정 - 향상된 평가"""
        base_confidence = 80  # REGTECH 기본 신뢰도

        # 위협 레벨 기반 조정
        threat_level = str(item.get("threatLevel", "medium")).lower()
        threat_adjustments = {"critical": 15, "high": 10, "medium": 0, "low": -10}

        confidence = base_confidence + threat_adjustments.get(threat_level, 0)

        # 추가 신뢰도 요소
        if item.get("verified"):
            confidence += 5
        if item.get("reportCount", 0) > 10:
            confidence += 5

        return max(10, min(100, confidence))

    def _parse_date(self, date_str: Any) -> Optional[str]:
        """날짜 문자열 파싱 - 향상된 처리 및 로깅"""
        if not date_str:
            return None

        # 원본 데이터 로깅
        logger.info(f"📅 날짜 파싱 시도: '{date_str}' (타입: {type(date_str)})")

        # 문자열로 변환
        # date_str_clean = str(date_str).strip()

        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y.%m.%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d.%m.%Y",
            "%Y%m%d",  # 8자리 숫자
            "%m/%d/%Y",
            "%m-%d-%Y",
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                result = parsed_date.strftime("%Y-%m-%d")
                logger.info(f"✅ 날짜 파싱 성공: '{date_str}' -> '{result}' (형식: {fmt})")
                return result
            except ValueError:
                continue

        logger.warning(f"❌ 날짜 파싱 실패: '{date_str}' - 지원되지 않는 형식")
        return None

    def _parse_html_response(self, html_content: str) -> List[Dict[str, Any]]:
        return parse_html_response(html_content)

    def _extract_country_info(self, cell_texts: List[str]) -> Optional[str]:
        """HTML 테이블 행에서 국가 정보 추출"""
        if not cell_texts:
            return None

        # 국가 코드/이름을 찾기 위한 패턴들
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

        # 각 셀에서 국가 정보 찾기
        for cell_text in cell_texts:
            if not cell_text or len(cell_text.strip()) < 2:
                continue

            cell_upper = cell_text.upper().strip()

            # 국가 코드 매칭
            for country_code, patterns in country_patterns.items():
                for pattern in patterns:
                    if pattern.upper() in cell_upper:
                        logger.info(f"✅ 국가 정보 발견: '{cell_text}' -> {country_code}")
                        return country_code

            # 2글자 국가 코드 형태인지 확인
            if len(cell_text.strip()) == 2 and cell_text.strip().isalpha():
                country_code = cell_text.strip().upper()
                logger.info(f"✅ 국가 코드 발견: {country_code}")
                return country_code

        return None

    def _is_valid_ip(self, ip_str: str) -> bool:
        """IP 주소 유효성 검사 - 향상된 검증"""
        try:
            import ipaddress

            ip_obj = ipaddress.ip_address(ip_str.strip())

            # 사설 IP 및 특수 IP 필터링
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
                return False

            # IPv4 우선, IPv6 지원
            return True

        except ValueError:
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """세션 정보 반환 - 향상된 정보"""
        return {
            "authenticated": self.authenticated,
            "cookies_count": len(self.session.cookies),
            "base_url": self.base_url,
            "cache_size": len(self._data_cache),
            "auth_cache_size": len(self._auth_cache),
            "performance_mode": "optimized",
            "last_activity": datetime.now().isoformat(),
            "rate_limiter": self.rate_limiter.get_stats(),
        }

    def clear_cache(self):
        """캐시 정리"""
        self._data_cache.clear()
        self._auth_cache.clear()
        logger.info("🧹 캐시 정리 완료")


# 전역 인스턴스
regtech_collector = RegtechCollector()
