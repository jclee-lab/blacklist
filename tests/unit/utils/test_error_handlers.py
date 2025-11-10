"""
Unit tests for error handlers utility
Tests error_handlers.py with various exception scenarios
Target: 0% → 100% coverage (8 statements)
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.mark.unit
class TestHandleException:
    """Test handle_exception function"""

    def test_handle_exception_with_context(self, app):
        """Test handle_exception with context string"""
        from core.utils.error_handlers import handle_exception

        exception = ValueError("Test error")
        context = "Database operation"

        with app.app_context():
            response, status_code = handle_exception(exception, context)

        # Verify status code
        assert status_code == 500

        # Verify response structure
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Database operation: Test error" in data["error"]
        assert "timestamp" in data

    def test_handle_exception_without_context(self, app):
        """Test handle_exception without context (empty string)"""
        from core.utils.error_handlers import handle_exception

        exception = RuntimeError("Runtime issue")

        with app.app_context():
            response, status_code = handle_exception(exception)

        # Verify status code
        assert status_code == 500

        # Verify response structure
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"] == "Runtime issue"
        assert "timestamp" in data

    def test_handle_exception_with_empty_context(self, app):
        """Test handle_exception with explicitly empty context"""
        from core.utils.error_handlers import handle_exception

        exception = Exception("General error")

        with app.app_context():
            response, status_code = handle_exception(exception, "")

        data = json.loads(response.data)
        assert data["error"] == "General error"  # No context prefix

    def test_handle_exception_logs_error(self, app):
        """Test handle_exception logs the error"""
        from core.utils.error_handlers import handle_exception

        with patch('core.utils.error_handlers.logger') as mock_logger:
            exception = ValueError("Test error")
            context = "Test context"

            with app.app_context():
                handle_exception(exception, context)

            # Verify logger.error was called with exc_info=True
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Test context: Test error" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    def test_handle_exception_various_exception_types(self, app):
        """Test handle_exception with different exception types"""
        from core.utils.error_handlers import handle_exception

        exceptions = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
        ]

        for exc in exceptions:
            with app.app_context():
                response, status_code = handle_exception(exc, "Test")

            assert status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False
            assert "Test:" in data["error"]

    def test_handle_exception_timestamp_format(self, app):
        """Test handle_exception timestamp is ISO format"""
        from core.utils.error_handlers import handle_exception

        exception = Exception("Test")
        with app.app_context():
            response, _ = handle_exception(exception)

        data = json.loads(response.data)

        # Verify timestamp is ISO 8601 format
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise

    def test_handle_exception_response_is_jsonify(self, app):
        """Test handle_exception returns Flask jsonify response"""
        from core.utils.error_handlers import handle_exception
        from flask import Response

        exception = Exception("Test")
        with app.app_context():
            response, _ = handle_exception(exception)

        # Verify response is Flask Response object
        assert isinstance(response, Response)
        assert response.content_type == "application/json"

    def test_handle_exception_with_unicode_message(self, app):
        """Test handle_exception handles Unicode characters"""
        from core.utils.error_handlers import handle_exception

        exception = Exception("에러 메시지 한글")
        context = "데이터베이스 작업"

        with app.app_context():
            response, status_code = handle_exception(exception, context)

        assert status_code == 500
        data = json.loads(response.data)
        assert "데이터베이스 작업" in data["error"]
        assert "에러 메시지 한글" in data["error"]

    def test_handle_exception_with_long_error_message(self, app):
        """Test handle_exception handles long error messages"""
        from core.utils.error_handlers import handle_exception

        long_message = "Error: " + "x" * 1000
        exception = Exception(long_message)

        with app.app_context():
            response, status_code = handle_exception(exception, "Context")

        assert status_code == 500
        data = json.loads(response.data)
        assert long_message in data["error"]

    def test_handle_exception_with_special_characters(self, app):
        """Test handle_exception handles special characters"""
        from core.utils.error_handlers import handle_exception

        exception = Exception("Error with quotes: ' \" and backslash: \\")
        context = "Context with special chars: <>{}[]"

        with app.app_context():
            response, status_code = handle_exception(exception, context)

        assert status_code == 500
        data = json.loads(response.data)
        assert "Context with special chars" in data["error"]


@pytest.mark.unit
class TestHandleExceptionEdgeCases:
    """Test edge cases for error handlers"""

    def test_handle_exception_with_none_context(self, app):
        """Test handle_exception with None context defaults to empty"""
        from core.utils.error_handlers import handle_exception

        exception = Exception("Test error")

        # None context should be treated as empty/falsy
        with app.app_context():
            response, status_code = handle_exception(exception, context=None)

        data = json.loads(response.data)
        # With None context, should show error without prefix
        assert data["error"] == "Test error"

    def test_handle_exception_with_exception_subclass(self, app):
        """Test handle_exception with custom exception subclass"""
        from core.utils.error_handlers import handle_exception

        class CustomError(Exception):
            pass

        exception = CustomError("Custom error message")
        with app.app_context():
            response, status_code = handle_exception(exception, "Custom context")

        assert status_code == 500
        data = json.loads(response.data)
        assert "Custom context: Custom error message" in data["error"]

    def test_handle_exception_preserves_exception_args(self, app):
        """Test handle_exception preserves exception message"""
        from core.utils.error_handlers import handle_exception

        # Exception with multiple args
        exception = ValueError("Arg1", "Arg2", "Arg3")

        with app.app_context():
            response, status_code = handle_exception(exception)

        data = json.loads(response.data)
        # str(exception) will show all args as tuple
        assert "Arg1" in data["error"] or "('Arg1'" in data["error"]

    def test_handle_exception_response_json_valid(self, app):
        """Test handle_exception always returns valid JSON"""
        from core.utils.error_handlers import handle_exception

        # Various exception types that might have complex string representations
        exceptions = [
            Exception(),  # Empty exception
            Exception(""),  # Empty message
            Exception(None),  # None message
            Exception(123),  # Numeric message
        ]

        for exc in exceptions:
            with app.app_context():
                response, status_code = handle_exception(exc)

            # Should always be valid JSON
            data = json.loads(response.data)
            assert "success" in data
            assert "error" in data
            assert "timestamp" in data
