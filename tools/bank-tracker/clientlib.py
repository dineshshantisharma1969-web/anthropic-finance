import re, datetime, collections, openpyxl

KNOWN={'ICICI 039951000005','SBI 31024290656','HDFC 57500000129944',
       'DBS 858200061542','KOTAK (KKBK0000195)','IDFC 10221675468'}

BANKWORD = re.compile(r'\b(BANK|BANKING|HDFC|ICICI|AXIS|KOTAK|IDBI|CANARA|UNION|PNB|PUNJAB|SBI|HSBC|CITI|CITIBANK|'
                      r'STANDARD|CHARTERED|DEUTSCHE|BARCLAYS|RBL|INDUSIND|FEDERAL|IDFC|BANDHAN|DBS|'
                      r'YESB|BOFA|AMERICA|JP|MORGAN|OVERSEAS|CENTRAL|BARODA|MAHARASHTRA|SINDH|INDIAN)\b')
MODETOK  = re.compile(r'(?i)^(NEFT|FT|RTG|RTGS|IMPS|UPI|CHQ|CASH|TRANSFER|COLL|COLLECTION|CR)$')
IFSCTOK  = re.compile(r'^[A-Z]{4}[0O][A-Z0-9]{4,7}$')
REFTOK   = re.compile(r'^(?=.*\d)[A-Z0-9]{8,}$')
NOISE    = re.compile(r'^(AC|A/C|ENDING|POOL|WITH|FROM|TO|OF|THE|LTD|NO|PVT)$')

def _clean(s):
    s = re.sub(r'[^A-Z0-9&.\s-]', ' ', str(s or '').upper())
    s = re.sub(r'\s+', ' ', s).strip(' -.')
    return s

CONNECT = re.compile(r'^(OF|THE|AND|&|[A-Z])$')

def _stop_scan(tokens):
    """Payer name = tokens up to the IFSC/ref, minus the TRAILING bank descriptor.

    Bank words appear inside real client names ("THE HDFC SCHOOL GURGAON"), so we
    never cut at the first one -- we only strip a bank phrase that runs to the end.
    """
    out=[]
    for t in tokens:
        if IFSCTOK.match(t) or t=='ENDING': break
        if REFTOK.match(t) and len(t)>=11: break
        out.append(t)
        if len(out)>=10: break
    # find earliest index from which everything left is bank-descriptor noise
    for i in range(1, len(out)):
        if not BANKWORD.match(out[i]): continue
        if all(BANKWORD.match(t) or CONNECT.match(t) for t in out[i:]):
            out=out[:i]; break
    while out and (NOISE.match(out[-1]) or CONNECT.match(out[-1])): out.pop()
    return ' '.join(out).strip()

def from_narration(n):
    """Best-effort payer name from a bank narration. '' if not resolvable."""
    if not n: return ''
    N = str(n).strip()
    U = N.upper()

    # Government / aggregator credits -> bucket, not a client
    if 'PFMS' in U:            return 'Credit Through PFMS (Govt)'
    if U.startswith('EZY/') or 'ICICIPOS' in U or U.startswith('POS '): return 'POS Settlement'

    # CMS/ TRANSFER/NAME   |  CMS/<ref>/NAME
    if U.startswith('CMS'):
        parts=[p.strip() for p in N.split('/') if p.strip()]
        cand=[p for p in parts[1:] if not MODETOK.match(p.strip())]
        # ICICI CMS reference-only strings (CMS/IN.../CMS..._1/NEFT/FT/RTG) name no payer
        cand=[p for p in cand if not re.fullmatch(r'(?i)(IN\d+|CMS\d+(_\d+)?)', p.strip())]
        if cand: return _clean(cand[-1])
        return 'CMS Collections (unnamed)'
    # TRFR FROM: NAME
    m=re.match(r'(?i)^TRFR\s+FROM\s*:\s*(.+)$', N)
    if m: return _clean(m.group(1))
    # CLG/NAME/chequeno/...  |  TRF/NAME/chequeno/...
    if U.startswith('CLG/') or U.startswith('TRF/'):
        parts=N.split('/')
        if len(parts)>1: return _clean(parts[1])
        return ''
    # SGB/n/ref/NAME/purpose
    if U.startswith('SGB/'):
        parts=N.split('/')
        if len(parts)>3: return _clean(parts[3])
        return ''
    # CHQ DEP ... WBO: NAME :BANK
    m=re.search(r':\s*([^:]+?)\s*:', N)
    if m and U.startswith('CHQ DEP'): return _clean(m.group(1))
    # FT  ref -  - acct - NAME
    if U.startswith('FT'):
        parts=[p.strip() for p in N.split('-') if p.strip()]
        if parts:
            tail=_clean(parts[-1])
            if tail and not re.fullmatch(r'[\d\s]+', tail) and not REFTOK.match(tail.replace(' ','')):
                return tail
        return ''
    # DBS: TRANSFER NEFTIN/RTGS/IMPS <ref> NAME BANK IFSC ...
    m=re.match(r'(?i)^(?:BY\s+)?TRANSFER\s+(?:NEFTIN|NEFT|RTGS|IMPS|FT)?\s*(.*)$', N)
    if m:
        toks=_clean(m.group(1)).split()
        if toks and REFTOK.match(toks[0]): toks=toks[1:]
        return _stop_scan(toks)
    # KOTAK/ICICI: NEFT <ref> NAME   |  NEFT-<ref>-NAME-...
    m=re.match(r'(?i)^(NEFT|RTGS|IMPS|INFT|MMT|UPI|ACH)\b[\s/-]*(.*)$', N)
    if m:
        body=m.group(2)
        if '-' in body:
            segs=[s.strip() for s in body.split('-') if s.strip()]
            segs=[s for s in segs if not REFTOK.match(_clean(s).replace(' ',''))]
            if segs: return _stop_scan(_clean(segs[0]).split())
        toks=_clean(body).split()
        if toks and REFTOK.match(toks[0]): toks=toks[1:]
        return _stop_scan(toks)
    return ''

def canonical(names):
    """Merge truncated bank spellings: if A is a prefix of B, fold A into B."""
    uniq=sorted({n for n in names if n}, key=lambda s:(-len(s), s))
    parent={}
    for n in uniq:
        tgt=n
        # only merge reasonably distinctive prefixes -- a short stub like "THE"
        # is not evidence of the same client
        for m in (uniq if len(n)>=10 else []):
            if m!=n and len(m)>len(n) and m.startswith(n):
                tgt=m; break
        parent[n]=tgt
    # resolve chains
    for n in list(parent):
        seen=set()
        while parent[n]!=n and parent[n] not in seen:
            seen.add(parent[n]); parent[n]=parent[parent[n]]
    return parent

def load(path='tracker.xlsx', tabs=('August 2026','September 2026'), floor='2026-08-01'):
    """Yield deduped, rule-compliant client receipt rows."""
    wb=openpyxl.load_workbook(path, read_only=True, data_only=True)
    seen=set(); out=[]; stats=collections.Counter()
    for tab in tabs:
        for r in wb[tab].iter_rows(min_row=2, values_only=True):
            dr,vd,bank,narr,pty,mode,ref,typ,deb,cred,bal,tag,ibf,se,po,tk=(list(r)+[None]*16)[:16]
            if bank is not None and not isinstance(bank,str): stats['malformed']+=1; continue
            bank=(bank or '').strip()
            if bank not in KNOWN: continue
            dt=dr.strftime('%Y-%m-%d') if isinstance(dr,(datetime.datetime,datetime.date)) else None
            if dt is None or dt<floor: continue
            key=tk if (isinstance(tk,str) and tk) else f"{dt}|{bank}|{str(narr or '')[:40]}|{deb}|{cred}|{bal}"
            if key in seen: stats['dupes']+=1; continue
            seen.add(key)
            if not isinstance(cred,(int,float)) or cred<=0: continue
            nu=str(narr or '').upper()
            ib=(str(ibf or '').strip().upper()=='YES') or (typ and 'TRANSFER' in str(typ).upper())
            if not ib and '*IMPRESSIONS SERV' in nu: ib=True; stats['rule5']+=1
            if ib: stats['interbank']+=1; continue
            p=_clean(pty)
            src='party'
            if not p:
                p=from_narration(narr); src='narration' if p else 'none'
            stats[src]+=1
            out.append({'date':dt,'bank':bank,'narr':str(narr or ''),'client':p,'amt':float(cred),'src':src})
    return out, stats
