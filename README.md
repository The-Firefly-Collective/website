# Firefly Collective SPA

This is a single-page application for the Firefly Collective.

## Testing

### Automated Frontend Tests

We use [Playwright](https://playwright.dev/) with Python to run automated frontend tests.

#### Prerequisites

- Python 3.x
- Playwright Python package
- Playwright browser binaries (e.g., Chromium)

To install the prerequisites, run:
```bash
pip install playwright
playwright install chromium
```

#### Running Tests

To run the error handling tests for the live data fetch:
```bash
python3 test_impact_fetch.py
```

These tests verify that:
1. Network failures during live data fetch are handled gracefully.
2. Invalid JSON responses are caught.
3. Server errors (e.g., 500) do not crash the application.
4. Fallback data is displayed when live data cannot be retrieved.
