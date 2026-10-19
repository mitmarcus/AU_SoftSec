import csv
import io
from datetime import datetime

import requests
from fastapi import FastAPI, Header, HTTPException
from payrates import round_quarter, total_pay
from pydantic import BaseModel

RECORDS = "http://records:8000"

app = FastAPI()


class Job(BaseModel):
    month: str


def make_csv(data, shifts, result):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["cleaner", data["cleaner"]])
    writer.writerow(["month", data["month"]])
    writer.writerow(["hourly_rate", data["hourly_rate"]])
    writer.writerow([])
    writer.writerow(["start", "end", "hours"])
    for start, end in shifts:
        writer.writerow([start.isoformat(), end.isoformat(), round_quarter((end - start).total_seconds() / 3600)])
    writer.writerow([])
    writer.writerow(["total_hours", result["hours"]])
    writer.writerow(["total_pay", result["pay"]])
    return out.getvalue()


@app.post("/jobs")
def run_job(job: Job, authorization: str = Header(default="")):
    # payroll has no key of its own; it passes on the job token from api and records decides
    headers = {"Authorization": authorization}

    resp = requests.get(f"{RECORDS}/entries", params={"month": job.month}, headers=headers, timeout=5)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.json().get("detail"))
    data = resp.json()

    shifts = [(datetime.fromisoformat(e["start_time"]), datetime.fromisoformat(e["end_time"]))
              for e in data["entries"]]
    result = total_pay(shifts, data["hourly_rate"])

    resp = requests.put(f"{RECORDS}/payslips/{job.month}", json={"content": make_csv(data, shifts, result)},
                        headers=headers, timeout=5)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.json().get("detail"))
    return {**resp.json(), **result}


@app.get("/health")
def health():
    return {"status": "ok"}
