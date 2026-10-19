# Threat model

Course table format (Threat Modeling to DevSecOps, Unit 1). First version is in [PLAN.md](PLAN.md) (`65be63d`); this one adds where each control landed and what proves it.

- **Attacker:** a logged-in cleaner (`iza`) after another cleaner's data (`marius`) or more pay, plus anything running inside a container.
- **Trusted:** the host, docker, the JWT keys.

## Asset register

| No. | Asset | Description / Purpose | Security Importance |
|---|---|---|---|
| 1 | Time entries | Clock-in/out per cleaner and job (`entries` table) | Integrity: they decide pay. Confidentiality: where and when someone works |
| 2 | Payslips | CSV per cleaner and month in `payslips/<cleaner>/` | Salary confidentiality; integrity of what gets paid |
| 3 | Hourly rates | `users.hourly_rate` | Confidential between cleaners |
| 4 | Jobs | Customer, address, date, assigned cleaner | Customer addresses; who works where |
| 5 | Credentials and keys | bcrypt hashes in `users`, `API_JWT_KEY`, `RECORDS_JWT_KEY` | `RECORDS_JWT_KEY` lets anyone mint a job token for any cleaner |
| 6 | `payrates` wheel | Runs inside `payroll` next to the job token | A changed wheel computes wrong pay or misuses the token |

## STRIDE

| STRIDE | Threat | Asset | Impact | Control and evidence |
|---|---|---|---|---|
| Spoofing | Forged, expired or wrong-audience token | 1, 2, 3 | Act as another cleaner | `jwt.decode` with key, `aud`, required claims (`records/app.py:60`, `api/app.py:25`); `test_records_rejects_expired_job_token`, `test_records_rejects_wrong_audience`, `test_records_rejects_token_signed_with_api_key`, `test_no_token_is_rejected` |
| Spoofing | Internal caller names another cleaner (`X-Cleaner-Id`, `cleaner_id`) | 1, 2, 3 | iza gets marius's payslip | V4, fixed in `9661bad`: cleaner only from token `sub`; `test_payroll_cannot_act_for_other_cleaner`, `test_api_ignores_cleaner_in_payslip_request`, `tests/exploits/test_cwe862_confused_deputy.py` |
| Tampering | Shift ending before it starts, or 30 h long | 1, 2 | Inflated pay | V3, fixed in `552b4d8`: `records/app.py:193-196`, `payroll/app.py:50-52`; `tests/exploits/test_cwe20_input_validation.py` |
| Tampering | Search text changes the SQL | 4 | All jobs exposed | V2, fixed in `00f06ef`: parameterised query `records/app.py:143`; `tests/exploits/test_cwe89_sql_injection.py`; B608 in `evidence/v1-vulnerable/bandit.json`, gone in `evidence/v2-fixed/bandit.json` |
| Tampering | Different bytes in the `payrates` wheel | 2, 6 | Wrong or leaked payslips | `--require-hashes` in `payroll/Dockerfile:9`; `wheels/payrates-0.1.0-py3-none-any.whl: OK` in `evidence/v2-fixed/pipeline.log` |
| Repudiation | Cleaner denies registering an entry | 1 | Pay dispute | Creator `sub` stored per entry (`records/app.py:179`). No audit log beyond that |
| Information Disclosure | `../` in payslip file name | 2, 3 | Read marius's payslip | V1, fixed in `4853573`: `resolve()` + `is_relative_to` (`records/app.py:236-239`); `tests/exploits/test_cwe22_path_traversal.py` |
| Information Disclosure | Cleaner calls manager overview | 1, 2, 3 | All hours and payslips | Role check `api/app.py:147`, `records/app.py:78`; `test_cleaner_cannot_call_manager_endpoints` |
| Denial of Service | Flood of payslip jobs or logins | 2 | Slow service | Not handled, no rate limit. Accepted |
| Elevation of Privilege | Cleaner assigns jobs, or job token on user endpoints | 1, 4 | Manager actions by a cleaner | `manager` (`records/app.py:78`), role required (`records/app.py:71`); `test_cleaner_cannot_call_manager_endpoints`, `test_job_token_cannot_use_user_endpoints` |
| Elevation of Privilege | `payroll` writes outside its job | 2 | Payslip for another month or cleaner | `job_token` checks scope and month (`records/app.py:90-94`); `test_payroll_cannot_write_other_month`, `test_records_rejects_missing_scope` |

## Threat to control mapping

| STRIDE | Primary control | Objective |
|---|---|---|
| Spoofing | bcrypt, signed JWTs with audience and expiry, identity only from verified `sub` | Authentication |
| Tampering | Parameterised SQL, time-entry validation in two services, pinned wheel hash | Integrity |
| Repudiation | Creator `sub` stored per entry | Accountability |
| Information Disclosure | Ownership check on every `records` query, canonical payslip paths | Confidentiality |
| Denial of Service | Short token lifetimes only | Availability |
| Elevation of Privilege | Role checks in `api` and `records`; job token = one cleaner, one month, two scopes, 5 min | Authorization |

## Not covered

No TLS between services, key rotation, rate limiting or audit log. The report covers what production would need.
