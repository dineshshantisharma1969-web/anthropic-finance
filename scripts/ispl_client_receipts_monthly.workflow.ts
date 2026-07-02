import { workflow, node, trigger, expr, newCredential, sticky } from '@n8n/workflow-sdk';

// Deployed as n8n workflow eMfGJ6cGzOt4VLaj ("ISPL Client Receipts (Monthly)").
// Runs daily 09:50. Clears the "Client Receipts" tab, reads the CURRENT month's data tab
// (e.g. "July 2026"), aggregates RECEIPTS by client, and writes a ranked list + TOTAL row.
// EXCLUDES inter-bank transfers, loan-payment reversals and DD cancellations (bank credits
// the auto-classifier would otherwise mis-count as client money — e.g. a Rs 10 cr loan reversal).

const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';
const SHEETS_CRED = () => newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0');
const MONTH_TAB = "{{ $now.setZone('Asia/Kolkata').toFormat('LLLL yyyy') }}";

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily 9:50 Trigger',
    parameters: { rule: { interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 9, triggerAtMinute: 50 }] } }
  },
  output: [{}]
});

const clearTab = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Clear Client Receipts',
    parameters: {
      resource: 'sheet', operation: 'clear',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: 'Client Receipts' },
      clear: 'specificRange', range: 'A:D'
    },
    credentials: { googleSheetsOAuth2Api: SHEETS_CRED() }
  },
  output: [{}]
});

const readTx = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Read Month Tab',
    parameters: {
      resource: 'sheet', operation: 'read',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: expr(MONTH_TAB) },
      options: { returnAllMatches: 'returnAllMatches' }
    },
    credentials: { googleSheetsOAuth2Api: SHEETS_CRED() }
  },
  output: [{ 'Party Name': 'GMR AIRPORTS LIMITED', 'Type': 'RECEIPT', 'Credit': 4314210.18, 'Inter-Bank Excluded?': 'NO' }]
});

const build = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Aggregate By Client',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode:
        "const items=$input.all();\n" +
        "function up(s){return String(s==null?'':s).toUpperCase();}\n" +
        "function num(v){ if(v===''||v==null) return 0; const n=parseFloat(String(v).replace(/,/g,'')); return isNaN(n)?0:n; }\n" +
        "function r2(x){return Math.round(x*100)/100;}\n" +
        "const agg={};\n" +
        "for(const it of items){ const j=it.json; if(up(j['Inter-Bank Excluded?'])==='YES') continue; const credit=num(j['Credit']); if(!(credit>0)) continue; const narr=String(j['Narration']||''); const U=narr.toUpperCase(); if(U.indexOf('LOAN PAYMENT REVERSAL')>-1) continue; if(U.indexOf('DD CANCLN')>-1) continue; let client=''; const p=j['Party Name']; if(p!=null&&String(p).trim()!==''&&String(p).trim().toLowerCase()!=='nan') client=String(p).trim(); else if(U.indexOf('EZY/')===0||U.indexOf('ICICIPOS')>-1) client='POS Settlement (card)'; else if(U.indexOf('CMS/')===0) client='CMS Collection (coded, unnamed)'; else { const m=narr.match(/(?:NEFT|RTGS|IMPS)[-\\s]\\S+[-\\s]([^-]+?)[-\\s]/); client=m?m[1].trim().slice(0,60):'(Unidentified)'; } if(!agg[client]) agg[client]={t:0,c:0}; agg[client].t+=credit; agg[client].c+=1; }\n" +
        "const rows=Object.keys(agg).map(k=>({client:k,t:agg[k].t,c:agg[k].c})).sort((a,b)=>b.t-a.t);\n" +
        "let TT=0,TC=0; const out=[];\n" +
        "for(const r of rows){ TT+=r.t; TC+=r.c; out.push({json:{'Client':r.client,'Total Received':r2(r.t),'# Receipts':r.c}}); }\n" +
        "out.push({json:{'Client':'TOTAL CLIENT RECEIPTS','Total Received':r2(TT),'# Receipts':TC}});\n" +
        "return out;\n"
    }
  },
  output: [{ 'Client': 'GMR AIRPORTS LIMITED', 'Total Received': 4314210.18, '# Receipts': 1 }]
});

const writeTab = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Write Client Receipts',
    parameters: {
      resource: 'sheet', operation: 'append',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: 'Client Receipts' },
      columns: {
        mappingMode: 'autoMapInputData', value: {}, matchingColumns: [],
        schema: [
          { id: 'Client', displayName: 'Client', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'Total Received', displayName: 'Total Received', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: true },
          { id: '# Receipts', displayName: '# Receipts', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: true }
        ]
      },
      options: { cellFormat: 'USER_ENTERED' }
    },
    credentials: { googleSheetsOAuth2Api: SHEETS_CRED() }
  },
  output: [{ 'Client': 'GMR AIRPORTS LIMITED' }]
});

const note = sticky(
  '## ISPL Client Receipts (Monthly)\nDaily 09:50. Clears the Client Receipts tab, reads the current month tab (LLLL yyyy), aggregates receipts by client (Party Name; POS / CMS bucketed), excludes inter-bank / loan-payment reversals / DD cancellations, and writes the ranked client list + TOTAL.',
  [scheduleTrigger, writeTab],
  { color: 6 }
);

export default workflow('ispl-client-receipts-monthly', 'ISPL Client Receipts (Monthly)')
  .add(scheduleTrigger)
  .to(clearTab)
  .to(readTx)
  .to(build)
  .to(writeTab)
  .add(note);
