#!/usr/bin/env python3
"""
Quick query tool for the salary_rows database (proves the ask-anything DB works
without needing the Telegram bot). Runs a few demo auditor-style queries, and
lets you run your own SQL with --sql "SELECT ...".

  python query_db.py --host ... --user ... --password ...
  python query_db.py --host ... --user ... --password ... --sql "SELECT count(*) FROM salary_rows"
"""
import argparse, sys

DEMOS = [
    ("Employees below Rs15,000 (BASIC+DA) with NO PF — per month (live from raw rows)",
     """SELECT month, count(*) AS employees
        FROM (SELECT emp_code, month FROM salary_rows
              GROUP BY emp_code, month
              HAVING sum(coalesce(revised_pf,0))=0
                 AND sum(coalesce(revised_basic,0)+coalesce(revised_da,0))<15000) t
        GROUP BY month ORDER BY month"""),
    ("Total reconciled PF (Rs) per month",
     "SELECT month, round(sum(coalesce(revised_pf,0))) AS pf FROM salary_rows GROUP BY month ORDER BY month"),
    ("Top 8 states by employee-rows (Apr-2025)",
     """SELECT coalesce(site_state,'(blank)') AS state, count(*) AS rows
        FROM salary_rows WHERE month='2025-04'
        GROUP BY site_state ORDER BY rows DESC LIMIT 8"""),
]


def run(cur, title, sql):
    print("\n" + "=" * 70 + f"\n{title}\n" + "-" * 70)
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    for r in cur.fetchall():
        print(" | ".join(str(x) for x in r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", default="5432")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--dbname", default="postgres")
    ap.add_argument("--sql", default=None, help="run your own SQL instead of the demos")
    a = ap.parse_args()
    try:
        import psycopg2
    except ImportError:
        print("Run:  pip install psycopg2-binary"); sys.exit(1)

    c = psycopg2.connect(host=a.host, port=int(a.port), user=a.user,
                         password=a.password, dbname=a.dbname)
    cur = c.cursor()
    if a.sql:
        run(cur, "Your query", a.sql)
    else:
        for title, sql in DEMOS:
            run(cur, title, sql)
        print("\n" + "=" * 70)
        print("Your database works! Run your own question with:  --sql \"SELECT ...\"")
    c.close()


if __name__ == "__main__":
    main()
