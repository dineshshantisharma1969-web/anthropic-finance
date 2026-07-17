# GST Notice Tracker — Second Brain Sync

Structured snapshot of the **GST NOTICE TRACKER — Impressions Services Pvt Ltd** maintained in Google Drive, synced into this repo so the data is queryable and version-tracked.

## Source

| | |
|---|---|
| Drive file | `GST notice tracker_Google Drive.xlsx` |
| Drive file ID | `1ySb1_B2z7YOjMchvn8lxZWNqpuqbprK5` (owner: akdash@impressionsgroup.in, folder *IMPRESSIONS SERVICES GST NOTICE TRACKER*) |
| Sheet used | `📋 All Notices` (consolidated across all state sheets) |
| Tracker last updated | 17-Jul-2026 03:01 AM |
| Synced to repo | 17-Jul-2026 |

## Files

- `all_notices.json` — all 34 cases as structured JSON (one object per case)
- `all_notices.csv` — same data as CSV

Fields per case: `State, DemandID, CaseID, CaseType, FY, IssueDate, DueDate, IGST, CGST, SGST, Interest, Penalty, LateFee, TotalDemand, AppealDeposited, FinalStatus, OrderStatus, Description, ISPLNotes, WayForward, Remarks, StatusAsOnDate`. Dates are normalised to `YYYY-MM-DD` where the sheet allowed it; amounts are INR.

## Snapshot summary (as of this sync)

- **Total cases:** 34 (31 pending, 3 completed; 9 under appeal)
- **Total demand:** ₹62.59 Cr (IGST ₹12.56 Cr, CGST ₹8.77 Cr, SGST ₹8.77 Cr, interest ₹9.96 Cr, penalty ₹22.36 Cr, late fee ₹16.5 L)
- **Appeal amount deposited:** ₹60.30 L

State-wise demand (₹):

| State | Cases | Demand |
|---|---|---|
| Haryana | 11 | 28,90,53,574 |
| Delhi | 6 | 20,29,85,538 |
| Uttar Pradesh | 2 | 4,82,86,636 |
| West Bengal | 4 | 3,94,36,576 |
| Maharashtra | 3 | 3,46,27,402 |
| Telangana | 2 | 85,35,414 |
| Tamil Nadu | 1 | 20,16,950 |
| Rajasthan | 1 | 5,46,060 |
| Karnataka | 1 | 2,64,092 |
| Himachal Pradesh | 1 | 1,21,220 |
| Kerala | 1 | 22,702 |
| Jharkhand | 1 | 9,816 |

## Raising queries through Telegram

The n8n workflow **“GST Notice Tracker Query Bot”** (workflow ID `PPBdXvLYmi7dDOjF`, active) answers questions in Telegram:

1. **Telegram Trigger** — receives your message.
2. **Download GST Notice Tracker** — downloads the *live* Drive xlsx (file ID above) on every question, so answers always reflect the current tracker, not this repo snapshot.
3. **Extract All Notices Sheet → Build Cases JSON** — parses the `📋 All Notices` sheet into the same case structure stored here.
4. **Answer Tracker Question** — Claude Sonnet 5 agent (with per-chat memory) answers from the case data.
5. **Send Telegram Reply** — plain-text reply, amounts in lakh/crore.

Just message the bot questions like *“which cases are overdue?”*, *“total demand for Haryana”*, or *“status of case ZD070824017152N”*.

> This repo snapshot is the version-tracked "second brain" copy for reference/analysis; the Telegram bot always reads the live Drive file, so no re-sync is needed for the bot to see tracker updates. Re-run a sync when you want the repo copy refreshed.
