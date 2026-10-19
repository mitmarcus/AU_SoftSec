# Architecture

Three FastAPI services, one container each (`docker-compose.yml`), talking HTTP. The SQLite file lives inside `records` and isn't a component of its own.

| Component | Code | Owns | Holds | Network |
|---|---|---|---|---|
| `api` | `api/app.py` | nothing persistent | `API_JWT_KEY`, `RECORDS_JWT_KEY` | `public` (port 8000) and `internal` |
| `records` | `records/app.py` | users, jobs, entries (`/data/records.db`), payslip CSVs (`/data/payslips/<cleaner>/`) on volume `records-data` | `RECORDS_JWT_KEY` | `internal` only |
| `payroll` | `payroll/app.py` | nothing | no key, no volume | `internal` only |

- **Helper package:** `payrates` (`round_quarter`, `supplement`, `total_pay`). Built into `wheels/payrates-0.1.0-py3-none-any.whl` by `payrates/build_wheel.sh`, installed in `payroll/Dockerfile:9` with `pip install --no-deps --require-hashes -r payrates.txt`. Only the wheel goes into `payroll`, never the source.
- **Users:** every container runs as system user `app`.
- **Isolation:** `internal` is `internal: true` (`docker-compose.yml:44`), so `records` and `payroll` can't reach outside. Checked in Stage 2: a request from `payroll` to pypi.org failed with "Temporary failure in name resolution".

## Trust boundaries

```mermaid
flowchart LR
    subgraph host["Host: untrusted"]
        client["client.py"]
    end
    subgraph net["internal network: TB2"]
        api
        payroll
        records
        db[("records.db")]
        vol[("payslips/")]
    end
    client -- "TB1: HTTP :8000, user token" --> api
    api -- "TB3: records token" --> records
    api -- "TB3: job token" --> payroll
    payroll -- "TB3: job token" --> records
    records --- db
    records --- vol
```

- **TB1, host to `api`:** client input is untrusted. User token verified at `api/app.py:25`.
- **TB2, internal network:** being on it grants nothing. Before the CWE-862 fix (`9661bad`) `records` acted like it did. That was the composition bug.
- **TB3, service to service:** `records` decodes every token with its own key, `aud="records"`, required `exp`, `aud`, `sub` (`records/app.py:60-68`). Only `POST /login` skips this, and it just answers yes/no to a password.

## Tokens

| Token | Minted at | Claims | Key | Lifetime | Verified at |
|---|---|---|---|---|---|
| User token | `api/app.py:61` (login) | `sub`, `role`, `aud=api`, `exp` | `API_JWT_KEY` | 30 min | `api/app.py:25` |
| Records token | `api/app.py:40` (every user request) | `sub`, `role`, `aud=records`, `exp` | `RECORDS_JWT_KEY` | 60 s | `records/app.py:60` |
| Job token | `api/app.py:120` (payslip job) | `sub`, `job_id`, `month`, `scope=["entries:read","payslips:write"]`, `aud=records`, `exp` | `RECORDS_JWT_KEY` | 5 min | `records/app.py:60` and `:90` |

Records tokens have a `role` and no `scope`; job tokens the reverse. User endpoints require a role (`records/app.py:71`), job endpoints require a scope and matching month (`records/app.py:90`), so neither works on the other's endpoints (`test_job_token_cannot_use_user_endpoints`, `test_records_rejects_missing_scope`).

## Payslip flow

```mermaid
sequenceDiagram
    actor iza as iza (client.py)
    participant api
    participant payroll
    participant records

    iza->>api: POST /payslips {month: 2026-09}<br/>Authorization: user token
    Note over api: check 1: user token signature, aud=api, exp<br/>check 2: role == cleaner<br/>check 3: month matches YYYY-MM
    api->>api: mint job token<br/>sub=iza (from the JWT), month=2026-09,<br/>scope=[entries:read, payslips:write], exp=5 min
    api->>payroll: POST /jobs {month}<br/>Authorization: job token
    Note over payroll: holds no key, passes the token on unchanged
    payroll->>records: GET /entries?month=2026-09<br/>Authorization: job token
    Note over records: check 4: signature with records key, aud=records, exp<br/>check 5: scope has entries:read<br/>check 6: month == token month<br/>cleaner = token sub
    records-->>payroll: iza's rate and closed entries
    Note over payroll: check 7: every shift has start < end and is at most 12 h
    payroll->>payroll: payrates.total_pay(...)
    payroll->>records: PUT /payslips/2026-09 {content}<br/>Authorization: job token
    Note over records: checks 4 and 6 again, scope has payslips:write<br/>file written to payslips/iza/iza-2026-09.csv
    records-->>payroll: {file: iza-2026-09.csv}
    payroll-->>api: file, hours, pay, rate
    api-->>iza: 201

    iza->>api: GET /payslips?file=iza-2026-09.csv
    Note over api: user token, role == cleaner
    api->>records: GET /payslips?file=...<br/>Authorization: records token (sub=iza, 60 s)
    Note over records: records token, role == cleaner<br/>path resolved and kept inside payslips/iza/
    records-->>api: CSV
    api-->>iza: CSV
```

| Check | Code |
|---|---|
| 1 to 3 | `api/app.py:25`, `:121-123` |
| 4 | `records/app.py:60-68` |
| 5, 6 | `records/app.py:90-94` |
| 7 | `payroll/app.py:50-52` |
| download path | `records/app.py:235-239` |
