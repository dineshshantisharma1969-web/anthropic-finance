import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';

const manualTrigger = trigger({
  type: 'n8n-nodes-base.manualTrigger',
  version: 1,
  config: { name: 'Run Once' },
  output: [{}]
});

const buildLookup = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Build Lookup',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode:
        "var Q=String.fromCharCode(34);\n" +
        "var SQ=String.fromCharCode(39);\n" +
        "var sheet=SQ+'ISPL Bank Statement Tracker'+SQ;\n" +
        "var cond='ISNUMBER(SEARCH($B$3,'+sheet+'!$E$2:$E$5000))*('+sheet+'!$H$2:$H$5000='+Q+'RECEIPT'+Q+')*('+sheet+'!$M$2:$M$5000='+Q+'NO'+Q+')*(($B$4='+Q+Q+')+(TEXT('+sheet+'!$A$2:$A$5000,'+Q+'yyyy-mm-dd'+Q+')=TEXT($B$4,'+Q+'yyyy-mm-dd'+Q+')))';\n" +
        "var totalF='=ROUND(SUMPRODUCT('+cond+'*IFERROR(VALUE('+sheet+'!$J$2:$J$5000),0)),2)';\n" +
        "var countF='=SUMPRODUCT('+cond+')';\n" +
        "var values=[['CLIENT RECEIPT LOOKUP',''],['',''],['Client name (partial OK):','Cushman'],['Date yyyy-mm-dd (blank = all dates):','2026-06-15'],['',''],['Total Received:',totalF],['Number of Receipts:',countF],['',''],['Tip: type part of a client name in B3. Leave B4 blank to total across all dates.','']];\n" +
        "var addBody={requests:[{addSheet:{properties:{title:'Client Lookup',index:0,tabColor:{red:0.055,green:0.624,blue:0.431}}}}]};\n" +
        "var writeBody={valueInputOption:'USER_ENTERED',data:[{range:SQ+'Client Lookup'+SQ+'!A1',values:values}]};\n" +
        "return [{json:{addBody:addBody,writeBody:writeBody}}];\n"
    }
  },
  output: [{ addBody: { requests: [] }, writeBody: { valueInputOption: 'USER_ENTERED', data: [] } }]
});

const addTab = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Add Lookup Tab',
    onError: 'continueRegularOutput',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + ':batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr("{{ JSON.stringify($('Build Lookup').item.json.addBody) }}")
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ replies: [{ addSheet: { properties: { sheetId: 123 } } }] }]
});

const formatCell = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Format Total Cell',
    onError: 'continueRegularOutput',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + ':batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr("{{ JSON.stringify({requests:[{repeatCell:{range:{sheetId:$('Add Lookup Tab').item.json.replies[0].addSheet.properties.sheetId,startRowIndex:5,endRowIndex:6,startColumnIndex:1,endColumnIndex:2},cell:{userEnteredFormat:{numberFormat:{type:'CURRENCY',pattern:'₹#,##0.00'},textFormat:{bold:true,fontSize:14}}},fields:'userEnteredFormat'}}]}) }}")
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ spreadsheetId: SHEET_ID }]
});

const writeValues = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Write Lookup Values',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + '/values:batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr("{{ JSON.stringify($('Build Lookup').item.json.writeBody) }}")
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ spreadsheetId: SHEET_ID }]
});

export default workflow('ispl-client-lookup-setup', 'ISPL Client Lookup Setup')
  .add(manualTrigger)
  .to(buildLookup)
  .to(addTab)
  .to(formatCell)
  .to(writeValues);
