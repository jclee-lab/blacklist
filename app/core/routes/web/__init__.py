"""
Web Routes Module
웹 인터페이스 라우트 모듈 패키지
"""

from flask import Blueprint

# 메인 웹 블루프린트 생성
web_bp = Blueprint("web", __name__)

# 하위 모듈들의 라우트 등록
from . import dashboard_routes

__all__ = ["web_bp"]
