#!/usr/bin/env python3
"""May-2025 M13 FINAL — full checks & balances per the pf-salary-reconciliation skill.

Runs the complete validation suite from PF_SALARY_RECONCILIATION_SKILL_v4.md
(incl. the v4.1 Rule-M6/C10 addendum, the C9-C13 day-adjustment set, the C-MW
minimum-wage floor, the v3 projection addendum) plus the M17+M18a-e row-level
worklist checks (fy2526_worklist.py logic) against May_M13_FINAL.xlsx
(sheet "Salary (Corrected)", 19,327 employee rows + 5 footer rows).

Usage: python3 may25_checks.py <May_M13_FINAL.xlsx> [out_dir]
The source file is 21 MB (over the Drive-connector 10 MB cap) — fetch it in
ranged slices (see the n8n "May M13 FINAL - ranged slice bridge" workflow) or
run locally.
"""
import sys, json, os
import numpy as np
import pandas as pd

FULL_MONTH = 31           # May
PF_CEIL = 15000.0         # statutory PF wage ceiling
ESI_CEIL = 21000.0        # statutory ESI gross ceiling
SKIP_RULES = {'SKIP_ZERO_BASIC'}

VAR_COLS = ['OT AMOUNT', 'EXTRA OT', 'BASIC DA ARREARS', 'OTHER ARREARS', 'ATTENDANCE ALW',
            'PAID LEAVE', 'NATIONAL /FESTIVAL HOLIDAY', 'FESTIVAL HOLIDAY', 'WEEKLY OFF',
            'TRAVELLING ALLOWANCE', 'PAID HOLIDAY', 'NATIONAL HOLIDAY']


def num(s):
    return pd.to_numeric(s, errors='coerce').fillna(0.0)


def load(path):
    df = pd.read_excel(path, sheet_name='Salary (Corrected)', header=0, engine='openpyxl')
    # 5 trailing footer/summary rows (v3 addendum: _RESIDUAL_RECLASS_NB_ + blank +
    # 3 ECR-reconciliation label rows) — preserve, don't audit
    is_footer = df['EMPCODE'].isna() | ~df['MONTH'].astype(str).str.startswith('2025-05')
    footer = df[is_footer]
    data = df[~is_footer].copy()
    return data, footer


def main():
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    d, footer = load(src)
    n = len(d)
    r = {}          # check-id -> dict(result)
    viol_rows = {}  # check-id -> DataFrame of violating rows

    rule = d['RULE_APPLIED'].astype(str)
    active = ~rule.isin(SKIP_RULES)

    rb, rd = num(d['REVISED_BASIC']), num(d['REVISED_DA'])
    rpf, ecr = num(d['REVISED_PF']), num(d['ECR_PF'])
    resi = num(d['ESIC.1'])
    net, rnet = num(d['NETPAYABLE']), num(d['REVISED_NET_PAYABLE'])
    gross, ded = num(d['REVISED_GROSS']), num(d['REVISED_TOTAL_DED'])
    att = num(d['REVISED_ATTENDANCE_ALLOWANCE'])
    od = num(d['OTHER_DEDUCTION'])
    adj = num(d['ADJ_WORKING_DAYS'])
    rgn = num(d['REVISED_GROSS_NEW (final)'])
    normal = num(d['NORMALDAYS'])
    basic = num(d['BASIC'])

    def rec(cid, desc, mask, severity='FAIL', keep_cols=None, note=''):
        cnt = int(mask.sum())
        r[cid] = dict(desc=desc, violations=cnt, severity=severity, note=note)
        if cnt:
            cols = ['EMPCODE', 'FULLNAME', 'SITESTATE', 'RULE_APPLIED'] + (keep_cols or [])
            viol_rows[cid] = d.loc[mask, [c for c in cols if c in d.columns]]

    # ---------------- Golden rules ----------------
    emp = d.groupby(d['EMPCODE'].astype(str))[[]].size()
    g = pd.DataFrame({'rpf': rpf.values, 'ecr': ecr.values}, index=d['EMPCODE'].astype(str))
    ge = g.groupby(level=0).sum()
    gap = (ge['rpf'] - ge['ecr'])
    r['G1'] = dict(desc='Golden 1: per-employee SUM(REVISED_PF) = SUM(ECR_PF)',
                   violations=int((gap.abs() > 1).sum()),
                   severity='FAIL', note=f'total gap Rs.{(rpf.sum()-ecr.sum()):,.0f}; employees={len(ge):,}')
    rec('G3', 'Golden 3: NET unchanged per row (REVISED_NET = NETPAYABLE, +/-1)',
        (rnet - net).abs() > 1, keep_cols=['NETPAYABLE', 'REVISED_NET_PAYABLE'])
    fut = num(d['ESIC AS PER FUTURE'])
    r['G2'] = dict(desc='Golden 2: SUM(REVISED_ESIC) vs ESIC-as-per-Future',
                   violations=0 if abs(resi.sum() - fut.sum()) <= max(5.0, 0.00001*fut.sum()) else 1,
                   severity='FAIL',
                   note=f'REVISED_ESIC Rs.{resi.sum():,.0f} vs Future Rs.{fut.sum():,.2f} (diff Rs.{resi.sum()-fut.sum():,.2f})')

    # ---------------- Post-recon integrity C1-C8 ----------------
    rec('C1', 'OTHER_DEDUCTION >= 0 (+/-1)', od < -1, keep_cols=['OTHER_DEDUCTION'])
    rec('C2', 'REVISED_NET = REVISED_GROSS - REVISED_TOTAL_DED (+/-1)',
        (rnet - (gross - ded)).abs() > 1,
        keep_cols=['REVISED_GROSS', 'REVISED_TOTAL_DED', 'REVISED_NET_PAYABLE'])
    c3_scope = (rpf > 0)
    rec('C3', 'REVISED_PF = 12% x (REVISED_BASIC+REVISED_DA) (+/-1, PF>0 rows)',
        c3_scope & ((rpf - 0.12 * (rb + rd)).abs() > 1),
        keep_cols=['REVISED_BASIC', 'REVISED_DA', 'REVISED_PF'],
        note=f'scope {int(c3_scope.sum()):,} rows')
    c4_scope = (resi > 0)
    c4_strict = c4_scope & ((resi - (0.0075 * rgn).round()).abs() <= 1)
    r['C4'] = dict(desc='ESIC.1 = 0.75% x REVISED_GROSS_NEW(final) — informational',
                   violations=0, severity='INFO',
                   note=f'strict {int(c4_strict.sum()):,} / relaxed {int((c4_scope & ~c4_strict).sum()):,} of {int(c4_scope.sum()):,} ESI rows (relaxation expected where ESI pinned to Future)')
    rec('C5', 'REVISED_ATTENDANCE_ALLOWANCE >= 0', att < -0.5, keep_cols=['REVISED_ATTENDANCE_ALLOWANCE'])
    rec('C6', 'REVISED_TOTAL_DED >= 0', ded < -0.5, keep_cols=['REVISED_TOTAL_DED'])
    rec('C7', 'REVISED_GROSS = REVISED_BASIC+DA+ATT_ALW (+/-1)',
        (gross - (rb + rd + att)).abs() > 1, keep_cols=['REVISED_GROSS'])
    rec('C8', '|REVISED_NET - NETPAYABLE| <= 1 (same as G3, total drift)',
        (rnet - net).abs() > 1, note=f'total drift Rs.{(rnet.sum()-net.sum()):,.2f}')

    # ---------------- Day-adjustment set C9-C13 (recently added) ----------------
    rec('C9', 'ADJ_WORKING_DAYS in [1,31] and integer (active rows)',
        active & ((adj < 1) | (adj > FULL_MONTH)), keep_cols=['ADJ_WORKING_DAYS', 'NORMALDAYS'])
    nonint = active & (adj % 1 != 0)
    r['C9i'] = dict(desc='ADJ_WORKING_DAYS integer (C-INT)', violations=int(nonint.sum()),
                    severity='REVIEW', note='fractional day counts (day-tinker residue)')
    if nonint.any():
        viol_rows['C9i'] = d.loc[nonint, ['EMPCODE', 'FULLNAME', 'SITESTATE', 'RULE_APPLIED', 'ADJ_WORKING_DAYS']]
    c10 = (rpf > 0) & ((rb + rd) > PF_CEIL + 1)
    above_ceil = ecr > 1800  # ECR itself filed above the Rs.1,800 EE cap -> B+D>15k by construction
    rec('C10', 'PF>0 => REVISED_BASIC+DA <= 15,001', c10, severity='REVIEW',
        keep_cols=['REVISED_BASIC', 'REVISED_DA', 'REVISED_PF', 'ECR_PF'],
        note=f'{int((c10 & above_ceil).sum()):,} of these have ECR filed above the Rs.1,800 cap '
             f'(PF=ECR held; structural, cannot satisfy ceiling without breaking Golden Rule 1)')
    proj_bd = np.where(adj > 0, (rb + rd) * FULL_MONTH / np.where(adj > 0, adj, 1), 0.0)
    m6 = (ecr > 0) & (adj > 0) & (proj_bd > PF_CEIL + 0.5)
    m6_fixable = m6 & ~above_ceil & ((rb + rd) <= PF_CEIL + 1)
    rec('M6', 'Rule M6 / C10-hard: ECR_PF>0 => (B+D) x 31/ADJ_DAYS <= 15,000.5', m6_fixable,
        keep_cols=['REVISED_BASIC', 'REVISED_DA', 'ADJ_WORKING_DAYS', 'ECR_PF'],
        note=f'day-adjust fixable (send back through Step 6: ADJ_DAYS = ceil((B+D)x31/15000)); '
             f'plus {int((m6 & ~m6_fixable).sum()):,} structural above-ceiling-ECR rows counted under C10')
    c11 = active & (rpf <= 0) & (ecr <= 0) & ((rb + rd) > 0) & (adj > 0) & (proj_bd <= PF_CEIL)
    rec('C11', 'PF=0 => BD projection > 15K (self-consistency)', c11, severity='REVIEW',
        keep_cols=['REVISED_BASIC', 'REVISED_DA', 'ADJ_WORKING_DAYS'])
    c12 = (resi > 0) & (rgn > ESI_CEIL + 1)
    c12_periodcont = c12 & ((resi - (0.0075 * rgn).round()).abs() <= 1)
    rec('C12', 'ESI>0 => REVISED_GROSS_NEW(final) <= 21,001', c12, severity='REVIEW',
        keep_cols=['ESIC.1', 'REVISED_GROSS_NEW (final)'],
        note=f'{int(c12_periodcont.sum()):,} of these are exact 0.75% x gross and tie to the Future '
             f'register — ESI contribution-period continuation (statutory), not book errors')
    proj_gr = np.where(adj > 0, rgn * FULL_MONTH / np.where(adj > 0, adj, 1), 0.0)
    c13 = active & (resi <= 0) & (rgn > 0) & (adj > 0) & (proj_gr <= ESI_CEIL)
    rec('C13', 'ESI=0 => gross projection > 21K (self-consistency)', c13, severity='REVIEW',
        keep_cols=['REVISED_GROSS_NEW (final)', 'ADJ_WORKING_DAYS'])
    reccap = (ecr - rpf) > 1
    rec('CAP', 'ECR_PF <= REVISED_PF per row (ECR cap rule)', reccap,
        keep_cols=['ECR_PF', 'REVISED_PF'])

    # ---------------- C-MW min-wage floor (recently added) ----------------
    mw_scope = (rpf > 0) & (normal > 0)
    mw_floor = np.where(normal > 0, basic / np.where(normal > 0, normal, 1) * adj, 0.0)
    rec('C-MW', 'REVISED_BASIC >= (BASIC/NORMALDAYS) x ADJ_DAYS - 0.5 (PF>0 rows)',
        mw_scope & (rb < mw_floor - 0.5), severity='REVIEW',
        keep_cols=['BASIC', 'NORMALDAYS', 'ADJ_WORKING_DAYS', 'REVISED_BASIC'],
        note=f'scope {int(mw_scope.sum()):,} rows')

    # ---------------- v3 projection addendum ----------------
    stored_gp = num(d['MONTHLY_GROSS_PROJECTION'])
    recomputed_gp = pd.Series(proj_gr, index=d.index)
    drift = (stored_gp - recomputed_gp).abs() > 5
    r['PROJ'] = dict(desc='Stored MONTHLY_GROSS_PROJECTION vs recompute from RGN(final) & ADJ',
                     violations=0, severity='INFO',
                     note=f'{int(drift.sum()):,} rows drift >Rs.5 (documented v3 limitation — recomputed values used for checks)')
    implaus = recomputed_gp > 100000
    r['IMPL'] = dict(desc='IMPLAUSIBLE_PROJECTION: recomputed gross projection > Rs.1,00,000',
                     violations=int(implaus.sum()), severity='REVIEW', note='ballooning low-ADJ projections')
    if implaus.any():
        viol_rows['IMPL'] = d.loc[implaus, ['EMPCODE', 'FULLNAME', 'SITESTATE', 'RULE_APPLIED',
                                            'REVISED_GROSS_NEW (final)', 'ADJ_WORKING_DAYS']]

    # ---------------- ESI block invariants ----------------
    multi = d.groupby(d['EMPCODE'].astype(str))['EMPCODE'].transform('size') > 1
    prim = d.assign(_esi=resi).groupby(d['EMPCODE'].astype(str))['_esi'].transform('max')
    sec_bad = multi & (resi > 0) & (resi < prim)
    r['E-SEC'] = dict(desc='Multi-site: ESI carried on more than one row of an employee',
                      violations=int(sec_bad.sum()), severity='REVIEW',
                      note='secondary rows should carry ESI 0')
    if sec_bad.any():
        viol_rows['E-SEC'] = d.loc[sec_bad, ['EMPCODE', 'FULLNAME', 'SITESTATE', 'ESIC.1']]
    ge2 = pd.DataFrame({'resi': resi.values, 'fut': fut.values}, index=d['EMPCODE'].astype(str)).groupby(level=0).sum()
    matched = ge2[ge2['fut'] > 0]
    esi_gap = (matched['resi'] - matched['fut']).abs() > 1
    r['E-AGG'] = dict(desc='Per-employee SUM(ESIC.1) = ESIC-as-per-Future (matched employees, +/-1)',
                      violations=int(esi_gap.sum()), severity='FAIL',
                      note=f'{len(matched):,} matched employees; max per-emp gap Rs.{(matched["resi"]-matched["fut"]).abs().max():.2f}')

    # ---------------- M17 + M18a-e worklist (recently added) ----------------
    fg, gr0, days = num(d['FIXEDGROSS']), num(d['GROSS AMT']), normal
    div = num(d['SITEDIVISIONDAYS']).replace(0, 30)
    var = sum((num(d[c]).clip(lower=0) for c in VAR_COLS if c in d.columns))
    scope = (fg > 0) & (gr0 > 0) & (days > 0)
    per_day = (div == 1) | (fg < 3000)
    cand_pd = fg * days + var
    cand_mo = fg / div * days + var
    mid = (~per_day) & (fg < 6000)
    expected = np.where(per_day, cand_pd, cand_mo)
    exp_mid = np.where((cand_pd - gr0).abs() < (cand_mo - gr0).abs(), cand_pd, cand_mo)
    expected = np.where(mid, exp_mid, expected)
    gmin = pd.concat([gr0.where(gr0 > 0), gross.where(gross > 0), rgn.where(rgn > 0)], axis=1).min(axis=1)
    exc = np.minimum((gmin - expected).clip(lower=0), gmin.clip(lower=0))
    exc = np.minimum(exc, net.clip(lower=0))
    tol = np.maximum(500.0, expected * 0.02)
    close = ((gr0 - expected).abs() <= tol) | ((gross - expected).abs() <= tol) | ((rgn - expected).abs() <= tol)
    kept = scope & (exc >= 1) & (~close)
    hi = kept & (exc > 10000)
    r['M18-REC'] = dict(desc='M17/M18 recovery review (excess vs expected pay, cash-capped)',
                        violations=int(kept.sum()), severity='REVIEW',
                        note=f'HIGH(>Rs.10k): {int(hi.sum())} rows Rs.{float(exc[hi].sum()):,.0f}; total pool Rs.{float(exc[kept].sum()):,.0f}; cleared {int((scope & ~kept).sum()):,} of {int(scope.sum()):,} scanned')
    wl = d.loc[kept, ['EMPCODE', 'FULLNAME', 'CLIENTGROUPNAME', 'SITESTATE', 'NORMALDAYS', 'FIXEDGROSS', 'GROSS AMT']].copy()
    wl['EXPECTED'] = expected[kept].round(0)
    wl['EXCESS'] = exc[kept].round(0)
    viol_rows['M18-REC'] = wl.sort_values('EXCESS', ascending=False)

    esi_zero = (num(d['ESIC']) <= 0) & (resi <= 0)
    full_rate = np.where(per_day, fg * 26, fg)
    esi_enrol = scope & esi_zero & (full_rate > 0) & (full_rate <= ESI_CEIL)
    r['M18-ESI'] = dict(desc='M18c ESI enrollment needed (exempt but full-month rate <= 21k)',
                        violations=int(esi_enrol.sum()), severity='REVIEW',
                        note=f'4% exposure Rs.{float((gr0[esi_enrol] * 0.04).sum()):,.0f}/month')
    viol_rows['M18-ESI'] = d.loc[esi_enrol, ['EMPCODE', 'FULLNAME', 'CLIENTGROUPNAME', 'SITESTATE', 'GROSS AMT']]

    ctc = num(d['CTC'])
    wc_scope = (ctc > 0) & ((basic + num(d['DA'])) > 0) & (gr0 >= 0)
    ratio = np.where(ctc > 0, (basic + num(d['DA'])) / np.where(ctc > 0, ctc, 1), 1.0)
    wc_fail = wc_scope & (ratio < 0.5)
    sev30 = wc_fail & (ratio < 0.30)
    shortfall = float((ctc[wc_fail] * 0.5 - (basic + num(d['DA']))[wc_fail]).clip(lower=0).sum())
    r['M18-WC'] = dict(desc='Wage Code 50% check (BASIC+DA >= 50% of CTC)',
                       violations=int(wc_fail.sum()), severity='REVIEW',
                       note=f'{int(sev30.sum())} severe <30%; shortfall Rs.{shortfall:,.0f}/month')
    wcv = d.loc[wc_fail, ['EMPCODE', 'FULLNAME', 'CLIENTGROUPNAME', 'SITESTATE', 'BASIC', 'DA', 'CTC']].copy()
    wcv['PCT'] = (ratio[wc_fail] * 100).round(1)
    viol_rows['M18-WC'] = wcv.sort_values('PCT')

    # ---------------- output ----------------
    print(f'rows audited: {n:,} (+{len(footer)} footer rows preserved)')
    print(f"anchors: NET {net.sum():,.0f} | REVISED_PF {rpf.sum():,.0f} | ECR_PF {ecr.sum():,.0f} | "
          f"ESIC.1 {resi.sum():,.0f} | booked PF {num(d['PF']).sum():,.0f} | orig ESIC {num(d['ESIC']).sum():,.0f}")
    for cid, v in r.items():
        status = 'PASS' if v['violations'] == 0 else v['severity']
        print(f"{cid:8} {status:6} viol={v['violations']:<6} {v['desc']}  {v.get('note','')}")

    os.makedirs(out_dir, exist_ok=True)
    with pd.ExcelWriter(os.path.join(out_dir, 'May25_M13_check_violations.xlsx'), engine='openpyxl') as xw:
        for cid, vdf in viol_rows.items():
            if len(vdf):
                vdf.head(5000).to_excel(xw, sheet_name=cid[:31], index=False)
    json.dump({k: {kk: vv for kk, vv in v.items()} for k, v in r.items()},
              open(os.path.join(out_dir, 'may25_check_results.json'), 'w'), indent=1)
    print('wrote May25_M13_check_violations.xlsx + may25_check_results.json ->', out_dir)


if __name__ == '__main__':
    main()
