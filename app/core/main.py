#!/usr/bin/env python3
"""
Full Flask 애플리케이션 - 완전한 웹 인터페이스 지원
"""
import os
import logging
from flask import Flask, jsonify
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def create_app():
    """완전한 Flask 애플리케이션 생성 (템플릿 지원)"""
    # ABSOLUTE PATH SOLUTION - 확실한 템플릿 경로 설정

    # 현재 파일의 실제 위치 기반으로 절대 경로 계산
    current_file = Path(__file__).resolve()

    # 컨테이너 환경에서는 절대 경로 강제 사용
    if str(current_file).startswith("/app/"):
        # 컨테이너 환경: 절대 경로 사용
        templates_dir = Path("/app/templates")
        static_dir = Path("/app/static")
        logger.info(f"🐳 컨테이너 환경 감지: {current_file}")
        logger.info(f"📁 템플릿 절대경로: {templates_dir}")
        logger.info(f"📁 템플릿 존재: {templates_dir.exists()}")

        # 템플릿이 없으면 다른 가능한 경로 확인
        if not templates_dir.exists():
            possible_paths = [
                Path("/app/src/templates"),
                Path("/templates"),
                current_file.parent.parent / "templates",
            ]
            for path in possible_paths:
                logger.debug(f"🔍 대체 경로 확인: {path} (존재: {path.exists()})")
                if path.exists():
                    templates_dir = path
                    logger.info(f"✅ 템플릿 경로 발견: {templates_dir}")
                    break
    else:
        # 로컬 개발 환경: src/core/main.py -> src/templates
        src_root = current_file.parent.parent
        templates_dir = src_root / "templates"
        static_dir = src_root / "static"
        logger.info(f"🏠 로컬 환경 감지: {current_file}")
        logger.info(f"📁 템플릿 경로: {templates_dir}")

    # 템플릿 디렉토리가 없으면 생성 (안전장치)
    templates_dir.mkdir(exist_ok=True)
    if static_dir:
        static_dir.mkdir(exist_ok=True)

    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(static_dir) if static_dir.exists() else None,
    )

    # Add custom Jinja2 filter for environment variables

    @app.template_filter("getenv")
    def getenv_filter(key, default=""):
        """Jinja2 filter to get environment variables"""
        return os.getenv(key, default)

    # Dashboard blueprint removed - user request

    # Register optimized unified API (replaces 8 scattered blueprints)
    try:
        from core.routes.blacklist_api import blacklist_api_bp

        app.register_blueprint(blacklist_api_bp, url_prefix="/api")
        logger.info("✅ Optimized API routes registered - unified structure")
    except ImportError as e:
        logger.error(f"❌ Optimized API routes registration failed: {e}")

    # Register statistics API
    try:
        from core.routes.statistics_api import statistics_api_bp

        app.register_blueprint(statistics_api_bp, url_prefix="/api")
        logger.info("✅ Statistics API routes registered")
    except ImportError as e:
        logger.error(f"❌ Statistics API routes registration failed: {e}")

    # Register web routes (web UI only)
    try:
        from core.routes.web_routes import web_bp

        # Check if blueprint is already registered to avoid conflicts
        if 'web' not in app.blueprints:
            app.register_blueprint(web_bp)
            logger.info("✅ Web routes registered")
        else:
            logger.info("ℹ️ Web routes already registered, skipping")
    except ImportError as e:
        logger.error(f"❌ Web routes registration failed: {e}")

    # Register REGTECH admin routes (Credential Management & Collection)
    try:
        from core.routes.regtech_admin_routes import regtech_admin_bp
        app.register_blueprint(regtech_admin_bp, url_prefix="/admin")
        logger.info("✅ REGTECH admin routes registered")
    except ImportError as e:
        logger.error(f"❌ REGTECH admin routes registration failed: {e}")

    # Register Collection API Blueprint (for collection_api.py routes)
    try:
        from core.routes.api import api_bp
        # Import collection_api to register its routes with api_bp
        from core.routes.api import collection_api
        app.register_blueprint(api_bp)
        logger.info("✅ Collection API Blueprint registered")
    except ImportError as e:
        logger.error(f"❌ Collection API Blueprint registration failed: {e}")

    # Register Database API routes
    try:
        from core.routes.api.database_api import database_api_bp
        app.register_blueprint(database_api_bp)
        logger.info("✅ Database API routes registered")
    except ImportError as e:
        logger.error(f"❌ Database API routes registration failed: {e}")

    # Register IP Management API routes
    try:
        from core.routes.api.ip_management_api import ip_management_api_bp
        app.register_blueprint(ip_management_api_bp)
        logger.info("✅ IP Management API routes registered")
    except ImportError as e:
        logger.error(f"❌ IP Management API routes registration failed: {e}")

    # Register FortiGate API routes
    try:
        from core.routes.fortinet_api import fortinet_api_bp
        app.register_blueprint(fortinet_api_bp)
        logger.info("✅ FortiGate API routes registered")
    except ImportError as e:
        logger.error(f"❌ FortiGate API routes registration failed: {e}")

    # Register Collection Panel routes (Credential Management UI)
    try:
        from core.routes.collection_panel import collection_bp
        app.register_blueprint(collection_bp)
        logger.info("✅ Collection panel routes registered")
    except ImportError as e:
        logger.error(f"❌ Collection panel routes registration failed: {e}")

    # Register Collection API Routes (Simple Trigger)
    try:
        from core.routes.collection_routes_simple import collection_simple_bp
        app.register_blueprint(collection_simple_bp)
        logger.info("✅ Collection API routes registered")
    except ImportError as e:
        logger.error(f"❌ Collection API routes registration failed: {e}")

    # Register Multi-Source Collection API Routes (REGTECH + SECUDIUM)
    try:
        from core.routes.multi_collection_api import multi_collection_bp
        app.register_blueprint(multi_collection_bp)
        logger.info("✅ Multi-source collection API routes registered")
    except ImportError as e:
        logger.error(f"❌ Multi-source collection API routes registration failed: {e}")

    # Register system routes (health check only)
    try:
        from core.routes.system_routes import system_bp

        app.register_blueprint(system_bp)
        logger.info("✅ System routes registered")
    except ImportError as e:
        logger.error(f"❌ System routes registration failed: {e}")

    # Monitoring routes removed - not needed for simple blacklist management

    # Additional routes removed - keeping only core blacklist functionality

    # Metric collection removed - not needed for simple blacklist system

    # Setup Prometheus Metrics
    try:
        from core.monitoring import setup_metrics, metrics_view

        setup_metrics(app)

        # Add /metrics endpoint
        app.add_url_rule("/metrics", "metrics", metrics_view)
        logger.info("✅ Prometheus metrics endpoint registered at /metrics")
    except ImportError as e:
        logger.warning(f"⚠️ Prometheus metrics not available: {e}")

    # Setup Error Monitoring Integration
    try:
        from flask import request

        @app.errorhandler(500)
        def handle_500_error(error):
            """Internal Server Error Handler with GitHub Issue Creation"""
            try:
                _request_info = {
                    "url": request.url,
                    "method": request.method,
                    "remote_addr": request.remote_addr,
                    "user_agent": (
                        request.user_agent.string if request.user_agent else "Unknown"
                    ),
                    "endpoint": request.endpoint,
                    "mode": "full",
                }

                # Error logging (GitHub monitoring removed)
                app.logger.error(f"500 Error: {error}")

            except Exception as e:
                app.logger.error(f"Error monitoring failed: {e}")

            return (
                jsonify(
                    {
                        "error": "Internal Server Error",
                        "message": "An internal error occurred and has been automatically reported",
                        "timestamp": datetime.now().isoformat(),
                        "mode": "full",
                    }
                ),
                500,
            )

        # Generic exception handler removed - let Flask handle 404s naturally

        logger.info("✅ Error monitoring integration enabled")

    except ImportError as e:
        logger.warning(f"⚠️ Error monitoring not available: {e}")

    @app.route("/health", methods=["GET", "POST"])
    def health_check():
        """헬스체크 엔드포인트"""
        try:
            return jsonify(
                {
                    "status": "healthy",
                    "mode": "full",
                    "templates": str(templates_dir),
                    "templates_exist": templates_dir.exists(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "mode": "full",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                500,
            )

    return app


# Create app instance for WSGI servers (like Gunicorn)
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2542))
    logger.info(f"🚀 Starting Full Mode Flask application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
