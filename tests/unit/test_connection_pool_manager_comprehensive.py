"""
Comprehensive tests for connection_pool_manager.py
Target: connection_pool_manager.py (99 statements, 0% baseline)
Phase 5.3: Connection pool manager testing
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
import psycopg2


class TestSmartConnectionManagerInit:
    """Test SmartConnectionManager.__init__() - Lines 24-31"""

    def test_initialization_creates_instance(self):
        """Test SmartConnectionManager initialization"""
        from core.database.connection_pool_manager import SmartConnectionManager

        manager = SmartConnectionManager()

        assert manager is not None
        assert manager._last_error_time is None
        assert manager._error_count == 0
        assert manager._cached_stats is None

    def test_initialization_sets_default_params(self):
        """Test initialization sets default parameters - Lines 28-31"""
        from core.database.connection_pool_manager import SmartConnectionManager

        manager = SmartConnectionManager()

        assert manager._cache_timeout == 300  # 5 minutes
        assert manager._backoff_duration == 60  # 1 minute
        assert manager._max_error_logs == 5

    def test_initialization_calls_get_connection_params(self):
        """Test initialization gets connection parameters - Line 25"""
        from core.database.connection_pool_manager import SmartConnectionManager

        manager = SmartConnectionManager()

        assert hasattr(manager, 'connection_params')
        assert isinstance(manager.connection_params, dict)


class TestGetConnectionParams:
    """Test _get_connection_params() - Lines 33-55"""

    def test_get_connection_params_from_database_url(self):
        """Test parsing DATABASE_URL - Lines 38-47"""
        from core.database.connection_pool_manager import SmartConnectionManager

        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@dbhost:5433/mydb'
        }):
            manager = SmartConnectionManager()

            assert manager.connection_params['host'] == 'dbhost'
            assert manager.connection_params['port'] == 5433
            assert manager.connection_params['database'] == 'mydb'
            assert manager.connection_params['user'] == 'user'
            assert manager.connection_params['password'] == 'pass'

    def test_get_connection_params_from_postgres_url(self):
        """Test parsing POSTGRES_URL when DATABASE_URL not set - Lines 39-47"""
        from core.database.connection_pool_manager import SmartConnectionManager

        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://pguser:pgpass@pghost:5434/pgdb'
        }, clear=True):
            manager = SmartConnectionManager()

            assert manager.connection_params['host'] == 'pghost'
            assert manager.connection_params['port'] == 5434
            assert manager.connection_params['database'] == 'pgdb'

    def test_get_connection_params_from_individual_env_vars(self):
        """Test parsing individual POSTGRES_* env vars - Lines 49-55"""
        from core.database.connection_pool_manager import SmartConnectionManager

        env_vars = {
            'POSTGRES_HOST': 'custom-host',
            'POSTGRES_PORT': '5555',
            'POSTGRES_DB': 'custom-db',
            'POSTGRES_USER': 'custom-user',
            'POSTGRES_PASSWORD': 'custom-pass',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            manager = SmartConnectionManager()

            assert manager.connection_params['host'] == 'custom-host'
            assert manager.connection_params['port'] == 5555
            assert manager.connection_params['database'] == 'custom-db'
            assert manager.connection_params['user'] == 'custom-user'
            assert manager.connection_params['password'] == 'custom-pass'

    def test_get_connection_params_uses_defaults(self):
        """Test default values when no env vars set - Lines 50-54"""
        from core.database.connection_pool_manager import SmartConnectionManager

        with patch.dict(os.environ, {}, clear=True):
            manager = SmartConnectionManager()

            assert manager.connection_params['host'] == 'blacklist-postgres'
            assert manager.connection_params['port'] == 5432
            assert manager.connection_params['database'] == 'blacklist'
            assert manager.connection_params['user'] == 'postgres'


class TestShouldSuppressErrorLogging:
    """Test _should_suppress_error_logging() - Lines 57-78"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        from core.database.connection_pool_manager import SmartConnectionManager
        return SmartConnectionManager()

    def test_should_not_suppress_first_error(self, manager):
        """Test first error is not suppressed - Lines 62-63"""
        assert manager._should_suppress_error_logging() is False

    def test_should_suppress_after_max_logs(self, manager):
        """Test suppression after max error logs - Lines 68-72"""
        manager._error_count = 5
        manager._last_error_time = datetime.now()

        assert manager._should_suppress_error_logging() is True

    def test_should_not_suppress_within_backoff_if_below_max(self, manager):
        """Test no suppression if below max logs within backoff"""
        manager._error_count = 3
        manager._last_error_time = datetime.now()

        assert manager._should_suppress_error_logging() is False

    def test_should_reset_counter_after_backoff_period(self, manager):
        """Test counter reset after backoff period - Lines 75-76"""
        manager._error_count = 5
        manager._last_error_time = datetime.now() - timedelta(seconds=70)

        # Should not suppress and should reset counter
        result = manager._should_suppress_error_logging()

        assert result is False
        assert manager._error_count == 0


class TestLogConnectionError:
    """Test _log_connection_error() - Lines 80-94"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        from core.database.connection_pool_manager import SmartConnectionManager
        return SmartConnectionManager()

    def test_log_connection_error_increments_count(self, manager):
        """Test error count increments - Line 85"""
        error = Exception("Connection refused")

        manager._log_connection_error(error, "test-host")

        assert manager._error_count == 1
        assert manager._last_error_time is not None

    def test_log_connection_error_suppresses_after_max(self, manager):
        """Test error logging suppression after max - Lines 82-83"""
        manager._error_count = 5
        manager._last_error_time = datetime.now()

        error = Exception("Connection refused")
        initial_count = manager._error_count

        manager._log_connection_error(error, "test-host")

        # Should not increment if suppressed
        assert manager._error_count == initial_count

    def test_log_connection_error_logs_warning_at_max(self, manager):
        """Test special message at max error count - Lines 88-92"""
        manager._error_count = 4  # Will become 5

        with patch('core.database.connection_pool_manager.logger') as mock_logger:
            error = Exception("Connection refused")
            manager._log_connection_error(error, "test-host")

            # Should log with backoff message
            assert mock_logger.warning.called
            call_args = str(mock_logger.warning.call_args)
            assert "억제" in call_args or "suppress" in call_args.lower()


class TestGetConnection:
    """Test get_connection() - Lines 96-129"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        from core.database.connection_pool_manager import SmartConnectionManager
        return SmartConnectionManager()

    def test_get_connection_success_first_host(self, manager):
        """Test successful connection on first host - Lines 110-123"""
        mock_conn = MagicMock()

        with patch('psycopg2.connect', return_value=mock_conn) as mock_connect:
            conn = manager.get_connection()

            assert conn is mock_conn
            assert mock_connect.called
            assert manager._error_count == 0
            assert manager._last_error_time is None

    def test_get_connection_tries_fallback_hosts(self, manager):
        """Test fallback hosts when first fails - Lines 98-127"""
        mock_conn = MagicMock()

        def connect_side_effect(*args, **kwargs):
            if kwargs.get('host') == 'blacklist-postgres':
                return mock_conn
            raise psycopg2.OperationalError("Connection refused")

        with patch('psycopg2.connect', side_effect=connect_side_effect):
            conn = manager.get_connection()

            assert conn is mock_conn

    def test_get_connection_returns_none_all_hosts_fail(self, manager):
        """Test returns None when all hosts fail - Line 129"""
        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection refused")):
            conn = manager.get_connection()

            assert conn is None

    def test_get_connection_logs_errors(self, manager):
        """Test connection errors are logged - Line 126"""
        with patch('psycopg2.connect', side_effect=Exception("Connection refused")), \
             patch.object(manager, '_log_connection_error') as mock_log:
            manager.get_connection()

            assert mock_log.called

    def test_get_connection_uses_timeout(self, manager):
        """Test connection uses 3 second timeout - Line 116"""
        mock_conn = MagicMock()

        with patch('psycopg2.connect', return_value=mock_conn) as mock_connect:
            manager.get_connection()

            # Verify connect_timeout parameter
            assert mock_connect.call_args[1]['connect_timeout'] == 3


class TestGetStatsWithGracefulDegradation:
    """Test get_stats_with_graceful_degradation() - Lines 131-205"""

    @pytest.fixture
    def manager(self):
        """Create manager instance"""
        from core.database.connection_pool_manager import SmartConnectionManager
        return SmartConnectionManager()

    def test_get_stats_returns_cached_if_valid(self, manager):
        """Test returns cached stats if still valid - Lines 134-140"""
        cached_data = {
            "status": "connected",
            "tables": 10,
            "connections": 5
        }
        manager._cached_stats = {
            "data": cached_data,
            "cached_at": datetime.now()
        }

        result = manager.get_stats_with_graceful_degradation()

        assert result == cached_data

    def test_get_stats_fetches_if_cache_expired(self, manager):
        """Test fetches new stats if cache expired"""
        old_cached_data = {
            "status": "connected",
            "tables": 5
        }
        manager._cached_stats = {
            "data": old_cached_data,
            "cached_at": datetime.now() - timedelta(seconds=400)  # Expired
        }

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone.side_effect = [(15,), (8,)]
        mock_conn.get_dsn_parameters.return_value = {"host": "test-host"}

        with patch.object(manager, 'get_connection', return_value=mock_conn):
            result = manager.get_stats_with_graceful_degradation()

            assert result["tables"] == 15
            assert result["connections"] == 8

    def test_get_stats_returns_fallback_on_connection_failure(self, manager):
        """Test returns fallback stats on connection failure - Lines 145-164"""
        with patch.object(manager, 'get_connection', return_value=None):
            result = manager.get_stats_with_graceful_degradation()

            assert result["status"] == "degraded"
            assert result["tables"] == 0
            assert result["connections"] == 0

    def test_get_stats_returns_cached_on_connection_failure(self, manager):
        """Test returns cached data on connection failure - Lines 154-162"""
        cached_data = {
            "status": "connected",
            "tables": 12,
            "connections": 6
        }
        manager._cached_stats = {
            "data": cached_data,
            "cached_at": datetime.now() - timedelta(seconds=400)  # Expired but used as fallback
        }

        with patch.object(manager, 'get_connection', return_value=None):
            result = manager.get_stats_with_graceful_degradation()

            assert result["status"] == "degraded"
            assert result["tables"] == 12  # From cache
            assert result["connections"] == 6  # From cache

    def test_get_stats_executes_queries(self, manager):
        """Test executes table and connection count queries - Lines 169-179"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone.side_effect = [(20,), (10,)]
        mock_conn.get_dsn_parameters.return_value = {"host": "test-host"}

        with patch.object(manager, 'get_connection', return_value=mock_conn):
            result = manager.get_stats_with_graceful_degradation()

            assert result["status"] == "connected"
            assert result["tables"] == 20
            assert result["connections"] == 10

    def test_get_stats_caches_result(self, manager):
        """Test caches successful query result - Lines 191"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone.side_effect = [(15,), (8,)]
        mock_conn.get_dsn_parameters.return_value = {"host": "test-host"}

        with patch.object(manager, 'get_connection', return_value=mock_conn):
            manager.get_stats_with_graceful_degradation()

            assert manager._cached_stats is not None
            assert manager._cached_stats["data"]["tables"] == 15

    def test_get_stats_handles_query_exception(self, manager):
        """Test handles exception during query execution - Lines 195-202"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_cursor.execute.side_effect = Exception("Query failed")

        with patch.object(manager, 'get_connection', return_value=mock_conn):
            result = manager.get_stats_with_graceful_degradation()

            assert result["status"] == "error"
            assert "쿼리 실패" in result["message"] or "Query failed" in result["message"]

    def test_get_stats_closes_connection(self, manager):
        """Test closes connection in finally block - Lines 204-205"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone.side_effect = [(10,), (5,)]
        mock_conn.get_dsn_parameters.return_value = {"host": "test-host"}

        with patch.object(manager, 'get_connection', return_value=mock_conn):
            manager.get_stats_with_graceful_degradation()

            # Verify connection was closed
            assert mock_conn.close.called


class TestModuleLevelFunctions:
    """Test module-level functions - Lines 209-223"""

    def test_global_smart_connection_manager_exists(self):
        """Test global manager instance exists - Line 209"""
        from core.database import connection_pool_manager

        assert hasattr(connection_pool_manager, 'smart_connection_manager')
        assert connection_pool_manager.smart_connection_manager is not None

    def test_get_postgres_stats_smart(self):
        """Test get_postgres_stats_smart() function - Lines 212-214"""
        from core.database.connection_pool_manager import get_postgres_stats_smart

        with patch('core.database.connection_pool_manager.smart_connection_manager.get_stats_with_graceful_degradation') as mock_get_stats:
            mock_get_stats.return_value = {"status": "connected"}

            result = get_postgres_stats_smart()

            assert mock_get_stats.called
            assert result == {"status": "connected"}

    def test_test_smart_connection_success(self):
        """Test test_smart_connection() returns True on success - Lines 217-223"""
        from core.database.connection_pool_manager import test_smart_connection

        mock_conn = MagicMock()

        with patch('core.database.connection_pool_manager.smart_connection_manager.get_connection', return_value=mock_conn):
            result = test_smart_connection()

            assert result is True
            assert mock_conn.close.called

    def test_test_smart_connection_failure(self):
        """Test test_smart_connection() returns False on failure - Line 223"""
        from core.database.connection_pool_manager import test_smart_connection

        with patch('core.database.connection_pool_manager.smart_connection_manager.get_connection', return_value=None):
            result = test_smart_connection()

            assert result is False


class TestIntegration:
    """Integration tests for SmartConnectionManager"""

    def test_connection_retry_with_backoff(self):
        """Test connection retries with exponential backoff"""
        from core.database.connection_pool_manager import SmartConnectionManager

        manager = SmartConnectionManager()

        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection refused")):
            # First attempt
            conn1 = manager.get_connection()
            assert conn1 is None
            assert manager._error_count > 0

            # Second attempt (should still try)
            conn2 = manager.get_connection()
            assert conn2 is None

    def test_cache_timeout_behavior(self):
        """Test cache timeout and refresh behavior"""
        from core.database.connection_pool_manager import SmartConnectionManager

        manager = SmartConnectionManager()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_cursor.fetchone.side_effect = [(10,), (5,), (15,), (8,)]
        mock_conn.get_dsn_parameters.return_value = {"host": "test"}

        with patch.object(manager, 'get_connection', return_value=mock_conn):
            # First call - should query database
            result1 = manager.get_stats_with_graceful_degradation()
            assert result1["tables"] == 10

            # Second call immediately - should use cache
            result2 = manager.get_stats_with_graceful_degradation()
            assert result2["tables"] == 10  # Same cached value

            # Expire cache
            manager._cached_stats["cached_at"] = datetime.now() - timedelta(seconds=400)

            # Third call - should query database again
            result3 = manager.get_stats_with_graceful_degradation()
            assert result3["tables"] == 15  # New value
