#!/usr/bin/env python3
"""
Rule M17 — Monthly Recovery & ESI Worklist generator.

Takes a reconciled monthly file (AFTER Rule M16 is applied) and produces
<Mon>_WORKLIST_Recovery_ESI.xlsx with three tabs:

  1. SUMMARY          — headline counts/amounts + by-client breakdown
  2. RECOVERY_REVIEW  — overpaid-vs-rate employees, HIGH priority (> Rs.10k)
                        highlighted & on top, with working columns:
                        VERIFIED / DECISION / RECOVERY_MONTH / REMARKS
  3. ESI_ENROLLMENT   — ESI-eligible-but-exempt employees grouped by client,
                        with EE/ER contribution columns and working columns:
                        IC_NO_ALLOTTED / ENROLLED_FROM / REMARKS
  4. WAGE_CODE_50PCT  — Code on Wages 2019 test: rows where BASIC+DA < 50% of
                        CTC (wages must be >= 50% of total remuneration).
                        Severity-banded (<30% highlighted), with working
                        columns: RESTRUCTURE (Y/N) / TARGET_BASIC_DA / REMARKS.
                        CTC is located by header name 'CTC' (column FI in the
                        April-26 reconciled layout).

Usage:  python make_worklist_M17.py <Month_RECONCILED_M16.xlsx> <output.xlsx>
Needs:  pip install openpyxl
"""
import sys
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

HDR_FILL = PatternFill("solid", fgColor="1F4E79")
HDR_FONT = Font(color="FFFFFF", bold=True, size=10)
HI_FILL  = PatternFill("solid", fgColor="FFC7CE")   # high priority (red-ish)
OK_FILL  = PatternFill("solid", fgColor="C6EFCE")   # section headers (green-ish)
TOT_FONT = Font(bold=True)
THIN = Border(bottom=Side(style="thin", color="D9D9D9"))

def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = ws.cell(row=row + 1, column=1)

def autowidth(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def main(src, dst):
    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    ix = {h: i for i, h in enumerate(hdr)}
    rows = [r for r in it if r is not None]

    def g(r, col):
        return r[ix[col]] if col in ix and ix[col] < len(r) else None

    # -- classify ----------------------------------------------------------
    recovery, esi = [], []
    for r in rows:
        if str(g(r, 'ACTION_NEEDED') or '').strip().upper() != 'Y':
            continue
        reason = str(g(r, 'ACTION_REASON') or '').upper()
        if 'ESI-EXEMPT' in reason:
            esi.append(r)
        elif 'PAID ABOVE' in reason or 'IMPLIED' in reason:
            recovery.append(r)

    out = Workbook()

    # -- Tab 2: RECOVERY_REVIEW ----------------------------------------------
    # Rule M18 (day-basis correction): FIXEDGROSS is expressed at the
    # SITEDIVISIONDAYS divisor (1 = per-day rate, else 26/27/28/30/31 = monthly
    # at that divisor). Expected pay = FIXEDGROSS / SITEDIVISIONDAYS x NORMALDAYS.
    # EXCESS_TO_REVIEW = clamp(GROSS - EXPECTED, 0, GROSS). Rows the day-basis
    # clears (excess <= 0) are dropped from the tab and counted in SUMMARY.
    rec_cols = ['PRIORITY', 'NOTE', 'EMPCODE', 'FULLNAME', 'CLIENTGROUPNAME', 'SITENAME',
                'SITESTATE', 'DESIGNATIONNAME', 'RATE_BASIS', 'FIXEDGROSS',
                'NORMALDAYS', 'EXPECTED_GROSS (rate/div×days)', 'GROSS AMT',
                'OT+ARREARS', 'ATTENDANCE ALW', 'EXCESS_TO_REVIEW',
                'VERIFIED (Y/N)', 'DECISION (RECOVER/WAIVE/JUSTIFIED)',
                'RECOVERY_MONTH', 'REMARKS']
    wr = out.active
    wr.title = "RECOVERY_REVIEW"
    wr.append(rec_cols)
    style_header(wr, len(rec_cols))

    def daybasis(r):
        div = num(g(r, 'SITEDIVISIONDAYS')) or 30
        days = num(g(r, 'NORMALDAYS'))
        fg = num(g(r, 'FIXEDGROSS'))
        gr = num(g(r, 'GROSS AMT'))
        expected = fg / div * days if div > 0 else fg
        exc = max(0.0, min(gr - expected, gr))
        return div, days, fg, gr, expected, exc

    cleared = 0
    cleared_amt = 0.0
    kept = []
    for r in recovery:
        div, days, fg, gr, expected, exc = daybasis(r)
        old = min(num(g(r, 'EXCESS_SALARY')), gr)
        if exc < 1:
            cleared += 1
            cleared_amt += old
            continue
        kept.append((exc, div, days, fg, gr, expected, r))
    kept.sort(key=lambda x: -x[0])
    n_hi = 0
    rec_total = hi_total = 0.0
    for exc, div, days, fg, gr, expected, r in kept:
        ot_arr = (num(g(r, 'OT AMOUNT')) + num(g(r, 'EXTRA OT')) +
                  num(g(r, 'BASIC DA ARREARS')) + num(g(r, 'OTHER ARREARS')))
        note = 'OT/ARREARS may explain' if ot_arr >= exc else ''
        hi = exc > 10000
        n_hi += hi
        rec_total += exc
        hi_total += exc if hi else 0
        wr.append(['HIGH' if hi else 'LOW', note, g(r, 'EMPCODE'), g(r, 'FULLNAME'),
                   g(r, 'CLIENTGROUPNAME'), g(r, 'SITENAME'), g(r, 'SITESTATE'),
                   g(r, 'DESIGNATIONNAME'),
                   'PER-DAY' if div == 1 else f'MONTHLY/{int(div)}',
                   round(fg, 0), days, round(expected, 0), round(gr, 0),
                   round(ot_arr, 0), round(num(g(r, 'ATTENDANCE ALW')), 0),
                   round(exc, 0), '', '', '', ''])
        if hi:
            for c in range(1, len(rec_cols) + 1):
                wr.cell(row=wr.max_row, column=c).fill = HI_FILL
    autowidth(wr, [8, 22, 11, 24, 26, 24, 14, 18, 11, 10, 8, 13, 10, 10, 9, 12, 9, 16, 12, 24])

    # -- Tab 3: ESI_ENROLLMENT ---------------------------------------------
    esi_cols = ['EMPCODE', 'FULLNAME', 'CLIENTGROUPNAME', 'SITENAME', 'SITESTATE',
                'ESIC NO', 'UAN NO', 'GROSS AMT', 'REAL_FULL_MONTH_GROSS',
                'ESI_EE_0.75%', 'ESI_ER_3.25%', 'IC_NO_ALLOTTED',
                'ENROLLED_FROM (month)', 'REMARKS']
    we = out.create_sheet("ESI_ENROLLMENT")
    we.append(esi_cols)
    style_header(we, len(esi_cols))
    esi.sort(key=lambda r: (str(g(r, 'CLIENTGROUPNAME') or ''), -num(g(r, 'GROSS AMT'))))
    esi_gross = 0.0
    for r in esi:
        gr = num(g(r, 'GROSS AMT'))
        esi_gross += gr
        we.append([g(r, 'EMPCODE'), g(r, 'FULLNAME'), g(r, 'CLIENTGROUPNAME'),
                   g(r, 'SITENAME'), g(r, 'SITESTATE'), g(r, 'ESIC NO'),
                   g(r, 'UAN NO'), gr, num(g(r, 'REAL_FULL_MONTH_GROSS')),
                   round(gr * 0.0075, 0), round(gr * 0.0325, 0), '', '', ''])
    autowidth(we, [11, 24, 26, 24, 14, 14, 14, 10, 12, 10, 10, 14, 12, 24])

    # -- Tab 4: WAGE_CODE_50PCT ----------------------------------------------
    wc_cols = ['SEVERITY', 'NOTE', 'EMPCODE', 'FULLNAME', 'CLIENTGROUPNAME', 'SITENAME',
               'SITESTATE', 'DESIGNATIONNAME', 'NORMALDAYS', 'BASIC', 'DA', 'BASIC+DA',
               'OT+ARREARS', 'GROSS AMT', 'CTC', 'BASIC+DA % OF CTC', 'SHORTFALL_TO_50PCT',
               'RESTRUCTURE (Y/N)', 'TARGET_BASIC_DA (=50% CTC)', 'REMARKS']
    ww = out.create_sheet("WAGE_CODE_50PCT")
    ww.append(wc_cols)
    style_header(ww, len(wc_cols))
    wage_fail, neg_gross = [], 0
    for r in rows:
        b, d, ctc = num(g(r, 'BASIC')), num(g(r, 'DA')), num(g(r, 'CTC'))
        gr = num(g(r, 'GROSS AMT'))
        if ctc <= 0 or (b + d) <= 0:
            continue                       # zero-basic skip rows / no CTC
        if gr < 0:                         # salary-reversal rows are not wage structures
            neg_gross += 1
            continue
        ratio = (b + d) / ctc
        if ratio < 0.5:
            ot_arr = (num(g(r, 'OT AMOUNT')) + num(g(r, 'EXTRA OT')) +
                      num(g(r, 'BASIC DA ARREARS')) + num(g(r, 'OTHER ARREARS')))
            wage_fail.append((ratio, b, d, ctc, gr, ot_arr, r))
    wage_fail.sort(key=lambda x: x[0])     # worst ratio first
    n_sev = n_struct = 0
    for ratio, b, d, ctc, gr, ot_arr, r in wage_fail:
        sev = '<30%' if ratio < 0.30 else ('30-40%' if ratio < 0.40 else
              ('40-45%' if ratio < 0.45 else '45-50%'))
        note = ''
        if ot_arr > gr * 0.5:
            note = 'OT/ARREARS-HEAVY — remuneration inflated this month'
        elif num(g(r, 'NORMALDAYS')) <= 2:
            note = 'LOW-DAY ROW — verify'
        else:
            n_struct += 1
        target = round(ctc * 0.5, 0)
        ww.append([sev, note, g(r, 'EMPCODE'), g(r, 'FULLNAME'), g(r, 'CLIENTGROUPNAME'),
                   g(r, 'SITENAME'), g(r, 'SITESTATE'), g(r, 'DESIGNATIONNAME'),
                   num(g(r, 'NORMALDAYS')), round(b, 0), round(d, 0), round(b + d, 0),
                   round(ot_arr, 0), round(gr, 0), round(ctc, 0),
                   round(ratio * 100, 1), round(target - (b + d), 0),
                   '', target, ''])
        if ratio < 0.30 and not note:
            n_sev += 1
            for c in range(1, len(wc_cols) + 1):
                ww.cell(row=ww.max_row, column=c).fill = HI_FILL
    autowidth(ww, [8, 34, 11, 24, 26, 24, 14, 18, 8, 9, 8, 10, 10, 10, 10, 11, 12, 9, 14, 24])

    # -- Tab 1: SUMMARY ------------------------------------------------------
    s = out.create_sheet("SUMMARY", 0)
    s.append(["MONTHLY WORKLIST — RECOVERY REVIEW & ESI ENROLLMENT (Rule M17)"])
    s.cell(row=1, column=1).font = Font(bold=True, size=13)
    s.append([f"Source: {src.split('/')[-1]}  ·  Excess values are M16 cash-capped"])
    s.append([])
    s.append(["WORKSTREAM", "EMPLOYEES", "AMOUNT (Rs.)", "WHERE"])
    for c in range(1, 5):
        s.cell(row=4, column=c).fill = HDR_FILL
        s.cell(row=4, column=c).font = HDR_FONT
    s.append(["Recovery review — HIGH priority (> Rs.10k each)", n_hi, round(hi_total, 0),
              "Tab RECOVERY_REVIEW (red rows, on top; M18 day-basis excess)"])
    s.cell(row=5, column=1).fill = HI_FILL
    s.append(["Recovery review — remaining (small amounts)", len(kept) - n_hi,
              round(rec_total - hi_total, 0), "Tab RECOVERY_REVIEW"])
    s.append(["Cleared by M18 day-basis correction (rate/div × days)", cleared,
              round(cleared_amt, 0), "Removed from tab — expected pay >= gross once FIXEDGROSS read at its divisor"])
    s.append(["ESI enrollment needed (eligible, currently exempt)", len(esi),
              round(esi_gross * 0.04, 0), "Tab ESI_ENROLLMENT (amount = 4%/month exposure)"])
    wc_short = sum(max(0.0, ctc * 0.5 - (b + d)) for _, b, d, ctc, _g, _o, _r in wage_fail)
    s.append(["Wage Code 50% test FAIL (Basic+DA < 50% of CTC)", len(wage_fail),
              round(wc_short, 0),
              f"Tab WAGE_CODE_50PCT ({n_struct} structural; rest OT/arrears/low-day — see NOTE col; "
              f"{neg_gross} negative-gross reversal rows excluded)"])
    s.append(["TOTAL (working rows)", len(kept) + len(esi) + len(wage_fail), "", ""])
    s.cell(row=s.max_row, column=1).font = TOT_FONT
    s.cell(row=s.max_row, column=2).font = TOT_FONT
    s.append([])
    # by-client tables
    from collections import defaultdict
    def byclient(rowset, valfn):
        d = defaultdict(lambda: [0, 0.0])
        for r in rowset:
            k = str(g(r, 'CLIENTGROUPNAME') or 'UNKNOWN')[:45]
            d[k][0] += 1
            d[k][1] += valfn(r)
        return sorted(d.items(), key=lambda x: -x[1][1])
    s.append(["RECOVERY BY CLIENT (top 10, M18 day-basis)", "EMPLOYEES", "EXCESS (Rs.)"])
    s.cell(row=s.max_row, column=1).fill = OK_FILL
    s.cell(row=s.max_row, column=1).font = TOT_FONT
    rec_cl = defaultdict(lambda: [0, 0.0])
    for exc, div, days, fg, gr, expected, r in kept:
        k = str(g(r, 'CLIENTGROUPNAME') or 'UNKNOWN')[:45]
        rec_cl[k][0] += 1
        rec_cl[k][1] += exc
    for k, (n_, v) in sorted(rec_cl.items(), key=lambda x: -x[1][1])[:10]:
        s.append([k, n_, round(v, 0)])
    s.append([])
    s.append(["ESI ENROLLMENT BY CLIENT (top 10)", "EMPLOYEES", "4%/MONTH EXPOSURE (Rs.)"])
    s.cell(row=s.max_row, column=1).fill = OK_FILL
    s.cell(row=s.max_row, column=1).font = TOT_FONT
    for k, (n, v) in byclient(esi, lambda r: num(g(r, 'GROSS AMT')) * 0.04)[:10]:
        s.append([k, n, round(v, 0)])
    s.append([])
    s.append(["WAGE CODE 50% FAILS BY CLIENT (top 10)", "EMPLOYEES", "SHORTFALL (Rs.)"])
    s.cell(row=s.max_row, column=1).fill = OK_FILL
    s.cell(row=s.max_row, column=1).font = TOT_FONT
    from collections import defaultdict as dd
    wc_cl = dd(lambda: [0, 0.0])
    for ratio, b, d, ctc, _g2, _o2, r in wage_fail:
        k = str(g(r, 'CLIENTGROUPNAME') or 'UNKNOWN')[:45]
        wc_cl[k][0] += 1
        wc_cl[k][1] += max(0.0, ctc * 0.5 - (b + d))
    for k, (n_, v) in sorted(wc_cl.items(), key=lambda x: -x[1][0])[:10]:
        s.append([k, n_, round(v, 0)])
    autowidth(s, [52, 12, 16, 42])

    out.save(dst)
    print(f"worklist written: {dst}")
    print(f"  RECOVERY_REVIEW : {len(kept):,} rows (HIGH {n_hi}, Rs.{hi_total:,.0f}) · total Rs.{rec_total:,.0f} · M18 cleared {cleared} rows (Rs.{cleared_amt:,.0f} old excess)")
    print(f"  ESI_ENROLLMENT  : {len(esi):,} rows · 4%/month exposure Rs.{esi_gross*0.04:,.0f}")
    print(f"  WAGE_CODE_50PCT : {len(wage_fail):,} rows (<30% severe: {n_sev}) · monthly shortfall to 50% Rs.{wc_short:,.0f}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
