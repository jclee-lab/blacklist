"""
Integration tests for Collection API endpoints
"""
import pytest
import json


class TestCollectionAPI:
    """Test cases for Collection API endpoints"""

    def test_collection_status(self, client):
        """Test /api/collection/status endpoint"""
        response = client.get("/api/collection/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data

    def test_collection_history(self, client):
        """Test /api/collection/history endpoint"""
        response = client.get("/api/collection/history")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))

    def test_regtech_collection_trigger(self, client):
        """Test /api/collection/regtech/trigger endpoint"""
        response = client.post("/api/collection/regtech/trigger")

        # Should return 200 (triggered) or 202 (already running) or 503 (not configured)
        assert response.status_code in [200, 202, 503]
        data = json.loads(response.data)
        assert "status" in data
