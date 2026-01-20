"""Data processing related exceptions"""

from typing import Optional

from .base_exceptions import BlacklistError


class DataProcessingError(BlacklistError):
    """
    데이터 처리 관련 예외

    파일 읽기/쓰기 실패, 데이터 파싱 오류, 변환 실패 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        data_type: Optional[str] = None,
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        if data_type:
            details["data_type"] = data_type

        super().__init__(message, "DATA_PROCESSING_ERROR", details)
        self.file_path = file_path
        self.operation = operation
        self.data_type = data_type


class DataError(BlacklistError):
    """
    데이터 관련 예외 (DataProcessingError의 별칭)

    데이터 로드, 검색, 처리 실패 등에 사용됩니다.
    """

    def __init__(
        self,
        message: str,
        data_source: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if data_source:
            details["data_source"] = data_source
        if operation:
            details["operation"] = operation

        super().__init__(message, "DATA_ERROR", details)
        self.data_source = data_source
        self.operation = operation
