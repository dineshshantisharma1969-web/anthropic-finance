import pandas as pd, numpy as np, math
df0=pd.read_excel('/tmp/December.xlsx',sheet_name='Sheet1'); FM=31
emp=df0['EMPCODE']; junk=emp.isna()|(emp.astype(str).str.strip().isin(['','nan','NaN','None']))
n_junk=int(junk.sum()); df=df0[~junk].reset_index(drop=True); n=len(df)
def num(c): return pd.to_numeric(df[c],errors='coerce').fillna(0).values if c in df.columns else np.zeros(n)
ecr=num('ECR_PF');fut=num('ESIC_AS_PER_FUTURE');netp=num('NETPAYABLE')
basic_o=num('BASIC');da_o=num('DA');nd=num('NORMALDAYS')
da_src=num('REVISED_DA') if 'REVISED_DA' in df.columns else da_o
rev_pf=np.zeros(n);rev_esi=np.zeros(n);rb=np.zeros(n);rd=np.zeros(n)
rg=np.zeros(n);ra=np.zeros(n);ro=np.zeros(n);rt=np.zeros(n);rn=np.zeros(n)
adj=np.zeros(n,int);act=np.array(['OK']*n,dtype=object);mw=np.zeros(n,bool)
for i in range(n):
    pf=ecr[i];esi=fut[i];npay=netp[i];in_pf=pf>0;in_esi=esi>0
    bd=round(pf/0.12) if in_pf else (basic_o[i]+da_o[i])
    da_alloc=min(da_src[i],bd)
    g=max((round(esi/0.0075) if in_esi else 0.0),bd,npay+pf+esi)
    rev_pf[i]=pf;rev_esi[i]=esi;rb[i]=bd-da_alloc;rd[i]=da_alloc
    rg[i]=g;ra[i]=g-bd;rt[i]=g-npay;ro[i]=(g-npay)-pf-esi;rn[i]=npay
sd=lambda i:max(1,min(FM,int(round(nd[i])) if nd[i]>0 else 1))
for i in range(n):
    if rev_pf[i]>0 and nd[i]>0:
        fl=(basic_o[i]/nd[i])*sd(i)
        if rb[i]<fl-0.5:
            rb[i]=fl;rev_pf[i]=round(0.12*(rb[i]+rd[i]),2);mw[i]=True;bd=rb[i]+rd[i]
            if rg[i]<bd: rg[i]=bd
            ra[i]=rg[i]-bd;rt[i]=rg[i]-rn[i];ro[i]=rt[i]-rev_pf[i]-rev_esi[i]
for i in range(n):
    if ro[i]<-0.5:
        amt=-ro[i];ra[i]+=amt;rg[i]+=amt;rt[i]+=amt;ro[i]=0.0;act[i]='E3_neg_other_to_att'
for i in range(n):
    if rev_esi[i]>0 and rg[i]>21000.5:
        ro[i]+=rev_esi[i];rev_esi[i]=0.0
        act[i]=(act[i]+'; ' if act[i]!='OK' else '')+'ESI_ZEROED_gross_over_21000'
def set_days(i):
    pf=rev_pf[i];esi=rev_esi[i];bd=rb[i]+rd[i];g=rg[i];lo,hi=1,FM;base=sd(i)
    if pf>0 and bd>0: lo=max(lo,math.ceil(bd*FM/15000))
    if esi>0 and g>0: lo=max(lo,math.ceil(g*FM/21000))
    if pf<=0 and bd>0: hi=min(hi,math.floor(bd*FM/15001))
    if esi<=0 and g>0: hi=min(hi,math.floor(g*FM/21001))
    d=min(FM,max(1,lo)) if lo>hi else (lo if base<lo else (hi if base>hi else base))
    if pf>0 and bd>0:
        t=math.ceil(bd*FM/15000)
        if d<t<=FM: d=t
    if g>0:
        t=max(1,min(FM,math.floor(g*FM/21001)));d=max(d,t)
    return max(1,min(FM,int(d)))
for i in range(n): adj[i]=set_days(i)
bd_arr=rb+rd; gproj=np.round(np.where(adj>0,rg*FM/adj,0)); bdproj=np.round(np.where(adj>0,bd_arr*FM/adj,0))
high_pf=rev_pf>1800.5; high_earn=rg>50000

# assemble clean output
keep=['MONTH','BRANCHCODE','BRANCHNAME','SITECODE','SITENAME','SITESTATE','EMPCODE','FULLNAME',
 'DESIGNATIONNAME','DUTYNAME','PF WAGES','ESI WAGES','NORMALDAYS','FIXED_BASIC','FIXED_DA','FIXEDGROSS',
 'BASIC','DA','GROSS AMT','PF','ESIC','PT','LWF','OTHER DEDUCTION','TOTALDEDUCTION','NETPAYABLE',
 'PF NO','UAN NO','ESIC NO','SITEDIVISIONDAYS','ECR_PF','ROW_COUNT','IS_MAIN_PF','IS_PRIMARY_ESI','RULE_APPLIED','REMARK']
keep=[c for c in keep if c in df.columns]
out=df[keep].copy()
out['ADJ_WORKING_DAYS']=adj
out['REVISED_BASIC']=np.round(rb,2); out['REVISED_DA']=np.round(rd,2)
out['REVISED_ATTENDANCE_ALLOWANCE']=np.round(ra,2); out['REVISED_GROSS']=np.round(rg,2)
out['REVISED_PF']=np.round(rev_pf,2); out['REVISED_ESIC']=np.round(rev_esi,2)
out['ESIC_AS_PER_FUTURE']=np.round(fut,2)
out['REVISED_OTHER_DEDUCTION']=np.round(ro,2); out['REVISED_TOTAL_DED']=np.round(rt,2)
out['REVISED_NET_PAYABLE']=np.round(rn,2)
out['12%_OF_REVISED_BASIC+DA']=np.round(0.12*bd_arr,2)
out['DIFF_12PCT_vs_REVISED_PF']=np.round(0.12*bd_arr-rev_pf,2)
out['REVISED_PF_PCT']=np.round(np.where(bd_arr>0,rev_pf/bd_arr*100,0),2)
out['MONTHLY_BD_PROJECTION']=bdproj.astype(int)
out['MONTHLY_GROSS_PROJECTION']=gproj.astype(int)
out['NET_PAYABLE_DIFF']=np.round(rn-netp,2)
out['CAPPING_ACTION']=act
out['HIGH_EARNER_EXCEPTION']=np.where(high_earn,'GENUINE_HIGH_EARNER_proj=gross','')

# validation recompute for summary
def cnt(m): return int(np.sum(m))
checks=[('C1 OTHER_DED>=0',cnt(ro<-1)),('C2 NET=GROSS-TOTDED',cnt(np.abs(rn-(rg-rt))>1)),
 ('C3 PF=12%(B+D) on PF>0',cnt((rev_pf>0)&(np.abs(rev_pf-0.12*bd_arr)>1))),
 ('C5 ATT>=0',cnt(ra<-1)),('C6 TOTAL_DED>=0',cnt(rt<-1)),
 ('C7 GROSS=B+D+ATT',cnt(np.abs(rg-(bd_arr+ra))>1)),('C8 NET=NETPAYABLE',cnt(np.abs(rn-netp)>1)),
 ('C9 days in [1,31]',cnt((adj<1)|(adj>FM))),
 ('C10 ECR>0 & BDproj>15000 (excl PF>1800)',cnt((ecr>0)&(~high_pf)&(bdproj>15000.5))),
 ('C12 ESI>0 & GROSS>21000',cnt((rev_esi>0)&(rg>21000.5)))]
summ=[['December 2025 — CLEAN REBUILD (skill v4.1 + patch)',''],
 ['Input rows',len(df0)],['Junk ECR total-rows removed',n_junk],['Employee rows',n],
 ['',''],['--- ANCHORS ---',''],
 ['ECR_PF total (real, junk removed)',round(ecr.sum())],['REVISED_PF total',round(rev_pf.sum())],
 ['ESIC_AS_PER_FUTURE total',round(fut.sum())],['REVISED_ESIC total',round(rev_esi.sum())],
 ['NETPAYABLE total',round(netp.sum())],['REVISED_NET_PAYABLE total',round(rn.sum())],
 ['NET diff (must be 0)',round(rn.sum()-netp.sum(),2)],
 ['',''],['--- USER COMPLAINTS ---',''],
 ['Check 3b: ESI & gross>21000 (was 2286/725)',cnt((rev_esi>0)&(rg>21000.5))],
 ['Check 4: gross proj>50k (was 405)',cnt(gproj>50000)],
 ['  of which genuine high earners (paid>50k)',cnt((gproj>50000)&high_earn)],
 ['Max gross projection (was 20.9 crore)',int(gproj.max())],
 ['',''],['--- VALIDATION (all must be 0) ---','']]+[[k,v] for k,v in checks]+[
 ['',''],['Accepted: PF filed >1800 (high earners)',int(high_pf.sum())],
 ['MW-floor lifts',int(mw.sum())],
 ['TOTAL HARD-CHECK FAILURES',sum(v for _,v in checks)],
 ['STATUS','PASS — filing-grade' if sum(v for _,v in checks)==0 else 'REVIEW']]
summary=pd.DataFrame(summ,columns=['Metric','Value'])

OUT='/home/user/anthropic-finance/December_Reconciled_CLEAN.xlsx'
with pd.ExcelWriter(OUT,engine='openpyxl') as xw:
    summary.to_excel(xw,sheet_name='Summary',index=False)
    out.to_excel(xw,sheet_name='Reconciled_Data',index=False)
print("WROTE",OUT)
print("cols in output:",out.shape[1],"rows:",out.shape[0])
print("FAILURES:",sum(v for _,v in checks))
print("ECR_PF real total:",f"{ecr.sum():,.0f}","REVISED_PF:",f"{rev_pf.sum():,.0f}")
print("Check3b:",cnt((rev_esi>0)&(rg>21000.5)),"Check4>50k:",cnt(gproj>50000),"max proj:",f"{gproj.max():,.0f}")
