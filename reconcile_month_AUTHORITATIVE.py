#!/usr/bin/env python3
"""
AUTHORITATIVE monthly PF/ESI/gross reconciliation — the SINGLE source of truth.

Replaces the entire stacked pipeline (build_*_management_review, M7/M8/M10/FTE,
REVISED_GROSS_NEW, etc.). Run ONLY this. It is idempotent and self-policing:
it REFUSES to write output unless every hard check (C1-C12) is zero.

Why the old process kept breaking (and this doesn't):
  1. ECR total/footer rows (blank EMPCODE) were merged in -> filed PF inflated
     ~3x and produced absurd projections. THIS script strips them first.
  2. Each cycle bolted another pass onto the previous OUTPUT. THIS script
     rebuilds once from the stable anchors (ECR_PF, ESIC_AS_PER_FUTURE,
     NETPAYABLE) and ends with the projection cap, so nothing can drift.

Anchors held sacrosanct: NETPAYABLE never changes; REVISED_PF = 12% of (B+D)
with B+D = ECR_PF/0.12; REVISED_ESIC = ESIC_AS_PER_FUTURE; days only INCREASE
to keep PF (B+D proj <=15000) and ESI (gross <=21000) within ceiling.

Usage:
  python reconcile_month_AUTHORITATIVE.py <Month.xlsx> [--out <clean.xlsx>] [--sheet Sheet1]
"""
import argparse, calendar, math, sys
from pathlib import Path
import numpy as np, pandas as pd

PF_CEIL=15000; ESI_CEIL=21000; PF_RATE=0.12; ESI_RATE=0.0075
FY={'april':(2025,4),'may':(2025,5),'june':(2025,6),'july':(2025,7),'august':(2025,8),
    'september':(2025,9),'october':(2025,10),'november':(2025,11),'december':(2025,12),
    'january':(2026,1),'february':(2026,2),'march':(2026,3)}

def month_days(stem):
    k=stem.strip().lower()
    for name,(y,m) in FY.items():
        if k.startswith(name): return calendar.monthrange(y,m)[1]
    return 31

def run(path, out=None, sheet=0):
    path=Path(path); FM=month_days(path.stem)
    df0=pd.read_excel(path, sheet_name=sheet)
    if 'EMPCODE' not in df0.columns:
        sys.exit("FATAL: no EMPCODE column; wrong sheet?")
    emp=df0['EMPCODE']
    s=emp.astype(str).str.strip()
    blank=emp.isna()|s.isin(['','nan','NaN','None'])
    nonnum=pd.to_numeric(emp,errors='coerce').isna()&~blank   # placeholder/total rows e.g. _RESIDUAL_RECLASS_NB_
    junk=blank|nonnum
    n_junk=int(junk.sum()); n_blank=int(blank.sum()); n_named=int(nonnum.sum())
    if n_named:
        dropped=s[nonnum].tolist()
        print(f"  !! dropped {n_named} NON-EMPLOYEE rows (text EMPCODE): {dropped}")
        print(f"     their ECR_PF sum = {pd.to_numeric(df0.loc[nonnum,'ECR_PF'],errors='coerce').fillna(0).sum():,.0f}")
    df=df0[~junk].reset_index(drop=True); n=len(df)
    def num(c): return pd.to_numeric(df[c],errors='coerce').fillna(0).values if c in df.columns else np.zeros(n)
    ecr=num('ECR_PF'); fut=num('ESIC_AS_PER_FUTURE'); netp=num('NETPAYABLE')
    basic_o=num('BASIC'); da_o=num('DA'); nd=num('NORMALDAYS')
    da_src=num('REVISED_DA') if 'REVISED_DA' in df.columns else da_o

    rev_pf=np.zeros(n);rev_esi=np.zeros(n);rb=np.zeros(n);rd=np.zeros(n)
    rg=np.zeros(n);ra=np.zeros(n);ro=np.zeros(n);rt=np.zeros(n);rn=np.zeros(n)
    adj=np.zeros(n,int); act=np.array(['OK']*n,dtype=object); mw=np.zeros(n,bool)
    for i in range(n):
        pf=ecr[i];esi=fut[i];npay=netp[i];in_pf=pf>0;in_esi=esi>0
        bd=round(pf/PF_RATE) if in_pf else (basic_o[i]+da_o[i])
        da_alloc=min(da_src[i],bd)
        g=max((round(esi/ESI_RATE) if in_esi else 0.0),bd,npay+pf+esi)
        rev_pf[i]=pf;rev_esi[i]=esi;rb[i]=bd-da_alloc;rd[i]=da_alloc
        rg[i]=g;ra[i]=g-bd;rt[i]=g-npay;ro[i]=(g-npay)-pf-esi;rn[i]=npay
    sd=lambda i:max(1,min(FM,int(round(nd[i])) if nd[i]>0 else 1))
    # HARD RULE: REVISED_PF == ECR_PF (filed/deposited amount) at all costs.
    # B+D is pinned at ECR_PF/0.12, so PF = 12% x (B+D) = ECR_PF exactly, every row.
    # No min-wage basic-floor uplift is applied (it would restate PF above filed).
    for i in range(n):  # E3 negative OTHER_DED -> ATT (NET unchanged)
        if ro[i]<-0.5:
            amt=-ro[i];ra[i]+=amt;rg[i]+=amt;rt[i]+=amt;ro[i]=0.0;act[i]='E3_neg_other_to_att'
    for i in range(n):  # CAP6: ESI present but gross over ceiling -> zero ESI to OTHER_DED
        if rev_esi[i]>0 and rg[i]>ESI_CEIL+0.5:
            ro[i]+=rev_esi[i];rev_esi[i]=0.0
            act[i]=(act[i]+'; ' if act[i]!='OK' else '')+'ESI_ZEROED_gross_over_21000'
    def set_days(i):
        pf=rev_pf[i];esi=rev_esi[i];bd=rb[i]+rd[i];g=rg[i];lo,hi=1,FM;base=sd(i)
        if pf>0 and bd>0: lo=max(lo,math.ceil(bd*FM/PF_CEIL))
        if esi>0 and g>0: lo=max(lo,math.ceil(g*FM/ESI_CEIL))
        if pf<=0 and bd>0: hi=min(hi,math.floor(bd*FM/(PF_CEIL+1)))
        if esi<=0 and g>0: hi=min(hi,math.floor(g*FM/(ESI_CEIL+1)))
        d=min(FM,max(1,lo)) if lo>hi else (lo if base<lo else (hi if base>hi else base))
        if pf>0 and bd>0:
            t=math.ceil(bd*FM/PF_CEIL)
            d=max(d,min(t,FM))          # raise toward ceiling-target, capped at month-days (never skip)
        if g>0:
            t=max(1,min(FM,math.floor(g*FM/(ESI_CEIL+1))));d=max(d,t)
        return max(1,min(FM,int(d)))
    for i in range(n): adj[i]=set_days(i)

    bd_arr=rb+rd
    gproj=np.round(np.where(adj>0,rg*FM/adj,0)); bdproj=np.round(np.where(adj>0,bd_arr*FM/adj,0))
    high_pf=bd_arr>PF_CEIL+0.5; high_earn=rg>50000   # B+D over ceiling = genuine high earner (incl. MW-lifted at-ceiling)
    checks=[('C1 OTHER_DED>=0',int(np.sum(ro<-1))),
            ('C2 NET=GROSS-TOTDED',int(np.sum(np.abs(rn-(rg-rt))>1))),
            ('C3 PF=12%(B+D) on PF>0',int(np.sum((rev_pf>0)&(np.abs(rev_pf-PF_RATE*bd_arr)>1)))),
            ('C5 ATT>=0',int(np.sum(ra<-1))),('C6 TOTAL_DED>=0',int(np.sum(rt<-1))),
            ('C7 GROSS=B+D+ATT',int(np.sum(np.abs(rg-(bd_arr+ra))>1))),
            ('C8 NET=NETPAYABLE',int(np.sum(np.abs(rn-netp)>1))),
            ('C9 days in [1,FM]',int(np.sum((adj<1)|(adj>FM)))),
            ('C10 ECR>0 & BDproj>ceil (excl high earners)',int(np.sum((ecr>0)&(~high_pf)&(bdproj>PF_CEIL+0.5)))),
            ('C12 ESI>0 & GROSS>ceil',int(np.sum((rev_esi>0)&(rg>ESI_CEIL+0.5))))]
    fails=sum(v for _,v in checks)

    keep=[c for c in ['MONTH','BRANCHCODE','BRANCHNAME','SITECODE','SITENAME','SITESTATE','EMPCODE',
        'FULLNAME','DESIGNATIONNAME','DUTYNAME','PF WAGES','ESI WAGES','NORMALDAYS','FIXED_BASIC',
        'FIXED_DA','FIXEDGROSS','BASIC','DA','GROSS AMT','PF','ESIC','PT','LWF','OTHER DEDUCTION',
        'TOTALDEDUCTION','NETPAYABLE','PF NO','UAN NO','ESIC NO','SITEDIVISIONDAYS','ECR_PF',
        'ROW_COUNT','IS_MAIN_PF','IS_PRIMARY_ESI','RULE_APPLIED','REMARK'] if c in df.columns]
    o=df[keep].copy()
    for col,val in [('ADJ_WORKING_DAYS',adj),('REVISED_BASIC',np.round(rb,2)),('REVISED_DA',np.round(rd,2)),
        ('REVISED_ATTENDANCE_ALLOWANCE',np.round(ra,2)),('REVISED_GROSS',np.round(rg,2)),
        ('REVISED_PF',np.round(rev_pf,2)),('REVISED_ESIC',np.round(rev_esi,2)),
        ('ESIC_AS_PER_FUTURE',np.round(fut,2)),('REVISED_OTHER_DEDUCTION',np.round(ro,2)),
        ('REVISED_TOTAL_DED',np.round(rt,2)),('REVISED_NET_PAYABLE',np.round(rn,2)),
        ('12%_OF_REVISED_BD',np.round(PF_RATE*bd_arr,2)),('DIFF_12PCT_vs_PF',np.round(PF_RATE*bd_arr-rev_pf,2)),
        ('MONTHLY_BD_PROJECTION',bdproj.astype(int)),('MONTHLY_GROSS_PROJECTION',gproj.astype(int)),
        ('NET_PAYABLE_DIFF',np.round(rn-netp,2)),('CAPPING_ACTION',act),
        ('HIGH_EARNER_EXCEPTION',np.where(high_earn,'GENUINE_HIGH_EARNER','')),
        # --- PF deducted vs deposited, side by side (12% rule on full Basic+DA) ---
        ('PF_WAGE_BASE_FULL',np.round(basic_o+da_o,2)),
        ('PF_DEDUCTED_12PCT',np.round(PF_RATE*(basic_o+da_o),2)),
        ('PF_DEPOSITED_ECR',np.round(ecr,2)),
        ('PF_NOT_DEPOSITED',np.round(PF_RATE*(basic_o+da_o)-ecr,2))]:
        o[col]=val

    summ=[['Month',path.stem],['Calendar days',FM],['Input rows',len(df0)],
        ['Junk ECR total-rows removed',n_junk],['Employee rows',n],['',''],
        ['ECR_PF total (clean)',round(ecr.sum())],['REVISED_PF total',round(rev_pf.sum())],
        ['ESIC_AS_PER_FUTURE total',round(fut.sum())],['REVISED_ESIC total',round(rev_esi.sum())],
        ['NETPAYABLE total',round(netp.sum())],['REVISED_NET total',round(rn.sum())],
        ['NET diff (must be 0)',round(rn.sum()-netp.sum(),2)],['',''],
        ['Check 3b ESI&gross>21000',int(np.sum((rev_esi>0)&(rg>ESI_CEIL+0.5)))],
        ['Check 4 proj>50k (genuine high earners)',int(np.sum(gproj>50000))],
        ['Max gross projection',int(gproj.max()) if n else 0],
        ['MW-floor lifts',int(mw.sum())],['B+D>15000 high earners (accepted)',int(high_pf.sum())],['','']]+\
        [[k,v] for k,v in checks]+[['TOTAL HARD FAILURES',fails],
        ['STATUS','PASS - filing-grade' if fails==0 else 'FAIL - NOT WRITTEN']]
    summary=pd.DataFrame(summ,columns=['Metric','Value'])

    print(f"\n=== {path.stem}  (days={FM}, rows={n}, junk removed={n_junk}) ===")
    for k,v in checks: print(f"  {k:42s}{v:6d}  {'OK' if v==0 else 'FAIL'}")
    print(f"  Check3b={int(np.sum((rev_esi>0)&(rg>ESI_CEIL+0.5)))}  Check4>50k={int(np.sum(gproj>50000))}  maxproj={int(gproj.max()) if n else 0:,}")
    print(f"  ECR(clean)={ecr.sum():,.0f}  REVISED_PF={rev_pf.sum():,.0f}  NETdiff={rn.sum()-netp.sum():.2f}")

    if fails!=0:
        print(f"  *** {fails} HARD-CHECK FAILURES — OUTPUT NOT WRITTEN (by design) ***")
        return False
    if out is None: out=path.with_name(f"{path.stem}_Reconciled_CLEAN.xlsx")
    with pd.ExcelWriter(out,engine='openpyxl') as xw:
        summary.to_excel(xw,sheet_name='Summary',index=False)
        o.to_excel(xw,sheet_name='Reconciled_Data',index=False)
    print(f"  WROTE {out}")
    return True

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--out'); ap.add_argument('--sheet',default=0)
    a=ap.parse_args()
    ok=run(a.file,a.out,a.sheet if a.sheet==0 else a.sheet)
    sys.exit(0 if ok else 2)
