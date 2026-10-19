"""Command-line client for the cleaning manager API."""

import argparse
import getpass
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

API = "http://localhost:8000"
TOKEN_FILE = Path(".token")


def auth():
    if not TOKEN_FILE.exists():
        sys.exit("not logged in, run: client.py login <username>")
    return {"Authorization": f"Bearer {TOKEN_FILE.read_text().strip()}"}


def show(resp):
    if resp.status_code >= 400:
        sys.exit(f"error {resp.status_code}: {resp.json().get('detail')}")
    print(json.dumps(resp.json(), indent=2))


def login(args):
    password = args.password or getpass.getpass()
    resp = requests.post(f"{API}/login", json={"username": args.username, "password": password}, timeout=5)
    if resp.status_code != 200:
        sys.exit(f"error {resp.status_code}: {resp.json().get('detail')}")
    TOKEN_FILE.write_text(resp.json()["token"])
    TOKEN_FILE.chmod(0o600)
    print(f"logged in as {args.username} ({resp.json()['role']})")


def jobs(args):
    show(requests.get(f"{API}/jobs", headers=auth(), timeout=5))


def assign(args):
    job = {"customer": args.customer, "address": args.address, "date": args.date, "cleaner": args.cleaner}
    show(requests.post(f"{API}/jobs", json=job, headers=auth(), timeout=5))


def search(args):
    show(requests.get(f"{API}/jobs/search", params={"customer": args.customer}, headers=auth(), timeout=5))


def clock(action):
    def run(args):
        time = args.at or datetime.now().isoformat(timespec="seconds")
        show(requests.post(f"{API}/jobs/{args.job_id}/{action}", json={"time": time}, headers=auth(), timeout=5))
    return run


def payslip(args):
    show(requests.post(f"{API}/payslips", json={"month": args.month}, headers=auth(), timeout=30))


def download(args):
    resp = requests.get(f"{API}/payslips", params={"file": args.file}, headers=auth(), timeout=5)
    if resp.status_code >= 400:
        sys.exit(f"error {resp.status_code}: {resp.json().get('detail')}")
    print(resp.text)


def all_hours(args):
    show(requests.get(f"{API}/manager/overview", headers=auth(), timeout=5))


def main():
    parser = argparse.ArgumentParser(description="Cleaning manager client")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("login")
    p.add_argument("username")
    p.add_argument("--password")
    p.set_defaults(func=login)

    sub.add_parser("jobs", help="list your jobs").set_defaults(func=jobs)

    p = sub.add_parser("assign", help="manager: assign a job")
    p.add_argument("cleaner")
    p.add_argument("customer")
    p.add_argument("address")
    p.add_argument("date", help="YYYY-MM-DD")
    p.set_defaults(func=assign)

    p = sub.add_parser("search", help="search your jobs by customer")
    p.add_argument("customer")
    p.set_defaults(func=search)

    for action in ("clock-in", "clock-out"):
        p = sub.add_parser(action)
        p.add_argument("job_id", type=int)
        p.add_argument("--at", help="time, e.g. 2026-09-21T08:00 (default: now)")
        p.set_defaults(func=clock(action))

    p = sub.add_parser("payslip", help="generate your payslip")
    p.add_argument("month", help="YYYY-MM")
    p.set_defaults(func=payslip)

    p = sub.add_parser("download", help="download a payslip")
    p.add_argument("file", help="e.g. iza-2026-09.csv")
    p.set_defaults(func=download)

    sub.add_parser("all-hours", help="manager: hours and payslips of all cleaners").set_defaults(func=all_hours)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
