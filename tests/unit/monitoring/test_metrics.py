"""
Unit tests for Prometheus metrics module
Tests metrics.py with mocked Flask app and Prometheus metrics
Target: 40% → 80%+ coverage (87 statements)
"""
import pytest
import time
from unittest.mock import MagicMock, patch, call
from flask import Flask, g


@pytest.mark.unit
class TestPrometheusMetricsDefinitions:
    """Test Prometheus metrics are properly defined"""

    def test_http_request_metrics_exist(self):
        """Test HTTP request metrics are defined"""
        from core.monitoring.metrics import (
            http_requests_total,
            http_request_duration_seconds,
            http_request_size_bytes,
            http_response_size_bytes,
        )

        # Verify Counter metrics have labels() method
        assert hasattr(http_requests_total, 'labels')
        assert hasattr(http_request_duration_seconds, 'labels')
        assert hasattr(http_request_size_bytes, 'labels')
        assert hasattr(http_response_size_bytes, 'labels')

    def test_business_metrics_exist(self):
        """Test blacklist business metrics are defined"""
        from core.monitoring.metrics import (
            blacklist_decisions_total,
            blacklist_whitelist_hits_total,
            blacklist_queries_total,
            blacklist_entries_total,
            blacklist_db_operations_total,
            blacklist_db_operation_duration_seconds,
        )

        # Verify all metrics exist
        assert hasattr(blacklist_decisions_total, 'labels')
        assert hasattr(blacklist_whitelist_hits_total, 'labels')
        assert hasattr(blacklist_queries_total, 'labels')
        assert hasattr(blacklist_entries_total, 'labels')
        assert hasattr(blacklist_db_operations_total, 'labels')
        assert hasattr(blacklist_db_operation_duration_seconds, 'labels')

    def test_application_health_metrics_exist(self):
        """Test application health metrics are defined"""
        from core.monitoring.metrics import (
            blacklist_app_info,
            blacklist_errors_total,
        )

        # Verify Gauge and Counter metrics
        assert hasattr(blacklist_app_info, 'labels')
        assert hasattr(blacklist_errors_total, 'labels')


@pytest.mark.unit
class TestSetupMetrics:
    """Test setup_metrics() Flask middleware configuration"""

    def test_setup_metrics_registers_hooks(self, app):
        """Test setup_metrics registers before/after request hooks"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info') as mock_app_info:
            setup_metrics(app)

            # Verify app_info metric set
            mock_app_info.labels.assert_called_once_with(version="1.0.0", mode="full")
            mock_app_info.labels.return_value.set.assert_called_once_with(1)

    def test_before_request_sets_start_time(self, app):
        """Test before_request hook sets g.start_time"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            setup_metrics(app)

        with app.test_request_context('/test', method='GET'):
            # Trigger before_request
            app.preprocess_request()

            # Verify g.start_time is set
            assert hasattr(g, 'start_time')
            assert isinstance(g.start_time, float)
            assert g.start_time <= time.time()

    def test_before_request_records_request_size(self, app):
        """Test before_request records request size if content_length exists"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.http_request_size_bytes') as mock_histogram:
                setup_metrics(app)

                with app.test_request_context(
                    '/test',
                    method='POST',
                    data=b'test data',
                    content_type='application/json'
                ):
                    # Trigger before_request
                    app.preprocess_request()

                    # Verify request size observed
                    mock_histogram.labels.assert_called_once()
                    mock_histogram.labels.return_value.observe.assert_called_once()

    def test_after_request_records_metrics(self, app):
        """Test after_request records HTTP metrics"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.http_requests_total') as mock_counter:
                with patch('core.monitoring.metrics.http_request_duration_seconds') as mock_histogram:
                    with patch('core.monitoring.metrics.http_requests_inprogress'):
                        setup_metrics(app)

                        with app.test_request_context('/test', method='GET'):
                            g.start_time = time.time() - 0.5  # 500ms ago

                            # Create response
                            response = MagicMock()
                            response.status_code = 200
                            response.content_length = None

                            # Trigger after_request
                            app.process_response(response)

                            # Verify metrics recorded
                            mock_counter.labels.assert_called_once()
                            mock_counter.labels.return_value.inc.assert_called_once()
                            mock_histogram.labels.assert_called_once()
                            mock_histogram.labels.return_value.observe.assert_called_once()

    def test_after_request_records_response_size(self, app):
        """Test after_request records response size if content_length exists"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.http_requests_total'):
                with patch('core.monitoring.metrics.http_request_duration_seconds'):
                    with patch('core.monitoring.metrics.http_response_size_bytes') as mock_histogram:
                        setup_metrics(app)

                        with app.test_request_context('/test', method='GET'):
                            g.start_time = time.time()

                            # Create response with content_length
                            response = MagicMock()
                            response.status_code = 200
                            response.content_length = 1024  # 1KB response

                            # Trigger after_request
                            app.process_response(response)

                            # Verify response size observed
                            mock_histogram.labels.assert_called_once()
                            mock_histogram.labels.return_value.observe.assert_called_with(1024)

    def test_error_handler_404(self, app):
        """Test 404 error handler increments error metric"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.blacklist_errors_total') as mock_errors:
                setup_metrics(app)

                with app.test_request_context('/nonexistent', method='GET'):
                    # Trigger 404 handler
                    error_handlers = app.error_handler_spec[None][404]
                    assert len(error_handlers) > 0

                    # Call 404 handler
                    handler = error_handlers[0]
                    response, status_code = handler(None)

                    # Verify error metric incremented
                    mock_errors.labels.assert_called_with(
                        error_type="NotFound",
                        endpoint="unknown"
                    )
                    mock_errors.labels.return_value.inc.assert_called_once()

                    # Verify response
                    assert status_code == 404
                    assert "error" in response.json

    def test_error_handler_exception(self, app):
        """Test general exception handler increments error metric"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.blacklist_errors_total') as mock_errors:
                setup_metrics(app)

                with app.test_request_context('/test', method='GET'):
                    # Get exception handler
                    error_handlers = app.error_handler_spec[None][Exception]
                    assert len(error_handlers) > 0

                    handler = error_handlers[0]

                    # Trigger exception handler
                    test_exception = ValueError("Test error")
                    with pytest.raises(ValueError):
                        handler(test_exception)

                    # Verify error metric incremented
                    mock_errors.labels.assert_called_with(
                        error_type="ValueError",
                        endpoint="unknown"
                    )
                    mock_errors.labels.return_value.inc.assert_called_once()


@pytest.mark.unit
class TestMetricsView:
    """Test metrics_view() endpoint"""

    def test_metrics_view_returns_prometheus_format(self):
        """Test metrics_view returns Prometheus metrics"""
        from core.monitoring.metrics import metrics_view

        with patch('core.monitoring.metrics.generate_latest') as mock_generate:
            with patch('core.monitoring.metrics.CONTENT_TYPE_LATEST', 'text/plain; version=0.0.4'):
                mock_generate.return_value = b"# HELP metric_name\nmetric_name 1.0\n"

                response, status_code, headers = metrics_view()

                # Verify response
                assert status_code == 200
                assert headers["Content-Type"] == 'text/plain; version=0.0.4'
                mock_generate.assert_called_once()

    def test_metrics_view_content_type(self):
        """Test metrics_view uses correct Prometheus content type"""
        from core.monitoring.metrics import metrics_view

        with patch('core.monitoring.metrics.generate_latest', return_value=b"metrics"):
            response, status_code, headers = metrics_view()

            # Verify Content-Type header
            assert "Content-Type" in headers
            assert status_code == 200


@pytest.mark.unit
class TestTrackBlacklistQueryDecorator:
    """Test track_blacklist_query decorator"""

    def test_decorator_tracks_hit_result(self):
        """Test decorator tracks 'hit' when function returns truthy"""
        from core.monitoring.metrics import track_blacklist_query

        with patch('core.monitoring.metrics.blacklist_queries_total') as mock_counter:
            @track_blacklist_query("check")
            def check_function():
                return {"blocked": True}

            result = check_function()

            # Verify metric incremented for 'hit'
            mock_counter.labels.assert_called_once_with(
                query_type="check",
                result="hit"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
            assert result == {"blocked": True}

    def test_decorator_tracks_miss_result(self):
        """Test decorator tracks 'miss' when function returns falsy"""
        from core.monitoring.metrics import track_blacklist_query

        with patch('core.monitoring.metrics.blacklist_queries_total') as mock_counter:
            @track_blacklist_query("search")
            def search_function():
                return None

            result = search_function()

            # Verify metric incremented for 'miss'
            mock_counter.labels.assert_called_once_with(
                query_type="search",
                result="miss"
            )
            mock_counter.labels.return_value.inc.assert_called_once()
            assert result is None

    def test_decorator_tracks_error_result(self):
        """Test decorator tracks 'error' when function raises exception"""
        from core.monitoring.metrics import track_blacklist_query

        with patch('core.monitoring.metrics.blacklist_queries_total') as mock_counter:
            @track_blacklist_query("check")
            def failing_function():
                raise ValueError("Database error")

            # Should re-raise exception
            with pytest.raises(ValueError):
                failing_function()

            # Verify metric incremented for 'error'
            mock_counter.labels.assert_called_once_with(
                query_type="check",
                result="error"
            )
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata"""
        from core.monitoring.metrics import track_blacklist_query

        with patch('core.monitoring.metrics.blacklist_queries_total'):
            @track_blacklist_query("test")
            def original_function():
                """Original docstring"""
                pass

            # Verify function metadata preserved
            assert original_function.__name__ == "original_function"
            assert original_function.__doc__ == "Original docstring"


@pytest.mark.unit
class TestTrackDbOperationDecorator:
    """Test track_db_operation decorator"""

    def test_decorator_tracks_successful_operation(self):
        """Test decorator tracks successful DB operation"""
        from core.monitoring.metrics import track_db_operation

        with patch('core.monitoring.metrics.blacklist_db_operations_total') as mock_counter:
            with patch('core.monitoring.metrics.blacklist_db_operation_duration_seconds') as mock_histogram:
                @track_db_operation("insert")
                def insert_function():
                    return {"id": 123}

                result = insert_function()

                # Verify success metric incremented
                mock_counter.labels.assert_called_once_with(
                    operation="insert",
                    status="success"
                )
                mock_counter.labels.return_value.inc.assert_called_once()

                # Verify duration observed
                mock_histogram.labels.assert_called_once_with(operation="insert")
                mock_histogram.labels.return_value.observe.assert_called_once()

                assert result == {"id": 123}

    def test_decorator_tracks_failed_operation(self):
        """Test decorator tracks failed DB operation"""
        from core.monitoring.metrics import track_db_operation

        with patch('core.monitoring.metrics.blacklist_db_operations_total') as mock_counter:
            with patch('core.monitoring.metrics.blacklist_db_operation_duration_seconds') as mock_histogram:
                @track_db_operation("update")
                def failing_function():
                    raise ConnectionError("Database unavailable")

                # Should re-raise exception
                with pytest.raises(ConnectionError):
                    failing_function()

                # Verify error metric incremented
                mock_counter.labels.assert_called_once_with(
                    operation="update",
                    status="error"
                )
                mock_counter.labels.return_value.inc.assert_called_once()

                # Verify duration still observed (even on error)
                mock_histogram.labels.assert_called_once_with(operation="update")
                mock_histogram.labels.return_value.observe.assert_called_once()

    def test_decorator_records_operation_duration(self):
        """Test decorator records accurate operation duration"""
        from core.monitoring.metrics import track_db_operation

        with patch('core.monitoring.metrics.blacklist_db_operations_total'):
            with patch('core.monitoring.metrics.blacklist_db_operation_duration_seconds') as mock_histogram:
                @track_db_operation("delete")
                def slow_function():
                    time.sleep(0.1)  # 100ms operation
                    return True

                slow_function()

                # Verify duration observed (should be >= 0.1s)
                mock_histogram.labels.return_value.observe.assert_called_once()
                observed_duration = mock_histogram.labels.return_value.observe.call_args[0][0]
                assert observed_duration >= 0.1

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata"""
        from core.monitoring.metrics import track_db_operation

        with patch('core.monitoring.metrics.blacklist_db_operations_total'):
            with patch('core.monitoring.metrics.blacklist_db_operation_duration_seconds'):
                @track_db_operation("select")
                def original_function():
                    """Query database"""
                    pass

                # Verify function metadata preserved
                assert original_function.__name__ == "original_function"
                assert original_function.__doc__ == "Query database"


@pytest.mark.unit
class TestUpdateEntriesCount:
    """Test update_entries_count utility function"""

    def test_update_entries_count_sets_gauge(self):
        """Test update_entries_count sets Gauge metric"""
        from core.monitoring.metrics import update_entries_count

        with patch('core.monitoring.metrics.blacklist_entries_total') as mock_gauge:
            update_entries_count("ip", 1500)

            # Verify Gauge metric set
            mock_gauge.labels.assert_called_once_with(category="ip")
            mock_gauge.labels.return_value.set.assert_called_once_with(1500)

    def test_update_entries_count_multiple_categories(self):
        """Test update_entries_count works for different categories"""
        from core.monitoring.metrics import update_entries_count

        with patch('core.monitoring.metrics.blacklist_entries_total') as mock_gauge:
            update_entries_count("domain", 850)
            update_entries_count("email", 320)

            # Verify multiple calls with different categories
            assert mock_gauge.labels.call_count == 2
            mock_gauge.labels.assert_any_call(category="domain")
            mock_gauge.labels.assert_any_call(category="email")

    def test_update_entries_count_zero_value(self):
        """Test update_entries_count handles zero count"""
        from core.monitoring.metrics import update_entries_count

        with patch('core.monitoring.metrics.blacklist_entries_total') as mock_gauge:
            update_entries_count("ip", 0)

            # Verify zero value accepted
            mock_gauge.labels.return_value.set.assert_called_once_with(0)


@pytest.mark.unit
class TestMetricsEdgeCases:
    """Test edge cases for metrics module"""

    def test_after_request_without_start_time(self, app):
        """Test after_request handles missing g.start_time gracefully"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.http_requests_total') as mock_counter:
                setup_metrics(app)

                with app.test_request_context('/test', method='GET'):
                    # Don't set g.start_time (simulate before_request not called)

                    response = MagicMock()
                    response.status_code = 200

                    # Should not raise exception
                    result = app.process_response(response)

                    # Metrics should not be recorded without start_time
                    mock_counter.labels.assert_not_called()

    def test_before_request_without_content_length(self, app):
        """Test before_request handles missing content_length"""
        from core.monitoring.metrics import setup_metrics

        with patch('core.monitoring.metrics.blacklist_app_info'):
            with patch('core.monitoring.metrics.http_request_size_bytes') as mock_histogram:
                setup_metrics(app)

                with app.test_request_context('/test', method='GET'):
                    # No content_length (GET request typically has none)
                    app.preprocess_request()

                    # Should not observe request size
                    mock_histogram.labels.assert_not_called()

    def test_decorator_with_different_query_types(self):
        """Test track_blacklist_query with various query types"""
        from core.monitoring.metrics import track_blacklist_query

        query_types = ["check", "search", "lookup", "verify"]

        with patch('core.monitoring.metrics.blacklist_queries_total') as mock_counter:
            for query_type in query_types:
                @track_blacklist_query(query_type)
                def test_function():
                    return True

                test_function()

            # Verify all query types tracked
            assert mock_counter.labels.call_count == len(query_types)

    def test_decorator_with_different_db_operations(self):
        """Test track_db_operation with various operations"""
        from core.monitoring.metrics import track_db_operation

        operations = ["insert", "update", "delete", "select"]

        with patch('core.monitoring.metrics.blacklist_db_operations_total') as mock_counter:
            with patch('core.monitoring.metrics.blacklist_db_operation_duration_seconds'):
                for operation in operations:
                    @track_db_operation(operation)
                    def test_function():
                        return True

                    test_function()

                # Verify all operations tracked
                assert mock_counter.labels.call_count == len(operations)
