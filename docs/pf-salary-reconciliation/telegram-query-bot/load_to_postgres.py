#!/usr/bin/env python3
"""
Load ALL raw reconciled employee-rows (every month, key columns) into a Postgres
database (e.g. free Supabase) so a text-to-SQL bot can answer ANY question —
no pre-computed summary columns needed. Built for ad-hoc auditor queries.

USAGE (on the PC where the reconciled files live)
-------------------------------------------------
    pip install pandas openpyxl sqlalchemy psycopg2-binary

    python load_to_postgres.py ^
      --in "D:\\...\\ESI_WASHING_REALLOCATED" "D:\\...\\desktop salary folder" ^
      --fy 2025 ^
      --conn "postgresql://postgres:YOURPASSWORD@db.xxxx.supabase.co:5432/postgres"

It reads every *_M13_FINAL.xlsx / *_Final_Complete.xlsx, normalises a canonical
set of audit columns, adds a MONTH column, and writes them to table
`salary_rows` (replacing it each run — a full refresh). Then the n8n bot queries
that one table with SQL.

Nothing in your source files is modified.
"""
from __future__ import annotations
import argparse, calendar, os, re, sys
import pandas as pd

# ---- canonical audit schema: clean_name -> possible source column names ----
COLS = {
    "emp_code":                ["EMPCODE", "EMP CODE"],
    "emp_old_code":            ["EMPOLDCODE"],
    "emp_master_id":           ["EMPMASTERID"],
    "full_name":               ["FULLNAME", "FULL NAME"],
    "site_code":               ["SITECODE"],
    "site_name":               ["SITENAME"],
    "site_state":              ["SITESTATE", "STATE"],
    "branch_code":             ["BRANCHCODE"],
    "branch_name":             ["BRANCHNAME"],
    "client_group":            ["CLIENTGROUPNAME"],
    "normal_days":             ["NORMALDAYS", "NORMAL DAYS"],
    "adj_working_days":        ["ADJ_WORKING_DAYS"],
    "basic":                   ["BASIC"],
    "da":                      ["DA"],
    "gross_amt":               ["GROSS AMT", "GROSS"],
    "netpayable":              ["NETPAYABLE", "NET PAYABLE"],
    "ecr_pf":                  ["ECR_PF"],
    "revised_pf":              ["REVISED_PF"],
    "revised_basic":           ["REVISED_BASIC"],
    "revised_da":              ["REVISED_DA"],
    "revised_gross":           ["REVISED_GROSS"],
    "revised_esic":            ["REVISED_ESIC"],
    "future_esi":              ["Future_ESI", "FUTURE_ESI"],
    "revised_attendance_allow":["REVISED_ATTENDANCE_ALLOWANCE"],
    "revised_other_deduction": ["REVISED_OTHER_DEDUCTION"],
    "revised_total_ded":       ["REVISED_TOTAL_DED"],
    "revised_net_payable":     ["REVISED_NET_PAYABLE"],
    "monthly_bd_projection":   ["MONTHLY_BD_PROJECTION"],
    "monthly_gross_projection":["MONTHLY_GROSS_PROJECTION"],
    "rule_applied":            ["RULE_APPLIED"],
    "anomaly_below_ceiling":   ["ANOMALY_BELOW_CEILING"],
}
NUMERIC = {"normal_days","adj_working_days","basic","da","gross_amt","netpayable",
    "ecr_pf","revised_pf","revised_basic","revised_da","revised_gross","revised_esic",
    "future_esi","revised_attendance_allow","revised_other_deduction","revised_total_ded",
    "revised_net_payable","monthly_bd_projection","monthly_gross_projection"}

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1)}
FY_START = None


def _norm(s): return "".join(str(s).strip().upper().split())
def resolve(cols, names):
    lut = {_norm(c): c for c in cols}
    for n in names:
        if _norm(n) in lut: return lut[_norm(n)]
    return None


def month_label(path):
    base = os.path.basename(path)
    m = re.search(r"(20\d{2})[-_]?(0[1-9]|1[0-2])", base)
    if m: return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_ ]?(\d{2,4})", base, re.I)
    if m:
        yy = m.group(2); yy = ("20"+yy) if len(yy)==2 else yy
        return f"{yy}-{MONTHS[m.group(1).lower()[:3]]:02d}"
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)", base, re.I)
    if m and FY_START:
        mo = MONTHS[m.group(1).lower()[:3]]; return f"{FY_START if mo>=4 else FY_START+1}-{mo:02d}"
    return None


def is_final_file(path):
    b = os.path.basename(path).lower()
    if b.startswith("~$") or ".bak." in b or ".pre" in b: return False
    return b.endswith("_final_complete.xlsx") or b.endswith("_m13_final.xlsx")


def detect_header(path, maxscan=10):
    raw = pd.read_excel(path, header=None, nrows=maxscan)
    for i in range(len(raw)):
        cells = {_norm(c) for c in raw.iloc[i].tolist()}
        if "REVISED_PF" in cells and ("REVISED_BASIC" in cells or "EMPCODE" in cells):
            return i
    return None


def load_file(path):
    hdr = detect_header(path)
    df = pd.read_excel(path, header=hdr if hdr is not None else 0)
    out = pd.DataFrame()
    out["month"] = [month_label(path)] * len(df)
    for clean, names in COLS.items():
        src = resolve(df.columns, names)
        if src is None:
            out[clean] = pd.NA
        elif clean in NUMERIC:
            out[clean] = pd.to_numeric(df[src], errors="coerce")
        else:
            out[clean] = df[src].astype(str).str.strip()
    out["source_file"] = os.path.basename(path)
    return out


def main():
    global FY_START
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inputs", nargs="+", action="append", required=True)
    ap.add_argument("--fy", type=int, default=None)
    ap.add_argument("--conn", default=None, help="Full Postgres URI (or use the parts below)")
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", default="5432")
    ap.add_argument("--user", default="postgres")
    ap.add_argument("--password", default=None, help="DB password (special chars handled automatically)")
    ap.add_argument("--dbname", default="postgres")
    ap.add_argument("--table", default="salary_rows")
    a = ap.parse_args()
    a.inputs = [p for grp in a.inputs for p in grp]
    FY_START = a.fy

    files = []
    for p in a.inputs:
        if os.path.isdir(p):
            for root,_d,fs in os.walk(p):
                for f in fs:
                    if is_final_file(os.path.join(root,f)): files.append(os.path.join(root,f))
        elif os.path.isfile(p) and is_final_file(p):
            files.append(p)
    files = sorted(set(files))
    if not files:
        print("No reconciled FINAL files found."); sys.exit(1)

    print(f"Loading {len(files)} file(s)...")
    frames = []
    for f in files:
        try:
            fr = load_file(f)
            frames.append(fr)
            print(f"  {fr['month'].iloc[0]}: {len(fr):>6} rows  ({os.path.basename(f)})")
        except Exception as e:
            print(f"  !! skipped {os.path.basename(f)}: {e}")
    allrows = pd.concat(frames, ignore_index=True)
    print(f"\nTotal rows: {len(allrows):,}  columns: {len(allrows.columns)}")

    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import URL
    except ImportError:
        print("Missing libs. Run:  pip install sqlalchemy psycopg2-binary"); sys.exit(1)

    if a.password is not None and a.host:
        # build the URL from parts — SQLAlchemy percent-encodes the password for us
        url = URL.create("postgresql+psycopg2", username=a.user, password=a.password,
                         host=a.host, port=int(a.port), database=a.dbname)
        eng = create_engine(url)
    elif a.conn:
        eng = create_engine(a.conn)
    else:
        print("Provide either --conn \"postgresql://...\"  OR  --host --user --password."); sys.exit(1)
    print(f"Writing to table '{a.table}' (replace)...")
    allrows.to_sql(a.table, eng, if_exists="replace", index=False,
                   chunksize=1000, method="multi")
    with eng.begin() as c:
        c.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{a.table}_month ON {a.table}(month)'))
        c.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{a.table}_emp ON {a.table}(emp_code)'))
        n = c.execute(text(f'SELECT count(*) FROM {a.table}')).scalar()
    print(f"DONE — {n:,} rows now in '{a.table}'. The bot can query any question via SQL.")


if __name__ == "__main__":
    main()
