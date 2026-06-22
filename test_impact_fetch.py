import os
import subprocess
import time
import socket
from playwright.sync_api import sync_playwright

def get_free_port():
    """Finds a free port on the local machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_impact_test(name, route_handler):
    """
    Helper to run a test case for the impact data fetch.
    """
    print(f"Running test: {name}...")
    port = get_free_port()

    # Start a local server to serve the SPA
    server_process = subprocess.Popen(
        ["python3", "-m", "http.server", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for the server to be ready
    max_retries = 10
    connected = False
    while max_retries > 0:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                connected = True
                break
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
            max_retries -= 1

    if not connected:
        server_process.terminate()
        raise Exception("Could not start local server.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # The URL of the Google Apps Script that provides live impact data
            impact_script_url = "https://script.google.com/macros/s/AKfycby_owYH4w5yghpplmh4CZ7IFSY6L0InArQ-kLcNMTQLcK-IZDXhFuV7CpbYVy6NNvzb/exec"

            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            # Intercept the live data fetch request
            page.route(impact_script_url, route_handler)

            # Navigating to #impact triggers the fetch via updateImpactStats()
            page.goto(f"http://localhost:{port}/#impact")

            # Wait for the fallback data to be visible instead of using a hardcoded timeout
            # The '40' value is the fallback for 'Total service visits'
            try:
                page.wait_for_selector("text=40", timeout=5000)
                page.wait_for_selector("text=Total service visits", timeout=5000)
            except Exception as e:
                print(f"Warning: wait_for_selector failed: {e}")

            # 1. Verify that the error was caught and logged to the console
            found_error = any("Live data fetch failed:" in error for error in console_errors)
            if not found_error:
                raise Exception(f"FAILED: Expected 'Live data fetch failed:' not found in console logs. Logs: {console_errors}")

            # 2. Verify the application remains functional and displays fallback data
            if page.is_visible("text=40") and page.is_visible("text=Total service visits"):
                print(f"PASSED: {name} - Error handled gracefully, fallback data visible.")
            else:
                raise Exception(f"FAILED: {name} - Fallback data (40 visits) not visible or app crashed.")

            browser.close()
    finally:
        server_process.terminate()
        server_process.wait()

def test_network_failure():
    run_impact_test("Network Failure", lambda route: route.abort("failed"))

def test_invalid_json_response():
    run_impact_test("Invalid JSON Response", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body="this is not json"
    ))

def test_server_error_500():
    run_impact_test("Server Error (500)", lambda route: route.fulfill(
        status=500,
        body="Internal Server Error"
    ))

if __name__ == "__main__":
    print("--- Starting Live Data Fetch Error Handling Tests ---")
    try:
        test_network_failure()
        test_invalid_json_response()
        test_server_error_500()
        print("--- All tests passed! ---")
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        exit(1)
