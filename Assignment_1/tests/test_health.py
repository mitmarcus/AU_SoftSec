import requests
from conftest import API


def test_api_health():
    assert requests.get(f"{API}/health", timeout=5).json() == {"status": "ok"}
