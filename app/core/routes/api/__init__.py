"""API 라우트 패키지
API 엔드포인트를 기능별로 모듈화
"""

# 기본 API 블루프린트 생성
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# 하위 모듈들 임포트
from . import collection_api
from . import core_api
from . import database_api
from . import ip_management_api
from . import system_api
