"""
Web UI Routes Package

Web interface routes for the blacklist platform.
"""

# Import web_bp from parent web_routes for sub-modules
from ..web_routes import web_bp

# Import api_routes to register its routes on web_bp
from . import api_routes  # noqa: F401

__all__ = ["web_bp"]
