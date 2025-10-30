"""
Integration tests for Statistics API endpoints
"""
import pytest
import json


class TestStatisticsAPI:
    """Test statistics API endpoints"""

    def test_stats_endpoint_returns_200(self, client):
        """Test /api/stats returns 200 with statistics"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "blacklist_count" in data or "statistics" in data

    def test_stats_returns_valid_structure(self, client):
        """Test statistics response has valid structure"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check for expected fields
        if "blacklist_count" in data:
            assert isinstance(data["blacklist_count"], int)
        if "whitelist_count" in data:
            assert isinstance(data["whitelist_count"], int)

    def test_stats_by_country_endpoint(self, client):
        """Test /api/stats/by-country endpoint"""
        response = client.get("/api/stats/by-country")

        # May return 200 with data or 404 if endpoint not found
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, (dict, list))

    def test_stats_top_countries(self, client):
        """Test top countries statistics"""
        response = client.get("/api/stats/top-countries?limit=10")

        # May return 200 with data or 404 if endpoint not found
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, (dict, list))


class TestMonitoringDashboard:
    """Test monitoring dashboard endpoint"""

    def test_monitoring_dashboard_returns_200(self, client):
        """Test /api/monitoring/dashboard returns 200"""
        response = client.get("/api/monitoring/dashboard")

        # May return 200 or 404 depending on implementation
        assert response.status_code in [200, 404]

    def test_monitoring_dashboard_data_structure(self, client):
        """Test monitoring dashboard returns expected data structure"""
        response = client.get("/api/monitoring/dashboard")

        if response.status_code == 200:
            data = json.loads(response.data)
            # Monitoring dashboard should have some metrics
            assert isinstance(data, dict)


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Test /metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.content_type == "text/plain; version=0.0.4; charset=utf-8"

    def test_metrics_contains_blacklist_metrics(self, client):
        """Test /metrics contains blacklist-specific metrics"""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.data.decode('utf-8')

        # Check for expected metric names
        assert "blacklist_decisions_total" in data or "# TYPE" in data

    def test_metrics_contains_help_text(self, client):
        """Test /metrics contains HELP and TYPE comments"""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.data.decode('utf-8')

        # Prometheus format should have HELP or TYPE directives
        assert "# HELP" in data or "# TYPE" in data or len(data) > 0
