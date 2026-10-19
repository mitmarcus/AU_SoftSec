import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

DB_PATH = "/data/records.db"
PAYSLIP_DIR = Path("/data/payslips")
KEY = os.environ["RECORDS_JWT_KEY"]
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MAX_SHIFT = timedelta(hours=12)

app = FastAPI()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    PAYSLIP_DIR.mkdir(exist_ok=True)
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                hourly_rate REAL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                customer TEXT NOT NULL,
                address TEXT NOT NULL,
                date TEXT NOT NULL,
                cleaner TEXT NOT NULL REFERENCES users(username)
            );
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                job_id INTEGER NOT NULL REFERENCES jobs(id),
                cleaner TEXT NOT NULL REFERENCES users(username),
                start_time TEXT NOT NULL,
                end_time TEXT
            );
        """)


init_db()


# --- auth ---

def claims(authorization: str = Header(default="")):
    # every request needs a token signed with the records key and addressed to records
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing token")
    try:
        return jwt.decode(authorization[7:], KEY, algorithms=["HS256"], audience="records",
                          options={"require": ["exp", "aud", "sub"]})
    except jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")


def user(c=Depends(claims)):
    # job tokens have no role, so they cannot use the user endpoints
    if c.get("role") not in ("cleaner", "manager"):
        raise HTTPException(403, "user token required")
    return c


def manager(c=Depends(user)):
    if c["role"] != "manager":
        raise HTTPException(403, "manager only")
    return c


def cleaner(c=Depends(user)):
    if c["role"] != "cleaner":
        raise HTTPException(403, "cleaner only")
    return c


def job_token(c, scope, month):
    if scope not in c.get("scope", []):
        raise HTTPException(403, f"token lacks scope {scope}")
    if c.get("month") != month:
        raise HTTPException(403, "token is for another month")


def check_month(month):
    if not MONTH.match(month):
        raise HTTPException(400, "month must be YYYY-MM")


# --- login (called by api) ---

class Login(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(body: Login):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
    if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
        raise HTTPException(401, "wrong username or password")
    return {"username": row["username"], "role": row["role"]}


# --- jobs ---

class NewJob(BaseModel):
    customer: str
    address: str
    date: str
    cleaner: str


@app.get("/jobs")
def list_jobs(c=Depends(user)):
    with db() as conn:
        if c["role"] == "manager":
            rows = conn.execute("SELECT * FROM jobs ORDER BY date").fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs WHERE cleaner = ? ORDER BY date", (c["sub"],)).fetchall()
    return [dict(r) for r in rows]


@app.get("/jobs/search")
def search_jobs(customer: str, c=Depends(user)):
    with db() as conn:
        if c["role"] == "manager":
            rows = conn.execute("SELECT * FROM jobs WHERE customer LIKE ?", (f"%{customer}%",)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs WHERE cleaner = ? AND customer LIKE ?",
                                (c["sub"], f"%{customer}%")).fetchall()
    return [dict(r) for r in rows]


@app.post("/jobs", status_code=201)
def assign_job(body: NewJob, c=Depends(manager)):
    with db() as conn:
        row = conn.execute("SELECT role FROM users WHERE username = ?", (body.cleaner,)).fetchone()
        if not row or row["role"] != "cleaner":
            raise HTTPException(400, "unknown cleaner")
        cur = conn.execute("INSERT INTO jobs (customer, address, date, cleaner) VALUES (?, ?, ?, ?)",
                           (body.customer, body.address, body.date, body.cleaner))
    return {"id": cur.lastrowid, **body.model_dump()}


# --- clocking ---

class Clock(BaseModel):
    time: datetime


def own_job(conn, job_id, username):
    job = conn.execute("SELECT cleaner FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        raise HTTPException(404, "no such job")
    if job["cleaner"] != username:
        raise HTTPException(403, "not your job")


@app.post("/jobs/{job_id}/clock-in", status_code=201)
def clock_in(job_id: int, body: Clock, c=Depends(cleaner)):
    with db() as conn:
        own_job(conn, job_id, c["sub"])
        if conn.execute("SELECT 1 FROM entries WHERE job_id = ? AND end_time IS NULL", (job_id,)).fetchone():
            raise HTTPException(409, "already clocked in")
        cur = conn.execute("INSERT INTO entries (job_id, cleaner, start_time) VALUES (?, ?, ?)",
                           (job_id, c["sub"], body.time.replace(tzinfo=None).isoformat()))
    return {"entry_id": cur.lastrowid}


@app.post("/jobs/{job_id}/clock-out")
def clock_out(job_id: int, body: Clock, c=Depends(cleaner)):
    end = body.time.replace(tzinfo=None)
    with db() as conn:
        own_job(conn, job_id, c["sub"])
        entry = conn.execute("SELECT * FROM entries WHERE job_id = ? AND end_time IS NULL", (job_id,)).fetchone()
        if not entry:
            raise HTTPException(409, "not clocked in")
        start = datetime.fromisoformat(entry["start_time"])
        if end <= start:
            raise HTTPException(400, "clock-out must be after clock-in")
        if end - start > MAX_SHIFT:
            raise HTTPException(400, "shift longer than 12 hours")
        conn.execute("UPDATE entries SET end_time = ? WHERE id = ?", (end.isoformat(), entry["id"]))
    return {"entry_id": entry["id"], "start": entry["start_time"], "end": end.isoformat()}


# --- payslip job (job token only) ---

class Payslip(BaseModel):
    content: str


@app.get("/entries")
def entries_for_job(month: str, c=Depends(claims)):
    check_month(month)
    job_token(c, "entries:read", month)
    with db() as conn:
        rate = conn.execute("SELECT hourly_rate FROM users WHERE username = ?", (c["sub"],)).fetchone()
        rows = conn.execute("SELECT start_time, end_time FROM entries WHERE cleaner = ? AND start_time LIKE ? AND end_time IS NOT NULL",
                            (c["sub"], f"{month}-%")).fetchall()
    return {"cleaner": c["sub"], "month": month, "hourly_rate": rate["hourly_rate"], "entries": [dict(r) for r in rows]}


@app.put("/payslips/{month}")
def store_payslip(month: str, body: Payslip, c=Depends(claims)):
    check_month(month)
    job_token(c, "payslips:write", month)
    folder = PAYSLIP_DIR / c["sub"]
    folder.mkdir(exist_ok=True)
    name = f"{c['sub']}-{month}.csv"
    (folder / name).write_text(body.content)
    return {"file": name}


# --- payslip download and manager overview ---

@app.get("/payslips")
def download_payslip(file: str, c=Depends(cleaner)):
    path = PAYSLIP_DIR / c["sub"] / file  # VULN CWE-22: file is joined as given, so ../ leaves the cleaner's folder
    if not path.is_file():
        raise HTTPException(404, "no such payslip")
    return FileResponse(path, media_type="text/csv")


@app.get("/overview")
def overview(c=Depends(manager)):
    with db() as conn:
        rows = conn.execute("""
            SELECT cleaner, substr(start_time, 1, 7) AS month,
                   ROUND(SUM((julianday(end_time) - julianday(start_time)) * 24), 2) AS hours
            FROM entries WHERE end_time IS NOT NULL
            GROUP BY cleaner, month ORDER BY cleaner, month
        """).fetchall()
    payslips = sorted(str(p.relative_to(PAYSLIP_DIR)) for p in PAYSLIP_DIR.glob("*/*.csv"))
    return {"hours": [dict(r) for r in rows], "payslips": payslips}


@app.get("/health")
def health():
    return {"status": "ok"}
