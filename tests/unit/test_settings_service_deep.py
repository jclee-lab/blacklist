#!/usr/bin/env python3
"""
Comprehensive deep unit tests for services/settings_service.py
Target: 213 lines, 23% → 80%+ coverage

High-impact methods:
- get_setting: Single setting retrieval with caching/decryption/type conversion
- set_setting: Update setting with encryption
- get_all_settings: Bulk retrieval with filters
- create_setting/delete_setting: CRUD operations
- Encryption/decryption methods
- Cache management
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import sys
import os
import json
import base64

sys.path.insert(0, '/app')
os.chdir('/app')

from core.services.settings_service import SettingsService, settings_service


# ============================================================================
# Initialization Tests
# ============================================================================

class TestSettingsServiceInitialization:
    """Test SettingsService initialization"""

    def test_singleton_pattern(self):
        """Singleton returns same instance"""
        service1 = SettingsService()
        service2 = SettingsService()
        assert service1 is service2

    def test_singleton_instance_exists(self):
        assert settings_service is not None
        assert isinstance(settings_service, SettingsService)

    def test_init_sets_cache_ttl(self):
        service = SettingsService()
        assert service._cache_ttl == 60

    def test_encryption_key_from_env(self):
        """Encryption key initialized from env"""
        with patch.dict(os.environ, {"SETTINGS_ENCRYPTION_KEY": "test_key_value"}):
            service = SettingsService()
            # Re-init encryption key
            service._init_encryption_key()
            assert service._encryption_key == b"test_key_value"

    def test_encryption_key_from_secret_key(self):
        """Encryption key generated from SECRET_KEY when SETTINGS_ENCRYPTION_KEY missing"""
        with patch.dict(os.environ, {"SECRET_KEY": "test-secret"}, clear=False):
            # Remove SETTINGS_ENCRYPTION_KEY if exists
            os.environ.pop('SETTINGS_ENCRYPTION_KEY', None)
            service = SettingsService()
            service._init_encryption_key()
            assert service._encryption_key is not None
            assert len(service._encryption_key) > 0


# ============================================================================
# Encryption/Decryption Tests
# ============================================================================

class TestEncryptionDecryption:
    """Test encryption and decryption methods"""

    @pytest.fixture
    def service(self):
        return SettingsService()

    def test_encrypt_decrypt_roundtrip(self, service):
        """Encrypt and decrypt returns original value"""
        original = "test_password_123"
        encrypted = service._encrypt_value(original)
        decrypted = service._decrypt_value(encrypted)

        assert decrypted == original
        assert encrypted != original

    def test_encrypt_value_changes_data(self, service):
        """Encrypted value is different from original"""
        original = "sensitive_data"
        encrypted = service._encrypt_value(original)

        assert encrypted != original
        assert len(encrypted) > len(original)

    def test_decrypt_invalid_data_raises(self, service):
        """Decrypting invalid data raises exception"""
        with pytest.raises(Exception):
            service._decrypt_value("invalid_encrypted_data")

    def test_encrypt_exception_handling(self, service):
        """Encryption with invalid key raises exception"""
        service._encryption_key = b"invalid_short_key"
        with pytest.raises(Exception):
            service._encrypt_value("test")


# ============================================================================
# Cache Management Tests
# ============================================================================

class TestCacheManagement:
    """Test cache invalidation and validity checks"""

    @pytest.fixture
    def service(self):
        return SettingsService()

    def test_invalidate_cache(self, service):
        """Cache invalidation clears cache and timestamp"""
        service._cache = {"TEST": "value"}
        service._cache_timestamp = datetime.now()

        service._invalidate_cache()

        assert service._cache == {}
        assert service._cache_timestamp is None

    def test_is_cache_valid_false_when_no_timestamp(self, service):
        """Cache invalid when no timestamp"""
        service._cache_timestamp = None
        assert service._is_cache_valid() is False

    def test_is_cache_valid_true_when_fresh(self, service):
        """Cache valid when fresh"""
        service._cache_timestamp = datetime.now()
        assert service._is_cache_valid() is True

    def test_is_cache_valid_false_when_expired(self, service):
        """Cache invalid when expired"""
        service._cache_timestamp = datetime.now() - timedelta(seconds=65)
        assert service._is_cache_valid() is False


# ============================================================================
# get_setting Tests
# ============================================================================

class TestGetSetting:
    """Test get_setting method"""

    @pytest.fixture
    def service(self):
        service = SettingsService()
        service._cache = {}
        service._cache_timestamp = None
        return service

    def test_get_setting_from_cache(self, service):
        """Get setting from cache when valid"""
        service._cache = {"TEST_KEY": "cached_value"}
        service._cache_timestamp = datetime.now()

        result = service.get_setting("TEST_KEY")

        assert result == "cached_value"

    def test_get_setting_from_db(self, service):
        """Get setting from database when not in cache"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("test_value", "string", False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("TEST_KEY")

            assert result == "test_value"
            assert service._cache["TEST_KEY"] == "test_value"

    def test_get_setting_with_decryption(self, service):
        """Get encrypted setting and decrypt"""
        encrypted_value = service._encrypt_value("secret_password")

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (encrypted_value, "password", True)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("PASSWORD")

            assert result == "secret_password"

    def test_get_setting_integer_conversion(self, service):
        """Get setting with integer conversion"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("3600", "integer", False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("INTERVAL")

            assert result == 3600
            assert isinstance(result, int)

    def test_get_setting_boolean_conversion(self, service):
        """Get setting with boolean conversion"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("true", "boolean", False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("ENABLED")

            assert result is True
            assert isinstance(result, bool)

    def test_get_setting_json_conversion(self, service):
        """Get setting with JSON conversion"""
        json_data = {"key": "value", "list": [1, 2, 3]}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (json.dumps(json_data), "json", False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("JSON_CONFIG")

            assert result == json_data

    def test_get_setting_not_found_returns_default(self, service):
        """Get missing setting returns default"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("MISSING_KEY", default="default_value")

            assert result == "default_value"

    def test_get_setting_exception_returns_default(self, service):
        """Get setting with exception returns default"""
        with patch.object(service.db, 'get_connection', side_effect=Exception("DB error")):
            result = service.get_setting("KEY", default="fallback")

            assert result == "fallback"

    def test_get_setting_bypass_cache(self, service):
        """Get setting with use_cache=False bypasses cache"""
        service._cache = {"TEST_KEY": "cached_value"}
        service._cache_timestamp = datetime.now()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("fresh_value", "string", False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_setting("TEST_KEY", use_cache=False)

            assert result == "fresh_value"


# ============================================================================
# _convert_value Tests
# ============================================================================

class TestConvertValue:
    """Test _convert_value type conversion"""

    @pytest.fixture
    def service(self):
        return SettingsService()

    def test_convert_integer(self, service):
        """Convert string to integer"""
        assert service._convert_value("42", "integer") == 42

    def test_convert_boolean_true_variants(self, service):
        """Convert various true values to boolean"""
        assert service._convert_value("true", "boolean") is True
        assert service._convert_value("True", "boolean") is True
        assert service._convert_value("1", "boolean") is True
        assert service._convert_value("yes", "boolean") is True
        assert service._convert_value("on", "boolean") is True

    def test_convert_boolean_false_variants(self, service):
        """Convert various false values to boolean"""
        assert service._convert_value("false", "boolean") is False
        assert service._convert_value("False", "boolean") is False
        assert service._convert_value("0", "boolean") is False
        assert service._convert_value("no", "boolean") is False
        assert service._convert_value("off", "boolean") is False

    def test_convert_json(self, service):
        """Convert JSON string to dict"""
        json_str = '{"key": "value"}'
        result = service._convert_value(json_str, "json")
        assert result == {"key": "value"}

    def test_convert_string(self, service):
        """Convert to string (passthrough)"""
        assert service._convert_value("test", "string") == "test"

    def test_convert_none(self, service):
        """Convert None returns None"""
        assert service._convert_value(None, "string") is None

    def test_convert_exception_returns_original(self, service):
        """Conversion exception returns original value"""
        result = service._convert_value("invalid_json", "json")
        assert result == "invalid_json"


# ============================================================================
# set_setting Tests
# ============================================================================

class TestSetSetting:
    """Test set_setting method"""

    @pytest.fixture
    def service(self):
        service = SettingsService()
        service._cache = {"TEST": "value"}
        service._cache_timestamp = datetime.now()
        return service

    def test_set_setting_plain_value(self, service):
        """Set plain string value"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.set_setting("TEST_KEY", "new_value")

            assert result is True
            mock_conn.commit.assert_called_once()
            # Cache should be invalidated
            assert service._cache == {}

    def test_set_setting_encrypted(self, service):
        """Set encrypted value"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.set_setting("PASSWORD", "secret", encrypt=True)

            assert result is True
            # Verify encrypted flag passed to query
            execute_args = mock_cursor.execute.call_args[0]
            assert execute_args[1][1] is True  # is_encrypted parameter

    def test_set_setting_boolean(self, service):
        """Set boolean value"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.set_setting("ENABLED", True)

            assert result is True
            execute_args = mock_cursor.execute.call_args[0]
            assert execute_args[1][0] == "true"

    def test_set_setting_dict(self, service):
        """Set dict value (JSON)"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.set_setting("CONFIG", {"key": "value"})

            assert result is True
            execute_args = mock_cursor.execute.call_args[0]
            assert json.loads(execute_args[1][0]) == {"key": "value"}

    def test_set_setting_not_found(self, service):
        """Set non-existent setting returns False"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.set_setting("NONEXISTENT", "value")

            assert result is False

    def test_set_setting_exception(self, service):
        """Set setting with exception returns False"""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("DB error")

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.set_setting("KEY", "value")

            assert result is False
            mock_conn.rollback.assert_called_once()


# ============================================================================
# get_all_settings Tests
# ============================================================================

class TestGetAllSettings:
    """Test get_all_settings method"""

    @pytest.fixture
    def service(self):
        return SettingsService()

    def test_get_all_settings_no_filter(self, service):
        """Get all settings without filter"""
        mock_data = [
            ("KEY1", "value1", "string", "Description 1", False, True, "general", 1, datetime(2025, 1, 1)),
            ("KEY2", "value2", "string", "Description 2", False, True, "security", 2, datetime(2025, 1, 2)),
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_all_settings()

            assert len(result) == 2
            assert result[0]["key"] == "KEY1"
            assert result[1]["key"] == "KEY2"

    def test_get_all_settings_by_category(self, service):
        """Get settings filtered by category"""
        mock_data = [
            ("KEY1", "value1", "string", "Description", False, True, "security", 1, datetime(2025, 1, 1)),
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_all_settings(category="security")

            assert len(result) == 1
            assert result[0]["category"] == "security"

    def test_get_all_settings_include_encrypted(self, service):
        """Get all settings with encrypted values decrypted"""
        encrypted_value = service._encrypt_value("secret")
        mock_data = [
            ("PASSWORD", encrypted_value, "password", "Password", True, True, "security", 1, datetime(2025, 1, 1)),
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_all_settings(include_encrypted=True)

            assert result[0]["value"] == "secret"

    def test_get_all_settings_mask_encrypted(self, service):
        """Get all settings with encrypted values masked"""
        mock_data = [
            ("PASSWORD", "encrypted_blob", "password", "Password", True, True, "security", 1, datetime(2025, 1, 1)),
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_all_settings(include_encrypted=False)

            assert result[0]["value"] == "********"

    def test_get_all_settings_decryption_error(self, service):
        """Get all settings handles decryption error"""
        mock_data = [
            ("PASSWORD", "invalid_encrypted", "password", "Password", True, True, "security", 1, datetime(2025, 1, 1)),
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.get_all_settings(include_encrypted=True)

            assert result[0]["value"] == "***DECRYPTION_ERROR***"

    def test_get_all_settings_exception(self, service):
        """Get all settings with exception returns empty list"""
        with patch.object(service.db, 'get_connection', side_effect=Exception("DB error")):
            result = service.get_all_settings()

            assert result == []


# ============================================================================
# get_settings_by_category Tests
# ============================================================================

class TestGetSettingsByCategory:
    """Test get_settings_by_category method"""

    @pytest.fixture
    def service(self):
        return SettingsService()

    def test_get_settings_by_category(self, service):
        """Group settings by category"""
        mock_settings = [
            {"key": "KEY1", "category": "general", "value": "v1"},
            {"key": "KEY2", "category": "security", "value": "v2"},
            {"key": "KEY3", "category": "general", "value": "v3"},
        ]

        with patch.object(service, 'get_all_settings', return_value=mock_settings):
            result = service.get_settings_by_category()

            assert "general" in result
            assert "security" in result
            assert len(result["general"]) == 2
            assert len(result["security"]) == 1

    def test_get_settings_by_category_empty(self, service):
        """Group settings with empty result"""
        with patch.object(service, 'get_all_settings', return_value=[]):
            result = service.get_settings_by_category()

            assert result == {}


# ============================================================================
# create_setting Tests
# ============================================================================

class TestCreateSetting:
    """Test create_setting method"""

    @pytest.fixture
    def service(self):
        service = SettingsService()
        service._cache = {}
        return service

    def test_create_setting_plain(self, service):
        """Create plain setting"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.create_setting("NEW_KEY", "value", "string", "Description", "general")

            assert result is True
            mock_conn.commit.assert_called_once()

    def test_create_setting_encrypted(self, service):
        """Create encrypted setting"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.create_setting("PASSWORD", "secret", "password", encrypt=True)

            assert result is True
            execute_args = mock_cursor.execute.call_args[0]
            # Verify encrypted flag
            assert execute_args[1][5] is True

    def test_create_setting_boolean(self, service):
        """Create boolean setting"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.create_setting("ENABLED", True, "boolean")

            assert result is True
            execute_args = mock_cursor.execute.call_args[0]
            assert execute_args[1][1] == "true"

    def test_create_setting_json(self, service):
        """Create JSON setting"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.create_setting("CONFIG", {"key": "value"}, "json")

            assert result is True

    def test_create_setting_exception(self, service):
        """Create setting with exception returns False"""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("DB error")

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.create_setting("KEY", "value")

            assert result is False
            mock_conn.rollback.assert_called_once()


# ============================================================================
# delete_setting Tests
# ============================================================================

class TestDeleteSetting:
    """Test delete_setting method"""

    @pytest.fixture
    def service(self):
        service = SettingsService()
        service._cache = {"TEST": "value"}
        return service

    def test_delete_setting_success(self, service):
        """Soft delete setting successfully"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.delete_setting("TEST_KEY")

            assert result is True
            mock_conn.commit.assert_called_once()
            # Cache invalidated
            assert service._cache == {}

    def test_delete_setting_not_found(self, service):
        """Delete non-existent setting returns False"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.delete_setting("NONEXISTENT")

            assert result is False

    def test_delete_setting_exception(self, service):
        """Delete setting with exception returns False"""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("DB error")

        with patch.object(service.db, 'get_connection', return_value=mock_conn):
            result = service.delete_setting("KEY")

            assert result is False
            mock_conn.rollback.assert_called_once()


# ============================================================================
# Convenience Methods Tests
# ============================================================================

class TestConvenienceMethods:
    """Test convenience methods"""

    @pytest.fixture
    def service(self):
        return SettingsService()

    def test_get_collection_interval(self, service):
        """Get collection interval"""
        with patch.object(service, 'get_setting', return_value=7200) as mock_get:
            result = service.get_collection_interval()

            mock_get.assert_called_once_with('COLLECTION_INTERVAL', default=3600)
            assert result == 7200

    def test_is_auto_collection_disabled(self, service):
        """Check if auto collection disabled"""
        with patch.object(service, 'get_setting', return_value=False) as mock_get:
            result = service.is_auto_collection_disabled()

            mock_get.assert_called_once_with('DISABLE_AUTO_COLLECTION', default=True)
            assert result is False

    def test_get_regtech_base_url(self, service):
        """Get REGTECH base URL"""
        with patch.object(service, 'get_setting', return_value='https://custom.url') as mock_get:
            result = service.get_regtech_base_url()

            mock_get.assert_called_once_with('REGTECH_BASE_URL', default='https://regtech.fsec.or.kr')
            assert result == 'https://custom.url'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
