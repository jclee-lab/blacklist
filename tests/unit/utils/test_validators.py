"""
Unit tests for validators utility
Tests validators.py with various IP validation scenarios
Target: 0% → 80% coverage (31 statements)
"""
import pytest


@pytest.mark.unit
class TestValidateIP:
    """Test validate_ip function"""

    def test_validate_ip_valid_ipv4(self):
        """Test validate_ip with valid IPv4 addresses"""
        from core.utils.validators import validate_ip

        assert validate_ip("192.168.1.1") is True
        assert validate_ip("10.0.0.1") is True
        assert validate_ip("172.16.0.1") is True
        assert validate_ip("8.8.8.8") is True
        assert validate_ip("1.2.3.4") is True
        assert validate_ip("0.0.0.0") is True
        assert validate_ip("255.255.255.255") is True

    def test_validate_ip_valid_ipv6(self):
        """Test validate_ip with valid IPv6 addresses"""
        from core.utils.validators import validate_ip

        assert validate_ip("::1") is True
        assert validate_ip("2001:db8::1") is True
        assert validate_ip("fe80::1") is True
        assert validate_ip("::") is True
        assert validate_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True

    def test_validate_ip_invalid(self):
        """Test validate_ip with invalid IP addresses"""
        from core.utils.validators import validate_ip

        assert validate_ip("256.1.2.3") is False
        assert validate_ip("192.168.1") is False
        assert validate_ip("192.168.1.1.1") is False
        assert validate_ip("abc.def.ghi.jkl") is False
        assert validate_ip("not_an_ip") is False
        assert validate_ip("192.168.-1.1") is False

    def test_validate_ip_empty_string(self):
        """Test validate_ip with empty string"""
        from core.utils.validators import validate_ip

        assert validate_ip("") is False

    def test_validate_ip_whitespace(self):
        """Test validate_ip with whitespace"""
        from core.utils.validators import validate_ip

        # Leading/trailing whitespace should fail
        assert validate_ip(" 192.168.1.1 ") is False
        assert validate_ip("\t192.168.1.1\n") is False


@pytest.mark.unit
class TestIsPrivateIP:
    """Test is_private_ip function"""

    def test_is_private_ip_rfc1918_addresses(self):
        """Test is_private_ip with RFC 1918 private addresses"""
        from core.utils.validators import is_private_ip

        # 10.0.0.0/8
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.254") is True

        # 172.16.0.0/12
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.254") is True

        # 192.168.0.0/16
        assert is_private_ip("192.168.1.1") is True
        assert is_private_ip("192.168.255.254") is True

    def test_is_private_ip_loopback_addresses(self):
        """Test is_private_ip with loopback addresses"""
        from core.utils.validators import is_private_ip

        # IPv4 loopback
        assert is_private_ip("127.0.0.1") is True
        assert is_private_ip("127.0.0.2") is True
        assert is_private_ip("127.255.255.254") is True

        # IPv6 loopback
        assert is_private_ip("::1") is True

    def test_is_private_ip_link_local_addresses(self):
        """Test is_private_ip with link-local addresses"""
        from core.utils.validators import is_private_ip

        # IPv4 link-local (169.254.0.0/16)
        assert is_private_ip("169.254.1.1") is True
        assert is_private_ip("169.254.255.254") is True

        # IPv6 link-local
        assert is_private_ip("fe80::1") is True

    def test_is_private_ip_public_addresses(self):
        """Test is_private_ip with public IP addresses"""
        from core.utils.validators import is_private_ip

        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False
        assert is_private_ip("216.58.194.174") is False

    def test_is_private_ip_invalid(self):
        """Test is_private_ip with invalid IP addresses"""
        from core.utils.validators import is_private_ip

        assert is_private_ip("invalid_ip") is False
        assert is_private_ip("256.1.2.3") is False
        assert is_private_ip("") is False

    def test_is_private_ip_special_addresses(self):
        """Test is_private_ip with special addresses"""
        from core.utils.validators import is_private_ip

        # 0.0.0.0 is private
        assert is_private_ip("0.0.0.0") is True

        # 255.255.255.255 is private (broadcast)
        assert is_private_ip("255.255.255.255") is True


@pytest.mark.unit
class TestIsPublicIP:
    """Test is_public_ip function"""

    def test_is_public_ip_public_addresses(self):
        """Test is_public_ip with public IP addresses"""
        from core.utils.validators import is_public_ip

        assert is_public_ip("8.8.8.8") is True
        assert is_public_ip("1.1.1.1") is True
        assert is_public_ip("216.58.194.174") is True

    def test_is_public_ip_private_addresses(self):
        """Test is_public_ip excludes private addresses"""
        from core.utils.validators import is_public_ip

        assert is_public_ip("192.168.1.1") is False
        assert is_public_ip("10.0.0.1") is False
        assert is_public_ip("172.16.0.1") is False

    def test_is_public_ip_loopback_addresses(self):
        """Test is_public_ip excludes loopback addresses"""
        from core.utils.validators import is_public_ip

        assert is_public_ip("127.0.0.1") is False
        assert is_public_ip("::1") is False

    def test_is_public_ip_link_local_addresses(self):
        """Test is_public_ip excludes link-local addresses"""
        from core.utils.validators import is_public_ip

        assert is_public_ip("169.254.1.1") is False
        assert is_public_ip("fe80::1") is False

    def test_is_public_ip_reserved_addresses(self):
        """Test is_public_ip excludes reserved addresses"""
        from core.utils.validators import is_public_ip

        # Broadcast
        assert is_public_ip("255.255.255.255") is False

        # Unspecified
        assert is_public_ip("0.0.0.0") is False

    def test_is_public_ip_invalid(self):
        """Test is_public_ip with invalid IP addresses"""
        from core.utils.validators import is_public_ip

        assert is_public_ip("invalid_ip") is False
        assert is_public_ip("256.1.2.3") is False
        assert is_public_ip("") is False


@pytest.mark.unit
class TestFilterPrivateIPs:
    """Test filter_private_ips function"""

    def test_filter_private_ips_mixed_list(self):
        """Test filter_private_ips with mixed IP list"""
        from core.utils.validators import filter_private_ips

        ip_list = [
            "8.8.8.8",         # Public
            "192.168.1.1",     # Private
            "1.1.1.1",         # Public
            "10.0.0.1",        # Private
            "216.58.194.174",  # Public
            "172.16.0.1",      # Private
        ]

        public_ips, private_ips = filter_private_ips(ip_list)

        # Verify separation
        assert len(public_ips) == 3
        assert len(private_ips) == 3

        # Verify public IPs
        assert "8.8.8.8" in public_ips
        assert "1.1.1.1" in public_ips
        assert "216.58.194.174" in public_ips

        # Verify private IPs
        assert "192.168.1.1" in private_ips
        assert "10.0.0.1" in private_ips
        assert "172.16.0.1" in private_ips

    def test_filter_private_ips_all_public(self):
        """Test filter_private_ips with all public IPs"""
        from core.utils.validators import filter_private_ips

        ip_list = ["8.8.8.8", "1.1.1.1", "216.58.194.174"]

        public_ips, private_ips = filter_private_ips(ip_list)

        assert len(public_ips) == 3
        assert len(private_ips) == 0

    def test_filter_private_ips_all_private(self):
        """Test filter_private_ips with all private IPs"""
        from core.utils.validators import filter_private_ips

        ip_list = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]

        public_ips, private_ips = filter_private_ips(ip_list)

        assert len(public_ips) == 0
        assert len(private_ips) == 3

    def test_filter_private_ips_empty_list(self):
        """Test filter_private_ips with empty list"""
        from core.utils.validators import filter_private_ips

        public_ips, private_ips = filter_private_ips([])

        assert len(public_ips) == 0
        assert len(private_ips) == 0

    def test_filter_private_ips_with_loopback(self):
        """Test filter_private_ips includes loopback in private"""
        from core.utils.validators import filter_private_ips

        ip_list = ["127.0.0.1", "8.8.8.8", "::1"]

        public_ips, private_ips = filter_private_ips(ip_list)

        # Loopback should be in private
        assert "127.0.0.1" in private_ips
        assert "::1" in private_ips
        assert "8.8.8.8" in public_ips

    def test_filter_private_ips_returns_tuple(self):
        """Test filter_private_ips returns tuple of two lists"""
        from core.utils.validators import filter_private_ips

        result = filter_private_ips(["8.8.8.8", "192.168.1.1"])

        # Verify return type
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)


@pytest.mark.unit
class TestFilterPublicIPsOnly:
    """Test filter_public_ips_only function"""

    def test_filter_public_ips_only_mixed_list(self):
        """Test filter_public_ips_only with mixed IP list"""
        from core.utils.validators import filter_public_ips_only

        ip_list = [
            "8.8.8.8",         # Public
            "192.168.1.1",     # Private
            "1.1.1.1",         # Public
            "10.0.0.1",        # Private
        ]

        result = filter_public_ips_only(ip_list)

        assert len(result) == 2
        assert "8.8.8.8" in result
        assert "1.1.1.1" in result
        assert "192.168.1.1" not in result
        assert "10.0.0.1" not in result

    def test_filter_public_ips_only_all_public(self):
        """Test filter_public_ips_only with all public IPs"""
        from core.utils.validators import filter_public_ips_only

        ip_list = ["8.8.8.8", "1.1.1.1", "216.58.194.174"]

        result = filter_public_ips_only(ip_list)

        assert len(result) == 3
        assert all(ip in result for ip in ip_list)

    def test_filter_public_ips_only_all_private(self):
        """Test filter_public_ips_only with all private IPs"""
        from core.utils.validators import filter_public_ips_only

        ip_list = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]

        result = filter_public_ips_only(ip_list)

        assert len(result) == 0

    def test_filter_public_ips_only_empty_list(self):
        """Test filter_public_ips_only with empty list"""
        from core.utils.validators import filter_public_ips_only

        result = filter_public_ips_only([])

        assert len(result) == 0
        assert result == []

    def test_filter_public_ips_only_excludes_loopback(self):
        """Test filter_public_ips_only excludes loopback"""
        from core.utils.validators import filter_public_ips_only

        ip_list = ["127.0.0.1", "8.8.8.8", "::1", "1.1.1.1"]

        result = filter_public_ips_only(ip_list)

        # Should only include public IPs
        assert len(result) == 2
        assert "8.8.8.8" in result
        assert "1.1.1.1" in result
        assert "127.0.0.1" not in result
        assert "::1" not in result

    def test_filter_public_ips_only_excludes_reserved(self):
        """Test filter_public_ips_only excludes reserved addresses"""
        from core.utils.validators import filter_public_ips_only

        ip_list = ["0.0.0.0", "8.8.8.8", "255.255.255.255", "1.1.1.1"]

        result = filter_public_ips_only(ip_list)

        # Should only include actual public IPs
        assert len(result) == 2
        assert "8.8.8.8" in result
        assert "1.1.1.1" in result
        assert "0.0.0.0" not in result
        assert "255.255.255.255" not in result

    def test_filter_public_ips_only_returns_list(self):
        """Test filter_public_ips_only returns list"""
        from core.utils.validators import filter_public_ips_only

        result = filter_public_ips_only(["8.8.8.8"])

        assert isinstance(result, list)


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError exception class"""

    def test_validation_error_can_be_raised(self):
        """Test ValidationError can be raised"""
        from core.utils.validators import ValidationError

        with pytest.raises(ValidationError):
            raise ValidationError("Test error")

    def test_validation_error_message(self):
        """Test ValidationError preserves message"""
        from core.utils.validators import ValidationError

        error_message = "Invalid IP address format"

        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(error_message)

        assert str(exc_info.value) == error_message

    def test_validation_error_is_exception(self):
        """Test ValidationError is subclass of Exception"""
        from core.utils.validators import ValidationError

        assert issubclass(ValidationError, Exception)

    def test_validation_error_can_be_caught_as_exception(self):
        """Test ValidationError can be caught as Exception"""
        from core.utils.validators import ValidationError

        try:
            raise ValidationError("Test error")
        except Exception as e:
            assert isinstance(e, ValidationError)
            assert str(e) == "Test error"


@pytest.mark.unit
class TestValidatorsEdgeCases:
    """Test edge cases for validators"""

    def test_validate_ip_with_ipv6_compressed(self):
        """Test validate_ip with compressed IPv6"""
        from core.utils.validators import validate_ip

        # Various compressed forms
        assert validate_ip("2001:db8::1") is True
        assert validate_ip("::1") is True
        assert validate_ip("::") is True
        assert validate_ip("2001:db8::") is True

    def test_filter_functions_preserve_order(self):
        """Test filter functions preserve IP order"""
        from core.utils.validators import filter_private_ips, filter_public_ips_only

        ip_list = ["8.8.8.8", "192.168.1.1", "1.1.1.1", "10.0.0.1"]

        public_ips, private_ips = filter_private_ips(ip_list)

        # Order should be preserved
        assert public_ips == ["8.8.8.8", "1.1.1.1"]
        assert private_ips == ["192.168.1.1", "10.0.0.1"]

        public_only = filter_public_ips_only(ip_list)
        assert public_only == ["8.8.8.8", "1.1.1.1"]

    def test_is_private_ip_ipv6_private_addresses(self):
        """Test is_private_ip with IPv6 private addresses"""
        from core.utils.validators import is_private_ip

        # IPv6 ULA (Unique Local Address) fc00::/7
        assert is_private_ip("fd00::1") is True

        # IPv6 documentation prefix (considered private/reserved)
        assert is_private_ip("2001:db8::1") is True

    def test_filter_with_duplicate_ips(self):
        """Test filter functions handle duplicate IPs"""
        from core.utils.validators import filter_private_ips, filter_public_ips_only

        ip_list = ["8.8.8.8", "192.168.1.1", "8.8.8.8", "192.168.1.1"]

        public_ips, private_ips = filter_private_ips(ip_list)

        # Duplicates should be preserved
        assert len(public_ips) == 2
        assert len(private_ips) == 2

        public_only = filter_public_ips_only(ip_list)
        assert len(public_only) == 2
