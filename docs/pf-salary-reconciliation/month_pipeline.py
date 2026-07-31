#!/usr/bin/env python3
"""
month_pipeline.py — one-command monthly pipeline: Drive folder -> clean CSV -> ERP.

Runs the full chain for a month:
  1. Find the inputs in the month's (Drive-synced) folder:
       salary sheet   *salary*.xlsx / *FULL_monthly*.xlsx
       ECR PF файлы   FORMAT*.xls[x]  (one or more)
       ESI / Future   *ESIC*.xlsx / *FUTURE*.xlsx
  2. Run reconcile.py (the ESI-corrected pipeline) -> <prefix>_Final_Complete.xlsx
  3. Post-step: corrected ESI coverage flag ONLY (no overpayment/excess flags).
     Day-column rule: REAL_FULL_MONTH_GROSS = REVISED_GROSS_NEW (the ESI base)
     / NORMALDAYS x calendar days-in-month (never SITEDIVISIONDAYS, never 30).
  4. Validate: Golden Rules + C1-C10 row checks. Any hard FAIL aborts the load.
  5. Write  <Month>_CLEAN.csv  and  <Month>_RULES_OUTCOME.csv  into the folder.
  6. --load: ingest the clean CSV straight into the payroll ERP database
     (uses erp/payroll/webui/ingest.py and the ERP_DB connection string), so the
     month appears in the ERP without touching the browser.

Also accepts an already-reconciled working file (skip step 2):
  python month_pipeline.py --reconciled <workbook.xlsx> [--sheet <name>] --month 2026-06 [--load]

Full run:
  python month_pipeline.py --folder "G:\\My Drive\\SALARY DATA 2026-27\\2026-06" --month 2026-06 --load

DB connection for --load comes from the ERP_DB env var
(e.g.  set ERP_DB=host=... port=5432 user=... password=... dbname=postgres).
"""
from __future__ import annotations
import argparse, calendar, glob, os, re, subprocess, sys

import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ESI_REASON = ("ESI APPLICABLE: full-month <= Rs.21,000, wages earned, "
              "ESI not deducted - enrol/regularise")


def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def find_inputs(folder):
    """Locate salary / ECR / Future files by the naming conventions."""
    xl = [p for p in glob.glob(os.path.join(folder, "*.xls*"))
          if not re.search(r"_CLEAN|_Final_Complete|_Reconciliation_Report|RULES_OUTCOME",
                           os.path.basename(p), re.I)]
    ecr = [p for p in xl if re.match(r"FORMAT", os.path.basename(p), re.I)]
    fut = [p for p in xl if re.search(r"ESIC|FUTURE", os.path.basename(p), re.I)
           and p not in ecr]
    rest = [p for p in xl if p not in ecr and p not in fut]
    sal = [p for p in rest if re.search(r"salary|monthly", os.path.basename(p), re.I)] or rest
    sal = max(sal, key=os.path.getsize) if sal else None
    return sal, ecr, (fut[0] if fut else None)


def detect_header(path, sheet=None, scan=12):
    """Row index whose cells include EMPCODE (working files bury it under a title block)."""
    raw = pd.read_excel(path, sheet_name=sheet or 0, header=None, nrows=scan, dtype=object)
    for i in range(len(raw)):
        vals = {str(v).strip().upper() for v in raw.iloc[i].tolist()}
        if "EMPCODE" in vals:
            return i
    return 0


def pick_sheet(path):
    """Sheet with the most columns among sheets that contain EMPCODE."""
    xls = pd.ExcelFile(path)
    best, width = None, -1
    for s in xls.sheet_names:
        head = pd.read_excel(path, sheet_name=s, header=None, nrows=8, dtype=object)
        if any("EMPCODE" in {str(v).strip().upper() for v in head.iloc[i].tolist()}
               for i in range(len(head))):
            w = head.shape[1]
            if w > width:
                best, width = s, w
    return best or xls.sheet_names[0]


# ESI-ineligible allowances — the exact March-26 "HP" column formula:
#   REVISED_GROSS_NEW = GF - (CA+BZ+CZ+DK+CU+CM+CY+CX+CO)
# HRA is deliberately NOT excluded: it stays inside the ESI base.
ESI_EXEMPT = ["WASHING ALLOWANCE", "CONVEYENCE", "TRANSPORT ALLOWANCE",
              "TRAVELLING ALLOWANCE", "UNIFORM COST", "ATTIRE",
              "MOBILE REIMB", "VEHICLE REIMB", "LTA"]
ESI_RATE = 0.0075


def esi_gross_new_block(df):
    """M13 ESI block, as per the March-26 sheet.

    REVISED_GROSS_NEW is the ESI base. Where ESI is anchored to the Future
    sheet, the base is backsolved (ESI / 0.75%) so the 0.75% test ties exactly,
    and HRA is the balancing figure — raised or reduced by the difference. If
    the required HRA would go negative it floors at 0 and the remainder is
    parked in EXTRA_EXCL (March's BACKSOLVED_TO_BENCHMARK treatment).

    Monetary columns (PF, ESIC, GROSS, NET) are never touched — the HRA move is
    notional, for the ESI base only, so all Golden Rules still hold.
    """
    rg = num(df.get("REVISED_GROSS", 0))
    esi = num(df.get("REVISED_ESIC", 0))
    hra0 = num(df.get("HRA", 0))
    exempt = sum(num(df[c]) for c in ESI_EXEMPT if c in df.columns)

    formula_gn = (rg - exempt).round(2)              # the HP formula, as-is
    target = (esi / ESI_RATE).round(2)              # base that makes 0.75% tie
    has = esi > 0
    delta = np.where(has, (target - formula_gn).round(2), 0.0)
    hra_new = np.where(has, (hra0 + delta).round(2), hra0)
    extra = np.where(hra_new < 0, -hra_new, 0.0).round(2)
    hra_new = np.where(hra_new < 0, 0.0, hra_new)
    gn = np.where(has, target, formula_gn)

    df["REVISED_GROSS_NEW_FORMULA"] = formula_gn
    df["REVISED_GROSS_NEW"] = np.round(gn, 2)
    df["STATUTORY_EXCL_TOTAL"] = exempt.round(2)
    df["EXTRA_EXCL"] = extra
    df["REVISED_HRA"] = hra_new
    df["HRA_ADJUSTMENT"] = delta
    df["ESI 0.75% OF GROSS_NEW (LIVE)"] = np.where(has, (gn * ESI_RATE).round(2), 0.0)
    df["ESI DIFF (0.75%calc - REVISED_ESIC)"] = (df["ESI 0.75% OF GROSS_NEW (LIVE)"] - esi).round(2)
    df["ESI_PCT_OF_GROSS_NEW"] = np.where(gn > 0, (esi / np.where(gn > 0, gn, 1) * 100).round(4), 0.0)
    df["ESI_GN_TREATMENT"] = np.where(~has, "NOT_ELIGIBLE",
                             np.where(extra > 0, "BACKSOLVED_TO_BENCHMARK",
                              np.where(np.abs(delta) > 0.5, "HRA_BALANCED",
                                       "FRESH_0.75%_OF_(GROSS-INELIGIBLE)")))
    df["M8_STATUS"] = np.where(~has, "NO_ESI",
                       np.where(np.abs(delta) <= 0.5, "M8_OK",
                        np.where(delta < 0, "M8_EXTRA_EXCL", "M8_LIFT")))
    hj = (rg - num(df.get("REVISED_TOTAL_DED", 0))).round(2)
    df["HJ_NEW (=GG-HK)"] = hj
    df["HI_NEW (=HJ_NEW-PF-ESI)"] = (hj - num(df.get("REVISED_PF", 0)) - esi).round(2)

    ties = int((has & (np.abs(df["ESI DIFF (0.75%calc - REVISED_ESIC)"]) <= 0.51)).sum())
    print(f"  ESI base: {int(has.sum()):,} ESI rows, 0.75% x GROSS_NEW ties on {ties:,}"
          f"  ({'PASS' if ties == int(has.sum()) else 'REVIEW'})")
    return df


def post_and_validate(df, month, out_dir, prefix):
    """Corrected ESI flag + Golden-Rule/C-check validation. Returns (clean_csv, ok)."""
    y, m = map(int, month.split("-"))
    fmd = calendar.monthrange(y, m)[1]

    need = ["EMPCODE", "ESIC", "GROSS AMT", "NORMALDAYS", "REVISED_GROSS",
            "REVISED_PF", "ECR_PF", "REVISED_ESIC", "NETPAYABLE"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        sys.exit(f"missing required columns: {missing}")
    df = df[df["EMPCODE"].notna() & df["EMPCODE"].astype(str).str.strip().ne("")].copy()
    # skill rule: strip the Excel float '.0' suffix from codes so an employee is
    # ONE employee across months ('10010010.0' == '10010010')
    for col in ("EMPCODE", "SITECODE"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.split(".").str[0]

    # Build REVISED_GROSS_NEW (the ESI base: gross minus ESI-ineligible allowances,
    # HRA retained) FIRST — the ESI coverage-gap test projects on it, not on GROSS.
    df = esi_gross_new_block(df)

    if "Future_ESI" not in df.columns:
        df["Future_ESI"] = df["ESIC AS PER FUTURE"] if "ESIC AS PER FUTURE" in df.columns \
            else df["REVISED_ESIC"]

    # ESI coverage-gap flag — per the day-column rule (SKILL.md "Day-Column
    # Semantics"): full-month equivalent = earned amount / ACTUAL days worked x
    # calendar days in month. Amount = REVISED_GROSS_NEW (the ESI base), divisor =
    # NORMALDAYS (never SITEDIVISIONDAYS, never a hardcoded 30). A row is a genuine
    # ESI enrolment gap only if this projection is still <= Rs.21,000 at the
    # employee's real attendance. (Apr-2026 M13: this basis = 40 gaps; the old
    # FIXEDGROSS/SITEDIVISIONDAYS basis over-stated it at 187.)
    rgn = num(df["REVISED_GROSS_NEW"])
    nd = num(df["NORMALDAYS"])
    full_month = np.where(nd > 0, rgn / nd.replace(0, np.nan) * fmd, 0.0)
    df["REAL_FULL_MONTH_GROSS"] = np.round(np.nan_to_num(full_month), 2)

    gap = (num(df["ESIC"]) == 0) & (num(df["GROSS AMT"]) > 0) \
        & (df["REAL_FULL_MONTH_GROSS"] > 0) & (df["REAL_FULL_MONTH_GROSS"] <= 21000)
    df["ACTION_NEEDED"] = np.where(gap, "Y", "N")
    df["ACTION_REASON"] = np.where(gap, ESI_REASON, "")
    df["EXCESS_SALARY"] = 0

    # ---- validation: anchors + C1-C10 (active rows) ------------------- #
    active = (num(df["REVISED_PF"]) > 0) | (num(df["REVISED_ESIC"]) > 0)
    rb, rd = num(df.get("REVISED_BASIC", 0)), num(df.get("REVISED_DA", 0))
    att = num(df.get("REVISED_ATTENDANCE_ALLOWANCE", 0))
    rg, td = num(df.get("REVISED_GROSS", 0)), num(df.get("REVISED_TOTAL_DED", 0))
    rnet, onet = num(df.get("REVISED_NET_PAYABLE", 0)), num(df["NETPAYABLE"])
    od = num(df.get("REVISED_OTHER_DEDUCTION", 0))
    adj = num(df.get("ADJ_WORKING_DAYS", 0))
    rpf, ecr, resi = num(df["REVISED_PF"]), num(df["ECR_PF"]), num(df["REVISED_ESIC"])
    apf = num(df["ESIC AS PER FUTURE"]) if "ESIC AS PER FUTURE" in df.columns else resi

    checks = [
        ("Golden Rule 1: sum REVISED_PF = sum ECR_PF",
         abs(rpf.sum() - ecr.sum()) <= 1, f"gap {rpf.sum()-ecr.sum():,.0f}"),
        ("Golden Rule 2: REVISED_ESIC = ESIC as per Future (per row)",
         int(((resi - apf).abs() > 0.5).sum()) == 0,
         f"{int(((resi-apf).abs()>0.5).sum())} rows differ"),
        ("Golden Rule 3 / C8: REVISED_NET = NETPAYABLE",
         int(((rnet - onet).abs() > 1).sum()) == 0,
         f"{int(((rnet-onet).abs()>1).sum())} rows drift"),
        ("C1 OTHER_DED >= 0", int((od < -0.5).sum()) == 0, f"{int((od<-0.5).sum())} rows"),
        ("C2 NET = GROSS - TOTAL_DED",
         int(((rnet - (rg - td)).abs() > 1).sum()) == 0,
         f"{int(((rnet-(rg-td)).abs()>1).sum())} rows"),
        ("C3 PF = 12% x (B+D)",
         int((((0.12 * (rb + rd)).round(2) - rpf).abs().where(rpf > 0, 0) > 1).sum()) == 0,
         f"{int((((0.12*(rb+rd)).round(2)-rpf).abs().where(rpf>0,0)>1).sum())} rows"),
        ("C5 ATT_ALW >= 0", int((att < -0.5).sum()) == 0, f"{int((att<-0.5).sum())} rows"),
        ("C6 TOTAL_DED >= 0", int((td < -0.5).sum()) == 0, f"{int((td<-0.5).sum())} rows"),
        ("C7 GROSS = B+D+ATT",
         int(((rg - (rb + rd + att)).abs() > 1).sum()) == 0,
         f"{int(((rg-(rb+rd+att)).abs()>1).sum())} rows"),
        (f"C9 days in [1,{fmd}] (active rows)",
         int((~adj.between(1, fmd) & active).sum()) == 0,
         f"{int((~adj.between(1,fmd)&active).sum())} active rows"),
        ("C10 filed ECR_PF <= REVISED_PF", int(((ecr - rpf) > 1).sum()) == 0,
         f"{int(((ecr-rpf)>1).sum())} rows"),
    ]

    ok = True
    out_rows = []
    print(f"\nVALIDATION — {month} ({len(df):,} rows, FULL_MONTH={fmd})")
    for name, passed, detail in checks:
        ok &= bool(passed)
        print(f"  {'PASS' if passed else 'FAIL'}  {name}  ({detail})")
        out_rows.append({"Check": name, "Result": "PASS" if passed else "FAIL", "Detail": detail})
    n_gap = int(gap.sum())
    print(f"  INFO  ESI coverage-gap flags: {n_gap}")
    out_rows.append({"Check": "ESI coverage gap (corrected rule)",
                     "Result": "ACTION", "Detail": f"{n_gap} rows flagged"})
    out_rows.append({"Check": "Totals", "Result": "-",
                     "Detail": (f"rows {len(df):,} | REVISED_PF {rpf.sum():,.0f} | "
                                f"NET {rnet.sum():,.0f}")})

    clean_csv = os.path.join(out_dir, f"{prefix}_CLEAN.csv")
    df.to_csv(clean_csv, index=False)
    pd.DataFrame(out_rows).to_csv(os.path.join(out_dir, f"{prefix}_RULES_OUTCOME.csv"), index=False)
    print(f"\nwrote {clean_csv}  ({len(df):,} rows x {df.shape[1]} cols)")
    print(f"wrote {os.path.join(out_dir, f'{prefix}_RULES_OUTCOME.csv')}")
    return clean_csv, ok


def load_into_erp(clean_csv, month):
    sys.path.insert(0, os.path.join(HERE, "..", "..", "erp", "payroll", "webui"))
    import psycopg2, ingest
    dsn = os.environ.get("ERP_DB")
    if not dsn:
        sys.exit("--load needs the ERP_DB env var (same connection as the ERP app).")
    y, m = map(int, month.split("-"))
    start = y if m >= 4 else y - 1
    fy = f"{start}-{str(start+1)[-2:]}"
    rows = ingest.read_rows(clean_csv)
    conn = psycopg2.connect(dsn)
    try:
        s = ingest.ingest_period(conn, month, fy, rows, run_by="month_pipeline",
                                 source_files=os.path.basename(clean_csv))
    finally:
        conn.close()
    c = s["checks"]
    print(f"\nLOADED into ERP: {month}  rows {s['rows']:,}  action items {s['action_items']:,}")
    print(f"  PF gap {s['pf_gap']:,.0f} ({'PASS' if c['rule1_pass'] else 'REVIEW'})  "
          f"net drift {s['net_drift']:,.0f} ({'PASS' if c['rule3_pass'] else 'REVIEW'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", help="month folder with salary + FORMAT ECR + ESIC/Future files")
    ap.add_argument("--reconciled", help="already-reconciled working file (skip reconcile.py)")
    ap.add_argument("--sheet", default=None, help="sheet name in --reconciled (auto if omitted)")
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--load", action="store_true", help="load the clean CSV into the ERP DB")
    a = ap.parse_args()
    mon = pd.Period(a.month).strftime("%b%Y")  # e.g. Jun2026
    prefix = mon

    if a.reconciled:
        sheet = a.sheet or pick_sheet(a.reconciled)
        hdr = detect_header(a.reconciled, sheet)
        print(f"Reading reconciled file: {a.reconciled} [sheet '{sheet}', header row {hdr+1}]")
        df = pd.read_excel(a.reconciled, sheet_name=sheet, header=hdr)
        out_dir = os.path.dirname(os.path.abspath(a.reconciled))
    else:
        if not a.folder:
            sys.exit("give --folder (raw inputs) or --reconciled (working file)")
        sal, ecr, fut = find_inputs(a.folder)
        print(f"Inputs found in {a.folder}:")
        print(f"  salary : {sal}")
        print(f"  ECR    : {ecr}")
        print(f"  future : {fut}")
        if not (sal and ecr and fut):
            sys.exit("missing inputs — need salary + at least one FORMAT ECR + an ESIC/Future file")
        cmd = [sys.executable, os.path.join(HERE, "reconcile.py"),
               "--salary", sal, "--ecr", *ecr, "--future", fut,
               "--month", a.month, "--out-prefix", os.path.join(a.folder, prefix)]
        print("\nRunning reconcile.py …")
        rc = subprocess.run(cmd).returncode
        if rc not in (0, 2):
            sys.exit(f"reconcile.py failed (exit {rc})")
        df = pd.read_excel(os.path.join(a.folder, f"{prefix}_Final_Complete.xlsx"))
        out_dir = a.folder

    clean_csv, ok = post_and_validate(df, a.month, out_dir, prefix)
    if not ok:
        sys.exit("VALIDATION FAILED — clean CSV written for inspection, NOT loaded. Fix and re-run.")
    if a.load:
        load_into_erp(clean_csv, a.month)
    print("\nDONE.")


if __name__ == "__main__":
    main()
