"""Configuration and dependency related exceptions"""

from typing import List, Optional

from .base_exceptions import BlacklistError


class ConfigurationError(BlacklistError):
    """
    구성 관련 예외

    환경 변수 누락, 설정 파일 오류, 잘못된 구성 값 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        expected_type: Optional[str] = None,
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_file:
            details["config_file"] = config_file
        if expected_type:
            details["expected_type"] = expected_type

        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key
        self.config_file = config_file
        self.expected_type = expected_type


class DependencyError(BlacklistError):
    """
    의존성 관련 예외

    의존성 주입 실패, 순환 의존성, 서비스 해결 실패 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        dependency_chain: Optional[List[str]] = None,
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if dependency_chain:
            details["dependency_chain"] = dependency_chain

        super().__init__(message, "DEPENDENCY_ERROR", details)
        self.service_name = service_name
        self.dependency_chain = dependency_chain or []
