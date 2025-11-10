#!/usr/bin/env python3
"""
Prometheus metrics for Blacklist application
포트폴리오용 실제 비즈니스 메트릭 수집
"""
import time
import logging
from functools import wraps
from flask import request, g
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logger = logging.getLogger(__name__)

# ============================================================================
# HTTP Request Metrics
# ============================================================================

http_requests_total = Counter(
    "blacklist_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "blacklist_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_request_size_bytes = Histogram(
    "blacklist_http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "blacklist_http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)

# ============================================================================
# Business Metrics (Blacklist-specific)
# ============================================================================

# Phase 2.2: Blacklist Decision Tracking (Claude-Gemini 합의안)
blacklist_decisions_total = Counter(
    "blacklist_decisions_total",
    "Total blacklist decisions with reason tracking",
    ["decision", "reason"],  # decision: ALLOWED/BLOCKED, reason: whitelist/blacklist/etc
)

blacklist_whitelist_hits_total = Counter(
    "blacklist_whitelist_hits_total",
    "Total whitelist hits (VIP protection tracking)",
    ["ip_type"],  # ip_type: vip/partner/internal
)

blacklist_queries_total = Counter(
    "blacklist_queries_total",
    "Total blacklist queries",
    ["query_type", "result"],  # query_type: check/search, result: hit/miss
)

blacklist_entries_total = Gauge(
    "blacklist_entries_total",
    "Current number of entries in blacklist",
    ["category"],  # category: domain/ip/email/etc
)

blacklist_db_operations_total = Counter(
    "blacklist_db_operations_total",
    "Total database operations",
    ["operation", "status"],  # operation: insert/update/delete, status: success/error
)

blacklist_db_operation_duration_seconds = Histogram(
    "blacklist_db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["operation"],
)

# ============================================================================
# Application Health Metrics
# ============================================================================

blacklist_app_info = Gauge(
    "blacklist_app_info",
    "Application information",
    ["version", "mode"],
)

blacklist_errors_total = Counter(
    "blacklist_errors_total",
    "Total application errors",
    ["error_type", "endpoint"],
)


# ============================================================================
# Flask Middleware for automatic metrics collection
# ============================================================================


def setup_metrics(app):
    """
    Flask 애플리케이션에 Prometheus 메트릭 수집 설정
    """

    # Set application info
    blacklist_app_info.labels(version="1.0.0", mode="full").set(1)

    @app.before_request
    def before_request():
        """요청 시작 시간 기록"""
        g.start_time = time.time()

        # Record request size
        if request.content_length:
            endpoint = request.endpoint or "unknown"
            http_request_size_bytes.labels(
                method=request.method, endpoint=endpoint
            ).observe(request.content_length)

    @app.after_request
    def after_request(response):
        """요청 완료 후 메트릭 기록"""
        # Calculate request duration
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            endpoint = request.endpoint or "unknown"

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            # Record response size
            if response.content_length:
                http_response_size_bytes.labels(
                    method=request.method, endpoint=endpoint
                ).observe(response.content_length)

        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        """404 에러 조용히 처리 (메트릭만 기록)"""
        endpoint = request.endpoint or "unknown"
        blacklist_errors_total.labels(
            error_type="NotFound", endpoint=endpoint
        ).inc()
        # 404는 조용히 반환 (500으로 변환하지 않음)
        from flask import jsonify
        return jsonify({
            "error": "Not Found",
            "message": "The requested URL was not found",
            "path": request.path
        }), 404

    @app.errorhandler(Exception)
    def handle_exception(error):
        """에러 발생 시 메트릭 기록"""
        endpoint = request.endpoint or "unknown"
        error_type = type(error).__name__

        blacklist_errors_total.labels(
            error_type=error_type, endpoint=endpoint
        ).inc()

        # Let Flask handle the error normally
        raise error

    logger.info("✅ Prometheus metrics middleware configured")


# ============================================================================
# Metrics Endpoint Handler
# ============================================================================


def metrics_view():
    """
    Prometheus /metrics 엔드포인트
    """
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ============================================================================
# Decorators for business logic instrumentation
# ============================================================================


def track_blacklist_query(query_type):
    """
    Blacklist 쿼리 추적 데코레이터

    Usage:
        @track_blacklist_query("check")
        def check_blacklist(item):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # Determine if query was a hit or miss
                query_result = "hit" if result else "miss"

                blacklist_queries_total.labels(
                    query_type=query_type, result=query_result
                ).inc()

                return result
            except Exception as e:
                blacklist_queries_total.labels(
                    query_type=query_type, result="error"
                ).inc()
                raise e

        return wrapper

    return decorator


def track_db_operation(operation):
    """
    데이터베이스 작업 추적 데코레이터

    Usage:
        @track_db_operation("insert")
        def insert_entry(data):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                blacklist_db_operations_total.labels(
                    operation=operation, status="success"
                ).inc()

                duration = time.time() - start_time
                blacklist_db_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)

                return result
            except Exception as e:
                blacklist_db_operations_total.labels(
                    operation=operation, status="error"
                ).inc()

                duration = time.time() - start_time
                blacklist_db_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)

                raise e

        return wrapper

    return decorator


# ============================================================================
# Utility functions
# ============================================================================


def update_entries_count(category, count):
    """
    블랙리스트 엔트리 수 업데이트

    Usage:
        update_entries_count("domain", 1500)
        update_entries_count("ip", 850)
    """
    blacklist_entries_total.labels(category=category).set(count)


logger.info("✅ Prometheus metrics module loaded")
