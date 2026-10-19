import requests
from conftest import API


def test_login_wrong_password():
    resp = requests.post(f"{API}/login", json={"username": "iza", "password": "nope"}, timeout=5)
    assert resp.status_code == 401


def test_cleaner_lists_own_jobs(iza):
    jobs = requests.get(f"{API}/jobs", headers=iza, timeout=5).json()
    assert jobs and all(j["cleaner"] == "iza" for j in jobs)


def test_search_jobs(iza):
    jobs = requests.get(f"{API}/jobs/search", params={"customer": "hans"}, headers=iza, timeout=5).json()
    assert [j["customer"] for j in jobs] == ["Hansen"]


def test_manager_assigns_job(andreea, iza):
    job = {"customer": "Larsen", "address": "Park Alle 7, Aarhus C", "date": "2026-09-20", "cleaner": "iza"}
    resp = requests.post(f"{API}/jobs", json=job, headers=andreea, timeout=5)
    assert resp.status_code == 201
    jobs = requests.get(f"{API}/jobs", headers=iza, timeout=5).json()
    assert resp.json()["id"] in [j["id"] for j in jobs]


def test_clock_in_and_out(andreea, iza):
    job = {"customer": "Olsen", "address": "Jaegergaardsgade 2, Aarhus C", "date": "2026-09-21", "cleaner": "iza"}
    job_id = requests.post(f"{API}/jobs", json=job, headers=andreea, timeout=5).json()["id"]

    resp = requests.post(f"{API}/jobs/{job_id}/clock-in", json={"time": "2026-09-21T08:00:00"}, headers=iza, timeout=5)
    assert resp.status_code == 201
    resp = requests.post(f"{API}/jobs/{job_id}/clock-out", json={"time": "2026-09-21T11:00:00"}, headers=iza, timeout=5)
    assert resp.status_code == 200
    assert resp.json()["end"] == "2026-09-21T11:00:00"


def test_generate_and_download_payslip(iza):
    resp = requests.post(f"{API}/payslips", json={"month": "2026-09"}, headers=iza, timeout=30)
    assert resp.status_code == 201, resp.text
    assert resp.json()["file"] == "iza-2026-09.csv"

    csv = requests.get(f"{API}/payslips", params={"file": "iza-2026-09.csv"}, headers=iza, timeout=5)
    assert csv.status_code == 200
    assert "cleaner,iza" in csv.text and "hourly_rate,180.0" in csv.text


def test_manager_overview(andreea):
    resp = requests.get(f"{API}/manager/overview", headers=andreea, timeout=5)
    assert resp.status_code == 200
    assert {"iza", "marius"} <= {h["cleaner"] for h in resp.json()["hours"]}
