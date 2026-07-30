#!/usr/bin/env python3
"""
manage_users.py — create and manage ISPL Payroll application users.

Auth uses a salted password hash (Werkzeug's pbkdf2); plaintext passwords are
never stored. Run against the same Postgres as the web app.

  export ERP_DB="host=<h> user=<u> password=<p> dbname=postgres"

  python manage_users.py add   dinesh --role admin    --name "Dinesh Sharma"
  python manage_users.py add   asha   --role approver  --name "Asha"
  python manage_users.py passwd dinesh                 # prompt for new password
  python manage_users.py role  asha  viewer            # change role
  python manage_users.py disable asha                  # deactivate (keeps history)
  python manage_users.py list

Passwords are read from the ERP_USER_PW env var if set, else prompted (hidden),
so they never land in shell history.
"""
import argparse, getpass, os, sys
import psycopg2
from werkzeug.security import generate_password_hash

DSN = os.environ.get("ERP_DB", "host=/tmp/pgs user=postgres dbname=erp")
ROLES = ("viewer", "clerk", "approver", "admin")


def conn():
    return psycopg2.connect(DSN)


def get_pw():
    pw = os.environ.get("ERP_USER_PW")
    if pw:
        return pw
    pw = getpass.getpass("New password: ")
    if pw != getpass.getpass("Confirm: "):
        sys.exit("Passwords do not match.")
    if len(pw) < 6:
        sys.exit("Password too short (min 6 chars).")
    return pw


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("username"); a.add_argument("--role", default="viewer", choices=ROLES); a.add_argument("--name", default=None)
    p = sub.add_parser("passwd"); p.add_argument("username")
    r = sub.add_parser("role"); r.add_argument("username"); r.add_argument("role", choices=ROLES)
    d = sub.add_parser("disable"); d.add_argument("username")
    e = sub.add_parser("enable"); e.add_argument("username")
    sub.add_parser("list")
    args = ap.parse_args()

    c = conn(); c.autocommit = True; cur = c.cursor()

    if args.cmd == "add":
        cur.execute(
            "INSERT INTO app_user (username, password_hash, full_name, role) VALUES (%s,%s,%s,%s) "
            "ON CONFLICT (username) DO NOTHING RETURNING id",
            (args.username, generate_password_hash(get_pw()), args.name, args.role))
        print(f"Added {args.username} ({args.role})" if cur.fetchone() else f"User {args.username} already exists.")
    elif args.cmd == "passwd":
        cur.execute("UPDATE app_user SET password_hash=%s WHERE username=%s",
                    (generate_password_hash(get_pw()), args.username))
        print("Password updated." if cur.rowcount else "No such user.")
    elif args.cmd == "role":
        cur.execute("UPDATE app_user SET role=%s WHERE username=%s", (args.role, args.username))
        print(f"{args.username} → {args.role}" if cur.rowcount else "No such user.")
    elif args.cmd in ("disable", "enable"):
        cur.execute("UPDATE app_user SET active=%s WHERE username=%s", (args.cmd == "enable", args.username))
        print(f"{args.username} {'enabled' if args.cmd=='enable' else 'disabled'}" if cur.rowcount else "No such user.")
    elif args.cmd == "list":
        cur.execute("SELECT username, role, active, coalesce(full_name,'') FROM app_user ORDER BY role, username")
        rows = cur.fetchall()
        if not rows:
            print("No users yet. Add one:  python manage_users.py add <name> --role admin")
        for u, role, active, name in rows:
            print(f"  {u:16} {role:9} {'active' if active else 'DISABLED':9} {name}")
    c.close()


if __name__ == "__main__":
    main()
