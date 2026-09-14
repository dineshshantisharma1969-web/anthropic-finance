function num(v){ const x=Number(String(v==null?'':v).replace(/,/g,'')); return isNaN(x)?0:x; }
function isoDate(v){
  const s=String(v==null?'':v).trim();
  let m=s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if(m) return m[1]+'-'+m[2]+'-'+m[3];
  m=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if(m) return m[3]+'-'+String(m[2]).padStart(2,'0')+'-'+String(m[1]).padStart(2,'0');
  return '';
}
const BANKWORD=/^(BANK|BANKING|HDFC|ICICI|AXIS|KOTAK|IDBI|CANARA|UNION|PNB|PUNJAB|SBI|HSBC|CITI|CITIBANK|STANDARD|CHARTERED|DEUTSCHE|BARCLAYS|RBL|INDUSIND|FEDERAL|IDFC|BANDHAN|DBS|YESB|BOFA|AMERICA|JP|MORGAN|OVERSEAS|CENTRAL|BARODA|MAHARASHTRA|SINDH|INDIAN|MIZUHO|SUMITOMO|MUFG|SHINHAN|WOORI|SCB|DBSS|NATWEST|BNP|PARIBAS|CREDIT|AGRICOLE)$/;
const IFSCTOK=/^[A-Z]{4}[0O][A-Z0-9]{4,7}$/;
const REFTOK=/^(?=.*\d)[A-Z0-9]{8,}$/;
const NOISE=/^(AC|ENDING|POOL|WITH|FROM|TO|OF|THE|LTD|NO|PVT)$/;
const KNOWN_BANKS={'ICICI 039951000005':1,'SBI 31024290656':1,'HDFC 57500000129944':1,
                   'DBS 858200061542':1,'KOTAK (KKBK0000195)':1,'IDFC 10221675468':1};
const CONNECT=/^(OF|THE|AND|&|[A-Z])$/;
const MODETOK=/^(NEFT|FT|RTG|RTGS|IMPS|UPI|CHQ|CASH|TRANSFER|COLL|COLLECTION|CR)$/i;
const REFSUFFIX=/-\d{4}-\d{2}-\d{2}-[\d.]+$/;
function dedupeKey(r, d, cr){
  const tk=String(r.txn==null?'':r.txn);
  if(tk){
    const parts=tk.split('|');
    if(parts.length>=3){ parts[2]=parts[2].replace(REFSUFFIX,''); return parts.join('|'); }
    return tk;
  }
  return d+'|'+r.bank+'|'+String(r.narr).slice(0,40)+'|'+cr;
}

function clean(s){
  let u=String(s==null?'':s).toUpperCase().replace(/[^A-Z0-9&.\s-]/g,' ').replace(/\s+/g,' ').trim();
  return u.replace(/^[-.\s]+|[-.\s]+$/g,'');
}
function stopScan(toks){
  const out=[];
  for(const t of toks){
    if(IFSCTOK.test(t) || t==='ENDING') break;
    if(REFTOK.test(t) && t.length>=11) break;
    out.push(t);
    if(out.length>=10) break;
  }
  for(let i=1;i<out.length;i++){
    if(!BANKWORD.test(out[i])) continue;
    let allBank=true;
    for(let j=i;j<out.length;j++){ if(!BANKWORD.test(out[j]) && !CONNECT.test(out[j])){ allBank=false; break; } }
    if(allBank){ out.length=i; break; }
  }
  while(out.length && (NOISE.test(out[out.length-1]) || CONNECT.test(out[out.length-1]))) out.pop();
  return out.join(' ').trim();
}
function fromNarration(n){
  if(!n) return '';
  const N=String(n).trim(), U=N.toUpperCase();
  if(U.indexOf('PFMS')>=0) return 'Credit Through PFMS (Govt)';
  if(/^CHEQUE\s+DEPOSIT[\s-]*\d*$/i.test(N)) return 'Cheque Deposit (payer not named)';
  if(U.indexOf('EZY/')===0 || U.indexOf('ICICIPOS')>=0 || U.indexOf('POS ')===0) return 'POS Settlement';
  if(U.indexOf('CMS')===0){
    const parts=N.split('/').map(p=>p.trim()).filter(p=>p);
    const cand=parts.slice(1).filter(p=>!MODETOK.test(p)).filter(p=>!/^(IN\d+|CMS\d+(_\d+)?)$/i.test(p));
    return cand.length ? clean(cand[cand.length-1]) : 'CMS Collections (unnamed)';
  }
  let m=N.match(/^TRFR\s+FROM\s*:\s*(.+)$/i);
  if(m) return clean(m[1]);
  if(U.indexOf('CLG/')===0 || U.indexOf('TRF/')===0){
    const p=N.split('/'); return p.length>1 ? clean(p[1]) : '';
  }
  if(U.indexOf('SGB/')===0){
    const p=N.split('/'); return p.length>3 ? clean(p[3]) : '';
  }
  if(U.indexOf('CHQ DEP')===0){
    m=N.match(/:\s*([^:]+?)\s*:/); if(m) return clean(m[1]);
  }
  if(U.indexOf('FT')===0){
    const p=N.split('-').map(x=>x.trim()).filter(x=>x);
    if(p.length){
      const tail=clean(p[p.length-1]);
      if(tail && !/^[\d\s]+$/.test(tail) && !REFTOK.test(tail.replace(/\s/g,''))) return tail;
    }
    return '';
  }
  m=N.match(/^(?:BY\s+)?TRANSFER\s+(?:NEFTIN|NEFT|RTGS|IMPS|FT)?\s*(.*)$/i);
  if(m){
    let toks=clean(m[1]).split(' ').filter(t=>t);
    if(toks.length && REFTOK.test(toks[0])) toks=toks.slice(1);
    return stopScan(toks);
  }
  m=N.match(/^(NEFT|RTGS|IMPS|INFT|MMT|UPI|ACH)\b[\s/-]*(.*)$/i);
  if(m){
    const body=m[2];
    if(body.indexOf('-')>=0){
      const segs=body.split('-').map(s=>s.trim()).filter(s=>s).filter(s=>!REFTOK.test(clean(s).replace(/\s/g,'')));
      if(segs.length) return stopScan(clean(segs[0]).split(' ').filter(t=>t));
    }
    let toks=clean(body).split(' ').filter(t=>t);
    if(toks.length && REFTOK.test(toks[0])) toks=toks.slice(1);
    return stopScan(toks);
  }
  return '';
}
function buildAlias(names){
  const uniq=[...new Set(names.filter(n=>n))].sort((a,b)=> b.length-a.length || (a<b?-1:1));
  const parent={};
  for(const n of uniq){
    let tgt=n;
    if(n.length>=10){
      for(const mm of uniq){
        if(mm===n || mm.length<=n.length || mm.indexOf(n)!==0) continue;
        const tail=mm.slice(n.length).split(' ').filter(t=>t);
        let hasBank=false, allBankish=tail.length>0;
        for(const t of tail){
          if(BANKWORD.test(t)) hasBank=true;
          else if(!CONNECT.test(t)){ allBankish=false; break; }
        }
        if(hasBank && allBankish) continue;
        tgt=mm; break;
      }
    }
    parent[n]=tgt;
  }
  for(const n of Object.keys(parent)){
    let guard=0;
    while(parent[n]!==n && guard++<8) parent[n]=parent[parent[n]];
  }
  return parent;
}
function classify(rows){
  const seen={}; const out=[];
  const stats={party:0,narr:0,none:0,ib:0,dupes:0,malformed:0};
  for(const r of rows){
    if(!KNOWN_BANKS[String(r.bank==null?'':r.bank).trim()]){ if(String(r.bank==null?'':r.bank).trim()) stats.malformed++; continue; }
    const d=isoDate(r.date); if(!d) continue;
    const cr=num(r.credit); if(cr<=0) continue;
    const key=dedupeKey(r, d, cr);
    if(seen[key]){ stats.dupes++; continue; } seen[key]=1;
    const nu=String(r.narr==null?'':r.narr).toUpperCase();
    let ib = String(r.ib==null?'':r.ib).trim().toUpperCase()==='YES'
          || String(r.type==null?'':r.type).toUpperCase().indexOf('TRANSFER')>=0;
    if(!ib && nu.indexOf('*IMPRESSIONS SERV')>=0) ib=true;
    if(ib){ stats.ib++; continue; }
    let p=clean(r.party);
    if(p && /^[\d\s.]+$/.test(p)) p='';
    if(p) stats.party++;
    else { p=fromNarration(r.narr); if(p) stats.narr++; else stats.none++; }
    out.push({date:d, client:p, amt:cr});
  }
  return {rows:out, stats};
}
module.exports={classify,buildAlias,fromNarration,clean};
