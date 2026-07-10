# One-time correction — INFT client receipts wrongly excluded (July 2026)

**Sheet:** [ISPL Bank Statement Tracker](https://docs.google.com/spreadsheets/d/1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc/edit) · **Tab:** `July 2026`

The daily loop excluded every ICICI `INF/INFT` credit as an inter-bank transfer because it
hardcoded the party as ISPL's own account. Six of those credits are genuine client receipts
(clients paying from their own ICICI accounts). The parser is fixed from 2026-07-10
(`scripts/ispl_bank_statement_loop.workflow.ts`); the six rows already written to the sheet
need this one-time edit.

## Rows to correct (match on Reference No, column G)

For each row set: **Party Name** (col E) as below · **Auto Tag** (col L) = `Client Receipt` ·
**Inter-Bank Excluded?** (col M) = `NO`.

| Sheet row | Date | Reference No | Credit ₹ | Party Name (col E) |
|-----------|------------|-----------|-------------:|--------------------|
| 13 | 2026-07-01 | S54391577 | 52,598.00 | CLINIKALLY DIGI |
| 286 | 2026-07-03 | S82545326 | 1,98,009.00 | ELITE METALIKS |
| 374 | 2026-07-04 | S87597515 | 48,48,836.00 | SNOW WHITE TECHNOLOG |
| 1207 | 2026-07-07 | S23126706 | 11,92,142.00 | SNOW WHITE TECHNOLOG |
| 1548 | 2026-07-08 | S37814000 | 2,54,415.00 | BENGAL ULTIMATE |
| 1634 | 2026-07-08 | S37962726 | 1,67,012.00 | SNOW WHITE TECHNOLOG |
| | | **Total** | **67,13,012.00** | |

Row numbers are as of 2026-07-10; if the loop has appended since, match on Reference No.
The Dashboard and Client Receipts tabs are rebuilt daily by the refresh workflows, so they
pick up the corrections on their next 09:45/09:50 run — no manual edit needed there.

## Effect on July 1–10 headline numbers

| Metric | Before | After correction |
|--------|-------:|------:|
| Receipts MTD | ₹15.92 cr | ₹16.59 cr |
| Payments MTD | ₹28.05 cr | ₹28.05 cr |
| Cumulative deficit | ₹12.13 cr | ₹11.46 cr |
| WCDL interest @7.9% p.a., Jul 1–10 | ₹1,17,066 | ₹1,08,034 |
| Interest run-rate at current deficit | ₹26,254/day | ₹24,800/day |

## Deployment

1. Re-deploy **ISPL Bank Statement Loop** (`Cv3IBhUaGD7DpHk7`) in n8n from
   `scripts/ispl_bank_statement_loop.workflow.ts` so future INFT client receipts classify
   correctly.
2. Apply the six row edits above (n8n Google Sheets update matching on `Reference No`, or
   manually in the sheet).
3. Let the 09:45 Dashboard refresh / 09:50 Client Receipts run rebuild the summary tabs, or
   trigger them once manually.
