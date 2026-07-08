#!/usr/bin/env python3
"""
Maharashtra AISSS FY2024-25 PF reconciliation.
Applies the pf-salary-reconciliation skill (Golden Rules + 4 PF rules +
12% audit + statutory caps M2/CAP + M6 ceiling / day-adjustment checks)
to the purpose-built per-employee monthly salary-vs-ECR comparison workbook.

Input : cmp.xlsx  (SUMMARY + 12 monthly tabs; one row per employee/month)
Output: per-month corrected CSVs, a combined xlsx, a summary CSV and rule-stats CSV.
"""
import math, os
import numpy as np
import pandas as pd

# Directory containing cmp.xlsx (the Salary_vs_ECR_PF_EE comparison workbook, SUMMARY + 12 monthly tabs).
# Override with env MH_DIR; defaults to this script's directory.
SP  = os.environ.get("MH_DIR", os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SP, "out")
os.makedirs(OUT, exist_ok=True)

# calendar full-month days per fiscal month tab
FULL_MONTH = {
    'APR-24':30,'MAY-24':31,'JUN-24':30,'JUL-24':31,'AUG-24':31,'SEP-24':30,
    'OCT-24':31,'NOV-24':30,'DEC-24':31,'JAN-25':31,'FEB-25':28,'MAR-25':31,
}
PF_RATE = 0.12
PF_CAP  = 1800.0     # CAP1: employee PF capped at 12% of 15,000
BD_CEIL = 15000.0    # PF wage ceiling

def isnum(x):
    try:
        float(x); return True
    except Exception:
        return False

def reconcile_month(df, month):
    fm = FULL_MONTH[month]
    df = df.copy()
    df['EMP CODE'] = df['EMP CODE'].astype(str).str.strip().str.split('.').str[0]
    orig_pf = pd.to_numeric(df['PF AS PER SALARY (EE)'], errors='coerce').fillna(0.0)
    ecr_raw = df['ECR PF AMOUNT (EE)']
    in_ecr  = ecr_raw.apply(isnum)
    ecr_pf  = pd.to_numeric(ecr_raw.where(in_ecr), errors='coerce').fillna(0.0)
    basic   = pd.to_numeric(df['BASIC'], errors='coerce').fillna(0.0)   # BASIC+DA wage base (salary PF = 12% x BASIC)
    gross   = pd.to_numeric(df['GROSS'], errors='coerce').fillna(0.0)
    ndays   = pd.to_numeric(df['W/DAYS'], errors='coerce').fillna(0.0)  # NORMALDAYS (actual worked)
    mdiv    = pd.to_numeric(df['M/DAYS'], errors='coerce').fillna(fm)   # site divisor

    n = len(df)
    rule      = np.empty(n, dtype=object)
    rev_pf    = np.zeros(n); rev_basic = np.zeros(n)
    adj_days  = np.zeros(n); parked    = np.zeros(n)
    remark    = np.empty(n, dtype=object)
    ecr_capped= np.zeros(n); surplus   = np.zeros(n)   # min(ecr,1800) anchor & above-cap surplus

    # ---- Multi-site (M1): primary PF row = max NORMALDAYS; secondaries zeroed ----
    is_secondary = np.zeros(n, dtype=bool)
    grp = df.groupby('EMP CODE').indices
    for emp, idxs in grp.items():
        if len(idxs) > 1:
            # primary = row with max worked days (ties -> first)
            sub = ndays.iloc[list(idxs)]
            primary_pos = sub.idxmax()
            for i in idxs:
                if i != primary_pos and ecr_pf.iloc[i] == ecr_pf.iloc[primary_pos]:
                    is_secondary[i] = True  # duplicate ECR carried on secondary -> zero it

    for i in range(n):
        opf = float(orig_pf.iloc[i]); epf = float(ecr_pf.iloc[i])
        b   = float(basic.iloc[i]);   nd = float(ndays.iloc[i]); md = float(mdiv.iloc[i])
        matched = bool(in_ecr.iloc[i])

        if is_secondary[i]:
            rule[i] = 'MULTI_SITE_SECONDARY_PF'
            rev_pf[i] = 0.0; rev_basic[i] = b; parked[i] = opf
            adj_days[i] = nd; remark[i] = 'secondary row - PF parked'
            ecr_capped[i] = 0.0; surplus[i] = 0.0   # ECR belongs to primary row
            continue

        if not matched:
            # Rule 3 - Not in ECR: zero PF, park original PF, ensure full-month projection > ceiling (P2)
            rule[i] = 'NOT_IN_ECR'
            rev_pf[i] = 0.0; rev_basic[i] = b; parked[i] = opf
            # reduce ADJ days so (basic) x FULL_MONTH / days > 15000 (self-consistency for PF absence)
            if b > 0:
                proj = b * fm / nd if nd > 0 else 0
                if proj <= BD_CEIL:
                    nd_new = math.floor(b * fm / (BD_CEIL + 1))
                    adj_days[i] = max(1, min(fm, nd_new)) if nd_new >= 1 else max(1, nd)
                else:
                    adj_days[i] = max(1, min(fm, round(nd)))
            else:
                adj_days[i] = max(1, min(fm, round(nd)))
            remark[i] = 'ok - not in ECR (PF=0)'
            continue

        # Matched employee
        diff = opf - epf
        if abs(diff) <= 1.0:
            rule[i] = 'NO_ADJUSTMENT'
            rev_pf[i] = epf
            remark[i] = 'match as per ecr'
        elif diff > 1.0:
            # ECR < salary PF
            if b >= BD_CEIL - 0.5:           # at/above ceiling -> Case A (basic stays capped)
                rule[i] = 'CASE_A'; remark[i] = 'Pf capped / >15000'
            else:                             # below ceiling -> Case B (reduce basic)
                rule[i] = 'CASE_B'; remark[i] = 'to be check (basic reduced)'
            rev_pf[i] = epf
        else:
            # ECR > salary PF -> Cond 2 (Rule 4)
            rule[i] = 'COND2'; remark[i] = 'match as per ecr (OD reduced)'
            rev_pf[i] = epf

        # statutory cap: PF anchor = min(ECR, 1800); surplus above 1800 cannot be filed as EE PF
        surplus[i]    = max(0.0, epf - PF_CAP)
        ecr_capped[i] = min(epf, PF_CAP)
        # cap PF at 1800 (M2 CAP1)
        if rev_pf[i] > PF_CAP:
            rev_pf[i] = PF_CAP
        # 12% rule -> revised basic = pf / 0.12, capped at 15000 (CAP5)
        rb = round(rev_pf[i] / PF_RATE)
        if rb > BD_CEIL: rb = BD_CEIL
        rev_basic[i] = rb
        parked[i]    = opf - rev_pf[i]        # PF difference parked in OTHER DEDUCTION (net unchanged)

        # M6 / day adjustment so ECR_PF>0 row projects <= 15000 full-month
        if rev_pf[i] > 0 and rb > 0:
            target_days = math.ceil(rb * fm / BD_CEIL)
            adj_days[i] = max(1, min(fm, target_days))
        else:
            adj_days[i] = max(1, min(fm, round(nd)))

    out = pd.DataFrame({
        'EMP CODE': df['EMP CODE'].values,
        'NAME': df['NAME OF EMPLOYEE'].values,
        'DESIGNATION': df['DESIGNATION'].values,
        'EPF NO': df['EPF NO'].values,
        'UAN NO': df['UAN NO'].values,
        'SITE NAME': df['SITE NAME'].values,
        'BRANCH': df['BRANCH'].values,
        'M/DAYS (divisor)': mdiv.values,
        'NORMALDAYS (W/DAYS)': ndays.values,
        'NCP': pd.to_numeric(df['NCP'], errors='coerce').fillna(0).values,
        'ORIG_BASIC(+DA)': basic.round(2).values,
        'GROSS': gross.values,
        'ORIG_PF (salary EE)': orig_pf.round(2).values,
        'ECR_PF (EE, filed)': np.where(in_ecr.values, ecr_pf.round(2).values, np.nan),
        'ECR_PF_CAPPED (min 1800)': np.round(ecr_capped,2),
        'ABOVE_1800_SURPLUS': np.round(surplus,2),
        'PF SOURCE': df['PF SOURCE'].values,
        'RULE_APPLIED': rule,
        'REVISED_PF': np.round(rev_pf,2),
        'REVISED_BASIC(+DA)': np.round(rev_basic,2),
        'ADJ_WORKING_DAYS': adj_days.astype(int),
        'PF_DIFF_PARKED_IN_OTHER_DED': np.round(parked,2),
        '12% OF REVISED_BASIC': np.round(rev_basic*PF_RATE,2),
        'DIFF (12% vs REVISED_PF)': np.round(rev_basic*PF_RATE - rev_pf,2),
        'BD_MONTHLY_PROJECTION': np.where(adj_days>0, np.round(rev_basic*fm/np.where(adj_days>0,adj_days,1),0), 0),
        'REMARK': remark,
    })
    return out, in_ecr, ecr_pf, orig_pf

def run_checks(out, in_ecr, ecr_pf, orig_pf, month):
    fm = FULL_MONTH[month]
    pfpos = out['REVISED_PF'] > 0
    checks = {}
    # Golden Rule 1: sum revised PF == sum ECR_PF_CAPPED (statutory anchor); per-employee gap 0
    sum_rev  = out['REVISED_PF'].sum()
    sum_capd = out['ECR_PF_CAPPED (min 1800)'].sum()
    checks['GR1_gap (Σrevised-Σecr_capped)'] = round(sum_rev - sum_capd, 2)
    checks['GR1_max_per_row_gap'] = round(float((out['REVISED_PF'] - out['ECR_PF_CAPPED (min 1800)']).abs().max()), 2)
    # C3: 12% relation on PF>0
    checks['C3_12pct_violations'] = int((out.loc[pfpos,'DIFF (12% vs REVISED_PF)'].abs() > 1.0).sum())
    # CAP1: PF <= 1800 ; CAP5: basic <= 15000 on PF>0
    checks['CAP1_PF>1800'] = int((out['REVISED_PF'] > PF_CAP + 0.5).sum())
    checks['CAP5_BASIC>15000'] = int((out.loc[pfpos,'REVISED_BASIC(+DA)'] > BD_CEIL + 0.5).sum())
    # C10 / M6: rows carrying revised PF must project BD <= 15000.5
    proj = out['BD_MONTHLY_PROJECTION']
    checks['C10_PFrow_proj>15000'] = int((pfpos & (proj > 15000.5)).sum())
    # P2: not-in-ECR rows should project strictly ABOVE ceiling (boundary 15000 = at-ceiling exception, not a fail)
    notin = out['RULE_APPLIED']=='NOT_IN_ECR'
    checks['P2_notInECR_proj<15000'] = int((notin & (out['ORIG_BASIC(+DA)']>0) & (proj < 14999.5)).sum())
    checks['P2_atCeiling_15000_exceptions'] = int((notin & (proj.round(0)==15000)).sum())
    # ADJ days in [1, FULL_MONTH]
    checks['C9_days_out_of_range'] = int(((out['ADJ_WORKING_DAYS']<1)|(out['ADJ_WORKING_DAYS']>fm)).sum())
    return checks, sum_rev, sum_capd, orig_pf.sum()

def main():
    xl = pd.ExcelFile(f"{SP}/cmp.xlsx")
    months = [s for s in xl.sheet_names if s != 'SUMMARY']
    summary_rows = []
    rule_rows = []
    check_rows = []
    combined = {}
    for m in months:
        df = xl.parse(m)
        out, in_ecr, ecr_pf, orig_pf = reconcile_month(df, m)
        checks, sum_rev, sum_capd, sum_orig = run_checks(out, in_ecr, ecr_pf, orig_pf, m)
        out.to_csv(f"{OUT}/CORRECTED_{m}.csv", index=False)
        combined[m] = out
        rc = out['RULE_APPLIED'].value_counts().to_dict()
        summary_rows.append({
            'MONTH': m, 'ROWS': len(out),
            'ORIG_SALARY_PF': round(sum_orig,2),
            'ECR_PF_FILED': round(float(ecr_pf[in_ecr].sum()),2),
            'ECR_PF_CAPPED (anchor)': round(sum_capd,2),
            'REVISED_PF': round(sum_rev,2),
            'PF_GAP (rev-capped)': checks['GR1_gap (Σrevised-Σecr_capped)'],
            'ABOVE_1800_SURPLUS': round(float(out['ABOVE_1800_SURPLUS'].sum()),2),
            'PF_PARKED_IN_OTHER_DED': round(float(out['PF_DIFF_PARKED_IN_OTHER_DED'].sum()),2),
        })
        rr = {'MONTH': m}; rr.update(rc); rule_rows.append(rr)
        cr = {'MONTH': m}; cr.update(checks); check_rows.append(cr)
        print(f"{m}: rows={len(out)} orig={sum_orig:12,.0f} filed={ecr_pf[in_ecr].sum():12,.0f} "
              f"capped={sum_capd:12,.0f} rev={sum_rev:12,.0f} surplus>1800={out['ABOVE_1800_SURPLUS'].sum():10,.0f} | "
              + " ".join(f"{k}={v}" for k,v in checks.items()))

    summ = pd.DataFrame(summary_rows)
    tot = {'MONTH':'TOTAL'}
    for c in summ.columns:
        if c!='MONTH': tot[c]=round(float(summ[c].sum()),2)
    summ = pd.concat([summ, pd.DataFrame([tot])], ignore_index=True)
    summ.to_csv(f"{OUT}/SUMMARY_FY2024-25.csv", index=False)
    pd.DataFrame(rule_rows).fillna(0).to_csv(f"{OUT}/RULE_STATS_FY2024-25.csv", index=False)
    checks_df = pd.DataFrame(check_rows)
    checks_df.to_csv(f"{OUT}/CHECKS_FY2024-25.csv", index=False)

    # combined workbook
    with pd.ExcelWriter(f"{OUT}/Maharashtra_PF_Corrected_Monthly_FY2024-25.xlsx", engine='openpyxl') as xw:
        summ.to_excel(xw, sheet_name='SUMMARY', index=False)
        checks_df.to_excel(xw, sheet_name='CHECKS', index=False)
        pd.DataFrame(rule_rows).fillna(0).to_excel(xw, sheet_name='RULE_STATS', index=False)
        for m in months:
            combined[m].to_excel(xw, sheet_name=m, index=False)

    print("\n===== FY2024-25 TOTALS =====")
    print(summ.tail(1).to_string(index=False))
    print("\n===== CHECKS (all should be 0 except gap≈0) =====")
    print(checks_df.to_string(index=False))

if __name__ == '__main__':
    main()
