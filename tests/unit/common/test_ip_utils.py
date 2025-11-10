"""
Unit tests for IP utilities module
Tests ip_utils.py with various IP address scenarios
Target: 0% → 80% coverage (34 statements)
"""
import pytest


@pytest.mark.unit
class TestIPUtils:
    """Test IPUtils class"""

    def test_is_valid_ip_valid_ipv4(self):
        """Test is_valid_ip with valid IPv4 addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_valid_ip("192.168.1.1") is True
        assert IPUtils.is_valid_ip("10.0.0.1") is True
        assert IPUtils.is_valid_ip("172.16.0.1") is True
        assert IPUtils.is_valid_ip("8.8.8.8") is True
        assert IPUtils.is_valid_ip("1.2.3.4") is True

    def test_is_valid_ip_valid_ipv6(self):
        """Test is_valid_ip with valid IPv6 addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_valid_ip("::1") is True
        assert IPUtils.is_valid_ip("2001:db8::1") is True
        assert IPUtils.is_valid_ip("fe80::1") is True
        assert IPUtils.is_valid_ip("::") is True

    def test_is_valid_ip_invalid(self):
        """Test is_valid_ip with invalid IP addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_valid_ip("256.1.2.3") is False
        assert IPUtils.is_valid_ip("192.168.1") is False
        assert IPUtils.is_valid_ip("192.168.1.1.1") is False
        assert IPUtils.is_valid_ip("abc.def.ghi.jkl") is False
        assert IPUtils.is_valid_ip("not_an_ip") is False

    def test_is_valid_ip_empty_string(self):
        """Test is_valid_ip with empty string"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_valid_ip("") is False

    def test_is_valid_ip_none(self):
        """Test is_valid_ip with None (should handle gracefully)"""
        from core.common.ip_utils import IPUtils

        # None will fail the "if not ip_str" check
        assert IPUtils.is_valid_ip(None) is False

    def test_is_private_ip_private_addresses(self):
        """Test is_private_ip with private IP addresses"""
        from core.common.ip_utils import IPUtils

        # RFC 1918 private addresses
        assert IPUtils.is_private_ip("192.168.1.1") is True
        assert IPUtils.is_private_ip("10.0.0.1") is True
        assert IPUtils.is_private_ip("172.16.0.1") is True
        assert IPUtils.is_private_ip("172.31.255.254") is True

    def test_is_private_ip_public_addresses(self):
        """Test is_private_ip with public IP addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_private_ip("8.8.8.8") is False
        assert IPUtils.is_private_ip("1.1.1.1") is False
        assert IPUtils.is_private_ip("216.58.194.174") is False

    def test_is_private_ip_loopback(self):
        """Test is_private_ip with loopback addresses"""
        from core.common.ip_utils import IPUtils

        # Loopback is considered private
        assert IPUtils.is_private_ip("127.0.0.1") is True
        assert IPUtils.is_private_ip("::1") is True

    def test_is_private_ip_invalid(self):
        """Test is_private_ip with invalid IP addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_private_ip("invalid_ip") is False
        assert IPUtils.is_private_ip("256.1.2.3") is False

    def test_get_ip_type_private(self):
        """Test get_ip_type returns 'private' for private IPs"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.get_ip_type("192.168.1.1") == "private"
        assert IPUtils.get_ip_type("10.0.0.1") == "private"
        assert IPUtils.get_ip_type("172.16.0.1") == "private"

    def test_get_ip_type_loopback(self):
        """Test get_ip_type returns 'private' for loopback IPs (loopback is subset of private)"""
        from core.common.ip_utils import IPUtils

        # Loopback IPs are also private, so is_private check catches them first
        assert IPUtils.get_ip_type("127.0.0.1") == "private"
        assert IPUtils.get_ip_type("::1") == "private"

    def test_get_ip_type_multicast(self):
        """Test get_ip_type returns 'multicast' for multicast IPs"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.get_ip_type("224.0.0.1") == "multicast"
        assert IPUtils.get_ip_type("239.255.255.255") == "multicast"
        assert IPUtils.get_ip_type("ff02::1") == "multicast"

    def test_get_ip_type_public(self):
        """Test get_ip_type returns 'public' for public IPs"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.get_ip_type("8.8.8.8") == "public"
        assert IPUtils.get_ip_type("1.1.1.1") == "public"
        assert IPUtils.get_ip_type("216.58.194.174") == "public"

    def test_get_ip_type_invalid(self):
        """Test get_ip_type returns 'invalid' for invalid IPs"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.get_ip_type("invalid_ip") == "invalid"
        assert IPUtils.get_ip_type("256.1.2.3") == "invalid"
        assert IPUtils.get_ip_type("not_an_ip") == "invalid"


@pytest.mark.unit
class TestIPUtilsEdgeCases:
    """Test edge cases for IPUtils"""

    def test_is_valid_ip_whitespace(self):
        """Test is_valid_ip with whitespace"""
        from core.common.ip_utils import IPUtils

        # Leading/trailing whitespace should fail
        assert IPUtils.is_valid_ip(" 192.168.1.1 ") is False
        assert IPUtils.is_valid_ip("\t192.168.1.1\n") is False

    def test_is_valid_ip_special_ipv4(self):
        """Test is_valid_ip with special IPv4 addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_valid_ip("0.0.0.0") is True
        assert IPUtils.is_valid_ip("255.255.255.255") is True

    def test_is_valid_ip_link_local(self):
        """Test is_valid_ip with link-local addresses"""
        from core.common.ip_utils import IPUtils

        assert IPUtils.is_valid_ip("169.254.1.1") is True
        assert IPUtils.is_valid_ip("fe80::1") is True

    def test_is_private_ip_zero_address(self):
        """Test is_private_ip with 0.0.0.0"""
        from core.common.ip_utils import IPUtils

        # 0.0.0.0 is considered private by Python's ipaddress module
        assert IPUtils.is_private_ip("0.0.0.0") is True

    def test_is_private_ip_broadcast(self):
        """Test is_private_ip with broadcast address"""
        from core.common.ip_utils import IPUtils

        # 255.255.255.255 is considered private by Python's ipaddress module
        assert IPUtils.is_private_ip("255.255.255.255") is True

    def test_is_private_ip_link_local(self):
        """Test is_private_ip with link-local addresses"""
        from core.common.ip_utils import IPUtils

        # Link-local is considered private
        assert IPUtils.is_private_ip("169.254.1.1") is True
        assert IPUtils.is_private_ip("fe80::1") is True

    def test_get_ip_type_ipv6_addresses(self):
        """Test get_ip_type with various IPv6 addresses"""
        from core.common.ip_utils import IPUtils

        # IPv6 private (ULA)
        assert IPUtils.get_ip_type("fd00::1") == "private"

        # IPv6 loopback (also private, so returns "private")
        assert IPUtils.get_ip_type("::1") == "private"

        # IPv6 documentation prefix (also considered private/reserved)
        assert IPUtils.get_ip_type("2001:db8::1") == "private"

    def test_get_ip_type_priority_order(self):
        """Test get_ip_type checks in correct priority order"""
        from core.common.ip_utils import IPUtils

        # Private is checked first
        # 127.0.0.1 is both private and loopback, but returns 'private' (checked first)
        assert IPUtils.get_ip_type("127.0.0.1") == "private"

        # Multicast is checked after private/loopback
        assert IPUtils.get_ip_type("224.0.0.1") == "multicast"

    def test_static_methods_no_instance_needed(self):
        """Test that methods work without instantiating IPUtils"""
        from core.common.ip_utils import IPUtils

        # All methods are static, no instance needed
        assert IPUtils.is_valid_ip("1.2.3.4") is True
        assert IPUtils.is_private_ip("192.168.1.1") is True
        assert IPUtils.get_ip_type("8.8.8.8") == "public"

    def test_consecutive_calls_independent(self):
        """Test that consecutive calls are independent (no state)"""
        from core.common.ip_utils import IPUtils

        # First call
        result1 = IPUtils.get_ip_type("192.168.1.1")

        # Second call with different IP
        result2 = IPUtils.get_ip_type("8.8.8.8")

        # Results should be independent
        assert result1 == "private"
        assert result2 == "public"
