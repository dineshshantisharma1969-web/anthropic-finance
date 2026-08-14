import { workflow, node, trigger, newCredential, sticky } from '@n8n/workflow-sdk';

const SHEET_ID = '1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc';
const DASH = 1061189248;

const src = (c0: number, c1: number) => ({ sourceRange: { sources: [{ sheetId: DASH, startRowIndex: 0, endRowIndex: 400, startColumnIndex: c0, endColumnIndex: c1 }] } });
const rgb = (r: number, g: number, b: number) => ({ rgbColor: { red: r, green: g, blue: b } });

const body = {
  requests: [
    {
      addChart: {
        chart: {
          spec: {
            title: 'ISPL — Daily Receipts vs Payments',
            titleTextFormat: { bold: true, fontSize: 14 },
            basicChart: {
              chartType: 'COLUMN',
              legendPosition: 'BOTTOM_LEGEND',
              headerCount: 1,
              axis: [
                { position: 'BOTTOM_AXIS', title: 'Date' },
                { position: 'LEFT_AXIS', title: 'Amount (INR)' }
              ],
              domains: [{ domain: src(0, 1) }],
              series: [
                { series: src(1, 2), targetAxis: 'LEFT_AXIS', colorStyle: rgb(0.055, 0.624, 0.431) },
                { series: src(2, 3), targetAxis: 'LEFT_AXIS', colorStyle: rgb(0.878, 0.141, 0.141) }
              ]
            }
          },
          position: { overlayPosition: { anchorCell: { sheetId: DASH, rowIndex: 1, columnIndex: 8 }, offsetXPixels: 5, offsetYPixels: 5, widthPixels: 680, heightPixels: 340 } }
        }
      }
    },
    {
      addChart: {
        chart: {
          spec: {
            title: 'ISPL — Cumulative Receipts, Payments & Net',
            titleTextFormat: { bold: true, fontSize: 14 },
            basicChart: {
              chartType: 'LINE',
              legendPosition: 'BOTTOM_LEGEND',
              headerCount: 1,
              lineSmoothing: true,
              axis: [
                { position: 'BOTTOM_AXIS', title: 'Date' },
                { position: 'LEFT_AXIS', title: 'Cumulative (INR)' }
              ],
              domains: [{ domain: src(0, 1) }],
              series: [
                { series: src(4, 5), targetAxis: 'LEFT_AXIS', colorStyle: rgb(0.055, 0.624, 0.431) },
                { series: src(5, 6), targetAxis: 'LEFT_AXIS', colorStyle: rgb(0.878, 0.141, 0.141) },
                { series: src(6, 7), targetAxis: 'LEFT_AXIS', colorStyle: rgb(0.102, 0.337, 0.859) }
              ]
            }
          },
          position: { overlayPosition: { anchorCell: { sheetId: DASH, rowIndex: 20, columnIndex: 8 }, offsetXPixels: 5, offsetYPixels: 5, widthPixels: 680, heightPixels: 340 } }
        }
      }
    }
  ]
};

const manualTrigger = trigger({
  type: 'n8n-nodes-base.manualTrigger',
  version: 1,
  config: { name: 'Run Once' },
  output: [{}]
});

const addCharts = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Add Charts (Sheets API)',
    parameters: {
      method: 'POST',
      url: 'https://sheets.googleapis.com/v4/spreadsheets/' + SHEET_ID + ':batchUpdate',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'googleSheetsOAuth2Api',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: JSON.stringify(body)
    },
    credentials: { googleSheetsOAuth2Api: newCredential('Google Sheets account', 'MzcFHNlXKDc9lIZ0') }
  },
  output: [{ replies: [{ addChart: { chart: { chartId: 1 } } }] }]
});

const note = sticky(
  '## ISPL Bank Dashboard Charts\nOne-shot: adds two native charts to the Dashboard tab via the Sheets API batchUpdate (addChart) — a COLUMN chart (daily receipts vs payments) and a smoothed LINE chart (cumulative receipts/payments/net). Run once; charts persist and auto-update as the Dashboard data is rebuilt.',
  [manualTrigger, addCharts],
  { color: 3 }
);

export default workflow('ispl-bank-dashboard-charts', 'ISPL Bank Dashboard Charts')
  .add(manualTrigger)
  .to(addCharts)
  .add(note);
