"""Service related exceptions"""

from typing import Optional

from .base_exceptions import BlacklistError


class RateLimitError(BlacklistError):
    """
    Rate Limiting 관련 예외

    요청 한도 초과, 속도 제한 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        identifier: Optional[str] = None,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: Optional[int] = None,
    ):
        details = {}
        if identifier:
            details["identifier"] = identifier
        if limit is not None:
            details["limit"] = limit
        if window_seconds is not None:
            details["window_seconds"] = window_seconds
        if retry_after is not None:
            details["retry_after"] = retry_after

        super().__init__(message, "RATE_LIMIT_ERROR", details)
        self.identifier = identifier
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after


class ServiceUnavailableError(BlacklistError):
    """
    서비스 불가 상태 예외

    외부 API 연결 실패, 시스템 과부하, 유지보수 모드 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
        status_code: Optional[int] = None,
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if retry_after is not None:
            details["retry_after"] = retry_after
        if status_code is not None:
            details["status_code"] = status_code

        super().__init__(message, "SERVICE_UNAVAILABLE_ERROR", details)
        self.service_name = service_name
        self.retry_after = retry_after
        self.status_code = status_code


class MonitoringError(BlacklistError):
    """
    모니터링 관련 예외

    메트릭 수집 실패, 헬스체크 오류, 알림 전송 실패 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        component: Optional[str] = None,
    ):
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if component:
            details["component"] = component

        super().__init__(message, "MONITORING_ERROR", details)
        self.metric_name = metric_name
        self.component = component
