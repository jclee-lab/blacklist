"""
IP Management API Package - Modular IP whitelist/blacklist management.

Structure:
- repository.py: Raw SQL database operations
- handlers.py: Validation and response formatting
- routes.py: Thin route definitions (Blueprint)
"""

from .routes import ip_management_api_bp, ip_management_legacy_bp

__all__ = ["ip_management_api_bp", "ip_management_legacy_bp"]
