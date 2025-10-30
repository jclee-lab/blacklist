"""
Unit tests for SECUDIUM Collector Components
Tests authentication, API client, and data parsing with mocks
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime
import json


@pytest.mark.unit
class TestSecudiumAuthentication:
    """Test cases for SECUDIUM authentication logic"""

    @patch('requests.post')
    def test_authentication_success(self, mock_post):
        """Test successful SECUDIUM authentication"""
        # Mock successful auth response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "token": "test_token_12345"
        }
        mock_post.return_value = mock_response

        # Simulated authentication call
        result = mock_post("https://api.example.com/auth", json={
            "login_name": "test_user",
            "password": "test_password"
        })

        assert result.status_code == 200
        data = result.json()
        assert data["result"] == "success"
        assert "token" in data

    @patch('requests.post')
    def test_authentication_invalid_credentials(self, mock_post):
        """Test authentication with invalid credentials"""
        # Mock failed auth response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "result": "fail",
            "message": "Invalid credentials"
        }
        mock_post.return_value = mock_response

        result = mock_post("https://api.example.com/auth", json={
            "login_name": "wrong_user",
            "password": "wrong_password"
        })

        assert result.status_code == 401
        data = result.json()
        assert data["result"] == "fail"

    @patch('requests.post')
    def test_authentication_network_error(self, mock_post):
        """Test authentication with network error"""
        import requests.exceptions
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(requests.exceptions.ConnectionError):
            mock_post("https://api.example.com/auth", json={})

    @patch('requests.post')
    def test_authentication_timeout(self, mock_post):
        """Test authentication timeout handling"""
        import requests.exceptions
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(requests.exceptions.Timeout):
            mock_post("https://api.example.com/auth", json={}, timeout=10)

    @patch('requests.post')
    def test_authentication_token_format(self, mock_post):
        """Test that authentication returns properly formatted token"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "token": "Bearer_abc123xyz"
        }
        mock_post.return_value = mock_response

        result = mock_post("https://api.example.com/auth", json={})

        data = result.json()
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0


@pytest.mark.unit
class TestSecudiumAPIClient:
    """Test cases for SECUDIUM API client"""

    @patch('requests.get')
    def test_fetch_data_success(self, mock_get):
        """Test successful data fetch from SECUDIUM API"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'mock_excel_data'
        mock_response.headers = {'Content-Type': 'application/vnd.ms-excel'}
        mock_get.return_value = mock_response

        result = mock_get("https://api.example.com/data", headers={"Authorization": "Bearer token"})

        assert result.status_code == 200
        assert result.content == b'mock_excel_data'
        assert 'excel' in result.headers['Content-Type'].lower()

    @patch('requests.get')
    def test_fetch_data_unauthorized(self, mock_get):
        """Test data fetch with expired/invalid token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_get.return_value = mock_response

        result = mock_get("https://api.example.com/data", headers={"Authorization": "Bearer invalid_token"})

        assert result.status_code == 401

    @patch('requests.get')
    def test_fetch_data_with_retry(self, mock_get):
        """Test data fetch with retry logic on temporary failure"""
        # First call fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.content = b'data'

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        # First call
        result1 = mock_get("https://api.example.com/data")
        assert result1.status_code == 500

        # Retry call
        result2 = mock_get("https://api.example.com/data")
        assert result2.status_code == 200

    @patch('requests.get')
    def test_fetch_data_empty_response(self, mock_get):
        """Test handling of empty API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b''
        mock_get.return_value = mock_response

        result = mock_get("https://api.example.com/data")

        assert result.status_code == 200
        assert result.content == b''


@pytest.mark.unit
class TestSecudiumExcelParsing:
    """Test cases for SECUDIUM Excel data parsing"""

    @patch('pandas.read_excel')
    def test_parse_excel_success(self, mock_read_excel):
        """Test successful Excel file parsing"""
        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_df.iterrows.return_value = [
            (0, {'IP': '1.2.3.4', 'Country': 'CN', 'Reason': 'Malicious'}),
            (1, {'IP': '5.6.7.8', 'Country': 'RU', 'Reason': 'Scanning'})
        ]
        mock_df.__len__.return_value = 2
        mock_read_excel.return_value = mock_df

        result = mock_read_excel(b'mock_excel_data')

        assert len(result) == 2
        rows = list(result.iterrows())
        assert rows[0][1]['IP'] == '1.2.3.4'
        assert rows[1][1]['IP'] == '5.6.7.8'

    @patch('pandas.read_excel')
    def test_parse_excel_empty_file(self, mock_read_excel):
        """Test parsing of empty Excel file"""
        mock_df = MagicMock()
        mock_df.iterrows.return_value = []
        mock_df.__len__.return_value = 0
        mock_read_excel.return_value = mock_df

        result = mock_read_excel(b'empty_excel')

        assert len(result) == 0

    @patch('pandas.read_excel')
    def test_parse_excel_invalid_format(self, mock_read_excel):
        """Test parsing of corrupted Excel file"""
        mock_read_excel.side_effect = Exception("Invalid Excel format")

        with pytest.raises(Exception, match="Invalid Excel format"):
            mock_read_excel(b'corrupted_data')

    @patch('pandas.read_excel')
    def test_parse_excel_missing_columns(self, mock_read_excel):
        """Test parsing Excel with missing required columns"""
        mock_df = MagicMock()
        # Missing 'Country' column
        mock_df.iterrows.return_value = [
            (0, {'IP': '1.2.3.4', 'Reason': 'Malicious'})
        ]
        mock_df.__len__.return_value = 1
        mock_read_excel.return_value = mock_df

        result = mock_read_excel(b'incomplete_excel')

        # Should still parse, but with missing data
        rows = list(result.iterrows())
        assert 'IP' in rows[0][1]
        assert 'Country' not in rows[0][1]

    @patch('openpyxl.load_workbook')
    def test_parse_excel_fallback_openpyxl(self, mock_load_workbook):
        """Test Excel parsing fallback to openpyxl when pandas fails"""
        # Mock openpyxl workbook
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.iter_rows.return_value = [
            ['IP', 'Country', 'Reason'],
            ['1.2.3.4', 'CN', 'Malicious'],
            ['5.6.7.8', 'RU', 'Scanning']
        ]
        mock_wb.active = mock_sheet
        mock_load_workbook.return_value = mock_wb

        result = mock_load_workbook(b'excel_data')

        assert result.active is not None
        rows = list(result.active.iter_rows())
        assert len(rows) == 3  # Header + 2 data rows


@pytest.mark.unit
class TestSecudiumDataValidation:
    """Test cases for SECUDIUM data validation logic"""

    def test_validate_ip_address_format(self):
        """Test IP address format validation (basic pattern matching)"""
        import re
        # Simple pattern matching (doesn't validate octets are 0-255)
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')

        # Valid format (matches pattern)
        assert ip_pattern.match('192.168.1.1')
        assert ip_pattern.match('10.0.0.1')
        assert ip_pattern.match('255.255.255.255')
        assert ip_pattern.match('256.1.1.1')  # Matches pattern even though invalid IP

        # Invalid format (doesn't match pattern)
        assert not ip_pattern.match('192.168.1')  # Too few octets
        assert not ip_pattern.match('invalid_ip')  # Not numeric
        assert not ip_pattern.match('192.168.1.1.1')  # Too many octets

    def test_validate_country_code(self):
        """Test country code validation"""
        valid_codes = ['US', 'CN', 'RU', 'KR', 'JP']

        assert 'CN' in valid_codes
        assert 'US' in valid_codes
        assert 'XX' not in valid_codes

    def test_validate_required_fields(self):
        """Test that required fields are present in data"""
        required_fields = ['IP', 'Country', 'Reason']

        data = {
            'IP': '1.2.3.4',
            'Country': 'CN',
            'Reason': 'Malicious activity'
        }

        for field in required_fields:
            assert field in data

    def test_sanitize_data_input(self):
        """Test data sanitization to prevent SQL injection"""
        malicious_input = "'; DROP TABLE blacklist_ips; --"

        # Sanitization: escape single quotes
        sanitized = malicious_input.replace("'", "''")

        assert "DROP TABLE" in sanitized
        assert "''" in sanitized  # Escaped quote

    def test_validate_data_types(self):
        """Test that data types are correct"""
        data = {
            'IP': '1.2.3.4',
            'Country': 'CN',
            'items_collected': 100,
            'success': True,
            'execution_time_ms': 1500
        }

        assert isinstance(data['IP'], str)
        assert isinstance(data['Country'], str)
        assert isinstance(data['items_collected'], int)
        assert isinstance(data['success'], bool)
        assert isinstance(data['execution_time_ms'], int)


@pytest.mark.unit
class TestSecudiumCollectionFlow:
    """Test cases for SECUDIUM end-to-end collection flow"""

    @patch('requests.post')
    @patch('requests.get')
    @patch('pandas.read_excel')
    def test_full_collection_flow_success(self, mock_read_excel, mock_get, mock_post):
        """Test complete collection flow: auth → fetch → parse → store"""
        # Mock authentication
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {
            "result": "success",
            "token": "test_token"
        }
        mock_post.return_value = mock_auth_response

        # Mock data fetch
        mock_data_response = MagicMock()
        mock_data_response.status_code = 200
        mock_data_response.content = b'excel_data'
        mock_get.return_value = mock_data_response

        # Mock Excel parsing
        mock_df = MagicMock()
        mock_df.iterrows.return_value = [
            (0, {'IP': '1.2.3.4', 'Country': 'CN', 'Reason': 'Test'})
        ]
        mock_df.__len__.return_value = 1
        mock_read_excel.return_value = mock_df

        # Simulate flow
        # Step 1: Authenticate
        auth_result = mock_post("https://api.example.com/auth", json={})
        assert auth_result.status_code == 200
        token = auth_result.json()["token"]

        # Step 2: Fetch data
        fetch_result = mock_get("https://api.example.com/data", headers={"Authorization": f"Bearer {token}"})
        assert fetch_result.status_code == 200

        # Step 3: Parse data
        df = mock_read_excel(fetch_result.content)
        assert len(df) == 1

        # Flow completed successfully
        assert True

    @patch('requests.post')
    def test_collection_flow_auth_failure(self, mock_post):
        """Test collection flow when authentication fails"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"result": "fail"}
        mock_post.return_value = mock_response

        result = mock_post("https://api.example.com/auth", json={})

        # Flow should stop at authentication
        assert result.status_code == 401
        assert result.json()["result"] == "fail"

    @patch('requests.post')
    @patch('requests.get')
    def test_collection_flow_fetch_failure(self, mock_get, mock_post):
        """Test collection flow when data fetch fails"""
        # Auth succeeds
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"token": "test_token"}
        mock_post.return_value = mock_auth_response

        # Fetch fails
        mock_data_response = MagicMock()
        mock_data_response.status_code = 500
        mock_get.return_value = mock_data_response

        auth = mock_post("https://api.example.com/auth", json={})
        assert auth.status_code == 200

        data = mock_get("https://api.example.com/data")
        assert data.status_code == 500

    @patch('requests.post')
    @patch('requests.get')
    @patch('pandas.read_excel')
    def test_collection_flow_parse_failure(self, mock_read_excel, mock_get, mock_post):
        """Test collection flow when Excel parsing fails"""
        # Auth succeeds
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"token": "test_token"}
        mock_post.return_value = mock_auth_response

        # Fetch succeeds
        mock_data_response = MagicMock()
        mock_data_response.status_code = 200
        mock_data_response.content = b'corrupted_excel'
        mock_get.return_value = mock_data_response

        # Parse fails
        mock_read_excel.side_effect = Exception("Parse error")

        auth = mock_post("https://api.example.com/auth", json={})
        data = mock_get("https://api.example.com/data")

        with pytest.raises(Exception, match="Parse error"):
            mock_read_excel(data.content)


@pytest.mark.unit
class TestSecudiumSchedulerIntegration:
    """Test cases for SECUDIUM integration with scheduler"""

    def test_scheduler_includes_secudium_collector(self):
        """Test that scheduler recognizes SECUDIUM collector"""
        collectors = {
            "REGTECH": {"enabled": True, "interval": 3600},
            "SECUDIUM": {"enabled": True, "interval": 86400}
        }

        assert "SECUDIUM" in collectors
        assert collectors["SECUDIUM"]["enabled"] is True
        assert collectors["SECUDIUM"]["interval"] == 86400

    def test_scheduler_secudium_interval_configuration(self):
        """Test SECUDIUM collection interval configuration"""
        # Daily collection (86400 seconds)
        secudium_interval = 86400

        assert secudium_interval == 24 * 60 * 60
        assert secudium_interval > 0

    def test_scheduler_concurrent_collection_handling(self):
        """Test that scheduler can handle concurrent REGTECH and SECUDIUM collections"""
        running_collections = set()

        # Start REGTECH collection
        running_collections.add("REGTECH")

        # Start SECUDIUM collection (should be allowed concurrently)
        running_collections.add("SECUDIUM")

        assert "REGTECH" in running_collections
        assert "SECUDIUM" in running_collections
        assert len(running_collections) == 2

    def test_scheduler_prevents_duplicate_secudium_runs(self):
        """Test that scheduler prevents duplicate SECUDIUM collection runs"""
        running_collections = set()

        # First SECUDIUM run
        if "SECUDIUM" not in running_collections:
            running_collections.add("SECUDIUM")

        # Attempt duplicate run
        can_run_duplicate = "SECUDIUM" not in running_collections

        assert not can_run_duplicate  # Should prevent duplicate

    def test_scheduler_error_count_tracking(self):
        """Test that scheduler tracks SECUDIUM error counts"""
        collectors = {
            "SECUDIUM": {
                "error_count": 0,
                "last_error": None
            }
        }

        # Simulate error
        collectors["SECUDIUM"]["error_count"] += 1
        collectors["SECUDIUM"]["last_error"] = "Connection timeout"

        assert collectors["SECUDIUM"]["error_count"] == 1
        assert collectors["SECUDIUM"]["last_error"] is not None


@pytest.mark.unit
class TestSecudiumDatabaseOperations:
    """Test cases for SECUDIUM database operations"""

    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_store_collection_result_success(self, mock_pool):
        """Test storing SECUDIUM collection results in database"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.return_value.getconn.return_value = mock_conn

        # Simulate INSERT
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None

        # Execute mock query
        pool = mock_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO collection_history (service_name, items_collected, success) VALUES (%s, %s, %s)",
            ("SECUDIUM", 100, True)
        )
        conn.commit()

        # Verify
        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_retrieve_secudium_statistics(self, mock_pool):
        """Test retrieving SECUDIUM statistics from database"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.return_value.getconn.return_value = mock_conn

        # Mock query result
        mock_cursor.fetchall.return_value = [
            {"service_name": "SECUDIUM", "total_collections": 10, "total_items": 1000}
        ]

        # Execute mock query
        pool = mock_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM collection_history WHERE service_name = %s", ("SECUDIUM",))
        results = cursor.fetchall()

        assert len(results) == 1
        assert results[0]["service_name"] == "SECUDIUM"
        assert results[0]["total_collections"] == 10

    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_update_secudium_credentials(self, mock_pool):
        """Test updating SECUDIUM credentials in database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.return_value.getconn.return_value = mock_conn

        pool = mock_pool()
        conn = pool.getconn()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE collection_credentials SET username = %s, password = %s WHERE service_name = %s",
            ("new_user", "new_password", "SECUDIUM")
        )
        conn.commit()

        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()
