import { workflow, node, trigger, newCredential, sticky } from '@n8n/workflow-sdk';

const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';

// Sheets API batchUpdate: restyle the two existing charts (data labels + ₹ axis title),
// format data + KPI cells as ₹ currency, write 3 live "Today" KPI helper cells (I/J),
// and add 3 scorecard charts (Today's Receipts / Payments / Net).
const jsonBody = '{"requests":[' +
  '{"updateChartSpec":{"chartId":1559283598,"spec":{"title":"ISPL — Daily Receipts vs Payments","titleTextFormat":{"bold":true,"fontSize":14},"basicChart":{"chartType":"COLUMN","legendPosition":"BOTTOM_LEGEND","headerCount":1,"axis":[{"position":"BOTTOM_AXIS","title":"Date"},{"position":"LEFT_AXIS","title":"Amount (₹)"}],"domains":[{"domain":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":0,"endColumnIndex":1}]}}}],"series":[{"series":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":1,"endColumnIndex":2}]}},"targetAxis":"LEFT_AXIS","colorStyle":{"rgbColor":{"red":0.055,"green":0.624,"blue":0.431}},"dataLabel":{"type":"DATA","placement":"OUTSIDE_END","textFormat":{"fontSize":8}}},{"series":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":2,"endColumnIndex":3}]}},"targetAxis":"LEFT_AXIS","colorStyle":{"rgbColor":{"red":0.878,"green":0.141,"blue":0.141}},"dataLabel":{"type":"DATA","placement":"OUTSIDE_END","textFormat":{"fontSize":8}}}]}}}},' +
  '{"updateChartSpec":{"chartId":1009815737,"spec":{"title":"ISPL — Cumulative Receipts, Payments & Net","titleTextFormat":{"bold":true,"fontSize":14},"basicChart":{"chartType":"LINE","legendPosition":"BOTTOM_LEGEND","headerCount":1,"lineSmoothing":true,"axis":[{"position":"BOTTOM_AXIS","title":"Date"},{"position":"LEFT_AXIS","title":"Cumulative (₹)"}],"domains":[{"domain":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":0,"endColumnIndex":1}]}}}],"series":[{"series":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":4,"endColumnIndex":5}]}},"targetAxis":"LEFT_AXIS","colorStyle":{"rgbColor":{"red":0.055,"green":0.624,"blue":0.431}},"dataLabel":{"type":"DATA","placement":"ABOVE","textFormat":{"fontSize":8}}},{"series":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":5,"endColumnIndex":6}]}},"targetAxis":"LEFT_AXIS","colorStyle":{"rgbColor":{"red":0.878,"green":0.141,"blue":0.141}},"dataLabel":{"type":"DATA","placement":"ABOVE","textFormat":{"fontSize":8}}},{"series":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":0,"endRowIndex":400,"startColumnIndex":6,"endColumnIndex":7}]}},"targetAxis":"LEFT_AXIS","colorStyle":{"rgbColor":{"red":0.102,"green":0.337,"blue":0.859}},"dataLabel":{"type":"DATA","placement":"ABOVE","textFormat":{"fontSize":8}}}]}}}},' +
  '{"repeatCell":{"range":{"sheetId":1061189248,"startRowIndex":1,"endRowIndex":400,"startColumnIndex":1,"endColumnIndex":7},"cell":{"userEnteredFormat":{"numberFormat":{"type":"CURRENCY","pattern":"₹#,##0"}}},"fields":"userEnteredFormat.numberFormat"}},' +
  '{"updateCells":{"start":{"sheetId":1061189248,"rowIndex":0,"columnIndex":9},"fields":"userEnteredValue","rows":[' +
    '{"values":[{"userEnteredValue":{"stringValue":"Today\'s Date"}},{"userEnteredValue":{"formulaValue":"=LOOKUP(2,1/(A2:A<>\\"\\"),A2:A)"}}]},' +
    '{"values":[{"userEnteredValue":{"stringValue":"Today\'s Receipts"}},{"userEnteredValue":{"formulaValue":"=LOOKUP(2,1/(B2:B<>\\"\\"),B2:B)"}}]},' +
    '{"values":[{"userEnteredValue":{"stringValue":"Today\'s Payments"}},{"userEnteredValue":{"formulaValue":"=LOOKUP(2,1/(C2:C<>\\"\\"),C2:C)"}}]},' +
    '{"values":[{"userEnteredValue":{"stringValue":"Today\'s Net"}},{"userEnteredValue":{"formulaValue":"=LOOKUP(2,1/(D2:D<>\\"\\"),D2:D)"}}]}' +
  ']}},' +
  '{"repeatCell":{"range":{"sheetId":1061189248,"startRowIndex":1,"endRowIndex":4,"startColumnIndex":10,"endColumnIndex":11},"cell":{"userEnteredFormat":{"numberFormat":{"type":"CURRENCY","pattern":"₹#,##0"}}},"fields":"userEnteredFormat.numberFormat"}},' +
  '{"addChart":{"chart":{"spec":{"title":"Today\'s Receipts","scorecardChart":{"keyValueData":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":1,"endRowIndex":2,"startColumnIndex":10,"endColumnIndex":11}]}},"numberFormatSource":"FROM_DATA"}},"position":{"overlayPosition":{"anchorCell":{"sheetId":1061189248,"rowIndex":40,"columnIndex":8},"offsetXPixels":5,"offsetYPixels":5,"widthPixels":220,"heightPixels":140}}}}},' +
  '{"addChart":{"chart":{"spec":{"title":"Today\'s Payments","scorecardChart":{"keyValueData":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":2,"endRowIndex":3,"startColumnIndex":10,"endColumnIndex":11}]}},"numberFormatSource":"FROM_DATA"}},"position":{"overlayPosition":{"anchorCell":{"sheetId":1061189248,"rowIndex":40,"columnIndex":12},"offsetXPixels":5,"offsetYPixels":5,"widthPixels":220,"heightPixels":140}}}}},' +
  '{"addChart":{"chart":{"spec":{"title":"Today\'s Net Cash Flow","scorecardChart":{"keyValueData":{"sourceRange":{"sources":[{"sheetId":1061189248,"startRowIndex":3,"endRowIndex":4,"startColumnIndex":10,"endColumnIndex":11}]}},"numberFormatSource":"FROM_DATA"}},"position":{"overlayPosition":{"anchorCell":{"sheetId":1061189248,"rowIndex":40,"columnIndex":16},"offsetXPixels":5,"offsetYPixels":5,"widthPixels":220,"heightPixels":140}}}}}' +
  ']}';

const manualTrigger = trigger({
  type: 'n8n-nodes-base.manualTrigger',
  version: 1,
  config: { name: 'Run Once' },
  output: [{}]
});

const styleCharts = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Style + KPIs (Sheets API)',
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

const note = sticky(
  '## ISPL Dashboard Style & KPIs\nOne-shot. Adds data labels + ₹ currency formatting to the two charts, writes live "Today" KPI cells (I/J), formats them as ₹, and adds 3 scorecard charts (Today Receipts / Payments / Net). Run once only — re-running adds duplicate scorecards.',
  [manualTrigger, styleCharts],
  { color: 6 }
);

export default workflow('ispl-dashboard-style-kpis', 'ISPL Dashboard Style & KPIs')
  .add(manualTrigger)
  .to(styleCharts)
  .add(note);
