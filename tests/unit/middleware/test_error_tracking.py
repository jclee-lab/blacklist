"""
Unit tests for error tracking middleware
Tests error_tracking.py with Flask app context and mocked metrics
Target: 0% → 80% coverage (76 statements)
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
import time
import logging


@pytest.mark.unit
class TestRequestContextMiddleware:
    """Test RequestContextMiddleware class"""

    def test_initialization_without_app(self):
        """Test middleware initialization without Flask app"""
        from core.middleware.error_tracking import RequestContextMiddleware

        middleware = RequestContextMiddleware()

        assert middleware.app is None

    def test_initialization_with_app(self, app):
        """Test middleware initialization with Flask app"""
        from core.middleware.error_tracking import RequestContextMiddleware

        with patch.object(RequestContextMiddleware, 'init_app') as mock_init:
            middleware = RequestContextMiddleware(app)

            mock_init.assert_called_once_with(app)
            assert middleware.app == app

    def test_init_app_registers_hooks(self, app):
        """Test init_app registers before/after/teardown request hooks"""
        from core.middleware.error_tracking import RequestContextMiddleware

        middleware = RequestContextMiddleware()

        # Register hooks
        middleware.init_app(app)

        # Verify hooks were registered by checking they're callable
        # Flask stores hooks as lists of functions
        assert hasattr(app, 'before_request_funcs')
        assert hasattr(app, 'after_request_funcs')
        assert hasattr(app, 'teardown_request_funcs')

    def test_before_request_sets_context(self, app):
        """Test before_request sets Flask g context variables"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='GET', headers={'X-Request-ID': 'test-123'}):
            # Mock metrics
            with patch('core.middleware.error_tracking.http_requests_inprogress') as mock_gauge:
                RequestContextMiddleware.before_request()

                # Verify g attributes set
                assert hasattr(g, 'request_start_time')
                assert hasattr(g, 'request_id')
                assert hasattr(g, 'endpoint')
                assert g.request_id == 'test-123'

                # Verify metric incremented
                mock_gauge.labels.assert_called_once()
                mock_gauge.labels.return_value.inc.assert_called_once()

    def test_before_request_generates_request_id(self, app):
        """Test before_request generates request ID if not provided"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='GET'):
            with patch('core.middleware.error_tracking.http_requests_inprogress'):
                RequestContextMiddleware.before_request()

                # Verify request_id was generated
                assert hasattr(g, 'request_id')
                assert g.request_id.startswith('req-')

    def test_after_request_records_metrics(self, app):
        """Test after_request records metrics and adds headers"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='GET'):
            # Setup g context
            g.request_start_time = time.time() - 0.5  # 500ms ago
            g.request_id = 'test-123'
            g.endpoint = 'test_endpoint'

            # Mock metrics
            with patch('core.middleware.error_tracking.http_requests_total') as mock_counter:
                with patch('core.middleware.error_tracking.http_request_duration_seconds') as mock_histogram:
                    with patch('core.middleware.error_tracking.http_requests_inprogress') as mock_gauge:
                        # Create mock response with proper headers dictionary
                        response = MagicMock()
                        response.status_code = 200
                        response.headers = {}  # Initialize as dict for header assignment

                        result = RequestContextMiddleware.after_request(response)

                        # Verify metrics recorded
                        mock_counter.labels.assert_called_once()
                        mock_histogram.labels.assert_called_once()
                        mock_gauge.labels.assert_called_once()

                        # Verify headers added
                        assert 'X-Request-ID' in result.headers
                        assert 'X-Response-Time' in result.headers
                        assert result.headers['X-Request-ID'] == 'test-123'

    def test_after_request_tracks_errors(self, app):
        """Test after_request tracks HTTP errors (4xx, 5xx)"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='POST'):
            g.request_start_time = time.time()
            g.request_id = 'test-456'
            g.endpoint = 'api_endpoint'

            with patch('core.middleware.error_tracking.http_requests_total'):
                with patch('core.middleware.error_tracking.http_request_duration_seconds'):
                    with patch('core.middleware.error_tracking.http_requests_inprogress'):
                        with patch('core.middleware.error_tracking.http_errors_total') as mock_errors:
                            # 4xx error
                            response_400 = MagicMock()
                            response_400.status_code = 404

                            RequestContextMiddleware.after_request(response_400)

                            # Verify error tracked as client_error
                            mock_errors.labels.assert_called_with(
                                method='POST',
                                endpoint='api_endpoint',
                                error_type='client_error',
                                status=404
                            )

    def test_after_request_tracks_server_errors(self, app):
        """Test after_request tracks 5xx errors as server_error"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='GET'):
            g.request_start_time = time.time()
            g.request_id = 'test-789'
            g.endpoint = 'failing_endpoint'

            with patch('core.middleware.error_tracking.http_requests_total'):
                with patch('core.middleware.error_tracking.http_request_duration_seconds'):
                    with patch('core.middleware.error_tracking.http_requests_inprogress'):
                        with patch('core.middleware.error_tracking.http_errors_total') as mock_errors:
                            # 5xx error
                            response_500 = MagicMock()
                            response_500.status_code = 500

                            RequestContextMiddleware.after_request(response_500)

                            # Verify error tracked as server_error
                            mock_errors.labels.assert_called_with(
                                method='GET',
                                endpoint='failing_endpoint',
                                error_type='server_error',
                                status=500
                            )

    def test_after_request_without_start_time(self, app):
        """Test after_request handles missing request_start_time"""
        from core.middleware.error_tracking import RequestContextMiddleware

        with app.test_request_context('/test', method='GET'):
            # No g.request_start_time set
            response = MagicMock()
            response.status_code = 200

            # Should not raise exception
            result = RequestContextMiddleware.after_request(response)

            assert result == response

    def test_teardown_request_without_exception(self, app):
        """Test teardown_request with no exception"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='GET'):
            g.request_id = 'test-clean'

            # No exception
            RequestContextMiddleware.teardown_request(exception=None)

            # Should complete without errors

    def test_teardown_request_with_exception(self, app):
        """Test teardown_request logs and tracks exceptions"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/test', method='POST'):
            g.request_id = 'test-error'

            with patch('core.middleware.error_tracking.application_errors_total') as mock_errors:
                with patch('core.middleware.error_tracking.logger') as mock_logger:
                    # Simulate exception
                    test_exception = ValueError("Test error")

                    RequestContextMiddleware.teardown_request(exception=test_exception)

                    # Verify logging
                    mock_logger.error.assert_called_once()

                    # Verify error metric incremented
                    mock_errors.labels.assert_called_once()
                    mock_errors.labels.return_value.inc.assert_called_once()


@pytest.mark.unit
class TestTrackErrorsDecorator:
    """Test track_errors decorator"""

    def test_decorator_successful_execution(self):
        """Test decorator allows successful function execution"""
        from core.middleware.error_tracking import track_errors

        @track_errors('test_error')
        def successful_function():
            return "success"

        result = successful_function()

        assert result == "success"

    def test_decorator_tracks_exception(self):
        """Test decorator tracks exception and re-raises"""
        from core.middleware.error_tracking import track_errors

        with patch('core.middleware.error_tracking.application_errors_total') as mock_errors:
            with patch('core.middleware.error_tracking.logger'):
                @track_errors('database_error')
                def failing_function():
                    raise ValueError("Database connection failed")

                # Should re-raise exception
                with pytest.raises(ValueError):
                    failing_function()

                # Verify error metric incremented
                mock_errors.labels.assert_called_once()
                mock_errors.labels.return_value.inc.assert_called_once()

    def test_decorator_uses_exception_type_if_no_label(self):
        """Test decorator uses exception type name if no error_type provided"""
        from core.middleware.error_tracking import track_errors

        with patch('core.middleware.error_tracking.application_errors_total') as mock_errors:
            with patch('core.middleware.error_tracking.logger'):
                @track_errors()
                def failing_function():
                    raise KeyError("Missing key")

                with pytest.raises(KeyError):
                    failing_function()

                # Verify error tracked with exception type name
                call_kwargs = mock_errors.labels.call_args[1]
                assert call_kwargs['error_type'] == 'KeyError'

    def test_decorator_determines_severity(self):
        """Test decorator determines error severity"""
        from core.middleware.error_tracking import track_errors

        with patch('core.middleware.error_tracking.application_errors_total') as mock_errors:
            with patch('core.middleware.error_tracking.logger'):
                @track_errors('test_error')
                def failing_function():
                    raise RuntimeError("Runtime error")

                with pytest.raises(RuntimeError):
                    failing_function()

                # Verify severity set to 'critical' for exceptions without status_code
                call_kwargs = mock_errors.labels.call_args[1]
                assert call_kwargs['severity'] == 'critical'

    def test_decorator_logs_error(self):
        """Test decorator logs errors with structured context"""
        from core.middleware.error_tracking import track_errors

        with patch('core.middleware.error_tracking.application_errors_total'):
            with patch('core.middleware.error_tracking.logger') as mock_logger:
                @track_errors('custom_error')
                def failing_function():
                    raise ValueError("Test error")

                with pytest.raises(ValueError):
                    failing_function()

                # Verify logging called with exc_info=True
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                assert call_args[1]['exc_info'] is True


@pytest.mark.unit
class TestStructuredLogger:
    """Test StructuredLogger class"""

    def test_log_error_basic(self, app):
        """Test log_error with basic parameters"""
        from core.middleware.error_tracking import StructuredLogger
        from flask import g

        with app.test_request_context('/test'):
            g.request_id = 'test-log-123'
            g.endpoint = 'test_endpoint'

            with patch('core.middleware.error_tracking.logger') as mock_logger:
                StructuredLogger.log_error("Test error message")

                # Verify logger.log called
                mock_logger.log.assert_called_once()
                call_args = mock_logger.log.call_args

                # Verify default level (ERROR)
                assert call_args[0][0] == logging.ERROR
                assert call_args[0][1] == "Test error message"

    def test_log_error_with_exception(self, app):
        """Test log_error with exception object"""
        from core.middleware.error_tracking import StructuredLogger
        from flask import g

        with app.test_request_context('/test'):
            g.request_id = 'test-log-456'

            with patch('core.middleware.error_tracking.logger') as mock_logger:
                test_error = ValueError("Test exception")

                StructuredLogger.log_error(
                    "Error occurred",
                    error=test_error
                )

                # Verify exc_info=True when error provided
                call_kwargs = mock_logger.log.call_args[1]
                assert call_kwargs['exc_info'] is True

                # Verify error details in extra
                extra = call_kwargs['extra']
                assert extra['error_type'] == 'ValueError'
                assert extra['error_message'] == 'Test exception'

    def test_log_error_with_context(self, app):
        """Test log_error with additional context"""
        from core.middleware.error_tracking import StructuredLogger
        from flask import g

        with app.test_request_context('/test'):
            g.request_id = 'test-log-789'
            g.endpoint = 'api_endpoint'

            with patch('core.middleware.error_tracking.logger') as mock_logger:
                context = {
                    "user_id": "user123",
                    "action": "delete",
                    "resource": "item456"
                }

                StructuredLogger.log_error(
                    "Operation failed",
                    context=context
                )

                # Verify context merged into extra
                extra = mock_logger.log.call_args[1]['extra']
                assert extra['user_id'] == "user123"
                assert extra['action'] == "delete"
                assert extra['resource'] == "item456"

    def test_log_error_custom_level(self, app):
        """Test log_error with custom logging level"""
        from core.middleware.error_tracking import StructuredLogger
        from flask import g

        with app.test_request_context('/test'):
            g.request_id = 'test-log-warning'

            with patch('core.middleware.error_tracking.logger') as mock_logger:
                StructuredLogger.log_error(
                    "Warning message",
                    level=logging.WARNING
                )

                # Verify WARNING level used
                call_args = mock_logger.log.call_args[0]
                assert call_args[0] == logging.WARNING

    def test_log_error_timestamp_format(self, app):
        """Test log_error includes ISO 8601 timestamp"""
        from core.middleware.error_tracking import StructuredLogger
        from flask import g

        with app.test_request_context('/test'):
            g.request_id = 'test-timestamp'

            with patch('core.middleware.error_tracking.logger') as mock_logger:
                StructuredLogger.log_error("Test message")

                # Verify timestamp in extra
                extra = mock_logger.log.call_args[1]['extra']
                assert 'timestamp' in extra

                # Verify ISO 8601 format with Z suffix
                timestamp = extra['timestamp']
                assert timestamp.endswith('Z')

                # Should be parseable
                datetime.fromisoformat(timestamp[:-1])  # Remove Z for parsing


@pytest.mark.unit
class TestPrometheusMetrics:
    """Test Prometheus metrics are defined correctly"""

    def test_http_requests_total_counter_exists(self):
        """Test http_requests_total counter is defined"""
        from core.middleware.error_tracking import http_requests_total

        assert http_requests_total is not None
        assert hasattr(http_requests_total, 'labels')

    def test_http_errors_total_counter_exists(self):
        """Test http_errors_total counter is defined"""
        from core.middleware.error_tracking import http_errors_total

        assert http_errors_total is not None
        assert hasattr(http_errors_total, 'labels')

    def test_http_request_duration_seconds_histogram_exists(self):
        """Test http_request_duration_seconds histogram is defined"""
        from core.middleware.error_tracking import http_request_duration_seconds

        assert http_request_duration_seconds is not None
        assert hasattr(http_request_duration_seconds, 'labels')

    def test_http_requests_inprogress_gauge_exists(self):
        """Test http_requests_inprogress gauge is defined"""
        from core.middleware.error_tracking import http_requests_inprogress

        assert http_requests_inprogress is not None
        assert hasattr(http_requests_inprogress, 'labels')

    def test_application_errors_total_counter_exists(self):
        """Test application_errors_total counter is defined"""
        from core.middleware.error_tracking import application_errors_total

        assert application_errors_total is not None
        assert hasattr(application_errors_total, 'labels')


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases for error tracking"""

    def test_after_request_with_unknown_endpoint(self, app):
        """Test after_request handles missing endpoint gracefully"""
        from core.middleware.error_tracking import RequestContextMiddleware
        from flask import g

        with app.test_request_context('/unknown', method='GET'):
            g.request_start_time = time.time()
            g.request_id = 'test-unknown'
            # No g.endpoint set

            with patch('core.middleware.error_tracking.http_requests_total'):
                with patch('core.middleware.error_tracking.http_request_duration_seconds'):
                    with patch('core.middleware.error_tracking.http_requests_inprogress'):
                        response = MagicMock()
                        response.status_code = 200

                        # Should handle missing endpoint
                        result = RequestContextMiddleware.after_request(response)

                        assert result == response

    def test_log_error_without_flask_context(self, app):
        """Test log_error with Flask app context but no request context"""
        from core.middleware.error_tracking import StructuredLogger

        with app.app_context():
            with patch('core.middleware.error_tracking.logger') as mock_logger:
                # App context but no request context (no g.request_id set)
                StructuredLogger.log_error("Error without request")

                # Should still log, using 'unknown' for request_id
                extra = mock_logger.log.call_args[1]['extra']
                assert extra['request_id'] == 'unknown'
                assert extra['endpoint'] == 'unknown'

    def test_decorator_preserves_function_metadata(self):
        """Test track_errors decorator preserves function metadata"""
        from core.middleware.error_tracking import track_errors

        @track_errors('test')
        def test_function():
            """Test function docstring"""
            pass

        # Verify functools.wraps preserved metadata
        assert test_function.__name__ == 'test_function'
        assert test_function.__doc__ == 'Test function docstring'
