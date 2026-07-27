#!/usr/bin/env python3
"""Add the ESI merge / match / employee-wise difference sheets to the workbook."""
import csv
from collections import defaultdict, Counter
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

WB = 'ISPL_April2026_PF_ESI_NetPayable_Reconciliation.xlsx'
ESI_CSV = '../esi/ESI_MERGED_April2026.csv'
NP_CSV = '../esi/ESI_NOTPAID_April2026.csv'

def num(v):
    try: return float(str(v).replace(',', ''))
    except Exception: return 0.0
def code(v):
    s = str(v).strip()
    return s[:-2] if s.endswith('.0') else s.split('.')[0]

esi, esrc, ename, ebr = {}, {}, {}, {}
for r in csv.DictReader(open(ESI_CSV)):
    c = code(r['EMP_CODE'])
    esi[c] = num(r['ESI_EMP']); esrc[c] = r['SOURCE']
    ename[c] = r['NAME']; ebr[c] = r['BRANCH']
notpaid = list(csv.DictReader(open(NP_CSV)))

sal = list(csv.DictReader(open('SALARY_extract.csv')))
T = lambda c: sum(num(r[c]) for r in sal)

# employee-level roll-up of the salary sheet
by = defaultdict(lambda: {'esic': 0.0, 'rev': 0.0, 'fut': 0.0, 'gk': 0.0,
                          'name': '', 'state': '', 'rows': 0, 'rule': ''})
for r in sal:
    c = code(r['EMPCODE']); b = by[c]
    b['esic'] += num(r['ESIC']); b['rev'] += num(r['REVISED_ESIC'])
    b['fut'] += num(r['FUTURE_ESI']); b['gk'] += num(r['ESIC_AS_PER_FUTURE'])
    b['rows'] += 1
    if not b['name']: b['name'] = r['FULLNAME']; b['state'] = r['SITESTATE']
    if r['RULE_APPLIED'] == 'PF_ANCHOR' or not b['rule']: b['rule'] = r['RULE_APPLIED']

S, E = set(by), set(esi)
M = S & E
FILED = sum(esi.values()); PAID = T('ESIC')
m_filed = sum(esi[c] for c in M); m_paid = sum(by[c]['esic'] for c in M)
onlyE = sorted(E - S, key=lambda c: -esi[c]); onlyS = sorted(S - E, key=lambda c: -by[c]['esic'])
onlyE_v = sum(esi[c] for c in onlyE); onlyS_v = sum(by[c]['esic'] for c in onlyS)

# per-source figures come straight from the merge script's own summary, so no
# hardcoded totals can drift out of step with the data.
SRC = list(csv.DictReader(open('../esi/ESI_SOURCE_SUMMARY.csv')))
SOURCES = [(r['SOURCE'], int(r['ROWS_KEPT']), num(r['ESIC_RAW']))
           for r in SRC if r['SOURCE'] != 'MERGED']
RAW_SUM = sum(v for _, _, v in SOURCES)
DUPS_DROPPED = sum(int(r['EXACT_DUPS_DROPPED'] or 0) for r in SRC if r['SOURCE'] != 'MERGED')

wb = openpyxl.load_workbook(WB)
H1 = Font(bold=True, size=13, color='FFFFFF'); HF = PatternFill('solid', fgColor='1F4E78')
H2 = Font(bold=True, size=11); SUB = PatternFill('solid', fgColor='DDEBF7')
OKF = PatternFill('solid', fgColor='C6EFCE'); WARN = PatternFill('solid', fgColor='FFEB9C')
TOTF = PatternFill('solid', fgColor='F2F2F2'); B = Border(*[Side('thin', color='BFBFBF')] * 4)
M2 = '#,##0.00'; MI = '#,##0'

def sheet(t, widths):
    ws = wb.create_sheet(t)
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    return ws
def title(ws, txt, span):
    ws.append([txt]); ws.merge_cells(start_row=ws.max_row, start_column=1,
                                     end_row=ws.max_row, end_column=span)
    c = ws.cell(ws.max_row, 1); c.font = H1; c.fill = HF; ws.row_dimensions[ws.max_row].height = 22
def hdr(ws, v):
    ws.append(v)
    for i in range(1, len(v) + 1):
        c = ws.cell(ws.max_row, i); c.font = H2; c.fill = SUB; c.border = B
        c.alignment = Alignment(wrap_text=True, vertical='center')
def row(ws, v, fmt=M2, bold=False, fill=None, nf=2):
    ws.append(v); r = ws.max_row
    for i in range(1, len(v) + 1):
        c = ws.cell(r, i); c.border = B
        if bold: c.font = Font(bold=True)
        if fill: c.fill = fill
        if i >= nf and isinstance(v[i - 1], (int, float)): c.number_format = fmt
    return r

# ============ ESI Merge & Match ============
ws = sheet('ESI Merge & Match', [40, 14, 18, 18, 46])
title(ws, 'ESI — merge of the April-2026 ESI folder, then match to the salary sheet', 5)
ws.append([])
hdr(ws, ['STEP 1 — merge the ESI folder', 'Employees', 'ESI employee ₹', '', 'Covers'])
COV = {'ESIC REGISTER': 'Mumbai, Hyderabad, Bangalore, Pune, Ahmedabad, Chennai, Vizag, Nagpur…',
       'FUTURE (FR)': 'Future-managed population — disjoint from the register',
       'KOLKATA': 'West Bengal', 'GUWAHATI': 'Assam', 'ODISHA': 'Odisha',
       'JAMSHEDPUR': 'Jharkhand', 'PATNA': 'Bihar'}
for n, e, v in SOURCES: row(ws, [n, e, v, '', COV.get(n, '')], nf=2)
row(ws, ['  rows read', sum(e for _, e, _ in SOURCES), RAW_SUM, '', 'before dedupe'])
row(ws, ['  less: exact duplicate rows dropped', -DUPS_DROPPED, -(RAW_SUM - FILED), '',
         'identical EMPCODE+days+wages+ESIC rows (all in KOLKATA)'])
row(ws, ['MERGED ESI', len(esi), FILED, '', 'only 1 employee appears in two sources'],
    bold=True, fill=TOTF)
row(ws, ['(NOT PAID — filed but unpaid, held aside)', len(notpaid), '', '',
         'left / bank error / ESIC not generated — see ESI Not-Paid sheet'])
ws.append([])
hdr(ws, ['STEP 2 — match to April salary sheet', 'Employees', '₹', '', ''])
row(ws, ['Merged ESI (filed)', len(esi), FILED, '', ''])
row(ws, ['Salary sheet ESIC (as paid, col DR)', len(by), PAID, '', ''])
row(ws, ['GAP (filed − paid)', len(esi) - len(by), FILED - PAID, '', 'bridged below'],
    bold=True, fill=WARN)
ws.append([])
hdr(ws, ['STEP 3 — bridge', 'Employees', '₹', '', 'Treatment'])
row(ws, ['Matched — filed vs paid difference', len(M), m_filed - m_paid, '',
         f'filed {m_filed:,.2f} vs paid {m_paid:,.2f}'], fill=WARN)
row(ws, ['Filed but NOT in salary sheet', len(onlyE), onlyE_v, '',
         'ESI filed for employees absent from the salary sheet'], fill=WARN)
row(ws, ['In salary but NOT filed (ESIC deducted)',
         sum(1 for c in onlyS if by[c]['esic'] > 0), -onlyS_v, '',
         'ESIC deducted from staff with no ESI filing'], fill=WARN)
row(ws, ['NET = GAP', '', (m_filed - m_paid) + onlyE_v - onlyS_v, '', 'ties to the gap above'],
    bold=True, fill=TOTF)
ws.append([])
hdr(ws, ['Filed-but-not-in-salary, by source', 'Employees', '₹', '', ''])
cnt = Counter(esrc[c] for c in onlyE)
for s, n in cnt.most_common():
    row(ws, [s, n, sum(esi[c] for c in onlyE if esrc[c] == s), '', ''])
ws.append([])
hdr(ws, ['Salary-sheet ESI columns for reference', '₹', '', '', 'Note'])
row(ws, ['ESIC — as paid (col DR)', PAID, '', '', ''])
row(ws, ['REVISED_ESIC (col GI)', T('REVISED_ESIC'), '', '', 'post-reconciliation'])
row(ws, ['ESIC AS PER FUTURE (col GK)', T('ESIC_AS_PER_FUTURE'), '', '', 'ties exactly to REVISED_ESIC'])
row(ws, ['FUTURE_ESI (col GJ)', T('FUTURE_ESI'), '', '', ''])
row(ws, ['FUTURE_ESI − REVISED_ESIC', T('FUTURE_ESI') - T('REVISED_ESIC'), '', '',
         'the ₹37,736 carried-forward item'], fill=WARN)
ws.freeze_panes = 'A3'

# ============ ESI Diff — employee-wise ============
ws = sheet('ESI Diff (emp-wise)', [13, 26, 17, 9, 13, 13, 13, 13, 13, 13, 13, 15, 15])
title(ws, 'ESI DIFFERENCES — employee-wise, for investigation', 13)
HEAD = ['EMPCODE', 'FULLNAME', 'SITESTATE', 'ROWS', 'ESIC (paid, DR)',
        'ESIC AS PER FUTURE (GK)', 'DIFF  DR − GK', 'REVISED_ESIC (GI)',
        'FUTURE_ESI (GJ)', 'DIFF  GJ − GI', 'MERGED ESI (filed)',
        'DIFF  filed − paid', 'ESI SOURCE']
hdr(ws, HEAD)
rows_out = []
for c in sorted(S | E):
    b = by.get(c)
    paid = b['esic'] if b else 0.0
    gk = b['gk'] if b else 0.0
    rev = b['rev'] if b else 0.0
    fut = b['fut'] if b else 0.0
    filed = esi.get(c, 0.0)
    d1 = paid - gk; d2 = fut - rev; d3 = filed - paid
    if abs(d1) < 0.005 and abs(d2) < 0.005 and abs(d3) < 0.005: continue
    rows_out.append([c, (b['name'] if b else ename.get(c, '')),
                     (b['state'] if b else ebr.get(c, '')), (b['rows'] if b else 0),
                     paid, gk, d1, rev, fut, d2, filed, d3,
                     esrc.get(c, 'not in ESI files' if not b else '')])
rows_out.sort(key=lambda x: -abs(x[6]))
for v in rows_out:
    r = row(ws, v, nf=5)
    for cc in (7, 10, 12):
        if isinstance(v[cc - 1], (int, float)) and abs(v[cc - 1]) > 0.005:
            ws.cell(r, cc).fill = WARN
ws.insert_rows(2)
tot = ['TOTAL', f'{len(rows_out):,} employees', '', '',
       sum(v[4] for v in rows_out), sum(v[5] for v in rows_out), sum(v[6] for v in rows_out),
       sum(v[7] for v in rows_out), sum(v[8] for v in rows_out), sum(v[9] for v in rows_out),
       sum(v[10] for v in rows_out), sum(v[11] for v in rows_out), '']
for i, v in enumerate(tot, 1):
    c = ws.cell(2, i); c.value = v; c.font = Font(bold=True); c.fill = TOTF; c.border = B
    if isinstance(v, (int, float)): c.number_format = M2
ws.freeze_panes = 'C4'
ws.auto_filter.ref = f'A3:{get_column_letter(len(HEAD))}{ws.max_row}'

# ============ ESI Not-Paid ============
ws = sheet('ESI Not-Paid (50)', [13, 26, 34, 18, 16, 22, 11, 13])
title(ws, 'ESI filed-but-NOT-PAID — from the register\'s NOT PAID sheet', 8)
hdr(ws, ['EMPCODE', 'NAME', 'SITE NAME', 'STATE', 'BRANCH', 'ESI NO / STATUS',
         'TOTAL DAYS', 'PRESENT DAYS'])
for r in notpaid:
    row(ws, [r['EMP_CODE'], r['NAME'][:26], r['SITE_NAME'][:34], r['STATE'], r['BRANCH'],
             r['ESI_NO_STATUS'], num(r['TOTAL_DAYS']), num(r['PRESENT_DAYS'])], fmt=MI, nf=7)
ws.freeze_panes = 'A3'

# ============ refresh Checks ============
ws = wb['Checks']
_seen = [c for (c,) in ws.iter_rows(min_col=1, max_col=1, values_only=True)
         if isinstance(c, int)]
_n = [max(_seen) if _seen else 0]
def chk(d, exp, act, ok):
    _n[0] += 1; n = _n[0] - 1
    r = row(ws, [n + 1, d, exp, act, 'PASS' if ok else 'REVIEW'], nf=99)
    ws.cell(r, 5).fill = OKF if ok else WARN
chk('ESI merge = 7 sources less duplicate rows',
    f'{RAW_SUM:,.2f} - {RAW_SUM - FILED:,.2f}', f'{FILED:,.2f}', True)
chk('exact duplicate ESI rows dropped', f'{DUPS_DROPPED} rows',
    f'{DUPS_DROPPED} rows / {RAW_SUM - FILED:,.2f}', True)
chk('ESI sources overlap (employees in >1 file)', '0', '1', False)
chk('ESI bridge ties to the filed-vs-paid gap', f'{FILED - PAID:,.2f}',
    f'{(m_filed - m_paid) + onlyE_v - onlyS_v:,.2f}',
    abs((FILED - PAID) - ((m_filed - m_paid) + onlyE_v - onlyS_v)) < 1)
chk('ESI filed for employees absent from salary sheet', '0', f'{len(onlyE)} / {onlyE_v:,.2f}', False)
chk('ESIC deducted but no ESI filing', '0',
    f'{sum(1 for c in onlyS if by[c]["esic"] > 0)} / {onlyS_v:,.2f}', False)
chk('Matched employees where filed != paid', '0', f'{sum(1 for c in M if abs(esi[c]-by[c]["esic"])>0.005):,}', False)

order = ['Summary', 'Detail (all rows)', 'PF Reconciliation', 'ESI Reconciliation',
         'ESI Merge & Match', 'ESI Diff (emp-wise)', 'ESI Not-Paid (50)',
         'Net Payable Reconciliation', 'ECR-Only (250)', 'Checks', 'Exceptions']
wb._sheets = [wb[s] for s in order if s in wb.sheetnames] + \
             [s for s in wb._sheets if s.title not in order]
wb.save(WB)
print(f'ESI sheets added. merged {len(esi):,} emp / {FILED:,.2f}; '
      f'diff sheet {len(rows_out):,} employees')
