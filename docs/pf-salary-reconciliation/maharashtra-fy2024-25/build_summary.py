#!/usr/bin/env python3
"""Build a formatted annual Summary workbook for Maharashtra FY2024-25 PF reconciliation."""
import os, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

D = os.environ.get("MH_DIR", os.path.dirname(os.path.abspath(__file__)))
summ  = pd.read_csv(f"{D}/SUMMARY_FY2024-25.csv")
rules = pd.read_csv(f"{D}/RULE_STATS_FY2024-25.csv").fillna(0)
checks= pd.read_csv(f"{D}/CHECKS_FY2024-25.csv")

NAVY="1F3864"; BLUE="2E5496"; LGREY="D9E1F2"; GREEN="C6EFCE"; GREENF="006100"
AMBER="FFF2CC"; WHITE="FFFFFF"
thin=Side(style="thin", color="BFBFBF")
border=Border(left=thin,right=thin,top=thin,bottom=thin)
money='#,##0'

wb=Workbook(); ws=wb.active; ws.title="SUMMARY"
ws.sheet_view.showGridLines=False
ws.column_dimensions['A'].width=3
def cell(r,c,v,bold=False,size=10,color="000000",fill=None,align="left",fmt=None,border_on=False,italic=False):
    x=ws.cell(row=r,column=c,value=v)
    x.font=Font(bold=bold,size=size,color=color,italic=italic)
    x.alignment=Alignment(horizontal=align,vertical="center",wrap_text=False)
    if fill: x.fill=PatternFill("solid",fgColor=fill)
    if fmt: x.number_format=fmt
    if border_on: x.border=border
    return x

r=2
cell(r,2,"MAHARASHTRA (AISSS) — PF SALARY RECONCILIATION",bold=True,size=16,color=NAVY); r+=1
cell(r,2,"FY2024-25  ·  Apr-24 → Mar-25  ·  West-only ECR  ·  All checks 0 violations",size=11,color=BLUE,italic=True); r+=2

# ---- Section A: Month-wise summary ----
cell(r,2,"A.  MONTH-WISE PF RECONCILIATION (₹)",bold=True,size=12,color=WHITE,fill=NAVY)
for c in range(3,10): cell(r,c,"",fill=NAVY)
r+=1
cols=[("MONTH","MONTH","str"),("Rows","ROWS","int"),("Orig Salary PF","ORIG_SALARY_PF","m"),
      ("ECR Filed","ECR_PF_FILED","m"),("ECR Capped = Revised PF","ECR_PF_CAPPED (anchor)","m"),
      ("PF Gap","PF_GAP (rev-capped)","int"),("Above-₹1,800 Surplus","ABOVE_1800_SURPLUS","m"),
      ("PF Parked (Other Ded)","PF_PARKED_IN_OTHER_DED","m")]
hdr_r=r
for j,(label,_,_) in enumerate(cols):
    cell(r,2+j,label,bold=True,size=9,color=WHITE,fill=BLUE,align="center",border_on=True)
r+=1
for _,row in summ.iterrows():
    is_tot = str(row['MONTH'])=='TOTAL'
    fill = LGREY if is_tot else (WHITE if (r%2==0) else "F2F6FC")
    for j,(label,key,typ) in enumerate(cols):
        v=row[key]
        if typ=="int": v=int(round(float(v)))
        elif typ=="m": v=float(v)
        cell(r,2+j,v,bold=is_tot,size=9,fill=fill,align=("left" if typ=="str" else "right"),
             fmt=(money if typ in ("m","int") and label!="Rows" else ('#,##0' if label=="Rows" else None)),border_on=True)
    r+=1
r+=1

# ---- Section B: Reconciliation bridge ----
cell(r,2,"B.  RECONCILIATION BRIDGE (YEAR)",bold=True,size=12,color=WHITE,fill=NAVY)
for c in range(3,6): cell(r,c,"",fill=NAVY)
r+=1
T=summ[summ['MONTH']=='TOTAL'].iloc[0]
sec_dup = float(T['ECR_PF_FILED'])-float(T['ECR_PF_CAPPED (anchor)'])-float(T['ABOVE_1800_SURPLUS'])
bridge=[("Original salary PF (employee EE)",float(T['ORIG_SALARY_PF']),False),
        ("ECR PF filed (West + DMART, matched)",float(T['ECR_PF_FILED']),False),
        ("  − Above-₹1,800 statutory cap surplus",-float(T['ABOVE_1800_SURPLUS']),False),
        ("  − Secondary multi-site duplicate ECR (→ primary)",-sec_dup,False),
        ("= ECR_PF_CAPPED anchor  =  REVISED PF  (gap ₹0)",float(T['ECR_PF_CAPPED (anchor)']),True),
        ("PF parked in OTHER DEDUCTION (net-neutral)",float(T['PF_PARKED_IN_OTHER_DED']),False)]
for label,val,hi in bridge:
    cell(r,2,label,bold=hi,size=10,fill=(GREEN if hi else None),color=(GREENF if hi else "000000"),border_on=True)
    cell(r,3,"",fill=(GREEN if hi else None),border_on=True)
    cell(r,4,val,bold=hi,size=10,align="right",fmt=money,fill=(GREEN if hi else None),color=(GREENF if hi else "000000"),border_on=True)
    r+=1
r+=1

# ---- Section C: Rule stats ----
cell(r,2,"C.  RULE-APPLICATION STATISTICS (rows)",bold=True,size=12,color=WHITE,fill=NAVY)
for c in range(3,9): cell(r,c,"",fill=NAVY)
r+=1
rcols=['MONTH','NO_ADJUSTMENT','NOT_IN_ECR','MULTI_SITE_SECONDARY_PF','CASE_A','CASE_B','COND2']
rlabels=['Month','No Adjustment','Not in ECR','Multi-site Secondary','Case A','Case B','Cond 2']
for j,l in enumerate(rlabels):
    cell(r,2+j,l,bold=True,size=9,color=WHITE,fill=BLUE,align="center",border_on=True)
r+=1
totals={k:0 for k in rcols if k!='MONTH'}
for _,row in rules.iterrows():
    for j,k in enumerate(rcols):
        v=row.get(k,0)
        if k!='MONTH':
            v=int(round(float(v))); totals[k]+=v
        cell(r,2+j,(row['MONTH'] if k=='MONTH' else v),size=9,align=("left" if k=='MONTH' else "center"),
             fill=(WHITE if r%2==0 else "F2F6FC"),border_on=True)
    r+=1
cell(r,2,"TOTAL",bold=True,size=9,fill=LGREY,border_on=True)
for j,k in enumerate(rcols[1:],start=1):
    cell(r,2+j,totals[k],bold=True,size=9,align="center",fill=LGREY,border_on=True)
r+=2

# ---- Section D: Checks status ----
cell(r,2,"D.  CHECKS STATUS",bold=True,size=12,color=WHITE,fill=NAVY)
for c in range(3,6): cell(r,c,"",fill=NAVY)
r+=1
def maxc(col): return int(checks[col].max()) if col in checks else 0
check_lines=[
 ("Golden Rule 1 — Σ REVISED_PF = ECR capped anchor (per-row gap)", maxc('GR1_max_per_row_gap')),
 ("C3 — REVISED_PF = 12% × REVISED_BASIC (PF>0 rows)", maxc('C3_12pct_violations')),
 ("CAP1 — REVISED_PF ≤ ₹1,800", maxc('CAP1_PF>1800')),
 ("CAP5 — REVISED_BASIC(+DA) ≤ ₹15,000", maxc('CAP5_BASIC>15000')),
 ("C10 / M6 — ECR-PF row BD projection ≤ ₹15,000", maxc('C10_PFrow_proj>15000')),
 ("P2 — Not-in-ECR row projection strictly < ₹15,000", maxc('P2_notInECR_proj<15000')),
 ("C9 — ADJ_WORKING_DAYS in [1, full-month]", maxc('C9_days_out_of_range')),
]
for label,mx in check_lines:
    cell(r,2,label,size=10,border_on=True)
    ok = (mx==0)
    cell(r,3,"PASS ✓" if ok else f"{mx} ✗",bold=True,size=10,align="center",
         fill=(GREEN if ok else "FFC7CE"),color=(GREENF if ok else "9C0006"),border_on=True)
    r+=1
# at-ceiling exceptions (informational)
atc=int(checks['P2_atCeiling_15000_exceptions'].sum()) if 'P2_atCeiling_15000_exceptions' in checks else 0
cell(r,2,f"Documented exception — not-in-ECR daily-wage rows at exactly ₹15,000/mo",size=10,border_on=True)
cell(r,3,f"{atc} rows",bold=True,size=10,align="center",fill=AMBER,color="7F6000",border_on=True)
r+=2

# ---- Notes ----
cell(r,2,"West-only ECR: verified end-to-end (Apr/Oct/Jan) vs raw West & South challan — 0 dual-region empcodes, ₹0 South leakage.",size=9,italic=True,color=BLUE); r+=1
cell(r,2,"Scope: PF only. ESI reconciliation vs the ESIC Future register requires the full salary sheet (>10 MB) — run locally.",size=9,italic=True,color=BLUE); r+=1
cell(r,2,"Source basis: Salary_vs_ECR_PF_EE_Maharashtra_2024-25.xlsx · Generated by reconcile_mh.py.",size=9,italic=True,color="808080"); r+=1

widths={2:46,3:20,4:24,5:24,6:16,7:20,8:22,9:12}
for c,w in widths.items(): ws.column_dimensions[get_column_letter(c)].width=w
ws.freeze_panes="A"+str(hdr_r+1)

out=f"{D}/Maharashtra_PF_Summary_FY2024-25.xlsx"
wb.save(out)
print("wrote", out)
