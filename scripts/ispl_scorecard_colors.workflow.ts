import { workflow, node, trigger, newCredential } from '@n8n/workflow-sdk';

// One-shot (n8n workflow A8YXNhY0jaYj0XA6): colors the three Today scorecard charts via
// Sheets API updateChartSpec — Receipts green, Payments red, Net blue (bold, 28pt).
const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';

const jsonBody = '{"requests":[' +
  '{"updateChartSpec":{"chartId":699728460,"spec":{"title":"Today\'s Receipts","scorecardChart":{"keyValueData":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":1,"endRowIndex":2,"startColumnIndex":10,"endColumnIndex":11}]}},"numberFormatSource":"FROM_DATA","keyValueFormat":{"textFormat":{"bold":true,"fontSize":28,"foregroundColorStyle":{"rgbColor":{"red":0.055,"green":0.624,"blue":0.431}}}}}}}},' +
  '{"updateChartSpec":{"chartId":89391805,"spec":{"title":"Today\'s Payments","scorecardChart":{"keyValueData":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":2,"endRowIndex":3,"startColumnIndex":10,"endColumnIndex":11}]}},"numberFormatSource":"FROM_DATA","keyValueFormat":{"textFormat":{"bold":true,"fontSize":28,"foregroundColorStyle":{"rgbColor":{"red":0.878,"green":0.141,"blue":0.141}}}}}}}},' +
  '{"updateChartSpec":{"chartId":448051791,"spec":{"title":"Today\'s Net Cash Flow","scorecardChart":{"keyValueData":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":3,"endRowIndex":4,"startColumnIndex":10,"endColumnIndex":11}]}},"numberFormatSource":"FROM_DATA","keyValueFormat":{"textFormat":{"bold":true,"fontSize":28,"foregroundColorStyle":{"rgbColor":{"red":0.102,"green":0.337,"blue":0.859}}}}}}}}' +
  ']}';

const manualTrigger = trigger({
  type: 'n8n-nodes-base.manualTrigger',
  version: 1,
  config: { name: 'Run Once' },
  output: [{}]
});

const colorScorecards = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Color Scorecards (Sheets API)',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + ':batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: jsonBody
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ spreadsheetId: SHEET_ID }]
});

export default workflow('ispl-scorecard-colors', 'ISPL Scorecard Colors')
  .add(manualTrigger)
  .to(colorScorecards);
