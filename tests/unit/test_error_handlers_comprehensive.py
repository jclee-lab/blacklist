"""
Comprehensive tests for error_handlers.py
Target: error_handlers.py (79 statements, 0% baseline)
Phase 5.2: Error handler testing
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, Forbidden, NotFound, MethodNotAllowed, TooManyRequests


class TestBuildErrorResponse:
    """Test build_error_response() function - Lines 32-80"""

    @pytest.fixture
    def app_context(self):
        """Create Flask app context for testing"""
        from core.app import create_app
        app = create_app()
        with app.test_request_context('/test'):
            yield app

    def test_build_error_response_basic(self, app_context):
        """Test basic error response structure"""
        from core.error_handlers import build_error_response

        response, status_code = build_error_response(
            error_code="TEST_ERROR",
            message="Test message",
            status_code=400
        )

        assert status_code == 400
        assert response["error"] == "TEST_ERROR"
        assert response["message"] == "Test message"
        assert response["status_code"] == 400
        assert "timestamp" in response
        assert response["path"] == "/test"

    def test_build_error_response_with_details(self, app_context):
        """Test error response with details parameter - Lines 68-69"""
        from core.error_handlers import build_error_response

        details = {"field": "username", "constraint": "required"}
        response, status_code = build_error_response(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            status_code=422,
            details=details
        )

        assert response["details"] == details

    def test_build_error_response_with_trace(self, app_context):
        """Test error response with stack trace - Lines 72-75"""
        from core.error_handlers import build_error_response

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            response, status_code = build_error_response(
                error_code="TEST_ERROR",
                message="Error with trace",
                status_code=500,
                include_trace=True,
                exception=e
            )

            assert "trace" in response
            assert isinstance(response["trace"], list)

    def test_build_error_response_includes_request_id(self, app_context):
        """Test error response includes request ID - Lines 64-65"""
        from core.error_handlers import build_error_response
        from flask import request

        with app_context.test_request_context('/test', headers={'X-Request-ID': 'req-12345'}):
            response, status_code = build_error_response(
                error_code="TEST_ERROR",
                message="Test",
                status_code=400
            )

            assert response["request_id"] == "req-12345"
            assert response["method"] == "GET"

    def test_build_error_response_includes_help_url(self, app_context):
        """Test error response includes help URL - Line 78"""
        from core.error_handlers import build_error_response

        response, status_code = build_error_response(
            error_code="NOT_FOUND",
            message="Resource not found",
            status_code=404
        )

        assert response["help_url"] == "https://docs.jclee.me/errors/NOT_FOUND"


class TestHTTPErrorHandlers:
    """Test HTTP error handlers - Lines 87-218"""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        from core.app import create_app
        app = create_app()
        yield app

    def test_handle_400_bad_request(self, app):
        """Test 400 Bad Request handler - Lines 87-96"""
        from core.error_handlers import handle_400_bad_request

        with app.test_request_context('/api/test', method='POST'):
            error = BadRequest(description="Invalid input")
            response, status_code = handle_400_bad_request(error)

            assert status_code == 400
            assert response["error"] == "BAD_REQUEST"
            assert response["message"] == "Invalid input"
            assert response["details"]["method"] == "POST"

    def test_handle_401_unauthorized(self, app):
        """Test 401 Unauthorized handler - Lines 99-108"""
        from core.error_handlers import handle_401_unauthorized

        with app.test_request_context('/api/protected'):
            error = Unauthorized()
            response, status_code = handle_401_unauthorized(error)

            assert status_code == 401
            assert response["error"] == "UNAUTHORIZED"
            assert response["message"] == "Authentication required"
            assert response["details"]["auth_required"] is True

    def test_handle_403_forbidden(self, app):
        """Test 403 Forbidden handler - Lines 111-119"""
        from core.error_handlers import handle_403_forbidden

        with app.test_request_context('/api/admin'):
            error = Forbidden()
            response, status_code = handle_403_forbidden(error)

            assert status_code == 403
            assert response["error"] == "FORBIDDEN"
            assert response["message"] == "Insufficient permissions"

    def test_handle_404_not_found(self, app):
        """Test 404 Not Found handler - Lines 122-131"""
        from core.error_handlers import handle_404_not_found

        with app.test_request_context('/nonexistent', method='GET'):
            error = NotFound()
            response, status_code = handle_404_not_found(error)

            assert status_code == 404
            assert response["error"] == "NOT_FOUND"
            assert response["details"]["path"] == "/nonexistent"
            assert response["details"]["method"] == "GET"

    def test_handle_405_method_not_allowed(self, app):
        """Test 405 Method Not Allowed handler - Lines 134-146"""
        from core.error_handlers import handle_405_method_not_allowed

        with app.test_request_context('/api/resource', method='DELETE'):
            error = MethodNotAllowed(valid_methods=['GET', 'POST'])
            response, status_code = handle_405_method_not_allowed(error)

            assert status_code == 405
            assert response["error"] == "METHOD_NOT_ALLOWED"
            assert "DELETE" in response["message"]
            assert response["details"]["method"] == "DELETE"

    def test_handle_429_too_many_requests(self, app):
        """Test 429 Too Many Requests handler - Lines 149-158"""
        from core.error_handlers import handle_429_too_many_requests

        with app.test_request_context('/api/endpoint'):
            error = TooManyRequests()
            error.retry_after = 120
            response, status_code = handle_429_too_many_requests(error)

            assert status_code == 429
            assert response["error"] == "TOO_MANY_REQUESTS"
            assert "rate limit" in response["message"].lower()
            assert response["details"]["retry_after"] == 120

    def test_handle_500_internal_error(self, app):
        """Test 500 Internal Error handler - Lines 161-183"""
        from core.error_handlers import handle_500_internal_error

        with app.test_request_context('/api/crash'):
            error = Exception("Something went wrong")
            response, status_code = handle_500_internal_error(error)

            assert status_code == 500
            assert response["error"] == "INTERNAL_ERROR"
            assert "internal server error" in response["message"].lower()

    def test_handle_500_includes_trace_in_debug_mode(self, app):
        """Test 500 includes stack trace in DEBUG mode - Lines 175-182"""
        from core.error_handlers import handle_500_internal_error

        app.config['DEBUG'] = True

        with app.test_request_context('/api/debug'):
            error = Exception("Debug error")
            response, status_code = handle_500_internal_error(error)

            assert "trace" in response

    def test_handle_502_bad_gateway(self, app):
        """Test 502 Bad Gateway handler - Lines 186-195"""
        from core.error_handlers import handle_502_bad_gateway

        with app.test_request_context('/api/proxy'):
            error = Exception("External service failed")
            response, status_code = handle_502_bad_gateway(error)

            assert status_code == 502
            assert response["error"] == "BAD_GATEWAY"
            assert response["details"]["service"] == "external"

    def test_handle_503_service_unavailable(self, app):
        """Test 503 Service Unavailable handler - Lines 198-207"""
        from core.error_handlers import handle_503_service_unavailable

        with app.test_request_context('/api/maintenance'):
            error = Exception("Service down")
            response, status_code = handle_503_service_unavailable(error)

            assert status_code == 503
            assert response["error"] == "SERVICE_UNAVAILABLE"
            assert response["details"]["retry_after"] == 60

    def test_handle_504_gateway_timeout(self, app):
        """Test 504 Gateway Timeout handler - Lines 210-218"""
        from core.error_handlers import handle_504_gateway_timeout

        with app.test_request_context('/api/slow'):
            error = Exception("Request timeout")
            response, status_code = handle_504_gateway_timeout(error)

            assert status_code == 504
            assert response["error"] == "GATEWAY_TIMEOUT"
            assert "timeout" in response["message"].lower()


class TestApplicationErrorHandler:
    """Test handle_application_error() - Lines 225-248"""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        from core.app import create_app
        app = create_app()
        yield app

    def test_handle_application_error_500_level(self, app):
        """Test application error with 500+ status code - Lines 236-237"""
        from core.error_handlers import handle_application_error
        from core.exceptions import DatabaseConnectionError

        with app.test_request_context('/api/database'):
            error = DatabaseConnectionError("Connection failed")
            response, status_code = handle_application_error(error)

            assert status_code >= 500
            assert "timestamp" in response
            assert response["path"] == "/api/database"

    def test_handle_application_error_400_level(self, app):
        """Test application error with 400+ status code - Lines 238-239"""
        from core.error_handlers import handle_application_error
        from core.exceptions import ValidationError

        with app.test_request_context('/api/validate'):
            error = ValidationError("Invalid data")
            response, status_code = handle_application_error(error)

            assert 400 <= status_code < 500
            assert "timestamp" in response

    def test_handle_application_error_adds_timestamp(self, app):
        """Test application error adds timestamp - Lines 244-245"""
        from core.error_handlers import handle_application_error
        from core.exceptions import BaseApplicationError

        with app.test_request_context('/api/custom'):
            error = BaseApplicationError(
                error_code="CUSTOM_ERROR",
                message="Custom error message",
                status_code=400
            )
            response, status_code = handle_application_error(error)

            assert "timestamp" in response
            # Verify ISO 8601 format
            datetime.fromisoformat(response["timestamp"].replace("Z", "+00:00"))


class TestGenericExceptionHandler:
    """Test handle_generic_exception() - Lines 255-274"""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        from core.app import create_app
        app = create_app()
        yield app

    def test_handle_generic_exception_http_exception(self, app):
        """Test generic handler with HTTPException - Lines 266-271"""
        from core.error_handlers import handle_generic_exception

        with app.test_request_context('/test'):
            error = NotFound(description="Resource missing")
            response, status_code = handle_generic_exception(error)

            assert status_code == 404
            assert response["error"] == "NOT_FOUND"

    def test_handle_generic_exception_generic_error(self, app):
        """Test generic handler with non-HTTP exception - Lines 273-274"""
        from core.error_handlers import handle_generic_exception

        with app.test_request_context('/test'):
            error = ValueError("Invalid value")
            response, status_code = handle_generic_exception(error)

            assert status_code == 500
            assert response["error"] == "INTERNAL_ERROR"


class TestRegisterErrorHandlers:
    """Test register_error_handlers() - Lines 281-306"""

    def test_register_error_handlers_success(self):
        """Test error handlers registration - Lines 289-304"""
        from core.app import create_app
        from core.error_handlers import register_error_handlers

        app = create_app()

        # Check that error handlers are registered
        # Flask stores error handlers in app.error_handler_spec
        assert None in app.error_handler_spec
        assert 400 in app.error_handler_spec[None]
        assert 404 in app.error_handler_spec[None]
        assert 500 in app.error_handler_spec[None]

    def test_all_http_error_codes_registered(self):
        """Test all HTTP error codes are registered"""
        from core.app import create_app

        app = create_app()

        # Verify all HTTP error codes from the function
        http_codes = [400, 401, 403, 404, 405, 429, 500, 502, 503, 504]
        for code in http_codes:
            assert code in app.error_handler_spec[None], f"HTTP {code} handler not registered"

    def test_custom_exception_handler_registered(self):
        """Test BaseApplicationError handler registered - Line 301"""
        from core.app import create_app
        from core.exceptions import BaseApplicationError

        app = create_app()

        # BaseApplicationError should be registered
        assert BaseApplicationError in app.error_handler_spec[None]

    def test_generic_exception_handler_registered(self):
        """Test generic Exception handler registered - Line 304"""
        from core.app import create_app

        app = create_app()

        # Generic Exception should be registered
        assert Exception in app.error_handler_spec[None]


class TestErrorResponseIntegration:
    """Integration tests for error responses"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from core.app import create_app
        app = create_app()
        with app.test_client() as client:
            yield client

    def test_404_error_integration(self, client):
        """Test 404 error returns proper JSON response"""
        response = client.get('/nonexistent-endpoint')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["error"] == "NOT_FOUND"
        assert "timestamp" in data

    def test_405_error_integration(self, client):
        """Test 405 error for unsupported HTTP method"""
        # /health only supports GET/POST, try DELETE
        response = client.delete('/health')

        assert response.status_code == 405
        data = json.loads(response.data)
        assert data["error"] == "METHOD_NOT_ALLOWED"

    def test_error_response_has_help_url(self, client):
        """Test all error responses include help_url"""
        response = client.get('/nonexistent')

        data = json.loads(response.data)
        assert "help_url" in data
        assert "docs.jclee.me/errors" in data["help_url"]
