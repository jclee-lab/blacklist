"""
Unit tests for encryption utility
Tests encryption.py with mocked file system and cryptography
Target: 0% → 80% coverage (93 statements)
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
import base64
import os


@pytest.mark.unit
class TestCredentialEncryptionInit:
    """Test CredentialEncryption initialization"""

    def test_initialization_with_provided_key(self):
        """Test initialization with explicitly provided master key"""
        from core.utils.encryption import CredentialEncryption

        master_key = "test_master_key_12345"

        encryptor = CredentialEncryption(master_key=master_key)

        assert encryptor.master_key == master_key
        assert encryptor.fernet is not None

    def test_initialization_without_key_uses_auto_generation(self):
        """Test initialization without key triggers auto-generation"""
        from core.utils.encryption import CredentialEncryption

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("os.makedirs"):
                    with patch("builtins.open", mock_open()):
                        encryptor = CredentialEncryption()

                        # Should have generated a key
                        assert encryptor.master_key is not None
                        assert len(encryptor.master_key) > 0


@pytest.mark.unit
class TestGetOrCreateMasterKey:
    """Test master key acquisition/generation"""

    def test_get_master_key_from_environment_variable(self):
        """Test loading master key from ENCRYPTION_MASTER_KEY env var"""
        from core.utils.encryption import CredentialEncryption

        env_key = "env_master_key_123"

        with patch.dict(os.environ, {"ENCRYPTION_MASTER_KEY": env_key}):
            encryptor = CredentialEncryption()

            assert encryptor.master_key == env_key

    def test_get_master_key_from_file(self):
        """Test loading master key from /app/config/.master_key file"""
        from core.utils.encryption import CredentialEncryption

        file_key = "file_master_key_456"

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=file_key)):
                    encryptor = CredentialEncryption()

                    assert encryptor.master_key == file_key

    def test_create_new_master_key_when_not_exists(self):
        """Test creating new master key when env var and file not exist"""
        from core.utils.encryption import CredentialEncryption

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("os.makedirs"):
                    with patch("builtins.open", mock_open()) as mock_file:
                        encryptor = CredentialEncryption()

                        # Should have generated a new key
                        assert encryptor.master_key is not None
                        # Key should be base64 encoded (ends with = or alphanumeric)
                        assert isinstance(encryptor.master_key, str)

    def test_key_file_read_exception_handled(self):
        """Test handling of file read exceptions"""
        from core.utils.encryption import CredentialEncryption

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=PermissionError("No access")):
                    with patch("os.makedirs"):
                        with patch("builtins.open", mock_open()):
                            encryptor = CredentialEncryption()

                            # Should fall back to generating new key
                            assert encryptor.master_key is not None

    def test_key_file_write_exception_handled(self):
        """Test handling of file write exceptions"""
        from core.utils.encryption import CredentialEncryption

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                with patch("os.makedirs", side_effect=PermissionError("No write access")):
                    encryptor = CredentialEncryption()

                    # Should still have generated a key despite write failure
                    assert encryptor.master_key is not None


@pytest.mark.unit
class TestEncryptDecrypt:
    """Test encryption and decryption functions"""

    def test_encrypt_decrypt_round_trip(self):
        """Test encrypting and decrypting returns original plaintext"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        plaintext = "secret_password_123"

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_returns_different_value(self):
        """Test encrypt returns different value than plaintext"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        plaintext = "my_secret"

        encrypted = encryptor.encrypt(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

    def test_encrypt_empty_string(self):
        """Test encrypting empty string returns empty string"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")

        encrypted = encryptor.encrypt("")

        assert encrypted == ""

    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns empty string"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")

        decrypted = encryptor.decrypt("")

        assert decrypted == ""

    def test_encrypt_unicode_characters(self):
        """Test encrypting Unicode characters"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        plaintext = "비밀번호_한글_パスワード"

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_long_string(self):
        """Test encrypting long string"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        plaintext = "x" * 10000

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_decrypt_invalid_data_raises_error(self):
        """Test decrypting invalid data raises EncryptionError"""
        from core.utils.encryption import CredentialEncryption, EncryptionError

        encryptor = CredentialEncryption(master_key="test_key_12345")

        with pytest.raises(EncryptionError):
            encryptor.decrypt("invalid_encrypted_data!!!")

    def test_encrypt_with_different_keys_produces_different_output(self):
        """Test same plaintext with different keys produces different ciphertext"""
        from core.utils.encryption import CredentialEncryption

        encryptor1 = CredentialEncryption(master_key="key1")
        encryptor2 = CredentialEncryption(master_key="key2")
        plaintext = "same_secret"

        encrypted1 = encryptor1.encrypt(plaintext)
        encrypted2 = encryptor2.encrypt(plaintext)

        # Different keys should produce different ciphertext
        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_raises_error(self):
        """Test decrypting with wrong key raises error"""
        from core.utils.encryption import CredentialEncryption, EncryptionError

        encryptor1 = CredentialEncryption(master_key="key1")
        encryptor2 = CredentialEncryption(master_key="key2")

        plaintext = "secret"
        encrypted = encryptor1.encrypt(plaintext)

        # Decrypting with different key should fail
        with pytest.raises(EncryptionError):
            encryptor2.decrypt(encrypted)


@pytest.mark.unit
class TestEncryptDecryptCredentials:
    """Test credential encryption/decryption"""

    def test_encrypt_credentials_returns_dict(self):
        """Test encrypt_credentials returns dictionary with encrypted data"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        username = "test_user"
        password = "test_password"

        result = encryptor.encrypt_credentials(username, password)

        assert isinstance(result, dict)
        assert "username" in result
        assert "password" in result
        assert "encrypted" in result
        assert "encryption_version" in result
        assert result["encrypted"] is True
        assert result["encryption_version"] == "1.0"

    def test_encrypt_decrypt_credentials_round_trip(self):
        """Test encrypting and decrypting credentials returns original values"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        username = "admin"
        password = "super_secret_pass"

        encrypted = encryptor.encrypt_credentials(username, password)
        decrypted = encryptor.decrypt_credentials(encrypted)

        assert decrypted["username"] == username
        assert decrypted["password"] == password

    def test_decrypt_credentials_unencrypted_data(self):
        """Test decrypt_credentials with unencrypted data returns as-is"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")

        # Unencrypted data (encrypted: False or missing)
        unencrypted_data = {
            "username": "plain_user",
            "password": "plain_pass",
            "encrypted": False,
        }

        decrypted = encryptor.decrypt_credentials(unencrypted_data)

        assert decrypted["username"] == "plain_user"
        assert decrypted["password"] == "plain_pass"

    def test_decrypt_credentials_missing_encrypted_field(self):
        """Test decrypt_credentials with missing 'encrypted' field"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")

        # Data without 'encrypted' field
        data = {"username": "user", "password": "pass"}

        decrypted = encryptor.decrypt_credentials(data)

        assert decrypted["username"] == "user"
        assert decrypted["password"] == "pass"

    def test_encrypt_credentials_empty_values(self):
        """Test encrypting empty username and password"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")

        result = encryptor.encrypt_credentials("", "")

        assert result["username"] == ""
        assert result["password"] == ""
        assert result["encrypted"] is True


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing functions"""

    def test_create_password_hash(self):
        """Test creating password hash"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        password = "my_password"

        hash_value = encryptor.create_password_hash(password)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 character hex string

    def test_create_password_hash_deterministic(self):
        """Test same password produces same hash"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        password = "test_pass"

        hash1 = encryptor.create_password_hash(password)
        hash2 = encryptor.create_password_hash(password)

        assert hash1 == hash2

    def test_create_password_hash_different_passwords(self):
        """Test different passwords produce different hashes"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")

        hash1 = encryptor.create_password_hash("password1")
        hash2 = encryptor.create_password_hash("password2")

        assert hash1 != hash2

    def test_verify_password_hash_correct_password(self):
        """Test verifying correct password returns True"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        password = "correct_password"

        hash_value = encryptor.create_password_hash(password)
        result = encryptor.verify_password_hash(password, hash_value)

        assert result is True

    def test_verify_password_hash_incorrect_password(self):
        """Test verifying incorrect password returns False"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        correct_password = "correct"
        wrong_password = "wrong"

        hash_value = encryptor.create_password_hash(correct_password)
        result = encryptor.verify_password_hash(wrong_password, hash_value)

        assert result is False


@pytest.mark.unit
class TestEncryptionError:
    """Test EncryptionError exception"""

    def test_encryption_error_can_be_raised(self):
        """Test EncryptionError can be raised"""
        from core.utils.encryption import EncryptionError

        with pytest.raises(EncryptionError):
            raise EncryptionError("Test encryption error")

    def test_encryption_error_message(self):
        """Test EncryptionError preserves message"""
        from core.utils.encryption import EncryptionError

        error_message = "Encryption failed for sensitive data"

        with pytest.raises(EncryptionError) as exc_info:
            raise EncryptionError(error_message)

        assert str(exc_info.value) == error_message

    def test_encryption_error_is_exception(self):
        """Test EncryptionError is subclass of Exception"""
        from core.utils.encryption import EncryptionError

        assert issubclass(EncryptionError, Exception)


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_encrypt_string_convenience_function(self):
        """Test encrypt_string convenience function"""
        from core.utils.encryption import encrypt_string

        plaintext = "test_secret"

        encrypted = encrypt_string(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

    def test_decrypt_string_convenience_function(self):
        """Test decrypt_string convenience function"""
        from core.utils.encryption import encrypt_string, decrypt_string

        plaintext = "test_secret"

        encrypted = encrypt_string(plaintext)
        decrypted = decrypt_string(encrypted)

        assert decrypted == plaintext

    def test_encrypt_credentials_convenience_function(self):
        """Test encrypt_credentials convenience function"""
        from core.utils.encryption import encrypt_credentials

        result = encrypt_credentials("user", "pass")

        assert isinstance(result, dict)
        assert "username" in result
        assert "password" in result
        assert "encrypted" in result

    def test_decrypt_credentials_convenience_function(self):
        """Test decrypt_credentials convenience function"""
        from core.utils.encryption import encrypt_credentials, decrypt_credentials

        username = "test_user"
        password = "test_pass"

        encrypted = encrypt_credentials(username, password)
        decrypted = decrypt_credentials(encrypted)

        assert decrypted["username"] == username
        assert decrypted["password"] == password


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and special scenarios"""

    def test_encrypt_special_characters(self):
        """Test encrypting special characters"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        plaintext = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_newlines_and_whitespace(self):
        """Test encrypting strings with newlines and whitespace"""
        from core.utils.encryption import CredentialEncryption

        encryptor = CredentialEncryption(master_key="test_key_12345")
        plaintext = "line1\nline2\tline3\r\nline4   "

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_fernet_instance_creation(self):
        """Test Fernet instance is created correctly"""
        from core.utils.encryption import CredentialEncryption
        from cryptography.fernet import Fernet

        encryptor = CredentialEncryption(master_key="test_key_12345")

        assert isinstance(encryptor.fernet, Fernet)

    def test_multiple_encryptors_independent(self):
        """Test multiple encryptor instances are independent"""
        from core.utils.encryption import CredentialEncryption

        encryptor1 = CredentialEncryption(master_key="key1")
        encryptor2 = CredentialEncryption(master_key="key2")

        # Each should have different Fernet instances
        assert encryptor1.fernet != encryptor2.fernet

    def test_global_encryption_service_exists(self):
        """Test global encryption_service instance exists"""
        from core.utils.encryption import encryption_service

        assert encryption_service is not None
        assert hasattr(encryption_service, "encrypt")
        assert hasattr(encryption_service, "decrypt")
