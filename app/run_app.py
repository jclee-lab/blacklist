#!/usr/bin/env python3
"""
Independent container Flask application execution script
"""
import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Set up proper Python path for containerized environment
app_root = Path(__file__).parent  # /app (where this script is located)
src_root = app_root  # /app (since build context is src/)

# Add path to ensure module resolution works in container
sys.path.insert(0, str(app_root))  # For core.main import


def get_flask_app():
    """
    Import Flask application using app factory pattern with Phase 1.3 security
    """
    try:
        # Use app factory pattern from core.app (includes Phase 1.3 security)
        from core.app import create_app

        app = create_app()
        logger.info("✅ Flask app created via core.app factory (Phase 1.3 security enabled)")
        return app
    except ImportError as e1:
        logger.error(f"❌ core.app import failed: {e1}")

        # Fallback to old core.main if app factory not available
        try:
            from core.main import app
            logger.warning("⚠️ Using fallback core.main (no Phase 1.3 security)")
            return app
        except ImportError as e2:
            logger.error(f"❌ core.main import also failed: {e2}")
            logger.critical("🚨 Critical: Unable to import Flask application")
            sys.exit(1)


# Get Flask application instance
app = get_flask_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2542))
    app.run(host="0.0.0.0", port=port, debug=False)
