"""
Unit tests for DatabaseService
"""
import pytest
from unittest.mock import MagicMock, patch
import psycopg2


class TestDatabaseService:
    """Test cases for DatabaseService"""

    @pytest.fixture
    def db_service(self):
        """Create DatabaseService instance"""
        with patch('psycopg2.pool.SimpleConnectionPool'):
            from core.services.database_service import DatabaseService
            service = DatabaseService()
            return service

    def test_get_connection_returns_connection(self, db_service):
        """Test get_connection returns a database connection"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        db_service._pool = mock_pool

        conn = db_service.get_connection()

        assert conn == mock_conn
        mock_pool.getconn.assert_called_once()

    def test_return_connection_returns_connection_to_pool(self, db_service):
        """Test return_connection returns connection to pool"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()

        db_service._pool = mock_pool
        db_service.return_connection(mock_conn)

        mock_pool.putconn.assert_called_once_with(mock_conn)

    def test_connection_pool_singleton_pattern(self):
        """Test DatabaseService follows singleton pattern"""
        with patch('psycopg2.pool.SimpleConnectionPool'):
            from core.services.database_service import DatabaseService

            service1 = DatabaseService()
            service2 = DatabaseService()

            assert service1 is service2
