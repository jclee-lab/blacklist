"""
Integration tests for Blacklist API endpoints
"""
import pytest
import json


class TestBlacklistAPI:
    """Test cases for Blacklist API endpoints"""

    def test_health_check_returns_200(self, client):
        """Test /health endpoint returns 200"""
        response = client.get("/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] in ["healthy", "unhealthy"]

    def test_blacklist_check_with_query_param(self, client):
        """Test /api/blacklist/check with query parameter"""
        response = client.get("/api/blacklist/check?ip=1.2.3.4")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "blocked" in data
        assert "reason" in data
        assert "ip" in data

    def test_blacklist_check_with_json_body(self, client):
        """Test /api/blacklist/check with JSON body"""
        response = client.post(
            "/api/blacklist/check",
            data=json.dumps({"ip": "1.2.3.4"}),
            content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "blocked" in data

    def test_blacklist_check_invalid_ip_returns_400(self, client):
        """Test /api/blacklist/check with invalid IP returns 400"""
        response = client.get("/api/blacklist/check?ip=invalid_ip")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_whitelist_manual_add(self, client):
        """Test /api/whitelist/manual-add endpoint"""
        payload = {
            "ip_address": "192.168.1.100",
            "country": "KR",
            "reason": "VIP customer"
        }

        response = client.post(
            "/api/whitelist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Should return 200 or 409 (if already exists)
        assert response.status_code in [200, 409]
        data = json.loads(response.data)
        assert "status" in data

    def test_whitelist_list_pagination(self, client):
        """Test /api/whitelist/list with pagination"""
        response = client.get("/api/whitelist/list?page=1&per_page=10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert "total" in data
        assert "page" in data

    def test_blacklist_manual_add(self, client):
        """Test /api/blacklist/manual-add endpoint"""
        payload = {
            "ip_address": "1.2.3.4",
            "country": "CN",
            "notes": "Malicious activity"
        }

        response = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Should return 200 or 409 (if already exists)
        assert response.status_code in [200, 409]
        data = json.loads(response.data)
        assert "status" in data
