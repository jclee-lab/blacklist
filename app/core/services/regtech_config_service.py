"""
REGTECH Configuration Service
REGTECH 인증정보 및 설정 관리를 위한 서비스
"""

import logging
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from ..database.connection import get_db_connection

# Encryption removed - storing credentials in plain text

logger = logging.getLogger(__name__)


class RegtechConfigService:
    """REGTECH 설정 및 인증정보 관리 서비스"""

    def __init__(self):
        self.service_name = "REGTECH"

    def save_regtech_credentials(
        self,
        username: str,
        password: str,
        base_url: str = "https://regtech.fsec.or.kr",
        login_url: str = "/login/loginProcess",
        advisory_url: str = "/advisory/advisory01_search",
        timeout_seconds: int = 30,
        max_pages: int = 100,
        items_per_page: int = 50,
        request_delay_seconds: int = 1,
    ) -> Dict[str, Any]:
        """REGTECH 인증정보 저장 - 보안 서비스 사용"""
        try:
            from .secure_credential_service import save_regtech_credentials as save_secure_credentials
            
            # 추가 설정 정보
            config = {
                "base_url": base_url,
                "login_url": login_url,
                "advisory_url": advisory_url,
                "timeout_seconds": timeout_seconds,
                "max_pages": max_pages,
                "items_per_page": items_per_page,
                "request_delay_seconds": request_delay_seconds
            }
            
            # 보안 서비스를 통한 저장
            from .secure_credential_service import secure_credential_service
            success = secure_credential_service.save_credentials("REGTECH", username, password, config)
            
            if success:
                logger.info(f"✅ REGTECH 인증정보 저장 완료: {username}")
                return {
                    "success": True,
                    "message": "REGTECH 인증정보가 안전하게 저장되었습니다",
                    "username": username,
                    "encrypted": True
                }
            else:
                logger.error("❌ REGTECH 인증정보 저장 실패")
                return {
                    "success": False,
                    "error": "인증정보 저장에 실패했습니다"
                }
                
        except Exception as e:
            logger.error(f"❌ REGTECH 인증정보 저장 실패: {e}")
            return {
                "success": False,
                "error": f"인증정보 저장 중 오류 발생: {str(e)}"
            }

    def get_regtech_credentials(self) -> Optional[Dict[str, Any]]:
        """REGTECH 인증정보 조회 - 보안 서비스 사용"""
        try:
            from .secure_credential_service import get_regtech_credentials
            
            credentials = get_regtech_credentials()
            if not credentials:
                logger.warning("⚠️ REGTECH 인증정보가 설정되지 않음")
                return None
                
            # 기존 인터페이스와 호환되도록 변환
            return {
                "username": credentials.get("username", ""),
                "password": credentials.get("password", ""),
                "base_url": credentials.get("config", {}).get("base_url", "https://regtech.fsec.or.kr"),
                "login_url": credentials.get("config", {}).get("login_url", "/login/loginProcess"),
                "advisory_url": credentials.get("config", {}).get("advisory_url", "/advisory/advisory01_search"),
                "timeout_seconds": credentials.get("config", {}).get("timeout_seconds", 30),
                "max_pages": credentials.get("config", {}).get("max_pages", 100),
                "items_per_page": credentials.get("config", {}).get("items_per_page", 50),
                "request_delay_seconds": credentials.get("config", {}).get("request_delay_seconds", 1),
                "created_at": credentials.get("created_at"),
                "updated_at": credentials.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"❌ REGTECH 인증정보 조회 실패: {e}")
            return None

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정값 반환"""
        return {
            "base_url": os.getenv("REGTECH_BASE_URL", "https://regtech.fsec.or.kr"),
            "login_url": "/login/loginProcess",
            "advisory_url": "/fcti/securityAdvisory/advisoryList",
            "max_pages": 100,
            "items_per_page": 50,
            "timeout_seconds": 30,
            "request_delay_seconds": 1,
            "encryption_version": "1.0",
        }

    def test_regtech_connection(self) -> Dict[str, Any]:
        """🔍 기본 REGTECH 연결 테스트 (하위 호환성)"""
        return self.test_regtech_connection_enhanced()

    def test_regtech_connection_enhanced(self) -> Dict[str, Any]:
        """🚀 고도화된 REGTECH 연결 테스트 (다중 검증 단계)"""
        start_time = datetime.now()
        test_phases = {
            "credential_check": {"status": "pending", "message": ""},
            "collector_health": {"status": "pending", "message": ""},
            "authentication": {"status": "pending", "message": ""},
            "data_access": {"status": "pending", "message": ""},
        }

        try:
            logger.info("🔍 고도화된 REGTECH 연결 테스트 시작")

            # Phase 1: 저장된 인증정보 확인
            logger.info("📋 Phase 1: 인증정보 확인")
            credentials = self.get_regtech_credentials()
            if not credentials:
                test_phases["credential_check"] = {
                    "status": "failed",
                    "message": "저장된 인증정보가 없습니다",
                }
                return self._format_test_result(
                    False, test_phases, start_time, "NO_CREDENTIALS"
                )

            username = credentials.get("username", "").strip()
            password = credentials.get("password", "")

            if not username or not password:
                test_phases["credential_check"] = {
                    "status": "failed",
                    "message": "인증정보가 불완전합니다",
                }
                return self._format_test_result(
                    False, test_phases, start_time, "INCOMPLETE_CREDENTIALS"
                )

            test_phases["credential_check"] = {
                "status": "success",
                "message": f"인증정보 확인 완료 (사용자: {username})",
            }
            logger.info(f"✅ Phase 1 완료: 사용자 {username} 인증정보 유효")

            # Phase 2: 수집 컨테이너 헬스체크
            logger.info("🏥 Phase 2: 수집 컨테이너 상태 확인")
            try:
                collector_url = "http://blacklist-collector:8545"
                health_response = requests.get(f"{collector_url}/health", timeout=10)

                if health_response.status_code == 200:
                    health_data = health_response.json()
                    test_phases["collector_health"] = {
                        "status": "success",
                        "message": f"수집 컨테이너 정상 (상태: {health_data.get('status', 'unknown')})",
                    }
                    logger.info("✅ Phase 2 완료: 수집 컨테이너 정상")
                else:
                    test_phases["collector_health"] = {
                        "status": "warning",
                        "message": f"수집 컨테이너 응답 이상 (코드: {health_response.status_code})",
                    }
                    logger.warning(
                        f"⚠️ Phase 2 경고: 컨테이너 응답 코드 {health_response.status_code}"
                    )

            except requests.RequestException as e:
                test_phases["collector_health"] = {
                    "status": "failed",
                    "message": f"수집 컨테이너 연결 실패: {str(e)[:100]}",
                }
                logger.error(f"❌ Phase 2 실패: 컨테이너 연결 오류 - {e}")
                return self._format_test_result(
                    False, test_phases, start_time, "COLLECTOR_UNAVAILABLE"
                )

            # Phase 3: REGTECH 인증 테스트 (실제 로그인 시도)
            logger.info("🔐 Phase 3: REGTECH 포털 인증 테스트")
            try:
                from .collection_service import collection_service

                # 오늘 날짜로 최소한의 테스트 수집 시도
                today = datetime.now().strftime("%Y-%m-%d")
                auth_test_result = collection_service.test_regtech_collection(
                    username, password, today, today
                )

                if auth_test_result.get("success"):
                    collected_count = auth_test_result.get("collected_count", 0)
                    test_phases["authentication"] = {
                        "status": "success",
                        "message": "REGTECH 인증 성공",
                    }
                    test_phases["data_access"] = {
                        "status": "success",
                        "message": f"데이터 접근 성공 ({collected_count}개 항목)",
                    }
                    logger.info(f"✅ Phase 3-4 완료: 인증 및 데이터 접근 성공 ({collected_count}개)")
                else:
                    auth_error = auth_test_result.get("error", "인증 실패")
                    test_phases["authentication"] = {
                        "status": "failed",
                        "message": f"REGTECH 인증 실패: {auth_error[:100]}",
                    }
                    test_phases["data_access"] = {
                        "status": "failed",
                        "message": "인증 실패로 데이터 접근 불가",
                    }
                    logger.error(f"❌ Phase 3 실패: 인증 오류 - {auth_error}")
                    return self._format_test_result(
                        False, test_phases, start_time, "AUTH_FAILED"
                    )

            except Exception as e:
                test_phases["authentication"] = {
                    "status": "error",
                    "message": f"인증 테스트 오류: {str(e)[:100]}",
                }
                logger.error(f"💥 Phase 3 오류: 인증 테스트 예외 - {e}")
                return self._format_test_result(
                    False, test_phases, start_time, "AUTH_ERROR"
                )

            # 모든 단계 성공
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"🎉 REGTECH 연결 테스트 완료 - 모든 단계 성공 (소요시간: {duration:.2f}초)")

            return self._format_test_result(True, test_phases, start_time, "SUCCESS")

        except Exception as e:
            logger.error(f"💥 REGTECH 연결 테스트 중 예외 발생: {e}")
            test_phases["authentication"]["status"] = "error"
            test_phases["authentication"]["message"] = f"테스트 중 오류: {str(e)[:100]}"
            return self._format_test_result(
                False, test_phases, start_time, "TEST_ERROR"
            )

    def _format_test_result(
        self, success: bool, phases: Dict, start_time: datetime, result_code: str
    ) -> Dict[str, Any]:
        """테스트 결과 포맷팅"""
        duration = (datetime.now() - start_time).total_seconds()

        # 성공한 단계 수 계산
        success_count = sum(
            1 for phase in phases.values() if phase["status"] == "success"
        )
        total_phases = len(phases)

        # 전체 메시지 생성
        if success:
            main_message = "✅ 모든 연결 테스트 통과"
        else:
            failed_phases = [
                name
                for name, phase in phases.items()
                if phase["status"] in ["failed", "error"]
            ]
            main_message = f"❌ 연결 테스트 실패 (실패 단계: {', '.join(failed_phases)})"

        return {
            "success": success,
            "message": main_message,
            "result_code": result_code,
            "phases": phases,
            "summary": {
                "success_phases": success_count,
                "total_phases": total_phases,
                "success_rate": f"{(success_count/total_phases)*100:.1f}%",
            },
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

    def update_regtech_password(self, new_password: str) -> bool:
        """REGTECH 비밀번호 업데이트"""
        try:
            credentials = self.get_regtech_credentials()
            if not credentials:
                logger.warning("업데이트할 인증정보가 없습니다.")
                return False

            return self.save_regtech_credentials(credentials["username"], new_password)

        except Exception as e:
            logger.error(f"REGTECH 비밀번호 업데이트 실패: {e}")
            return False

    def initialize_regtech_credentials(self) -> bool:
        """REGTECH 인증정보 초기화 (환경변수에서 로드)"""
        try:
            import os

            # 환경변수에서 인증정보 로드 (GitHub Secrets에서 제공)
            default_username = os.getenv("REGTECH_ID", "")
            default_password = os.getenv("REGTECH_PW", "")

            if not default_username or not default_password:
                logger.warning("환경변수에서 REGTECH 인증정보를 찾을 수 없습니다.")
                return False

            return self.save_regtech_credentials(default_username, default_password)

        except Exception as e:
            logger.error(f"REGTECH 인증정보 초기화 실패: {e}")
            return False

    def delete_regtech_credentials(self) -> bool:
        """REGTECH 인증정보 삭제 - 보안 서비스 사용"""
        try:
            from .secure_credential_service import delete_regtech_credentials
            
            success = delete_regtech_credentials()
            if success:
                logger.info("✅ REGTECH 인증정보 삭제 완료")
            else:
                logger.warning("⚠️ 삭제할 REGTECH 인증정보가 없음")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ REGTECH 인증정보 삭제 실패: {e}")
            return False


# 싱글톤 인스턴스
regtech_config_service = RegtechConfigService()
