"""
Advanced tests for blacklist_service.py - Phase 4.2
Target: Increase coverage from 36% to 80%+ by testing uncovered methods
Focus: collection_status, active_blacklist, statistics, search, schema operations
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from core.services.blacklist_service import BlacklistService, HealthStatus


class TestCollectionStatus:
    """Test get_collection_status() method - Lines 336-372"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance with mocked Redis"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_get_collection_status_success(self, service):
        """Test get_collection_status returns correct structure"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock fetchall() to return source data
        mock_cursor.fetchall.return_value = [
            {"source": "REGTECH", "count": 100, "last_seen": datetime(2025, 10, 20, 12, 0, 0)},
            {"source": "SECUDIUM", "count": 50, "last_seen": datetime(2025, 10, 19, 12, 0, 0)},
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.get_collection_status()

        assert result["collection_enabled"] is True
        assert result["total_ips"] == 150
        assert "last_updated" in result
        assert "sources" in result
        assert "regtech" in result["sources"]
        assert result["sources"]["regtech"]["total_ips"] == 100
        assert result["sources"]["regtech"]["enabled"] is True
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_get_collection_status_empty_sources(self, service):
        """Test get_collection_status with no sources"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.get_collection_status()

        assert result["collection_enabled"] is True
        assert result["total_ips"] == 0
        assert result["sources"] == {}

    def test_get_collection_status_error_handling(self, service):
        """Test get_collection_status handles database errors"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB connection failed")):
            result = service.get_collection_status()

        assert "error" in result
        assert result["collection_enabled"] is False
        assert "DB connection failed" in result["error"]


class TestActiveBlacklistAsync:
    """Test get_active_blacklist() async method - Lines 376-433"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_get_active_blacklist_text_format(self, service):
        """Test get_active_blacklist with text format"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("1.2.3.4",),
            ("5.6.7.8",),
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = await service.get_active_blacklist(format_type="text")

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert "1.2.3.4" in result["data"]
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_active_blacklist_enhanced_format(self, service):
        """Test get_active_blacklist with enhanced format"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock fetchall() to return tuple data (not dict)
        mock_cursor.fetchall.return_value = [
            ("1.2.3.4", "Malicious", "REGTECH", True, datetime(2025, 10, 20), 5),
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = await service.get_active_blacklist(format_type="enhanced")

        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["ip_address"] == "1.2.3.4"
        assert result["data"][0]["reason"] == "Malicious"
        assert result["data"][0]["detection_count"] == 5

    @pytest.mark.asyncio
    async def test_get_active_blacklist_fortigate_format(self, service):
        """Test get_active_blacklist with fortigate format"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("1.2.3.4",),
            ("5.6.7.8",),
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = await service.get_active_blacklist(format_type="fortigate")

        assert result["success"] is True
        assert "entries" in result["data"]
        assert result["data"]["total"] == 2
        assert result["data"]["format"] == "fortigate_external_connector"
        assert result["data"]["entries"][0] == {"ip": "1.2.3.4", "action": "block"}

    @pytest.mark.asyncio
    async def test_get_active_blacklist_error_handling(self, service):
        """Test get_active_blacklist handles errors"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB error")):
            result = await service.get_active_blacklist()

        assert result["success"] is False
        assert "error" in result


class TestActiveBlacklistSync:
    """Test get_active_blacklist_ips() synchronous method - Lines 437-467"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_get_active_blacklist_ips_success(self, service):
        """Test get_active_blacklist_ips returns IP list"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # RealDictCursor returns dict-like rows
        mock_cursor.fetchall.return_value = [
            {"ip_address": "1.2.3.4"},
            {"ip_address": "5.6.7.8"},
            {"ip_address": "9.10.11.12"},
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.get_active_blacklist_ips()

        assert len(result) == 3
        assert "1.2.3.4" in result
        assert "5.6.7.8" in result

    def test_get_active_blacklist_ips_empty(self, service):
        """Test get_active_blacklist_ips with no results"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.get_active_blacklist_ips()

        assert result == []

    def test_get_active_blacklist_ips_error_handling(self, service):
        """Test get_active_blacklist_ips handles errors gracefully"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB error")):
            result = service.get_active_blacklist_ips()

        assert result == []


class TestFortiGateFormat:
    """Test format_for_fortigate() method - Lines 471-480"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_format_for_fortigate_success(self, service):
        """Test format_for_fortigate returns correct structure"""
        ips = ["1.2.3.4", "5.6.7.8", "9.10.11.12"]

        result = service.format_for_fortigate(ips)

        assert "entries" in result
        assert result["total"] == 3
        assert result["format"] == "fortigate_external_connector"
        assert "timestamp" in result
        assert len(result["entries"]) == 3
        assert result["entries"][0] == {"ip": "1.2.3.4", "action": "block"}

    def test_format_for_fortigate_empty_list(self, service):
        """Test format_for_fortigate with empty list"""
        result = service.format_for_fortigate([])

        assert result["total"] == 0
        assert result["entries"] == []

    def test_format_for_fortigate_error_handling(self, service):
        """Test format_for_fortigate handles errors"""
        # Pass invalid input to trigger exception
        with patch('core.services.blacklist_service.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Datetime error")
            result = service.format_for_fortigate(["1.2.3.4"])

        assert "error" in result
        assert result["total"] == 0


class TestSearchIP:
    """Test search_ip() method - Lines 484-528"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_search_ip_found(self, service):
        """Test search_ip when IP is found"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Return tuple (not dict) as cursor returns tuples
        mock_cursor.fetchone.return_value = (
            "1.2.3.4", "Malicious", "REGTECH", True, datetime(2025, 10, 20), 5
        )

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.search_ip("1.2.3.4")

        assert result["success"] is True
        assert result["found"] is True
        assert result["data"]["ip_address"] == "1.2.3.4"
        assert result["data"]["reason"] == "Malicious"
        assert result["data"]["source"] == "REGTECH"
        assert result["data"]["detection_count"] == 5

    def test_search_ip_not_found(self, service):
        """Test search_ip when IP is not found"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.search_ip("1.2.3.4")

        assert result["success"] is True
        assert result["found"] is False
        assert result["data"] is None

    def test_search_ip_error_handling(self, service):
        """Test search_ip handles database errors"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB error")):
            result = service.search_ip("1.2.3.4")

        assert result["success"] is False
        assert "error" in result


class TestStatistics:
    """Test get_statistics() and get_system_stats() methods - Lines 532-619"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_get_statistics_success(self, service):
        """Test get_statistics returns correct structure"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock multiple fetchone() calls for different queries
        mock_cursor.fetchone.side_effect = [
            (200,),  # total_ips count
            (150,),  # active_ips count
        ]

        # Mock fetchall() for source statistics
        mock_cursor.fetchall.return_value = [
            ("REGTECH", 100),
            ("SECUDIUM", 50),
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.get_statistics()

        assert result["success"] is True
        assert result["statistics"]["total_ips"] == 200
        assert result["statistics"]["active_ips"] == 150
        assert "REGTECH" in result["statistics"]["sources"]
        assert result["statistics"]["sources"]["REGTECH"]["count"] == 100

    def test_get_statistics_error_handling(self, service):
        """Test get_statistics handles errors"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB error")):
            result = service.get_statistics()

        assert result["success"] is False
        assert "error" in result

    def test_get_system_stats_success(self, service):
        """Test get_system_stats returns correct structure"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            (300,),  # total_ips
            (250,),  # active_ips
        ]

        mock_cursor.fetchall.return_value = [
            ("REGTECH", 200),
        ]

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.get_system_stats()

        assert result["success"] is True
        assert result["total_ips"] == 300
        assert result["active_ips"] == 250
        assert "REGTECH" in result["sources"]

    def test_get_system_stats_error_handling(self, service):
        """Test get_system_stats handles errors with defaults"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB error")):
            result = service.get_system_stats()

        assert result["success"] is False
        assert result["total_ips"] == 0
        assert result["active_ips"] == 0


class TestAsyncCollectionMethods:
    """Test async collection methods - Lines 630-674"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_enable_collection_success(self, service):
        """Test enable_collection method"""
        result = await service.enable_collection()

        assert result["success"] is True
        assert "message" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_disable_collection_success(self, service):
        """Test disable_collection method"""
        result = await service.disable_collection()

        assert result["success"] is True
        assert "message" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_collect_all_data_success(self, service):
        """Test collect_all_data method"""
        # Mock _collect_regtech_data
        mock_regtech_result = {"success": True, "collected": 100}

        with patch.object(service, '_collect_regtech_data', return_value=mock_regtech_result):
            result = await service.collect_all_data(force=False)

        assert "success" in result
        assert "results" in result
        assert "regtech" in result["results"]
        assert result["summary"]["total_sources"] == 1


class TestSchemaOperations:
    """Test schema-related methods - Lines 145-168, 712-738, 742-823"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_create_whitelist_table_success(self, service):
        """Test _create_whitelist_table creates table"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            service._create_whitelist_table()

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_create_whitelist_table_error_handling(self, service):
        """Test _create_whitelist_table handles errors"""
        with patch.object(service, 'get_db_connection', side_effect=Exception("DB error")):
            # Should not raise exception
            service._create_whitelist_table()

    def test_sync_with_collector_healthy(self, service):
        """Test sync_with_collector when collector is healthy"""
        # Mock requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock get_system_stats
        mock_stats = {
            "total_ips": 1000,
            "active_ips": 800,
        }

        with patch('requests.get', return_value=mock_response), \
             patch.object(service, 'get_system_stats', return_value=mock_stats):
            result = service.sync_with_collector()

        assert result["success"] is True
        assert result["collector_status"] == "healthy"
        assert result["total_ips"] == 1000
        assert result["database_shared"] is True

    def test_sync_with_collector_unreachable(self, service):
        """Test sync_with_collector when collector is unreachable"""
        # Mock requests.get to raise exception
        with patch('requests.get', side_effect=Exception("Connection refused")), \
             patch.object(service, 'get_system_stats', return_value={"total_ips": 0, "active_ips": 0}):
            result = service.sync_with_collector()

        assert result["success"] is True
        assert result["collector_status"] == "unreachable"


class TestDataRefreshOperations:
    """Test data refresh methods - Lines 827-920"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance"""
        with patch('redis.Redis'):
            service = BlacklistService()
            service.redis_client = MagicMock()
            return service

    def test_fallback_direct_collection(self, service):
        """Test _fallback_direct_collection returns error"""
        result = service._fallback_direct_collection()

        assert result["success"] is False
        assert "error" in result
        assert result["fallback_attempted"] is True


class TestCacheWriteFailures:
    """Test cache write failure paths - Lines 130-131, 265-266"""

    @pytest.fixture
    def service(self):
        """Create BlacklistService instance with failing Redis"""
        with patch('redis.Redis'):
            service = BlacklistService()
            # Mock Redis client that fails on setex
            service.redis_client = MagicMock()
            service.redis_client.setex.side_effect = Exception("Redis write failed")
            return service

    def test_is_whitelisted_cache_write_failure(self, service):
        """Test is_whitelisted handles Redis write failures gracefully"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"count": 1}

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            # Should not raise exception, should return True
            result = service.is_whitelisted("1.2.3.4")

        assert result is True

    def test_check_blacklist_cache_write_failure(self, service):
        """Test check_blacklist handles Redis write failures gracefully"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        # Mock Redis get to return None (cache miss)
        service.redis_client.get.return_value = None

        with patch.object(service, 'get_db_connection', return_value=mock_conn):
            result = service.check_blacklist("1.2.3.4")

        assert result["blocked"] is False
        assert result["reason"] == "not_in_blacklist"
