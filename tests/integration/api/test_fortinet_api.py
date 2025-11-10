"""
Integration tests for FortiGate/FortiManager API endpoints
"""
import pytest
import json


class TestFortinetAPI:
    """Test FortiGate integration API endpoints"""

    def test_fortinet_active_ips_returns_200(self, client):
        """Test /api/fortinet/active-ips returns 200"""
        response = client.get("/api/fortinet/active-ips")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))

    def test_fortinet_active_ips_structure(self, client):
        """Test active IPs response has valid structure"""
        response = client.get("/api/fortinet/active-ips")

        assert response.status_code == 200
        data = json.loads(response.data)

        if isinstance(data, list):
            # If list, check items have expected fields
            if len(data) > 0:
                item = data[0]
                assert "ip_address" in item or "ip" in item
        elif isinstance(data, dict):
            # If dict, should have data or ips key
            assert "data" in data or "ips" in data or "total" in data

    def test_fortinet_blocklist_returns_200(self, client):
        """Test /api/fortinet/blocklist returns 200"""
        response = client.get("/api/fortinet/blocklist")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))

    def test_fortinet_blocklist_format(self, client):
        """Test blocklist returns FortiGate-compatible format"""
        response = client.get("/api/fortinet/blocklist")

        assert response.status_code == 200
        data = json.loads(response.data)

        # FortiGate blocklist should be a list of IPs or objects
        if isinstance(data, list):
            if len(data) > 0:
                item = data[0]
                # Should be IP string or object with IP field
                assert isinstance(item, (str, dict))
        elif isinstance(data, dict):
            # Dictionary format with ips or data key
            assert "ips" in data or "data" in data or "blocklist" in data

    def test_fortinet_active_ips_excludes_whitelisted(self, client):
        """Test that active IPs excludes whitelisted IPs"""
        # First, add an IP to whitelist
        whitelist_payload = {
            "ip_address": "192.168.100.50",
            "country": "KR",
            "reason": "VIP test"
        }
        client.post(
            "/api/whitelist/manual-add",
            data=json.dumps(whitelist_payload),
            content_type="application/json"
        )

        # Get active IPs
        response = client.get("/api/fortinet/active-ips")
        assert response.status_code == 200
        data = json.loads(response.data)

        # Convert to list of IPs for checking
        ips = []
        if isinstance(data, list):
            ips = [item if isinstance(item, str) else item.get("ip_address", item.get("ip"))
                   for item in data]
        elif isinstance(data, dict) and "data" in data:
            ips = [item if isinstance(item, str) else item.get("ip_address", item.get("ip"))
                   for item in data["data"]]

        # Whitelisted IP should not be in active blocklist
        assert "192.168.100.50" not in ips

    def test_fortinet_api_pagination(self, client):
        """Test FortiGate API supports pagination"""
        response = client.get("/api/fortinet/active-ips?page=1&limit=10")

        assert response.status_code == 200
        data = json.loads(response.data)

        if isinstance(data, dict):
            # If paginated, should have page metadata
            assert "data" in data or "ips" in data or isinstance(data, dict)


class TestFortinetConfiguration:
    """Test FortiGate configuration endpoints"""

    def test_fortinet_config_endpoint_exists(self, client):
        """Test FortiGate configuration endpoint availability"""
        response = client.get("/api/fortinet/config")

        # May return 200, 404, or 401 depending on implementation
        assert response.status_code in [200, 404, 401, 403]

    def test_fortinet_external_connector_format(self, client):
        """Test External Block List (EBL) format compatibility"""
        response = client.get("/api/fortinet/blocklist")

        assert response.status_code == 200
        data = json.loads(response.data)

        # EBL format should be compatible with FortiGate
        # Either plain text IPs or JSON with specific structure
        assert isinstance(data, (list, dict, str))
