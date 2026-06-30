import { workflow, node, trigger, expr, newCredential, sticky } from '@n8n/workflow-sdk';

// Deployed as n8n workflow QrtxpYLVuedOPU0e ("ISPL Bank Dashboard Refresh").
// Runs daily 09:15 (after the main loop). Clears + rebuilds the "Dashboard" tab of the
// ISPL Bank Statement Tracker with daily receipts/payments and running cumulative totals
// (excluding inter-bank transfers), plus a TOTAL row.
//
// MONTHLY RESET: the dashboard reads ONLY the current month's data tab (e.g. "Jul 2026"),
// so on the 1st of each month the daily rows and the running cumulative both start afresh
// from zero. The single "Dashboard" tab (and its charts / KPI scorecards) is reused every
// month — only its data (A:G) is rebuilt — so nothing needs re-styling at month rollover.
//
// NOTE: the "Dashboard" tab must exist once before first run. It was created via the
// Google Sheets node (sheet:create) during setup; thereafter this workflow only
// clears + appends. The month data tab is referenced by NAME (e.g. "Jul 2026").

const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';
const SHEETS_CRED = () => newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0');

// Current month's data tab, evaluated in IST at run time — matches the loop's MONTH_TAB.
const MONTH_TAB = "{{ $now.setZone('Asia/Kolkata').toFormat('LLL yyyy') }}";

const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily 9:15 Refresh',
    parameters: { rule: { interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 9, triggerAtMinute: 45 }] } }
  },
  output: [{}]
});

const clearDash = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Clear Dashboard',
    parameters: {
      resource: 'sheet',
      operation: 'clear',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: 'Dashboard' },
      clear: 'specificRange',
      range: 'A:G'
    },
    credentials: { googleSheetsOAuth2Api: SHEETS_CRED() }
  },
  output: [{}]
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
      sheetName: { __rl: true, mode: 'name', value: expr(MONTH_TAB) },
      options: { returnAllMatches: 'returnAllMatches' }
    },
    credentials: { googleSheetsOAuth2Api: SHEETS_CRED() }
  },
  output: [{ 'Date': '2026-06-16', 'Credit': 13986.7, 'Debit': '', 'Inter-Bank Excluded?': 'NO' }]
});

const buildDash = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Build Daily + Cumulative',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode:
        "const items=$input.all();\n" +
        "const byDate={};\n" +
        "function r2(x){return Math.round(x*100)/100;}\n" +
        "for(const it of items){ const j=it.json; if(String(j['Inter-Bank Excluded?']||'')==='YES') continue; const d=j['Date']||''; if(!d||d==='TOTAL') continue; const rc=parseFloat(String(j['Credit']!=null?j['Credit']:'0').replace(/,/g,''))||0; const pay=parseFloat(String(j['Debit']!=null?j['Debit']:'0').replace(/,/g,''))||0; if(!byDate[d]) byDate[d]={r:0,p:0}; byDate[d].r+=rc; byDate[d].p+=pay; }\n" +
        "const dates=Object.keys(byDate).sort();\n" +
        "let cr=0,cp=0; const out=[];\n" +
        "for(const d of dates){ const r=byDate[d].r,p=byDate[d].p; cr+=r; cp+=p; out.push({json:{'Date':d,'Daily Receipts':r2(r),'Daily Payments':r2(p),'Daily Net':r2(r-p),'Cumulative Receipts':r2(cr),'Cumulative Payments':r2(cp),'Cumulative Net':r2(cr-cp)}}); }\n" +
        "out.push({json:{'Date':'TOTAL','Daily Receipts':r2(cr),'Daily Payments':r2(cp),'Daily Net':r2(cr-cp),'Cumulative Receipts':r2(cr),'Cumulative Payments':r2(cp),'Cumulative Net':r2(cr-cp)}});\n" +
        "return out;\n"
    }
  },
  output: [{ 'Date': '2026-06-16', 'Daily Receipts': 322470.16, 'Daily Payments': 0, 'Daily Net': 322470.16, 'Cumulative Receipts': 20469012.94, 'Cumulative Payments': 2232812, 'Cumulative Net': 18236200.94 }]
});

const writeDash = node({
  type: 'n8n-nodes-base.googleSheets',
  version: 4.7,
  config: {
    name: 'Write Dashboard',
    parameters: {
      resource: 'sheet',
      operation: 'append',
      documentId: { __rl: true, mode: 'id', value: SHEET_ID },
      sheetName: { __rl: true, mode: 'name', value: 'Dashboard' },
      columns: {
        mappingMode: 'autoMapInputData',
        value: {},
        schema: [
          { id: 'Date', displayName: 'Date', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false },
          { id: 'Daily Receipts', displayName: 'Daily Receipts', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'Daily Payments', displayName: 'Daily Payments', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'Daily Net', displayName: 'Daily Net', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'Cumulative Receipts', displayName: 'Cumulative Receipts', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'Cumulative Payments', displayName: 'Cumulative Payments', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false },
          { id: 'Cumulative Net', displayName: 'Cumulative Net', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: false }
        ]
      },
      options: { cellFormat: 'USER_ENTERED' }
    },
    credentials: { googleSheetsOAuth2Api: SHEETS_CRED() }
  },
  output: [{ 'Date': '2026-06-16' }]
});

const note = sticky(
  '## ISPL Bank Dashboard Refresh\nDaily 09:15. Clears the Dashboard tab (A:G only — KPI cells in J survive), reads the **current month\'s data tab** (e.g. "Jul 2026"), aggregates daily receipts/payments + running cumulative (excluding inter-bank), and rewrites the Dashboard with a TOTAL row.\n\nBecause it reads only the current month, the cumulative resets to 0 on the 1st of each month — July starts afresh.',
  [scheduleTrigger, writeDash],
  { color: 5 }
);

export default workflow('ispl-bank-dashboard-refresh', 'ISPL Bank Dashboard Refresh')
  .add(scheduleTrigger)
  .to(clearDash)
  .to(readTx)
  .to(buildDash)
  .to(writeDash)
  .add(note);
