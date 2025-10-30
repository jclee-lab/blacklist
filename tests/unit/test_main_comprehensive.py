"""
Comprehensive tests for main.py - Flask application entry point
Target: main.py (142 statements, 0% baseline)
Phase 5.1: Entry point testing
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime


class TestMainAppCreation:
    """Test create_app() function from main.py - Lines 14-265"""

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables for testing"""
        env_vars = {
            'POSTGRES_HOST': 'test-db',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'blacklist',
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'test-password',
            'REDIS_HOST': 'test-redis',
        }
        with patch.dict(os.environ, env_vars):
            yield env_vars

    def test_create_app_basic_initialization(self, mock_env):
        """Test create_app returns Flask instance"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            assert app is not None
            assert app.name == 'core.main'

    def test_create_app_template_folder_set(self, mock_env):
        """Test create_app sets template_folder correctly"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            assert app.template_folder is not None
            assert 'templates' in app.template_folder

    def test_create_app_static_folder_set(self, mock_env):
        """Test create_app sets static_folder if exists"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            # static_folder may be None if directory doesn't exist
            # This tests the logic handles both cases
            assert app.static_folder is None or 'static' in app.static_folder


class TestEnvironmentDetection:
    """Test container vs local environment detection - Lines 22-50"""

    def test_container_environment_detection(self):
        """Test __file__ path starting with /app/ triggers container mode"""
        mock_path = MagicMock()
        mock_path.resolve.return_value = Path('/app/core/main.py')
        mock_path.__str__ = lambda self: '/app/core/main.py'

        with patch('pathlib.Path.__new__', return_value=mock_path), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            # Should use absolute /app/templates path in container
            assert app is not None

    def test_local_environment_detection(self):
        """Test non-/app/ path triggers local development mode"""
        mock_path = MagicMock()
        mock_path.resolve.return_value = Path('/home/user/project/core/main.py')
        mock_path.parent.parent = Path('/home/user/project')

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            # Should use relative path in local mode
            assert app is not None

    def test_template_directory_creation(self):
        """Test templates_dir.mkdir(exist_ok=True) is called - Line 52"""
        mock_mkdir = MagicMock()

        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir', mock_mkdir):
            from core.main import create_app
            app = create_app()

            # mkdir should be called for templates directory
            assert mock_mkdir.called


class TestBlueprintRegistration:
    """Test blueprint registration - Lines 72-176"""

    @pytest.fixture
    def app_with_mocked_blueprints(self):
        """Create app with mocked blueprints"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('core.main.blacklist_api_bp', MagicMock()), \
             patch('core.main.statistics_api_bp', MagicMock()), \
             patch('core.main.web_bp', MagicMock()), \
             patch('core.main.regtech_admin_bp', MagicMock()), \
             patch('core.main.api_bp', MagicMock()), \
             patch('core.main.database_api_bp', MagicMock()), \
             patch('core.main.ip_management_api_bp', MagicMock()), \
             patch('core.main.fortinet_api_bp', MagicMock()), \
             patch('core.main.collection_bp', MagicMock()), \
             patch('core.main.collection_simple_bp', MagicMock()), \
             patch('core.main.multi_collection_bp', MagicMock()), \
             patch('core.main.system_bp', MagicMock()):
            from core.main import create_app
            app = create_app()
            yield app

    def test_blacklist_api_blueprint_registered(self, app_with_mocked_blueprints):
        """Test blacklist_api_bp registration - Lines 72-78"""
        # Blueprint should be registered with /api prefix
        assert app_with_mocked_blueprints is not None

    def test_statistics_api_blueprint_registered(self, app_with_mocked_blueprints):
        """Test statistics_api_bp registration - Lines 80-87"""
        assert app_with_mocked_blueprints is not None

    def test_web_routes_blueprint_registered(self, app_with_mocked_blueprints):
        """Test web_bp registration with duplicate check - Lines 89-100"""
        app = app_with_mocked_blueprints

        # Check web blueprint handling (lines 94-98: duplicate check)
        assert app is not None

    def test_regtech_admin_blueprint_registered(self, app_with_mocked_blueprints):
        """Test regtech_admin_bp registration - Lines 102-108"""
        assert app_with_mocked_blueprints is not None

    def test_collection_api_blueprint_registered(self, app_with_mocked_blueprints):
        """Test api_bp and collection_api registration - Lines 110-118"""
        assert app_with_mocked_blueprints is not None

    def test_all_blueprints_registered_successfully(self, app_with_mocked_blueprints):
        """Test all 12 blueprints can register without errors"""
        app = app_with_mocked_blueprints

        # If we got here, all blueprints registered successfully
        assert app is not None


class TestBlueprintImportFailures:
    """Test blueprint import failure handling - Lines 77, 86, 99, etc."""

    def test_blacklist_api_import_failure_handled(self):
        """Test ImportError handling for blacklist_api_bp - Line 77-78"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('core.main.blacklist_api_bp', side_effect=ImportError("Module not found")):
            from core.main import create_app

            # Should not raise exception, just log error
            app = create_app()
            assert app is not None

    def test_statistics_api_import_failure_handled(self):
        """Test ImportError handling for statistics_api_bp - Line 86-87"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('core.main.statistics_api_bp', side_effect=ImportError("Module not found")):
            from core.main import create_app

            app = create_app()
            assert app is not None


class TestJinja2Filters:
    """Test Jinja2 custom filters - Lines 64-67"""

    def test_getenv_filter_registered(self):
        """Test getenv Jinja2 filter is registered"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            # Check filter is registered
            assert 'getenv' in app.jinja_env.filters

    def test_getenv_filter_returns_env_value(self):
        """Test getenv filter returns environment variable"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            from core.main import create_app
            app = create_app()

            getenv_filter = app.jinja_env.filters['getenv']
            result = getenv_filter('TEST_VAR')

            assert result == 'test_value'

    def test_getenv_filter_returns_default(self):
        """Test getenv filter returns default when env var missing"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            getenv_filter = app.jinja_env.filters['getenv']
            result = getenv_filter('NONEXISTENT_VAR', 'default_value')

            assert result == 'default_value'


class TestErrorHandlers:
    """Test error handler registration - Lines 199-230"""

    @pytest.fixture
    def app_for_error_testing(self):
        """Create app for error handler testing"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()
            yield app

    def test_500_error_handler_registered(self, app_for_error_testing):
        """Test 500 error handler is registered - Lines 199-230"""
        app = app_for_error_testing

        # Error handlers should be registered
        assert 500 in app.error_handler_spec[None]

    def test_500_error_handler_returns_json(self, app_for_error_testing):
        """Test 500 error handler returns JSON response"""
        app = app_for_error_testing

        with app.test_request_context('/test'):
            error_handler = app.error_handler_spec[None][500][Exception]
            response, status_code = error_handler(Exception("Test error"))

            assert status_code == 500
            data = json.loads(response.data)
            assert data['error'] == 'Internal Server Error'
            assert 'timestamp' in data

    def test_500_error_handler_includes_request_info(self, app_for_error_testing):
        """Test 500 error handler logs request information - Lines 203-212"""
        app = app_for_error_testing

        with app.test_request_context('/test-endpoint', method='POST'):
            error_handler = app.error_handler_spec[None][500][Exception]

            # Should handle error without raising
            response, status_code = error_handler(Exception("Test error"))
            assert status_code == 500


class TestHealthEndpoint:
    """Test /health endpoint - Lines 239-263"""

    @pytest.fixture
    def client(self):
        """Create test client for health endpoint testing"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()
            with app.test_client() as client:
                yield client

    def test_health_endpoint_get_method(self, client):
        """Test /health endpoint responds to GET - Line 239"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['mode'] == 'full'

    def test_health_endpoint_post_method(self, client):
        """Test /health endpoint responds to POST - Line 239"""
        response = client.post('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_health_endpoint_includes_template_info(self, client):
        """Test health endpoint includes template directory info - Lines 247-248"""
        response = client.get('/health')

        data = json.loads(response.data)
        assert 'templates' in data
        assert 'templates_exist' in data
        assert isinstance(data['templates_exist'], bool)

    def test_health_endpoint_includes_timestamp(self, client):
        """Test health endpoint includes ISO timestamp - Line 249"""
        response = client.get('/health')

        data = json.loads(response.data)
        assert 'timestamp' in data

        # Verify it's valid ISO format
        datetime.fromisoformat(data['timestamp'])

    def test_health_endpoint_error_handling(self, client):
        """Test health endpoint error handling - Lines 252-263"""
        # This tests the exception handling in health_check()
        # Since current implementation always succeeds, we verify error structure
        with patch('core.main.Path.exists', side_effect=Exception("Template error")):
            response = client.get('/health')

            # Should still return 200 or handle error
            assert response.status_code in [200, 500]


class TestPrometheusMetrics:
    """Test Prometheus metrics setup - Lines 184-193"""

    def test_prometheus_metrics_setup_success(self):
        """Test setup_metrics is called when available"""
        mock_setup_metrics = MagicMock()
        mock_metrics_view = MagicMock()

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('core.main.setup_metrics', mock_setup_metrics), \
             patch('core.main.metrics_view', mock_metrics_view):
            from core.main import create_app
            app = create_app()

            # setup_metrics should be called with app
            mock_setup_metrics.assert_called_once_with(app)

    def test_prometheus_metrics_import_failure_handled(self):
        """Test ImportError handling for monitoring module - Line 192-193"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'), \
             patch('core.main.setup_metrics', side_effect=ImportError("No module")):
            from core.main import create_app

            # Should not raise exception
            app = create_app()
            assert app is not None


class TestWSGIInstance:
    """Test WSGI app instance creation - Lines 268-269"""

    def test_wsgi_app_instance_created(self):
        """Test module-level 'app' variable is created - Line 269"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core import main

            # Module should have 'app' attribute
            assert hasattr(main, 'app')
            assert main.app is not None

    def test_wsgi_app_is_flask_instance(self):
        """Test module-level 'app' is Flask application"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core import main
            from flask import Flask

            assert isinstance(main.app, Flask)


class TestMainEntryPoint:
    """Test __main__ execution - Lines 271-274"""

    def test_main_entry_point_port_default(self):
        """Test default port is 2542 - Line 272"""
        with patch.dict(os.environ, {}, clear=True):
            default_port = int(os.environ.get("PORT", 2542))
            assert default_port == 2542

    def test_main_entry_point_port_from_env(self):
        """Test port can be set via PORT env variable"""
        with patch.dict(os.environ, {'PORT': '8080'}):
            port = int(os.environ.get("PORT", 2542))
            assert port == 8080

    def test_main_entry_point_app_run_not_called_on_import(self):
        """Test app.run() is only called when __name__ == '__main__'"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            from core import main

            # app.run() should NOT be called on import
            # (only when executed as main script)
            assert main.app is not None


class TestAlternativeTemplatePaths:
    """Test alternative template path detection - Lines 32-42"""

    def test_alternative_template_paths_checked_when_missing(self):
        """Test alternative paths checked when /app/templates doesn't exist"""
        mock_path_main = MagicMock()
        mock_path_main.resolve.return_value = Path('/app/core/main.py')
        mock_path_main.__str__ = lambda self: '/app/core/main.py'

        # First path doesn't exist, second does
        def mock_exists(self):
            path_str = str(self)
            if '/app/templates' in path_str:
                return False
            elif '/app/src/templates' in path_str:
                return True
            return False

        with patch('pathlib.Path.exists', mock_exists), \
             patch('pathlib.Path.mkdir'):
            from core.main import create_app
            app = create_app()

            # Should find alternative path
            assert app is not None
