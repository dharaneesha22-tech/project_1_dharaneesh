"""
Database setup helper script.
Runs schema.sql, then seed_data.sql, then updates all user passwords
with properly generated bcrypt hashes.

Usage:
    python setup_db.py

Requirements: .env file must be configured first.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()

import mysql.connector
from mysql.connector import Error
import bcrypt


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}

DB_NAME = os.getenv("DB_NAME", "placement_management")


def run_sql_file(cursor, filepath: str):
    """Execute a SQL file statement by statement, skipping USE and CREATE DATABASE."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Remove single-line comments
    import re
    content = re.sub(r'--[^\n]*', '', content)
    # Remove block comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Split on semicolons, filter empty/whitespace-only
    statements = [s.strip() for s in content.split(";")]
    for stmt in statements:
        if not stmt:
            continue
        # Skip database-level statements (already handled)
        upper = stmt.upper().lstrip()
        if upper.startswith("CREATE DATABASE") or upper.startswith("USE "):
            continue
        try:
            cursor.execute(stmt)
        except Error as e:
            # Ignore benign errors: duplicate entry, column exists, table exists
            if e.errno in (1062, 1060, 1050, 1061, 1091):
                pass
            else:
                print(f"  Warning [{e.errno}]: {e.msg[:120]}")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def setup():
    print("=== College Smart Placement Management System Setup ===\n")

    # Connect without DB first to create it
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        cursor = conn.cursor()
        print(f"[1/5] Creating database '{DB_NAME}'...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("      Done.")
    except Error as e:
        print(f"ERROR: Cannot connect to MySQL: {e}")
        print("Check your .env file and ensure MySQL is running.")
        sys.exit(1)

    # Connect to the new DB
    conn = mysql.connector.connect(**DB_CONFIG, database=DB_NAME)
    conn.autocommit = False
    cursor = conn.cursor()

    # Run schema
    schema_path = os.path.join(ROOT, "database", "schema.sql")
    print("[2/5] Running schema.sql...")
    run_sql_file(cursor, schema_path)
    conn.commit()
    print("      Done.")

    # Run seed data
    seed_path = os.path.join(ROOT, "database", "seed_data.sql")
    print("[3/5] Running seed_data.sql...")
    run_sql_file(cursor, seed_path)
    conn.commit()
    print("      Done.")

    # Update passwords with real bcrypt hashes
    print("[4/5] Hashing passwords...")
    password_map = {
        "admin":         "Admin@123",
        "hod_cse":       "Hod@123",
        "hod_it":        "Hod@123",
        "hod_bca":       "Hod@123",
        "hod_bscs":      "Hod@123",
        "faculty_cse1":  "Faculty@123",
        "faculty_cse2":  "Faculty@123",
        "faculty_it1":   "Faculty@123",
        "faculty_bca1":  "Faculty@123",
        "CSE2021001":    "Student@123",
        "CSE2021002":    "Student@123",
    }

    for username, password in password_map.items():
        hashed = hash_password(password)
        cursor.execute(
            "UPDATE users SET password_hash=%s WHERE username=%s",
            (hashed, username),
        )
    conn.commit()
    print(f"      Updated {len(password_map)} user passwords.")

    # Update remaining student passwords in bulk
    print("      Hashing remaining student passwords...")
    student_hash = hash_password("Student@123")
    cursor.execute(
        """
        UPDATE users u
        JOIN roles r ON u.role_id = r.id
        SET u.password_hash = %s
        WHERE r.name = 'STUDENT'
          AND u.username NOT IN (%s, %s)
        """,
        (student_hash, "CSE2021001", "CSE2021002"),
    )
    conn.commit()
    print("      Done.")

    cursor.close()
    conn.close()

    print("\n[5/5] Setup complete!")
    print("\n" + "=" * 55)
    print("  Sample Login Credentials")
    print("=" * 55)
    print(f"  Admin:    admin       / Admin@123")
    print(f"  HOD CSE:  hod_cse    / Hod@123")
    print(f"  Faculty:  faculty_cse1 / Faculty@123")
    print(f"  Student:  CSE2021001  / Student@123")
    print("=" * 55)
    print("\nRun the app with:")
    print("  streamlit run streamlit_app.py")


if __name__ == "__main__":
    setup()
