"""
Unit tests for BlacklistService
"""
import pytest
from unittest.mock import MagicMock, patch


class TestBlacklistService:
    """Test cases for BlacklistService"""

    @pytest.fixture
    def blacklist_service(self):
        """Create BlacklistService instance"""
        with patch('core.services.database_service.db_service'):
            from core.services.blacklist_service import BlacklistService
            return BlacklistService()

    def test_is_whitelisted_returns_true_for_whitelisted_ip(self, blacklist_service, mock_db_connection):
        """Test whitelist check returns True for whitelisted IP"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = (1,)

        with patch.object(blacklist_service, '_get_db_connection', return_value=mock_conn):
            result = blacklist_service.is_whitelisted("192.168.1.100")

        assert result is True
        mock_cursor.execute.assert_called_once()

    def test_is_whitelisted_returns_false_for_non_whitelisted_ip(self, blacklist_service, mock_db_connection):
        """Test whitelist check returns False for non-whitelisted IP"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = (0,)

        with patch.object(blacklist_service, '_get_db_connection', return_value=mock_conn):
            result = blacklist_service.is_whitelisted("1.2.3.4")

        assert result is False

    def test_check_blacklist_priority_whitelist_first(self, blacklist_service):
        """Test that whitelist check has priority over blacklist"""
        with patch.object(blacklist_service, 'is_whitelisted', return_value=True):
            with patch.object(blacklist_service, '_check_blacklist_db') as mock_blacklist:
                result = blacklist_service.check_blacklist("192.168.1.100")

                assert result["blocked"] is False
                assert result["reason"] == "whitelist"
                mock_blacklist.assert_not_called()  # Should not check blacklist if whitelisted

    def test_check_blacklist_returns_blocked_for_blacklisted_ip(self, blacklist_service):
        """Test blacklist check returns blocked for blacklisted IP"""
        with patch.object(blacklist_service, 'is_whitelisted', return_value=False):
            with patch.object(blacklist_service, '_check_blacklist_db', return_value={"found": True, "country": "CN"}):
                result = blacklist_service.check_blacklist("1.2.3.4")

                assert result["blocked"] is True
                assert result["reason"] == "blacklisted"
                assert result["metadata"]["country"] == "CN"

    def test_check_blacklist_returns_not_blocked_for_clean_ip(self, blacklist_service):
        """Test blacklist check returns not blocked for clean IP"""
        with patch.object(blacklist_service, 'is_whitelisted', return_value=False):
            with patch.object(blacklist_service, '_check_blacklist_db', return_value={"found": False}):
                result = blacklist_service.check_blacklist("8.8.8.8")

                assert result["blocked"] is False
                assert result["reason"] == "not_found"
