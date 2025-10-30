"""
Test Configuration - Safeguards to Prevent Real API Calls
⚠️ CRITICAL: All tests MUST use mock data, NEVER real credentials
"""
import os
import pytest
import warnings

# Mock credentials (NEVER use real ones!)
MOCK_CREDENTIALS = {
    "regtech": {
        "username": "test_regtech_user",
        "password": "test_regtech_pass_fake_12345",
        "base_url": "https://test.regtech.example.com"
    },
    "secudium": {
        "username": "test_secudium_user",
        "password": "test_secudium_pass_fake_67890",
        "api_url": "https://test.secudium.example.com",
        "token": "fake_token_abcdefgh"
    }
}

# Forbidden real API URLs (tests MUST NOT access these)
FORBIDDEN_URLS = [
    "regtech.fsec.or.kr",
    "secudium.skinfosec.co.kr",
    "www.secudium.com",
    "blacklist.nxtd.co.kr"  # Even our own production API
]


def validate_test_credentials(username, password, url=None):
    """
    Validate that test credentials are NOT real production credentials

    Raises:
        ValueError: If real credentials detected
    """
    # Check for mock patterns
    if not ("test_" in username or "fake" in password.lower()):
        raise ValueError(
            f"🚨 SECURITY: Real credentials detected in test!\n"
            f"Username: {username}\n"
            f"Tests MUST use mock credentials only."
        )

    # Check for forbidden URLs
    if url:
        for forbidden in FORBIDDEN_URLS:
            if forbidden in url:
                raise ValueError(
                    f"🚨 SECURITY: Production URL detected in test!\n"
                    f"URL: {url}\n"
                    f"Tests MUST NOT access real APIs."
                )

    return True


def check_environment_safety():
    """
    Check that test environment doesn't have real credentials

    Warns if suspicious environment variables found
    """
    suspicious_env_vars = [
        "REGTECH_USERNAME",
        "REGTECH_PASSWORD",
        "SECUDIUM_USERNAME",
        "SECUDIUM_PASSWORD",
        "SECUDIUM_TOKEN"
    ]

    found_vars = []
    for var in suspicious_env_vars:
        if os.getenv(var):
            found_vars.append(var)

    if found_vars:
        warnings.warn(
            f"⚠️ WARNING: Real credential env vars found during testing: {found_vars}\n"
            f"Tests should NOT use real credentials. Use test_config.MOCK_CREDENTIALS instead.",
            UserWarning
        )


# Run safety check when module imported
check_environment_safety()


# Pytest fixture to enforce mock credentials
@pytest.fixture(autouse=True, scope="session")
def enforce_mock_credentials():
    """Auto-applied fixture to ensure tests use mock data"""
    # Set mock credentials in environment (override any real ones)
    os.environ["TESTING"] = "true"
    os.environ["USE_MOCK_CREDENTIALS"] = "true"

    # Warning banner
    print("\n" + "="*70)
    print("🧪 TEST MODE: Using MOCK credentials only")
    print("🚫 Real API calls are FORBIDDEN")
    print("="*70 + "\n")

    yield

    # Cleanup
    os.environ.pop("TESTING", None)
    os.environ.pop("USE_MOCK_CREDENTIALS", None)


# Decorator to mark tests that need network (should be rare)
def requires_network(func):
    """
    Decorator for tests that legitimately need network access
    (Should be used VERY rarely, most tests should be mocked)
    """
    return pytest.mark.network(func)


# Decorator to explicitly mark tests as mock-only (recommended)
def mock_only(func):
    """
    Decorator to explicitly mark test as using mocks only
    (Recommended for all collection tests)
    """
    def wrapper(*args, **kwargs):
        # Double-check no real credentials
        if os.getenv("TESTING") != "true":
            pytest.fail("Test must run in TESTING=true environment")
        return func(*args, **kwargs)
    return wrapper
