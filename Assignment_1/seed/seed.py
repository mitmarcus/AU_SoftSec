# Run inside the records container: make seed
# Wipes the database and payslips and inserts the test data.
import shutil

import bcrypt
from app import PAYSLIP_DIR, db, init_db

USERS = [
    ("iza", "iza-pass", "cleaner", 180.0),
    ("marius", "marius-pass", "cleaner", 210.0),
    ("andreea", "andreea-pass", "manager", None),
]

# (customer, address, date, cleaner)
JOBS = [
    ("Hansen", "Nordre Ringgade 1, Aarhus C", "2026-09-01", "iza"),
    ("Jensen", "Vestergade 12, Aarhus C", "2026-09-05", "iza"),
    ("Nielsen Kontor", "Aaboulevarden 3, Aarhus C", "2026-09-02", "marius"),
    ("Pedersen", "Frederiks Alle 20, Aarhus C", "2026-09-06", "marius"),
]

# (job id, start, end)
ENTRIES = [
    (1, "2026-09-01T08:00:00", "2026-09-01T12:00:00"),
    (2, "2026-09-05T10:00:00", "2026-09-05T13:30:00"),
    (3, "2026-09-02T18:00:00", "2026-09-02T22:00:00"),
    (4, "2026-09-06T09:00:00", "2026-09-06T15:00:00"),
]

shutil.rmtree(PAYSLIP_DIR, ignore_errors=True)
init_db()
with db() as conn:
    conn.execute("DELETE FROM entries")
    conn.execute("DELETE FROM jobs")
    conn.execute("DELETE FROM users")
    for username, password, role, rate in USERS:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, hashed, role, rate))
    for i, job in enumerate(JOBS, start=1):
        conn.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?)", (i, *job))
    for job_id, start, end in ENTRIES:
        cleaner = JOBS[job_id - 1][3]
        conn.execute("INSERT INTO entries (job_id, cleaner, start_time, end_time) VALUES (?, ?, ?, ?)",
                     (job_id, cleaner, start, end))

print("seeded", len(USERS), "users,", len(JOBS), "jobs,", len(ENTRIES), "entries")
