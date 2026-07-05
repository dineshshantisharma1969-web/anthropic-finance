#!/usr/bin/env python3
"""Wage Code 50% pack v2 — Dec-25..Mar-26, FAQ-adjusted denominator.
Per MoLE Additional FAQs (16.03.2026): remuneration EXCLUDES gratuity & ER-ESI,
INCLUDES ER PF/pension + statutory bonus. Denominator = CTC - GRATUITY_PROVISION
- ESIC COMPANY. Numerator = earned BASIC + DA (REVISED_DA where no DA col)."""
import re, sys
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill
from collections import defaultdict

U = "/root/.claude/uploads/024fbf27-08ad-5a18-b65d-12bc1d64e2a1"
MONTHS = [("Dec-25", f"{U}/91ba4dd3-December_M13_FINAL.xlsx"),
          ("Jan-26", f"{U}/d6f5981d-January_M13_FINAL.xlsx"),
          ("Feb-26", f"{U}/8be0a71b-February_M13_FINAL.xlsx"),
          ("Mar-26", f"{U}/1463ff5d-March_M13_FINAL.xlsx")]
PF_ER, GRAT = 0.13, 0.0481

def num(v):
    if v is None: return 0.0
    if isinstance(v,(int,float)): return float(v)
    s=re.sub(r"[^0-9.\-]","",str(v))
    try: return float(s) if s not in ("","-",".") else 0.0
    except ValueError: return 0.0

emp = {}; permonth = []
for mon, path in MONTHS:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb["Salary (Corrected)"]
    it = ws.iter_rows(values_only=True)
    hdr=None
    for row in it:
        if row and any(str(v).strip()=="EMPCODE" for v in row if v): hdr=list(row); break
    ix={str(h).strip():i for i,h in enumerate(hdr) if h is not None}
    g=lambda r,c: r[ix[c]] if c in ix and ix[c]<len(r) else None
    gn=lambda r,c: num(g(r,c))
    fails=0; short_t=0.0; n_v1_only=0; total_rows=0
    for r in it:
        if r is None or not any(v is not None for v in r): continue
        b = gn(r,'BASIC'); d = gn(r,'DA') if 'DA' in ix else gn(r,'REVISED_DA')
        ctc, gr = gn(r,'CTC'), gn(r,'GROSS AMT')
        if ctc<=0 or (b+d)<=0 or gr<0: continue
        total_rows+=1
        rem = ctc - gn(r,'GRATUITY_PROVISION') - gn(r,'ESIC COMPANY')   # FAQ-adjusted
        if rem<=0: continue
        ratio_v2 = (b+d)/rem
        if (b+d)/ctc < 0.5 and ratio_v2 >= 0.5: n_v1_only+=1
        if ratio_v2 >= 0.5: continue
        ot_arr = gn(r,'OT AMOUNT')+gn(r,'EXTRA OT')+gn(r,'BASIC DA ARREARS')+gn(r,'OTHER ARREARS')
        note = ('OT/ARREARS-HEAVY' if ot_arr>gr*0.5 else
                'LOW-DAY ROW' if gn(r,'NORMALDAYS')<=2 else '')
        sh = max(0.0, rem*0.5-(b+d)); fails+=1; short_t+=sh
        code=str(g(r,'EMPCODE'))
        rec = emp.setdefault(code, {"name":g(r,'FULLNAME'),"client":g(r,'CLIENTGROUPNAME'),
                                    "site":g(r,'SITENAME'),"months":[],"struct":0})
        rec["months"].append(mon); rec["struct"] += (note=='')
        rec.update(bd=b+d, rem=rem, ctc=ctc, ratio=round(ratio_v2*100,1), short=sh,
                   target=rem*0.5, last=mon, note=note)
    permonth.append((mon,fails,short_t,n_v1_only,total_rows))
    wb.close()
    print(f"{mon}: v2 fails {fails:,} shortfall {short_t:,.0f} (cleared vs v1-CTC-basis: {n_v1_only})")

persistent = {c:r for c,r in emp.items() if r["struct"]>=2}
by_client = defaultdict(lambda:[0,0.0])
for c,r in persistent.items():
    by_client[r["client"]][0]+=1; by_client[r["client"]][1]+=r["short"]

HDRF=PatternFill("solid",start_color="1F4E79"); HF=Font(bold=True,color="FFFFFF")
RED=PatternFill("solid",start_color="FFC7CE")
out=Workbook(); out.remove(out.active)
def sheet(t,h):
    s=out.create_sheet(t); s.append(h)
    for c in s[1]: c.fill,c.font=HDRF,HF
    s.freeze_panes="A2"; return s
s=sheet("SUMMARY",["","VALUE"])
s.append(["Method (v2 — per MoLE FAQ 16.03.2026)","Numerator: earned BASIC+DA. Denominator: CTC − GRATUITY_PROVISION − ESIC COMPANY (gratuity & ER-ESI excluded from remuneration per FAQ 1; ER PF + statutory bonus remain included)"])
s.append(["Employees failing in ≥1 month (Dec-25→Mar-26)",len(emp)])
s.append(["PERSISTENT structural failers (≥2 months) — restructuring list",len(persistent)])
s.append(["Monthly shortfall to 50% (persistent, latest month)",round(sum(r['short'] for r in persistent.values()),0)])
s.append(["Monthly ER cost to fix (PF ~13% + gratuity 4.81%)",round(sum(r['short']*(PF_ER+GRAT) for r in persistent.values()),0)])
s.append([])
s.append(["MONTH","V2 FAILS","V2 SHORTFALL (Rs.)","ROWS CLEARED vs v1 (CTC basis)"])
for c in range(1,5): s.cell(row=s.max_row,column=c).fill,s.cell(row=s.max_row,column=c).font=HDRF,HF
for mon,f,sh,cl,_ in permonth: s.append([mon,f,round(sh,0),cl])
s=sheet("BY_CLIENT",["CLIENT","PERSISTENT FAILERS","MONTHLY SHORTFALL (Rs.)","MONTHLY ER COST TO FIX (Rs.)"])
for cl,(n,sh) in sorted(by_client.items(),key=lambda x:-x[1][1]):
    s.append([cl,n,round(sh,0),round(sh*(PF_ER+GRAT),0)])
s=sheet("PERSISTENT_FAILERS",["EMPCODE","NAME","CLIENT","SITE","MONTHS FAILED","LAST","BASIC+DA",
                              "REMUNERATION (FAQ-adj)","CTC","B+DA % REM","TARGET (=50% REM)",
                              "MONTHLY SHORTFALL","ER COST/MONTH","RESTRUCTURE (Y/N)","EFFECTIVE_MONTH","REMARKS"])
for code,r in sorted(persistent.items(),key=lambda x:-x[1]["short"]):
    s.append([code,r["name"],r["client"],r["site"],f"{r['struct']}/4 ({', '.join(r['months'])})",r["last"],
              round(r["bd"],0),round(r["rem"],0),round(r["ctc"],0),r["ratio"],round(r["target"],0),
              round(r["short"],0),round(r["short"]*(PF_ER+GRAT),0),"","",""])
    if r["ratio"]<30:
        for c in s[s.max_row]: c.fill=RED
for w in out.worksheets:
    for col in w.columns:
        wd=max((len(str(c.value)) for c in col if c.value is not None),default=8)
        w.column_dimensions[col[0].column_letter].width=min(50,max(10,wd+2))
out.save("Dec25_Mar26_WAGECODE_50PCT_PACK_v2.xlsx")
print(f"\nV2 PACK: {len(emp)} failers, {len(persistent)} persistent; shortfall Rs.{sum(r['short'] for r in persistent.values()):,.0f}/mo; ER cost Rs.{sum(r['short']*(PF_ER+GRAT) for r in persistent.values()):,.0f}/mo")
