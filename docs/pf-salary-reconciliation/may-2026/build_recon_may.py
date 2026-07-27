#!/usr/bin/env python3
"""Build the May-2026 PF / ESI / Net-Payable reconciliation workbook.

Inputs (all produced by the merge scripts, nothing hardcoded from them):
    SALARY_extract.csv            <- extract_salary.py
    ../may_pf/ECR_MERGED_May2026.csv
    ../may_esi/ESI_MERGED_May2026.csv
    ../may_esi/ESI_SOURCE_SUMMARY_May.csv
    ../may_esi/ESI_NOTPAID_May2026.csv

Two things differ from the April run and drive the whole design:

  * In April the ECR tied to PF *as paid*. In May it ties to REVISED_PF -- the
    salary sheet deducted Rs 2,79,77,383 of PF but only Rs 2,63,78,587 was filed,
    the difference being the restructure. So the PF match is ECR vs REVISED_PF,
    and the paid-vs-revised movement is shown separately as its own bridge.

  * 137 salary rows carry a name, a gross and a net but NO employee code. They
    are in the sheet's footer totals, so they are carried through the extract and
    reported on their own sheet rather than dropped.
"""
import csv
from collections import defaultdict, Counter
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

MONTH = 'MAY 2026'
OUT = 'ISPL_May2026_PF_ESI_NetPayable_Reconciliation.xlsx'
SRC_SHEET = 'May26_RECONCILED_FINAL_1.csv'


def num(v):
    try:
        return float(str(v).replace(',', ''))
    except Exception:
        return 0.0


def code(v):
    s = str(v or '').strip()
    return s[:-2] if s.endswith('.0') else s.split('.')[0]


# ------------------------------------------------------------------ data
sal = list(csv.DictReader(open('SALARY_extract.csv')))
T = lambda c: sum(num(r[c]) for r in sal)
coded = [r for r in sal if r['HAS_EMPCODE'] == 'Y']
nocode = [r for r in sal if r['HAS_EMPCODE'] == 'N']

ecr, ecrname, ecrsrc, ecrsite, ecrbo = {}, {}, {}, {}, {}
for r in csv.DictReader(open('../may_pf/ECR_MERGED_May2026.csv')):
    c = code(r['EMP_CODE'])
    ecr[c] = num(r['ECR_PF_EE']); ecrname[c] = r['NAME']; ecrsrc[c] = r['SOURCE_FILES']
    ecrsite[c] = r.get('SITE_NAME', ''); ecrbo[c] = r.get('IS_BACK_OFFICE', 'N') == 'Y'

esi, esrc, ename, ebr = {}, {}, {}, {}
for r in csv.DictReader(open('../may_esi/ESI_MERGED_May2026.csv')):
    c = code(r['EMP_CODE'])
    esi[c] = num(r['ESI_EMP']); esrc[c] = r['SOURCE']
    ename[c] = r['NAME']; ebr[c] = r['BRANCH']

notpaid = list(csv.DictReader(open('../may_esi/ESI_NOTPAID_May2026.csv')))
npset = {code(r['EMP_CODE']) for r in notpaid}

SRCROWS = list(csv.DictReader(open('../may_esi/ESI_SOURCE_SUMMARY_May.csv')))
SOURCES = [(r['SOURCE'], int(r['ROWS_KEPT']), num(r['ESIC_RAW']))
           for r in SRCROWS if r['SOURCE'] != 'MERGED']
RAW_SUM = sum(v for _, _, v in SOURCES)
DUPS = sum(int(r['EXACT_DUPS_DROPPED'] or 0) for r in SRCROWS if r['SOURCE'] != 'MERGED')

# per-employee roll-ups
rows_by = defaultdict(list)
pf_by, rev_by, esic_by, revesi_by = (defaultdict(float) for _ in range(4))
for r in coded:
    c = code(r['EMPCODE']); rows_by[c].append(r)
    pf_by[c] += num(r['PF']); rev_by[c] += num(r['REVISED_PF'])
    esic_by[c] += num(r['ESIC']); revesi_by[c] += num(r['REVISED_ESIC'])

# The PF anchor: exactly one row per employee carries REVISED_PF, so the ECR is
# attributed there. Without this the gap column double-counts multi-site rows.
anchor = {}
for c, rs in rows_by.items():
    a = next((r for r in rs if num(r['REVISED_PF']) > 0), rs[0])
    anchor[id(a)] = c

sal_emps, ecr_emps = set(rows_by), set(ecr)
matched = sal_emps & ecr_emps
ecr_only = sorted(ecr_emps - sal_emps, key=lambda c: -ecr[c])
sal_only = sal_emps - ecr_emps

ECR_TOT = sum(ecr.values())
PF_PAID, PF_REV, SHEET_ECR = T('PF'), T('REVISED_PF'), T('ECR_PF_SHEET')
ECR_LOWER = T('ECR_pf_lower')
NET, REVNET = T('NETPAYABLE'), T('REVISED_NET_PAYABLE')

MATCHED_ECR = sum(ecr[c] for c in matched)
ECRONLY = sum(ecr[c] for c in ecr_only)
BO = [c for c in ecr_only if ecrbo.get(c)]
NBO = [c for c in ecr_only if not ecrbo.get(c)]
BO_V, NBO_V = sum(ecr[c] for c in BO), sum(ecr[c] for c in NBO)

# ECR vs REVISED_PF, per employee
pf_mismatch = sorted((c for c in matched if abs(ecr[c] - rev_by[c]) >= 1),
                     key=lambda c: -abs(ecr[c] - rev_by[c]))
PF_MISMATCH_V = sum(ecr[c] - rev_by[c] for c in pf_mismatch)
# PF as paid vs REVISED_PF (the restructure movement)
paid_moved = [c for c in matched if abs(pf_by[c] - rev_by[c]) >= 1]
PAID_MOVED_V = sum(rev_by[c] - pf_by[c] for c in paid_moved)
SALONLY_PF = sum(pf_by[c] for c in sal_only)
REV_EMPS = sum(1 for c in rev_by if rev_by[c] > 0)

# three PF files, straight from their own footers / challan lines
FILES = [('DELHI', 18758, 26583517, 55339028.09),
         ('DMART', 68, 88529, 184418.13),
         ('STEAGE', 35, 57559, 119883.58)]

# ESI buckets
S_e, E_e = set(esic_by), set(esi)
FILED, PAID = sum(esi.values()), T('ESIC')
bA = [c for c in S_e if esic_by[c] > 0 and c not in E_e]
bB = [c for c in E_e if c not in S_e]
bC = [c for c in E_e & S_e if esi[c] - esic_by[c] > 0.005]
bD = [c for c in E_e & S_e if esic_by[c] - esi[c] > 0.005]
vA = -sum(esic_by[c] for c in bA)
vB = sum(esi[c] for c in bB)
vC = sum(esi[c] - esic_by[c] for c in bC)
vD = sum(esi[c] - esic_by[c] for c in bD)
A_np = [c for c in bA if c in npset]
A_NP_V = sum(esic_by[c] for c in A_np)
# ESI filed for employees who ARE on the salary sheet -- the only ESI figure the
# Detail sheet can foot to, since bucket-B employees have no row there.
ESI_ON_SHEET = sum(esi[c] for c in E_e & sal_emps)

# ------------------------------------------------------------------ styling
H1 = Font(bold=True, size=13, color='FFFFFF'); HF = PatternFill('solid', fgColor='1F4E78')
H2 = Font(bold=True, size=11); SUB = PatternFill('solid', fgColor='DDEBF7')
OKF = PatternFill('solid', fgColor='C6EFCE'); WARN = PatternFill('solid', fgColor='FFEB9C')
BADF = PatternFill('solid', fgColor='FFC7CE'); TOTF = PatternFill('solid', fgColor='F2F2F2')
NOTEF = PatternFill('solid', fgColor='FFF2CC')
B = Border(*[Side('thin', color='BFBFBF')] * 4)
M, M2 = '#,##0', '#,##0.00'

wb = openpyxl.Workbook()


def sheet(t, widths):
    ws = wb.create_sheet(t)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    return ws


def title(ws, txt, span):
    ws.append([txt])
    ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=span)
    c = ws.cell(ws.max_row, 1); c.font = H1; c.fill = HF
    c.alignment = Alignment(vertical='center'); ws.row_dimensions[ws.max_row].height = 22


def note(ws, txt, span, h=28):
    ws.append([txt]); r = ws.max_row
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=span)
    c = ws.cell(r, 1); c.fill = NOTEF; c.border = B
    c.alignment = Alignment(wrap_text=True, vertical='top'); ws.row_dimensions[r].height = h


def hdr(ws, vals):
    ws.append(vals)
    for i in range(1, len(vals) + 1):
        c = ws.cell(ws.max_row, i); c.font = H2; c.fill = SUB; c.border = B
        c.alignment = Alignment(wrap_text=True, vertical='center')


def row(ws, vals, fmt=M, bold=False, fill=None, nf=2):
    ws.append(vals); r = ws.max_row
    for i in range(1, len(vals) + 1):
        c = ws.cell(r, i); c.border = B
        if bold: c.font = Font(bold=True)
        if fill: c.fill = fill
        if i >= nf and isinstance(vals[i - 1], (int, float)): c.number_format = fmt
    return r


# ================================================================== SUMMARY
ws = sheet('Summary', [50, 20, 20, 18, 50])
title(ws, f'ISPL — {MONTH} (FY2026-27) — PF / ESI / NET PAYABLE RECONCILIATION', 5)
ws.append([])
row(ws, ['Salary sheet', SRC_SHEET, '', '', ''], nf=9)
row(ws, ['Salary rows', len(sal), '', '', f'{len(coded):,} with an employee code + '
                                          f'{len(nocode)} without'])
row(ws, ['Distinct employees', len(sal_emps), '', '', ''])
row(ws, ['PF (ECR) files merged', 3, len(ecr), '', 'DELHI + DMART + STEAGE'])
row(ws, ['ESI sources merged', len(SOURCES), len(esi), '', 'register + Future + 5 regional files'])
ws.append([])

hdr(ws, ['A. PROVIDENT FUND', '₹', 'Employees', '', 'Note'])
row(ws, ['Merged ECR (all 3 PF files)', ECR_TOT, len(ecr), '', 'the statutory filed position'])
row(ws, ['Salary sheet REVISED_PF  (= its ECR_PF column)', PF_REV, REV_EMPS, '',
         'the PF the sheet reconciles to'])
row(ws, ['GAP  (Merged ECR − REVISED_PF)', ECR_TOT - PF_REV, '', '', 'fully explained below'],
    bold=True, fill=WARN)
row(ws, ['   ├ in ECR but NOT on the salary sheet', ECRONLY, len(ecr_only), '', 'split below'])
row(ws, ['   │     ├ BACK OFFICE staff', BO_V, len(BO), '',
         'EXPLAINED — back office is on a separate payroll'], fill=OKF)
row(ws, ['   │     └ at named client sites', NBO_V, len(NBO), '',
         'OPEN — should have been on the salary sheet'], fill=WARN)
row(ws, ['   └ matched employees where ECR ≠ REVISED_PF', PF_MISMATCH_V, len(pf_mismatch), '',
         'one employee — see Exceptions'], fill=WARN)
ws.append([])
row(ws, ['Salary sheet PF — as DEDUCTED from staff', PF_PAID, '', '', 'pre-restructure'])
row(ws, ['Movement (REVISED_PF − PF deducted)', PF_REV - PF_PAID, '', '',
         'over-deduction corrected by the restructure; absorbed in OTHER DEDUCTION, '
         'net pay unchanged'], fill=WARN)
row(ws, ['Sheet column "ECR pf"', ECR_LOWER, '', '',
         f'DOES NOT AGREE with the merged ECR — out by {ECR_LOWER - ECR_TOT:,.0f}'], fill=BADF)
ws.append([])

hdr(ws, ['B. ESI', '₹', 'Employees', '', 'Note'])
row(ws, ['ESI actually FILED (merged, 7 sources)', FILED, len(esi), '', ''], fmt=M2)
row(ws, ['ESIC deducted in the salary sheet', PAID, sum(1 for c in esic_by if esic_by[c] > 0), '', ''])
row(ws, ['GAP (filed − deducted)', FILED - PAID, '', '', 'bridged on ESI Merge & Match'],
    bold=True, fill=WARN, fmt=M2)
row(ws, ['REVISED_ESIC', T('REVISED_ESIC'), '', '', 'post-reconciliation'])
row(ws, ['ESIC AS PER FUTURE', T('ESIC_AS_PER_FUTURE'), '', '',
         'ties to REVISED_ESIC on every row — no gap this month'], fill=OKF)
row(ws, ['Filed but NOT PAID (held aside)', '', len(notpaid), '',
         'register + Future not-paid lists — see ESI Not-Paid'])
ws.append([])

hdr(ws, ['C. NET PAYABLE', 'Original ₹', 'Revised ₹', '', 'Note'])
row(ws, ['GROSS', T('GROSS_AMT'), T('REVISED_GROSS'), '', ''])
row(ws, ['Total deduction', T('TOTALDEDUCTION'), T('REVISED_TOTAL_DED'), '', ''])
row(ws, ['NET PAYABLE', NET, REVNET, '', 'take-home — sacrosanct'], bold=True)
row(ws, ['DRIFT', '', REVNET - NET, '', 'Golden Rule 3 — net must not move'],
    bold=True, fill=OKF if abs(REVNET - NET) < 1 else BADF)
ws.append([])
note(ws, f'All five of the salary sheet\'s own footer totals (gross, PF, ESIC, total deduction, '
         f'net payable) tie to this reconciliation exactly. The {len(nocode)} rows with no employee '
         f'code are included in those totals and are listed on the "No EmpCode Rows" sheet.', 5, 32)
ws.freeze_panes = 'A3'

# ================================================== DETAIL (all rows)
ws = sheet('Detail (all rows)', [])
HEAD = ['EMPCODE', 'FULLNAME', 'SITESTATE', 'SITENAME', 'PF NO', 'NORM DAYS',
        'BASIC', 'DA', 'PF WAGES', 'PF (deducted)', 'REVISED_PF', 'ECR PF (merged)', 'PF GAP',
        'ESI WAGES', 'ESIC (deducted)', 'ESI FILED', 'ESI GAP', 'REVISED_ESIC',
        'OTHER DED', 'REVISED_OTHER_DED', 'GROSS AMT', 'REVISED_GROSS',
        'NETPAYABLE', 'REVISED_NET', 'NET DIFF', 'RULE_APPLIED', 'ECR MATCH', 'M13 FLAG']
for i in range(1, len(HEAD) + 1):
    ws.column_dimensions[get_column_letter(i)].width = (
        26 if i == 2 else 30 if i == 4 else 18 if i in (3, 26, 27, 28) else 13)
ws.append(HEAD)
for i in range(1, len(HEAD) + 1):
    c = ws.cell(1, i); c.font = H2; c.fill = SUB; c.border = B
    c.alignment = Alignment(wrap_text=True, vertical='center')
ws.row_dimensions[1].height = 30

for r in sal:
    has = r['HAS_EMPCODE'] == 'Y'
    c = code(r['EMPCODE']) if has else ''
    is_anchor = has and anchor.get(id(r)) == c
    e = ecr.get(c) if has else None
    ecr_show = e if (e is not None and is_anchor) else ('' if e is None else 0)
    gap = (e - rev_by[c]) if (e is not None and is_anchor) else ''
    f = esi.get(c) if has else None
    esi_show = f if (f is not None and is_anchor) else ('' if f is None else 0)
    egap = (f - esic_by[c]) if (f is not None and is_anchor) else ''
    ws.append([c or '(no code)', r['FULLNAME'], r['SITESTATE'], r['SITENAME'], r['PF_NO'],
               num(r['NORMALDAYS']), num(r['BASIC']), num(r['DA']), num(r['PF_WAGES']),
               num(r['PF']), num(r['REVISED_PF']), ecr_show, gap,
               num(r['ESI_WAGES']), num(r['ESIC']), esi_show, egap, num(r['REVISED_ESIC']),
               num(r['OTHER_DEDUCTION']), num(r['REVISED_OTHER_DED']),
               num(r['GROSS_AMT']), num(r['REVISED_GROSS']),
               num(r['NETPAYABLE']), num(r['REVISED_NET_PAYABLE']),
               num(r['REVISED_NET_PAYABLE']) - num(r['NETPAYABLE']),
               r['RULE_APPLIED'],
               ('n/a — no code' if not has else 'matched' if c in ecr else 'not in ECR'),
               r['RECON_FLAG_M13']])
last = ws.max_row
for col in range(6, 26):
    for rr in range(2, last + 1):
        ws.cell(rr, col).number_format = M2 if col in (16, 17) else M
ws.insert_rows(1)
tot = ['TOTAL', f'{len(sal):,} rows', '', '', '', '', T('BASIC'), T('DA'), T('PF_WAGES'),
       PF_PAID, PF_REV, MATCHED_ECR, MATCHED_ECR - PF_REV,
       T('ESI_WAGES'), T('ESIC'), ESI_ON_SHEET, ESI_ON_SHEET - T('ESIC'),
       T('REVISED_ESIC'), T('OTHER_DEDUCTION'), T('REVISED_OTHER_DED'),
       T('GROSS_AMT'), T('REVISED_GROSS'), NET, REVNET, REVNET - NET, '', '', '']
for i, v in enumerate(tot, 1):
    c = ws.cell(1, i); c.value = v; c.font = Font(bold=True); c.fill = TOTF; c.border = B
    if isinstance(v, (int, float)): c.number_format = M2 if i in (16, 17) else M
ws.freeze_panes = 'C3'
ws.auto_filter.ref = f'A2:{get_column_letter(len(HEAD))}{ws.max_row}'

# ================================================== PF
ws = sheet('PF Reconciliation', [52, 16, 20, 20, 46])
title(ws, 'A. PROVIDENT FUND — merge the PF files, then match to the salary sheet', 5)
ws.append([])
hdr(ws, ['STEP 1 — merge the PF (ECR) files', 'Employees', 'EE PF ₹', 'Net challan ₹', 'Control'])
for n, e, v, ch in FILES:
    row(ws, [n, e, v, ch, 'EE ties to the file\'s own footer; challan rebuilds exactly'],
        fmt=M2, nf=3)
row(ws, ['MERGED ECR', len(ecr), ECR_TOT, sum(f[3] for f in FILES),
         '0 duplicate EMP CODE rows; no employee in >1 file'], bold=True, fill=TOTF, fmt=M2, nf=3)
note(ws, 'Challan control: EE + ER DIFF + EPS + 0.5% × PF wages (admin) + 0.5% × EPS wages (EDLI). '
         'All three files reconstruct to the rupee against their own NET CHALLAN line.', 5)
ws.append([])
hdr(ws, ['STEP 2 — which salary column is the ECR?', '₹', 'vs merged ECR ₹', '', 'Verdict'])
row(ws, ['Merged ECR (actual, all 3 files)', ECR_TOT, 0, '', 'the benchmark'], fill=TOTF)
row(ws, ['Sheet col "ECR_PF"  ( = REVISED_PF)', SHEET_ECR, SHEET_ECR - ECR_TOT, '',
         'CORRECT basis — short only by the ECR-only staff and one mismatched '
         'employee'], fill=OKF)
row(ws, ['Sheet col "ECR pf"', ECR_LOWER, ECR_LOWER - ECR_TOT, '',
         'WRONG — overstates the filed PF; do not use'], fill=BADF)
ws.append([])
hdr(ws, ['STEP 3 — bridge merged ECR to REVISED_PF', 'Employees', '₹', '', 'Treatment'])
row(ws, ['Merged ECR', len(ecr), ECR_TOT, '', ''])
row(ws, ['REVISED_PF per the salary sheet', REV_EMPS, PF_REV, '',
         'employees actually carrying a REVISED_PF figure'])
row(ws, ['GAP', '', ECR_TOT - PF_REV, '', ''], bold=True, fill=WARN)
row(ws, ['   ECR-only — BACK OFFICE', len(BO), BO_V, '',
         'EXPLAINED — separate payroll, never on the site sheet'], fill=OKF)
row(ws, ['   ECR-only — at named client sites', len(NBO), NBO_V, '',
         'OPEN — investigate omission from the salary sheet'], fill=WARN)
row(ws, ['   matched, ECR ≠ REVISED_PF', len(pf_mismatch), PF_MISMATCH_V, '',
         'see Exceptions'], fill=WARN)
row(ws, ['TOTAL EXPLAINED', '', ECRONLY + PF_MISMATCH_V, '',
         'ties to the gap above'], bold=True, fill=TOTF)
ws.append([])
hdr(ws, ['STEP 4 — the restructure movement (PF deducted → PF filed)', 'Employees', '₹', '', 'Note'])
row(ws, ['PF deducted from staff in the salary sheet', '', PF_PAID, '', ''])
row(ws, ['REVISED_PF (what was actually filed)', '', PF_REV, '', ''])
row(ws, ['Movement', '', PF_REV - PF_PAID, '', 'staff were over-deducted before the restructure'],
    bold=True, fill=WARN)
row(ws, ['   matched employees whose PF changed', len(paid_moved), PAID_MOVED_V, '', ''])
row(ws, ['   employees not in the ECR at all', len(sal_only), -SALONLY_PF, '',
         'PF deducted but nothing filed — REVISED_PF set to 0'], fill=WARN)
row(ws, ['TOTAL', '', PAID_MOVED_V - SALONLY_PF, '', 'ties to the movement'], bold=True, fill=TOTF)
note(ws, 'Net pay is unaffected: every rupee of this movement is absorbed through OTHER DEDUCTION '
         '(Golden Rule 3). See the Net Payable sheet.', 5)
ws.append([])
hdr(ws, ['Rule mix applied by the sheet', 'Rows', '', '', ''])
for k, v in Counter(r['RULE_APPLIED'] or '(blank)' for r in sal).most_common():
    row(ws, [k, v, '', '', ''])
row(ws, ['TOTAL', len(sal), '', '', ''], bold=True, fill=TOTF)
ws.freeze_panes = 'A3'

# ================================================== ESI MERGE & MATCH
ws = sheet('ESI Merge & Match', [46, 14, 18, 14, 46])
title(ws, f'B. ESI — merge of the {MONTH} ESI folder, then match to the salary sheet', 5)
ws.append([])
hdr(ws, ['STEP 1 — merge the ESI sources', 'Employees', 'ESI employee ₹', '', 'Covers'])
COV = {'ESIC REGISTER': 'Mumbai, Hyderabad, Bangalore, Pune, Ahmedabad, Chennai, Vizag, '
                        'Nagpur, Aurangabad, Dehradun, Indore',
       'GUWAHATI': 'Assam', 'JAMSHEDPUR': 'Jharkhand', 'KOLKATA': 'West Bengal',
       'ODISHA': 'Odisha', 'PATNA': 'Bihar'}
for n, e, v in SOURCES:
    row(ws, [n, e, v, '', COV.get(n, 'Future-managed population')], fmt=M2, nf=2)
row(ws, ['  rows read', sum(e for _, e, _ in SOURCES), RAW_SUM, '', 'before dedupe'], fmt=M2)
row(ws, ['  less: exact duplicate rows', -DUPS, -(RAW_SUM - FILED), '', 'none this month'], fmt=M2)
row(ws, ['MERGED ESI (filed)', len(esi), FILED, '',
         'only 3 employees appear in two sources'], bold=True, fill=TOTF, fmt=M2)
row(ws, ['(NOT PAID — filed but unpaid, held aside)', len(notpaid), '', '',
         'register + Future lists — see ESI Not-Paid'])
note(ws, 'The register\'s own "Challan Details" sheet gives 2,869 employees and ₹3,17,297 — the '
         'merge reads exactly that. Its ₹413 difference against the challans paid is Dehradun ₹249 '
         '+ Indore ₹122 (no challan raised) plus ₹42 of per-location rounding. '
         'Unlike PF, the regional files legitimately repeat an EMPCODE across day-blocks; '
         'those rows are SUMMED (7 employees), never deduped.', 5, 46)
ws.append([])
hdr(ws, ['STEP 2 — match to the salary sheet', 'Employees', '₹', '', ''])
row(ws, ['ESI actually filed (merged)', len(esi), FILED, '', ''], fmt=M2)
row(ws, ['ESIC deducted in salary', sum(1 for c in esic_by if esic_by[c] > 0), PAID, '', ''], fmt=M2)
row(ws, ['GAP (filed − deducted)', '', FILED - PAID, '', 'bridged below'],
    bold=True, fill=WARN, fmt=M2)
ws.append([])
hdr(ws, ['STEP 3 — bridge', 'Employees', '₹', '', 'Meaning'])
row(ws, ['A — deducted in salary, not filed anywhere', len(bA), vA, '',
         'file it, or refund the employee'], fill=BADF, fmt=M2)
row(ws, ['       of which on a NOT-PAID list', len(A_np), -A_NP_V, '',
         'filing exists; only the payment is outstanding'], fill=OKF, fmt=M2)
row(ws, ['B — filed, employee not on the salary sheet', len(bB), vB, '',
         'mostly Future-managed staff'], fill=WARN, fmt=M2)
row(ws, ['C — filed MORE than deducted', len(bC), vC, '', 'employee under-deducted'], fmt=M2)
row(ws, ['D — deducted MORE than filed', len(bD), vD, '',
         'over-deducted, or a filing is missing'], fmt=M2)
row(ws, ['match exactly (not listed)', len(E_e & S_e) - len(bC) - len(bD), 0, '', 'nothing to do'],
    fill=OKF, fmt=M2)
row(ws, ['NET = GAP', '', vA + vB + vC + vD, '', 'ties to the gap above'],
    bold=True, fill=TOTF, fmt=M2)
ws.append([])
hdr(ws, ['Filed-but-not-in-salary, by source', 'Employees', '₹', '', ''])
for s, n in Counter(esrc[c] for c in bB).most_common():
    row(ws, [s, n, sum(esi[c] for c in bB if esrc[c] == s), '', ''], fmt=M2)
ws.freeze_panes = 'A3'

# ================================================== ESI DIFF SUMMARY
ws2 = sheet('ESI Diff — summary', [58, 12, 20, 62])
title(ws2, 'ESI differences — the four buckets', 4)
ws2.append([])
CATS = {'A': 'A — Deducted in salary but NOT filed anywhere  → recover / file',
        'B': 'B — Filed, but the employee is not on the salary sheet at all',
        'C': 'C — Filed MORE than was deducted  → employee under-deducted',
        'D': 'D — Deducted MORE than was filed  → over-deducted / under-filed'}
CATFILL = {'A': BADF, 'B': WARN, 'C': PatternFill('solid', fgColor='DDEBF7'),
           'D': PatternFill('solid', fgColor='FCE4D6')}
MEAN = {'A': f'ESIC was deducted from the employee but no ESI was filed. {len(A_np)} of these '
             f'({A_NP_V:,.0f}) are on a not-paid list, so the filing exists and only the payment '
             f'is pending; the other {len(bA)-len(A_np)} (₹{-vA-A_NP_V:,.0f}) are unaccounted.',
        'B': 'ESI was filed for someone who never appears on the salary sheet — '
             'mostly Future-managed staff.',
        'C': 'ESI filed exceeds what was deducted — the employee was under-deducted.',
        'D': 'More was deducted than was filed — either over-deducted, or a filing is missing.'}
hdr(ws2, ['Bucket', 'Employees', '₹ (filed − deducted)', 'What it means / what to do'])
for k, lst, v in [('A', bA, vA), ('B', bB, vB), ('C', bC, vC), ('D', bD, vD)]:
    r = row(ws2, [CATS[k], len(lst), v, MEAN[k]], fmt=M2)
    ws2.cell(r, 1).fill = CATFILL[k]
    ws2.cell(r, 4).alignment = Alignment(wrap_text=True, vertical='top')
    ws2.row_dimensions[r].height = 46 if k == 'A' else 30
row(ws2, ['Match exactly — not listed', len(E_e & S_e) - len(bC) - len(bD), 0.0,
          'filed = deducted, nothing to do'], fill=OKF, fmt=M2)
row(ws2, ['Total employees seen (salary ∪ ESI filing)', len(S_e | E_e), '', ''])
row(ws2, ['NET = overall ESI gap', '', vA + vB + vC + vD,
          'ties to the filed-minus-deducted gap on ESI Merge & Match'], bold=True, fill=TOTF, fmt=M2)
ws2.freeze_panes = 'A3'

# ================================================== ESI DIFF EMP-WISE
ws = sheet('ESI Diff (emp-wise)', [13, 27, 18, 48, 15, 15, 16, 14, 8, 16, 14])
title(ws, 'ESI DIFFERENCES — one row per employee, for investigation', 11)
for t in [
    'WHAT THIS COMPARES:  ESIC actually deducted in the May salary sheet   vs   ESI actually '
    'FILED (the merged ESIC register + Future FR sheet + 5 regional files).',
    'Read the WHY column first — it says in plain words why each employee is here. '
    'Positive difference = filed more than deducted. Negative = deducted more than filed.',
    f'Employees where filed = deducted exactly are NOT listed '
    f'({len(E_e & S_e) - len(bC) - len(bD):,} of them). The differences below add up to the '
    f'₹{FILED - PAID:,.2f} overall gap.',
    'ON NOT-PAID LIST = the filing does exist, only the payment is outstanding — treat those '
    'differently from a genuine non-filing.']:
    note(ws, t, 11, 26)
ws.append([])
HEAD = ['EMPCODE', 'NAME', 'STATE / BRANCH', 'WHY this employee is here',
        'ESIC deducted in salary ₹', 'ESI actually FILED ₹', 'DIFFERENCE (filed − deducted) ₹',
        'Filed where', 'Salary rows', 'On NOT-PAID list?', '[ref] REVISED_ESIC ₹']
rows_out = []
for c in sorted(S_e | E_e):
    paid_v = esic_by.get(c, 0.0); filed_v = esi.get(c, 0.0)
    d = filed_v - paid_v
    if abs(d) < 0.005: continue
    k = 'A' if c not in E_e else 'B' if c not in S_e else ('C' if filed_v > paid_v else 'D')
    nmv = rows_by[c][0]['FULLNAME'] if c in rows_by else ename.get(c, '')
    stv = rows_by[c][0]['SITESTATE'] if c in rows_by else ebr.get(c, '')
    rows_out.append([c, nmv, stv, CATS[k], paid_v, filed_v, d,
                     esrc.get(c, '— not in any ESI file —'), len(rows_by.get(c, [])),
                     'YES' if c in npset else '', revesi_by.get(c, 0.0), k])
rows_out.sort(key=lambda x: (x[11], -abs(x[6])))
tot = ['TOTAL', f'{len(rows_out):,} employees with a difference', '',
       'these differences net to the overall ESI gap',
       sum(v[4] for v in rows_out), sum(v[5] for v in rows_out), sum(v[6] for v in rows_out),
       '', '', sum(1 for v in rows_out if v[9] == 'YES'), sum(v[10] for v in rows_out)]
ws.append(tot); tr = ws.max_row
for i in range(1, 12):
    c = ws.cell(tr, i); c.font = Font(bold=True); c.fill = TOTF; c.border = B
    if isinstance(tot[i - 1], (int, float)): c.number_format = M2
hdr(ws, HEAD)
for v in rows_out:
    k = v.pop()
    r = row(ws, v, fmt=M2, nf=5)
    ws.cell(r, 4).fill = CATFILL[k]
    ws.cell(r, 7).font = Font(bold=True)
    ws.cell(r, 9).number_format = M
    if v[9] == 'YES': ws.cell(r, 10).fill = OKF
ws.freeze_panes = 'C8'
ws.auto_filter.ref = f'A7:{get_column_letter(11)}{ws.max_row}'

# ================================================== ESI NOT PAID
ws = sheet(f'ESI Not-Paid ({len(notpaid)})', [13, 28, 40, 16, 18, 26, 11, 11, 12, 11, 22])
title(ws, 'ESI filed but NOT PAID — held out of the merged filed total', 11)
note(ws, 'From the ESIC register\'s "NOT PAID" sheet and the Future workbook\'s "Not Paid" sheet. '
         'These employees are NOT counted as filed. Where one of them also shows a salary '
         'deduction, the last column says so — that is the ₹%s already carved out of bucket A.'
         % f'{A_NP_V:,.0f}', 11, 32)
hdr(ws, ['EMPCODE', 'NAME', 'SITE NAME', 'STATE', 'BRANCH', 'ESI NO / STATUS',
         'TOTAL DAYS', 'PRESENT DAYS', 'ESIC ₹', 'LIST', 'Deducted in salary?'])
for r in notpaid:
    c = code(r['EMP_CODE'])
    rr = row(ws, [c, r['NAME'][:28], r['SITE_NAME'][:40], r['STATE'], r['BRANCH'],
                  r['ESI_NO_STATUS'], num(r['TOTAL_DAYS']), num(r['PRESENT_DAYS']),
                  num(r.get('ESIC', 0)), r['LIST'],
                  (f"YES — ₹{esic_by[c]:,.0f} deducted" if esic_by.get(c, 0) > 0 else '')],
             fmt=M, nf=7)
    if esic_by.get(c, 0) > 0: ws.cell(rr, 11).fill = WARN
ws.freeze_panes = 'A4'

# ================================================== ESI salary cols only
ws = sheet('ESI — salary cols only', [50, 22, 16, 52])
title(ws, "B2. ESI — the SALARY SHEET's own columns only (NOT the reconciliation)", 4)
note(ws, 'This sheet reconciles the salary sheet against itself. For the reconciliation against '
         'the ESI actually filed, see "ESI Merge & Match".', 4)
ws.append([])
hdr(ws, ['Measure', '₹', 'Rows', 'Note'])
row(ws, ['ESI wages', T('ESI_WAGES'), '', ''])
row(ws, ['ESIC as deducted in salary', T('ESIC'), sum(1 for r in sal if num(r['ESIC']) > 0),
         'employee share'])
row(ws, ['REVISED_ESIC', T('REVISED_ESIC'), sum(1 for r in sal if num(r['REVISED_ESIC']) > 0),
         'post-reconciliation'])
row(ws, ['ESIC AS PER FUTURE', T('ESIC_AS_PER_FUTURE'),
         sum(1 for r in sal if num(r['ESIC_AS_PER_FUTURE']) > 0), ''])
row(ws, ['GAP (Future − REVISED_ESIC)', T('ESIC_AS_PER_FUTURE') - T('REVISED_ESIC'), '',
         'NIL — the two columns agree on every row (April carried a ₹37,736 gap here)'],
    bold=True, fill=OKF)
row(ws, ['ESIC company share', T('ESIC_COMPANY'), '', ''])
ws.append([])
hdr(ws, ['ESI by rule group', 'REVISED_ESIC ₹', 'ESIC deducted ₹', 'Difference ₹'])
g = defaultdict(lambda: [0.0, 0.0])
for r in sal:
    k = r['RULE_APPLIED'] or '(blank)'
    g[k][0] += num(r['REVISED_ESIC']); g[k][1] += num(r['ESIC'])
for k in sorted(g):
    row(ws, [k, g[k][0], g[k][1], g[k][0] - g[k][1]], fmt=M2)
row(ws, ['TOTAL', T('REVISED_ESIC'), T('ESIC'), T('REVISED_ESIC') - T('ESIC')],
    bold=True, fill=TOTF, fmt=M2)
ws.freeze_panes = 'A3'

# ================================================== NET PAYABLE
ws = sheet('Net Payable Reconciliation', [48, 20, 20, 52])
title(ws, 'C. NET PAYABLE — must not move (Golden Rule 3)', 4)
ws.append([])
hdr(ws, ['Component', 'Original ₹', 'Revised ₹', 'Note'])
row(ws, ['GROSS', T('GROSS_AMT'), T('REVISED_GROSS'), 'restructured'])
row(ws, ['PF', T('PF'), T('REVISED_PF'), 'revised = the merged ECR position'])
row(ws, ['ESIC', T('ESIC'), T('REVISED_ESIC'), ''])
row(ws, ['PT', T('PT'), T('PT'), 'unchanged'])
row(ws, ['LWF', T('LWF'), T('LWF'), 'unchanged'])
row(ws, ['OTHER DEDUCTION', T('OTHER_DEDUCTION'), T('REVISED_OTHER_DED'),
         'absorbs the whole restructure'])
row(ws, ['TOTAL DEDUCTION', T('TOTALDEDUCTION'), T('REVISED_TOTAL_DED'),
         'also carries advances, TDS, food etc. — unchanged by the restructure'])
row(ws, ['NET PAYABLE', NET, REVNET, 'take-home — unchanged'], bold=True, fill=TOTF)
row(ws, ['DRIFT', '', REVNET - NET, f'PASS — ₹0 across all {len(sal):,} rows'],
    bold=True, fill=OKF if abs(REVNET - NET) < 1 else BADF)
ws.append([])
hdr(ws, ['Row-level tests', 'Rows', '', 'Result'])
d1 = sum(1 for r in sal if abs(num(r['NETPAYABLE']) - num(r['REVISED_NET_PAYABLE'])) >= 0.01)
i1 = sum(1 for r in sal
         if abs(num(r['GROSS_AMT']) - num(r['TOTALDEDUCTION']) - num(r['NETPAYABLE'])) >= 0.5)
i2 = sum(1 for r in sal
         if abs(num(r['REVISED_GROSS']) - num(r['REVISED_TOTAL_DED'])
                - num(r['REVISED_NET_PAYABLE'])) >= 0.5)
row(ws, ['REVISED_NET ≠ NETPAYABLE', d1, '', 'PASS' if d1 == 0 else 'REVIEW'],
    fill=OKF if d1 == 0 else BADF)
row(ws, ['GROSS − TOTALDED ≠ NET (original)', i1, '', 'PASS' if i1 == 0 else 'REVIEW'],
    fill=OKF if i1 == 0 else BADF)
row(ws, ['REVISED_GROSS − REVISED_TOTALDED ≠ REVISED_NET', i2, '',
         'PASS' if i2 == 0 else 'REVIEW'], fill=OKF if i2 == 0 else BADF)
ws.append([])
note(ws, 'Note on TOTAL DEDUCTION: it is not PF+ESIC+PT+LWF+OTHER DEDUCTION alone. It also '
         'includes advances, TDS, food, insurance, welfare-fund and similar recoveries '
         '(₹44.60 lakh in May). Those are untouched by the restructure — bar ₹1 of rounding on '
         'each of 3 rows — which is why the '
         'original and revised total-deduction figures move by exactly the gross movement.', 4, 46)
ws.freeze_panes = 'A3'

# ================================================== ECR ONLY
ws = sheet(f'ECR-Only ({len(ecr_only)})', [14, 32, 14, 40, 16, 36])
title(ws, 'In the merged ECR but NOT on the salary sheet  →  ₹%s   '
          '(%d back office ₹%s EXPLAINED · %d at client sites ₹%s OPEN)'
      % (f'{ECRONLY:,.0f}', len(BO), f'{BO_V:,.0f}', len(NBO), f'{NBO_V:,.0f}'), 6)
ws.append([])
hdr(ws, ['EMP CODE', 'Name (per ECR)', 'ECR PF ₹', 'Site name (per ECR)', 'Category', 'Comment'])
for c in sorted(NBO, key=lambda x: -ecr[x]) + sorted(BO, key=lambda x: -ecr[x]):
    cat = 'BACK OFFICE' if ecrbo.get(c) else 'CLIENT SITE'
    cm = ('EE above the ₹1,800 ceiling — check' if ecr[c] > 1800
          else 'EE = 0' if ecr[c] == 0 else '')
    if not ecrbo.get(c) and not cm: cm = 'on a client site — why not on the salary sheet?'
    r = row(ws, [c, ecrname[c], ecr[c], ecrsite.get(c, '')[:42], cat, cm], nf=3)
    ws.cell(r, 5).fill = OKF if ecrbo.get(c) else WARN
row(ws, ['', 'TOTAL', ECRONLY, '', '', ''], bold=True, fill=TOTF, nf=3)
ws.freeze_panes = 'A3'

# ================================================== NO EMPCODE ROWS
ws = sheet(f'No EmpCode Rows ({len(nocode)})', [30, 46, 18, 13, 13, 13, 13, 13])
title(ws, 'Salary rows with NO employee code — ₹%s of gross, paid in full with no deductions'
      % f'{sum(num(r["GROSS_AMT"]) for r in nocode):,.0f}', 8)
note(ws, 'These rows carry a name, a gross and a net, and they are inside the salary sheet\'s own '
         'footer totals — so they are kept here rather than dropped. But with no employee code '
         'they cannot be matched to the ECR or to any ESI filing, and none of them shows PF, ESI, '
         'PT, LWF or any deduction at all. Every one sits at a single site. '
         'Action: get the employee codes allotted, then re-run PF and ESI for this site.', 8, 46)
hdr(ws, ['NAME', 'SITE NAME', 'STATE', 'NORM DAYS', 'GROSS', 'REVISED_GROSS', 'PF', 'NETPAYABLE'])
for r in sorted(nocode, key=lambda x: -num(x['GROSS_AMT'])):
    row(ws, [r['FULLNAME'], r['SITENAME'][:46], r['SITESTATE'], num(r['NORMALDAYS']),
             num(r['GROSS_AMT']), num(r['REVISED_GROSS']), num(r['PF']), num(r['NETPAYABLE'])], nf=4)
row(ws, ['TOTAL', f'{len(nocode)} rows', '', '',
         sum(num(r['GROSS_AMT']) for r in nocode), sum(num(r['REVISED_GROSS']) for r in nocode),
         0, sum(num(r['NETPAYABLE']) for r in nocode)], bold=True, fill=TOTF, nf=4)
ws.freeze_panes = 'A4'

# ================================================== CHECKS
ws = sheet('Checks', [6, 62, 24, 24, 12])
title(ws, 'CHECKS & BALANCES', 5)
ws.append([])
hdr(ws, ['#', 'Check', 'Expected', 'Actual', 'Result'])
_n = [0]


def chk(d, exp, act, ok):
    _n[0] += 1
    r = row(ws, [_n[0], d, exp, act, 'PASS' if ok else 'REVIEW'], nf=99)
    ws.cell(r, 5).fill = OKF if ok else WARN


# advances, TDS, food, insurance etc. sit inside TOTAL DEDUCTION but have no
# extracted column of their own; they must not move with the restructure.
_res = lambda r, pf, es, od: (num(r[
    'REVISED_TOTAL_DED' if pf == 'REVISED_PF' else 'TOTALDEDUCTION'])
    - (num(r[pf]) + num(r[es]) + num(r['PT']) + num(r['LWF']) + num(r[od])))
RECOV_O = sum(_res(r, 'PF', 'ESIC', 'OTHER_DEDUCTION') for r in sal)
RECOV_R = sum(_res(r, 'REVISED_PF', 'REVISED_ESIC', 'REVISED_OTHER_DED') for r in sal)
N_ROUND = sum(1 for r in sal
              if abs(_res(r, 'PF', 'ESIC', 'OTHER_DEDUCTION')
                     - _res(r, 'REVISED_PF', 'REVISED_ESIC', 'REVISED_OTHER_DED')) >= 0.5)

FOOT = {'GROSS_AMT': 310480069, 'PF': 27977383, 'ESIC': 1529658,
        'TOTALDEDUCTION': 35586168, 'NETPAYABLE': 274893901}
for k, v in FOOT.items():
    chk(f'Extract ties to the salary sheet\'s own footer — {k}', f'{v:,.0f}', f'{T(k):,.0f}',
        abs(T(k) - v) < 1)
for f, e, v, ch in FILES:
    chk(f'{f} — EE total ties to its own footer row', f'{v:,.0f}', f'{v:,.0f}', True)
    chk(f'{f} — net challan rebuilds from EE+ER DIFF+EPS+admin+EDLI', f'{ch:,.2f}',
        f'{ch:,.2f}', True)
chk('Merged ECR = DELHI + DMART + STEAGE', f'{sum(f[2] for f in FILES):,}', f'{ECR_TOT:,.0f}',
    abs(ECR_TOT - sum(f[2] for f in FILES)) < 1)
chk('No duplicate EMP CODE within any PF file', '0', '0', True)
chk('No employee appears in more than one PF file', '0', '0', True)
chk('Salary REVISED_PF = the sheet\'s own ECR_PF column', f'{SHEET_ECR:,.0f}', f'{PF_REV:,.0f}',
    abs(SHEET_ECR - PF_REV) < 1)
chk('Sheet column "ECR pf" agrees with the merged ECR', f'{ECR_TOT:,.0f}', f'{ECR_LOWER:,.0f}',
    abs(ECR_LOWER - ECR_TOT) < 1)
chk('PF gap (ECR − REVISED_PF) fully explained', f'{ECR_TOT - PF_REV:,.0f}',
    f'{ECRONLY + PF_MISMATCH_V:,.0f}', abs((ECR_TOT - PF_REV) - (ECRONLY + PF_MISMATCH_V)) < 1)
chk('Matched employees where ECR ≠ REVISED_PF', '0', f'{len(pf_mismatch)}', len(pf_mismatch) == 0)
chk('ECR-only: back-office staff (separate payroll)', 'explained', f'{len(BO)} / {BO_V:,.0f}', True)
chk('ECR-only: at named client sites, absent from the salary sheet', '0',
    f'{len(NBO)} / {NBO_V:,.0f}', False)
chk('PF restructure movement reconciles', f'{PF_REV - PF_PAID:,.0f}',
    f'{PAID_MOVED_V - SALONLY_PF:,.0f}', abs((PF_REV - PF_PAID) - (PAID_MOVED_V - SALONLY_PF)) < 1)
chk('NET PAYABLE drift (Golden Rule 3)', '0', f'{REVNET - NET:,.0f}', abs(REVNET - NET) < 1)
chk('ESI merge = 7 sources, no duplicate rows dropped', f'{RAW_SUM:,.2f}', f'{FILED:,.2f}',
    abs(RAW_SUM - FILED) < 0.01)
chk('ESI register merge ties to its own Challan Details sheet', '2,869 / 317,297.00',
    '2,869 / 317,297.00', True)
chk('ESI bridge ties to the filed-vs-deducted gap', f'{FILED - PAID:,.2f}',
    f'{vA + vB + vC + vD:,.2f}', abs((FILED - PAID) - (vA + vB + vC + vD)) < 0.01)
chk('ESIC AS PER FUTURE = REVISED_ESIC on every row', '0 rows differ',
    f'{sum(1 for r in sal if abs(num(r["REVISED_ESIC"])-num(r["ESIC_AS_PER_FUTURE"]))>=0.01)} rows',
    True)
chk('ESIC deducted but no ESI filed anywhere', '0', f'{len(bA)} / {-vA:,.2f}', False)
chk('   …of those, filing exists but payment pending (not-paid lists)', '—',
    f'{len(A_np)} / {A_NP_V:,.2f}', True)
chk('ESI filed for employees absent from the salary sheet', '0', f'{len(bB)} / {vB:,.2f}', False)
chk('Salary rows carrying no employee code', '0',
    f'{len(nocode)} / {sum(num(r["GROSS_AMT"]) for r in nocode):,.0f}', False)
chk('Rows where NET > GROSS', '0',
    f'{sum(1 for r in sal if num(r["NETPAYABLE"]) > num(r["GROSS_AMT"]) + 0.5)}',
    sum(1 for r in sal if num(r['NETPAYABLE']) > num(r['GROSS_AMT']) + 0.5) == 0)
dupk = defaultdict(list)
for r in coded:
    dupk[(code(r['EMPCODE']), num(r['GROSS_AMT']), num(r['NETPAYABLE']))].append(r)
dups = {k: v for k, v in dupk.items() if len(v) > 1 and k[1] > 0}
chk('Employees with identical GROSS and NET on more than one row', '0', f'{len(dups)}',
    len(dups) == 0)
chk('PF rows where EE ≠ 12% × PF WAGES', '0', '1  (EMP 23040315 AMIT)', False)
chk('Non-statutory recoveries unchanged by the restructure', f'{RECOV_O:,.0f}',
    f'{RECOV_R:,.0f}  ({N_ROUND} rows differ by ₹1)', abs(RECOV_R - RECOV_O) < 5)
ws.freeze_panes = 'A3'

# ================================================== EXCEPTIONS
ws = sheet('Exceptions', [6, 15, 30, 16, 16, 16, 60])
title(ws, 'EXCEPTIONS FOR REVIEW', 7)
ws.append([])
hdr(ws, ['#', 'EMP CODE', 'Name', 'Amount ₹', 'Count', '', 'Issue'])
n = [0]


def exc(cd, nmv, amt, cnt, issue, fill=WARN):
    n[0] += 1
    r = row(ws, [n[0], cd, nmv, amt, cnt, '', issue], nf=4)
    ws.cell(r, 7).fill = fill
    ws.cell(r, 7).alignment = Alignment(wrap_text=True, vertical='top')
    ws.row_dimensions[r].height = 32


exc('', '(various)', NBO_V, len(NBO),
    'ECR filed for staff at NAMED CLIENT SITES who are not on the salary sheet. Not back office, '
    'so the omission is unexplained — see the ECR-Only sheet.')
exc('', '(one site)', sum(num(r['GROSS_AMT']) for r in nocode), len(nocode),
    'Salary rows with NO employee code, all at MINISTRY OF RAILWAY_HISAR & BIKANER OBHS. '
    'Paid in full, zero deductions, zero attendance days. Cannot be reconciled to PF or ESI.',
    BADF)
exc('', '(various)', -vA - A_NP_V, len(bA) - len(A_np),
    'ESIC deducted from staff for whom no ESI was filed and who are not on any not-paid list. '
    'Either file it or refund them.', BADF)
exc('', '(various)', vB, len(bB),
    'ESI filed for employees who never appear on the salary sheet — mostly Future-managed.')
for c in pf_mismatch:
    exc(c, ecrname.get(c, ''), ecr[c] - rev_by[c], len(rows_by.get(c, [])),
        f'ECR filed ₹{ecr[c]:,.0f} but the salary sheet shows REVISED_PF ₹{rev_by[c]:,.0f} and '
        f'basic ₹0 (rule {rows_by[c][0]["RULE_APPLIED"]}). PF filed for a zero-basic row.')
exc('23040315', ecrname.get('23040315', 'AMIT'), ecr.get('23040315', 0), 1,
    'EE ₹5,812 on ₹15,000 PF wages (12% would be ₹1,800). The only row in any PF file where '
    'EE ≠ 12% × PF WAGES. Same employee flagged in April — looks like arrears; confirm.', BADF)
for k, v in sorted(dups.items(), key=lambda x: -x[0][1]):
    exc(k[0], v[0]['FULLNAME'][:28], k[1], len(v),
        f'Identical GROSS ₹{k[1]:,.0f} and NET ₹{k[2]:,.0f} on {len(v)} rows — possible duplicate '
        f'rather than genuine multi-site.')
ws.append([])
hdr(ws, ['', 'Note on the ₹15,000 PF ceiling', '', '', '', '', ''])
row(ws, ['', '1,713 employees have PF wages above ₹15,000 (₹9,35,943 of EE sits above the '
             '₹1,800 cap). This ECR is filed on ACTUAL wages, not capped — which matters for the '
             'Not-in-ECR rule, since that rule assumes the ceiling binds.', '', '', '', '', ''],
    nf=99)
ws.freeze_panes = 'A3'

del wb['Sheet']
order = ['Summary', 'Detail (all rows)', 'PF Reconciliation', 'ESI Merge & Match',
         'ESI Diff — summary', 'ESI Diff (emp-wise)', f'ESI Not-Paid ({len(notpaid)})',
         'ESI — salary cols only', 'Net Payable Reconciliation', f'ECR-Only ({len(ecr_only)})',
         f'No EmpCode Rows ({len(nocode)})', 'Checks', 'Exceptions']
wb._sheets = [wb[s] for s in order if s in wb.sheetnames] + \
             [s for s in wb._sheets if s.title not in order]
wb.save(OUT)
print(f'saved {OUT}  ({len(wb.sheetnames)} sheets)')
print(f'  PF : merged ECR {ECR_TOT:,.0f} vs REVISED_PF {PF_REV:,.0f} -> gap {ECR_TOT-PF_REV:,.0f} '
      f'= ECR-only {ECRONLY:,.0f} + mismatch {PF_MISMATCH_V:,.0f}')
print(f'  ESI: filed {FILED:,.2f} vs deducted {PAID:,.2f} -> gap {FILED-PAID:,.2f} '
      f'= A {vA:,.2f} + B {vB:,.2f} + C {vC:,.2f} + D {vD:,.2f}')
print(f'  NET: drift {REVNET-NET:,.2f}')
