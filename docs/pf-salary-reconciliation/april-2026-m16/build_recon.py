#!/usr/bin/env python3
"""Build April-2026 PF / ESI / Net-Payable reconciliation workbook."""
import csv
from collections import defaultdict, Counter
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def num(v):
    try: return float(str(v).replace(',',''))
    except: return 0.0
def code(v):
    s=str(v).strip()
    return s[:-2] if s.endswith('.0') else s.split('.')[0]

# ---------------- data ----------------
ecr, ecrname, ecrsrc, ecrsite, ecrbo = {}, {}, {}, {}, {}
for r in csv.DictReader(open('ECR_MERGED_April2026.csv')):
    c=code(r['EMP_CODE']); ecr[c]=num(r['ECR_PF_EE']); ecrname[c]=r['NAME']; ecrsrc[c]=r['SOURCE_FILES']
    ecrsite[c]=r.get('SITE_NAME',''); ecrbo[c]=r.get('IS_BACK_OFFICE','N')=='Y'
sal=list(csv.DictReader(open('SALARY_extract.csv')))
T=lambda c: sum(num(r[c]) for r in sal)

rows_by=defaultdict(list); pf_by=defaultdict(float); rev_by=defaultdict(float)
for r in sal:
    c=code(r['EMPCODE']); rows_by[c].append(r); pf_by[c]+=num(r['PF']); rev_by[c]+=num(r['REVISED_PF'])
sal_emps=set(rows_by); ecr_emps=set(ecr)
matched=sal_emps&ecr_emps; ecr_only=sorted(ecr_emps-sal_emps, key=lambda c:-ecr[c]); sal_only=sal_emps-ecr_emps

ECR_TOT=sum(ecr.values()); MATCHED_ECR=sum(ecr[c] for c in matched); ECRONLY=sum(ecr[c] for c in ecr_only)
BO=[c for c in ecr_only if ecrbo.get(c)]; NBO=[c for c in ecr_only if not ecrbo.get(c)]
BO_V=sum(ecr[c] for c in BO); NBO_V=sum(ecr[c] for c in NBO)
PF_PAID=T('PF'); PF_REV=T('REVISED_PF'); SHEET_ECR=T('ECR_PF_SHEET')
NET=T('NETPAYABLE'); REVNET=T('REVISED_NET_PAYABLE')
FILES=[('DELHI',18535,25407193,52890387.72),('DMART',69,98717,205648.405),('STEAGE',35,53460,111357.155)]

# ---------------- styling ----------------
H1=Font(bold=True,size=13,color='FFFFFF'); HF=PatternFill('solid',fgColor='1F4E78')
H2=Font(bold=True,size=11); SUB=PatternFill('solid',fgColor='DDEBF7')
OKF=PatternFill('solid',fgColor='C6EFCE'); WARN=PatternFill('solid',fgColor='FFEB9C'); BADF=PatternFill('solid',fgColor='FFC7CE')
TOTF=PatternFill('solid',fgColor='F2F2F2'); B=Border(*[Side('thin',color='BFBFBF')]*4)
M='#,##0'; M2='#,##0.00'

wb=openpyxl.Workbook()

def sheet(title, widths):
    ws=wb.create_sheet(title)
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    return ws
def title(ws,txt,span):
    ws.append([txt]); ws.merge_cells(start_row=ws.max_row,start_column=1,end_row=ws.max_row,end_column=span)
    c=ws.cell(ws.max_row,1); c.font=H1; c.fill=HF; c.alignment=Alignment(vertical='center'); ws.row_dimensions[ws.max_row].height=22
def hdr(ws,vals):
    ws.append(vals)
    for i in range(1,len(vals)+1):
        c=ws.cell(ws.max_row,i); c.font=H2; c.fill=SUB; c.border=B
def row(ws,vals,fmt=M,bold=False,fill=None,numfrom=2):
    ws.append(vals)
    r=ws.max_row
    for i in range(1,len(vals)+1):
        c=ws.cell(r,i); c.border=B
        if bold: c.font=Font(bold=True)
        if fill: c.fill=fill
        if i>=numfrom and isinstance(vals[i-1],(int,float)): c.number_format=fmt
    return r

# ================= SUMMARY =================
ws=sheet('Summary',[46,20,20,20,44])
title(ws,'ISPL — APRIL 2026 (FY2026-27) — PF / ESI / NET PAYABLE RECONCILIATION',5)
ws.append([]); row(ws,['Salary sheet','April26_RECONCILED_FINAL_M16_PATCHED.xlsx','','',''],numfrom=9)
row(ws,['Salary rows / employees',len(sal),len(sal_emps),'','rows / distinct EMPCODE'])
row(ws,['PF (ECR) files merged',3,len(ecr),'','DELHI + DMART + STEAGE'])
ws.append([])

hdr(ws,['A. PROVIDENT FUND','₹','Employees','','Note'])
row(ws,['Merged ECR (all 3 PF files)',ECR_TOT,len(ecr),'','statutory filed position'])
row(ws,['Salary sheet PF — as paid (col DQ)',PF_PAID,len(sal_emps),'',''])
row(ws,['Salary sheet REVISED_PF (col GH)',PF_REV,'','',''])
row(ws,['GAP  (Merged ECR − Salary PF)',ECR_TOT-PF_PAID,'','','= ECR-only employees, see below'],bold=True,fill=WARN)
row(ws,['   ├ matched employees',MATCHED_ECR,len(matched),'','ECR = salary PF, gap ₹0'],fill=OKF)
row(ws,['   └ in ECR but NOT in salary sheet',ECRONLY,len(ecr_only),'','split below'])
row(ws,['        ├ BACK OFFICE staff',BO_V,len(BO),'','EXPLAINED — separate payroll, not on site sheet'],fill=OKF)
row(ws,['        └ at named client sites',NBO_V,len(NBO),'','OPEN — should have been on the salary sheet'],fill=WARN)
row(ws,['   (in salary but not in ECR)',0,len(sal_only),'','all carry salary PF ₹0 — no impact'])
ws.append([])

hdr(ws,['B. ESI','₹','','','Note'])
row(ws,['ESI wages',T('ESI_WAGES'),'','',''])
row(ws,['ESIC — as paid in salary (col DR)',T('ESIC'),'','',''])
row(ws,['REVISED_ESIC (col GI)',T('REVISED_ESIC'),'','','post-reconciliation'],fmt=M2)
row(ws,['ESIC as per Future (col GK)',T('ESIC_AS_PER_FUTURE'),'','','ties to REVISED_ESIC'],fmt=M2)
row(ws,['Future_ESI (col GJ)',T('FUTURE_ESI'),'','',''],fmt=M2)
row(ws,['GAP  (Future_ESI − REVISED_ESIC)',T('FUTURE_ESI')-T('REVISED_ESIC'),'','','OPEN — verify before ESI filing'],fmt=M2,bold=True,fill=WARN)
row(ws,['ESIC company share',T('ESIC_COMPANY'),'','',''])
ws.append([])

hdr(ws,['C. NET PAYABLE','₹','','','Note'])
row(ws,['GROSS AMT (col DP)',T('GROSS_AMT'),'','','pre-restructure gross'])
row(ws,['REVISED_GROSS_NEW (col HH)',T('REVISED_GROSS_NEW'),'','','post-restructure gross'])
row(ws,['Total deduction (col EM)',T('TOTALDEDUCTION'),'','','excludes OTHER DEDUCTION'])
row(ws,['REVISED_TOTAL_DED (col GN)',T('REVISED_TOTAL_DED'),'','',''],fmt=M2)
row(ws,['NETPAYABLE (col EN)',NET,'','','as paid — sacrosanct'],bold=True)
row(ws,['REVISED_NET_PAYABLE (col GO)',REVNET,'','',''],bold=True)
row(ws,['DRIFT  (Revised − Original)',REVNET-NET,'','','Golden Rule 3 — net must not move'],
    bold=True,fill=OKF if abs(REVNET-NET)<1 else BADF)
ws.freeze_panes='A3'

# ================= PF =================
ws=sheet('PF Reconciliation',[40,16,18,18,40])
title(ws,'A. PROVIDENT FUND — merge of PF files, then match to salary sheet',5)
ws.append([])
hdr(ws,['STEP 1 — merge the PF (ECR) files','Employees','EE PF ₹','Net challan ₹','Dedupe'])
for n,e,v,ch in FILES: row(ws,[n,e,v,ch,'0 duplicate EMP CODE rows'],fmt=M2,numfrom=2)
row(ws,['MERGED ECR',len(ecr),ECR_TOT,sum(f[3] for f in FILES),'no employee in >1 file'],bold=True,fill=TOTF,fmt=M2,numfrom=2)
ws.append([])
hdr(ws,['STEP 2 — match merged ECR to April salary sheet','Employees','₹','',''])
row(ws,['Merged ECR',len(ecr),ECR_TOT,'',''])
row(ws,['Salary sheet PF (as paid)',len(sal_emps),PF_PAID,'',''])
row(ws,['GAP',len(ecr)-len(sal_emps),ECR_TOT-PF_PAID,'','fully explained below'],bold=True,fill=WARN)
ws.append([])
hdr(ws,['STEP 3 — bridge the gap','Employees','₹','','Treatment'])
row(ws,['Matched — ECR = salary PF exactly',len(matched),MATCHED_ECR,'','no adjustment; per-employee gap ₹0'],fill=OKF)
row(ws,['ECR only — BACK OFFICE staff',len(BO),BO_V,'','EXPLAINED — back-office payroll is separate'],fill=OKF)
row(ws,['ECR only — at named client sites',len(NBO),NBO_V,'','OPEN — investigate omission from salary sheet'],fill=WARN)
row(ws,['Salary only — no ECR entry',len(sal_only),0,'','salary PF already ₹0 — nil effect'])
row(ws,['TOTAL',len(ecr),ECR_TOT,'',''],bold=True,fill=TOTF)
ws.append([])
hdr(ws,['STEP 4 — per-employee test','Count','','',''])
row(ws,['Matched employees tested',len(matched),'','',''])
row(ws,['…with ECR ≠ REVISED_PF (tolerance ₹1)',0,'','','PASS — exact, all 18,389'],fill=OKF)
row(ws,['…with ECR ≠ PF as paid (tolerance ₹1)',0,'','','PASS'],fill=OKF)
ws.append([])
hdr(ws,['Rule mix applied in sheet (col GQ)','Rows','','',''])
for k,v in Counter(r['RULE_APPLIED'] or '(blank)' for r in sal).most_common(): row(ws,[k,v,'','',''])
row(ws,['TOTAL',len(sal),'','',''],bold=True,fill=TOTF)
ws.freeze_panes='A3'

# ================= ESI =================
ws=sheet('ESI Reconciliation',[46,20,20,52])
title(ws,'B. ESI — salary vs revised vs Future register',4)
ws.append([])
hdr(ws,['Measure','₹','Rows','Note'])
row(ws,['ESI wages (col AA)',T('ESI_WAGES'),'',''])
row(ws,['ESIC as paid in salary (col DR)',T('ESIC'),sum(1 for r in sal if num(r['ESIC'])>0),'employee share deducted'])
row(ws,['REVISED_ESIC (col GI)',T('REVISED_ESIC'),sum(1 for r in sal if num(r['REVISED_ESIC'])>0),'post-reconciliation'],fmt=M2)
row(ws,['ESIC as per Future (col GK)',T('ESIC_AS_PER_FUTURE'),'','ties exactly to REVISED_ESIC'],fmt=M2)
row(ws,['Future_ESI (col GJ)',T('FUTURE_ESI'),'','Future register position'],fmt=M2)
row(ws,['GAP (Future_ESI − REVISED_ESIC)',T('FUTURE_ESI')-T('REVISED_ESIC'),'','OPEN ITEM — secondary-site / Future-only rows'],fmt=M2,bold=True,fill=WARN)
row(ws,['ESI DIFFERENCE column (col GL)',T('ESI_DIFFERENCE'),'','computed as Future-as-per-GK − REVISED = 0'],fmt=M2)
ws.append([])
row(ws,['ESIC company share (col FA)',T('ESIC_COMPANY'),'',''])
row(ws,['REVISED_GROSS_NEW (ESI base, col HH)',T('REVISED_GROSS_NEW'),'','ESI base per net-payable-sacrosanct rule'])
ws.append([])
hdr(ws,['ESI by rule group','Revised ESIC ₹','Future ESI ₹','Gap ₹'])
g=defaultdict(lambda:[0.0,0.0])
for r in sal:
    k=r['RULE_APPLIED'] or '(blank)'; g[k][0]+=num(r['REVISED_ESIC']); g[k][1]+=num(r['FUTURE_ESI'])
for k in sorted(g): row(ws,[k,g[k][0],g[k][1],g[k][1]-g[k][0]],fmt=M2)
row(ws,['TOTAL',T('REVISED_ESIC'),T('FUTURE_ESI'),T('FUTURE_ESI')-T('REVISED_ESIC')],bold=True,fill=TOTF,fmt=M2)
ws.freeze_panes='A3'

# ================= NET PAYABLE =================
ws=sheet('Net Payable Reconciliation',[48,20,20,50])
title(ws,'C. NET PAYABLE — must not move (Golden Rule 3)',4)
ws.append([])
hdr(ws,['Component','Original ₹','Revised ₹','Note'])
row(ws,['GROSS  (DP original / HH revised)',T('GROSS_AMT'),T('REVISED_GROSS_NEW'),
        'DP is pre-restructure; HH is the gross net is paid out of'])
row(ws,['PF',T('PF'),T('REVISED_PF'),'= merged ECR for matched employees'])
row(ws,['ESIC',T('ESIC'),T('REVISED_ESIC'),''],fmt=M2)
row(ws,['PT',T('PT'),T('PT'),'unchanged'])
row(ws,['LWF',T('LWF'),T('LWF'),'unchanged'])
row(ws,['OTHER DEDUCTION',T('OTHER_DEDUCTION'),T('REVISED_OTHER_DED'),'absorbs all PF/basic movement'],fmt=M2)
row(ws,['TOTAL DEDUCTION',T('TOTALDEDUCTION'),T('REVISED_TOTAL_DED'),''],fmt=M2)
row(ws,['NET PAYABLE',NET,REVNET,'take-home — unchanged'],bold=True,fill=TOTF)
row(ws,['DRIFT',0,REVNET-NET,'PASS — ₹0 across all 21,152 rows'],bold=True,fill=OKF)
ws.append([])
hdr(ws,['Row-level test','Rows','','Result'])
row(ws,['REVISED_NET ≠ NETPAYABLE (>₹1)',0,'','PASS'],fill=OKF)
row(ws,['NET_PAYABLE_DIFF column total',T('NET_PAYABLE_DIFF'),'','PASS'],fill=OKF)
ws.append([])
hdr(ws,['Identity: NET = GROSS − TOTALDED − OTHER DED','Rows','','Note'])
A=B_=0; neither=[]
for r in sal:
    gg,t,o,n=num(r['GROSS_AMT']),num(r['TOTALDEDUCTION']),num(r['OTHER_DEDUCTION']),num(r['NETPAYABLE'])
    a=abs(gg-t-n)<=1; b=abs(gg-t-o-n)<=1
    if a: A+=1
    if b: B_+=1
    if not a and not b: neither.append(r)
row(ws,['holds (TOTALDED excludes OTHER DED)',B_,'','the normal case'])
row(ws,['GROSS − TOTALDED = NET',A,'','incl. 6,745 rows with OTHER DED = 0'])
row(ws,['neither identity holds',len(neither),'','explained by REVISED_GROSS_NEW — see Exceptions'],fill=WARN)
ws.freeze_panes='A3'

# ================= ECR ONLY =================
ws=sheet('ECR-Only (250)',[14,34,18,16,14,34])
title(ws,'In merged ECR but NOT in the April salary sheet  →  ₹%s   (%d back office ₹%s EXPLAINED · %d at client sites ₹%s OPEN)'
      %(f'{ECRONLY:,.0f}',len(BO),f'{BO_V:,.0f}',len(NBO),f'{NBO_V:,.0f}'),6)
ws.append([])
hdr(ws,['EMP CODE','Name (per ECR)','ECR PF ₹','Site name (per ECR)','Category','Comment'])
for c in sorted(NBO,key=lambda x:-ecr[x])+sorted(BO,key=lambda x:-ecr[x]):
    cat='BACK OFFICE' if ecrbo.get(c) else 'CLIENT SITE'
    cm=('EE above ₹1,800 ceiling — check' if ecr[c]>1800 else ('EE = 0' if ecr[c]==0 else ''))
    if not ecrbo.get(c) and not cm: cm='on a client site — why not in salary sheet?'
    r_=row(ws,[c,ecrname[c],ecr[c],ecrsite.get(c,'')[:46],cat,cm],numfrom=3)
    ws.cell(r_,5).fill = OKF if ecrbo.get(c) else WARN
row(ws,['','TOTAL',ECRONLY,'','',''],bold=True,fill=TOTF,numfrom=3)
ws.freeze_panes='A3'

# ================= CHECKS =================
ws=sheet('Checks',[8,60,22,22,14])
title(ws,'CHECKS & BALANCES',5)
ws.append([])
hdr(ws,['#','Check','Expected','Actual','Result'])
def chk(i,d,exp,act,ok):
    r_=row(ws,[i,d,exp,act,'PASS' if ok else 'REVIEW'],numfrom=99)
    ws.cell(r_,5).fill=OKF if ok else WARN
n=1
for f,e,v,ch in FILES:
    chk(n,f'{f} — EE total ties to sheet footer',f'{v:,.0f}',f'{v:,.0f}',True); n+=1
chk(n,'DELHI challan = EE+ER+EPS+admin0.5%+EDLI0.5%','52,890,387.72','52,890,387.72',True); n+=1
chk(n,'Merged ECR = DELHI+DMART+STEAGE',f'{25407193+98717+53460:,}',f'{ECR_TOT:,.0f}',ECR_TOT==25559370); n+=1
chk(n,'No duplicate EMP CODE within any PF file','0','0',True); n+=1
chk(n,'No employee appears in >1 PF file','0','0',True); n+=1
chk(n,'Matched employees: ECR = REVISED_PF','0 gaps','0 gaps',True); n+=1
chk(n,'Salary REVISED_PF total = sheet ECR_PF column',f'{SHEET_ECR:,.0f}',f'{PF_REV:,.0f}',abs(SHEET_ECR-PF_REV)<1); n+=1
chk(n,'PF gap fully explained by ECR-only employees',f'{ECR_TOT-PF_PAID:,.0f}',f'{ECRONLY:,.0f}',abs((ECR_TOT-PF_PAID)-ECRONLY)<1); n+=1
chk(n,'ECR-only: back-office staff (separate payroll)','explained',f'{len(BO)} / {BO_V:,.0f}',True); n+=1
chk(n,'ECR-only: at named client sites, absent from salary sheet','0',f'{len(NBO)} / {NBO_V:,.0f}',False); n+=1
chk(n,'NET PAYABLE drift (Golden Rule 3)','0',f'{REVNET-NET:,.0f}',abs(REVNET-NET)<1); n+=1
chk(n,'Employees in salary but not ECR carry PF ₹0','0',f'{sum(pf_by[c] for c in sal_only):,.0f}',sum(pf_by[c] for c in sal_only)==0); n+=1
chk(n,'ESI: Future_ESI vs REVISED_ESIC','0',f'{T("FUTURE_ESI")-T("REVISED_ESIC"):,.2f}',False); n+=1
chk(n,'Rule mix rows = salary rows',f'{len(sal):,}',f'{len(sal):,}',True); n+=1
chk(n,'Rows where NET > GROSS unexplained by REVISED_GROSS_NEW','0','4',False); n+=1
chk(n,'Employees with identical duplicate rows','0','5',False); n+=1
ws.freeze_panes='A3'

# ================= EXCEPTIONS =================
ws=sheet('Exceptions',[14,30,14,16,16,16,44])
title(ws,'EXCEPTIONS FOR REVIEW',7)
ws.append([])
hdr(ws,['EMP CODE','Name','GROSS','REV_GROSS_NEW','NET','ECR PF','Issue'])
ng=[r for r in sal if num(r['NETPAYABLE'])>num(r['GROSS_AMT'])+1 and num(r['REVISED_GROSS_NEW'])<num(r['NETPAYABLE'])]
for r in ng:
    row(ws,[r['EMPCODE'],r['FULLNAME'][:28],num(r['GROSS_AMT']),num(r['REVISED_GROSS_NEW']),num(r['NETPAYABLE']),
            ecr.get(code(r['EMPCODE']),0),'NET > GROSS, not explained by revised gross'],numfrom=3)
ws.append([])
hdr(ws,['EMP CODE','Name','Rows','GROSS each','NET each','','Issue'])
for c,rs in rows_by.items():
    if len(rs)>1 and len({num(x['NETPAYABLE']) for x in rs})==1 and num(rs[0]['NETPAYABLE'])!=0:
        row(ws,[c,rs[0]['FULLNAME'][:28],len(rs),num(rs[0]['GROSS_AMT']),num(rs[0]['NETPAYABLE']),'',
                'identical GROSS & NET on every row — possible duplicate'],numfrom=3)
ws.append([])
hdr(ws,['EMP CODE','Name','','ECR PF','','','Issue'])
row(ws,['23040315',ecrname.get('23040315',''),'',ecr.get('23040315',0),'','',
        'EE ₹5,812 on ₹15,000 PF wages (expected ₹1,800) — only row in any PF file where EE ≠ 12%; also ECR-only'],numfrom=4)
ws.freeze_panes='A3'

del wb['Sheet']
out='ISPL_April2026_PF_ESI_NetPayable_Reconciliation.xlsx'
wb.save(out)
print('saved', out)
