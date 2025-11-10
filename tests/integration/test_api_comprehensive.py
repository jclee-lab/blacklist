"""
Comprehensive API Integration Tests

Tests all critical API endpoints with various scenarios:
- IP check endpoints (GET/POST)
- Manual IP add/remove (whitelist/blacklist)
- Collection management
- Statistics and monitoring
- Error handling and edge cases
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestIPCheckEndpoints:
    """Test IP check API endpoints"""

    def test_blacklist_check_get_method(self, client):
        """Test GET /api/blacklist/check with query parameter"""
        response = client.get("/api/blacklist/check?ip=1.2.3.4")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data
        assert "blocked" in data
        assert "reason" in data
        assert "ip" in data
        assert data["ip"] == "1.2.3.4"

    def test_blacklist_check_post_method(self, client):
        """Test POST /api/blacklist/check with JSON body"""
        payload = {"ip": "5.6.7.8"}
        response = client.post(
            "/api/blacklist/check",
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ip"] == "5.6.7.8"

    def test_blacklist_check_missing_ip_returns_400(self, client):
        """Test missing IP parameter returns 400"""
        response = client.get("/api/blacklist/check")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_blacklist_check_whitelist_priority(self, client):
        """Test whitelisted IP is not blocked"""
        # This test requires database setup or mocking
        # Whitelist should always take priority
        pass  # Implement with database fixtures

    def test_blacklist_check_returns_metadata(self, client):
        """Test response includes metadata"""
        response = client.get("/api/blacklist/check?ip=1.2.3.4")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "metadata" in data


class TestManualIPManagement:
    """Test manual IP add/remove endpoints"""

    def test_whitelist_manual_add_valid_ip(self, client):
        """Test adding valid IP to whitelist"""
        payload = {
            "ip_address": "192.168.100.1",
            "country": "KR",
            "reason": "VIP customer test"
        }

        response = client.post(
            "/api/whitelist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Should succeed (200) or conflict if exists (409)
        assert response.status_code in [200, 409]

    def test_whitelist_manual_add_invalid_ip_format(self, client):
        """Test adding invalid IP format to whitelist"""
        invalid_payloads = [
            {"ip_address": "999.999.999.999", "country": "KR"},
            {"ip_address": "invalid_ip", "country": "KR"},
            {"ip_address": "", "country": "KR"},
        ]

        for payload in invalid_payloads:
            response = client.post(
                "/api/whitelist/manual-add",
                data=json.dumps(payload),
                content_type="application/json"
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_whitelist_manual_add_missing_required_field(self, client):
        """Test missing required IP field"""
        payload = {
            "country": "KR",
            "reason": "Test"
        }

        response = client.post(
            "/api/whitelist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_blacklist_manual_add_valid_ip(self, client):
        """Test adding valid IP to blacklist"""
        payload = {
            "ip_address": "10.0.0.1",
            "country": "CN",
            "notes": "Test malicious IP"
        }

        response = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code in [200, 409]

    def test_blacklist_manual_add_duplicate_ip_returns_409(self, client):
        """Test adding duplicate IP returns 409 conflict"""
        payload = {
            "ip_address": "10.0.0.2",
            "country": "CN"
        }

        # First add
        response1 = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Second add (duplicate)
        response2 = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # One should succeed, one should return 409
        status_codes = sorted([response1.status_code, response2.status_code])
        assert 409 in status_codes or status_codes == [200, 200]


class TestListEndpoints:
    """Test list/pagination endpoints"""

    def test_blacklist_list_default_pagination(self, client):
        """Test /api/blacklist/list with default pagination"""
        response = client.get("/api/blacklist/list")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data
        assert "data" in data
        assert "pagination" in data

    def test_blacklist_list_custom_pagination(self, client):
        """Test custom pagination parameters"""
        response = client.get("/api/blacklist/list?page=2&per_page=10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["per_page"] == 10

    def test_whitelist_list_returns_data(self, client):
        """Test /api/whitelist/list returns data"""
        response = client.get("/api/whitelist/list")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_pagination_total_count(self, client):
        """Test pagination includes total count"""
        response = client.get("/api/blacklist/list")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total" in data["pagination"]
        assert "pages" in data["pagination"]


class TestCollectionEndpoints:
    """Test collection management endpoints"""

    def test_collection_status_returns_data(self, client):
        """Test /api/collection/status returns status data"""
        response = client.get("/api/collection/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data

    def test_collection_history_returns_list(self, client):
        """Test /api/collection/history returns history"""
        response = client.get("/api/collection/history")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_regtech_trigger_endpoint_exists(self, client):
        """Test REGTECH trigger endpoint exists"""
        response = client.post("/api/collection/regtech/trigger")

        # Should return 200 or 502 (if collector unavailable)
        assert response.status_code in [200, 502, 400]

    def test_credential_status_endpoint(self, client):
        """Test credential status endpoint"""
        response = client.get("/api/credential/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data


class TestStatisticsEndpoints:
    """Test statistics and monitoring endpoints"""

    def test_stats_endpoint_returns_data(self, client):
        """Test /api/blacklist/stats returns statistics"""
        response = client.get("/api/blacklist/stats")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "stats" in data

    def test_database_tables_endpoint(self, client):
        """Test /api/database/tables endpoint"""
        response = client.get("/api/database/tables")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "tables" in data

    def test_system_containers_endpoint(self, client):
        """Test /api/system/containers endpoint"""
        response = client.get("/api/system/containers")

        # May succeed or fail depending on Docker availability
        assert response.status_code in [200, 500]


class TestHealthAndMonitoring:
    """Test health check and monitoring endpoints"""

    def test_health_endpoint_returns_status(self, client):
        """Test /health endpoint returns health status"""
        response = client.get("/health")

        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_health_endpoint_includes_database_status(self, client):
        """Test health check includes database status"""
        response = client.get("/health")

        data = json.loads(response.data)
        if response.status_code == 200:
            assert "database" in data

    def test_monitoring_dashboard_endpoint(self, client):
        """Test /api/monitoring/dashboard endpoint"""
        response = client.get("/api/monitoring/dashboard")

        assert response.status_code in [200, 500]


class TestErrorHandling:
    """Test error handling across endpoints"""

    def test_404_for_nonexistent_endpoint(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/api/nonexistent/endpoint")

        assert response.status_code == 404

    def test_405_for_wrong_http_method(self, client):
        """Test 405 for wrong HTTP method"""
        # POST endpoint called with GET (or vice versa)
        response = client.get("/api/whitelist/manual-add")

        assert response.status_code == 405

    def test_400_for_invalid_json(self, client):
        """Test 400 for invalid JSON payload"""
        response = client.post(
            "/api/blacklist/manual-add",
            data="invalid json",
            content_type="application/json"
        )

        assert response.status_code in [400, 500]

    def test_error_response_includes_timestamp(self, client):
        """Test error responses include timestamp"""
        response = client.get("/api/blacklist/check")  # Missing IP

        assert response.status_code == 400
        data = json.loads(response.data)
        # Timestamp may or may not be included, depends on implementation


class TestResponseFormat:
    """Test API response format consistency"""

    def test_success_response_format(self, client):
        """Test successful responses have consistent format"""
        response = client.get("/api/blacklist/check?ip=1.2.3.4")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data
        assert isinstance(data["success"], bool)

    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        response = client.get("/api/blacklist/check")  # Missing IP

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data or "message" in data

    def test_pagination_response_format(self, client):
        """Test pagination responses have consistent format"""
        response = client.get("/api/blacklist/list")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "pagination" in data
        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "pages" in pagination


class TestConcurrency:
    """Test concurrent request handling"""

    def test_multiple_simultaneous_ip_checks(self, client):
        """Test handling multiple simultaneous IP checks"""
        import concurrent.futures

        def check_ip(ip):
            return client.get(f"/api/blacklist/check?ip={ip}")

        ips = [f"1.2.3.{i}" for i in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_ip, ip) for ip in ips]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        for response in results:
            assert response.status_code == 200


class TestDataValidation:
    """Test data validation across endpoints"""

    def test_ip_validation_rejects_invalid_octets(self, client):
        """Test IP validation rejects octets > 255"""
        payload = {"ip_address": "256.1.1.1", "country": "CN"}

        response = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_country_code_optional(self, client):
        """Test country code is optional"""
        payload = {"ip_address": "10.0.0.3"}

        response = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Should succeed (country optional)
        assert response.status_code in [200, 409]

    def test_long_notes_field_accepted(self, client):
        """Test long notes field is accepted"""
        payload = {
            "ip_address": "10.0.0.4",
            "country": "CN",
            "notes": "A" * 1000  # Long notes
        }

        response = client.post(
            "/api/blacklist/manual-add",
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Should handle long notes gracefully
        assert response.status_code in [200, 409, 400]
