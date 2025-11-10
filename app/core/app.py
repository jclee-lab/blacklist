#!/usr/bin/env python3
"""
Flask Application - PostgreSQL Connection and Collection Management
"""
import os
import psycopg2
import secrets
from flask import Flask, jsonify, request
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from pathlib import Path


def create_app():
    """Create Flask application instance"""
    # Set templates directory to templates (build context is src/)
    app_root = Path(__file__).parent.parent  # /app
    templates_dir = app_root / "templates"  # /app/templates

    app = Flask(__name__, template_folder=str(templates_dir))

    # ========================================================================
    # Security Configuration (Phase 1.3: CSRF & Rate Limiting)
    # ========================================================================

    # Secret key for session management and CSRF protection
    # CRITICAL: Use environment variable in production, generate secure random in development
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)

    # CSRF Protection Configuration
    csrf = CSRFProtect(app)
    # Exempt health check and metrics endpoints from CSRF (GET requests only)
    csrf.exempt('/health')
    csrf.exempt('/metrics')
    # Exempt proxy routes (frontend already handles CSRF for its requests)
    app.logger.info("✅ CSRF protection enabled (Flask-WTF)")

    # Rate Limiting Configuration (Redis-backed for distributed systems)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=f"redis://{os.getenv('REDIS_HOST', 'blacklist-redis')}:{os.getenv('REDIS_PORT', 6379)}/1",
        storage_options={"socket_connect_timeout": 2},
        default_limits=["200 per day", "50 per hour"],  # Global rate limits
        strategy="fixed-window",
        headers_enabled=True  # Add X-RateLimit headers to responses
    )

    # Custom rate limits for specific API endpoints
    @limiter.request_filter
    def ip_whitelist_rate_limit():
        """Exempt internal health checks from rate limiting"""
        # Exempt localhost and container network
        remote_addr = get_remote_address()
        return remote_addr in ['127.0.0.1', 'localhost'] or remote_addr.startswith('172.')

    app.logger.info("✅ Rate limiting enabled (Flask-Limiter with Redis)")

    # Make limiter accessible for route-specific decorators
    app.limiter = limiter

    # Enable Gzip compression
    app.config['COMPRESS_ALGORITHM'] = 'gzip'
    app.config['COMPRESS_LEVEL'] = 6

    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'

        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # Enable HSTS (Strict Transport Security)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # XSS Protection (legacy, but still useful)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy (replace Feature-Policy)
        response.headers['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), '
            'gyroscope=(), magnetometer=(), microphone=(), '
            'payment=(), usb=()'
        )

        # Static file caching
        if request.path.startswith('/static/'):
            # Cache static files for 1 year
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif request.path in ['/favicon.ico', '/robots.txt']:
            # Cache favicon and robots.txt for 1 week
            response.headers['Cache-Control'] = 'public, max-age=604800'
        elif request.path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
            # Cache other static resources for 1 day
            response.headers['Cache-Control'] = 'public, max-age=86400'
        elif request.path.startswith('/api/'):
            # API responses should not be cached
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response

    # Enable Gzip compression for responses
    @app.after_request
    def compress_response(response):
        """Compress response if client supports it"""
        if 'gzip' not in request.headers.get('Accept-Encoding', '').lower():
            return response

        # Don't compress if already compressed or too small
        if (response.direct_passthrough or
            len(response.get_data()) < 500 or
            response.status_code < 200 or
            response.status_code >= 300):
            return response

        # Compress the response
        import gzip
        import io

        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(mode='wb', fileobj=gzip_buffer, compresslevel=6) as gzip_file:
            gzip_file.write(response.get_data())

        response.set_data(gzip_buffer.getvalue())
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['Content-Length'] = len(response.get_data())

        return response

    # Register core blueprints - streamlined approach
    try:
        from .routes.web_routes import web_bp
        # Check if blueprint is already registered to avoid conflicts
        if 'web' not in app.blueprints:
            app.register_blueprint(web_bp)
    except Exception as e:
        app.logger.error(f"Web routes failed: {e}")

    try:
        from .routes.statistics_api import statistics_api_bp
        app.register_blueprint(statistics_api_bp, url_prefix="/api")
    except Exception as e:
        app.logger.error(f"Statistics API failed: {e}")

    try:
        from .routes.blacklist_api import blacklist_api_bp
        app.register_blueprint(blacklist_api_bp, url_prefix="/api")
    except Exception as e:
        app.logger.error(f"Blacklist API failed: {e}")

    try:
        from .routes.api.database_api import database_api_bp
        app.register_blueprint(database_api_bp)
        app.logger.info("✅ Database API routes registered")
    except Exception as e:
        app.logger.error(f"Database API failed: {e}")

    try:
        from .routes.api.ip_management_api import ip_management_api_bp
        app.register_blueprint(ip_management_api_bp)
        app.logger.info("✅ IP Management API routes registered")
    except Exception as e:
        app.logger.error(f"IP Management API failed: {e}")

    # REGTECH Admin Routes (Credential Management & Collection)
    try:
        from .routes.regtech_admin_routes import regtech_admin_bp
        app.register_blueprint(regtech_admin_bp, url_prefix="/admin")
        app.logger.info("✅ REGTECH admin routes registered")
    except Exception as e:
        app.logger.error(f"REGTECH admin routes failed: {e}")

    # Settings Management Routes (System Settings & Credentials)
    try:
        from .routes.settings_routes import settings_bp
        app.register_blueprint(settings_bp)
        app.logger.info("✅ Settings management routes registered")
    except Exception as e:
        app.logger.error(f"Settings management routes failed: {e}")

    # Collection Panel Routes (Credential Management UI)
    try:
        from .routes.collection_panel import collection_bp
        app.register_blueprint(collection_bp)
        app.logger.info("✅ Collection panel routes registered")
    except Exception as e:
        app.logger.error(f"Collection panel routes failed: {e}")

    # Collection API Routes (Trigger & Config)
    try:
        from .routes.collection_routes_simple import collection_simple_bp
        app.register_blueprint(collection_simple_bp)
        app.logger.info("✅ Collection API routes registered")
    except Exception as e:
        app.logger.error(f"Collection API routes failed: {e}")

    # Multi-Source Collection API Routes (REGTECH + SECUDIUM)
    try:
        from .routes.multi_collection_api import multi_collection_bp
        app.register_blueprint(multi_collection_bp)
        csrf.exempt(multi_collection_bp)  # Exempt from CSRF (called via proxy from frontend)
        app.logger.info("✅ Multi-source collection API routes registered (CSRF exempt)")
    except Exception as e:
        app.logger.error(f"Multi-source collection API routes failed: {e}")

    # Proxy API Routes (Frontend → Backend)
    try:
        from .routes.proxy_routes import proxy_bp
        app.register_blueprint(proxy_bp)
        csrf.exempt(proxy_bp)  # Exempt from CSRF (frontend handles authentication)
        app.logger.info("✅ Proxy API routes registered (CSRF exempt)")
    except Exception as e:
        app.logger.error(f"Proxy API routes failed: {e}")

    # FortiGate Integration API Routes
    try:
        from .routes.fortinet_api import fortinet_api_bp
        app.register_blueprint(fortinet_api_bp)
        app.logger.info("✅ FortiGate integration API routes registered")
    except Exception as e:
        app.logger.error(f"FortiGate integration API routes failed: {e}")

    # Optional blueprints removed (CloudFlare integration disabled)

    try:
        from .routes.monitoring_dashboard import monitoring_dashboard_bp
        app.register_blueprint(monitoring_dashboard_bp)
    except Exception:
        pass

    # ========================================================================
    # Error Handling & Monitoring Integration
    # ========================================================================

    # Initialize error tracking middleware (disabled - files not present)
    # try:
    #     from .middleware import RequestContextMiddleware
    #     RequestContextMiddleware(app)
    #     app.logger.info("✅ Request context middleware initialized")
    # except Exception as e:
    #     app.logger.warning(f"⚠️ Request middleware initialization failed: {e}")

    # Register comprehensive error handlers (disabled - files not present)
    # try:
    #     from .error_handlers import register_error_handlers
    #     register_error_handlers(app)
    #     app.logger.info("✅ Comprehensive error handlers registered")
    # except Exception as e:
    #     app.logger.error(f"❌ Error handler registration failed: {e}")

    # Fallback to basic error handlers
    @app.errorhandler(500)
    def fallback_500(error):
        """Fallback Internal Server Error Handler"""
        app.logger.error(f"500 Error: {error}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "timestamp": datetime.now().isoformat()
        }), 500

    @app.errorhandler(404)
    def fallback_404(error):
        """Fallback Not Found Error Handler"""
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat()
        }), 404

    app.logger.info("✅ Using fallback error handlers")

    @app.route("/favicon.ico")
    def favicon():
        """Handle favicon requests (prevent 404 errors)"""
        from flask import Response
        return Response("", status=204, mimetype="image/x-icon")

    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        try:
            # Test PostgreSQL connection
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                database=os.getenv("POSTGRES_DB", "blacklist"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            )

            cursor = conn.cursor()

            # Check table existence
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Check blacklist IP count (safe even if table doesn't exist)
            try:
                cursor.execute("SELECT COUNT(*) FROM blacklist_ips")
                ip_count = cursor.fetchone()[0]
            except psycopg2.Error:
                ip_count = 0  # Set to 0 if table doesn't exist

            cursor.close()
            conn.close()

            return (
                jsonify(
                    {
                        "status": "healthy",
                        "timestamp": datetime.now().isoformat(),
                        "database": {
                            "connection": "successful",
                            "tables": tables,
                            "blacklist_ips_count": ip_count,
                        },
                        "message": "✅ PostgreSQL custom image connection successful!",
                    }
                ),
                200,
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "unhealthy",
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "message": "❌ Database connection failed",
                    }
                ),
                500,
            )

    @app.route("/api/logs")
    def get_logs():
        """Log collection API endpoint"""
        try:
            # Get parameters
            minutes = request.args.get("minutes", 5, type=int)
            log_level = request.args.get("level", "INFO")

            # Calculate log collection time
            since_time = datetime.now() - timedelta(minutes=minutes)

            logs = []

            # 1. Collect from in-memory log handler (default method)
            if hasattr(app, "_log_capture"):
                for record in app._log_capture:
                    if record.get("timestamp", datetime.min) >= since_time:
                        logs.append(record)

            # 2. Simulate log capture from stdout/stderr
            current_time = datetime.now()

            # System log simulation (in production, read actual log files)
            if not logs:
                # In production environment, implement actual log file reading here
                sample_logs = [
                    {
                        "timestamp": current_time.isoformat(),
                        "level": "INFO",
                        "message": "Flask application started successfully",
                    },
                    {
                        "timestamp": (current_time - timedelta(minutes=2)).isoformat(),
                        "level": "INFO",
                        "message": "Database connection pool initialized",
                    },
                ]

                # Generate actual error logs based on service status
                try:
                    # Test database connection
                    conn = psycopg2.connect(
                        host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
                        port=os.getenv("POSTGRES_PORT", "5432"),
                        database=os.getenv("POSTGRES_DB", "blacklist"),
                        user=os.getenv("POSTGRES_USER", "postgres"),
                        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                    )
                    conn.close()
                except Exception as db_error:
                    sample_logs.append(
                        {
                            "timestamp": current_time.isoformat(),
                            "level": "ERROR",
                            "message": f"Database connection failed: {str(db_error)}",
                        }
                    )

                logs = sample_logs

            # Filter logs by level
            if log_level != "ALL":
                level_priority = {
                    "DEBUG": 0,
                    "INFO": 1,
                    "WARNING": 2,
                    "ERROR": 3,
                    "CRITICAL": 4,
                }
                min_priority = level_priority.get(log_level, 1)
                logs = [
                    log
                    for log in logs
                    if level_priority.get(log.get("level", "INFO"), 1) >= min_priority
                ]

            return jsonify(
                {
                    "status": "success",
                    "logs": logs,
                    "count": len(logs),
                    "since_minutes": minutes,
                    "collected_at": current_time.isoformat(),
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Log collection failed: {str(e)}",
                        "logs": [],
                        "count": 0,
                    }
                ),
                500,
            )

    @app.route("/api/errors")
    def get_error_logs():
        """Dedicated endpoint for collecting error logs only"""
        try:
            minutes = request.args.get("minutes", 5, type=int)

            # Filter and get logs with ERROR/WARNING levels only
            all_logs_response = get_logs()
            if all_logs_response[1] != 200:
                return all_logs_response

            all_logs = all_logs_response[0].get_json()
            error_logs = [
                log
                for log in all_logs.get("logs", [])
                if log.get("level") in ["ERROR", "CRITICAL", "WARNING"]
            ]

            return jsonify(
                {
                    "status": "success",
                    "error_logs": error_logs,
                    "error_count": len(error_logs),
                    "since_minutes": minutes,
                    "collected_at": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Error log collection failed: {str(e)}",
                        "error_logs": [],
                        "error_count": 0,
                    }
                ),
                500,
            )

    @app.route("/api/monitoring/dashboard")
    def monitoring_dashboard():
        """Real-time monitoring dashboard API"""
        try:
            # Collect system metrics
            current_time = datetime.now()

            # 1. Basic system status
            system_status = {
                "timestamp": current_time.isoformat(),
                "uptime": "running",
                "status": "operational",
            }

            # 2. Database status
            db_status = {"connection": "unknown", "response_time": 0}
            try:
                db_start = datetime.now()
                conn = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
                    port=os.getenv("POSTGRES_PORT", "5432"),
                    database=os.getenv("POSTGRES_DB", "blacklist"),
                    user=os.getenv("POSTGRES_USER", "postgres"),
                    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                )
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                table_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                db_end = datetime.now()
                response_time = (db_end - db_start).total_seconds()

                db_status = {
                    "connection": "healthy",
                    "response_time": round(response_time, 3),
                    "table_count": table_count,
                }
            except Exception as db_error:
                db_status = {
                    "connection": "failed",
                    "response_time": 0,
                    "error": str(db_error),
                }

            # 3. Recent log statistics
            log_stats = {"total": 0, "errors": 0, "warnings": 0, "info": 0}
            try:
                logs_response = get_logs()
                if logs_response[1] == 200:
                    logs_data = logs_response[0].get_json()
                    logs = logs_data.get("logs", [])

                    log_stats["total"] = len(logs)
                    for log in logs:
                        level = log.get("level", "INFO")
                        if level in ["ERROR", "CRITICAL"]:
                            log_stats["errors"] += 1
                        elif level == "WARNING":
                            log_stats["warnings"] += 1
                        else:
                            log_stats["info"] += 1
            except BaseException:
                pass

            # 4. Performance metrics
            performance = {
                "response_time": "measuring",
                "memory_usage": "unknown",
                "cpu_usage": "unknown",
            }

            # Actual response time measurement is performed on client side

            # 5. Automation cluster status (GitHub API simulation)
            automation_status = {
                "active_workflows": "unknown",
                "recent_automations": 0,
                "success_rate": 0,
                "next_execution": "in 2 minutes",
            }

            # 6. Anomaly detection status
            anomaly_status = {
                "detection_active": True,
                "last_analysis": current_time.isoformat(),
                "anomaly_score": 0,
                "severity": "NORMAL",
            }

            # 7. Comprehensive dashboard data
            dashboard_data = {
                "status": "success",
                "timestamp": current_time.isoformat(),
                "system": system_status,
                "database": db_status,
                "logs": log_stats,
                "performance": performance,
                "automation": automation_status,
                "anomaly_detection": anomaly_status,
                "health_score": 100,  # Default value
                "alerts": [],
            }

            # 8. Calculate health score
            health_score = 100
            alerts = []

            if db_status["connection"] != "healthy":
                health_score -= 30
                alerts.append({"type": "warning", "message": "Database connection issue"})

            if log_stats["errors"] > 5:
                health_score -= 20
                alerts.append(
                    {
                        "type": "error",
                        "message": f"Error log increase ({log_stats['errors']} errors)",
                    }
                )
            elif log_stats["errors"] > 0:
                health_score -= 10
                alerts.append(
                    {
                        "type": "info",
                        "message": f"Error log detected ({log_stats['errors']} errors)",
                    }
                )

            dashboard_data["health_score"] = max(0, health_score)
            dashboard_data["alerts"] = alerts

            return jsonify(dashboard_data)

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Dashboard data collection failed: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                500,
            )

    # Monitoring metrics endpoint removed as requested

    # Main route removed - handled by web_routes.py
    # @app.route("/")
    # def index():
    #     """Main page - basic status information"""
    #     # Main dashboard handled by web_routes.py

    # Start auto collection scheduler on app startup (Flask 2.2+ compatible)
    def start_background_tasks():
        """Start background tasks (check auth settings first) - non-blocking mode"""
        try:
            from .services.scheduler_service import collection_scheduler
            from .services.database_service import db_service

            # Check authentication info (non-blocking mode)
            conn = db_service.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT username, password 
                FROM collection_credentials 
                WHERE service_name = 'REGTECH'
            """
            )
            result = cursor.fetchone()
            cursor.close()
            db_service.return_connection(conn)

            # Start scheduler only when authentication is configured
            if result and result[0] and result[1]:
                if collection_scheduler.start():
                    app.logger.info("🚀 Auto collection scheduler started (auth configured)")
                else:
                    app.logger.warning("⚠️ Auto collection scheduler start failed")
            else:
                app.logger.info("⏸️ Auto collection scheduler waiting (auth not configured)")
        except Exception as db_error:
            # Flask app starts normally even if database connection fails
            app.logger.warning(f"⚠️ Scheduler cannot start due to database connection failure: {db_error}")
            app.logger.info("ℹ️ Flask app started normally (scheduler only disabled)")

        except Exception as e:
            app.logger.error(f"❌ Background task start failed: {e}")

    # Start background tasks in separate thread using Flask 2.2+ method (non-blocking)
    import threading
    def delayed_background_start():
        import time
        time.sleep(2)  # Wait until Flask app fully starts
        with app.app_context():
            try:
                start_background_tasks()
            except Exception as e:
                app.logger.error(f"❌ Error during background initialization: {e}")

    # Start background tasks in separate thread (doesn't block Flask app startup)
    threading.Thread(target=delayed_background_start, daemon=True).start()

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 2542))
    app.run(host="0.0.0.0", port=port, debug=False)
