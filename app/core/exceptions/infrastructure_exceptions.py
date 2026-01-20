"""Infrastructure related exceptions"""

import re
from typing import Optional

from .base_exceptions import BlacklistError


class CacheError(BlacklistError):
    """
    캐시 관련 예외

    Redis 연결 실패, 캐시 데이터 손상, TTL 설정 오류 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
        cache_type: str = "unknown",
    ):
        details = {"cache_type": cache_type}
        if cache_key:
            details["cache_key"] = cache_key
        if operation:
            details["operation"] = operation

        super().__init__(message, "CACHE_ERROR", details)
        self.cache_key = cache_key
        self.operation = operation
        self.cache_type = cache_type


class DatabaseError(BlacklistError):
    """
    데이터베이스 관련 예외

    SQLite 연결 실패, 쿼리 오류, 스키마 문제 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        table: Optional[str] = None,
        database_url: Optional[str] = None,
    ):
        details = {}
        if query:
            details["query"] = query
        if table:
            details["table"] = table
        if database_url:
            # 보안을 위해 URL에서 민감한 정보 제거
            details["database_url"] = self._sanitize_url(database_url)

        super().__init__(message, "DATABASE_ERROR", details)
        self.query = query
        self.table = table
        self.database_url = database_url

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """데이터베이스 URL에서 민감한 정보 제거"""
        # 비밀번호 마스킹
        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


class ConnectionError(BlacklistError):
    """
    연결 관련 예외

    네트워크 연결 실패, API 호출 실패 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[int] = None,
        status_code: Optional[int] = None,
    ):
        details = {}
        if url:
            details["url"] = url
        if timeout is not None:
            details["timeout"] = timeout
        if status_code is not None:
            details["status_code"] = status_code

        super().__init__(message, "CONNECTION_ERROR", details)
        self.url = url
        self.timeout = timeout
        self.status_code = status_code
