"""
Pytest configuration and fixtures
⚠️ CRITICAL: All tests use MOCK data, NEVER real credentials
"""
import pytest
import os
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

# Import test configuration (safeguards)
from test_config import MOCK_CREDENTIALS, validate_test_credentials


@pytest.fixture(scope="session")
def test_db_config():
    """Database configuration for testing"""
    return {
        "host": os.getenv("POSTGRES_HOST", "blacklist-postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "blacklist_test"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }


@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing (session-scoped for performance)"""
    from core.main import create_app

    # Set testing environment variables to use Docker database
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["POSTGRES_DB"] = "blacklist"
    os.environ["POSTGRES_USER"] = "postgres"
    os.environ["POSTGRES_PASSWORD"] = "postgres"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

    yield app


@pytest.fixture(scope="function")
def client(app):
    """Flask test client (function-scoped for isolation)"""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Flask CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def mock_db_connection(mocker):
    """Mock database connection"""
    mock_conn = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    return mock_conn, mock_cursor


@pytest.fixture
def mock_regtech_credentials():
    """
    Mock REGTECH credentials (NEVER real ones!)
    ⚠️ These are FAKE credentials for testing only
    """
    creds = MOCK_CREDENTIALS["regtech"]
    # Validate they're not real
    validate_test_credentials(creds["username"], creds["password"], creds["base_url"])
    return creds


@pytest.fixture
def mock_secudium_credentials():
    """
    Mock SECUDIUM credentials (NEVER real ones!)
    ⚠️ These are FAKE credentials for testing only
    """
    creds = MOCK_CREDENTIALS["secudium"]
    validate_test_credentials(creds["username"], creds["password"], creds["api_url"])
    return creds


@pytest.fixture
def mock_collection_service(mocker):
    """
    Mock collection service to prevent real API calls
    ⚠️ All network requests are mocked
    """
    mock_service = mocker.MagicMock()
    mock_service.collect_regtech_ips.return_value = {
        "success": True,
        "ips_collected": 100,
        "source": "REGTECH_MOCK"
    }
    mock_service.collect_secudium_ips.return_value = {
        "success": True,
        "ips_collected": 50,
        "source": "SECUDIUM_MOCK"
    }
    return mock_service
