#!/usr/bin/env python3
"""Consolidated Dec-25 -> Mar-26 Wage Code 50% pack (law live from 21-11-2025).
Reads the WAGE_CODE_50PCT tab of each month's worklist, dedupes by EMPCODE,
prices the ER-side cost of restructuring to 50% (PF ~13% + gratuity 4.81%)."""
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill
from collections import defaultdict

MONTHS = [("Dec-25","Dec25_WORKLIST_Recovery_ESI_WageCode.xlsx"),
          ("Jan-26","Jan25_WORKLIST_Recovery_ESI_WageCode.xlsx"),
          ("Feb-26","Feb25_WORKLIST_Recovery_ESI_WageCode.xlsx"),
          ("Mar-26","Mar25_WORKLIST_Recovery_ESI_WageCode.xlsx")]
PF_ER, GRAT = 0.13, 0.0481   # employer PF+admin ~13%, gratuity accrual 4.81%

emp = {}                      # EMPCODE -> record
permonth = []
for mon, f in MONTHS:
    wb = load_workbook(f, read_only=True)
    ws = wb["WAGE_CODE_50PCT"]
    rows = list(ws.iter_rows(values_only=True)); hdr = list(rows[0]); rows = rows[1:]
    i = {h: k for k, h in enumerate(hdr)}
    n_struct = n_sev = 0; short = 0.0
    for r in rows:
        code = str(r[i['EMPCODE']])
        note = str(r[i['NOTE']] or '')
        structural = (note == '')
        n_struct += structural
        n_sev += (r[i['SEVERITY']] == '<30%' and structural)
        sh = float(r[i['SHORTFALL_TO_50PCT']] or 0)
        short += max(0.0, sh)
        rec = emp.setdefault(code, {"name": r[i['FULLNAME']], "client": r[i['CLIENTGROUPNAME']],
                                    "site": r[i['SITENAME']], "months": [], "struct_months": 0})
        rec["months"].append(mon)
        rec["struct_months"] += structural
        # keep latest month's economics (files processed in date order)
        rec.update(basic_da=float(r[i['BASIC+DA']] or 0), ctc=float(r[i['CTC']] or 0),
                   ratio=float(r[i['BASIC+DA % OF CTC']] or 0), short=max(0.0, sh),
                   target=float(r[i['TARGET_BASIC_DA (=50% CTC)']] or 0),
                   last=mon, note=note, days=r[i['NORMALDAYS']])
    permonth.append((mon, len(rows), n_struct, n_sev, short))
    wb.close()
    print(f"{mon}: {len(rows)} fails ({n_struct} structural, {n_sev} severe) shortfall {short:,.0f}")

persistent = {c: r for c, r in emp.items() if r["struct_months"] >= 2}
by_client = defaultdict(lambda: [0, 0.0, 0.0])
for c, r in persistent.items():
    er_delta = r["short"] * (PF_ER + GRAT)
    by_client[r["client"]][0] += 1
    by_client[r["client"]][1] += r["short"]
    by_client[r["client"]][2] += er_delta

HDRF = PatternFill("solid", start_color="1F4E79"); HF = Font(bold=True, color="FFFFFF")
RED = PatternFill("solid", start_color="FFC7CE")
out = Workbook(); out.remove(out.active)
def sheet(t, hdrs):
    s = out.create_sheet(t); s.append(hdrs)
    for c in s[1]: c.fill, c.font = HDRF, HF
    s.freeze_panes = "A2"; return s

s = sheet("SUMMARY", ["", "VALUE"])
s.append(["Law: Code on Wages 2019 s.2(y) — in force 21-11-2025; months covered", "Dec-25, Jan-26, Feb-26, Mar-26"])
s.append(["Employees failing 50% in ≥1 covered month", len(emp)])
s.append(["PERSISTENT structural failers (≥2 months) — the restructuring list", len(persistent)])
s.append(["Monthly Basic+DA shortfall to 50% (persistent, latest month)", round(sum(r['short'] for r in persistent.values()), 0)])
s.append(["Monthly ER cost of restructuring (PF ~13% + gratuity 4.81% on shortfall)", round(sum(r['short']*(PF_ER+GRAT) for r in persistent.values()), 0)])
s.append([])
s.append(["MONTH", "FAILS", "STRUCTURAL", "SEVERE <30%", "SHORTFALL (Rs.)"])
for c in range(1, 6): s.cell(row=s.max_row, column=c).fill, s.cell(row=s.max_row, column=c).font = HDRF, HF
for mon, n, st, sv, sh in permonth: s.append([mon, n, st, sv, round(sh, 0)])

s = sheet("BY_CLIENT", ["CLIENT", "PERSISTENT FAILERS", "MONTHLY SHORTFALL (Rs.)", "MONTHLY ER COST TO FIX (Rs.)"])
for cl, (n, sh, er) in sorted(by_client.items(), key=lambda x: -x[1][1]):
    s.append([cl, n, round(sh, 0), round(er, 0)])

s = sheet("PERSISTENT_FAILERS", ["EMPCODE","NAME","CLIENT","SITE","MONTHS FAILED","LAST MONTH","BASIC+DA","CTC",
                                 "B+DA % CTC","TARGET (=50% CTC)","MONTHLY SHORTFALL","ER COST DELTA/MONTH",
                                 "RESTRUCTURE (Y/N)","EFFECTIVE_MONTH","REMARKS"])
for code, r in sorted(persistent.items(), key=lambda x: -x[1]["short"]):
    s.append([code, r["name"], r["client"], r["site"], f"{r['struct_months']}/4 ({', '.join(r['months'])})",
              r["last"], round(r["basic_da"],0), round(r["ctc"],0), r["ratio"], round(r["target"],0),
              round(r["short"],0), round(r["short"]*(PF_ER+GRAT),0), "", "", ""])
    if r["ratio"] < 30:
        for c in s[s.max_row]: c.fill = RED

for ws_ in out.worksheets:
    for col in ws_.columns:
        w = max((len(str(c.value)) for c in col if c.value is not None), default=8)
        ws_.column_dimensions[col[0].column_letter].width = min(46, max(10, w+2))
out.save("Dec25_Mar26_WAGECODE_50PCT_PACK.xlsx")
print(f"\nPACK: {len(emp)} total failers, {len(persistent)} persistent; "
      f"shortfall Rs.{sum(r['short'] for r in persistent.values()):,.0f}/mo; "
      f"ER cost Rs.{sum(r['short']*(PF_ER+GRAT) for r in persistent.values()):,.0f}/mo")
