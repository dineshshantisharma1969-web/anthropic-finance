#!/usr/bin/env python3
"""
Merge the April-2026 ESI folder into a single per-employee sheet.

Sources (they cover DIFFERENT branches - there is no double counting):
  A. "ESIC REGISTER APRIL 2026.xlsx" sheet `ESIC`  -> Mumbai, Hyderabad, Bangalore,
     Pune, Ahmedabad, Chennai, Vishakhapatnam, Nagpur, Aurangabad, Dehradun, Indore
  B. the five regional .xls files                  -> Guwahati, Jamshedpur, Kolkata,
     Odisha, Patna
  C. sheet `NOT PAID` of the register              -> filed-but-unpaid, kept separate

NOTE vs the PF merge: the regional files legitimately carry the SAME EMPCODE on
several rows (a month split across day-blocks / sites). Those are SUMMED, not
deduped - deduping here would understate ESI. Exact duplicate rows are still
dropped.
"""
import csv, glob, os
import openpyxl, xlrd

def num(v):
    try: return float(str(v).replace(',', ''))
    except Exception: return 0.0

def scrub(v):
    """Collapse any embedded newline/tab so a record cannot split across lines."""
    return ' '.join(str(v or '').split())


def clean(v):
    if v is None: return ''
    s = str(v).strip()
    if s.endswith('.0'): s = s[:-2]
    return s.split('.')[0]

merged = {}   # empcode -> dict
report = []

def add(empcode, name, esi_no, days, wages, esic, site, branch, src):
    if not empcode: return
    m = merged.setdefault(empcode, {'name': name, 'esi_no': esi_no, 'days': 0.0,
                                    'wages': 0.0, 'esic': 0.0, 'site': site,
                                    'branch': branch, 'src': set(), 'rows': 0})
    m['days'] += days; m['wages'] += wages; m['esic'] += esic
    m['src'].add(src); m['rows'] += 1
    if not m['name']: m['name'] = name
    if not m['esi_no']: m['esi_no'] = esi_no

# ---------- A. ESIC REGISTER ----------
REG = glob.glob('ESIC REGISTER*.xlsx')[0]
# Month token for the output filenames, taken from the register's own name so the
# same script serves every month ("ESIC REGISTER MAY 2026.xlsx" -> "May2026").
_t = os.path.splitext(os.path.basename(REG))[0].upper().split()
TAG = _t[-2].capitalize() + _t[-1]
wb = openpyxl.load_workbook(REG, data_only=True, read_only=True)
ws = wb['ESIC']; rows = list(ws.iter_rows(values_only=True))
h = next(i for i, r in enumerate(rows[:8])
         if 'Employee Code' in [str(c).strip() if c else '' for c in r])
hdr = [str(c).strip() if c is not None else '' for c in rows[h]]
ix = {c: i for i, c in enumerate(hdr)}
seen = set(); n = 0; dup = 0
for r in rows[h+1:]:
    ec = clean(r[ix['Employee Code']])
    if not ec: continue
    key = (ec, num(r[ix['Total ESIC Wages']]), num(r[ix['ESI emp']]))
    if key in seen: dup += 1; continue
    seen.add(key)
    add(ec, str(r[ix['Employee Name']] or '').strip(), clean(r[ix['ESI No.']]),
        num(r[ix['Present Days']]), num(r[ix['Total ESIC Wages']]), num(r[ix['ESI emp']]),
        str(r[ix['Site Name']] or '').strip(), str(r[ix['BRANCH']] or '').strip(), 'REGISTER')
    n += 1
report.append(('ESIC REGISTER', n, dup, sum(num(r[ix['ESI emp']]) for r in rows[h+1:]
                                            if clean(r[ix['Employee Code']]))))
# NOT PAID kept aside
NPS = next(n for n in wb.sheetnames if n.upper().replace(' ', '') == 'NOTPAID')
ws = wb[NPS]; nprows = list(ws.iter_rows(values_only=True))
hn = next(i for i, r in enumerate(nprows[:8])
          if 'Employee Code' in [str(c).strip() if c else '' for c in r])
nhdr = [str(c).strip() if c is not None else '' for c in nprows[hn]]
nix = {c: i for i, c in enumerate(nhdr)}
notpaid = [r for r in nprows[hn+1:] if clean(r[nix['Employee Code']])]
wb.close()

# ---------- A2. Future reference sheet (FR) ----------
# Future is the ESI filing agent for a population the in-house register does not
# cover - the two sets overlap on a single employee, so FR is a third source, not
# a duplicate of the register.
FRF = glob.glob('Future reference*.xlsx')[0]
wb = openpyxl.load_workbook(FRF, data_only=True, read_only=True)
# April's workbook carries both 'FR_sheet' and 'FR_sheet (2)'; May's carries only
# 'FR_sheet (2)'. Prefer the plain sheet when present, else the (2) variant.
FRS = 'FR_sheet' if 'FR_sheet' in wb.sheetnames else \
      next(n for n in wb.sheetnames if n.upper().startswith('FR_SHEET'))
ws = wb[FRS]; frows = list(ws.iter_rows(values_only=True))
fh = next(i for i, r in enumerate(frows[:8])
          if 'EMPCODE' in [str(c).strip() if c else '' for c in r])
fhdr = [str(c).strip() if c is not None else '' for c in frows[fh]]
fix = {c: i for i, c in enumerate(fhdr)}
seen = set(); n = 0; dup = 0; tot = 0.0
for r in frows[fh+1:]:
    ec = clean(r[fix['EMPCODE']])
    if not ec: continue
    wg = num(r[fix['Final Gross']]); es = num(r[fix['ESIC']]); dy = num(r[fix['DAYS']])
    tot += es
    key = (ec, dy, wg, es)
    if key in seen: dup += 1; continue
    seen.add(key)
    add(ec, str(r[fix['FULLNAME']] or '').strip(), clean(r[fix['ESIC NO']]),
        dy, wg, es, str(r[fix['SITENAME']] or '').strip(),
        str(r[fix['BRANCHNAME']] or '').strip(), 'FUTURE')
    n += 1
report.append((f'FUTURE ({FRS})', n, dup, tot))
wb.close()

# ---------- B. regional .xls ----------
for f in sorted(glob.glob('*.xls')):
    tag = os.path.basename(f).split()[0].upper()
    b = xlrd.open_workbook(f); sh = b.sheet_by_index(0)
    hd = [str(sh.cell_value(0, j)).strip() for j in range(sh.ncols)]
    jx = {c: j for j, c in enumerate(hd)}
    seen = set(); n = 0; dup = 0; tot = 0.0
    for i in range(1, sh.nrows):
        ec = clean(sh.cell_value(i, jx['EMPCODE']))
        if not ec: continue
        wg = num(sh.cell_value(i, jx['ESI WAGES'])); es = num(sh.cell_value(i, jx['ESIC']))
        dy = num(sh.cell_value(i, jx['NORMALDAYS']))
        rowkey = (ec, dy, wg, es)
        tot += es
        if rowkey in seen: dup += 1; continue      # exact duplicate row
        seen.add(rowkey)
        add(ec, str(sh.cell_value(i, jx['FULLNAME'])).strip(),
            clean(sh.cell_value(i, jx['ESIC NO'])) if 'ESIC NO' in jx else '',
            dy, wg, es,
            str(sh.cell_value(i, jx['SITENAME'])).strip() if 'SITENAME' in jx else '',
            tag, tag)
        n += 1
    report.append((tag, n, dup, tot))

# ---------- output ----------
print('=' * 92)
print('ESI MERGE — per source')
print('=' * 92)
print(f"{'source':14}{'rows kept':>11}{'exact dups':>12}{'raw ESIC':>16}")
for t, n, d, tot in report:
    print(f'{t:14}{n:>11,}{d:>12,}{tot:>16,.2f}')
tot_esic = sum(v['esic'] for v in merged.values())
tot_wages = sum(v['wages'] for v in merged.values())
print('-' * 92)
print(f"{'MERGED':14}{len(merged):>11,}{'':>12}{tot_esic:>16,.2f}   wages {tot_wages:,.2f}")

overlap = {k: v for k, v in merged.items() if len(v['src']) > 1}
print(f'\nemployees appearing in >1 ESI source: {len(overlap)}')
for k, v in list(overlap.items())[:10]:
    print(f'   {k:>10} {v["name"][:24]:24} {sorted(v["src"])}  ESIC {v["esic"]:,.2f}')
multi = {k: v for k, v in merged.items() if v['rows'] > 1}
print(f'employees with >1 row summed (day-splits): {len(multi)}')

with open(f'ESI_MERGED_{TAG}.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['EMP_CODE','NAME','ESI_NO','DAYS','ESI_WAGES','ESI_EMP',
                'SITE_NAME','BRANCH','SOURCE','ROWS_SUMMED'])
    for k in sorted(merged):
        v = merged[k]
        w.writerow([k, scrub(v['name']), v['esi_no'], f"{v['days']:.0f}",
                    f"{v['wages']:.2f}", f"{v['esic']:.2f}", scrub(v['site']),
                    scrub(v['branch']), '+'.join(sorted(v['src'])), v['rows']])
print(f'\nwrote ESI_MERGED_{TAG}.csv  ({len(merged):,} employees, ESI emp {tot_esic:,.2f})')

with open(f'ESI_SOURCE_SUMMARY_{TAG}.csv', 'w') as f:
    f.write('SOURCE,ROWS_KEPT,EXACT_DUPS_DROPPED,ESIC_RAW\n')
    for t, n, d, tot in report:
        f.write(f'{t},{n},{d},{tot:.2f}\n')
    f.write(f'MERGED,{len(merged)},,{tot_esic:.2f}\n')
print(f'wrote ESI_SOURCE_SUMMARY_{TAG}.csv')

# The Future workbook carries its OWN "Not Paid" sheet. Missing it would leave
# those employees looking like "ESIC deducted but never filed", when in fact the
# filing exists and only the payment is outstanding.
notpaid_fr = []
wb = openpyxl.load_workbook(FRF, data_only=True, read_only=True)
FRNP = next((n for n in wb.sheetnames
             if n.upper().replace(' ', '').rstrip('.') == 'NOTPAID'), None)
if FRNP:
    nrows = list(wb[FRNP].iter_rows(values_only=True))
    nh = next(i for i, r in enumerate(nrows[:8])
              if 'EMPCODE' in [str(c).strip() if c else '' for c in r])
    nfhdr = [str(c).strip() if c is not None else '' for c in nrows[nh]]
    nfix = {c: i for i, c in enumerate(nfhdr)}
    notpaid_fr = [r for r in nrows[nh+1:] if clean(r[nfix['EMPCODE']])]
wb.close()

with open(f'ESI_NOTPAID_{TAG}.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['EMP_CODE','NAME','SITE_NAME','STATE','BRANCH','ESI_NO_STATUS',
                'TOTAL_DAYS','PRESENT_DAYS','ESIC','LIST'])
    for r in notpaid:
        g = lambda c: scrub(r[nix[c]]) if c in nix else ''
        w.writerow([clean(r[nix['Employee Code']]), g('Employee Name'), g('Site Name'),
                    g('STATE'), g('BRANCH'), g('ESI No.'), g('Total Days'),
                    g('Present Days'), '', 'REGISTER'])
    for r in notpaid_fr:
        g = lambda c: scrub(r[nfix[c]]) if c in nfix else ''
        w.writerow([clean(r[nfix['EMPCODE']]), g('FULLNAME'), g('SITENAME'),
                    g('STATE'), g('BRANCHNAME'), g('ESIC NO'), g('DAYS'),
                    g('DAYS'), f"{num(r[nfix['ESIC']]):.2f}", 'FUTURE'])
print(f'wrote ESI_NOTPAID_{TAG}.csv '
      f'({len(notpaid)} register + {len(notpaid_fr)} Future = '
      f'{len(notpaid)+len(notpaid_fr)} employees)')
