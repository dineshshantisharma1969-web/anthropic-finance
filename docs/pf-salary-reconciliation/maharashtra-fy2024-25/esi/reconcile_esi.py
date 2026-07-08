#!/usr/bin/env python3
"""
Maharashtra AISSS FY2024-25 ESI reconciliation.
Reconciles the filed ESIC register (Maharashtra ESIC Working 24-25, the deposited
"Future" anchor) against the salary population (from the PF comparison workbook),
and validates it against ESI statutory rules per the pf-salary-reconciliation skill.

Rates FY2024-25: employee ESI = 0.75% of ESIC wages, employer = 3.25%, eligibility ceiling = Rs.21,000.

Outputs per month: validated ESIC register (filed) + ESI coverage-gap list; plus a year
summary, checks, and a combined workbook.
"""
import os, numpy as np, pandas as pd

SP  = os.environ.get("MH_DIR", os.path.dirname(os.path.abspath(__file__)))
ESI = os.path.join(SP, "esic_working.xlsx")
CMP = os.path.join(SP, "cmp.xlsx")
OUT = os.path.join(SP, "esi_out"); os.makedirs(OUT, exist_ok=True)

EMP_RATE=0.0075; CO_RATE=0.0325; ESI_CEIL=21000.0
ORDER=['APR-24','MAY-24','JUN-24','JUL-24','AUG-24','SEP-24','OCT-24','NOV-24','DEC-24','JAN-25','FEB-25','MAR-25']

def load_register():
    e=pd.read_excel(ESI, header=1)
    e.columns=[str(c).strip() for c in e.columns]
    e['MONTH']=pd.to_datetime(e['MONTH'],errors='coerce')
    e['MKEY']=e['MONTH'].dt.strftime('%b-%y').str.upper()
    e['EMP']=e['Employee Code'].astype(str).str.strip().str.split('.').str[0]
    for c in ['Total Days','Present Days','Total ESIC Wages','ESI emp','ESI CO','Total']:
        e[c]=pd.to_numeric(e[c],errors='coerce').fillna(0)
    e['STATUS']=e.iloc[:,19]
    return e

def load_salary_month(m):
    c=pd.read_excel(CMP, sheet_name=m)
    c['EMP']=c['EMP CODE'].astype(str).str.strip().str.split('.').str[0]
    c['GROSSn']=pd.to_numeric(c['GROSS'],errors='coerce').fillna(0)
    c['BASICn']=pd.to_numeric(c['BASIC'],errors='coerce').fillna(0)
    return c

def main():
    esi=load_register()
    summary=[]; checks=[]; combined={}; gaps_all=[]
    for m in ORDER:
        r=esi[esi['MKEY']==m].copy()
        sal=load_salary_month(m)
        salset=set(sal['EMP'])
        # ---- validated register (filed ESI position) with statutory audit ----
        wage=r['Total ESIC Wages']; emp=r['ESI emp']; co=r['ESI CO']
        r['ESI_EMP_0.75%_EXPECTED']=(wage*EMP_RATE).round(2)
        r['ESI_EMP_DIFF']=(emp-wage*EMP_RATE).round(2)
        r['ESI_CO_3.25%_EXPECTED']=(wage*CO_RATE).round(2)
        r['ESI_CO_DIFF']=(co-wage*CO_RATE).round(2)
        r['ABOVE_21000_CEILING']=np.where(wage>ESI_CEIL,'Y','')
        r['IN_SALARY_SHEET']=np.where(r['EMP'].isin(salset),'Y','N')
        out=r[['MKEY','Site Name','Div Code','Employee Code','Employee Name','Designation',
               'STATE','BRANCH','ESI No.','Total Days','Present Days','Total ESIC Wages',
               'ESI emp','ESI CO','Total','ESI_EMP_0.75%_EXPECTED','ESI_EMP_DIFF',
               'ESI_CO_3.25%_EXPECTED','ESI_CO_DIFF','ABOVE_21000_CEILING','IN_SALARY_SHEET','STATUS']].copy()
        out.columns=['MONTH','SITE','DIV_CODE','EMP CODE','NAME','DESIGNATION','STATE','BRANCH','ESI NO',
                     'TOTAL_DAYS','PRESENT_DAYS','ESIC_WAGES','ESI_EMP(0.75%)','ESI_CO(3.25%)','ESI_TOTAL',
                     'ESI_EMP_EXPECTED','ESI_EMP_DIFF','ESI_CO_EXPECTED','ESI_CO_DIFF',
                     'ABOVE_21000','IN_SALARY','STATUS']
        out.to_csv(f"{OUT}/ESI_FILED_{m}.csv",index=False)
        combined[m]=out
        # ---- ESI coverage gaps: salary emps GROSS<=21000 not in ESIC register ----
        reg_emps=set(r['EMP'])
        gap=sal[(~sal['EMP'].isin(reg_emps)) & (sal['GROSSn']<=ESI_CEIL) & (sal['GROSSn']>0)].copy()
        g=gap[['EMP','NAME OF EMPLOYEE','BRANCH','SITE NAME','M/DAYS','W/DAYS','BASICn','GROSSn']].copy()
        g.insert(0,'MONTH',m)
        g.columns=['MONTH','EMP CODE','NAME','BRANCH','SITE NAME','M/DAYS','W/DAYS','BASIC','GROSS']
        g['IMPLIED_ESI_0.75%_OF_GROSS']=(g['GROSS']*EMP_RATE).round(2)
        g.to_csv(f"{OUT}/ESI_COVERAGE_GAP_{m}.csv",index=False)
        gaps_all.append(g)
        # ---- month summary ----
        summary.append({
            'MONTH':m,'REGISTER_EMPLOYEES':len(r),
            'ESIC_WAGES':round(float(wage.sum()),2),
            'ESI_EMP_FILED(0.75%)':round(float(emp.sum()),2),
            'ESI_CO_FILED(3.25%)':round(float(co.sum()),2),
            'ESI_TOTAL_FILED':round(float(r['Total'].sum()),2),
            'ABOVE_21000_ROWS':int((wage>ESI_CEIL).sum()),
            'ESI_COVERAGE_GAPS(<=21k not filed)':len(g),
            'IN_ESIC_NOT_IN_SALARY':int((~r['EMP'].isin(salset)).sum()),
        })
        # ---- checks (per month) ----
        checks.append({
            'MONTH':m,
            'EMP_rate!=0.75%(>Rs1)':int((r['ESI_EMP_DIFF'].abs()>1).sum()),
            'CO_rate!=3.25%(>Rs1)':int((r['ESI_CO_DIFF'].abs()>1).sum()),
            'ABOVE_21000_ceiling':int((wage>ESI_CEIL).sum()),
            'non_MAHARASHTRA_rows':int((r['STATE'].astype(str).str.upper()!='MAHARASHTRA').sum()),
            'zero_wage_with_ESI':int(((wage<=0)&(emp>0)).sum()),
            'coverage_gaps':len(g),
        })
        print(f"{m}: reg={len(r):4d} wages={wage.sum():14,.0f} ESIemp={emp.sum():11,.0f} "
              f"ESIco={co.sum():11,.0f} >21k={int((wage>ESI_CEIL).sum()):3d} gaps={len(g):3d} "
              f"rate_viol={int((r['ESI_EMP_DIFF'].abs()>1).sum())}")

    summ=pd.DataFrame(summary)
    tot={'MONTH':'TOTAL'}
    for c in summ.columns:
        if c!='MONTH': tot[c]=round(float(summ[c].sum()),2)
    summ=pd.concat([summ,pd.DataFrame([tot])],ignore_index=True)
    summ.to_csv(f"{OUT}/ESI_SUMMARY_FY2024-25.csv",index=False)
    chk=pd.DataFrame(checks); chk.to_csv(f"{OUT}/ESI_CHECKS_FY2024-25.csv",index=False)
    gaps=pd.concat(gaps_all,ignore_index=True); gaps.to_csv(f"{OUT}/ESI_COVERAGE_GAPS_YEAR.csv",index=False)

    with pd.ExcelWriter(f"{OUT}/Maharashtra_ESI_Reconciliation_FY2024-25.xlsx",engine='openpyxl') as xw:
        summ.to_excel(xw,sheet_name='SUMMARY',index=False)
        chk.to_excel(xw,sheet_name='CHECKS',index=False)
        gaps.to_excel(xw,sheet_name='COVERAGE_GAPS',index=False)
        for m in ORDER: combined[m].to_excel(xw,sheet_name=m,index=False)

    print("\n===== ESI YEAR TOTALS =====")
    print(summ.tail(1).to_string(index=False))
    print("\n===== CHECKS =====")
    print(chk.to_string(index=False))
    print(f"\nYear coverage gaps: {len(gaps)} employee-months (salary gross<=21k, not in ESIC register)")

if __name__=='__main__':
    main()
