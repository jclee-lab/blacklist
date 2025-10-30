
import os
import requests
import argparse
import json
import time

# --- Configuration ---
BASE_URL = os.getenv("BASE_URL", "http://blacklist-app:2542")
SUCCESS_COLOR = '\033[92m'
FAIL_COLOR = '\033[91m'
INFO_COLOR = '\033[94m'
RESET_COLOR = '\033[0m'

def print_step(message):
    """Prints a formatted step message."""
    print(f"\n{INFO_COLOR}▶ {message}{RESET_COLOR}")

def print_success(message):
    """Prints a formatted success message."""
    print(f"{SUCCESS_COLOR}✅ {message}{RESET_COLOR}")

def print_fail(message):
    """Prints a formatted failure message."""
    print(f"{FAIL_COLOR}❌ {message}{RESET_COLOR}")

def run_test(description, func, *args, **kwargs):
    """Runs a test function and prints the result."""
    print(f"  - {description}... ", end="")
    try:
        result, message = func(*args, **kwargs)
        if result:
            print(f"{SUCCESS_COLOR}PASS{RESET_COLOR}")
            return True, message
        else:
            print(f"{FAIL_COLOR}FAIL{RESET_COLOR}")
            print_fail(f"    Reason: {message}")
            return False, message
    except Exception as e:
        print(f"{FAIL_COLOR}ERROR{RESET_COLOR}")
        print_fail(f"    Exception: {e}")
        return False, str(e)

# --- Test Functions ---

def test_set_credentials(username, password):
    """Sets the REGTECH credentials via API."""
    url = f"{BASE_URL}/collection-panel/api/save-credentials"
    data = {
        "regtech_username": username,
        "regtech_password": password,
        "secudium_username": "",
        "secudium_password": ""
    }
    response = requests.post(url, json=data, timeout=10)
    if response.status_code == 200 and response.json().get("success"):
        return True, "Credentials set successfully."
    return False, f"API returned status {response.status_code}: {response.text}"

def test_load_credentials(expected_username):
    """Verifies that the credentials were saved correctly."""
    url = f"{BASE_URL}/collection-panel/api/load-credentials"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return False, f"API returned status {response.status_code}"
    
    data = response.json()
    if not data.get("success"):
        return False, "API call was not successful."

    loaded_username = data.get("credentials", {}).get("regtech_username")
    if loaded_username == expected_username:
        return True, "Loaded credentials match expected credentials."
    return False, f"Loaded username '{loaded_username}' does not match expected '{expected_username}'."

def test_health_check():
    """Checks the main health endpoint."""
    url = f"{BASE_URL}/health"
    response = requests.get(url, timeout=10)
    if response.status_code == 200 and response.json().get("status") == "healthy":
        return True, "Health check passed."
    return False, f"Health check failed with status {response.status_code}: {response.text}"

def test_monitoring_dashboard():
    """Checks the monitoring dashboard API."""
    url = f"{BASE_URL}/api/monitoring/dashboard"
    response = requests.get(url, timeout=15)
    if response.status_code == 200 and response.json().get("status") == "success":
        return True, "Monitoring dashboard is accessible."
    return False, f"Dashboard API failed with status {response.status_code}: {response.text}"

def test_api_logs():
    """Checks the API logs endpoint."""
    url = f"{BASE_URL}/api/logs?minutes=1"
    response = requests.get(url, timeout=10)
    if response.status_code == 200 and response.json().get("status") == "success":
        return True, "Logs API is accessible."
    return False, f"Logs API failed with status {response.status_code}: {response.text}"


def main():
    """Main function to run the integrated test suite."""
    parser = argparse.ArgumentParser(description="Blacklist Production Environment Test Script")
    parser.add_argument("--user", required=True, help="REGTECH Username")
    parser.add_argument("--password", required=True, help="REGTECH Password")
    args = parser.parse_args()

    print("==================================================")
    print("  Blacklist - Production Integration Test")
    print("==================================================")

    results = {}

    # --- Step 1: Configuration ---
    print_step("Step 1: Setting Credentials")
    results['set_credentials'], _ = run_test(
        "Set REGTECH credentials via API",
        test_set_credentials,
        args.user,
        args.password
    )
    time.sleep(1) # Give a moment for the config to settle

    # --- Step 2: Verification ---
    print_step("Step 2: Verifying System State")
    results['health_check'], _ = run_test("Check /health endpoint", test_health_check)
    
    if results.get('set_credentials'):
        results['load_credentials'], _ = run_test(
            "Verify saved credentials",
            test_load_credentials,
            args.user
        )

    # --- Step 3: API Endpoint Tests ---
    print_step("Step 3: Testing Core APIs")
    results['monitoring_dashboard'], _ = run_test("Check monitoring dashboard API", test_monitoring_dashboard)
    results['api_logs'], _ = run_test("Check logs API", test_api_logs)

    # --- Summary ---
    print("\n==================================================")
    print("                  Test Summary")
    print("==================================================")
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    if passed_count == total_count:
        print_success(f"All {total_count} tests passed!")
    else:
        print_fail(f"{passed_count}/{total_count} tests passed.")

    print("--------------------------------------------------")
    for test_name, success in results.items():
        status = f"{SUCCESS_COLOR}PASS{RESET_COLOR}" if success else f"{FAIL_COLOR}FAIL{RESET_COLOR}"
        print(f"{test_name.replace('_', ' ').title():<25}: {status}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
