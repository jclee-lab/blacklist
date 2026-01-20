"""Authentication and authorization exceptions"""

from typing import Optional

from .base_exceptions import BlacklistError


class AuthenticationError(BlacklistError):
    """
    인증 관련 예외

    JWT 토큰 검증 실패, API 키 오류, 권한 부족 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        user_id: Optional[str] = None,
        required_permission: Optional[str] = None,
    ):
        details = {}
        if auth_type:
            details["auth_type"] = auth_type
        if user_id:
            details["user_id"] = user_id
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(message, "AUTHENTICATION_ERROR", details)
        self.auth_type = auth_type
        self.user_id = user_id
        self.required_permission = required_permission


class AuthorizationError(BlacklistError):
    """
    권한 부여 관련 예외

    역할 기반 접근 제어, 리소스 접근 권한 등의 오류에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        required_role: Optional[str] = None,
        resource: Optional[str] = None,
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if required_role:
            details["required_role"] = required_role
        if resource:
            details["resource"] = resource

        super().__init__(message, "AUTHORIZATION_ERROR", details)
        self.user_id = user_id
        self.required_role = required_role
        self.resource = resource
