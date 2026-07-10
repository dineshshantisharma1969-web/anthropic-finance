import { workflow, node, trigger, splitInBatches, nextBatch, expr, newCredential, sticky } from '@n8n/workflow-sdk';

const FOLDER_ID = '129fqVeuWpUgwiSRNFkomywsLvUIsoVan';
const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';

// Each calendar month gets its own data tab so every month starts afresh.
// e.g. "Jul 2026", "Aug 2026". Evaluated in IST at run time, so on the 1st of a
// new month the loop automatically targets (and creates) the new month's tab.
const MONTH_TAB = "{{ $now.setZone('Asia/Kolkata').toFormat('LLLL yyyy') }}";

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily 9AM Trigger',
    parameters: {
      rule: { interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 9, triggerAtMinute: 30 }] }
    }
  },
  output: [{}]
});

const searchFiles = node({
  type: 'n8n-nodes-base.googleDrive',
  version: 3,
  config: {
    name: 'Find Today Statement Files',
    parameters: {
      resource: 'fileFolder',
      operation: 'search',
      searchMethod: 'query',
      queryString: expr("'" + FOLDER_ID + "' in parents and trashed = false and modifiedTime > '{{ $today.toISODate() }}T00:00:00'"),
      returnAll: true,
      options: { fields: ['id', 'name'] }
    },
    credentials: { googleDriveOAuth2Api: newCredential('Google Drive account', 'X6ONNTZzVhhKFi37') }
  },
  output: [{ id: '1C4KnHZRnV5MvYzROcQpCR78H1vlI3wxI', name: 'ICICI.xlsx' }]
});

const keepBankFile = node({
  type: 'n8n-nodes-base.filter',
  version: 2.3,
  config: {
    name: 'Keep Bank Statements',
    parameters: {
      conditions: {
        options: { caseSensitive: false, leftValue: '', typeValidation: 'loose' },
        combinator: 'or',
        conditions: [
          { leftValue: expr('{{ $json.name }}'), rightValue: 'ICICI', operator: { type: 'string', operation: 'contains' } },
          { leftValue: expr('{{ $json.name }}'), rightValue: 'DBS', operator: { type: 'string', operation: 'contains' } },
          { leftValue: expr('{{ $json.name }}'), rightValue: 'KOTAK', operator: { type: 'string', operation: 'contains' } },
          { leftValue: expr('{{ $json.name }}'), rightValue: 'HDFC', operator: { type: 'string', operation: 'contains' } },
          { leftValue: expr('{{ $json.name }}'), rightValue: 'IDFC', operator: { type: 'string', operation: 'contains' } }
        ]
      }
    }
  },
  output: [{ id: '1C4KnHZRnV5MvYzROcQpCR78H1vlI3wxI', name: 'ICICI.xlsx' }]
});

const loopFiles = splitInBatches({
  version: 3,
  config: { name: 'Loop Over Statement Files', parameters: { batchSize: 1 } }
});

const downloadFile = node({
  type: 'n8n-nodes-base.googleDrive',
  version: 3,
  config: {
    name: 'Download Statement File',
    parameters: {
      resource: 'file',
      operation: 'download',
      fileId: { __rl: true, mode: 'id', value: expr('{{ $json.id }}') },
      options: { binaryPropertyName: 'data' }
    },
    credentials: { googleDriveOAuth2Api: newCredential('Google Drive account', 'X6ONNTZzVhhKFi37') }
  },
  output: [{ id: '1C4KnHZRnV5MvYzROcQpCR78H1vlI3wxI', name: 'ICICI.xlsx' }]
});

const extractRows = node({
  type: 'n8n-nodes-base.extractFromFile',
  version: 1.1,
  config: {
    name: 'Extract Rows From XLSX',
    parameters: {
      operation: 'xlsx',
      binaryPropertyName: 'data',
      options: { headerRow: false, includeEmptyCells: true, rawData: false }
    }
  },
  output: [{ A: 'S.N.', B: 'Tran. Id' }]
});

const parseTxns = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Parse Classify Filter',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode:
        "const items = $input.all();\n" +
        "const rows = items.map(it => (Array.isArray(it.json.row) ? it.json.row : Object.values(it.json)).map(v => (v === null || v === undefined) ? '' : v));\n" +
        "const flat = rows.map(r => r.join(' | ')).join(String.fromCharCode(10));\n" +
        "const U = flat.toUpperCase();\n" +
        // Detect bank by EXACT header CELL, not by account number (a statement can cite another
        // bank's account in a narration — HDFC cites ICICI's & vice-versa — which fooled the old
        // number match). Order matters: ICICI/HDFC/KOTAK all carry a 'Transaction Date' column.
        "function cq(v){return rows.some(function(r){return r.some(function(c){return String(c).trim()===v;});});}\n" +
        "let bank='UNKNOWN';\n" +
        "if (cq('Tran. Id')||cq('S.N.')) bank='ICICI 039951000005';\n" +
        "else if (cq('Sl. No.')||cq('Dr / Cr')) bank='KOTAK (KKBK0000195)';\n" +
        "else if (cq('Particulars')) bank='IDFC 10221675468';\n" +
        "else if (cq('Transaction Date')) bank='HDFC 57500000129944';\n" +
        "else if (cq('Date')||flat.includes('858200061542')) bank='DBS 858200061542';\n" +
        "const today = $now.setZone('Asia/Kolkata').toFormat('yyyy-LL-dd');\n" +
        "const months = {jan:'01',feb:'02',mar:'03',apr:'04',may:'05',jun:'06',jul:'07',aug:'08',sep:'09',oct:'10',nov:'11',dec:'12'};\n" +
        "function pad(n){return String(n).padStart(2,'0');}\n" +
        "function iso(s){const m=String(s).match(/^(\\d{4})-(\\d{2})-(\\d{2})/);return m?m[1]+'-'+m[2]+'-'+m[3]:'';}\n" +
        "function serial(s){const t=String(s).trim();if(/^\\d{4,6}(\\.\\d+)?$/.test(t)){const d=new Date(Date.UTC(1899,11,30)+Math.round(parseFloat(t))*86400000);return d.toISOString().slice(0,10);}return '';}\n" +
        "function gen(s){const d=new Date(String(s));return isNaN(d)?'':d.toISOString().slice(0,10);}\n" +
        "function dMonY(s){const m=String(s).match(/(\\d{1,2})[\\/\\-]([A-Za-z]{3})[\\/\\-](\\d{4})/);return m?m[3]+'-'+months[m[2].toLowerCase()]+'-'+pad(m[1]):'';}\n" +
        "function normDate(s){ if(!s) return ''; s=String(s).trim(); return dMonY(s)||iso(s)||s; }\n" +
        "function dmy(s){ if(!s) return ''; s=String(s).trim(); let r=iso(s); if(r) return r; const m=s.match(/(\\d{1,2})\\/(\\d{1,2})\\/(\\d{4})/); if(m) return m[3]+'-'+pad(m[2])+'-'+pad(m[1]); r=serial(s); if(r) return r; return gen(s); }\n" +
        "function mdy(s){ if(!s) return ''; s=String(s).trim(); let r=iso(s); if(r) return r; const m=s.match(/(\\d{1,2})\\/(\\d{1,2})\\/(\\d{4})/); if(m) return m[3]+'-'+pad(m[1])+'-'+pad(m[2]); r=serial(s); if(r) return r; return gen(s); }\n" +
        "function num(v){ if(v===''||v===null||v===undefined) return ''; const n=parseFloat(String(v).replace(/,/g,'').replace(/[^0-9.\\-]/g,'')); return isNaN(n)?'':n; }\n" +
        "function modeOf(n){ n=(n||'').toUpperCase(); if(n.includes('ICICIPOS')||n.startsWith('EZY/')) return 'POS'; if(n.includes('RTGS')) return 'RTGS'; if(n.includes('IMPS')) return 'IMPS'; if(n.startsWith('INF/INFT')||n.includes('INFT')) return 'INFT'; if(n.includes('NEFT')) return 'NEFT'; if(n.startsWith('CLG')||n.includes('IWCLG')||n.includes('CHQ')) return 'CHQ'; if(n.startsWith('CMS')) return 'CMS'; if(n.startsWith('TRF')) return 'TRF'; return 'OTHER'; }\n" +
        // The SBI account (31024290656 / SBIN0004449) is used ONLY for compliance payments
        // (GST/TDS/PF/ESI), so sweeps TO it are real outflows and must stay in Payments.
        // Money coming back FROM it into the tracked accounts is WCDL/limit drawdown
        // (funding, not income) and stays excluded via the RECEIPT own-name rule below.
        "function isInter(narr,type,party){ const u=(narr||'').toUpperCase(); const p=(party||'').toUpperCase(); if(u.includes('CHARGES')||u.includes('CHRG')||u.startsWith('CGST')||u.startsWith('SGST')||u.startsWith('IGST')) return false; if(type==='PAYMENT' && /IMPRESSIONS SERVICES/.test(u) && /(STATE BANK|SBIN0)/.test(u)) return false; if(/FUND\\d/.test(u)) return true; if(u.includes('TRFD')) return true; if(type==='PAYMENT' && /IMPRESSIONS SERVICES/.test(u)) return true; if(type==='RECEIPT' && /IMPRESSIONS SERVICES/.test(p)) return true; return false; }\n" +
        "function classify(n,t){ const u=(n||'').toUpperCase(); if(t==='PAYMENT' && /IMPRESSIONS SERVICES/.test(u) && /(STATE BANK|SBIN0)/.test(u)) return 'Compliance Payment (SBI)'; if(u.includes('PAYROLL')||u.includes('SALARY')) return 'Payroll / Statutory'; if(u.includes('ESI')||u.includes('EPF')) return 'Payroll / Statutory'; if(u.includes('GST')||u.includes('TDS')||u.includes('IT DEPT')) return 'Tax Payment'; if(u.includes('RENT')||u.includes('LEASE')) return 'Rent'; if(u.includes('INTEREST')||u.includes('INT CHRG')||u.includes('CHARGES')) return 'Bank Charges'; if(u.includes('LOMBARD')||u.includes('INSURANCE')) return 'Vendor Payment'; if(modeOf(n)==='POS') return 'Client Receipt'; if(t==='RECEIPT'){ if(modeOf(n)==='CMS') return 'CMS Collection'; return 'Client Receipt'; } if(modeOf(n)==='CMS') return 'CMS Settlement / Review Required'; return 'Review Required'; }\n" +
        "function partyNeft(n){ const p=String(n).split('-'); return p.length>=3? p[2].trim().slice(0,60):''; }\n" +
        // INF/INFT = ICICI-to-ICICI internal transfer, but the SENDER can be a client with an
        // ICICI account (Snow White, Elite Metaliks, Bengal Ultimate, Clinikally...), so the
        // counterparty must be read from the narration segments, never assumed to be ISPL's own
        // account. Format: INF/INFT/<tranId>/<remark>/<party>[/NA] — take the last alphabetic
        // segment. Own transfers still get excluded via isInter (IMPRESSIONS/TRFD/FUND rules).
        "function partyInft(n){ const segs=String(n).split('/').slice(3).map(function(s){return s.trim();}).filter(function(s){return s && s.toUpperCase()!=='NA' && !/^\\d+$/.test(s) && /[A-Za-z]{3}/.test(s);}); return segs.length? segs[segs.length-1].slice(0,60):''; }\n" +
        "function rec(date,vdate,narr,party,m,ref,type,dr,cr,ib){ return { json: { 'Date':date,'Value Date':vdate,'Bank Account':bank,'Narration':narr,'Party Name':party,'Mode':m,'Reference No':ref,'Type':type,'Debit': dr===''?'':dr,'Credit': cr===''?'':cr,'Balance':'','Auto Tag': ib?'Inter-Bank Transfer':classify(narr,type),'Inter-Bank Excluded?': ib?'YES':'NO','Source Email Date':today,'Processed On':today } }; }\n" +
        "const out=[];\n" +
        "if(bank.startsWith('ICICI')){\n" +
        "  const h = rows.findIndex(r => String(r[0]).trim()==='S.N.' || r.some(c=>String(c).includes('Tran. Id')));\n" +
        "  for(let i=h+1;i<rows.length;i++){ const r=rows[i]; if(!r) continue; const tranId=String(r[1]||'').trim(); if(!tranId) continue; const vdate=normDate(r[2]); const narr=String(r[6]||'').trim(); const wd=num(r[7]); const dp=num(r[8]); if(wd==='' && dp==='') continue; const type= dp!=='' ? 'RECEIPT':'PAYMENT'; const m=modeOf(narr); let party=(m==='NEFT'||m==='RTGS')?partyNeft(narr):(m==='POS'?'POS Settlement':(m==='INFT'?partyInft(narr):'')); if(narr.toUpperCase().startsWith('CMS/ CMS')) party=narr.split('/').pop().trim(); const ib=isInter(narr,type,party); out.push(rec(vdate,vdate,narr,party,m,tranId,type,wd,dp,ib)); }\n" +
        "} else if(bank.startsWith('DBS')){\n" +
        "  const h = rows.findIndex(r => String(r[0]).trim()==='Date' && r.some(c=>String(c).toLowerCase().includes('debit')));\n" +
        "  for(let i=h+1;i<rows.length;i++){ const r=rows[i]; const d0=String(r[0]||'').trim(); if(!/\\d/.test(d0)) continue; const date=normDate(r[0]); const vdate=normDate(r[1]); const desc=(String(r[2]||'')+' '+String(r[3]||'')).trim(); const dr=num(r[4]); const cr=num(r[5]); if(dr==='' && cr==='') continue; const type= cr!=='' ? 'RECEIPT':'PAYMENT'; const m=modeOf(desc); const refm=desc.match(/(NEFTIN|NEFT|RTGS)\\s+(\\S+)/); const ref=refm?refm[2]:(date+'-'+(dr||cr)); let party=''; const pm=desc.match(/(?:NEFTIN|NEFT|RTGS)\\s+\\S+\\s+(.*?)\\s+(KOTAK|DEU|HSBC|HDFC|ICICI|BANK OF AMERICA|STANDARD CHARTERED|FEDERAL|YES BANK|STATE BANK|CITI|BASSEIN)/i); if(pm) party=pm[1].trim().slice(0,60); const ib=isInter(desc,type,party); out.push(rec(date,vdate,desc.slice(0,200),party,m,ref,type,dr,cr,ib)); }\n" +
        "} else if(bank.startsWith('KOTAK')){\n" +
        "  const h = rows.findIndex(r => String(r[0]).trim()==='Sl. No.' || r.some(c=>String(c).includes('Dr / Cr')));\n" +
        "  for(let i=h+1;i<rows.length;i++){ const r=rows[i]; const dc=String(r[6]||'').trim().toUpperCase(); if(dc!=='DR'&&dc!=='CR') continue; const date=mdy(r[2])||mdy(r[1]); const desc=String(r[3]||'').trim(); const amt=num(r[5]); if(amt==='') continue; const ref=(String(r[4]||'').trim()||'KOT')+'-'+date+'-'+amt; const type=dc==='CR'?'RECEIPT':'PAYMENT'; const m=modeOf(desc); const party=(m==='NEFT'||m==='RTGS')?partyNeft(desc):''; const ib=isInter(desc,type,party); out.push(rec(date,date,desc.slice(0,200),party,m,ref,type, dc==='DR'?amt:'', dc==='CR'?amt:'', ib)); }\n" +
        "} else if(bank.startsWith('IDFC')){\n" +
        "  const h = rows.findIndex(r => String(r[0]).trim()==='Transaction Date' && r.some(c=>String(c).trim()==='Particulars'));\n" +
        "  for(let i=h+1;i<rows.length;i++){ const r=rows[i]; const d0=String(r[0]||'').trim(); if(!/\\d/.test(d0)) continue; const date=normDate(r[0]); const vdate=normDate(r[1]); const desc=String(r[2]||'').trim(); if(!desc) continue; const chq=String(r[3]||'').trim(); const dr=num(r[4]); const cr=num(r[5]); if(dr==='' && cr==='') continue; const type= cr!=='' ? 'RECEIPT':'PAYMENT'; const m=modeOf(desc); const parts=desc.split('/'); let ref=chq; if(!ref && (m==='RTGS'||m==='NEFT'||m==='IMPS') && parts.length>=2) ref=parts[1].trim(); if(!ref) ref=date+'-'+(dr||cr); let party=''; if((m==='RTGS'||m==='NEFT'||m==='IMPS') && parts.length>=3) party=parts[2].trim().slice(0,60); else if(desc.toUpperCase().indexOf('CHQ DEP')>-1 && parts.length>=5) party=parts[4].trim().slice(0,60); const ib=isInter(desc,type,party); out.push(rec(date,vdate,desc.slice(0,200),party,m,ref,type,dr,cr,ib)); }\n" +
        "} else if(bank.startsWith('HDFC')){\n" +
        "  const h = rows.findIndex(r => String(r[0]).trim()==='Transaction Date' && r.some(c=>String(c).toLowerCase().includes('debit')));\n" +
        "  for(let i=h+1;i<rows.length;i++){ const r=rows[i]; const dc=String(r[3]||'').trim().toUpperCase(); if(dc!=='C'&&dc!=='D') continue; const desc=String(r[1]||'').trim(); const amt=num(r[2]); if(amt==='') continue; const date=dmy(r[5])||dmy(r[0]); const ref=(String(r[4]||'').trim()||'HDF')+'-'+date+'-'+amt; const type=dc==='C'?'RECEIPT':'PAYMENT'; const m=modeOf(desc); const party=(m==='NEFT'||m==='RTGS')?partyNeft(desc):''; const ib=isInter(desc,type,party); out.push(rec(date,date,desc.slice(0,200),party,m,ref,type, dc==='D'?amt:'', dc==='C'?amt:'', ib)); }\n" +
        "}\n" +
        // Txn Key = stable dedup key used by the Append-or-Update sheet write (LIVE workflow
        // hqrLbu8oBQxIURU3 matches on this column).
        "function normRefKey(s){ return String(s==null?'':s).toUpperCase().replace(/\\s+/g,'').replace(/\\.0$/,''); }\n" +
        "for (const o of out) { const j=o.json; j['Txn Key'] = j['Bank Account']+'|'+j['Date']+'|'+normRefKey(j['Reference No'])+'|'+String(Number(j['Debit'])||0)+'|'+String(Number(j['Credit'])||0); }\n" +
        "return out;\n"
    }
  },
  output: [{ 'Date': '2026-06-13', 'Bank Account': 'ICICI 039951000005', 'Reference No': 'S94023670', 'Type': 'RECEIPT', 'Credit': 13986.7, 'Auto Tag': 'Client Receipt', 'Inter-Bank Excluded?': 'NO' }]
});

// Create this month's data tab if it does not exist yet. Runs every day; on any day
// after the 1st the tab already exists, so the "already exists" error is swallowed
// (onError: continueRegularOutput) and the flow proceeds straight to the append.
const ensureMonthTab = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Ensure Month Tab',
    onError: 'continueRegularOutput',
    parameters: {
      resource: 'sheet',
      operation: 'create',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      title: expr(MONTH_TAB),
      options: {}
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{}]
});

const appendSheet = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Append To Tracker',
    parameters: {
      resource: 'sheet',
      operation: 'appendOrUpdate',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: expr(MONTH_TAB) },
      columns: {
        mappingMode: 'autoMapInputData',
        value: {},
        matchingColumns: ['Reference No'],
        schema: [
          { id: 'Date', displayName: 'Date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Value Date', displayName: 'Value Date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Bank Account', displayName: 'Bank Account', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Narration', displayName: 'Narration', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Party Name', displayName: 'Party Name', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Mode', displayName: 'Mode', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Reference No', displayName: 'Reference No', required: false, defaultMatch: true, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'Type', displayName: 'Type', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Debit', displayName: 'Debit', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Credit', displayName: 'Credit', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Balance', displayName: 'Balance', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Auto Tag', displayName: 'Auto Tag', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Inter-Bank Excluded?', displayName: 'Inter-Bank Excluded?', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Source Email Date', displayName: 'Source Email Date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Processed On', displayName: 'Processed On', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false }
        ]
      },
      options: { cellFormat: 'USER_ENTERED' }
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ 'Reference No': 'S94023670' }]
});

const note = sticky(
  '## ISPL Bank Statement Loop\nDaily 09:00 (instance TZ). Reads today\'s xlsx from the DAILY BANK STATEMENTS Drive folder, keeps ICICI & DBS (Pegasus skipped), parses + classifies, flags inter-bank transfers, then upserts into the **current month\'s tab** (e.g. "Jul 2026") by Reference No.\n\n"Ensure Month Tab" creates that tab on the 1st of each month so every month starts afresh; on later days the "already exists" error is ignored.',
  [scheduleTrigger, appendSheet],
  { color: 4 }
);

export default workflow('ispl-bank-statement-loop', 'ISPL Bank Statement Loop')
  .add(scheduleTrigger)
  .to(ensureMonthTab)
  .to(searchFiles)
  .to(keepBankFile)
  .to(loopFiles
    .onDone(appendSheet)
    .onEachBatch(downloadFile.to(extractRows).to(parseTxns).to(nextBatch(loopFiles)))
  )
  .add(note);
