"""
IP Validation Module for Collector ETL Pipeline
Validates and normalizes IP addresses before database insertion.
"""

import ipaddress
import re
from typing import Optional


IPV4_PATTERN = re.compile(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
CIDR_PATTERN = re.compile(
    r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(/(3[0-2]|[12]?[0-9]))?$"
)


def validate_ip(ip_str: str) -> bool:
    if not ip_str or not isinstance(ip_str, str):
        return False
    ip_str = ip_str.strip()
    return bool(IPV4_PATTERN.match(ip_str))


def validate_ip_or_cidr(ip_str: str) -> bool:
    if not ip_str or not isinstance(ip_str, str):
        return False
    ip_str = ip_str.strip()
    return bool(CIDR_PATTERN.match(ip_str))


def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str.split("/")[0])
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def is_public_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str.split("/")[0])
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        return False


def normalize_ip(ip_str: str) -> Optional[str]:
    if not ip_str:
        return None
    ip_str = ip_str.strip()
    if "/" in ip_str:
        try:
            network = ipaddress.ip_network(ip_str, strict=False)
            return str(network)
        except ValueError:
            return None
    try:
        return str(ipaddress.ip_address(ip_str))
    except ValueError:
        return None


def filter_valid_public_ips(ip_list: list[str]) -> tuple[list[str], list[str]]:
    valid_ips = []
    rejected_ips = []
    for ip in ip_list:
        normalized = normalize_ip(ip)
        if normalized and is_public_ip(normalized):
            valid_ips.append(normalized)
        else:
            rejected_ips.append(ip)
    return valid_ips, rejected_ips


def validate_country_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    code = code.strip().upper()
    if len(code) == 2 and code.isalpha():
        return code
    return None
