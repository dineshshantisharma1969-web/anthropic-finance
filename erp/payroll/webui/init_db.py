#!/usr/bin/env python3
"""
init_db.py — one-time setup: create the payroll schema and a first admin user.

Run this once against your database before starting the app. Safe to re-run
(the schema uses IF NOT EXISTS; the admin is only created if missing).

  export ERP_DB="host=<h> port=5432 user=<u> password=<p> dbname=postgres"
  python init_db.py

It reads schema.sql from ../schema.sql, applies it, then ensures one admin user
exists (username/password from ERP_ADMIN_USER / ERP_ADMIN_PW, else prompted).
"""
import os, sys, getpass
import psycopg2
from werkzeug.security import generate_password_hash

DSN = os.environ.get("ERP_DB", "host=/tmp/pgs user=postgres dbname=erp")
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schema.sql")


def main():
    if not os.path.exists(SCHEMA):
        sys.exit(f"schema.sql not found at {SCHEMA}")
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()

    print("Applying schema…")
    with open(SCHEMA) as f:
        cur.execute(f.read())
    print("  schema applied.")

    cur.execute("SELECT count(*) FROM app_user WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        print("\nNo admin user yet — let's create one.")
        user = os.environ.get("ERP_ADMIN_USER") or input("  Admin username: ").strip()
        pw = os.environ.get("ERP_ADMIN_PW")
        if not pw:
            pw = getpass.getpass("  Admin password: ")
            if pw != getpass.getpass("  Confirm password: "):
                sys.exit("Passwords do not match.")
        if len(pw) < 6:
            sys.exit("Password too short (min 6 chars).")
        cur.execute(
            "INSERT INTO app_user (username, password_hash, full_name, role) VALUES (%s,%s,%s,'admin')",
            (user, generate_password_hash(pw), user))
        print(f"  admin '{user}' created.")
    else:
        print("\nAdmin user already exists — skipping.")

    conn.close()
    print("\nDone. Start the app with:  python app.py   (then open http://127.0.0.1:8000)")


if __name__ == "__main__":
    main()
