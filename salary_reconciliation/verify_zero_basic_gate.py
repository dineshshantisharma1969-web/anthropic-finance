#!/usr/bin/env python3
"""
verify_zero_basic_gate.py  —  QA gate for the "original BASIC = 0" rule.

Rule (confirmed):
  For every row whose ORIGINAL BASIC == 0:
    * NET PAYABLE is sacrosanct  -> if original NET was 0, revised NET must stay 0.
    * REVISED_BASIC and REVISED_PF must be 0,
      UNLESS PF was actually deposited (ECR_PF > 0), in which case the row keeps
      the deposited PF: REVISED_PF == ECR_PF and REVISED_BASIC == ECR_PF / 0.12.

Reports three violation classes per month and an overall PASS/FAIL:
  V1  original NET == 0 but revised NET != 0      (net wrongly changed)
  V2  ECR_PF == 0 but revised BASIC or PF != 0    (should have been zeroed)
  V3  ECR_PF  > 0 but revised PF != ECR_PF        (deposited PF not mirrored)

USAGE:
  python verify_zero_basic_gate.py <folder_with_monthly_xlsx> [--tol 1]
  Reads the first/biggest data sheet of each *.xlsx in the folder.
  Column names are matched tolerantly (works on both the CLEAN and the
  WITH_FORMULAE / CORRECTED layouts).

Exit code is non-zero if any violation is found (handy for scheduled runs).
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

MONTH_ORDER = ["April", "May", "June", "July", "August", "September",
               "October", "November", "December", "January", "February", "March"]


def norm(s):
    return "".join(str(s).split()).replace("_", "").upper() if s is not None else ""


def read_data_sheet(path):
    xl = pd.ExcelFile(path)
    sh = max(xl.sheet_names, key=lambda s: xl.parse(s, header=None, nrows=1).shape[1])
    probe = xl.parse(sh, header=None, nrows=25)
    hdr = next((i for i in range(len(probe))
                if probe.iloc[i].astype(str).str.upper().str.strip().eq("EMPCODE").any()), 0)
    return xl.parse(sh, header=hdr)


def col(df, *cands):
    lut = {norm(c): c for c in df.columns}
    for c in cands:
        if norm(c) in lut:
            return lut[norm(c)]
    return None


def num(df, c):
    return pd.to_numeric(df[c], errors="coerce").fillna(0) if c else pd.Series(0.0, index=df.index)


def month_key(name):
    s = name.lower()
    for i, m in enumerate(MONTH_ORDER):
        if s.startswith(m.lower()):
            return i
    return 99


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--tol", type=float, default=1.0, help="rupee tolerance (default 1)")
    args = ap.parse_args()

    files = sorted(Path(args.folder).glob("*.xlsx"), key=lambda p: month_key(p.stem))
    files = [f for f in files if not f.name.startswith("~$")]
    if not files:
        sys.exit(f"No .xlsx files found in {args.folder}")

    tol = args.tol
    print(f"{'File':28s} {'BASIC=0':>8} {'V1':>5} {'V2':>5} {'V3':>5}")
    grand = dict(b=0, v1=0, v2=0, v3=0)
    for f in files:
        df = read_data_sheet(f)
        emp = col(df, "EMPCODE", "EMP CODE")
        if emp:
            df = df[pd.to_numeric(df[emp], errors="coerce").notna()].reset_index(drop=True)
        basic = num(df, col(df, "BASIC"))
        onet  = num(df, col(df, "NETPAYABLE"))
        rnet  = num(df, col(df, "REVISED_NET_PAYABLE", "REVISED NET PAYABLE"))
        rb    = num(df, col(df, "REVISED_BASIC"))
        rp    = num(df, col(df, "REVISED_PF"))
        ecr   = num(df, col(df, "ECR_PF", "ECR PF"))

        b0 = basic.abs() < 0.5
        v1 = int((b0 & (onet.abs() < 0.5) & (rnet.abs() > tol)).sum())
        v2 = int((b0 & (ecr.abs() < 0.5) & ((rb.abs() > tol) | (rp.abs() > tol))).sum())
        v3 = int((b0 & (ecr.abs() > 0.5) & ((rp - ecr).abs() > tol)).sum())
        print(f"{f.name[:28]:28s} {int(b0.sum()):8d} {v1:5d} {v2:5d} {v3:5d}")
        grand["b"] += int(b0.sum()); grand["v1"] += v1; grand["v2"] += v2; grand["v3"] += v3

    print("-" * 56)
    print(f"{'TOTAL':28s} {grand['b']:8d} {grand['v1']:5d} {grand['v2']:5d} {grand['v3']:5d}")
    total_viol = grand["v1"] + grand["v2"] + grand["v3"]
    print("\nV1 net wrongly changed | V2 should-be-zeroed row kept basic/PF (no ECR) | "
          "V3 revised PF != deposited ECR PF")
    if total_viol == 0:
        print("\nVERDICT: PASS — zero-basic gate holds on all files.")
        sys.exit(0)
    print(f"\nVERDICT: FAIL — {total_viol} violation(s). Review the months above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
