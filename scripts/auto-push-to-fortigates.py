#!/usr/bin/env python3
"""
FortiGate Auto-Push Script (Direct API)

Purpose:
  - Blacklist API에서 IP 가져오기
  - 모든 FortiGate에 직접 REST API 호출
  - FortiManager 불필요

Usage:
  python3 auto-push-to-fortigates.py

Environment:
  FORTIGATE_HOSTS - Comma-separated IPs (192.168.1.1,192.168.1.2)
  FORTIGATE_TOKEN - FortiGate API Token
  BLACKLIST_API   - Blacklist API URL
"""

import os
import sys
import json
import time
import requests
from typing import List, Dict

# Configuration
FORTIGATE_HOSTS = os.getenv("FORTIGATE_HOSTS", "").split(",")
FORTIGATE_TOKEN = os.getenv("FORTIGATE_TOKEN", "")
BLACKLIST_API = os.getenv("BLACKLIST_API", "https://blacklist.nxtd.co.kr/api/fortinet/active-ips")
VDOM = "root"

# Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

def log(msg: str):
    print(f"{GREEN}[{time.strftime('%Y-%m-%d %H:%M:%S')}]{NC} {msg}")

def error(msg: str):
    print(f"{RED}[ERROR]{NC} {msg}", file=sys.stderr)

def warn(msg: str):
    print(f"{YELLOW}[WARN]{NC} {msg}")

def fetch_blacklist_ips() -> List[str]:
    """Fetch IP list from Blacklist API"""
    try:
        log(f"Fetching IPs from {BLACKLIST_API}")
        response = requests.get(BLACKLIST_API, timeout=30)
        response.raise_for_status()

        ips = [line.strip() for line in response.text.split("\n") if line.strip()]
        log(f"✅ Fetched {len(ips)} IPs")
        return ips
    except Exception as e:
        error(f"Failed to fetch IPs: {e}")
        sys.exit(1)

def push_to_fortigate(host: str, ips: List[str]) -> bool:
    """Push IP list to single FortiGate"""
    try:
        log(f"Pushing to FortiGate: {host}")

        # Create address group
        url = f"https://{host}/api/v2/cmdb/firewall/addrgrp?vdom={VDOM}"
        headers = {
            "Authorization": f"Bearer {FORTIGATE_TOKEN}",
            "Content-Type": "application/json"
        }

        # Delete old group (if exists)
        requests.delete(
            f"{url}/NXTD-Blacklist-Group",
            headers=headers,
            verify=False,
            timeout=10
        )

        # Create individual address objects (batch)
        members = []
        for ip in ips:
            name = f"NXTD-{ip.replace('.', '-')}"
            members.append(name)

            addr_url = f"https://{host}/api/v2/cmdb/firewall/address?vdom={VDOM}"
            payload = {
                "name": name,
                "type": "ipmask",
                "subnet": f"{ip} 255.255.255.255",
                "comment": f"NXTD Blacklist {time.strftime('%Y-%m-%d')}"
            }

            requests.post(addr_url, json=payload, headers=headers, verify=False, timeout=10)

        # Create address group
        group_payload = {
            "name": "NXTD-Blacklist-Group",
            "member": members,
            "comment": "NXTD Blacklist Auto-updated"
        }

        response = requests.post(url, json=group_payload, headers=headers, verify=False, timeout=30)
        response.raise_for_status()

        log(f"✅ Pushed to {host} ({len(ips)} IPs)")
        return True

    except Exception as e:
        error(f"Failed to push to {host}: {e}")
        return False

def main():
    """Main function"""
    # Validation
    if not FORTIGATE_HOSTS[0]:
        error("FORTIGATE_HOSTS environment variable is required")
        error("Example: export FORTIGATE_HOSTS='192.168.1.1,192.168.1.2'")
        sys.exit(1)

    if not FORTIGATE_TOKEN:
        error("FORTIGATE_TOKEN environment variable is required")
        error("Create token: System > Administrators > Create New > REST API Admin")
        sys.exit(1)

    log("Starting auto-push to FortiGates...")
    log(f"Targets: {', '.join(FORTIGATE_HOSTS)}")

    # Fetch IPs
    ips = fetch_blacklist_ips()

    # Push to all FortiGates
    success_count = 0
    for host in FORTIGATE_HOSTS:
        if push_to_fortigate(host.strip(), ips):
            success_count += 1

    # Summary
    log("")
    log("=" * 50)
    log(f"✅ Completed: {success_count}/{len(FORTIGATE_HOSTS)} FortiGates updated")
    log("=" * 50)

if __name__ == "__main__":
    # Disable SSL warnings (for self-signed certs)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    main()
