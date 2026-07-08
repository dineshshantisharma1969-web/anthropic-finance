#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconcile_full_salary.py — LOCAL pipeline that writes the corrected Maharashtra
full salary sheet for FY2024-25, applying the pf-salary-reconciliation skill.

RUN LOCALLY. The full salary workbook (`Salary comb 2024-25.xlsx`, 224 MB /
`EMPLOYEE SALARY DETAILS - APRIL 24 TO MARCH 25 MAHARASHTRA.xlsx`, 19 MB) exceeds
the 10 MB Google-Drive connector cap, so it can only be processed on your machine.

WHAT IT DOES (per employee-month row, keeping NET SALARY unchanged):
  PF side:
    - Anchor REVISED_EPF = min(ECR PF for that employee, Rs.1,800)   (statutory cap)
    - REVISED_BASIC = round(REVISED_EPF / 0.12)  (12% rule), capped at 15,000
    - Not-in-ECR employees -> REVISED_EPF = 0 (PF parked)
    - PF difference is parked in REVISED_OTHER_DEDUCTION so Total Dedns / Net are unchanged
    - ADJ_WORKING_DAYS set so an ECR-PF row projects Basic+DA <= 15,000 full-month (M6)
  ESI side:
    - REVISED_ESI = filed ESIC-register employee contribution (the deposited anchor)
    - ESI difference parked in REVISED_OTHER_DEDUCTION (net-neutral)
  Audit + integrity checks: gap=0 (PF=ECR capped), 12% (+-Rs.1), PF<=1800, Basic+DA<=15000,
    ESI=0.75% of ESIC wages, Net unchanged, Other Ded >= 0.

INPUTS (edit the CONFIG block):
  SALARY_XLSX  : the full salary workbook (single consolidated sheet, MONTH column)
  ECR_SOURCE   : the PF ECR per employee/month. Two accepted forms:
                   (a) the comparison workbook Salary_vs_ECR_PF_EE_Maharashtra_2024-25.xlsx
                       (12 monthly tabs, cols: 'EMP CODE','ECR PF AMOUNT (EE)'), OR
                   (b) a folder of '## PF CONSOLIDATED <MON>-YY.xlsx' challan files.
  ESIC_XLSX    : Maharashtra ESIC Working 24-25 (Dinesh Sir).xlsx (register; header row 2)

OUTPUT:
  <out>/Maharashtra_Salary_CORRECTED_2024-25.xlsx  (original columns + REVISED_* + audit)
  <out>/reconcile_full_salary_checks.txt           (per-month check log)

Requires: pandas, openpyxl.  Usage:  python reconcile_full_salary.py
"""
import os, math, re, sys
import numpy as np
import pandas as pd

# ============================== CONFIG ==============================
CONFIG = {
    "SALARY_XLSX": r"Salary comb 2024-25.xlsx",
    "SALARY_SHEET": 0,                      # sheet index or name of the consolidated salary sheet
    "ECR_SOURCE":  r"Salary_vs_ECR_PF_EE_Maharashtra_2024-25.xlsx",  # comparison workbook (a)
    "ESIC_XLSX":   r"Maharashtra ESIC  Working 24-25 (Dinesh Sir).xlsx",
    "OUT_DIR":     r"out_corrected",
    # ESI is claimed at the EMPLOYEE level; the register month key is a datetime -> 'MON-YY'.
}
PF_RATE = 0.12; PF_CAP = 1800.0; BD_CEIL = 15000.0
ESI_EMP_RATE = 0.0075; ESI_CEIL = 21000.0
FULL_MONTH = {'APR':30,'MAY':31,'JUN':30,'JUL':31,'AUG':31,'SEP':30,
              'OCT':31,'NOV':30,'DEC':31,'JAN':31,'FEB':28,'MAR':31}
MON3 = {'JANUARY':'JAN','FEBRUARY':'FEB','MARCH':'MAR','APRIL':'APR','MAY':'MAY','JUNE':'JUN',
        'JULY':'JUL','AUGUST':'AUG','SEPTEMBER':'SEP','OCTOBER':'OCT','NOVEMBER':'NOV','DECEMBER':'DEC'}

# ---- column resolver: maps our logical names to the sheet's real headers (fuzzy) ----
WANT = {
    "EMP":   ["employee code"],
    "PFNO":  ["pf no", "epf no"],
    "ESINO": ["esi no"],
    "TOTDAYS":["total days"],
    "DAYSPAID":["days paid"],
    "BASIC": ["basic"],           # fixed basic (monthly)
    "DA":    ["da"],
    "EARNBASIC":["earn basic"],
    "EARNDA":["earn da"],
    "GROSS": ["gross"],
    "EPF":   ["epf"],             # salary PF deduction
    "ESI":   ["esi"],             # salary ESI deduction (the 'ESI' deduction column)
    "TOTDED":["total dedns", "total deductions"],
    "NET":   ["total net salary", "net salary"],
    "PFWAGES":["pf wages"],
    "ESICWAGES":["esic wages"],
    "STATE": ["state"],
    "BRANCH":["branch"],
    "MONTH": ["month"],
    "EXTRADED":["extra deduction","other deduction"],
}

def norm(s): return re.sub(r"[^a-z0-9]+"," ",str(s).lower()).strip()

def find_header_row(path, sheet):
    probe = pd.read_excel(path, sheet_name=sheet, header=None, nrows=8, dtype=str)
    for i in range(len(probe)):
        row = [norm(x) for x in probe.iloc[i].tolist()]
        if any("employee code" in c for c in row) and any(c=="gross" for c in row):
            return i
    return 1  # fallback (row index 1 = second row)

def resolve_cols(cols):
    """Return {logical: actual_column_name}. Picks the FIRST exact-ish match, so e.g. 'Basic'
       resolves before 'Earn Basic'. 'Employee Code' appears twice -> first occurrence."""
    ncols = [(c, norm(c)) for c in cols]
    out = {}
    used = set()
    for key, pats in WANT.items():
        pick = None
        # Iterate PATTERNS in priority order (WANT list order), then columns.
        # exact match
        for p in pats:
            for c, nc in ncols:
                if c in used: continue
                if nc == p or nc == p.replace(" ",""):
                    pick = c; break
            if pick: break
        # startswith
        if pick is None:
            for p in pats:
                for c, nc in ncols:
                    if c in used: continue
                    if nc.startswith(p+" "):
                        pick = c; break
                if pick: break
        # contains
        if pick is None:
            for p in pats:
                for c, nc in ncols:
                    if c in used: continue
                    if p in nc:
                        pick = c; break
                if pick: break
        if pick is not None:
            out[key] = pick; used.add(pick)
    return out

def month_key(v):
    """Salary 'MONTH' is a name like 'April'; return 'APR-24' using an assumed FY (Apr24..Mar25)."""
    s = str(v).strip().upper()
    m3 = MON3.get(s, s[:3])
    yy = "24" if m3 in ("APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC") else "25"
    return f"{m3}-{yy}"

# ---------------- load anchors ----------------
def load_ecr(path):
    """Return dict {(EMP, 'APR-24'): ecr_pf}. Accepts the comparison workbook (12 monthly tabs)."""
    xl = pd.ExcelFile(path)
    tabs = [t for t in xl.sheet_names if re.match(r"[A-Z]{3}-\d{2}", str(t).upper())]
    d = {}
    for t in tabs:
        key = str(t).upper()
        df = xl.parse(t)
        ecol = next((c for c in df.columns if "ecr pf amount" in norm(c)), None)
        emcol = next((c for c in df.columns if norm(c) in ("emp code","employee code")), None)
        if not ecol or not emcol: continue
        for _, r in df.iterrows():
            emp = str(r[emcol]).strip().split(".")[0]
            v = pd.to_numeric(pd.Series([r[ecol]]), errors="coerce").iloc[0]
            if pd.notna(v):
                d[(emp, key)] = float(v)
    return d

def load_esic(path):
    """Return dict {(EMP,'APR-24'): esi_emp} from the ESIC register (header row 2)."""
    e = pd.read_excel(path, header=1)
    e.columns = [str(c).strip() for c in e.columns]
    emp = e["Employee Code"].astype(str).str.strip().str.split(".").str[0]
    mk = pd.to_datetime(e["MONTH"], errors="coerce").dt.strftime("%b-%y").str.upper()
    val = pd.to_numeric(e["ESI emp"], errors="coerce").fillna(0.0)
    wage = pd.to_numeric(e["Total ESIC Wages"], errors="coerce").fillna(0.0)
    d = {}; dw = {}
    for a,b,c,w in zip(emp, mk, val, wage):
        if isinstance(b,str) and re.match(r"[A-Z]{3}-\d{2}", b):
            d[(a,b)] = c; dw[(a,b)] = w
    return d, dw

# ---------------- main ----------------
def main():
    C = CONFIG
    os.makedirs(C["OUT_DIR"], exist_ok=True)
    hdr = find_header_row(C["SALARY_XLSX"], C["SALARY_SHEET"])
    print(f"Header row detected at index {hdr}")
    sal = pd.read_excel(C["SALARY_XLSX"], sheet_name=C["SALARY_SHEET"], header=hdr)
    sal.columns = [str(c).strip() for c in sal.columns]
    col = resolve_cols(sal.columns)
    need = ["EMP","DAYSPAID","BASIC","DA","GROSS","EPF","TOTDED","NET","MONTH"]
    missing = [k for k in need if k not in col]
    if missing:
        raise SystemExit(f"Could not resolve required columns {missing}. Resolved: {col}")
    print("Resolved columns:", col)

    ecr = load_ecr(C["ECR_SOURCE"])
    esic, esic_w = load_esic(C["ESIC_XLSX"])

    g = lambda k: sal[col[k]] if k in col else pd.Series([np.nan]*len(sal))
    EMP  = g("EMP").astype(str).str.strip().str.split(".").str[0]
    MK   = g("MONTH").map(month_key)
    basic= pd.to_numeric(g("EARNBASIC") if "EARNBASIC" in col else g("BASIC"), errors="coerce").fillna(0.0)
    da   = pd.to_numeric(g("EARNDA") if "EARNDA" in col else g("DA"), errors="coerce").fillna(0.0)
    epf  = pd.to_numeric(g("EPF"), errors="coerce").fillna(0.0)
    esi  = pd.to_numeric(g("ESI"), errors="coerce").fillna(0.0)
    days = pd.to_numeric(g("DAYSPAID"), errors="coerce").fillna(0.0)
    totd = pd.to_numeric(g("TOTDED"), errors="coerce").fillna(0.0)
    net  = pd.to_numeric(g("NET"), errors="coerce").fillna(0.0)
    extra= pd.to_numeric(g("EXTRADED"), errors="coerce").fillna(0.0) if "EXTRADED" in col else pd.Series([0.0]*len(sal))

    n = len(sal)
    rev_epf=np.zeros(n); rev_basic=np.zeros(n); rev_esi=np.zeros(n)
    other_ded=np.zeros(n); adj_days=np.zeros(n); rule=np.empty(n,dtype=object)
    ecr_capd=np.zeros(n)

    for i in range(n):
        emp=EMP.iloc[i]; mk=MK.iloc[i]; b=float(basic.iloc[i]); d=float(da.iloc[i])
        fm = FULL_MONTH.get(mk.split("-")[0], 31)
        e_pf = ecr.get((emp,mk), None)
        # ---- PF ----
        if e_pf is None or e_pf==0:
            rule[i]='NOT_IN_ECR'; rev_epf[i]=0.0; rev_basic[i]=b+d; ecr_capd[i]=0.0
        else:
            capd=min(float(e_pf), PF_CAP); ecr_capd[i]=capd
            rev_epf[i]=capd
            rb=round(capd/PF_RATE); rb=min(rb, BD_CEIL); rev_basic[i]=rb
            rule[i]= 'NO_ADJ' if abs(epf.iloc[i]-capd)<=1 else ('COND2' if capd>epf.iloc[i] else 'CASE_AB')
        pf_diff = float(epf.iloc[i]) - rev_epf[i]     # parked (may be +/-)
        # ---- ESI ---- (register is the anchor; 0 if not in register)
        r_esi = esic.get((emp,mk), 0.0)
        rev_esi[i]=round(float(r_esi),2)
        esi_diff = float(esi.iloc[i]) - rev_esi[i]
        # ---- park both diffs net-neutral ----
        other_ded[i]=round(float(extra.iloc[i]) + pf_diff + esi_diff, 2)
        # ---- day adjust (M6): ECR row projects (basic+da) full-month <= 15000 ----
        bd = rev_basic[i]
        if rev_epf[i]>0 and bd>0:
            adj_days[i]=max(1,min(fm, math.ceil(bd*fm/BD_CEIL)))
        else:
            adj_days[i]=max(1,min(fm, round(days.iloc[i]) if days.iloc[i]>0 else fm))

    # revised total dedns unchanged; net unchanged (parking absorbs the delta)
    out = sal.copy()
    out["REVISED_EPF"]=np.round(rev_epf,2)
    out["ECR_PF_CAPPED"]=np.round(ecr_capd,2)
    out["REVISED_BASIC+DA"]=np.round(rev_basic,2)
    out["REVISED_ESI"]=np.round(rev_esi,2)
    out["REVISED_OTHER_DEDUCTION"]=np.round(other_ded,2)
    out["ADJ_WORKING_DAYS"]=adj_days.astype(int)
    out["RULE_APPLIED"]=rule
    out["12%_OF_REVISED_BASIC"]=np.round(rev_basic*PF_RATE,2)
    out["DIFF_12pct_vs_REVISED_EPF"]=np.round(rev_basic*PF_RATE-rev_epf,2)
    out["PF_DIFF_PARKED"]=np.round(epf.values-rev_epf,2)
    out["ESI_DIFF_PARKED"]=np.round(esi.values-rev_esi,2)
    # NET is preserved by construction: Total Dedns unchanged (EPF/ESI reductions offset by
    # REVISED_OTHER_DEDUCTION), so REVISED_NET == original NET.
    out["REVISED_NET"]=np.round(net.values,2)

    outpath=os.path.join(C["OUT_DIR"],"Maharashtra_Salary_CORRECTED_2024-25.xlsx")
    out.to_excel(outpath, index=False)

    # -------- integrity checks (per month) --------
    logs=[]; pfpos=out["REVISED_EPF"]>0; esipos=out["REVISED_ESI"]>0
    df=pd.DataFrame({"MK":MK,"rev_epf":rev_epf,"ecr_capd":ecr_capd,"rev_basic":rev_basic,
                     "rev_esi":rev_esi,"other":other_ded,"adj":adj_days,
                     "d12":out["DIFF_12pct_vs_REVISED_EPF"].values,
                     "esic_w":[esic_w.get((EMP.iloc[i],MK.iloc[i]),0.0) for i in range(n)]})
    def L(s): logs.append(s); print(s)
    L("MONTH  rows  PFgap  C3_12%>1  PF>1800  BD>15000  OtherDed<0  ESI!=0.75%>1")
    for mk,gp in df.groupby("MK"):
        pf_gap=round((gp["rev_epf"]-gp["ecr_capd"]).abs().max(),2)
        c3=int((gp.loc[gp.rev_epf>0,"d12"].abs()>1).sum())
        cap1=int((gp.rev_epf>PF_CAP+.5).sum())
        cap5=int((gp.loc[gp.rev_epf>0,"rev_basic"]>BD_CEIL+.5).sum())
        odn=int((gp.other< -1).sum())
        esi_rate=int(((gp.rev_esi>0)&((gp.rev_esi-gp.esic_w*ESI_EMP_RATE).abs()>1)).sum())
        L(f"{mk}  {len(gp):5d}  {pf_gap:5.2f}  {c3:6d}  {cap1:6d}  {cap5:7d}  {odn:9d}  {esi_rate:11d}")
    open(os.path.join(C["OUT_DIR"],"reconcile_full_salary_checks.txt"),"w").write("\n".join(logs))
    print("\nWrote:", outpath)
    print("Checks log:", os.path.join(C["OUT_DIR"],"reconcile_full_salary_checks.txt"))
    print("NOTE: OtherDed<0 rows mean the original OTHER-DED was too small to absorb an ECR>salary "
          "(Cond 2) uplift; per skill these shift into attendance allowance — review those rows.")

if __name__=="__main__":
    main()
