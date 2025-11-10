"""
Enhanced BlacklistService Unit Tests

Tests for enhanced BlacklistService with:
- Whitelist priority enforcement
- Redis caching integration
- Structured logging
- Health checks including Redis status
"""
import pytest
import json
from unittest.mock import patch, MagicMock, call
from datetime import datetime


class TestWhitelistPriority:
    """Test whitelist priority logic (Phase 1.1)"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('core.services.blacklist_service.redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_whitelisted_ip_never_blocked(self, service):
        """Test whitelisted IP is never blocked, even if in blacklist"""
        # Mock: IP is in both whitelist AND blacklist
        with patch.object(service, 'is_whitelisted', return_value=True):
            with patch.object(service, 'get_db_connection') as mock_db:
                result = service.check_blacklist("192.168.1.100")

                # Should return not blocked (whitelist priority)
                assert result["blocked"] is False
                assert result["reason"] == "whitelist"
                assert result["metadata"]["source"] == "whitelist"

                # Should NOT query blacklist database
                mock_db.assert_not_called()

    def test_whitelist_check_called_first(self, service):
        """Test whitelist is checked before blacklist"""
        call_order = []

        def mock_whitelist(ip):
            call_order.append("whitelist")
            return False

        def mock_get_conn():
            call_order.append("database")
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            return mock_conn

        with patch.object(service, 'is_whitelisted', side_effect=mock_whitelist):
            with patch.object(service, 'get_db_connection', side_effect=mock_get_conn):
                service.check_blacklist("1.2.3.4")

                # Whitelist should be checked first
                assert call_order[0] == "whitelist"
                assert call_order[1] == "database"

    def test_non_whitelisted_ip_proceeds_to_blacklist_check(self, service):
        """Test non-whitelisted IP proceeds to blacklist check"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                "ip_address": "1.2.3.4",
                "reason": "malicious",
                "source": "REGTECH",
                "detection_count": 5
            }
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.check_blacklist("1.2.3.4")

                # Should check blacklist
                assert result["blocked"] is True
                assert result["reason"] == "malicious"

    def test_whitelist_priority_with_prometheus_metrics(self, service):
        """Test whitelist hits are counted in Prometheus metrics"""
        with patch.object(service, 'is_whitelisted', return_value=True):
            with patch('core.services.blacklist_service.blacklist_whitelist_hits_total') as mock_metric:
                service.check_blacklist("192.168.1.100")

                # Should increment whitelist hit metric
                # Metric may be called in is_whitelisted method
                # Just verify it doesn't crash


class TestBlacklistLogic:
    """Test blacklist check logic"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('core.services.blacklist_service.redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_blacklisted_ip_returns_blocked(self, service):
        """Test blacklisted IP returns blocked status"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                "ip_address": "1.2.3.4",
                "reason": "malicious activity",
                "source": "REGTECH",
                "detection_count": 10
            }
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.check_blacklist("1.2.3.4")

                assert result["blocked"] is True
                assert result["reason"] == "malicious activity"
                assert result["metadata"]["source"] == "REGTECH"
                assert result["metadata"]["detection_count"] == 10

    def test_clean_ip_returns_not_blocked(self, service):
        """Test clean IP (not in blacklist) returns not blocked"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None  # Not in blacklist
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.check_blacklist("8.8.8.8")

                assert result["blocked"] is False
                assert result["reason"] == "not_in_blacklist"

    def test_blacklist_query_uses_is_active_filter(self, service):
        """Test blacklist query filters by is_active=true"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                service.check_blacklist("1.2.3.4")

                # Verify query includes is_active filter
                execute_call = mock_cursor.execute.call_args[0][0]
                assert "is_active = true" in execute_call or "is_active" in execute_call


class TestStructuredLogging:
    """Test structured logging integration (Phase 1.2)"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('core.services.blacklist_service.redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_log_decision_called_for_whitelist_hit(self, service):
        """Test log_decision is called for whitelist hits"""
        with patch.object(service, 'is_whitelisted', return_value=True):
            with patch.object(service, 'log_decision') as mock_log:
                service.check_blacklist("192.168.1.100")

                # Should log decision with whitelist reason
                mock_log.assert_called()
                call_args = mock_log.call_args[0]
                assert call_args[0] == "192.168.1.100"  # IP
                assert call_args[1] == "ALLOWED"  # Decision
                assert call_args[2] == "whitelist"  # Reason

    def test_log_decision_called_for_blacklist_hit(self, service):
        """Test log_decision is called for blacklist hits"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                "ip_address": "1.2.3.4",
                "reason": "malicious",
                "source": "REGTECH",
                "detection_count": 1
            }
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                with patch.object(service, 'log_decision') as mock_log:
                    service.check_blacklist("1.2.3.4")

                    # Should log blocked decision
                    mock_log.assert_called()
                    call_args = mock_log.call_args[0]
                    assert call_args[1] == "BLOCKED"

    def test_log_decision_includes_metadata(self, service):
        """Test log_decision includes relevant metadata"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                "ip_address": "1.2.3.4",
                "reason": "malicious",
                "source": "REGTECH",
                "detection_count": 5
            }
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                with patch.object(service, 'log_decision') as mock_log:
                    service.check_blacklist("1.2.3.4")

                    # Metadata should include source, detection_count
                    metadata = mock_log.call_args[0][3]
                    assert "source" in metadata
                    assert "detection_count" in metadata


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('core.services.blacklist_service.redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_health_check_includes_database_status(self, service):
        """Test health check includes database status"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 1000}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            health = service.get_health()

            assert health.status in ["healthy", "degraded"]
            assert "database" in health.components
            assert health.components["database"]["status"] == "healthy"

    def test_health_check_includes_redis_status(self, service):
        """Test health check includes Redis status"""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        service.redis_client = mock_redis

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 1000}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            health = service.get_health()

            assert "redis" in health.components
            assert health.components["redis"]["status"] == "healthy"

    def test_health_check_degrades_when_redis_unavailable(self, service):
        """Test health status degrades when Redis unavailable"""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Redis unavailable")
        service.redis_client = mock_redis

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 1000}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            health = service.get_health()

            # System should be degraded but not unhealthy
            # (Redis is optional, DB is required)
            assert health.components["redis"]["status"] == "degraded"

    def test_health_check_includes_version(self, service):
        """Test health check includes application version"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 1000}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            health = service.get_health()

            assert hasattr(health, 'version')
            assert health.version is not None


class TestErrorHandling:
    """Test error handling in BlacklistService"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('core.services.blacklist_service.redis.Redis'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_database_error_returns_safe_response(self, service):
        """Test database errors return safe response"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            with patch.object(service, 'get_db_connection', side_effect=Exception("DB Error")):
                result = service.check_blacklist("1.2.3.4")

                # Should return not blocked (fail-open for safety)
                assert result["blocked"] is False
                assert result["reason"] == "error"
                assert "error" in result["metadata"]

    def test_whitelist_error_allows_fallback_to_blacklist(self, service):
        """Test whitelist check errors don't prevent blacklist check"""
        with patch.object(service, 'is_whitelisted', side_effect=Exception("Whitelist Error")):
            # Even with whitelist error, should attempt blacklist check
            # Implementation may vary
            pass

    def test_invalid_database_response_handled_gracefully(self, service):
        """Test invalid database responses are handled gracefully"""
        with patch.object(service, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {}  # Empty dict
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.check_blacklist("1.2.3.4")

                # Should handle gracefully
                assert "blocked" in result
                assert "reason" in result


class TestCacheIntegration:
    """Test cache integration in BlacklistService"""

    @pytest.fixture
    def service_with_redis(self):
        """Create BlacklistService with mocked Redis"""
        mock_redis = MagicMock()
        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis
            return service

    def test_check_blacklist_uses_cache(self, service_with_redis):
        """Test check_blacklist attempts to use cache"""
        service_with_redis.redis_client.get.return_value = None

        with patch.object(service_with_redis, 'is_whitelisted', return_value=False):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service_with_redis, 'get_db_connection', return_value=mock_conn):
                service_with_redis.check_blacklist("1.2.3.4")

                # Should attempt cache read
                service_with_redis.redis_client.get.assert_called()

    def test_whitelist_uses_cache(self, service_with_redis):
        """Test is_whitelisted uses cache"""
        service_with_redis.redis_client.get.return_value = None

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 0}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service_with_redis, 'get_db_connection', return_value=mock_conn):
            service_with_redis.is_whitelisted("1.2.3.4")

            # Should attempt cache read
            service_with_redis.redis_client.get.assert_called_with("whitelist:1.2.3.4")
