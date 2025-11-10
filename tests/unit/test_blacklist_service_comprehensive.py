"""
Comprehensive unit tests for BlacklistService
Covers Redis caching, logging, metrics, and all public methods
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
import json


class TestBlacklistServiceInit:
    """Test BlacklistService initialization"""

    def test_init_creates_redis_client(self):
        """Test that Redis client is created on initialization"""
        with patch('redis.Redis') as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True

            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()

            assert service.redis_client is not None
            assert service._components["redis"] is True

    def test_init_handles_redis_failure_gracefully(self):
        """Test that service continues without Redis if unavailable"""
        with patch('redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")

            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()

            assert service.redis_client is None
            assert service._components["redis"] is False


class TestBlacklistServiceWhitelist:
    """Test whitelist functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance with mocked Redis"""
        with patch('redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_is_whitelisted_cache_hit_true(self, service):
        """Test whitelist check with Redis cache hit (IP is whitelisted)"""
        service.redis_client.get.return_value = "true"

        result = service.is_whitelisted("192.168.1.100")

        assert result is True
        service.redis_client.get.assert_called_once_with("whitelist:192.168.1.100")

    def test_is_whitelisted_cache_hit_false(self, service):
        """Test whitelist check with Redis cache hit (IP not whitelisted)"""
        service.redis_client.get.return_value = "false"

        result = service.is_whitelisted("1.2.3.4")

        assert result is False

    def test_is_whitelisted_cache_miss_db_hit(self, service, mock_db_connection):
        """Test whitelist check with cache miss but DB hit"""
        service.redis_client.get.return_value = None
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = {"count": 1}

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.is_whitelisted("192.168.1.100")

        assert result is True
        service.redis_client.setex.assert_called_once_with(
            "whitelist:192.168.1.100", 300, "true"
        )

    def test_is_whitelisted_cache_miss_db_miss(self, service, mock_db_connection):
        """Test whitelist check with both cache and DB miss"""
        service.redis_client.get.return_value = None
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = {"count": 0}

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.is_whitelisted("1.2.3.4")

        assert result is False
        service.redis_client.setex.assert_called_once_with(
            "whitelist:1.2.3.4", 300, "false"
        )

    def test_is_whitelisted_handles_redis_read_error(self, service, mock_db_connection):
        """Test whitelist check handles Redis read errors gracefully"""
        service.redis_client.get.side_effect = Exception("Redis read failed")
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = {"count": 1}

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.is_whitelisted("192.168.1.100")

        # Should fall back to DB and still work
        assert result is True


class TestBlacklistServiceCheckBlacklist:
    """Test check_blacklist functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance with mocked Redis"""
        with patch('redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_check_blacklist_whitelist_priority(self, service):
        """Test that whitelist check has priority over blacklist"""
        with patch.object(service, 'is_whitelisted', return_value=True):
            result = service.check_blacklist("192.168.1.100")

        assert result["blocked"] is False
        assert result["reason"] == "whitelist"
        assert result["metadata"]["source"] == "whitelist"

    def test_check_blacklist_cache_hit(self, service):
        """Test blacklist check with Redis cache hit"""
        cached_result = {
            "blocked": True,
            "reason": "blacklisted",
            "metadata": {"country": "CN", "cache_hit": False}
        }
        service.redis_client.get.return_value = json.dumps(cached_result)

        with patch.object(service, 'is_whitelisted', return_value=False):
            result = service.check_blacklist("1.2.3.4")

        assert result["blocked"] is True
        assert result["metadata"]["cache_hit"] is True

    def test_check_blacklist_db_hit(self, service, mock_db_connection):
        """Test blacklist check with DB hit"""
        service.redis_client.get.return_value = None
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = {
            "count": 1,
            "country": "CN",
            "reason": "Malicious activity"
        }

        with patch.object(service, 'is_whitelisted', return_value=False):
            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.check_blacklist("1.2.3.4")

        assert result["blocked"] is True
        assert result["reason"] == "blacklisted"

    def test_check_blacklist_not_found(self, service, mock_db_connection):
        """Test blacklist check when IP not found"""
        service.redis_client.get.return_value = None
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = {"count": 0}

        with patch.object(service, 'is_whitelisted', return_value=False):
            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.check_blacklist("8.8.8.8")

        assert result["blocked"] is False
        assert result["reason"] == "not_found"


class TestBlacklistServiceLogging:
    """Test logging and metrics functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        with patch('redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_log_decision_creates_structured_log(self, service):
        """Test that log_decision creates structured log entry"""
        with patch('core.services.blacklist_service.logger') as mock_logger:
            service.log_decision(
                ip="1.2.3.4",
                decision="BLOCKED",
                reason="blacklisted",
                metadata={"country": "CN"}
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "blacklist_decision"
            assert call_args[1]["ip"] == "1.2.3.4"
            assert call_args[1]["decision"] == "BLOCKED"
            assert call_args[1]["country"] == "CN"

    def test_log_decision_increments_prometheus_metric(self, service):
        """Test that log_decision increments Prometheus counter"""
        with patch('core.monitoring.metrics.blacklist_decisions_total') as mock_metric:
            service.log_decision(
                ip="1.2.3.4",
                decision="BLOCKED",
                reason="blacklisted"
            )

            mock_metric.labels.assert_called_once_with(decision="BLOCKED", reason="blacklisted")
            mock_metric.labels.return_value.inc.assert_called_once()


class TestBlacklistServiceHealth:
    """Test health check functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        with patch('redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_get_health_all_components_healthy(self, service, mock_db_connection):
        """Test health check when all components are healthy"""
        mock_conn, mock_cursor = mock_db_connection
        service.redis_client.ping.return_value = True

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            health = service.get_health()

        assert health.status == "healthy"
        assert health.components["database"] is True
        assert health.components["redis"] is True

    def test_get_health_redis_down(self, service, mock_db_connection):
        """Test health check when Redis is down"""
        mock_conn, mock_cursor = mock_db_connection
        service.redis_client.ping.side_effect = Exception("Redis down")

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            health = service.get_health()

        assert health.status == "degraded"
        assert health.components["redis"] is False

    def test_get_health_database_down(self, service):
        """Test health check when database is down"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB down")):
            health = service.get_health()

        assert health.status in ["degraded", "unhealthy"]
        assert health.components["database"] is False


class TestBlacklistServiceCacheTTL:
    """Test cache TTL configuration"""

    def test_cache_ttl_default_300_seconds(self):
        """Test that default cache TTL is 300 seconds (5 minutes)"""
        with patch('redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()

        assert service.cache_ttl == 300

    def test_cache_uses_configured_ttl(self, mock_db_connection):
        """Test that cache setex uses configured TTL"""
        with patch('redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = MagicMock()
            service.cache_ttl = 600  # 10 minutes

        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = {"count": 1}
        service.redis_client.get.return_value = None

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            service.is_whitelisted("192.168.1.100")

        # Verify TTL is used in setex call
        service.redis_client.setex.assert_called_once()
        call_args = service.redis_client.setex.call_args[0]
        assert call_args[1] == 600  # Custom TTL
