# Decisions

Where the assignment left things open, this is what I picked.

**Users and roles**

- `iza`, `marius` (cleaners), `andreea` (manager). In attacks, iza attacks and marius is the victim.
- Managers can list payslips but not download them. The assignment needs only one privileged action.
- Design principles: least privilege, complete mediation, fail-safe defaults (the three the assignment names).

**Tokens and auth**

- HS256, one shared key per audience. `payroll` gets no key.
- `api` mints a 60 s records token per request, so `records` authorises users itself instead of trusting `api`.
- `records` owns the users table and checks bcrypt. `api` asks it, then mints the token.
- `records` `/login` takes no token: it only answers yes/no, and only `api` calls it.
- Dev JWT keys default in `docker-compose.yml`, overridable via env. Real deployment needs a secret store.

**Data and endpoints**

- Clients send clock-in/out times, so hours can be registered after the shift. Needed for CWE-20.
- Payslips stored as `payslips/<cleaner>/<cleaner>-<YYYY-MM>.csv`.
- Download is `GET /payslips?file=...`, not a path segment. HTTP clients strip `../` from paths, which would hide the traversal.

**Build and infra**

- Wheel hash in `payroll/payrates.txt`, not `requirements.txt`. One hashed line makes pip demand hashes everywhere, so the wheel gets its own `--require-hashes --no-deps` step.
- `api` on `public` + `internal: true`; `records` and `payroll` only on `internal`, no route out.
- `make seed` pipes the seed script into `records`, the only service allowed to touch the DB.
- Tests run in a `tests` container on `internal` (`docker compose run --rm tests`) to reach `records` without publishing its port.

**Pipeline and scope**

- `v1-vulnerable` is on the Jenkinsfile commit so the pipeline can run on the vulnerable code.
- Bandit gate stays at HIGH as planned, so B608 (MEDIUM) doesn't block. The failing authorization tests block the vulnerable build instead.
- Optional supply-chain attack and Experiments A and B: not done.
