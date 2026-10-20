# Access control

- **Roles:** `cleaner` (ordinary), `manager` (privileged). `payroll` acts only through a job token.
- **Own:** the resource's cleaner equals the token `sub`.
- **Default:** anything not listed gets 401 or 403.

## Matrix

| Operation               | `api` endpoint                           | Internal endpoint               | anonymous | cleaner        | manager | payroll with job token                          |
| ----------------------- | ---------------------------------------- | ------------------------------- | --------- | -------------- | ------- | ----------------------------------------------- |
| Log in                  | `POST /login`                            | records `POST /login`           | yes       | yes            | yes     | no                                              |
| List jobs               | `GET /jobs`                              | records `GET /jobs`             | no        | own            | all     | no                                              |
| Search jobs by customer | `GET /jobs/search`                       | records `GET /jobs/search`      | no        | own            | all     | no                                              |
| Assign job              | `POST /jobs`                             | records `POST /jobs`            | no        | no             | yes     | no                                              |
| Clock in / out          | `POST /jobs/{id}/clock-in`, `/clock-out` | same on records                 | no        | own job        | no      | no                                              |
| Start payslip job       | `POST /payslips`                         | payroll `POST /jobs`            | no        | own, one month | no      | no                                              |
| Read entries and rate   | none                                     | records `GET /entries?month=`   | no        | no             | no      | token `sub` and `month`, scope `entries:read`   |
| Store payslip           | none                                     | records `PUT /payslips/{month}` | no        | no             | no      | token `sub` and `month`, scope `payslips:write` |
| Download payslip        | `GET /payslips?file=`                    | records `GET /payslips?file=`   | no        | own            | no      | no                                              |
| All hours and payslips  | `GET /manager/overview`                  | records `GET /overview`         | no        | no             | yes     | no                                              |

Two changes from the plan: download takes `?file=` instead of a path segment, and the overview is `/overview` in `records`. See "Changes during development" in [PLAN.md](PLAN.md).

## Where it's enforced

`records` owns the data, so it checks every rule. `api` repeats the role checks so a cleaner is refused before any internal call.

| Rule                                 | `api`                                                                     | `records`                                                                    | Test                                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Valid token required                 | `current_user`, `api/app.py:25`                                           | `claims`, `records/app.py:60`                                                | `test_no_token_is_rejected`                                                                          |
| Manager only                         | `require_role(user, "manager")`, `api/app.py:94`, `:147`                  | `manager`, `records/app.py:78`                                               | `test_cleaner_cannot_call_manager_endpoints`                                                         |
| Cleaner only                         | `require_role(user, "cleaner")`, `api/app.py:101`, `:108`, `:121`, `:139` | `cleaner`, `records/app.py:84`                                               | `test_clock_in_and_out`                                                                              |
| Own jobs only                        |                                                                           | `WHERE cleaner = ?` in `list_jobs` / `search_jobs`, `records/app.py:128-145` | `test_cleaner_lists_own_jobs`, `test_cleaner_cannot_see_other_cleaners_jobs`                         |
| Own job for clocking                 |                                                                           | `own_job`, `records/app.py:165`                                              | `test_cleaner_cannot_clock_in_on_other_cleaners_job`                                                 |
| Own payslip file                     |                                                                           | folder from token `sub`, path kept inside it, `records/app.py:235-239`       | `test_cleaner_cannot_download_other_cleaners_payslip`, `tests/exploits/test_cwe22_path_traversal.py` |
| User tokens stay off job endpoints   |                                                                           | no `scope` in a records token, `records/app.py:90`                           | `test_records_rejects_missing_scope`                                                                 |
| Job tokens stay off user endpoints   |                                                                           | `user` requires a role, `records/app.py:71`                                  | `test_job_token_cannot_use_user_endpoints`                                                           |
| Job token scope and month            |                                                                           | `job_token`, `records/app.py:90-94`                                          | `test_records_rejects_missing_scope`, `test_payroll_cannot_write_other_month`                        |
| Cleaner of a job from the token only | job token `sub` from the JWT, `api/app.py:125-131`                        | `who = c["sub"]`, `records/app.py:212`, `:224`                               | `test_payroll_cannot_act_for_other_cleaner`, `test_api_ignores_cleaner_in_payslip_request`           |

Tests are in `tests/test_authz.py` unless a path is given. All pass on `v2-fixed` (`evidence/v2-fixed/junit.xml`).
