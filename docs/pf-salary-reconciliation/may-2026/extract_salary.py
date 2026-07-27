#!/usr/bin/env python3
"""Lift the reconciliation columns out of the 218-column May-2026 salary sheet.

Two things this must get right, both learned the hard way:
  * the header is on line 5, and lines after the last employee carry the
    sheet's own TOTAL row -- read those as data and every total doubles;
  * 137 rows carry a name, a gross and a net but NO employee code. They are
    real money in the sheet's footer, so they are kept (flagged HAS_EMPCODE=N)
    rather than silently dropped -- otherwise the extract understates gross
    and net by Rs 4,18,888 each and no total ties to the source.
"""
import csv

SRC, OUT = 'SALARY_May26.csv', 'SALARY_extract.csv'
HEADER_LINE = 4           # 0-based

COLS = [
    ('SITESTATE','SITESTATE'), ('SITENAME','SITENAME'), ('EMPCODE','EMPCODE'),
    ('FULLNAME','FULLNAME'), ('PF_WAGES','PF WAGES'), ('ESI_WAGES','ESI WAGES'),
    ('NORMALDAYS','NORMALDAYS'), ('FIXED_BASIC','FIXED_BASIC'), ('FIXED_DA','FIXED_DA'),
    ('BASIC','BASIC'), ('DA','DA'), ('GROSS_AMT','GROSS AMT'), ('PF','PF'), ('ESIC','ESIC'),
    ('PT','PT'), ('LWF','LWF'), ('OTHER_DEDUCTION','OTHER DEDUCTION'),
    ('TOTALDEDUCTION','TOTALDEDUCTION'), ('NETPAYABLE','NETPAYABLE'),
    ('PF_COMPANY','PF COMPANY'), ('ESIC_COMPANY','ESIC COMPANY'),
    ('PF_NO','PF NO'), ('UAN_NO','UAN NO'), ('SITEDIVISIONDAYS','SITEDIVISIONDAYS'),
    ('ECR_pf_lower','ECR pf'), ('ECR_PF_SHEET','ECR_PF'),
    ('REVISED_BASIC','REVISED_BASIC'), ('REVISED_DA','REVISED_DA'),
    ('REVISED_GROSS','REVISED_GROSS'), ('REVISED_PF','REVISED_PF'),
    ('REVISED_OTHER_DED','REVISED_OTHER_DEDUCTION'),
    ('REVISED_TOTAL_DED','REVISED_TOTAL_DED'), ('REVISED_NET_PAYABLE','REVISED_NET_PAYABLE'),
    ('RULE_APPLIED','RULE_APPLIED'), ('REVISED_ESIC','REVISED_ESIC'),
    ('ESIC_AS_PER_FUTURE','ESIC AS PER FUTURE'), ('REVISED_GROSS_NEW','REVISED_GROSS_NEW'),
    ('RECON_FLAG_M13','RECON_FLAG_M13'),
]

def scrub(v):
    return ' '.join(str(v or '').split())

rows = list(csv.reader(open(SRC)))
hdr = [c.strip() for c in rows[HEADER_LINE]]
ix = {c: i for i, c in enumerate(hdr)}
for _, src in COLS:
    if src not in ix:
        raise SystemExit(f'missing source column {src!r}')

# A data row must carry a name; the TOTAL footer has figures but no name.
data = [r for r in rows[HEADER_LINE + 1:]
        if len(r) > ix['FULLNAME'] and scrub(r[ix['FULLNAME']])]

with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow([o for o, _ in COLS] + ['HAS_EMPCODE'])
    for r in data:
        g = lambda s: scrub(r[ix[s]]) if len(r) > ix[s] else ''
        w.writerow([g(s) for _, s in COLS] + ['Y' if g('EMPCODE') else 'N'])
print(f'wrote {OUT}: {len(data):,} rows, {len(COLS)+1} cols')
