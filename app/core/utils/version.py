"""
공통 버전 유틸리티
"""

import os


def get_app_version():
    """앱 버전 정보 가져오기"""
    # 환경변수에서 우선 가져오기
    version = os.getenv("APP_VERSION")
    if version:
        return version

    # Git 정보가 있으면 사용
    try:
        commit_hash = os.getenv("COMMIT_HASH", "unknown")
        build_number = os.getenv("BUILD_NUMBER", "dev")
        return f"3.1.0-{build_number}-{commit_hash[:7]}"
    except BaseException:
        return "3.1.0-dev"
