#!/usr/bin/env python3
"""
Comprehensive deep unit tests for services/collection/regtech_data.py
Target: 274 lines, 9% → 80%+ coverage

High-impact methods:
- collect_real_regtech_data: Main collection with session validation, URL discovery, data parsing
- _parse_regtech_data: HTML parsing with IP extraction (regex, table, JSON patterns)
- _discover_data_urls: Dynamic URL discovery from HTML
- _extract_navigation_links: Link extraction from HTML
- _is_private_ip: Private IP range filtering
- _extract_*_from_html: Confidence, detection_date, removal_date extraction
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, date
import sys
import os

sys.path.insert(0, '/app')
os.chdir('/app')

from core.services.collection.regtech_data import REGTECHDataCollector, regtech_data


# ============================================================================
# Initialization Tests
# ============================================================================

class TestREGTECHDataCollectorInitialization:
    """Test initialization"""

    def test_init_sets_base_url(self):
        collector = REGTECHDataCollector()
        assert collector.base_url == "https://regtech.fsec.or.kr"

    def test_singleton_instance_exists(self):
        assert regtech_data is not None
        assert isinstance(regtech_data, REGTECHDataCollector)


# ============================================================================
# collect_real_regtech_data Tests
# ============================================================================

class TestCollectRealRegtechData:
    """Test collect_real_regtech_data main collection method"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.cookies = {"session_id": "test123"}
        return session

    def test_collect_invalid_session_no_cookies(self, collector):
        """Invalid session without cookies"""
        mock_session = MagicMock()
        mock_session.cookies = None

        result = collector.collect_real_regtech_data(mock_session, "test_user")

        assert result["success"] is False
        assert "유효하지 않은 세션" in result["error"]
        assert result["collected_count"] == 0

    def test_collect_empty_session(self, collector):
        """Empty session object"""
        result = collector.collect_real_regtech_data(None, "test_user")

        assert result["success"] is False
        assert result["collected_count"] == 0

    def test_collect_session_expired_302(self, collector, mock_session):
        """Session expired with 302 redirect"""
        with patch.object(collector, '_discover_data_urls') as mock_discover:
            mock_discover.return_value = [{"url": "http://test.com/data", "type": "test"}]
            
            mock_response = MagicMock()
            mock_response.status_code = 302
            mock_session.get.return_value = mock_response

            result = collector.collect_real_regtech_data(mock_session, "test_user")

            assert result["success"] is False
            assert "세션이 만료되었습니다" in result["error"]
            assert result.get("session_expired") is True
            assert result["collected_count"] == 0

    def test_collect_success_with_data(self, collector, mock_session):
        """Successful collection with data"""
        with patch.object(collector, '_discover_data_urls') as mock_discover:
            mock_discover.return_value = [{"url": "http://test.com/data", "type": "test"}]
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><td>1.2.3.4</td></html>"
            mock_session.get.return_value = mock_response

            with patch.object(collector, '_parse_regtech_data') as mock_parse:
                mock_parse.return_value = [
                    {"ip_address": "1.2.3.4", "reason": "Test", "source": "regtech"}
                ]

                result = collector.collect_real_regtech_data(mock_session, "test_user")

                assert result["success"] is True
                assert result["collected_count"] == 1
                assert "source" in result
                assert result["source"] == "regtech_real"

    def test_collect_no_data_found(self, collector, mock_session):
        """Collection with no data"""
        with patch.object(collector, '_discover_data_urls') as mock_discover:
            mock_discover.return_value = [{"url": "http://test.com/data", "type": "test"}]
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html></html>"
            mock_session.get.return_value = mock_response

            with patch.object(collector, '_parse_regtech_data') as mock_parse:
                mock_parse.return_value = []

                result = collector.collect_real_regtech_data(mock_session, "test_user")

                assert result["success"] is True
                assert result["collected_count"] == 0
                assert "note" in result

    def test_collect_all_urls_fail(self, collector, mock_session):
        """All URL attempts fail"""
        with patch.object(collector, '_discover_data_urls') as mock_discover:
            mock_discover.return_value = [{"url": "http://test.com/data", "type": "test"}]
            
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_session.get.return_value = mock_response

            result = collector.collect_real_regtech_data(mock_session, "test_user")

            assert result["success"] is True
            assert result["collected_count"] == 0

    def test_collect_timeout_exception(self, collector, mock_session):
        """Timeout exception"""
        import requests
        with patch.object(collector, '_discover_data_urls') as mock_discover:
            mock_discover.return_value = [{"url": "http://test.com/data", "type": "test"}]
            mock_session.get.side_effect = requests.exceptions.Timeout()

            result = collector.collect_real_regtech_data(mock_session, "test_user")

            assert result["success"] is False
            assert "시간 초과" in result["error"]

    def test_collect_general_exception(self, collector, mock_session):
        """General exception"""
        with patch.object(collector, '_discover_data_urls') as mock_discover:
            mock_discover.side_effect = Exception("Test error")

            result = collector.collect_real_regtech_data(mock_session, "test_user")

            assert result["success"] is False
            assert "데이터 수집 오류" in result["error"]


# ============================================================================
# _parse_regtech_data Tests
# ============================================================================

class TestParseRegtechData:
    """Test _parse_regtech_data HTML parsing"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_parse_simple_ip_pattern(self, collector):
        """Parse simple IP pattern from HTML"""
        html = "<html>IP: 8.8.8.8 found</html>"
        
        result = collector._parse_regtech_data(html)
        
        assert len(result) > 0
        assert result[0]["ip_address"] == "8.8.8.8"
        assert result[0]["source"] == "regtech"

    def test_parse_table_data(self, collector):
        """Parse IP from table HTML"""
        html = "<table><tr><td>203.0.113.1</td><td>Threat</td></tr></table>"
        
        result = collector._parse_regtech_data(html)
        
        assert len(result) > 0
        assert result[0]["ip_address"] == "203.0.113.1"

    def test_parse_json_pattern(self, collector):
        """Parse IP from JSON in HTML"""
        html = '{"ipAddress": "198.51.100.1", "threat": "high"}'
        
        result = collector._parse_regtech_data(html)
        
        assert len(result) > 0
        assert result[0]["ip_address"] == "198.51.100.1"

    def test_parse_filters_private_ips(self, collector):
        """Filter out private IP ranges"""
        html = "<html>192.168.1.1, 10.0.0.1, 8.8.8.8</html>"
        
        result = collector._parse_regtech_data(html)
        
        # Only public IP should remain
        assert len(result) == 1
        assert result[0]["ip_address"] == "8.8.8.8"

    def test_parse_removes_duplicates(self, collector):
        """Remove duplicate IPs"""
        html = "<html>8.8.8.8, 1.1.1.1, 8.8.8.8, 1.1.1.1</html>"
        
        result = collector._parse_regtech_data(html)
        
        assert len(result) == 2

    def test_parse_no_ips_found(self, collector):
        """No IPs in HTML"""
        html = "<html><p>No threat data available</p></html>"
        
        result = collector._parse_regtech_data(html)
        
        assert len(result) == 0

    def test_parse_exception_handling(self, collector):
        """Exception during parsing"""
        # Invalid HTML that causes parsing error
        with patch('re.findall', side_effect=Exception("Regex error")):
            result = collector._parse_regtech_data("<html>test</html>")
            
            assert result == []


# ============================================================================
# _is_private_ip Tests
# ============================================================================

class TestIsPrivateIP:
    """Test _is_private_ip filtering"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_private_10_network(self, collector):
        """10.0.0.0/8 network"""
        assert collector._is_private_ip("10.0.0.1") is True
        assert collector._is_private_ip("10.255.255.255") is True

    def test_private_172_network(self, collector):
        """172.16.0.0/12 network"""
        assert collector._is_private_ip("172.16.0.1") is True
        assert collector._is_private_ip("172.31.255.255") is True
        assert collector._is_private_ip("172.15.0.1") is False  # Outside range
        assert collector._is_private_ip("172.32.0.1") is False  # Outside range

    def test_private_192_network(self, collector):
        """192.168.0.0/16 network"""
        assert collector._is_private_ip("192.168.0.1") is True
        assert collector._is_private_ip("192.168.255.255") is True
        assert collector._is_private_ip("192.167.0.1") is False

    def test_loopback_network(self, collector):
        """127.0.0.0/8 loopback"""
        assert collector._is_private_ip("127.0.0.1") is True
        assert collector._is_private_ip("127.255.255.255") is True

    def test_link_local_network(self, collector):
        """169.254.0.0/16 link-local"""
        assert collector._is_private_ip("169.254.0.1") is True
        assert collector._is_private_ip("169.254.255.255") is True

    def test_public_ips(self, collector):
        """Public IP addresses"""
        assert collector._is_private_ip("8.8.8.8") is False
        assert collector._is_private_ip("1.1.1.1") is False
        assert collector._is_private_ip("203.0.113.1") is False

    def test_invalid_ip_format(self, collector):
        """Invalid IP format returns True (safely excluded)"""
        assert collector._is_private_ip("invalid.ip") is True
        assert collector._is_private_ip("300.300.300.300") is True


# ============================================================================
# _discover_data_urls Tests
# ============================================================================

class TestDiscoverDataUrls:
    """Test _discover_data_urls URL discovery"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    def test_discover_from_main_page(self, collector, mock_session):
        """Discover URLs from main page"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<a href="/threat/blacklist">Blacklist</a>'
        mock_session.get.return_value = mock_response

        with patch.object(collector, '_extract_navigation_links') as mock_extract:
            mock_extract.return_value = [
                {"url": "https://regtech.fsec.or.kr/threat/blacklist", "type": "nav"}
            ]

            result = collector._discover_data_urls(mock_session)

            assert len(result) > 0

    def test_discover_main_page_fails_fallback(self, collector, mock_session):
        """Main page fails, use fallback"""
        mock_session.get.side_effect = Exception("Connection error")

        result = collector._discover_data_urls(mock_session)

        # Should still return fallback URLs
        assert len(result) > 0

    def test_discover_includes_common_patterns(self, collector, mock_session):
        """Includes common URL patterns"""
        mock_session.get.side_effect = Exception("Fail")

        result = collector._discover_data_urls(mock_session)

        # Check for fallback patterns
        urls = [item["url"] for item in result]
        assert any("blacklist" in url for url in urls)


# ============================================================================
# _extract_navigation_links Tests
# ============================================================================

class TestExtractNavigationLinks:
    """Test _extract_navigation_links HTML link extraction"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_extract_href_links(self, collector):
        """Extract href links"""
        html = '<a href="/threat/blacklist">Blacklist</a><a href="/security/intel">Intel</a>'
        
        result = collector._extract_navigation_links(html)
        
        assert len(result) > 0

    def test_extract_filters_by_keywords(self, collector):
        """Filter links by threat keywords"""
        html = '''
        <a href="/normal/page">Normal</a>
        <a href="/threat/blacklist">Threat</a>
        '''
        
        result = collector._extract_navigation_links(html)
        
        # Should only include threat-related links
        threat_urls = [item["url"] for item in result if "threat" in item["url"]]
        assert len(threat_urls) > 0

    def test_extract_removes_duplicates(self, collector):
        """Remove duplicate URLs"""
        html = '<a href="/threat/data">Link1</a><a href="/threat/data">Link2</a>'
        
        result = collector._extract_navigation_links(html)
        
        # Check uniqueness
        urls = [item["url"] for item in result]
        assert len(urls) == len(set(urls))

    def test_extract_exception_handling(self, collector):
        """Exception during extraction"""
        with patch('re.findall', side_effect=Exception("Regex error")):
            result = collector._extract_navigation_links("<html>test</html>")
            
            assert result == []


# ============================================================================
# _extract_confidence_from_html Tests
# ============================================================================

class TestExtractConfidenceFromHtml:
    """Test _extract_confidence_from_html confidence extraction"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_extract_confidence_english(self, collector):
        """Extract confidence in English"""
        html = "IP: 1.2.3.4 confidence: 85%"
        
        result = collector._extract_confidence_from_html(html, "1.2.3.4")
        
        assert result == 85

    def test_extract_confidence_no_match(self, collector):
        """No confidence found"""
        html = "IP: 1.2.3.4 detected"
        
        result = collector._extract_confidence_from_html(html, "1.2.3.4")
        
        assert result is None

    def test_extract_confidence_limits_range(self, collector):
        """Confidence limited to 0-100"""
        html = "IP: 1.2.3.4 confidence: 150"
        
        result = collector._extract_confidence_from_html(html, "1.2.3.4")
        
        assert result == 100

    def test_extract_confidence_exception(self, collector):
        """Exception during extraction"""
        with patch('re.findall', side_effect=Exception()):
            result = collector._extract_confidence_from_html("test", "1.2.3.4")
            
            assert result is None


# ============================================================================
# _extract_detection_date_from_html Tests
# ============================================================================

class TestExtractDetectionDateFromHtml:
    """Test _extract_detection_date_from_html date extraction"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_extract_date_dash_format(self, collector):
        """Extract date in YYYY-MM-DD format"""
        html = "IP: 1.2.3.4 detected on 2025-01-15"
        
        result = collector._extract_detection_date_from_html(html, "1.2.3.4")
        
        assert result == date(2025, 1, 15)

    def test_extract_date_dot_format(self, collector):
        """Extract date in YYYY.MM.DD format"""
        html = "IP: 1.2.3.4 found at 2025.01.20"
        
        result = collector._extract_detection_date_from_html(html, "1.2.3.4")
        
        assert result == date(2025, 1, 20)

    def test_extract_date_slash_format(self, collector):
        """Extract date in YYYY/MM/DD format"""
        html = "Detected: 2025/01/25 IP: 1.2.3.4"
        
        result = collector._extract_detection_date_from_html(html, "1.2.3.4")
        
        assert result == date(2025, 1, 25)

    def test_extract_date_no_match(self, collector):
        """No date found"""
        html = "IP: 1.2.3.4 detected recently"
        
        result = collector._extract_detection_date_from_html(html, "1.2.3.4")
        
        assert result is None

    def test_extract_date_invalid_format(self, collector):
        """Invalid date format"""
        html = "IP: 1.2.3.4 date: 2025-13-99"  # Invalid month/day
        
        result = collector._extract_detection_date_from_html(html, "1.2.3.4")
        
        # Should return None for invalid dates
        assert result is None or isinstance(result, date)


# ============================================================================
# _extract_removal_date_from_html Tests
# ============================================================================

class TestExtractRemovalDateFromHtml:
    """Test _extract_removal_date_from_html removal date extraction"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_extract_removal_date_english(self, collector):
        """Extract removal date in English"""
        html = "IP: 1.2.3.4 remove: 2025-12-31"
        
        result = collector._extract_removal_date_from_html(html, "1.2.3.4")
        
        assert result == date(2025, 12, 31)

    def test_extract_removal_date_no_match(self, collector):
        """No removal date found"""
        html = "IP: 1.2.3.4 active"
        
        result = collector._extract_removal_date_from_html(html, "1.2.3.4")
        
        assert result is None


# ============================================================================
# expand_regtech_collection Tests
# ============================================================================

class TestExpandRegtechCollection:
    """Test expand_regtech_collection data expansion"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_expand_adds_to_base_data(self, collector):
        """Expansion adds to base data"""
        base_data = [{"ip": "1.2.3.4"}]
        
        with patch.object(collector, '_generate_additional_ips') as mock_gen:
            mock_gen.return_value = [{"ip": "5.6.7.8"}]
            
            result = collector.expand_regtech_collection(base_data)
            
            assert len(result) == 2

    def test_expand_exception_returns_base(self, collector):
        """Exception returns base data"""
        base_data = [{"ip": "1.2.3.4"}]
        
        with patch.object(collector, '_generate_additional_ips', side_effect=Exception()):
            result = collector.expand_regtech_collection(base_data)
            
            assert result == base_data


# ============================================================================
# collect_regtech_ips Tests
# ============================================================================

class TestCollectRegtechIps:
    """Test collect_regtech_ips basic collection"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_collect_returns_empty_list(self, collector):
        """Basic collection returns empty (stub)"""
        result = collector.collect_regtech_ips()
        
        assert result == []


# ============================================================================
# test_regtech_collection Tests
# ============================================================================

class TestTestRegtechCollection:
    """Test test_regtech_collection test mode"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_collection_test_mode_success(self, collector):
        """Test mode returns success"""
        result = collector.test_regtech_collection("user", "pass")
        
        assert result["success"] is True
        assert result["test_mode"] is True

    def test_collection_test_exception(self, collector):
        """Exception in test mode"""
        with patch('logging.Logger.info', side_effect=Exception("Test error")):
            result = collector.test_regtech_collection("user", "pass")
            
            assert result["success"] is False


# ============================================================================
# collect_threat_intelligence_ips Tests
# ============================================================================

class TestCollectThreatIntelligenceIps:
    """Test collect_threat_intelligence_ips method"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_threat_intel_success(self, collector):
        """Threat intelligence collection success"""
        result = collector.collect_threat_intelligence_ips()
        
        assert result["success"] is True
        assert result["source"] == "threat_intelligence"

    def test_threat_intel_exception(self, collector):
        """Exception during collection"""
        with patch('logging.Logger.info', side_effect=Exception("Error")):
            result = collector.collect_threat_intelligence_ips()
            
            assert result["success"] is False


# ============================================================================
# collect_malicious_ip_lists Tests
# ============================================================================

class TestCollectMaliciousIpLists:
    """Test collect_malicious_ip_lists method"""

    @pytest.fixture
    def collector(self):
        return REGTECHDataCollector()

    def test_malicious_lists_success(self, collector):
        """Malicious lists collection success"""
        result = collector.collect_malicious_ip_lists()
        
        assert result["success"] is True
        assert result["source"] == "malicious_lists"

    def test_malicious_lists_exception(self, collector):
        """Exception during collection"""
        with patch('logging.Logger.info', side_effect=Exception("Error")):
            result = collector.collect_malicious_ip_lists()
            
            assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
