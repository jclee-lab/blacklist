"""Validation related exceptions"""

from typing import Any, Dict, Optional, List

from .base_exceptions import APIError


class ValidationError(APIError):
    """
    데이터 검증 관련 예외

    IP 주소, 날짜 형식, 입력 데이터 등의 검증 실패 시 발생합니다.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validation_errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        if validation_errors:
            error_details["validation_errors"] = validation_errors

        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR", details=error_details)
        self.field = field
        self.value = value
        self.validation_errors = validation_errors or []


class BadRequestError(APIError):
    """HTTP 400 Bad Request"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, status_code=400, error_code="BAD_REQUEST", details=error_details)
        self.field = field


class NotFoundError(APIError):
    """HTTP 404 Not Found"""

    def __init__(self, message: str, resource: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if resource:
            error_details["resource"] = resource
        super().__init__(message, status_code=404, error_code="NOT_FOUND", details=error_details)
        self.resource = resource


class ConflictError(APIError):
    """HTTP 409 Conflict"""

    def __init__(self, message: str, resource: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if resource:
            error_details["resource"] = resource
        super().__init__(message, status_code=409, error_code="CONFLICT", details=error_details)
        self.resource = resource


class InternalServerError(APIError):
    """HTTP 500 Internal Server Error"""

    def __init__(self, message: str, cause: Optional[str] = None):
        details = {"cause": cause} if cause else {}
        super().__init__(message, status_code=500, error_code="INTERNAL_SERVER_ERROR", details=details)
        self.cause = cause


class UnauthorizedError(APIError):
    """HTTP 401 Unauthorized"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED", details={})


class ForbiddenError(APIError):
    """HTTP 403 Forbidden"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403, error_code="FORBIDDEN", details={})
