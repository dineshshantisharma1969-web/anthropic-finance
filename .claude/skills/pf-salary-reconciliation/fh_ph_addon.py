#!/usr/bin/env python3
"""
Festival/National Holiday + Overtime add-on (skill: pf-salary-reconciliation, companion tool).

The monthly M13_FINAL salary sheets carry per-employee OTNET (Overtime), FHAMOUNT/FHESIC/
FHNET (Festival Holiday), and PHAMOUNT/PHESIC/PHNET (Paid/National Holiday) columns. These
are paid alongside the month's salary but are NOT part of REVISED_NET_PAYABLE (the M13
pipeline's anchor column) or the Monthly Summary's "Net Payable" total, so a monthly
reconciliation summary that only reports Net Payable understates what employees actually
received.

This script:
  1. Reads each month's raw M13_FINAL.xlsx, sums OTNET, FHNET and PHNET (net of ESIC) across
     all employees for that month.
  2. Loads an existing Monthly Summary workbook (e.g. ESI_Reallocation_Summary_FRESH.xlsx)
     and adds "Overtime Net" / "Festival Holiday Net" / "National Holiday Net" columns,
     month-matched by name.
  3. Adds a "Net Payable (incl OT/FH/PH)" column = Net Payable + OT Net + FH Net + PH Net.
  4. Recomputes the GRAND TOTAL row from the (now-augmented) monthly rows.

Run locally where the full monthly sheets live (Drive's 10 MB cap / this tool's read
limits make it impossible to total ~19,000-row sheets remotely).

    python fh_ph_addon.py \
        --sheets April_M13_FINAL.xlsx May_M13_FINAL.xlsx ... March_M13_FINAL.xlsx \
        --summary ESI_Reallocation_Summary_FRESH.xlsx \
        --out ESI_Reallocation_Summary_FRESH_with_FHPH.xlsx
"""
from __future__ import annotations
import argparse, re, sys
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

MONTH_ORDER = ["April", "May", "June", "July", "August", "September",
               "October", "November", "December", "January", "February", "March"]
MONTH_RE = re.compile("|".join(MONTH_ORDER), re.IGNORECASE)


def _norm(s):
    return "".join(str(s).strip().upper().split())

def resolve(df, *names, required=True):
    lut = {_norm(c): c for c in df.columns}
    for n in names:
        if _norm(n) in lut:
            return lut[_norm(n)]
    if required:
        raise KeyError(f"None of {names} found. sample={list(df.columns)[:30]}")
    return None

def num(df, *names, required=True):
    c = resolve(df, *names, required=required)
    if c is None:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype(float)

def detect_header(path, maxscan=12):
    raw = pd.read_excel(path, header=None, nrows=maxscan, dtype=object)
    want = {_norm(x) for x in ("EMPCODE", "EMP CODE", "FULLNAME", "NETPAYABLE")}
    for i in range(len(raw)):
        if {_norm(c) for c in raw.iloc[i].tolist()} & want:
            return i
    return 0

def month_from_filename(path):
    m = MONTH_RE.search(path)
    if not m:
        raise ValueError(f"Cannot infer month from filename: {path}")
    name = m.group(0).capitalize()
    return next(mo for mo in MONTH_ORDER if mo.lower() == name.lower())


def fh_ph_totals(paths):
    """Return {month: (ot_net_total, fh_net_total, ph_net_total, employees)} from the raw sheets."""
    out = {}
    for p in paths:
        month = month_from_filename(p)
        hdr = detect_header(p)
        df = pd.read_excel(p, header=hdr)
        ot = num(df, "OTNET", required=False)
        fh = num(df, "FHNET", required=False)
        ph = num(df, "PHNET", required=False)
        out[month] = (round(ot.sum(), 2), round(fh.sum(), 2), round(ph.sum(), 2), len(df))
        print(f"  {month:<10} rows={len(df):>6}  OT_NET={ot.sum():>14,.2f}  "
              f"FH_NET={fh.sum():>14,.2f}  PH_NET={ph.sum():>14,.2f}")
    return out


def augment_summary(summary_path, totals, out_path):
    wb = openpyxl.load_workbook(summary_path)
    ws = wb["Monthly Summary"] if "Monthly Summary" in wb.sheetnames else wb.active

    hdr_row = None
    headers = {}
    for r in range(1, ws.max_row + 1):
        vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        if vals and _norm(vals[0]) == "MONTH":
            hdr_row = r
            headers = {str(v).strip(): c for c, v in enumerate(vals, start=1) if v}
            break
    if hdr_row is None:
        raise KeyError("Could not find the 'Month' header row in the summary sheet")

    month_col = headers["Month"]
    net_col = headers.get("Net Payable")
    if net_col is None:
        raise KeyError("Could not find 'Net Payable' column in the summary sheet")

    last_col = ws.max_column
    ot_col, fh_col, ph_col, newnet_col = last_col + 1, last_col + 2, last_col + 3, last_col + 4
    BOLD = Font(bold=True)
    WHITE = Font(bold=True, color="FFFFFF")
    HDR_FILL = PatternFill("solid", fgColor="1F4E78")
    TOT_FILL = PatternFill("solid", fgColor="DDEBF7")
    thin = Side(style="thin", color="BFBFBF")
    BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
    RIGHT = Alignment(horizontal="right")
    NUMFMT = "#,##0"

    for col, title in ((ot_col, "Overtime Net"), (fh_col, "Festival Holiday Net"),
                       (ph_col, "National Holiday Net"), (newnet_col, "Net Payable (incl OT/FH/PH)")):
        c = ws.cell(row=hdr_row, column=col, value=title)
        c.font = WHITE; c.fill = HDR_FILL; c.border = BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    grand_row = None
    for r in range(hdr_row + 1, ws.max_row + 1):
        m = ws.cell(row=r, column=month_col).value
        if m is None:
            continue
        if _norm(m) == "GRANDTOTAL":
            grand_row = r
            continue
        if m not in totals:
            raise KeyError(f"No OT/FH/PH totals supplied for month '{m}' found in summary row {r}")
        ot, fh, ph, _ = totals[m]
        net = ws.cell(row=r, column=net_col).value or 0
        for col, val in ((ot_col, ot), (fh_col, fh), (ph_col, ph), (newnet_col, net + ot + fh + ph)):
            cc = ws.cell(row=r, column=col, value=val)
            cc.border = BORDER; cc.number_format = NUMFMT; cc.alignment = RIGHT

    if grand_row is not None:
        for col in (ot_col, fh_col, ph_col, newnet_col):
            total = sum(ws.cell(row=r, column=col).value or 0
                        for r in range(hdr_row + 1, grand_row))
            cc = ws.cell(row=grand_row, column=col, value=round(total, 2))
            cc.fill = TOT_FILL; cc.border = BORDER; cc.font = BOLD
            cc.number_format = NUMFMT; cc.alignment = RIGHT

    for col in (ot_col, fh_col, ph_col, newnet_col):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 16

    wb.save(out_path)
    return grand_row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheets", nargs="+", required=True,
                    help="the 12 raw *_M13_FINAL.xlsx files (any order)")
    ap.add_argument("--summary", required=True,
                    help="existing Monthly Summary workbook to augment "
                         "(e.g. ESI_Reallocation_Summary_FRESH.xlsx)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    print("Reading OT/FH/PH totals from the raw monthly sheets...")
    totals = fh_ph_totals(a.sheets)

    missing = set(MONTH_ORDER) - set(totals)
    if missing:
        print(f"  WARNING: no sheet supplied for {sorted(missing)} - "
              f"those months' OT/FH/PH will be left blank if present in the summary")

    print(f"\nAugmenting {a.summary} -> {a.out}")
    grand_row = augment_summary(a.summary, totals, a.out)

    ot_total = sum(v[0] for v in totals.values())
    fh_total = sum(v[1] for v in totals.values())
    ph_total = sum(v[2] for v in totals.values())
    print(f"\nFY totals from supplied sheets: OT_NET={ot_total:,.2f}  "
          f"FH_NET={fh_total:,.2f}  PH_NET={ph_total:,.2f}")
    print(f"GRAND TOTAL row: {'recomputed at row ' + str(grand_row) if grand_row else 'not found - not recomputed'}")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
