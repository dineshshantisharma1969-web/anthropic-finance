#!/usr/bin/env python3
"""
Build a COMPACT month-wise "exceptions & counts" summary from the reconciled
*_Final_Complete.xlsx files, so a Telegram/n8n bot can answer questions like:

    "How many employees have BASIC+DA < 15000 but ECR PF = 0, for any month?"

WHY THIS EXISTS
---------------
The full reconciled files are 18-20 MB with ~21,000 rows each. A chat bot cannot
scan those per message. This script reads them ONCE and writes a tiny table
(one row per month, ~10 columns) that a bot can read instantly from a Google
Sheet or CSV.

The headline metric `EMP_BD_LT_15000_AND_NO_PF` is exactly the reconcile.py
`ANOMALY_BELOW_CEILING` PF-branch: employees whose pay is below the PF ceiling
(BASIC+DA < 15,000) yet who have no ECR PF (ECR_PF = 0) that month.

USAGE (run on the PC where the reconciled files live)
-----------------------------------------------------
    python build_exceptions_summary.py --in "D:\\path\\to\\folder-with-Final_Complete-files" ...
    # you can pass several --in folders (e.g. FY25-26 folder + April-26 folder)

    # then it writes:  Salary_Exceptions_Summary.csv  and  .xlsx  (both tiny)

It auto-finds every "*_Final_Complete.xlsx" under each --in folder and derives
the month label from the file name. Nothing is changed in your source files.
"""
from __future__ import annotations
import argparse, glob, os, re, sys
import pandas as pd

BD_CEILING = 15000.0  # PF wage ceiling (BASIC+DA)

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1)}


def _norm(s):
    return "".join(str(s).strip().upper().split())


def resolve(df, *names):
    """Find a column by any of its possible names (case/space-insensitive)."""
    lut = {_norm(c): c for c in df.columns}
    for n in names:
        if _norm(n) in lut:
            return lut[_norm(n)]
    return None


def month_label(path):
    """Best-effort 'YYYY-MM'/'Mon-YY' label from a file name."""
    base = os.path.basename(path)
    # e.g. April26, Apr-25, 2026-04, Oct_25 ...
    m = re.search(r"(20\d{2})[-_]?(0[1-9]|1[0-2])", base)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_ ]?(\d{2,4})", base, re.I)
    if m:
        yy = m.group(2)
        yy = ("20" + yy) if len(yy) == 2 else yy
        return f"{yy}-{MONTHS[m.group(1).lower()[:3]]:02d}"
    return base.replace("_Final_Complete.xlsx", "")


def analyse(path):
    df = pd.read_excel(path)
    emp = resolve(df, "EMPCODE", "EMP CODE")
    rpf = resolve(df, "REVISED_PF")
    rb  = resolve(df, "REVISED_BASIC")
    rd  = resolve(df, "REVISED_DA")
    anom = resolve(df, "ANOMALY_BELOW_CEILING")
    net = resolve(df, "REVISED_NET_PAYABLE")
    resi = resolve(df, "REVISED_ESIC")
    if not (emp and rpf and rb and rd):
        print(f"  !! skipped {os.path.basename(path)} — missing required columns")
        return None

    df["_EMP"] = df[emp].astype(str).str.strip().str.split(".").str[0]
    df["_PF"]  = pd.to_numeric(df[rpf], errors="coerce").fillna(0.0)
    df["_BD"]  = (pd.to_numeric(df[rb], errors="coerce").fillna(0.0)
                  + pd.to_numeric(df[rd], errors="coerce").fillna(0.0))

    # per-EMPLOYEE roll-up (an employee may have several site rows)
    g = df.groupby("_EMP").agg(pf=("_PF", "sum"), bd=("_BD", "sum"))
    no_pf = g["pf"] <= 0.5
    below = (g["bd"] > 0) & (g["bd"] < BD_CEILING)

    # headline metric — the user's exact question
    emp_bd_lt_ceiling_no_pf = int((no_pf & below).sum())

    # native reconcile.py metric (row-level flag, unique employees) for cross-check
    native_anom = None
    if anom:
        flag = df[anom].astype(str).str.upper().isin(["TRUE", "1", "1.0", "YES"])
        native_anom = int(df.loc[flag, "_EMP"].nunique())

    return {
        "MONTH": month_label(path),
        "TOTAL_EMPLOYEES": int(g.shape[0]),
        "EMP_BD_LT_15000_AND_NO_PF": emp_bd_lt_ceiling_no_pf,
        "ANOMALY_BELOW_CEILING_native": native_anom if native_anom is not None else "",
        "EMP_WITH_PF": int((~no_pf).sum()),
        "EMP_NO_PF": int(no_pf.sum()),
        "REVISED_PF_TOTAL": round(float(df["_PF"].sum())),
        "REVISED_ESIC_TOTAL": round(float(pd.to_numeric(df[resi], errors="coerce").sum())) if resi else "",
        "REVISED_NET_TOTAL": round(float(pd.to_numeric(df[net], errors="coerce").sum())) if net else "",
        "SOURCE_FILE": os.path.basename(path),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inputs", nargs="+", required=True,
                    help="one or more folders (or files) containing *_Final_Complete.xlsx")
    ap.add_argument("--out", default="Salary_Exceptions_Summary",
                    help="output file prefix (writes .csv and .xlsx)")
    a = ap.parse_args()

    files = []
    for p in a.inputs:
        if os.path.isdir(p):
            files += glob.glob(os.path.join(p, "**", "*_Final_Complete.xlsx"), recursive=True)
        elif os.path.isfile(p):
            files.append(p)
    files = sorted(set(files))
    if not files:
        print("No *_Final_Complete.xlsx files found under the given --in path(s).")
        sys.exit(1)

    print(f"Found {len(files)} reconciled file(s):")
    rows = []
    for f in files:
        print(f"  reading {os.path.basename(f)} ...")
        r = analyse(f)
        if r:
            rows.append(r)
            print(f"    {r['MONTH']}: BASIC+DA<15000 & no PF = {r['EMP_BD_LT_15000_AND_NO_PF']} employees")

    if not rows:
        print("Nothing analysed.")
        sys.exit(1)

    out = pd.DataFrame(rows).sort_values("MONTH").reset_index(drop=True)
    out.to_csv(a.out + ".csv", index=False)
    out.to_excel(a.out + ".xlsx", index=False)
    total = out["EMP_BD_LT_15000_AND_NO_PF"].sum()
    print(f"\nWrote {a.out}.csv and {a.out}.xlsx ({len(out)} months).")
    print(f"TOTAL employees BASIC+DA<15000 with no ECR PF across all months = {total}")
    print("\nUpload the .xlsx to Google Drive (open as Google Sheet) and point the bot at it.")


if __name__ == "__main__":
    main()
