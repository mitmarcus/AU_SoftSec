import os

import requests
from conftest import API, RECORDS, job_token

# --- through api, as a user ---


def test_no_token_is_rejected():
    assert requests.get(f"{API}/jobs", timeout=5).status_code == 401


def test_cleaner_cannot_see_other_cleaners_jobs(iza):
    jobs = requests.get(f"{API}/jobs/search", params={"customer": "Pedersen"}, headers=iza, timeout=5).json()
    assert jobs == []


def test_cleaner_cannot_clock_in_on_other_cleaners_job(iza):
    # job 3 belongs to marius in the seed data
    resp = requests.post(f"{API}/jobs/3/clock-in", json={"time": "2026-09-22T08:00:00"}, headers=iza, timeout=5)
    assert resp.status_code == 403


def test_cleaner_cannot_download_other_cleaners_payslip(iza, marius):
    requests.post(f"{API}/payslips", json={"month": "2026-09"}, headers=marius, timeout=30)
    resp = requests.get(f"{API}/payslips", params={"file": "marius-2026-09.csv"}, headers=iza, timeout=5)
    assert resp.status_code == 404
    assert "marius" not in resp.text


def test_cleaner_cannot_call_manager_endpoints(iza):
    job = {"customer": "X", "address": "Y", "date": "2026-09-30", "cleaner": "iza"}
    assert requests.post(f"{API}/jobs", json=job, headers=iza, timeout=5).status_code == 403
    assert requests.get(f"{API}/manager/overview", headers=iza, timeout=5).status_code == 403


# --- straight to records, as payroll would call it ---


def test_records_rejects_expired_job_token():
    resp = requests.get(f"{RECORDS}/entries", params={"month": "2026-09"}, headers=job_token(minutes=-1), timeout=5)
    assert resp.status_code == 401


def test_records_rejects_wrong_audience():
    resp = requests.get(f"{RECORDS}/entries", params={"month": "2026-09"}, headers=job_token(aud="api"), timeout=5)
    assert resp.status_code == 401


def test_records_rejects_token_signed_with_api_key():
    headers = job_token(key=os.environ["API_JWT_KEY"])
    resp = requests.get(f"{RECORDS}/entries", params={"month": "2026-09"}, headers=headers, timeout=5)
    assert resp.status_code == 401


def test_records_rejects_missing_scope():
    headers = job_token(scope=["payslips:write"])
    resp = requests.get(f"{RECORDS}/entries", params={"month": "2026-09"}, headers=headers, timeout=5)
    assert resp.status_code == 403
    headers = job_token(scope=["entries:read"])
    resp = requests.put(f"{RECORDS}/payslips/2026-09", json={"content": "x"}, headers=headers, timeout=5)
    assert resp.status_code == 403


def test_job_token_cannot_use_user_endpoints():
    assert requests.get(f"{RECORDS}/jobs", headers=job_token(), timeout=5).status_code == 403


def test_payroll_cannot_write_other_month():
    resp = requests.put(f"{RECORDS}/payslips/2026-10", json={"content": "x"}, headers=job_token(month="2026-09"),
                        timeout=5)
    assert resp.status_code == 403


def test_payroll_cannot_act_for_other_cleaner():
    # the cleaner comes from the token; a header naming someone else changes nothing
    headers = {**job_token(sub="iza"), "X-Cleaner-Id": "marius"}
    entries = requests.get(f"{RECORDS}/entries", params={"month": "2026-09"}, headers=headers, timeout=5).json()
    assert entries["cleaner"] == "iza"
    resp = requests.put(f"{RECORDS}/payslips/2026-09", json={"content": "x"}, headers=headers, timeout=5)
    assert resp.json()["file"] == "iza-2026-09.csv"


def test_api_ignores_cleaner_in_payslip_request(iza):
    resp = requests.post(f"{API}/payslips", json={"month": "2026-09", "cleaner_id": "marius"}, headers=iza, timeout=30)
    assert resp.json()["file"] == "iza-2026-09.csv"
