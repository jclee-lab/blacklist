#!/usr/bin/env python3
"""
REGTECH Threat IP Collector for On-Premise Deployment
Korean Financial Security Institute (금융보안원) IP Blacklist Collector
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings for testing (remove in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class REGTECHCollector:
    """REGTECH 금융보안원 요주의 IP 수집기"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "https://regtech.fsec.or.kr"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        self.logged_in = False

    def login(self) -> bool:
        """REGTECH 시스템 로그인"""
        try:
            # 1. Get login page for session initialization
            logger.info("Accessing REGTECH login page...")
            login_page = self.session.get(
                f"{self.base_url}/login/loginForm",
                verify=False,
                timeout=30
            )

            logger.info(f"Login page status: {login_page.status_code}")
            if login_page.status_code != 200:
                logger.error(f"Failed to access login page: {login_page.status_code}")
                # Try alternative login page
                login_page = self.session.get(f"{self.base_url}/login", verify=False, timeout=30)
                if login_page.status_code != 200:
                    return False

            # Parse login form for any hidden fields
            soup = BeautifulSoup(login_page.text, 'html.parser')
            form_data = {}

            # Extract all hidden input fields
            for hidden in soup.find_all('input', {'type': 'hidden'}):
                if hidden.get('name') and hidden.get('value'):
                    form_data[hidden['name']] = hidden['value']

            # Add login credentials
            form_data.update({
                'username': self.username,
                'password': self.password,
                'id': self.username,
                'pwd': self.password,
                'user_id': self.username,
                'user_pw': self.password
            })

            # 2. Try multiple login endpoints
            login_endpoints = [
                '/login/addLogin',
                '/login/login.do',
                '/login/loginProcess',
                '/login/j_security_check'
            ]

            for endpoint in login_endpoints:
                logger.info(f"Attempting login with endpoint: {endpoint}")

                login_response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    data=form_data,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Referer': f"{self.base_url}/login/loginForm",
                        'Origin': self.base_url,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    verify=False,
                    allow_redirects=False,
                    timeout=30
                )

                logger.info(f"Login response status: {login_response.status_code}")

                # Check for successful login
                if login_response.status_code in [200, 302, 303]:
                    # Check if we got a session cookie
                    logger.info(f"Cookies after login: {list(self.session.cookies.keys())}")
                    if 'JSESSIONID' in self.session.cookies or 'SESSION' in self.session.cookies or 'session' in self.session.cookies:
                        logger.info(f"✅ Login successful with endpoint: {endpoint}")
                        self.logged_in = True
                        return True

                    # Check response content for success indicators
                    if login_response.text:
                        response_json = None
                        try:
                            response_json = login_response.json()
                        except:
                            pass

                        if response_json:
                            if response_json.get('success') or response_json.get('result') == 'success':
                                logger.info(f"Login successful (JSON) with endpoint: {endpoint}")
                                self.logged_in = True
                                return True

            logger.error("All login attempts failed")
            return False

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def collect_blacklist_ips(self) -> List[Dict]:
        """요주의 IP 수집"""
        if not self.logged_in:
            logger.info("Not logged in, attempting login...")
            if not self.login():
                logger.error("❌ Login failed, cannot collect IPs")
                return []

        logger.info("✅ Login successful, starting IP collection...")
        collected_ips = []

        # Try multiple possible endpoints
        endpoints = [
            ('/fcti/blacklist/list', 'POST'),
            ('/fcti/blacklist/ipList', 'POST'),
            ('/fcti/securityAdvisory/advisoryList', 'POST'),
            ('/fcti/threat/blacklist', 'GET'),
            ('/api/blacklist/ips', 'GET'),
            ('/data/blacklist.json', 'GET'),
            ('/api/v1/blacklist', 'GET'),
            ('/threat/ip/list', 'POST')
        ]

        for endpoint, method in endpoints:
            try:
                logger.info(f"Trying endpoint: {endpoint}")

                if method == 'POST':
                    # POST request with various parameter formats
                    param_sets = [
                        {
                            'page': '1',
                            'rows': '1000',
                            'sidx': 'reg_dt',
                            'sord': 'desc'
                        },
                        {
                            'pageNo': '1',
                            'pageSize': '1000',
                            'searchType': 'all'
                        },
                        {
                            'start': '0',
                            'limit': '1000',
                            'sort': 'regDate',
                            'dir': 'DESC'
                        }
                    ]

                    for params in param_sets:
                        response = self.session.post(
                            f"{self.base_url}{endpoint}",
                            data=params,
                            headers={
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Referer': f"{self.base_url}/fcti/main"
                            },
                            verify=False
                        )

                        if response.status_code == 200:
                            data = self._parse_response(response)
                            if data:
                                collected_ips.extend(data)
                                logger.info(f"Collected {len(data)} IPs from {endpoint}")
                                break
                else:
                    # GET request
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        verify=False
                    )

                    if response.status_code == 200:
                        data = self._parse_response(response)
                        if data:
                            collected_ips.extend(data)
                            logger.info(f"Collected {len(data)} IPs from {endpoint}")

            except Exception as e:
                logger.error(f"Error with endpoint {endpoint}: {str(e)}")
                continue

        # Remove duplicates
        unique_ips = {}
        for ip_data in collected_ips:
            ip_addr = ip_data.get('ip_address')
            if ip_addr and ip_addr not in unique_ips:
                unique_ips[ip_addr] = ip_data

        return list(unique_ips.values())

    def _parse_response(self, response) -> List[Dict]:
        """Parse response data"""
        collected = []

        try:
            # Try JSON parsing
            data = response.json()

            # Check various JSON structures
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get('data') or data.get('rows') or data.get('list') or data.get('items') or []
            else:
                items = []

            for item in items:
                # Extract IP address from various possible fields
                ip_address = (
                    item.get('ipAddr') or
                    item.get('ip_address') or
                    item.get('ip') or
                    item.get('IP') or
                    item.get('target_ip') or
                    item.get('malicious_ip')
                )

                if ip_address and self._is_valid_ip(ip_address):
                    collected.append({
                        'ip_address': ip_address,
                        'reason': (
                            item.get('blockReason') or
                            item.get('reason') or
                            item.get('threat_type') or
                            item.get('description') or
                            'REGTECH 요주의 IP'
                        ),
                        'country': item.get('country', 'KR'),
                        'detection_date': (
                            item.get('regDt') or
                            item.get('reg_date') or
                            item.get('detection_date') or
                            datetime.now().isoformat()
                        ),
                        'source': 'regtech'
                    })

        except json.JSONDecodeError:
            # Try HTML parsing if JSON fails
            logger.info("JSON parsing failed, trying HTML extraction")

            # Extract IPs from HTML
            ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
            found_ips = ip_pattern.findall(response.text)

            for ip in set(found_ips):  # Use set to remove duplicates
                if self._is_valid_ip(ip) and not self._is_private_ip(ip):
                    collected.append({
                        'ip_address': ip,
                        'reason': 'REGTECH 요주의 IP (HTML 추출)',
                        'country': 'KR',
                        'detection_date': datetime.now().isoformat(),
                        'source': 'regtech'
                    })

        return collected

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private (RFC 1918)"""
        try:
            parts = [int(p) for p in ip.split('.')]

            # 10.0.0.0/8
            if parts[0] == 10:
                return True

            # 172.16.0.0/12
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True

            # 192.168.0.0/16
            if parts[0] == 192 and parts[1] == 168:
                return True

            # 127.0.0.0/8
            if parts[0] == 127:
                return True

            return False
        except:
            return False


def main():
    """Main execution"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get credentials from environment
    username = os.getenv('REGTECH_ID', 'nextrade')
    password = os.getenv('REGTECH_PW', '')

    if not password:
        logger.error("REGTECH_PW environment variable not set")
        return

    # Create collector instance
    collector = REGTECHCollector(username, password)

    # Collect blacklist IPs
    logger.info("Starting REGTECH IP collection...")
    ips = collector.collect_blacklist_ips()

    if ips:
        logger.info(f"Successfully collected {len(ips)} unique IPs")

        # Save to file
        output_file = f"regtech_ips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ips, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved to {output_file}")

        # Print summary
        print("\n=== Collection Summary ===")
        print(f"Total IPs collected: {len(ips)}")
        print("\nSample IPs:")
        for ip in ips[:5]:
            print(f"  - {ip['ip_address']}: {ip['reason']}")
    else:
        logger.warning("No IPs collected")


if __name__ == "__main__":
    main()