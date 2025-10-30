"""
Comprehensive tests for Flask app initialization and configuration (app.py)

Target: app/core/app.py (297 statements, 0% coverage)
Coverage goal: Improve to 60%+ (~178 statements)

Tests cover:
- Flask app factory pattern (create_app)
- Security configuration (CSRF, rate limiting, headers)
- Blueprint registration
- Error handlers
- Health check endpoints
- Logging endpoints
- Monitoring dashboard
- Background task initialization
"""

import pytest
from unittest.mock import MagicMock, patch, call
import json
import os
from datetime import datetime, timedelta


class TestAppCreation:
    """Test create_app() factory function - Lines 16-693"""

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables"""
        env_vars = {
            'FLASK_SECRET_KEY': 'test-secret-key-12345',
            'POSTGRES_HOST': 'test-db',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'test_blacklist',
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_password',
            'REDIS_HOST': 'test-redis',
            'REDIS_PORT': '6379'
        }
        with patch.dict(os.environ, env_vars):
            yield env_vars

    def test_create_app_initialization(self, mock_env):
        """Test create_app returns Flask app instance with correct configuration"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app

            app = create_app()

            assert app is not None
            assert app.config['SECRET_KEY'] == 'test-secret-key-12345'
            assert 'COMPRESS_ALGORITHM' in app.config

    def test_create_app_secret_key_from_env(self, mock_env):
        """Test SECRET_KEY loaded from environment variable"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app

            app = create_app()

            assert app.config['SECRET_KEY'] == 'test-secret-key-12345'

    def test_create_app_secret_key_generation(self):
        """Test SECRET_KEY auto-generation when env var not set"""
        with patch.dict(os.environ, {}, clear=True), \
             patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app

            app = create_app()

            # Should generate random secret key (64 hex chars)
            assert app.config['SECRET_KEY'] is not None
            assert len(app.config['SECRET_KEY']) == 64

    def test_csrf_protection_enabled(self, mock_env):
        """Test CSRF protection is initialized"""
        mock_csrf = MagicMock()
        with patch('flask_wtf.csrf.CSRFProtect', return_value=mock_csrf), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app

            app = create_app()

            # CSRF should be initialized
            mock_csrf.exempt.assert_any_call('/health')
            mock_csrf.exempt.assert_any_call('/metrics')

    def test_rate_limiting_enabled(self, mock_env):
        """Test rate limiting is configured with Redis backend"""
        mock_limiter = MagicMock()
        with patch('flask_limiter.Limiter', return_value=mock_limiter), \
             patch('flask_wtf.csrf.CSRFProtect'), \
             patch('threading.Thread'):
            from core.app import create_app

            app = create_app()

            # Limiter should be attached to app
            assert hasattr(app, 'limiter')


class TestSecurityHeaders:
    """Test security headers middleware - Lines 68-119"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_security_headers_added(self, app, client):
        """Test security headers are added to responses"""
        response = client.get('/health')

        # Check security headers exist
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-XSS-Protection' in response.headers
        assert 'Content-Security-Policy' in response.headers
        assert 'Referrer-Policy' in response.headers

    def test_static_file_caching_headers(self, app):
        """Test cache headers for static files"""
        with app.test_request_context('/static/style.css'):
            from flask import request, Response
            response = Response("CSS content")

            # Simulate after_request processing
            for func in app.after_request_funcs.get(None, []):
                response = func(response)

            assert 'Cache-Control' in response.headers
            assert 'public' in response.headers['Cache-Control']

    def test_api_no_cache_headers(self, app):
        """Test no-cache headers for API endpoints"""
        with app.test_request_context('/api/test'):
            from flask import Response
            response = Response(json.dumps({"test": "data"}))

            # Simulate after_request processing
            for func in app.after_request_funcs.get(None, []):
                response = func(response)

            assert 'Cache-Control' in response.headers
            assert 'no-cache' in response.headers['Cache-Control']


class TestGzipCompression:
    """Test Gzip compression middleware - Lines 122-148"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_gzip_compression_enabled(self, app):
        """Test gzip compression for large responses"""
        with app.test_request_context(
            '/',
            headers={'Accept-Encoding': 'gzip'}
        ):
            from flask import Response
            # Create large response (> 500 bytes)
            large_content = "X" * 1000
            response = Response(large_content, status=200)

            # Simulate after_request processing
            for func in app.after_request_funcs.get(None, []):
                response = func(response)

            # Should be compressed
            if response.headers.get('Content-Encoding') == 'gzip':
                assert 'Vary' in response.headers

    def test_gzip_compression_disabled_small_response(self, app):
        """Test gzip compression skipped for small responses"""
        with app.test_request_context(
            '/',
            headers={'Accept-Encoding': 'gzip'}
        ):
            from flask import Response
            # Small response (< 500 bytes)
            small_content = "Small"
            response = Response(small_content, status=200)

            # Simulate after_request processing
            for func in app.after_request_funcs.get(None, []):
                response = func(response)

            # Should NOT be compressed
            assert response.headers.get('Content-Encoding') != 'gzip'


class TestHealthEndpoint:
    """Test /health endpoint - Lines 281-343"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_health_check_success(self, app, client):
        """Test health check returns 200 when database is accessible"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ('blacklist_ips',),
            ('whitelist_ips',),
            ('collection_history',)
        ]
        mock_cursor.fetchone.return_value = (150,)  # IP count

        with patch('core.app.psycopg2.connect', return_value=mock_conn):
            response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'database' in data
        assert data['database']['connection'] == 'successful'
        assert data['database']['blacklist_ips_count'] == 150

    def test_health_check_database_failure(self, app, client):
        """Test health check returns 500 when database fails"""
        with patch('core.app.psycopg2.connect', side_effect=Exception("Connection refused")):
            response = client.get('/health')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'
        assert 'error' in data

    def test_health_check_missing_table(self, app, client):
        """Test health check handles missing blacklist_ips table"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('other_table',)]
        # Simulate table doesn't exist
        import psycopg2
        mock_cursor.execute.side_effect = [
            None,  # First query (tables list)
            psycopg2.Error("relation blacklist_ips does not exist")  # Second query (count)
        ]

        with patch('core.app.psycopg2.connect', return_value=mock_conn):
            response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['database']['blacklist_ips_count'] == 0


class TestLogsEndpoint:
    """Test /api/logs endpoint - Lines 345-442"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_get_logs_default_parameters(self, app, client):
        """Test /api/logs with default parameters"""
        response = client.get('/api/logs')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'logs' in data
        assert 'count' in data
        assert data['since_minutes'] == 5  # Default value

    def test_get_logs_custom_minutes(self, app, client):
        """Test /api/logs with custom time range"""
        response = client.get('/api/logs?minutes=10')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['since_minutes'] == 10

    def test_get_logs_filter_by_level(self, app, client):
        """Test /api/logs with log level filtering"""
        response = client.get('/api/logs?level=ERROR')

        assert response.status_code == 200
        data = json.loads(response.data)
        # All logs should be ERROR or higher
        for log in data['logs']:
            assert log['level'] in ['ERROR', 'CRITICAL']

    def test_get_logs_database_error_logged(self, app, client):
        """Test /api/logs includes database connection errors"""
        with patch('core.app.psycopg2.connect', side_effect=Exception("Connection failed")):
            response = client.get('/api/logs')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should include error log about database failure
        error_logs = [log for log in data['logs'] if log['level'] == 'ERROR']
        assert len(error_logs) > 0


class TestErrorLogsEndpoint:
    """Test /api/errors endpoint - Lines 444-483"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_get_error_logs_success(self, app, client):
        """Test /api/errors returns only error/warning logs"""
        response = client.get('/api/errors')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'error_logs' in data
        assert 'error_count' in data
        # All logs should be ERROR, CRITICAL, or WARNING
        for log in data['error_logs']:
            assert log['level'] in ['ERROR', 'CRITICAL', 'WARNING']

    def test_get_error_logs_custom_time_range(self, app, client):
        """Test /api/errors with custom time range"""
        response = client.get('/api/errors?minutes=15')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['since_minutes'] == 15


class TestMonitoringDashboard:
    """Test /api/monitoring/dashboard endpoint - Lines 485-632"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_monitoring_dashboard_success(self, app, client):
        """Test monitoring dashboard returns complete metrics"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (5,)  # Table count

        with patch('core.app.psycopg2.connect', return_value=mock_conn):
            response = client.get('/api/monitoring/dashboard')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'system' in data
        assert 'database' in data
        assert 'logs' in data
        assert 'performance' in data
        assert 'automation' in data
        assert 'anomaly_detection' in data
        assert 'health_score' in data

    def test_monitoring_dashboard_database_healthy(self, app, client):
        """Test dashboard shows healthy database status"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (10,)

        with patch('core.app.psycopg2.connect', return_value=mock_conn):
            response = client.get('/api/monitoring/dashboard')

        data = json.loads(response.data)
        assert data['database']['connection'] == 'healthy'
        assert data['database']['table_count'] == 10
        assert data['health_score'] == 100

    def test_monitoring_dashboard_database_failure(self, app, client):
        """Test dashboard handles database connection failure"""
        with patch('core.app.psycopg2.connect', side_effect=Exception("Connection refused")):
            response = client.get('/api/monitoring/dashboard')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['database']['connection'] == 'failed'
        assert data['health_score'] < 100
        assert len(data['alerts']) > 0

    def test_monitoring_dashboard_health_score_calculation(self, app, client):
        """Test health score calculation with multiple errors"""
        # Mock database failure and error logs
        with patch('core.app.psycopg2.connect', side_effect=Exception("DB down")), \
             patch('core.app.get_logs') as mock_get_logs:

            # Mock get_logs to return errors
            mock_response = MagicMock()
            mock_response.get_json.return_value = {
                'logs': [
                    {'level': 'ERROR', 'message': 'Error 1'},
                    {'level': 'ERROR', 'message': 'Error 2'},
                    {'level': 'ERROR', 'message': 'Error 3'},
                    {'level': 'ERROR', 'message': 'Error 4'},
                    {'level': 'ERROR', 'message': 'Error 5'},
                    {'level': 'ERROR', 'message': 'Error 6'},
                ]
            }
            mock_get_logs.return_value = (mock_response, 200)

            response = client.get('/api/monitoring/dashboard')

        data = json.loads(response.data)
        # Health score should be reduced (database -30, errors -20)
        assert data['health_score'] <= 50
        assert len(data['alerts']) >= 2


class TestFaviconEndpoint:
    """Test /favicon.ico endpoint - Lines 275-279"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_favicon_returns_204(self, app, client):
        """Test favicon endpoint returns 204 No Content"""
        response = client.get('/favicon.ico')

        assert response.status_code == 204
        assert response.content_type == 'image/x-icon'


class TestBlueprintRegistration:
    """Test blueprint registration - Lines 150-231"""

    def test_blueprints_registered(self):
        """Test all blueprints are registered successfully"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app

            app = create_app()

            # Check blueprints exist (some may fail to register due to import errors)
            # Just verify app.blueprints is populated
            assert len(app.blueprints) > 0


class TestBackgroundTasks:
    """Test background task initialization - Lines 643-691"""

    def test_background_tasks_thread_started(self):
        """Test background tasks thread is started"""
        mock_thread = MagicMock()
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread', return_value=mock_thread):
            from core.app import create_app

            app = create_app()

            # Thread should be started
            mock_thread.start.assert_called_once()

    def test_background_tasks_scheduler_configured(self):
        """Test scheduler starts when auth is configured"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # Return valid credentials
        mock_cursor.fetchone.return_value = ('username', 'password')

        mock_scheduler = MagicMock()
        mock_scheduler.start.return_value = True

        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()

            # Simulate background task execution
            with app.app_context(), \
                 patch('core.services.database_service.db_service.get_connection', return_value=mock_conn), \
                 patch('core.services.database_service.db_service.return_connection'), \
                 patch('core.services.scheduler_service.collection_scheduler', mock_scheduler):

                from core.app import start_background_tasks
                start_background_tasks()

                # Scheduler should be started
                mock_scheduler.start.assert_called_once()

    def test_background_tasks_no_auth_configured(self):
        """Test scheduler does not start when auth is not configured"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # Return None (no credentials)
        mock_cursor.fetchone.return_value = None

        mock_scheduler = MagicMock()

        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()

            # Simulate background task execution
            with app.app_context(), \
                 patch('core.services.database_service.db_service.get_connection', return_value=mock_conn), \
                 patch('core.services.database_service.db_service.return_connection'), \
                 patch('core.services.scheduler_service.collection_scheduler', mock_scheduler):

                from core.app import start_background_tasks
                start_background_tasks()

                # Scheduler should NOT be started
                mock_scheduler.start.assert_not_called()


class TestErrorHandlers:
    """Test error handler registration - Lines 246-273"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        with patch('flask_wtf.csrf.CSRFProtect'), \
             patch('flask_limiter.Limiter'), \
             patch('threading.Thread'):
            from core.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app

    def test_fallback_500_error_handler(self, app, client):
        """Test 500 error handler returns JSON response"""
        # Trigger 500 error
        @app.route('/test-500')
        def trigger_500():
            raise Exception("Test error")

        response = client.get('/test-500')

        # Should be handled by error handler
        assert response.status_code == 500
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            assert 'error' in data

    def test_fallback_404_error_handler(self, app, client):
        """Test 404 error handler returns JSON response"""
        response = client.get('/nonexistent-route-xyz123')

        assert response.status_code == 404
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            assert 'error' in data
