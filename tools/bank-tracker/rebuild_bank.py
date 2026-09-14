import openpyxl, datetime, collections, json, re
import clientlib

KNOWN=list(clientlib.KNOWN)
SHORT={'ICICI 039951000005':'ICICI','SBI 31024290656':'SBI','HDFC 57500000129944':'HDFC',
       'DBS 858200061542':'DBS','KOTAK (KKBK0000195)':'KOTAK','IDFC 10221675468':'IDFC'}
ORDER=['ICICI 039951000005','SBI 31024290656','HDFC 57500000129944',
       'DBS 858200061542','KOTAK (KKBK0000195)','IDFC 10221675468']

wb=openpyxl.load_workbook('tracker.xlsx', read_only=True, data_only=True)
seen=set(); agg=collections.defaultdict(lambda:{'rec':0.0,'pay':0.0,'ib':0.0,'bal':None})
stats=collections.Counter()
for tab in ['August 2026','September 2026']:
    for r in wb[tab].iter_rows(min_row=2, values_only=True):
        dr,vd,bank,narr,pty,mode,ref,typ,deb,cred,bal,tag,ibf,se,po,tk=(list(r)+[None]*16)[:16]
        if bank is not None and not isinstance(bank,str): stats['malformed']+=1; continue
        bank=(bank or '').strip()
        if bank not in KNOWN: continue
        dt=dr.strftime('%Y-%m-%d') if isinstance(dr,(datetime.datetime,datetime.date)) else None
        if dt is None or dt<'2026-08-01': continue
        key=clientlib._dedupe_key(tk, dt, bank, narr, deb, cred, bal)
        if key in seen: stats['dupes']+=1; continue
        seen.add(key)
        deb = deb if isinstance(deb,(int,float)) else 0
        cred= cred if isinstance(cred,(int,float)) else 0
        nu=str(narr or '').upper()
        ib=(str(ibf or '').strip().upper()=='YES') or (typ and 'TRANSFER' in str(typ).upper())
        if not ib and dt<'2026-08-06' and deb>0 and 'IMPRESSIONS SERVICES' in nu and \
           ('SBIN0004449' in nu or '31024290656' in nu or 'STATE BANK' in nu):
            ib=True; stats['hist']+=1
        if not ib and cred>0 and '*IMPRESSIONS SERV' in nu: ib=True; stats['rule5']+=1
        e=agg[(bank,dt)]
        if ib: e['ib'] += (cred-deb)
        else:  e['rec']+=cred; e['pay']+=deb
        if isinstance(bal,(int,float)): e['bal']=float(bal)
        stats['used']+=1

dates=sorted({d for _,d in agg})
series={}
for b in ORDER:
    cum=0.0; rows=[]
    for d in dates:
        e=agg.get((b,d))
        if e is None:
            rows.append([d,0,0,0,round(cum,2),None,0,None])
        else:
            net=e['rec']-e['pay']; cum+=net
            rows.append([d, round(e['rec'],2), round(e['pay'],2), round(net,2),
                         round(cum,2), (round(e['bal'],2) if e['bal'] is not None else None),
                         round(e['ib'],2), ('b' if e['bal'] is not None else None)])
    series[b]=rows
DATA={'banks':ORDER,'short':SHORT,'series':series}
json.dump(DATA, open('data_payload.json','w'), separators=(',',':'))
print("stats:",dict(stats))
print("dates:",dates[0],"->",dates[-1],len(dates))
for b in ORDER:
    last=series[b][-1]
    tr=sum(r[1] for r in series[b])
    print("  %-24s receipts %14.2f  last[%s] bal=%s"%(SHORT[b],tr,last[0],last[5]))
print("TOTAL receipts: %.2f"%sum(r[1] for b in ORDER for r in series[b]))
