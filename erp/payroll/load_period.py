#!/usr/bin/env python3
"""
load_period.py — load ONE reconciled payroll month into the ERP payroll schema.

Thin CLI wrapper around webui/ingest.py (the same code path the web 'Run
reconciliation' endpoint uses, so both stay in sync). Takes the per-employee
output of reconcile.py (same columns as ACTION_NEEDED_<Month>.csv / the full
monthly sheet) and lands it in the normalized Postgres schema.

Usage:
  pip install psycopg2-binary
  python load_period.py --csv <sheet>.csv --period 2026-04 --fy 2026-27 \
      --host <h> --port 5432 --user <u> --password <p> --dbname postgres \
      [--run-by dinesh] [--source-files "apr26 sheet + DELHI/STEAGE/DMART ECR"] \
      [--net-anchor 259937250]
"""
import argparse, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "webui"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--period", required=True, help="YYYY-MM, e.g. 2026-04")
    ap.add_argument("--fy", required=True, help="e.g. 2026-27")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", default="5432")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", default="")
    ap.add_argument("--dbname", default="postgres")
    ap.add_argument("--run-by", default=None)
    ap.add_argument("--source-files", default=None)
    ap.add_argument("--net-anchor", type=float, default=None)
    a = ap.parse_args()

    try:
        import psycopg2
        from ingest import read_rows, ingest_period
    except ImportError as e:
        sys.exit(f"Missing dependency ({e}). Install:  pip install psycopg2-binary")

    rows = read_rows(a.csv)
    if not rows:
        sys.exit(f"No data rows found in {a.csv}")
    print(f"Read {len(rows):,} rows from {a.csv}")

    conn = psycopg2.connect(host=a.host, port=a.port, user=a.user,
                            password=a.password, dbname=a.dbname)
    s = ingest_period(conn, a.period, a.fy, rows, run_by=a.run_by,
                      source_files=a.source_files, net_anchor=a.net_anchor)
    conn.close()

    c = s["checks"]
    print(f"\nLoaded period {s['period']} (run #{s['run_id']})")
    print(f"  payroll rows : {s['rows']:,}   employees: {s['employees']:,}   sites: {s['sites']:,}")
    print(f"  action items : {s['action_items']:,}")
    print(f"  Σ REVISED_PF : {s['sum_revised_pf']:>16,.0f}")
    print(f"  Σ ECR_PF     : {s['sum_ecr_pf']:>16,.0f}")
    print(f"  PF gap (R1)  : {s['pf_gap']:>16,.0f}   {'PASS' if c['rule1_pass'] else 'REVIEW'}")
    print(f"  Σ NET        : {s['sum_net_payable']:>16,.0f}")
    print(f"  Net drift(R3): {s['net_drift']:>16,.0f}   {'PASS' if c['rule3_pass'] else 'REVIEW'}")
    print("Done.")


if __name__ == "__main__":
    main()
