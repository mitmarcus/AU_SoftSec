import requests

API = "http://localhost:8000"


def test_api_health():
    assert requests.get(f"{API}/health", timeout=5).json() == {"status": "ok"}
