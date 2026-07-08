#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
match_summary_to_salary.py — verify the published Maharashtra FY2024-25 SUMMARY ties to
your ACTUAL salary sheet, month by month.

Needs ONLY the salary sheet (no ECR/ESIC files). It reads the real workbook, totals PF/ESI/
gross/net per month, and compares the PF total against the reconciliation summary (values are
embedded below). Prints a MATCH / DIFF line per month and writes an Excel match report.

RUN LOCALLY (the salary workbook is >10 MB, so it can't be processed in the assistant).

  pip install pandas openpyxl
  python match_summary_to_salary.py --salary "D:\\path\\to\\Salary comb 2024-25.xlsx"

Output: SALARY_VS_SUMMARY_MATCH.xlsx  (+ a printed table).
"""
import argparse, re, sys
import numpy as np
import pandas as pd

# ---- expected month-wise figures from the published reconciliation summary ----
EXPECTED = {
 "APR-24": {"orig_pf":2584327.64,"revised_pf":2379009.52,"esi_filed":165735.0,"esic_wages":22006016.55},
 "MAY-24": {"orig_pf":2534768.88,"revised_pf":2350265.60,"esi_filed":162122.0,"esic_wages":21516404.79},
 "JUN-24": {"orig_pf":2667491.76,"revised_pf":2477027.92,"esi_filed":170679.0,"esic_wages":22659225.64},
 "JUL-24": {"orig_pf":2710675.40,"revised_pf":2522985.64,"esi_filed":172602.0,"esic_wages":22917978.97},
 "AUG-24": {"orig_pf":2802253.32,"revised_pf":2597426.00,"esi_filed":175874.0,"esic_wages":23349486.88},
 "SEP-24": {"orig_pf":2756165.72,"revised_pf":2545659.32,"esi_filed":169262.0,"esic_wages":22468543.85},
 "OCT-24": {"orig_pf":2812260.20,"revised_pf":2614187.20,"esi_filed":176139.0,"esic_wages":23389549.78},
 "NOV-24": {"orig_pf":2630461.08,"revised_pf":2442236.48,"esi_filed":164085.0,"esic_wages":21771617.69},
 "DEC-24": {"orig_pf":2691269.32,"revised_pf":2516762.84,"esi_filed":166360.0,"esic_wages":22090349.20},
 "JAN-25": {"orig_pf":2753833.52,"revised_pf":2576860.56,"esi_filed":169052.0,"esic_wages":22436923.53},
 "FEB-25": {"orig_pf":2798222.44,"revised_pf":2613353.40,"esi_filed":172634.0,"esic_wages":22912287.68},
 "MAR-25": {"orig_pf":2780937.84,"revised_pf":2593909.52,"esi_filed":169840.0,"esic_wages":22550960.00},
}
ORDER=list(EXPECTED.keys())
MON3={'JANUARY':'JAN','FEBRUARY':'FEB','MARCH':'MAR','APRIL':'APR','MAY':'MAY','JUNE':'JUN',
      'JULY':'JUL','AUGUST':'AUG','SEPTEMBER':'SEP','OCTOBER':'OCT','NOVEMBER':'NOV','DECEMBER':'DEC'}

def norm(s): return re.sub(r"[^a-z0-9]+"," ",str(s).lower()).strip()

def find_header_row(path, sheet):
    probe = pd.read_excel(path, sheet_name=sheet, header=None, nrows=8, dtype=str)
    for i in range(len(probe)):
        row=[norm(x) for x in probe.iloc[i].tolist()]
        if any("employee code" in c or c=="empcode" for c in row) and any("gross" in c for c in row):
            return i
    return 1

def pick(cols, *pats):
    nc=[(c,norm(c)) for c in cols]
    for p in pats:
        for c,n in nc:
            if n==p: return c
    for p in pats:
        for c,n in nc:
            if n.startswith(p+" "): return c
    for p in pats:
        for c,n in nc:
            if p in n: return c
    return None

def mkey(v):
    s=str(v).strip().upper(); m=MON3.get(s,s[:3])
    yy="24" if m in ("APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC") else "25"
    return f"{m}-{yy}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--salary", required=True, help="path to the full salary workbook")
    ap.add_argument("--sheet", default=0)
    ap.add_argument("--out", default="SALARY_VS_SUMMARY_MATCH.xlsx")
    ap.add_argument("--tol", type=float, default=1.0, help="rupee tolerance for MATCH")
    a=ap.parse_args()

    hdr=find_header_row(a.salary, a.sheet)
    df=pd.read_excel(a.salary, sheet_name=a.sheet, header=hdr)
    df.columns=[str(c).strip() for c in df.columns]

    c_month=pick(df.columns,"month")
    c_epf  =pick(df.columns,"epf","pf")
    c_esi  =pick(df.columns,"esi","esic")
    c_gross=pick(df.columns,"gross amt","gross")
    c_net  =pick(df.columns,"total net salary","netpayable","net salary","net")
    c_state=pick(df.columns,"state","sitestate")
    if not c_month or not c_epf:
        sys.exit(f"Could not find MONTH / EPF columns. Found month={c_month} epf={c_epf}. "
                 f"Columns: {list(df.columns)[:40]}")
    print(f"Header row {hdr}. Using  month='{c_month}' pf='{c_epf}' esi='{c_esi}' "
          f"gross='{c_gross}' net='{c_net}' state='{c_state}'")

    # Maharashtra only (defensive; the file is already MH)
    if c_state:
        df=df[df[c_state].astype(str).str.upper().str.contains("MAHARASH", na=False)]
    df["_MK"]=df[c_month].map(mkey)
    num=lambda c: pd.to_numeric(df[c],errors="coerce").fillna(0) if c else pd.Series([0]*len(df))
    df["_pf"]=num(c_epf); df["_esi"]=num(c_esi); df["_gross"]=num(c_gross); df["_net"]=num(c_net)

    rows=[]
    print("\nMONTH    rows  salary_PF      summary_orig_PF   diff       PF match")
    for m in ORDER:
        g=df[df["_MK"]==m]
        sal_pf=round(float(g["_pf"].sum()),2)
        exp=EXPECTED[m]
        diff=round(sal_pf-exp["orig_pf"],2)
        ok="MATCH" if abs(diff)<=a.tol else f"DIFF {diff:+,.2f}"
        rows.append({"MONTH":m,"salary_rows":len(g),
                     "salary_PF":sal_pf,"summary_orig_PF":exp["orig_pf"],"PF_diff":diff,
                     "salary_ESI":round(float(g["_esi"].sum()),2),
                     "summary_revised_PF":exp["revised_pf"],
                     "summary_ESI_filed":exp["esi_filed"],
                     "salary_gross":round(float(g["_gross"].sum()),2),
                     "salary_net":round(float(g["_net"].sum()),2),
                     "PF_MATCH":ok})
        print(f"{m}  {len(g):5d}  {sal_pf:14,.2f}  {exp['orig_pf']:15,.2f}  {diff:+10,.2f}  {ok}")
    out=pd.DataFrame(rows)
    tot={"MONTH":"TOTAL","salary_rows":out["salary_rows"].sum()}
    for c in ["salary_PF","summary_orig_PF","PF_diff","salary_ESI","summary_revised_PF",
              "summary_ESI_filed","salary_gross","salary_net"]:
        tot[c]=round(float(out[c].sum()),2)
    tot["PF_MATCH"]="MATCH" if abs(tot["PF_diff"])<=a.tol else f"DIFF {tot['PF_diff']:+,.2f}"
    out=pd.concat([out,pd.DataFrame([tot])],ignore_index=True)
    out.to_excel(a.out,index=False)
    print(f"\nTOTAL salary PF {tot['salary_PF']:,.2f} vs summary {tot['summary_orig_PF']:,.2f}  "
          f"-> {tot['PF_MATCH']}")
    print("Wrote:", a.out)
    print("\nIf any month shows DIFF, tell me the month + the two numbers and I'll trace it "
          "(usually a state-filter or a row-scope difference between the salary sheet and the "
          "reconciliation basis).")

if __name__=="__main__":
    main()
