#!/usr/bin/env python3
"""
load_maharashtra_to_postgres.py — load the Maharashtra FY2024-25 reconciled dataset
into the SAME Supabase/Postgres that holds the 25-26 data, so it is queryable alongside it.

Run this in the session/machine that already connects to your Supabase (the 25-26 loader works
there). It creates table `maharashtra_salary_2024_25` and bulk-loads
`maharashtra_salary_2024_25.csv` (21,551 rows, PF + ESI per employee-month).

Usage:
  pip install psycopg2-binary pandas
  python load_maharashtra_to_postgres.py \
      --csv maharashtra_salary_2024_25.csv \
      --host aws-1-ap-northeast-2.pooler.supabase.com --port 5432 \
      --user postgres.rgfhqghwkiqwhwxjatsc --password IsplSalary2026 --dbname postgres

Idempotent: drops & recreates the table each run (safe to re-load).
"""
import argparse, csv, io, sys

DDL = """
DROP TABLE IF EXISTS maharashtra_salary_2024_25;
CREATE TABLE maharashtra_salary_2024_25 (
    month                  text,
    fy                     text,
    emp_code               text,
    name                   text,
    designation            text,
    epf_no                 text,
    uan_no                 text,
    site_name              text,
    branch                 text,
    month_days             numeric,
    worked_days            numeric,
    ncp                    numeric,
    orig_basic_da          numeric,
    gross                  numeric,
    orig_pf                numeric,
    ecr_pf_filed           numeric,
    ecr_pf_capped          numeric,
    pf_above_1800_surplus  numeric,
    pf_source              text,
    pf_rule                text,
    revised_pf             numeric,
    revised_basic_da       numeric,
    adj_working_days       numeric,
    pf_diff_parked         numeric,
    bd_monthly_projection  numeric,
    esic_wages             numeric,
    esi_emp                numeric,
    esi_co                 numeric,
    esi_total              numeric,
    esi_above_21000        text,
    esi_status             text
);
CREATE INDEX IF NOT EXISTS idx_mh2425_emp   ON maharashtra_salary_2024_25 (emp_code);
CREATE INDEX IF NOT EXISTS idx_mh2425_month ON maharashtra_salary_2024_25 (month);
CREATE INDEX IF NOT EXISTS idx_mh2425_branch ON maharashtra_salary_2024_25 (branch);
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="maharashtra_salary_2024_25.csv")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", default="5432")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--dbname", default="postgres")
    ap.add_argument("--table", default="maharashtra_salary_2024_25")
    a = ap.parse_args()

    try:
        import psycopg2
    except ImportError:
        sys.exit("Install psycopg2 first:  pip install psycopg2-binary")

    conn = psycopg2.connect(host=a.host, port=a.port, user=a.user,
                            password=a.password, dbname=a.dbname)
    conn.autocommit = False
    cur = conn.cursor()

    ddl = DDL.replace("maharashtra_salary_2024_25", a.table)
    cur.execute(ddl)

    # stream the CSV in with COPY (fast). Empty strings -> NULL for numeric columns.
    with open(a.csv, newline="", encoding="utf-8") as f:
        header = f.readline().rstrip("\n")
        cols = header.split(",")
        buf = io.StringIO()
        w = csv.writer(buf)
        rdr = csv.reader(f)
        n = 0
        for row in rdr:
            row = [("" if c == "" else c) for c in row]
            w.writerow(row); n += 1
        buf.seek(0)
        cur.copy_expert(
            f"COPY {a.table} ({','.join(cols)}) FROM STDIN WITH (FORMAT csv, NULL '')",
            buf)
    conn.commit()

    cur.execute(f"SELECT count(*), count(distinct emp_code), count(distinct month) FROM {a.table};")
    rows, emps, months = cur.fetchone()
    print(f"Loaded {rows} rows into '{a.table}'  ({emps} employees, {months} months).")
    cur.execute(f"SELECT round(sum(revised_pf))::bigint, round(sum(esi_emp))::bigint FROM {a.table};")
    pf, esi = cur.fetchone()
    print(f"  Sum revised PF = {pf:,}   Sum ESI employee = {esi:,}")
    cur.close(); conn.close()
    print("Done. Table 'maharashtra_salary_2024_25' is now queryable alongside your 25-26 data.")

if __name__ == "__main__":
    main()
