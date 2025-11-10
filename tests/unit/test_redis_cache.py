"""
Redis Cache Tests

Tests Redis caching implementation in BlacklistService:
- Cache hit/miss behavior
- TTL expiration
- Graceful degradation when Redis unavailable
- Cache invalidation
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock, call
import redis


class TestRedisCacheWhitelist:
    """Test Redis caching for whitelist checks"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = MagicMock(spec=redis.Redis)
        return mock_client

    @pytest.fixture
    def blacklist_service_with_redis(self, mock_redis):
        """Create BlacklistService with mocked Redis"""
        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis
            return service

    def test_whitelist_cache_hit_returns_cached_value(self, blacklist_service_with_redis, mock_redis):
        """Test cache hit returns cached value without DB query"""
        # Setup: IP is cached as whitelisted
        mock_redis.get.return_value = "true"

        with patch.object(blacklist_service_with_redis, 'get_db_connection') as mock_db:
            result = blacklist_service_with_redis.is_whitelisted("192.168.1.100")

            # Should return True from cache
            assert result is True

            # Should check cache
            mock_redis.get.assert_called_once_with("whitelist:192.168.1.100")

            # Should NOT query database
            mock_db.assert_not_called()

    def test_whitelist_cache_miss_queries_db_and_caches_result(self, blacklist_service_with_redis, mock_redis):
        """Test cache miss queries DB and caches the result"""
        # Setup: Cache miss
        mock_redis.get.return_value = None

        # Mock database query (IP is whitelisted)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 1}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(blacklist_service_with_redis, 'get_db_connection', return_value=mock_conn):
            result = blacklist_service_with_redis.is_whitelisted("192.168.1.100")

            # Should return True from DB
            assert result is True

            # Should check cache first
            mock_redis.get.assert_called_once_with("whitelist:192.168.1.100")

            # Should query database
            mock_cursor.execute.assert_called_once()

            # Should cache the result with TTL
            mock_redis.setex.assert_called_once_with(
                "whitelist:192.168.1.100",
                blacklist_service_with_redis.cache_ttl,
                "true"
            )

    def test_whitelist_cache_stores_negative_results(self, blacklist_service_with_redis, mock_redis):
        """Test cache stores negative results (not whitelisted)"""
        # Setup: Cache miss
        mock_redis.get.return_value = None

        # Mock database query (IP is NOT whitelisted)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 0}
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(blacklist_service_with_redis, 'get_db_connection', return_value=mock_conn):
            result = blacklist_service_with_redis.is_whitelisted("1.2.3.4")

            # Should return False
            assert result is False

            # Should cache negative result
            mock_redis.setex.assert_called_once_with(
                "whitelist:1.2.3.4",
                blacklist_service_with_redis.cache_ttl,
                "false"
            )

    def test_whitelist_cache_ttl_is_5_minutes(self, blacklist_service_with_redis):
        """Test cache TTL is 5 minutes (300 seconds)"""
        assert blacklist_service_with_redis.cache_ttl == 300


class TestRedisCacheBlacklist:
    """Test Redis caching for blacklist checks"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = MagicMock(spec=redis.Redis)
        return mock_client

    @pytest.fixture
    def blacklist_service_with_redis(self, mock_redis):
        """Create BlacklistService with mocked Redis"""
        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis
            return service

    def test_blacklist_cache_hit_returns_cached_result(self, blacklist_service_with_redis, mock_redis):
        """Test blacklist cache hit returns cached result"""
        # Setup: Cached blacklist result
        cached_result = {
            "blocked": True,
            "reason": "blacklisted",
            "metadata": {"source": "REGTECH", "cache_hit": False}
        }
        mock_redis.get.return_value = json.dumps(cached_result)

        # Mock whitelist check (not whitelisted)
        with patch.object(blacklist_service_with_redis, 'is_whitelisted', return_value=False):
            with patch.object(blacklist_service_with_redis, 'get_db_connection') as mock_db:
                result = blacklist_service_with_redis.check_blacklist("1.2.3.4")

                # Should return cached result
                assert result["blocked"] is True
                assert result["reason"] == "blacklisted"
                assert result["metadata"]["cache_hit"] is True

                # Should NOT query database
                mock_db.assert_not_called()

    def test_blacklist_cache_miss_queries_db(self, blacklist_service_with_redis, mock_redis):
        """Test blacklist cache miss queries database"""
        # Setup: Cache miss
        mock_redis.get.return_value = None

        # Mock whitelist check (not whitelisted)
        with patch.object(blacklist_service_with_redis, 'is_whitelisted', return_value=False):
            # Mock database query (IP is blacklisted)
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {
                "ip_address": "1.2.3.4",
                "reason": "malicious",
                "source": "REGTECH",
                "detection_count": 5
            }
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(blacklist_service_with_redis, 'get_db_connection', return_value=mock_conn):
                result = blacklist_service_with_redis.check_blacklist("1.2.3.4")

                # Should return blocked
                assert result["blocked"] is True
                assert result["reason"] == "malicious"

                # Should query database
                mock_cursor.execute.assert_called_once()

                # Should cache result
                assert mock_redis.setex.called

    def test_blacklist_cache_whitelist_bypass_uses_whitelist_cache(self, blacklist_service_with_redis, mock_redis):
        """Test whitelisted IP uses whitelist cache, skips blacklist check"""
        # Setup: Whitelist cache hit
        mock_redis.get.side_effect = lambda key: "true" if "whitelist" in key else None

        with patch.object(blacklist_service_with_redis, 'get_db_connection') as mock_db:
            result = blacklist_service_with_redis.check_blacklist("192.168.1.100")

            # Should return not blocked (whitelist priority)
            assert result["blocked"] is False
            assert result["reason"] == "whitelist"

            # Should NOT query database for whitelist (cache hit)
            # Should NOT query database for blacklist (whitelist takes priority)
            mock_db.assert_not_called()


class TestRedisCacheGracefulDegradation:
    """Test graceful degradation when Redis is unavailable"""

    def test_whitelist_check_works_without_redis(self):
        """Test whitelist check works when Redis is unavailable"""
        # Create service without Redis
        with patch('core.services.blacklist_service.redis.Redis', side_effect=redis.ConnectionError("Redis unavailable")):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()

            # Redis should be None
            assert service.redis_client is None

            # Mock database query
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"count": 1}
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.is_whitelisted("192.168.1.100")

                # Should still work (DB fallback)
                assert result is True

    def test_blacklist_check_works_without_redis(self):
        """Test blacklist check works when Redis is unavailable"""
        with patch('core.services.blacklist_service.redis.Redis', side_effect=redis.ConnectionError("Redis unavailable")):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()

            # Mock whitelist (not whitelisted)
            with patch.object(service, 'is_whitelisted', return_value=False):
                # Mock blacklist DB query
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = {
                    "ip_address": "1.2.3.4",
                    "reason": "blacklisted",
                    "source": "REGTECH",
                    "detection_count": 1
                }
                mock_conn.cursor.return_value = mock_cursor

                with patch.object(service, 'get_db_connection', return_value=mock_conn):
                    result = service.check_blacklist("1.2.3.4")

                    # Should still work (DB fallback)
                    assert result["blocked"] is True

    def test_cache_read_error_falls_back_to_db(self):
        """Test cache read errors fall back to database"""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get.side_effect = redis.RedisError("Cache read failed")

        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis

            # Mock database query
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"count": 0}
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.is_whitelisted("1.2.3.4")

                # Should fall back to DB
                assert result is False
                mock_cursor.execute.assert_called_once()

    def test_cache_write_error_does_not_prevent_operation(self):
        """Test cache write errors don't prevent operations"""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = redis.RedisError("Cache write failed")

        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis

            # Mock database query
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"count": 1}
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                result = service.is_whitelisted("192.168.1.100")

                # Should still return correct result
                assert result is True

                # Cache write attempted but failed (shouldn't crash)
                mock_redis.setex.assert_called_once()


class TestCacheKeyNaming:
    """Test cache key naming conventions"""

    def test_whitelist_cache_key_format(self):
        """Test whitelist cache keys follow 'whitelist:{ip}' format"""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get.return_value = None

        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis

            # Mock database
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"count": 0}
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                service.is_whitelisted("1.2.3.4")

                # Should use correct key format
                mock_redis.get.assert_called_with("whitelist:1.2.3.4")
                mock_redis.setex.assert_called()
                call_args = mock_redis.setex.call_args[0]
                assert call_args[0] == "whitelist:1.2.3.4"

    def test_blacklist_cache_key_format(self):
        """Test blacklist cache keys follow 'blacklist:{ip}' format"""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get.return_value = None

        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis

            # Mock whitelist (not whitelisted)
            with patch.object(service, 'is_whitelisted', return_value=False):
                # Mock database
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = None
                mock_conn.cursor.return_value = mock_cursor

                with patch.object(service, 'get_db_connection', return_value=mock_conn):
                    service.check_blacklist("1.2.3.4")

                    # Should use correct key format
                    calls = [call[0][0] for call in mock_redis.get.call_args_list]
                    assert "blacklist:1.2.3.4" in calls


class TestCachePerformance:
    """Test cache performance improvements"""

    def test_cache_reduces_database_queries(self):
        """Test cache significantly reduces database queries"""
        mock_redis = MagicMock(spec=redis.Redis)

        with patch('core.services.blacklist_service.redis.Redis', return_value=mock_redis):
            from core.services.blacklist_service import BlacklistService
            service = BlacklistService()
            service.redis_client = mock_redis

            # First call: cache miss
            mock_redis.get.return_value = None
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"count": 1}
            mock_conn.cursor.return_value = mock_cursor

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                service.is_whitelisted("192.168.1.100")
                db_calls_first = mock_cursor.execute.call_count

            # Second call: cache hit
            mock_redis.get.return_value = "true"
            mock_cursor.execute.reset_mock()

            with patch.object(service, 'get_db_connection', return_value=mock_conn):
                service.is_whitelisted("192.168.1.100")
                db_calls_second = mock_cursor.execute.call_count

            # Second call should have 0 DB queries (cache hit)
            assert db_calls_first == 1
            assert db_calls_second == 0
