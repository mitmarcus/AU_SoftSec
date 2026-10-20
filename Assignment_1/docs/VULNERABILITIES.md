# Planted vulnerabilities

Three from the course catalog (CWE-22, CWE-89, CWE-20), one from composing the services (CWE-862 across `api`, `payroll`, `records`). Each planted in its own commit with a `# VULN CWE-xx` comment, proven by a test in `tests/exploits/`, then fixed.

- `v1-vulnerable` (`305067f`): all four bugs.
- `v2-fixed` (`9661bad`): all four fixes.

| # | CWE | Planted | Fixed | Exploit test |
|---|---|---|---|---|
| V1 | CWE-22 Path Traversal | `405b6f1` | `4853573` | `tests/exploits/test_cwe22_path_traversal.py` |
| V2 | CWE-89 SQL Injection | `9ef01b7` | `00f06ef` | `tests/exploits/test_cwe89_sql_injection.py` |
| V3 | CWE-20 Improper Input Validation | `c929555` | `552b4d8` | `tests/exploits/test_cwe20_input_validation.py` |
| V4 | CWE-862 Missing Authorization, across services | `baed1bb` | `9661bad` | `tests/exploits/test_cwe862_confused_deputy.py` |

On `v1-vulnerable` the exploit tests assert the attack works (all pass). The fix commits flip them to assert it's blocked (pass on `v2-fixed`, `evidence/v2-fixed/junit.xml`).

---

## V1: CWE-22 Path Traversal

1. **Name:** Improper Limitation of a Pathname to a Restricted Directory, payslip download in `records`.
2. **Characterisation:** the file name is appended to the cleaner's payslip folder. `../` escapes it, so iza reads anything `records` can, including other cleaners' payslips.
3. **Code** (`records/app.py:236` on `v1-vulnerable`):

   ```python
   path = PAYSLIP_DIR / c["sub"] / file  # VULN CWE-22
   if not path.is_file():
       raise HTTPException(404, "no such payslip")
   return FileResponse(path, media_type="text/csv")
   ```

   Flow: `client.py download` calls `api` `GET /payslips?file=` (`api/app.py:138`), which forwards to `records`. There `PAYSLIP_DIR / "iza" / "../marius/marius-2026-09.csv"` resolves to `/data/payslips/marius/marius-2026-09.csv`. The folder comes from the token, but nothing checks the final path stays in it.
4. **Assumption violated:** a file name is one segment inside the requester's folder.
5. **Underlying factor:** untrusted input in a path with no canonicalisation. `pathlib` keeps `..` as a normal segment and the OS resolves it.
6. **Exploitability:** any cleaner, via the public `api`. Query parameter, so HTTP clients don't normalise `../`. Catch: Linux only resolves `iza/..` if `payslips/iza/` exists, so iza generates a payslip first. The test then reads `cleaner,marius` and `hourly_rate,210.0`.

**Fix (`4853573`):** `records/app.py:236-239` resolves folder and path, refuses anything not `is_relative_to` the folder. The same request now returns `404 no such payslip`.

---

## V2: CWE-89 SQL Injection

1. **Name:** Improper Neutralization of Special Elements used in an SQL Command, cleaner job search.
2. **Characterisation:** search text becomes part of the SQL, so input changes query logic.
3. **Code** (`records/app.py:143` on `v1-vulnerable`):

   ```python
   query = f"SELECT * FROM jobs WHERE cleaner = '{c['sub']}' AND customer LIKE '%{customer}%'"  # VULN CWE-89
   rows = conn.execute(query).fetchall()
   ```

   `customer = "%' OR 1=1 --"` gives `... WHERE cleaner = 'iza' AND customer LIKE '%%' OR 1=1 --%'`. `AND` binds tighter than `OR`, so every row matches; `--` eats the trailing quote.
4. **Assumption violated:** search text is data and can't widen the ownership filter.
5. **Underlying factor:** string formatting mixed data and SQL. The manager branch two lines up already used placeholders; the cleaner branch didn't.
6. **Exploitability:** any cleaner, `client.py search "%' OR 1=1 --"` returns every job with customer, address and cleaner. Stacked queries (`; DROP TABLE`) fail since SQLite `execute` runs one statement; `OR` / `UNION SELECT` reads work. Bandit: B608, MEDIUM severity, LOW confidence (`evidence/v1-vulnerable/bandit.json`). Gate blocks HIGH only, so bandit alone didn't stop it.

**Fix (`00f06ef`):** `?` placeholders (`records/app.py:143-144`). The payload becomes a literal customer name search and returns `[]`. No B608 in `evidence/v2-fixed/bandit.json`.

---

## V3: CWE-20 Improper Input Validation

1. **Name:** Improper Input Validation, clock-out (`records`) and payslip calculation (`payroll`).
2. **Characterisation:** cleaner picks the clock-out time. No semantic checks, so shifts can end before they start or run any length. `payroll` pays whatever's stored.
3. **Code** (`records/app.py:192` on `v1-vulnerable`):

   ```python
   # VULN CWE-20: end time is stored without checking it is after the start or within MAX_SHIFT
   conn.execute("UPDATE entries SET end_time = ? WHERE id = ?", (end.isoformat(), entry["id"]))
   ```

   Pydantic checks `time` parses as a `datetime`, nothing more. `total_pay(shifts, rate)` (`payrates/payrates/__init__.py:25`) multiplies `end - start` by the rate without checking.
4. **Assumption violated:** a shift has end > start and is ≤ 12 h. `payroll` assumed `records` enforced it.
5. **Underlying factor:** no validation at entry, and the consumer trusted another component. The catalog names this: "assuming another component has already validated the input".
6. **Exploitability:** iza clocks in on job 1 at 2026-09-10 08:00, out at 2026-09-11 14:00. 200 OK, next payslip has 30 extra hours. Reversed shifts lower hours, so they don't help. Only iza's pay changes, but the employer pays.

**Fix (`552b4d8`):** `records/app.py:193-196` rejects `end <= start` and `end - start > MAX_SHIFT` with 400. `payroll/app.py:50-52` rechecks every shift before `total_pay`, 422 on failure. Month format was already checked (`api/app.py:122`, `records/app.py:97`). Exploit test now gets 400 for both cases, hours unchanged. No test reaches the `payroll` check alone since `records` rejects first; it covers rows that get into the DB another way.

---

## V4: CWE-862 across services (confused deputy)

1. **Name:** Missing Authorization, from how `api`, `payroll` and `records` are composed. `payroll` is the confused deputy, using its access to `records` for a cleaner the caller picked.
2. **Characterisation:** each service looks fine alone. `api` authenticates, `payroll` forwards, `records` checks the job token's signature, audience, expiry, scope and month. But the job's cleaner travels as a plain field outside the token, and the last service trusts it.
3. **Code** (`v1-vulnerable`):

   ```python
   # api/app.py:133
   cleaner_id = body.cleaner_id or user["sub"]  # VULN CWE-862
   # payroll/app.py:40
   headers = {"Authorization": authorization, "X-Cleaner-Id": job.cleaner_id}  # VULN CWE-862
   # records/app.py:205
   return x_cleaner_id or c["sub"]  # VULN CWE-862
   ```

   Flow: iza sends `{"month": "2026-09", "cleaner_id": "marius"}`. `api` mints a valid job token (`sub=iza`) and forwards `cleaner_id=marius`. `payroll` puts it in `X-Cleaner-Id`. `records` accepts the token, reads marius's entries and rate, writes `payslips/marius/marius-2026-09.csv`.
4. **Assumption violated:** a job acts on the cleaner the verified token names. `records` instead trusted anything from the internal network.
5. **Underlying factor:** authority split between a signed token and an unsigned header; network position treated as trust. Per-service tests pass, the bug only shows end to end. Two Stage 3 authorization tests caught it (`test_payroll_cannot_act_for_other_cleaner`, `test_api_ignores_cleaner_in_payslip_request`) and stopped the pipeline (`evidence/v1-vulnerable/pipeline.log`: "2 failed, 23 passed", "Finished: FAILURE").
6. **Exploitability:** any cleaner, one extra JSON field. Response: `marius-2026-09.csv`, rate 210.0, 10.0 hours. marius's stored payslip is overwritten too. iza can't download it via `api` (download uses iza's own records token), but the response already leaks the data, and V1 would expose the file anyway.

**Fix (`9661bad`):** `api` ignores any cleaner in the body, `payroll` drops `X-Cleaner-Id`, `records` takes the cleaner only from the job token (`records/app.py:212`, `:224`). The same request now produces `iza-2026-09.csv` at 180.0.
