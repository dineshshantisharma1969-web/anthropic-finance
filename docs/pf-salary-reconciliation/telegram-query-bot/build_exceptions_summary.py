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

BD_CEILING = 15000.0   # PF wage ceiling (BASIC+DA)
ESI_CEILING = 21000.0  # ESI wage ceiling (gross)

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

    # optional extra columns (present in every reconciled output)
    rgross = resolve(df, "REVISED_GROSS")
    rule   = resolve(df, "RULE_APPLIED")
    relax  = resolve(df, "RULE_075_RELAXED")
    negod  = resolve(df, "REVISED_OTHER_DEDUCTION")
    bdproj = resolve(df, "MONTHLY_BD_PROJECTION")

    df["_EMP"] = df[emp].astype(str).str.strip().str.split(".").str[0]
    df["_PF"]  = pd.to_numeric(df[rpf], errors="coerce").fillna(0.0)
    df["_ESI"] = pd.to_numeric(df[resi], errors="coerce").fillna(0.0) if resi else 0.0
    df["_GROSS"] = pd.to_numeric(df[rgross], errors="coerce").fillna(0.0) if rgross else 0.0
    df["_BD"]  = (pd.to_numeric(df[rb], errors="coerce").fillna(0.0)
                  + pd.to_numeric(df[rd], errors="coerce").fillna(0.0))

    # per-EMPLOYEE roll-up (an employee may have several site rows)
    g = df.groupby("_EMP").agg(pf=("_PF", "sum"), esi=("_ESI", "sum"),
                               bd=("_BD", "sum"), gross=("_GROSS", "sum"))
    no_pf  = g["pf"] <= 0.5
    no_esi = g["esi"] <= 0.5
    bd_below   = (g["bd"] > 0) & (g["bd"] < BD_CEILING)
    gross_below = (g["gross"] > 0) & (g["gross"] <= ESI_CEILING)

    def truthy(col):
        return df[col].astype(str).str.upper().isin(["TRUE", "1", "1.0", "YES"])

    row = {
        "MONTH": month_label(path),
        "TOTAL_EMPLOYEES": int(g.shape[0]),
        # ---- the anomalies you asked about ----
        "EMP_BD_LT_15000_AND_NO_PF": int((no_pf & bd_below).sum()),
        "EMP_GROSS_LE_21000_AND_NO_ESI": int((no_esi & gross_below).sum()),
        "ANOMALY_BELOW_CEILING_native": int(df.loc[truthy(anom), "_EMP"].nunique()) if anom else "",
        # ---- statutory-ceiling watches (row counts) ----
        "ROWS_PF_GT_1800": int((df["_PF"] > 1800.5).sum()),
        "ROWS_ESI_GROSS_GT_21000": int(((df["_ESI"] > 0) & (df["_GROSS"] > 21001)).sum()),
        "ROWS_PF_BDPROJ_GT_15000": (int(((df["_PF"] > 0) &
            (pd.to_numeric(df[bdproj], errors="coerce").fillna(0) > 15000.5)).sum())
            if bdproj else ""),
        "ROWS_ESI_075_RELAXED": int(truthy(relax).sum()) if relax else "",
        "ROWS_NEG_OTHER_DED": (int((pd.to_numeric(df[negod], errors="coerce").fillna(0) < -1).sum())
                               if negod else ""),
        # ---- PF/ESI coverage ----
        "EMP_WITH_PF": int((~no_pf).sum()),
        "EMP_NO_PF": int(no_pf.sum()),
        "EMP_WITH_ESI": int((~no_esi).sum()),
        # ---- rule breakdown (row counts) ----
        "RULE_PF_ANCHOR": "", "RULE_PF_SECONDARY": "",
        "RULE_ESI_ONLY": "", "RULE_NO_PF_NO_ESI": "",
        # ---- month totals ----
        "REVISED_PF_TOTAL": round(float(df["_PF"].sum())),
        "REVISED_ESIC_TOTAL": round(float(df["_ESI"].sum())),
        "REVISED_NET_TOTAL": round(float(pd.to_numeric(df[net], errors="coerce").sum())) if net else "",
        "SOURCE_FILE": os.path.basename(path),
    }
    if rule:
        vc = df[rule].astype(str).str.upper().value_counts()
        row["RULE_PF_ANCHOR"]    = int(vc.get("PF_ANCHOR", 0))
        row["RULE_PF_SECONDARY"] = int(vc.get("PF_SECONDARY", 0))
        row["RULE_ESI_ONLY"]     = int(vc.get("ESI_ONLY", 0))
        row["RULE_NO_PF_NO_ESI"] = int(vc.get("NO_PF_NO_ESI", 0))
    return row


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

    # ---- optional: attach ACTION_NEEDED_* row counts + excess salary by month ----
    # (April-26 introduced ACTION_NEEDED_<Month><YY>.csv — only present where built)
    action = {}
    for p in a.inputs:
        base = p if os.path.isdir(p) else os.path.dirname(p)
        for csvf in glob.glob(os.path.join(base, "**", "ACTION_NEEDED*.csv"), recursive=True):
            try:
                adf = pd.read_csv(csvf)
                mon = month_label(csvf)
                exc_col = resolve(adf, "EXCESS_SALARY", "EXCESS", "EXCESS_AMOUNT")
                action[mon] = (len(adf),
                               round(float(pd.to_numeric(adf[exc_col], errors="coerce").sum()))
                               if exc_col else "")
                print(f"  action-needed {mon}: {len(adf)} rows")
            except Exception as e:
                print(f"  !! could not read {os.path.basename(csvf)}: {e}")
    for r in rows:
        cnt, exc = action.get(r["MONTH"], ("", ""))
        r["ACTION_NEEDED_ROWS"] = cnt
        r["ACTION_NEEDED_EXCESS_SALARY"] = exc

    out = pd.DataFrame(rows).sort_values("MONTH").reset_index(drop=True)
    out.to_csv(a.out + ".csv", index=False)
    out.to_excel(a.out + ".xlsx", index=False)
    total = out["EMP_BD_LT_15000_AND_NO_PF"].sum()
    print(f"\nWrote {a.out}.csv and {a.out}.xlsx ({len(out)} months).")
    print(f"TOTAL employees BASIC+DA<15000 with no ECR PF across all months = {total}")
    print("\nUpload the .xlsx to Google Drive (open as Google Sheet) and point the bot at it.")


if __name__ == "__main__":
    main()
