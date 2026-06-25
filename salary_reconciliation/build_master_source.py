#!/usr/bin/env python3
"""
build_master_source.py  —  merge the 12 reconciled monthly files into ONE lean,
values-only source table ready for a PivotTable + slicers.

Why lean: the existing SALARY_ALL_MONTHS workbook is ~282 MB because it flat-merges
all ~218 formula columns. This keeps ~20 analysis columns as plain values, so the
output is small and pivots/slicers stay fast. Footer/total rows are dropped so sums
don't double-count.

USAGE:
  python build_master_source.py <folder_with_12_monthly_xlsx> [--out Salary_Master_Source_FY2025-26.xlsx]

Reads the biggest sheet of each *.xlsx, stamps MONTH from the file name, and writes
a single sheet 'SourceData'. Prints a per-month row count + REVISED_NET total so you
can sanity-check against your summaries.
"""
import argparse
from pathlib import Path

import pandas as pd

MONTH_ORDER = ["April", "May", "June", "July", "August", "September",
               "October", "November", "December", "January", "February", "March"]

# canonical output column -> acceptable source header spellings (tolerant match)
WANT = {
    "MONTH":                ["MONTH"],
    "SITESTATE":            ["SITESTATE", "SITE STATE"],
    "SITENAME":             ["SITENAME", "SITE NAME"],
    "BRANCHNAME":           ["BRANCHNAME", "BRANCH NAME"],
    "DESIGNATIONNAME":      ["DESIGNATIONNAME", "DESIGNATION"],
    "EMPCODE":              ["EMPCODE", "EMP CODE"],
    "FULLNAME":             ["FULLNAME", "FULL NAME"],
    "ADJ_WORKING_DAYS":     ["ADJ_WORKING_DAYS"],
    "ORIG_BASIC":           ["BASIC"],
    "ORIG_NETPAYABLE":      ["NETPAYABLE"],
    "REVISED_BASIC":        ["REVISED_BASIC"],
    "REVISED_DA":           ["REVISED_DA"],
    "REVISED_GROSS":        ["REVISED_GROSS"],
    "REVISED_PF":           ["REVISED_PF"],
    "ECR_PF":               ["ECR_PF", "ECR PF"],
    "REVISED_ESIC":         ["REVISED_ESIC"],
    "ESIC_AS_PER_FUTURE":   ["ESIC_AS_PER_FUTURE", "ESIC AS PER FUTURE"],
    "REVISED_TOTAL_DED":    ["REVISED_TOTAL_DED", "REVISED TOTAL DED"],
    "REVISED_NET_PAYABLE":  ["REVISED_NET_PAYABLE", "REVISED NET PAYABLE"],
    "RULE_APPLIED":         ["RULE_APPLIED"],
    "HIGH_EARNER_EXCEPTION":["HIGH_EARNER_EXCEPTION"],
}
NUMERIC = {"ADJ_WORKING_DAYS", "ORIG_BASIC", "ORIG_NETPAYABLE", "REVISED_BASIC",
           "REVISED_DA", "REVISED_GROSS", "REVISED_PF", "ECR_PF", "REVISED_ESIC",
           "ESIC_AS_PER_FUTURE", "REVISED_TOTAL_DED", "REVISED_NET_PAYABLE"}


def norm(s):
    return "".join(str(s).split()).replace("_", "").upper() if s is not None else ""


def read_data_sheet(path):
    xl = pd.ExcelFile(path)
    sh = max(xl.sheet_names, key=lambda s: xl.parse(s, header=None, nrows=2000).shape[0])
    probe = xl.parse(sh, header=None, nrows=25)
    hdr = next((i for i in range(len(probe))
                if probe.iloc[i].astype(str).str.upper().str.strip().eq("EMPCODE").any()), 0)
    return xl.parse(sh, header=hdr)


def month_key(stem):
    s = stem.lower()
    for i, m in enumerate(MONTH_ORDER):
        if s.startswith(m.lower()):
            return i, m
    return 99, stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default="Salary_Master_Source_FY2025-26.xlsx")
    args = ap.parse_args()

    files = [f for f in Path(args.folder).glob("*.xlsx") if not f.name.startswith("~$")]
    files.sort(key=lambda p: month_key(p.stem)[0])
    if not files:
        raise SystemExit(f"No .xlsx in {args.folder}")

    frames = []
    print(f"{'Month':10s} {'rows':>8} {'REVISED_NET total':>20}")
    for f in files:
        df = read_data_sheet(f)
        lut = {norm(c): c for c in df.columns}
        out = pd.DataFrame()
        for canon, spellings in WANT.items():
            src = next((lut[norm(s)] for s in spellings if norm(s) in lut), None)
            out[canon] = df[src] if src is not None else pd.NA
        # stamp MONTH from filename (authoritative, avoids blank/short labels)
        out["MONTH"] = month_key(f.stem)[1]
        # drop footer/total rows: EMPCODE must be numeric
        out = out[pd.to_numeric(out["EMPCODE"], errors="coerce").notna()].reset_index(drop=True)
        for c in NUMERIC:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)
        frames.append(out)
        print(f"{month_key(f.stem)[1]:10s} {len(out):8d} {out['REVISED_NET_PAYABLE'].sum():20,.2f}")

    master = pd.concat(frames, ignore_index=True)
    print("-" * 40)
    print(f"{'TOTAL':10s} {len(master):8d} {master['REVISED_NET_PAYABLE'].sum():20,.2f}")

    with pd.ExcelWriter(args.out, engine="openpyxl") as w:
        master.to_excel(w, sheet_name="SourceData", index=False)
    print(f"\nWrote {args.out}  ({len(master):,} rows x {master.shape[1]} cols, values only)")
    print("Next: in Excel, Insert > PivotTable > 'Add this data to the Data Model',")
    print("      then add slicers on MONTH / SITESTATE / DESIGNATIONNAME / RULE_APPLIED.")


if __name__ == "__main__":
    main()
