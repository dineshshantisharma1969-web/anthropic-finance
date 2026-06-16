import { workflow, node, trigger, newCredential, expr, sticky } from '@n8n/workflow-sdk';

const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily 9:20 Refresh',
    parameters: { rule: { interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 9, triggerAtMinute: 20 }] } }
  },
  output: [{}]
});

const getMeta = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Get Spreadsheet Metadata',
    parameters: {
      method: 'GET',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + '?fields=sheets.properties(title,sheetId)',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api'
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ sheets: [{ properties: { sheetId: 0, title: 'ISPL Bank Statement Tracker' } }] }]
});

const readTx = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Read Daily Transactions',
    parameters: {
      resource: 'sheet',
      operation: 'read',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: 'ISPL Bank Statement Tracker' },
      options: { returnAllMatches: 'returnAllMatches' }
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ 'Date': '2026-06-15', 'Party Name': 'D J INFRASTRUCTURE DEVELOPERS PV', 'Type': 'RECEIPT', 'Credit': 307635.78, 'Inter-Bank Excluded?': 'NO' }]
});

const build = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Build Client Receipts',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode:
        "const txns = $('Read Daily Transactions').all().map(i=>i.json);\n" +
        "const meta = $('Get Spreadsheet Metadata').first().json;\n" +
        "const existing = new Set((meta.sheets||[]).map(s=>s.properties.title));\n" +
        "const byDate = {};\n" +
        "for(const t of txns){ if(String(t['Type'])!=='RECEIPT') continue; if(String(t['Inter-Bank Excluded?'])==='YES') continue; const d=t['Date']; if(!d) continue; let client=String(t['Party Name']||'').trim(); if(!client) client='(Unidentified)'; const amt=parseFloat(String(t['Credit']!=null?t['Credit']:'0').replace(/,/g,''))||0; if(amt<=0) continue; byDate[d]=byDate[d]||{}; byDate[d][client]=byDate[d][client]||{total:0,count:0}; byDate[d][client].total+=amt; byDate[d][client].count+=1; }\n" +
        "const dates=Object.keys(byDate).sort();\n" +
        "const addRequests=[]; const clearRanges=[]; const valueData=[];\n" +
        "function r2(x){return Math.round(x*100)/100;}\n" +
        "for(const d of dates){ if(!existing.has(d)) addRequests.push({addSheet:{properties:{title:d}}}); clearRanges.push(\"'\"+d+\"'!A:C\"); const clients=Object.keys(byDate[d]).map(c=>({c,total:byDate[d][c].total,count:byDate[d][c].count})); clients.sort((a,b)=>b.total-a.total); const rows=[['Client','Total Received','# Receipts']]; let g=0,gc=0; for(const x of clients){ rows.push([x.c,r2(x.total),x.count]); g+=x.total; gc+=x.count; } rows.push(['TOTAL',r2(g),gc]); valueData.push({range:\"'\"+d+\"'!A1\",values:rows}); }\n" +
        "return [{json:{addBody:{requests:addRequests},clearBody:{ranges:clearRanges},writeBody:{valueInputOption:'USER_ENTERED',data:valueData}}}];\n"
    }
  },
  output: [{ addBody: { requests: [] }, clearBody: { ranges: [] }, writeBody: { valueInputOption: 'USER_ENTERED', data: [] } }]
});

const createTabs = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Create Missing Date Tabs',
    onError: 'continueRegularOutput',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + ':batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify($("Build Client Receipts").item.json.addBody) }}')
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ spreadsheetId: SHEET_ID }]
});

const clearTabs = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Clear Date Tabs',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + '/values:batchClear',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify($("Build Client Receipts").item.json.clearBody) }}')
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ spreadsheetId: SHEET_ID }]
});

const writeTabs = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Write Client Receipts',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + '/values:batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify($("Build Client Receipts").item.json.writeBody) }}')
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ spreadsheetId: SHEET_ID }]
});

const note = sticky(
  '## ISPL Client Daily Receipts\nDaily 09:20. Reads Daily Transactions, groups client RECEIPTS by date (inter-bank excluded), sums multiple receipts per client, and writes one tab per date (Client | Total Received | # Receipts + TOTAL). Creates new date tabs as they appear; refreshes existing ones each run.',
  [scheduleTrigger, writeTabs],
  { color: 4 }
);

export default workflow('ispl-client-daily-receipts', 'ISPL Client Daily Receipts')
  .add(scheduleTrigger)
  .to(getMeta)
  .to(readTx)
  .to(build)
  .to(createTabs)
  .to(clearTabs)
  .to(writeTabs)
  .add(note);
