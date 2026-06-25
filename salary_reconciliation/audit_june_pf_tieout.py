#!/usr/bin/env python3
"""
audit_june_pf_tieout.py  —  READ-ONLY audit for June's cosmetic summary drift.

The June reconciled data (NET PAYABLE, REVISED_PF, etc.) is correct and sacrosanct.
The only leftover is a *display* metric on a summary/Reconciliation tab: a site-level
REVISED_PF total that is off by a few rupees (the ~-Rs 858 / ~Rs 553 drift). This
script does NOT change any salary data — it just reads MONTHS/June.xlsx and prints
the AUTHORITATIVE figures so the summary cell can be set to the right value.

What it prints:
  * Total REVISED_PF (the number the site-total cell should equal)
  * Row-level tie-out:  sum( REVISED_GROSS - REVISED_TOTAL_DED - REVISED_NET_PAYABLE )
    (should be 0; any residual is the cosmetic drift)
  * Site-wise REVISED_PF totals (to locate which site cell is off)

USAGE (Windows, your local python):
  '/c/Users/Dinesh Sharma/AppData/Local/Python/bin/python.exe' audit_june_pf_tieout.py "June.xlsx"

Nothing is written. Safe to run anytime.
"""
import sys
from pathlib import Path
import pandas as pd


def norm(s):
    return "".join(str(s).split()).replace("_", "").upper() if s is not None else ""


def find_header_and_read(path, sheet=None):
    xl = pd.ExcelFile(path)
    sh = sheet or max(xl.sheet_names, key=lambda s: xl.parse(s, header=None, nrows=1).shape[1])
    probe = xl.parse(sh, header=None, nrows=20)
    hdr = next((i for i in range(len(probe))
                if probe.iloc[i].astype(str).str.upper().str.strip().eq("EMPCODE").any()), 0)
    return xl.parse(sh, header=hdr), sh, hdr


def col(df, *cands):
    lut = {norm(c): c for c in df.columns}
    for c in cands:
        if norm(c) in lut:
            return lut[norm(c)]
    return None


def num(df, c):
    return pd.to_numeric(df[c], errors="coerce").fillna(0) if c else pd.Series(0, index=df.index)


def main(path, sheet=None):
    df, sh, hdr = find_header_and_read(path, sheet)
    # drop footer/total rows (blank or non-numeric EMPCODE)
    emp = col(df, "EMPCODE", "EMP CODE")
    if emp:
        keep = pd.to_numeric(df[emp], errors="coerce").notna()
        df = df[keep].reset_index(drop=True)
    print(f"File   : {Path(path).name}")
    print(f"Sheet  : {sh} (header row {hdr + 1}); employee rows: {len(df):,}\n")

    cPf   = col(df, "REVISED_PF")
    cGr   = col(df, "REVISED_GROSS")
    cTd   = col(df, "REVISED_TOTAL_DED", "REVISED TOTAL DED")
    cNet  = col(df, "REVISED_NET_PAYABLE", "REVISED NET PAYABLE", "NETPAYABLE")
    cSite = col(df, "SITENAME")
    cState= col(df, "SITESTATE")

    pf = num(df, cPf)
    print(f"Total REVISED_PF (authoritative) : Rs {pf.sum():,.2f}")
    print("  -> set the off-by-Rs858 site-total summary cell to its share of this.\n")

    tie = (num(df, cGr) - num(df, cTd) - num(df, cNet)).sum()
    print(f"Row-level tie-out  sum(GROSS - TD - NET) : Rs {tie:,.2f}  (target 0)\n")

    grp = cState if cState else cSite
    if grp:
        print(f"Site-wise REVISED_PF (by {grp}):")
        s = pf.groupby(df[grp]).sum().sort_values(ascending=False)
        for k, v in s.items():
            print(f"  {str(k)[:40]:40s} Rs {v:,.2f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('Usage: python audit_june_pf_tieout.py "June.xlsx" [SheetName]')
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
