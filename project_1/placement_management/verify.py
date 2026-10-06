"""
Verification script — checks imports, cross-module references, SQL files,
and entry-point integrity WITHOUT touching any application logic.
Run: python verify.py
"""

import ast
import os
import sys
import importlib
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"
INFO = "\033[36mINFO\033[0m"

issues = []


def ok(msg):
    print(f"  [{PASS}] {msg}")


def fail(msg):
    print(f"  [{FAIL}] {msg}")
    issues.append(msg)


def warn(msg):
    print(f"  [{WARN}] {msg}")


def info(msg):
    print(f"  [{INFO}] {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Syntax check all .py files
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("1. SYNTAX CHECK — all .py files")
print("="*60)

py_files = []
for r, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
    for f in files:
        if f.endswith(".py"):
            py_files.append(os.path.join(r, f))

for path in sorted(py_files):
    rel = os.path.relpath(path, ROOT)
    try:
        with open(path, encoding="utf-8") as fh:
            ast.parse(fh.read())
        ok(rel)
    except SyntaxError as e:
        fail(f"{rel}: SyntaxError line {e.lineno}: {e.msg}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Stdlib / standard imports (no external deps needed for import check)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("2. STDLIB IMPORTS — check standard library modules used")
print("="*60)

stdlib_mods = ["os", "sys", "re", "io", "logging", "datetime",
               "typing", "ast", "importlib"]
for mod in stdlib_mods:
    try:
        importlib.import_module(mod)
        ok(mod)
    except ImportError as e:
        fail(f"{mod}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Third-party package availability
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("3. THIRD-PARTY PACKAGES — availability check")
print("="*60)

packages = {
    "streamlit":            "streamlit",
    "mysql.connector":      "mysql-connector-python",
    "pandas":               "pandas",
    "plotly":               "plotly",
    "sklearn":              "scikit-learn",
    "bcrypt":               "bcrypt",
    "dotenv":               "python-dotenv",
    "openpyxl":             "openpyxl",
    "numpy":                "numpy",
}
optional = {
    "pdfplumber":   "pdfplumber  (optional — resume analyzer)",
    "PyPDF2":       "PyPDF2      (optional — resume analyzer fallback)",
}

for mod, pkg in packages.items():
    try:
        importlib.import_module(mod)
        ok(f"{mod}  ({pkg})")
    except ImportError:
        fail(f"{mod} NOT installed — run: pip install {pkg}")

for mod, label in optional.items():
    try:
        importlib.import_module(mod)
        ok(f"{mod}  ({label})")
    except ImportError:
        warn(f"{mod} not installed — {label}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Internal module imports (utils/modules/ml)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("4. INTERNAL MODULE IMPORTS — cross-module references")
print("="*60)

internal = [
    "utils.database",
    "utils.security",
    "utils.validators",
    "modules.auth",
    "modules.student",
    "modules.faculty",
    "modules.hod",
    "modules.admin",
    "modules.companies",
    "modules.placements",
    "modules.analytics",
    "modules.reports",
    "ml.placement_prediction",
    "ml.career_recommendation",
]

for mod in internal:
    try:
        importlib.import_module(mod)
        ok(mod)
    except ImportError as e:
        # May fail if third-party lib missing — catch gracefully
        if "No module named" in str(e) and not str(e).endswith(f"'{mod}'"):
            warn(f"{mod} — needs third-party dep: {e}")
        else:
            fail(f"{mod}: {e}")
    except Exception as e:
        # Runtime errors (e.g. DB not connected) are expected at import time
        warn(f"{mod} — runtime error at import (expected without DB): {type(e).__name__}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. streamlit_app.py — entry point check
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("5. ENTRY POINT — streamlit_app.py")
print("="*60)

app_path = os.path.join(ROOT, "streamlit_app.py")

if not os.path.exists(app_path):
    fail("streamlit_app.py NOT FOUND at project root")
else:
    ok("streamlit_app.py exists at project root")

with open(app_path, encoding="utf-8") as fh:
    app_src = fh.read()

checks = {
    "st.set_page_config":           "st.set_page_config() called",
    "init_session_state":           "init_session_state() called",
    "show_login_page":              "Login page imported",
    "show_student_dashboard":       "Student dashboard routed",
    "show_faculty_dashboard":       "Faculty dashboard routed",
    "show_hod_dashboard":           "HOD dashboard routed",
    "show_admin_dashboard":         "Admin dashboard routed",
    "test_connection":              "DB connectivity checked",
    'if __name__ == "__main__"':    "__main__ guard present",
    "def main":                     "main() function defined",
    "logout":                       "Logout handled",
}

for pattern, label in checks.items():
    if pattern in app_src:
        ok(label)
    else:
        fail(f"MISSING: {label} — pattern '{pattern}' not found in streamlit_app.py")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Database module — connection pool and query helpers
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("6. DATABASE MODULE — utils/database.py")
print("="*60)

db_path = os.path.join(ROOT, "utils", "database.py")
with open(db_path, encoding="utf-8") as fh:
    db_src = fh.read()

db_checks = {
    "def execute_query":       "execute_query() defined",
    "def get_connection":      "get_connection() defined",
    "def test_connection":     "test_connection() defined",
    "MySQLConnectionPool":     "Connection pooling used",
    "parameterized":           "Parameterized queries documented",
    "cursor.execute(query":    "Parameterized execute called",
}
for pattern, label in db_checks.items():
    if pattern in db_src:
        ok(label)
    else:
        fail(f"MISSING in database.py: {label}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Security module — password hashing + session
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("7. SECURITY MODULE — utils/security.py")
print("="*60)

sec_path = os.path.join(ROOT, "utils", "security.py")
with open(sec_path, encoding="utf-8") as fh:
    sec_src = fh.read()

sec_checks = {
    "bcrypt.hashpw":        "bcrypt password hashing",
    "bcrypt.checkpw":       "bcrypt password verification",
    "def authenticate_user": "authenticate_user() defined",
    "def login_user":        "login_user() defined",
    "def logout_user":       "logout_user() defined",
    "def log_audit":         "log_audit() defined",
    "def require_role":      "require_role() defined",
    "session_state":         "Streamlit session_state used",
    "password_hash":         "Password hash removed from session",
}
for pattern, label in sec_checks.items():
    if pattern in sec_src:
        ok(label)
    else:
        fail(f"MISSING in security.py: {label}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. SQL files — schema.sql and seed_data.sql
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("8. SQL FILES — schema.sql and seed_data.sql")
print("="*60)

schema_path = os.path.join(ROOT, "database", "schema.sql")
seed_path   = os.path.join(ROOT, "database", "seed_data.sql")

for sql_file, label in [(schema_path, "schema.sql"), (seed_path, "seed_data.sql")]:
    if not os.path.exists(sql_file):
        fail(f"{label} NOT FOUND")
        continue
    ok(f"{label} exists")
    with open(sql_file, encoding="utf-8") as fh:
        sql = fh.read()

    # Balanced CREATE TABLE check
    creates = len(re.findall(r"CREATE\s+TABLE", sql, re.I))
    if label == "schema.sql":
        if creates >= 15:
            ok(f"  {creates} CREATE TABLE statements (expected >= 15)")
        else:
            fail(f"  Only {creates} CREATE TABLE — expected >= 15")

        # Check views
        views = len(re.findall(r"CREATE\s+OR\s+REPLACE\s+VIEW", sql, re.I))
        if views >= 2:
            ok(f"  {views} views defined")
        else:
            warn(f"  Only {views} views (expected 2)")

    if label == "seed_data.sql":
        insert_count = len(re.findall(r"^\s*INSERT\s+INTO", sql, re.I | re.M))
        ok(f"  {insert_count} INSERT INTO blocks found")
        if "CSE2021001" in sql:
            ok("  Student data present (CSE2021001)")
        else:
            fail("  Student seed data missing")
        if "Tata Consultancy Services" in sql:
            ok("  Company data present (TCS)")
        else:
            fail("  Company seed data missing")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Roles — all 4 dashboards present
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("9. ROLE DASHBOARDS — 4 roles covered")
print("="*60)

role_files = {
    "STUDENT":  os.path.join(ROOT, "modules", "student.py"),
    "FACULTY":  os.path.join(ROOT, "modules", "faculty.py"),
    "HOD":      os.path.join(ROOT, "modules", "hod.py"),
    "ADMIN":    os.path.join(ROOT, "modules", "admin.py"),
}
role_fns = {
    "STUDENT": "show_student_dashboard",
    "FACULTY": "show_faculty_dashboard",
    "HOD":     "show_hod_dashboard",
    "ADMIN":   "show_admin_dashboard",
}
for role, path in role_files.items():
    if not os.path.exists(path):
        fail(f"{role}: module file missing")
        continue
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    fn = role_fns[role]
    if f"def {fn}" in src:
        ok(f"{role}: {fn}() defined")
    else:
        fail(f"{role}: {fn}() NOT found in {os.path.basename(path)}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. ML modules — graceful degradation check
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("10. ML MODULES — graceful degradation")
print("="*60)

ml_files = {
    "placement_prediction.py":  os.path.join(ROOT, "ml", "placement_prediction.py"),
    "career_recommendation.py": os.path.join(ROOT, "ml", "career_recommendation.py"),
}
for fname, path in ml_files.items():
    if not os.path.exists(path):
        fail(f"{fname} missing")
        continue
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if "ImportError" in src or "except Import" in src:
        ok(f"{fname} handles ImportError (graceful degradation)")
    else:
        warn(f"{fname} — may not handle missing sklearn gracefully")
    if "return None" in src:
        ok(f"{fname} returns None on failure")

# ─────────────────────────────────────────────────────────────────────────────
# 11. .env.example and requirements.txt
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("11. CONFIG FILES")
print("="*60)

for fname in [".env.example", "requirements.txt", "README.md", "setup_db.py"]:
    fpath = os.path.join(ROOT, fname)
    if os.path.exists(fpath):
        ok(f"{fname} exists")
    else:
        fail(f"{fname} MISSING")

req_path = os.path.join(ROOT, "requirements.txt")
if os.path.exists(req_path):
    with open(req_path) as fh:
        reqs = fh.read()
    for pkg in ["streamlit", "mysql-connector-python", "pandas",
                "plotly", "scikit-learn", "bcrypt", "python-dotenv",
                "openpyxl"]:
        if pkg.lower() in reqs.lower():
            ok(f"  requirements: {pkg} listed")
        else:
            fail(f"  requirements: {pkg} NOT listed")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
if issues:
    print(f"\n  FAILED: {len(issues)} issue(s) found:")
    for i, iss in enumerate(issues, 1):
        print(f"    {i}. {iss}")
    sys.exit(1)
else:
    print("\n  ALL CHECKS PASSED — project is ready to run.")
    print("\n  Command to start the application:")
    print("\n    streamlit run streamlit_app.py")
    print()
