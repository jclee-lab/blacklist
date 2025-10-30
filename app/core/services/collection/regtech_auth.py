"""REGTECH 인증 및 로그인 모듈
REGTECH 포털 로그인 및 세션 관리
"""

import logging
import requests
import time

logger = logging.getLogger(__name__)


class REGTECHAuthManager:
    """REGTECH 인증 관리자"""

    def __init__(self):
        self.base_url = "https://regtech.fsec.or.kr"
        self._cached_session = None
        self._session_expiry = None
        self._session_cookies = None
        self._authenticated_user = None

    def _is_session_valid(self) -> bool:
        """세션 유효성 검사"""
        if not self._cached_session or not self._session_expiry:
            return False

        # 세션 만료 시간 체크 (1시간)
        if time.time() > self._session_expiry:
            logger.info("🕐 캐시된 REGTECH 세션 만료")
            return False

        # 쿠키 존재 여부 확인
        if not self._session_cookies:
            return False

        return True

    def _cache_session(self, session: requests.Session, regtech_id: str):
        """세션 캐시 저장"""
        self._cached_session = session
        self._session_expiry = time.time() + 3600  # 1시간
        self._session_cookies = dict(session.cookies)
        self._authenticated_user = regtech_id
        logger.info(f"💾 REGTECH 세션 캐시 저장: {regtech_id} (만료: 1시간)")

    def _clear_cached_session(self):
        """캐시된 세션 정리"""
        self._cached_session = None
        self._session_expiry = None
        self._session_cookies = None
        self._authenticated_user = None
        logger.info("🗑️ REGTECH 세션 캐시 정리")

    def get_cached_session(self, regtech_id: str, regtech_pw: str) -> tuple:
        """캐시된 세션 가져오기 또는 새로운 세션 생성"""
        try:
            # 기존 세션이 유효하고 같은 사용자인지 확인
            if self._is_session_valid() and self._authenticated_user == regtech_id:
                logger.info(f"♻️ 캐시된 REGTECH 세션 재사용: {regtech_id}")
                return self._cached_session, "캐시된 세션 재사용"

            # 기존 세션이 만료되었거나 다른 사용자
            if self._cached_session:
                logger.info("🔄 새로운 REGTECH 세션 생성 (기존 세션 만료 또는 사용자 변경)")
                self._clear_cached_session()

            # 새로운 세션 생성
            session, error = self.authenticate_session(regtech_id, regtech_pw)

            if session:
                self._cache_session(session, regtech_id)
                return session, "새로운 세션 생성 및 캐시"
            else:
                return None, error

        except Exception as e:
            logger.error(f"세션 캐시 처리 오류: {e}")
            self._clear_cached_session()
            return None, f"세션 캐시 오류: {str(e)}"

    def test_regtech_login(self, regtech_id: str, regtech_pw: str) -> dict:
        """REGTECH 로그인 테스트 - 새로운 포털 구조에 맞춰 업데이트"""
        try:
            session = requests.Session()

            # 1단계: 로그인 폼 페이지 접근
            login_form_url = f"{self.base_url}/login/loginForm"
            response = session.get(login_form_url, timeout=10)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"로그인 폼 페이지 접근 실패: {response.status_code}",
                }

            # 2단계: 직접 로그인 (HAR 파일 분석 기반)
            login_url = f"{self.base_url}/login/addLogin"
            login_data = {
                "username": regtech_id,
                "password": regtech_pw,
                "memberId": regtech_id,
            }

            login_response = session.post(
                login_url,
                data=login_data,
                timeout=10,
                allow_redirects=False,  # 302 리다이렉트 직접 처리
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": f"{self.base_url}/login/loginForm",
                },
            )

            # 로그인 성공 시 302 리다이렉트 또는 200 응답
            if login_response.status_code in [200, 302]:
                # 세션 쿠키 확인
                session_cookies = session.cookies
                if session_cookies:
                    return {
                        "success": True,
                        "message": "REGTECH 로그인 성공",
                        "session_cookies": dict(session_cookies),
                        "status_code": login_response.status_code,
                    }

            return {
                "success": False,
                "error": f"로그인 실패 - 상태코드: {login_response.status_code}",
                "status_code": login_response.status_code,
                "response_text": (
                    login_response.text[:500] if login_response.text else "No response"
                ),
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "REGTECH 포털 연결 시간 초과"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "REGTECH 포털 연결 실패"}
        except Exception as e:
            logger.error(f"REGTECH 로그인 테스트 오류: {e}")
            return {"success": False, "error": f"로그인 테스트 오류: {str(e)}"}

    def authenticate_session(self, regtech_id: str, regtech_pw: str) -> tuple:
        """REGTECH 세션 인증 및 반환 - 캐시 우선 사용"""
        try:
            # 캐시된 세션 먼저 확인
            cached_session, message = self.get_cached_session(regtech_id, regtech_pw)
            if cached_session:
                logger.info(f"✅ REGTECH 세션 준비 완료: {message}")
                return cached_session, message

            # 캐시된 세션이 없거나 만료된 경우 새로 생성
            session = requests.Session()

            # 로그인 수행
            login_result = self.test_regtech_login(regtech_id, regtech_pw)

            if not login_result.get("success"):
                error_msg = login_result.get("error", "인증 실패")
                logger.error(f"❌ REGTECH 로그인 실패: {error_msg}")
                return None, error_msg

            # 성공한 로그인 결과에서 세션 쿠키 적용
            if "session_cookies" in login_result:
                session_cookies = login_result["session_cookies"]
                for cookie_name, cookie_value in session_cookies.items():
                    session.cookies.set(
                        cookie_name, cookie_value, domain="regtech.fsec.or.kr"
                    )
                logger.info(f"🍪 세션 쿠키 적용 완료: {list(session_cookies.keys())}")

            # 세션 캐시에 저장
            self._cache_session(session, regtech_id)

            return session, "새로운 인증 세션 생성"

        except Exception as e:
            logger.error(f"REGTECH 세션 인증 오류: {e}")
            self._clear_cached_session()
            return None, f"세션 인증 오류: {str(e)}"


# 싱글톤 인스턴스
regtech_auth = REGTECHAuthManager()
