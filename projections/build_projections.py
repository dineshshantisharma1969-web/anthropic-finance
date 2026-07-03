#!/usr/bin/env python3
"""Build FY 2026-27 projected financials for Impressions Services Pvt Ltd.

Base: BS _TB _2025-26 CONSOLIDATED_set2.xlsx (FY 2025-26 audited working set).
Method: Revenue +10%; variable costs scale proportionately; prudence overrides:
  - Other income held flat (not grown)
  - Inventory change taken as NIL (no stock gain assumed)
  - Full current tax provided at 25.168% (s.115BAA), no prior-year credits
  - No dividend assumed; entire PAT retained
  - Borrowings held at FY26 level (no fresh leverage assumed to fund growth)
  - Gratuity/provisions grown with employee cost
"""
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

G = 0.10          # sales growth
TAXR = 0.25168    # 22% + 10% surcharge + 4% cess (s.115BAA)

# ---- FY 2025-26 base figures (INR) from 'pl' and 'BS' sheets ----
pl = dict(
    rev=4898238075.54, oi=9993615.65,
    pur=129055957.47, invchg=26225.00, emp=4143800770.32,
    fin=34403667.00, dep=26150367.00, oth=433672461.96,
)
bs = dict(
    sc=200000.00, rs=1458115248.22, interunit=15721313.81,
    ltb=89963690.64, ltp=94505792.00,
    stb=348135361.67, tp_msme=0.00, tp_oth=72303716.07,
    ocl=495509114.47, stp=20273486.75,
    ppe=186880905.31, intang=0.00, cwip=0.00,
    invsts=157195317.00, dta=29044756.00, ltla=86514244.74,
    inv=4636862.00, tr=1665625897.28, cash=48082440.00,
    stla=393603021.00, oca=23144280.66,
)

wb = openpyxl.Workbook()

# styles
H1 = Font(bold=True, size=13); H2 = Font(bold=True, size=11)
B = Font(bold=True); IT = Font(italic=True, size=9, color="555555")
thin = Side(style='thin', color="999999")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
top = Border(top=thin); topbot = Border(top=thin, bottom=Side(style='double'))
hdrfill = PatternFill('solid', fgColor="D9E2F3")
subfill = PatternFill('solid', fgColor="F2F2F2")
NUM = '#,##0;(#,##0)'
PCT = '0.0%'
CR = '#,##0.00,,,"  Cr";(#,##0.00,,,"  Cr")'

def sheet_header(ws, title, cols=6):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=cols)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=cols)
    ws.cell(1, 1, 'IMPRESSIONS SERVICES PRIVATE LIMITED').font = H1
    ws.cell(2, 1, title).font = H2
    ws.cell(3, 1, 'CIN: U74930DL2002PTC114966   |   Base: BS_TB 2025-26 CONSOLIDATED Set 2   |   Amount in INR').font = IT
    for r in (1, 2, 3):
        ws.cell(r, 1).alignment = Alignment(horizontal='center')

# ============ 1. ASSUMPTIONS ============
ws = wb.active; ws.title = 'Assumptions'
sheet_header(ws, 'PROJECTIONS FY 2026-27 — KEY ASSUMPTIONS', 4)
rows = [
    ('Driver / Item', 'Basis', 'Value'),
    ('Revenue from operations', 'Growth over FY 2025-26', G),
    ('Purchases of stock-in-trade', 'Proportionate to sales (+10%)', G),
    ('Employee benefits expense', 'Proportionate to sales (+10%) — manpower-linked business', G),
    ('Finance cost', 'Grown +10% (prudence: working capital rises with sales)', G),
    ('Depreciation', 'Grown +10% (maintenance capex assumed ≈ depreciation)', G),
    ('Other expenses', 'Proportionate to sales (+10%)', G),
    ('Other income', 'PRUDENCE: held flat at FY26 level — not grown', 0.0),
    ('Change in inventories', 'PRUDENCE: taken as NIL — no stock gain assumed', None),
    ('Current tax', 'PRUDENCE: full provision @ 25.168% (s.115BAA); no prior-year tax credits assumed', TAXR),
    ('Dividend', 'PRUDENCE: nil — entire PAT retained in reserves', None),
    ('Trade receivables / inventories / ST loans & adv / other CA', 'Scale with sales (+10%) — same collection cycle assumed', G),
    ('Trade payables / other current liabilities / ST provisions', 'Scale with sales (+10%)', G),
    ('Long-term provisions (gratuity)', 'Scale with employee cost (+10%)', G),
    ('Long & short-term borrowings', 'PRUDENCE: held at FY26 level — growth funded internally', 0.0),
    ('Share capital / investments / DTA / LT loans & advances / interunit', 'Held constant', 0.0),
    ('Property, plant & equipment (net)', 'Held flat — capex assumed equal to depreciation', 0.0),
    ('Cash & cash equivalents', 'Balancing figure', None),
]
r = 5
for i, row in enumerate(rows):
    for c, v in enumerate(row, 1):
        cell = ws.cell(r, c, v)
        cell.border = box
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        if i == 0:
            cell.font = B; cell.fill = hdrfill
        if c == 3 and isinstance(v, float):
            cell.number_format = PCT
    r += 1
ws.cell(5, 2).value = 'Basis'
gr_row = 6  # revenue growth cell C6 referenced by other sheets
ws.column_dimensions['A'].width = 42
ws.column_dimensions['B'].width = 62
ws.column_dimensions['C'].width = 10
ws.cell(r + 1, 1, 'Note: Change the growth rate in cell C6 — the projected P&L and Balance Sheet recalculate automatically.').font = IT

GROW = "(1+Assumptions!$C$6)"

# ============ 2. PROJECTED P&L ============
ws = wb.create_sheet('Projected P&L FY27')
sheet_header(ws, 'PROJECTED STATEMENT OF PROFIT AND LOSS FOR THE YEAR ENDING MARCH 31, 2027')
hdr = ['', 'Particulars', 'FY 2025-26 (Base)', 'FY 2026-27 (Projected)', 'Change', 'Basis']
for c, v in enumerate(hdr, 1):
    cell = ws.cell(5, c, v); cell.font = B; cell.fill = hdrfill; cell.border = box
    cell.alignment = Alignment(horizontal='center', wrap_text=True)

def prow(r, num, label, base, formula, basis, bold=False, fill=False):
    ws.cell(r, 1, num)
    ws.cell(r, 2, label)
    if base is not None:
        ws.cell(r, 3, base).number_format = NUM
    if formula is not None:
        ws.cell(r, 4, formula).number_format = NUM
    if base and formula:
        ws.cell(r, 5, f'=IFERROR(D{r}/C{r}-1,"")').number_format = PCT
    ws.cell(r, 6, basis).font = IT
    for c in range(1, 7):
        ws.cell(r, c).border = box
        if bold: ws.cell(r, c).font = Font(bold=True, italic=(c == 6))
        if fill: ws.cell(r, c).fill = subfill
    ws.cell(r, 2).alignment = Alignment(wrap_text=True)
    ws.cell(r, 6).alignment = Alignment(wrap_text=True)

r = 6
prow(r, 'I', 'Revenue from Operations', pl['rev'], f'=C{r}*{GROW}', 'Sales +10%'); rev_r = r; r += 1
prow(r, 'II', 'Other income', pl['oi'], f'=C{r}', 'Held flat — prudence'); r += 1
prow(r, 'III', 'Total Income (I+II)', pl['rev'] + pl['oi'], f'=SUM(D{r-2}:D{r-1})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{r-2}:C{r-1})'; ti_r = r; r += 1
prow(r, 'IV', 'Expenses:', None, None, ''); r += 1
prow(r, '', 'Purchases of Stock-in-Trade', pl['pur'], f'=C{r}*{GROW}', 'Proportionate +10%'); e1 = r; r += 1
prow(r, '', 'Changes in inventories of finished goods, WIP and stock-in-trade', pl['invchg'], 0, 'Taken as NIL — prudence'); r += 1
prow(r, '', 'Employee benefits expense', pl['emp'], f'=C{r}*{GROW}', 'Proportionate +10%'); r += 1
prow(r, '', 'Finance cost', pl['fin'], f'=C{r}*{GROW}', '+10% — prudence'); r += 1
prow(r, '', 'Depreciation and amortization expense', pl['dep'], f'=C{r}*{GROW}', '+10% — prudence'); r += 1
prow(r, '', 'Other expenses', pl['oth'], f'=C{r}*{GROW}', 'Proportionate +10%'); e2 = r; r += 1
prow(r, '', 'Total expenses', None, f'=SUM(D{e1}:D{e2})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{e1}:C{e2})'; ws.cell(r, 3).number_format = NUM
ws.cell(r, 5).value = f'=D{r}/C{r}-1'; ws.cell(r, 5).number_format = PCT; te_r = r; r += 1
prow(r, 'V', 'Profit Before Tax (III-IV)', None, f'=D{ti_r}-D{te_r}', '', bold=True)
ws.cell(r, 3).value = f'=C{ti_r}-C{te_r}'; ws.cell(r, 3).number_format = NUM
ws.cell(r, 5).value = f'=D{r}/C{r}-1'; ws.cell(r, 5).number_format = PCT; pbt_r = r; r += 1
prow(r, 'VI', 'Tax expense — current tax @ 25.168%', -29662103.00, f'=ROUND(D{pbt_r}*Assumptions!$C$14,0)',
     'Full provision, s.115BAA; FY26 had prior-year tax reversal (credit) — not assumed to recur'); tax_r = r; r += 1
prow(r, 'VII', 'Profit After Tax (V-VI)', 170784345.44, f'=D{pbt_r}-D{tax_r}', 'Retained in full — no dividend', bold=True, fill=True)
ws.cell(r, 5).value = f'=D{r}/C{r}-1'; ws.cell(r, 5).number_format = PCT; pat_r = r; r += 1
r += 1
prow(r, '', 'PBT margin', None, f'=D{pbt_r}/D{rev_r}', '')
ws.cell(r, 3).value = f'=C{pbt_r}/C{rev_r}'
for c in (3, 4): ws.cell(r, c).number_format = PCT
r += 1
prow(r, '', 'PAT margin', None, f'=D{pat_r}/D{rev_r}', '')
ws.cell(r, 3).value = f'=C{pat_r}/C{rev_r}'
for c in (3, 4): ws.cell(r, c).number_format = PCT

ws.column_dimensions['A'].width = 5
ws.column_dimensions['B'].width = 48
for col in 'CD': ws.column_dimensions[col].width = 20
ws.column_dimensions['E'].width = 9
ws.column_dimensions['F'].width = 42
PL = ws.title

# ============ 3. PROJECTED BALANCE SHEET ============
ws = wb.create_sheet('Projected BS FY27')
sheet_header(ws, 'PROJECTED BALANCE SHEET AS AT MARCH 31, 2027')
for c, v in enumerate(hdr, 1):
    cell = ws.cell(5, c, v); cell.font = B; cell.fill = hdrfill; cell.border = box
    cell.alignment = Alignment(horizontal='center', wrap_text=True)

def brow(r, num, label, base, formula, basis, bold=False, fill=False):
    ws.cell(r, 1, num); ws.cell(r, 2, label)
    if base is not None:
        ws.cell(r, 3, base).number_format = NUM
    if formula is not None:
        ws.cell(r, 4, formula).number_format = NUM
    if base is not None and formula is not None and base != 0:
        ws.cell(r, 5, f'=IFERROR(D{r}/C{r}-1,"")').number_format = PCT
    ws.cell(r, 6, basis).font = IT
    for c in range(1, 7):
        ws.cell(r, c).border = box
        if bold: ws.cell(r, c).font = Font(bold=True, italic=(c == 6))
        if fill: ws.cell(r, c).fill = subfill
    ws.cell(r, 2).alignment = Alignment(wrap_text=True)
    ws.cell(r, 6).alignment = Alignment(wrap_text=True)

r = 6
brow(r, 'I.', 'EQUITY AND LIABILITIES', None, None, '', bold=True); r += 1
brow(r, '(1)', 'Shareholders’ Funds', None, None, ''); r += 1
brow(r, '(a)', 'Share capital', bs['sc'], f'=C{r}', 'Constant'); sf1 = r; r += 1
brow(r, '(b)', 'Reserves and Surplus', bs['rs'], f"=C{r}+'{PL}'!D{pat_r}", 'Opening + projected PAT (nil dividend)'); r += 1
brow(r, '', 'Interunit', bs['interunit'], f'=C{r}', 'Held constant'); sf2 = r; r += 1
brow(r, '', 'Sub-total — Shareholders’ funds', None, f'=SUM(D{sf1}:D{sf2})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{sf1}:C{sf2})'; ws.cell(r, 3).number_format = NUM; r += 1
brow(r, '(2)', 'Non-current liabilities', None, None, ''); r += 1
brow(r, '(a)', 'Long-term borrowings', bs['ltb'], f'=C{r}', 'Held at FY26 level — prudence'); ncl1 = r; r += 1
brow(r, '(b)', 'Long-term provisions (gratuity)', bs['ltp'], f'=C{r}*{GROW}', 'Grows with employee cost +10%'); ncl2 = r; r += 1
brow(r, '', 'Sub-total — Non-current liabilities', None, f'=SUM(D{ncl1}:D{ncl2})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{ncl1}:C{ncl2})'; ws.cell(r, 3).number_format = NUM; r += 1
brow(r, '(3)', 'Current liabilities', None, None, ''); r += 1
brow(r, '(a)', 'Short-term borrowings', bs['stb'], f'=C{r}', 'Held at FY26 level — prudence'); cl1 = r; r += 1
brow(r, '(b)', 'Trade payables — MSME', bs['tp_msme'], 0, ''); r += 1
brow(r, '', 'Trade payables — others', bs['tp_oth'], f'=C{r}*{GROW}', 'Scales with sales +10%'); r += 1
brow(r, '(c)', 'Other current liabilities', bs['ocl'], f'=C{r}*{GROW}', 'Scales with sales +10%'); r += 1
brow(r, '(d)', 'Short-term provisions', bs['stp'], f'=C{r}*{GROW}', 'Scales with sales +10%'); cl2 = r; r += 1
brow(r, '', 'Sub-total — Current liabilities', None, f'=SUM(D{cl1}:D{cl2})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{cl1}:C{cl2})'; ws.cell(r, 3).number_format = NUM; clt = r; r += 1
brow(r, '', 'TOTAL — EQUITY AND LIABILITIES', None, f'=D{sf2+1}+D{ncl2+1}+D{clt}', '', bold=True)
ws.cell(r, 3).value = f'=C{sf2+1}+C{ncl2+1}+C{clt}'; ws.cell(r, 3).number_format = NUM
for c in range(1, 7): ws.cell(r, c).border = topbot
tot_liab = r; r += 2

brow(r, 'II.', 'ASSETS', None, None, '', bold=True); r += 1
brow(r, '(1)', 'Non-current assets', None, None, ''); r += 1
brow(r, '(a)', 'Property, plant & equipment (net)', bs['ppe'], f'=C{r}', 'Capex ≈ depreciation, net block flat'); nca1 = r; r += 1
brow(r, '(b)', 'Non-current investments', bs['invsts'], f'=C{r}', 'Held constant'); r += 1
brow(r, '(c)', 'Deferred tax assets (net)', bs['dta'], f'=C{r}', 'Held constant — prudence (no further DTA built up)'); r += 1
brow(r, '(d)', 'Long-term loans and advances', bs['ltla'], f'=C{r}', 'Held constant'); nca2 = r; r += 1
brow(r, '', 'Sub-total — Non-current assets', None, f'=SUM(D{nca1}:D{nca2})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{nca1}:C{nca2})'; ws.cell(r, 3).number_format = NUM; r += 1
brow(r, '(2)', 'Current assets', None, None, ''); r += 1
brow(r, '(a)', 'Inventories', bs['inv'], f'=C{r}*{GROW}', 'Scales with sales +10%'); ca1 = r; r += 1
brow(r, '(b)', 'Trade receivables', bs['tr'], f'=C{r}*{GROW}', 'Scales with sales +10% (same collection cycle)'); r += 1
brow(r, '(c)', 'Short-term loans and advances', bs['stla'], f'=C{r}*{GROW}', 'Scales with sales +10%'); r += 1
brow(r, '(d)', 'Other current assets', bs['oca'], f'=C{r}*{GROW}', 'Scales with sales +10%'); r += 1
brow(r, '(e)', 'Cash and cash equivalents', bs['cash'], None, 'Balancing figure'); cash_r = r; ca2 = r; r += 1
brow(r, '', 'Sub-total — Current assets', None, f'=SUM(D{ca1}:D{ca2})', '', bold=True, fill=True)
ws.cell(r, 3).value = f'=SUM(C{ca1}:C{ca2})'; ws.cell(r, 3).number_format = NUM; cat = r; r += 1
brow(r, '', 'TOTAL — ASSETS', None, f'=D{nca2+1}+D{cat}', '', bold=True)
ws.cell(r, 3).value = f'=C{nca2+1}+C{cat}'; ws.cell(r, 3).number_format = NUM
for c in range(1, 7): ws.cell(r, c).border = topbot
tot_asset = r
# cash = total liabilities - all other assets
ws.cell(cash_r, 4).value = (f'=D{tot_liab}-SUM(D{nca1}:D{nca2})-SUM(D{ca1}:D{ca2-1})')
ws.cell(cash_r, 4).number_format = NUM
ws.cell(cash_r, 5).value = f'=D{cash_r}/C{cash_r}-1'; ws.cell(cash_r, 5).number_format = PCT
r += 2
ws.cell(r, 2, 'Check: Total assets less total equity & liabilities')
ws.cell(r, 4, f'=D{tot_asset}-D{tot_liab}').number_format = NUM
ws.cell(r, 2).font = IT; ws.cell(r, 4).font = IT

ws.column_dimensions['A'].width = 5
ws.column_dimensions['B'].width = 48
for col in 'CD': ws.column_dimensions[col].width = 20
ws.column_dimensions['E'].width = 9
ws.column_dimensions['F'].width = 42
BS_ = ws.title

# ============ 4. SUMMARY (Rs Crore) & RATIOS ============
ws = wb.create_sheet('Summary & Ratios')
sheet_header(ws, 'PROJECTION SUMMARY — FY 2026-27 vs FY 2025-26 (₹ Crore)', 4)
for c, v in enumerate(['Metric', 'FY 2025-26', 'FY 2026-27 (Proj)', 'Change'], 1):
    cell = ws.cell(5, c, v); cell.font = B; cell.fill = hdrfill; cell.border = box
r = 6
def srow(r, label, f26, f27, pct=True, ratio=False):
    ws.cell(r, 1, label)
    ws.cell(r, 2, f26); ws.cell(r, 3, f27)
    fmt = '0.00' if ratio else '#,##0.00,,,'
    ws.cell(r, 2).number_format = fmt; ws.cell(r, 3).number_format = fmt
    if pct:
        ws.cell(r, 4, f'=IFERROR(C{r}/B{r}-1,"")').number_format = PCT
    else:
        ws.cell(r, 4, f'=C{r}-B{r}').number_format = '0.00'
    for c in range(1, 5): ws.cell(r, c).border = box

srow(r, 'Revenue from operations', f"='{PL}'!C{rev_r}", f"='{PL}'!D{rev_r}"); r += 1
srow(r, 'Total expenses', f"='{PL}'!C{te_r}", f"='{PL}'!D{te_r}"); r += 1
srow(r, 'Profit before tax', f"='{PL}'!C{pbt_r}", f"='{PL}'!D{pbt_r}"); r += 1
srow(r, 'Profit after tax', f"='{PL}'!C{pat_r}", f"='{PL}'!D{pat_r}"); r += 1
srow(r, 'Net worth (incl. interunit)', f"='{BS_}'!C{sf2+1}", f"='{BS_}'!D{sf2+1}"); r += 1
srow(r, 'Total borrowings (LT+ST)', f"='{BS_}'!C{ncl1}+'{BS_}'!C{cl1}", f"='{BS_}'!D{ncl1}+'{BS_}'!D{cl1}"); r += 1
srow(r, 'Trade receivables', f"='{BS_}'!C{ca1+1}", f"='{BS_}'!D{ca1+1}"); r += 1
srow(r, 'Cash & cash equivalents', f"='{BS_}'!C{cash_r}", f"='{BS_}'!D{cash_r}"); r += 1
srow(r, 'Balance sheet total', f"='{BS_}'!C{tot_asset}", f"='{BS_}'!D{tot_asset}"); r += 1
srow(r, 'Working capital (CA − CL)', f"='{BS_}'!C{cat}-'{BS_}'!C{clt}", f"='{BS_}'!D{cat}-'{BS_}'!D{clt}"); r += 2

ws.cell(r, 1, 'Key ratios').font = H2; r += 1
srow(r, 'PBT margin %', f"='{PL}'!C{pbt_r}/'{PL}'!C{rev_r}*100", f"='{PL}'!D{pbt_r}/'{PL}'!D{rev_r}*100", pct=False, ratio=True); r += 1
srow(r, 'PAT margin %', f"='{PL}'!C{pat_r}/'{PL}'!C{rev_r}*100", f"='{PL}'!D{pat_r}/'{PL}'!D{rev_r}*100", pct=False, ratio=True); r += 1
srow(r, 'Current ratio (x)', f"='{BS_}'!C{cat}/'{BS_}'!C{clt}", f"='{BS_}'!D{cat}/'{BS_}'!D{clt}", pct=False, ratio=True); r += 1
srow(r, 'Debt / equity (x)', f"=('{BS_}'!C{ncl1}+'{BS_}'!C{cl1})/'{BS_}'!C{sf2+1}",
     f"=('{BS_}'!D{ncl1}+'{BS_}'!D{cl1})/'{BS_}'!D{sf2+1}", pct=False, ratio=True); r += 1
srow(r, 'Debtor days (on closing TR)', f"='{BS_}'!C{ca1+1}/'{PL}'!C{rev_r}*365",
     f"='{BS_}'!D{ca1+1}/'{PL}'!D{rev_r}*365", pct=False, ratio=True); r += 1
srow(r, 'Return on net worth %', f"='{PL}'!C{pat_r}/'{BS_}'!C{sf2+1}*100", f"='{PL}'!D{pat_r}/'{BS_}'!D{sf2+1}*100", pct=False, ratio=True); r += 2

notes = [
    'Prudence notes:',
    '1. Other income NOT grown — held at FY 2025-26 level.',
    '2. FY 2025-26 PAT (₹17.08 Cr) includes a prior-year current-tax reversal of ₹2.97 Cr; the projection assumes NO such credit and provides full tax at 25.168%, so projected PAT growth appears muted vs the reported base.',
    '3. Inventory change taken as nil; no stock-appreciation gain assumed.',
    '4. Borrowings held at FY26 levels — incremental working capital is funded from internal accruals; cash is the balancing figure.',
    '5. Entire PAT retained; no dividend assumed.',
    '6. Gratuity (long-term provision) grown in line with employee cost.',
]
for n in notes:
    ws.cell(r, 1, n).font = IT if not n.endswith(':') else B
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    ws.cell(r, 1).alignment = Alignment(wrap_text=True)
    ws.row_dimensions[r].height = 26 if len(n) > 80 else 14
    r += 1

ws.column_dimensions['A'].width = 34
for col in 'BC': ws.column_dimensions[col].width = 17
ws.column_dimensions['D'].width = 10

out = 'PROJECTIONS_FY2026-27_BS_PL_set2.xlsx'
wb.save(out)
print('saved', out)
