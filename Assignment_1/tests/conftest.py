import os
from datetime import UTC, datetime, timedelta

import jwt
import pytest
import requests

API = "http://api:8000"
RECORDS = "http://records:8000"
PASSWORDS = {"iza": "iza-pass", "marius": "marius-pass", "andreea": "andreea-pass"}


def login(username):
    resp = requests.post(f"{API}/login", json={"username": username, "password": PASSWORDS[username]}, timeout=5)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def job_token(sub="iza", month="2026-09", scope=("entries:read", "payslips:write"),
              aud="records", minutes=5, key=None):
    """A job token like the one api mints, with fields that tests can change."""
    claims = {
        "sub": sub,
        "job_id": "test",
        "month": month,
        "scope": list(scope),
        "aud": aud,
        "exp": datetime.now(UTC) + timedelta(minutes=minutes),
    }
    token = jwt.encode(claims, key or os.environ["RECORDS_JWT_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def iza():
    return login("iza")


@pytest.fixture
def marius():
    return login("marius")


@pytest.fixture
def andreea():
    return login("andreea")
