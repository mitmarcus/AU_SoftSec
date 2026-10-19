import os
import re
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

API_KEY = os.environ["API_JWT_KEY"]
RECORDS_KEY = os.environ["RECORDS_JWT_KEY"]
RECORDS = "http://records:8000"
PAYROLL = "http://payroll:8000"
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

app = FastAPI()


def make_token(claims, key, lifetime):
    claims = {**claims, "exp": datetime.now(timezone.utc) + lifetime}
    return jwt.encode(claims, key, algorithm="HS256")


def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing token")
    try:
        return jwt.decode(authorization[7:], API_KEY, algorithms=["HS256"], audience="api",
                          options={"require": ["exp", "aud", "sub", "role"]})
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid or expired token")


def require_role(user, role):
    if user["role"] != role:
        raise HTTPException(403, f"{role} only")


def records_auth(user):
    # short-lived token for records, so records can do its own checks on this user
    token = make_token({"sub": user["sub"], "role": user["role"], "aud": "records"},
                       RECORDS_KEY, timedelta(seconds=60))
    return {"Authorization": f"Bearer {token}"}


def check(resp):
    if resp.status_code >= 400:
        raise HTTPException(resp.status_code, resp.json().get("detail", "error"))
    return resp


# --- login ---

class Login(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(body: Login):
    user = check(requests.post(f"{RECORDS}/login", json=body.model_dump(), timeout=5)).json()
    token = make_token({"sub": user["username"], "role": user["role"], "aud": "api"},
                       API_KEY, timedelta(minutes=30))
    return {"token": token, "role": user["role"]}


# --- jobs and clocking ---

class NewJob(BaseModel):
    customer: str
    address: str
    date: str
    cleaner: str


class Clock(BaseModel):
    time: datetime


@app.get("/jobs")
def list_jobs(user=Depends(current_user)):
    return check(requests.get(f"{RECORDS}/jobs", headers=records_auth(user), timeout=5)).json()


@app.get("/jobs/search")
def search_jobs(customer: str, user=Depends(current_user)):
    return check(requests.get(f"{RECORDS}/jobs/search", params={"customer": customer},
                              headers=records_auth(user), timeout=5)).json()


@app.post("/jobs", status_code=201)
def assign_job(body: NewJob, user=Depends(current_user)):
    require_role(user, "manager")
    return check(requests.post(f"{RECORDS}/jobs", json=body.model_dump(),
                               headers=records_auth(user), timeout=5)).json()


@app.post("/jobs/{job_id}/clock-in", status_code=201)
def clock_in(job_id: int, body: Clock, user=Depends(current_user)):
    require_role(user, "cleaner")
    return check(requests.post(f"{RECORDS}/jobs/{job_id}/clock-in", json={"time": body.time.isoformat()},
                               headers=records_auth(user), timeout=5)).json()


@app.post("/jobs/{job_id}/clock-out")
def clock_out(job_id: int, body: Clock, user=Depends(current_user)):
    require_role(user, "cleaner")
    return check(requests.post(f"{RECORDS}/jobs/{job_id}/clock-out", json={"time": body.time.isoformat()},
                               headers=records_auth(user), timeout=5)).json()


# --- payslips ---

class PayslipRequest(BaseModel):
    month: str
    cleaner_id: str | None = None


@app.post("/payslips", status_code=201)
def generate_payslip(body: PayslipRequest, user=Depends(current_user)):
    require_role(user, "cleaner")
    if not MONTH.match(body.month):
        raise HTTPException(400, "month must be YYYY-MM")
    # job token: one cleaner, one month, two actions, five minutes
    job_token = make_token({
        "sub": user["sub"],
        "job_id": str(uuid.uuid4()),
        "month": body.month,
        "scope": ["entries:read", "payslips:write"],
        "aud": "records",
    }, RECORDS_KEY, timedelta(minutes=5))
    cleaner_id = body.cleaner_id or user["sub"]  # VULN CWE-862: cleaner taken from the request body, not the JWT
    resp = requests.post(f"{PAYROLL}/jobs", json={"month": body.month, "cleaner_id": cleaner_id},
                         headers={"Authorization": f"Bearer {job_token}"}, timeout=30)
    return check(resp).json()


@app.get("/payslips")
def download_payslip(file: str, user=Depends(current_user)):
    require_role(user, "cleaner")
    resp = check(requests.get(f"{RECORDS}/payslips", params={"file": file},
                              headers=records_auth(user), timeout=5))
    return Response(resp.content, media_type="text/csv")


@app.get("/manager/overview")
def overview(user=Depends(current_user)):
    require_role(user, "manager")
    return check(requests.get(f"{RECORDS}/overview", headers=records_auth(user), timeout=5)).json()


@app.get("/health")
def health():
    return {"status": "ok"}
