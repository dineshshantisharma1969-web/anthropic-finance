#!/usr/bin/env python3
# Faithful local port of the n8n "Run Checks" logic + report assembly.
import sys, os, re, math
import pandas as pd

def norm(s):
    return re.sub(r'[^A-Z0-9]', '', str(s).upper())

def num(v):
    if v is None: return 0.0
    if isinstance(v, (int, float)):
        return 0.0 if (isinstance(v, float) and math.isnan(v)) else float(v)
    s = str(v).strip()
    if s == '' or s.lower() == 'nan': return 0.0
    s = s.replace(',', '')
    try: return float(s)
    except: return 0.0

DAYS = {'january':31,'february':28,'march':31,'april':30,'may':31,'june':30,
        'july':31,'august':31,'september':30,'october':31,'november':30,'december':31}

def run(path):
    fname = os.path.basename(path)
    stem = re.sub(r'\.[^.]+$', '', fname).strip()
    days = DAYS.get(stem.lower(), 31)
    month_label = stem or 'Month'

    xl = pd.ExcelFile(path)
    # pick first sheet (matches extractFromFile default behaviour on the data sheet)
    sheet = xl.sheet_names[0]
    df = xl.parse(sheet, header=0, dtype=object)
    rows = df.to_dict('records')

    keys = list(df.columns)
    lut = {}
    for k in keys: lut[norm(k)] = k
    def col(*cands):
        for x in cands:
            k = lut.get(norm(x))
            if k is not None: return k
        return None

    cBas=col('REVISED_BASIC'); cDa=col('REVISED_DA'); cPf=col('REVISED_PF')
    cEcr=col('ECR_PF','ECR PF'); cGr=col('REVISED_GROSS','REVISED_GROSS_NEW (final)')
    cEsi=col('REVISED_ESIC'); cFut=col('ESIC AS PER FUTURE','ESIC_AS_PER_FUTURE')
    cAdj=col('ADJ_WORKING_DAYS'); cGp=col('MONTHLY_GROSS_PROJECTION','PROJECTED_GROSS_FULL_MONTH')
    cEmp=col('EMPCODE','EMP CODE'); cName=col('FULLNAME','FULL NAME')
    cState=col('SITESTATE'); cSite=col('SITENAME')

    TOL=1; PF_CEIL=15000; ESI_CEIL=21000; CAP=1000
    SCHEMA_KEYS=['MONTH','CHECK','EMPCODE','FULLNAME','SITESTATE','SITENAME','REVISED_BASIC',
        'REVISED_DA','BASIC_PLUS_DA','REVISED_PF','EXPECTED_PF_12pct','ECR_PF','REVISED_GROSS',
        'REVISED_ESIC','EXPECTED_ESI_075pct','ESIC_AS_PER_FUTURE','ADJ_WORKING_DAYS',
        'FULL_MONTH_GROSS_PROJECTION','NOTE']
    def mk(**o):
        base={k:'' for k in SCHEMA_KEYS}; base['MONTH']=month_label; base.update(o); return base
    def idf(r):
        return dict(EMPCODE=r.get(cEmp,'') if cEmp else '', FULLNAME=r.get(cName,'') if cName else '',
                    SITESTATE=r.get(cState,'') if cState else '', SITENAME=r.get(cSite,'') if cSite else '')

    nPf=c1=nEcr=c2=nEsi=c3a=c3b=c4=c4b=0; maxProj=0.0
    f1=[];f2=[];f3a=[];f3b=[];f4=[]
    for r in rows:
        bas=num(r.get(cBas)); da=num(r.get(cDa)); pf=num(r.get(cPf)); ecr=num(r.get(cEcr))
        gr=num(r.get(cGr)); esi=num(r.get(cEsi)); adj=num(r.get(cAdj))
        bd=bas+da
        gp = num(r.get(cGp)) if cGp else (gr*days/adj if adj>0 else 0)
        if gp>maxProj: maxProj=gp
        if pf>0:
            nPf+=1; ex=round(0.12*bd,2)
            if abs(pf-ex)>TOL:
                c1+=1
                if len(f1)<CAP: f1.append(mk(**idf(r),CHECK='1_PF_not_12pct',REVISED_BASIC=bas,REVISED_DA=da,BASIC_PLUS_DA=bd,REVISED_PF=pf,EXPECTED_PF_12pct=ex,NOTE='PF off by '+str(round(pf-ex,2))))
        if ecr>0:
            nEcr+=1
            if bd>PF_CEIL+0.5:
                c2+=1
                if len(f2)<CAP: f2.append(mk(**idf(r),CHECK='2_ECR_BD_over_15000',REVISED_BASIC=bas,REVISED_DA=da,BASIC_PLUS_DA=bd,REVISED_PF=pf,ECR_PF=ecr,ADJ_WORKING_DAYS=adj,NOTE='Basic+DA above PF ceiling (exception)'))
        if esi>0:
            nEsi+=1; ee=round(0.0075*gr,2)
            if abs(esi-ee)>TOL:
                c3a+=1
                if len(f3a)<CAP: f3a.append(mk(**idf(r),CHECK='3a_ESI_not_075pct',REVISED_GROSS=gr,REVISED_ESIC=esi,EXPECTED_ESI_075pct=ee,ESIC_AS_PER_FUTURE=(num(r.get(cFut)) if cFut else ''),NOTE='ESI vs 0.75% (often relaxed to Future)'))
            if gr>ESI_CEIL+0.5:
                c3b+=1
                if len(f3b)<CAP: f3b.append(mk(**idf(r),CHECK='3b_ESI_gross_over_21000',REVISED_GROSS=gr,REVISED_ESIC=esi,NOTE='Gross above ESI ceiling (exception)'))
        if gp>50000:
            c4+=1
            if gp>100000: c4b+=1
            f4.append(mk(**idf(r),CHECK='4_gross_proj_too_high',REVISED_GROSS=gr,ADJ_WORKING_DAYS=adj,FULL_MONTH_GROSS_PROJECTION=round(gp),NOTE=('IMPLAUSIBLE' if gp>100000 else 'high')))
    f4.sort(key=lambda x: x['FULL_MONTH_GROSS_PROJECTION'], reverse=True)
    f4c=f4[:CAP]

    L=[]
    L.append("Month "+month_label+" | rows "+str(len(rows))+" | days "+str(days))
    L.append("Check1 PF<>12%(B+D): "+str(c1)+" of "+str(nPf)+" PF rows")
    L.append("Check2 ECR set & B+D>15000: "+str(c2)+" of "+str(nEcr)+" ECR rows (exceptions)")
    L.append("Check3a ESI<>0.75%gross: "+str(c3a)+" of "+str(nEsi)+" ESI rows")
    L.append("Check3b ESI set & gross>21000: "+str(c3b)+" (exceptions)")
    L.append("Check4 gross proj >50k: "+str(c4)+" (>100k: "+str(c4b)+", max Rs "+str(round(maxProj))+")")

    # management summary (mirrors the Write Summary agent's brief, factual style)
    summary = (
        f"Reconciliation summary for {month_label} ({len(rows)} employee rows, {days} days). "
        f"Check 1 (PF = 12% of Basic+DA): {c1} of {nPf} PF rows deviate beyond Rs 1 tolerance. "
        f"Check 2 (ECR filed but Basic+DA over the Rs 15,000 PF ceiling): {c2} of {nEcr} ECR rows are such exceptions (high earners). "
        f"Check 3a (ESI = 0.75% of gross): {c3a} of {nEsi} ESI rows mismatch, typically because ESI is aligned to the filed 'ESIC as per Future' figure. "
        f"Check 3b (ESI filed with gross over the Rs 21,000 ceiling): {c3b} exception rows. "
        f"Check 4 (full-month gross projection): {c4} rows exceed Rs 50,000 ({c4b} exceed Rs 100,000 and are implausible; max Rs {round(maxProj)}). "
        f"Figures are derived solely from the source sheet."
    )

    out=[]
    for ln in summary.split('\n'):
        if ln.strip(): out.append(mk(CHECK='AI_SUMMARY',NOTE=ln))
    out.append(mk(CHECK=''))
    out.append(mk(CHECK='OVERVIEW',NOTE='  ||  '.join(L)))
    for s in L: out.append(mk(CHECK='SUMMARY',NOTE=s))
    for arr in (f1,f2,f3a,f3b,f4c):
        out.extend(arr)

    rep = pd.DataFrame(out, columns=SCHEMA_KEYS)
    outpath = os.path.join(os.path.dirname(path) or '.', f"{month_label}_Audit_Report.xlsx")
    with pd.ExcelWriter(outpath, engine='openpyxl') as w:
        rep.to_excel(w, sheet_name='Audit', index=False)
    print("ROWS:", len(rows), "COLS:", len(keys))
    print("MATCHED COLUMNS:", dict(BASIC=cBas,DA=cDa,PF=cPf,ECR=cEcr,GROSS=cGr,ESIC=cEsi,FUTURE=cFut,ADJ=cAdj,GP=cGp,EMP=cEmp,NAME=cName,STATE=cState,SITE=cSite))
    for s in L: print("  ", s)
    print("REPORT:", outpath, "report_rows:", len(out))
    return outpath

if __name__ == '__main__':
    run(sys.argv[1])
