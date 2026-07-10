# ISPL Bank Statement Loop

Daily automation that reads PC Jain's "DAILY BANK STATEMENT" email, extracts every
receipt and payment (excluding inter-bank transfers), classifies each line, and appends
it to the **ISPL Bank Statement Tracker** Google Sheet.

- **Owner:** dinesh@impressionsgroup.in
- **Source sender:** pcjain@impressionsgroup.in (PC Jain, Senior Manager – Finance & Accounts)
- **Cadence:** daily, 09:00 IST, Mon–Sat (PC Jain sends the statement ~07:30–08:30 IST)
- **Trigger command:**

```
/loop 9am check Gmail for today's daily bank statement from pcjain@impressionsgroup.in and extract all receipts and payments excluding inter-bank transfers, then append to ISPL Bank Statement Tracker Google Sheet. Follow the ISPL_BANK_STATEMENT_LOOP.md workflow exactly.
```

> **Run this workflow exactly as written below.** Steps are ordered; do not skip the
> inter-bank filter (Step 4) or the dedup check (Step 6).

---

## Prerequisites / configuration (fill in before first live run)

| Item | Value | Status |
|------|-------|--------|
| Google Sheet name | ISPL Bank Statement Tracker | ✅ created |
| Google Sheet ID | `1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc` | ✅ |
| Drive folder ("DAILY BANK STATEMENTS") | `129fqVeuWpUgwiSRNFkomywsLvUIsoVan` | ✅ |
| ISPL bank accounts (for inter-bank filter) | ICICI `039951000005`, DBS `858200061542`, SBI `SBIN0004xx`, Kotak (own-name credits) | ✅ confirmed from data |
| Pegasus Outsourcing Services LLP (IC-POSLLP) | **skipped** — separate legal entity, not tracked here | ✅ per instruction |
| Scheduling mechanism | **n8n Schedule Trigger** (workflow `Cv3IBhUaGD7DpHk7`) | ✅ built |

> **Source of today's data:** the statement did NOT arrive by email (PC Jain's
> 2026-06-16 mail said "HDFC SITE NOT WORKING"). The user placed the files in the
> Drive folder **DAILY BANK STATEMENTS**: `ICICI.xlsx`, `DBS.xlsx`, and
> `IC-POSLLP.xlsx` (Pegasus — skipped). So Step 2 has a Drive-folder fallback.

The Google Sheet ID is mandatory before the loop can append rows. Until it is provided,
the loop should run in **dry-run** mode: parse + classify + filter, then report the
extracted rows in chat instead of writing.

---

## Workflow

### Step 1 — Loop Trigger (09:00 IST daily)
Fires from the `/loop` command above. Each run handles **today's** statement only.

### Step 2 — Gmail Search
Locate today's statement from PC Jain. Search Gmail with:

```
from:pcjain@impressionsgroup.in subject:"DAILY BANK STATEMENT" newer_than:1d
```

Notes:
- The statement arrives as a reply within the long-running thread
  **"Re: DAILY BANK STATEMENT-FOR COLLECTION REPORT"**, addressed to
  `collection.report@impressionsgroup.in` and `billing7@impressionsgroup.in`.
- Some days the email is a **note, not a statement** (e.g. "HDFC SITE NOT WORKING").
  If there is no usable attachment / statement content → log
  **"No statement received"** with the reason, then exit gracefully (do not write rows).
- If multiple banks are sent as separate attachments, process each.

### Step 3 — Parse Statement
Read the PDF/Excel attachment(s) and the email body. For each transaction capture:

`Date · Narration · Mode (NEFT/RTGS/IMPS/CHQ/UPI) · Reference No · Debit · Credit · Balance · Party Name`

### Step 4 — Inter-Bank Filter (exclude internal transfers)
Drop any line that is a movement between ISPL's own accounts. Exclude when **any** rule matches:

1. Transfer between ISPL banks: **HDFC ↔ DBS ↔ SBI ↔ Axis**
2. Narration contains `SWEEP`, `FD BOOKING`, `OD ACCOUNT`, or `INTERNAL`
3. "Impressions Services" appears as **both** sender and receiver
4. Self-transfer / own-account keywords
5. Same-date, same-amount debit+credit pair across ISPL accounts

Excluded rows are **not** appended to Daily Transactions, but are flagged
(`Inter-Bank Excluded? = YES`) if logged for audit.

### Step 5 — Auto-Classify (tag each kept transaction)
| Tag | Match heuristic |
|-----|-----------------|
| Client Receipt | NEFT/credit from a client |
| Payroll / Statutory | `SALARY`, `ESI`, `EPF` |
| Vendor Payment | known supplier names |
| Rent | `RENT`, `LEASE` |
| Tax Payment | `GST`, `TDS`, `IT DEPT` |
| Bank Charges | `INTEREST`, `INT CHRG` |
| Review Required | unknown / unmatched narration |

### Step 6 — Write to Google Sheets (append + deduplicate)
- Sheet: **ISPL Bank Statement Tracker**
- Tab: **Daily Transactions** (15 columns, schema below)
- **Dedup on `Reference No`** — skip any row whose Reference No already exists.
- After appending, refresh the **Monthly Summary** tab totals.
- Record the run outcome in the **Run Log** tab.

---

## Google Sheet schema — tab "Daily Transactions"

| Col | Field | Notes |
|-----|-------|-------|
| A | Date | transaction date |
| B | Value Date | bank value date |
| C | Bank Account | which ISPL account |
| D | Narration | raw bank narration |
| E | Party Name | counterparty |
| F | Mode | NEFT / RTGS / IMPS / CHQ / UPI |
| G | Reference No | **dedup key** |
| H | Type | RECEIPT / PAYMENT |
| I | Debit ₹ | |
| J | Credit ₹ | |
| K | Balance ₹ | |
| L | Auto Tag | from Step 5 |
| M | Inter-Bank Excluded? | YES / NO |
| N | Source Email Date | date of PC Jain's email |
| O | Processed On | loop run timestamp |

### Other tabs
| Tab | Purpose |
|-----|---------|
| Monthly data tab — `"<Mon> <yyyy>"` (e.g. `"Jul 2026"`) | main data (15 cols). **One tab per calendar month** so every month starts afresh. **Referenced by NAME**, computed in IST at run time. |
| Dashboard | ✅ built — daily + cumulative figures (see below) for the **current month only**, rebuilt daily by the dashboard workflow |

> Originally-envisioned Monthly Summary / Run Log / Config tabs can be added later; the
> live figures the user asked for are delivered by the **Dashboard** tab.

---

## Monthly reset (fresh start each month)

From **July 2026** onward each calendar month is kept **separate** and **starts afresh**:

- **Data** — the loop writes into a **per-month tab** named `"<Mon> <yyyy>"` (e.g. `"Jul 2026"`,
  `"Aug 2026"`). The `Ensure Month Tab` node creates that tab on the 1st of the month (the
  "already exists" error is ignored on later days), and `Append To Tracker` upserts into it.
  Both the loop and the dashboard compute the tab name as
  `{{ $now.setZone('Asia/Kolkata').toFormat('LLL yyyy') }}`, so the rollover is automatic —
  no edit needed each month.
- **Dashboard** — the refresh reads **only the current month's tab**, so the daily rows and the
  running cumulative both reset to **₹0 on the 1st**. The single `Dashboard` tab (with its charts
  and KPI scorecards) is reused every month; only its data (`A:G`) is rebuilt, so nothing needs
  re-styling at rollover.

### One-time July 2026 cutover (do once, on/before 2026-07-01)
1. **Clear June out of the active tracker** — per the user's instruction, delete June's rows.
   Either delete the old first tab `"ISPL Bank Statement Tracker"` or clear its data rows
   (keep nothing from June in the live sheet). *(June is not archived.)*
2. **Create the `"Jul 2026"` data tab** with the 15-column header row (A–O):
   `Date · Value Date · Bank Account · Narration · Party Name · Mode · Reference No · Type ·
   Debit · Credit · Balance · Auto Tag · Inter-Bank Excluded? · Source Email Date · Processed On`.
   *(If you skip this, the loop's `Ensure Month Tab` node creates the tab automatically on the
   first July run; `appendOrUpdate` then writes the header row on first append.)*
3. **Re-deploy** the two updated workflows in n8n from `scripts/`:
   `ispl_bank_statement_loop.workflow.ts` and `ispl_bank_dashboard_refresh.workflow.ts`.
4. **Leave the `Dashboard` tab in place** — do **not** delete it. On the first July refresh it
   rebuilds from July data only (cumulative starts at ₹0); the charts/scorecards keep working.
5. **First July run** appends July transactions into `"Jul 2026"`; the Dashboard then shows only
   July figures. June numbers (₹2.04cr receipts etc.) no longer appear, as requested.

> The same automatic behaviour repeats every month after July — a fresh `"<Mon> <yyyy>"` tab and a
> reset dashboard — with no manual steps beyond the one-time deploy above.

## Dashboard

**Dashboard** tab (auto-maintained) — one row per date plus a `TOTAL` row:

| Col | Field |
|-----|-------|
| A | Date |
| B | Daily Receipts |
| C | Daily Payments |
| D | Daily Net |
| E | Cumulative Receipts |
| F | Cumulative Payments |
| G | Cumulative Net |

All figures **exclude inter-bank transfers** (`Inter-Bank Excluded? = NO` only).

Maintained by n8n workflow **ISPL Bank Dashboard Refresh** (`QrtxpYLVuedOPU0e`,
source `scripts/ispl_bank_dashboard_refresh.workflow.ts`): daily 09:15 it
**clears + rebuilds** the Dashboard tab from the **current month's data tab** (Schedule → Clear
Dashboard → Read current month tab → Build Daily + Cumulative (Code) → Write Dashboard). Because
it reads only the current month, the cumulative **resets to ₹0 on the 1st of each month**.

The June 2026 first run on 2026-06-16 populated it as below; from **July 2026** the Dashboard shows
**July figures only** (the June table is retained here for reference, not in the live sheet):

| Date | Daily Receipts | Daily Payments | Cumulative Net |
|------|---------------:|---------------:|---------------:|
| 2026-06-13 | 33,445.70 | 12,924.00 | 20,521.70 |
| 2026-06-14 | 3,00,389.39 | 0.00 | 3,20,911.09 |
| 2026-06-15 | 1,98,12,707.69 | 22,19,888.00 | 1,79,13,730.78 |
| 2026-06-16 | 3,22,470.16 | 0.00 | 1,82,36,200.94 |
| **TOTAL** | **2,04,69,012.94** | **22,32,812.00** | **1,82,36,200.94** |

### Charts (native, embedded in the Dashboard tab)
Two interactive Google Sheets charts were added via the Sheets API (`spreadsheets.batchUpdate`
→ `addChart`), called from an n8n HTTP Request node using the Google Sheets OAuth credential:

- **Column** — "ISPL — Daily Receipts vs Payments" (Daily Receipts green, Daily Payments red).
- **Line (smoothed)** — "ISPL — Cumulative Receipts, Payments & Net" (green / red / blue).

Built by one-shot workflow **ISPL Bank Dashboard Charts** (`YDBoXgV2kUa4QeOh`, source
`scripts/ispl_bank_dashboard_charts.workflow.ts`). Charts persist and auto-update as the
Dashboard data is rebuilt daily — **run this workflow only once** (re-running adds duplicate
charts). The n8n Google Sheets node cannot create charts, hence the HTTP/Sheets-API approach.

### Styling + KPI scorecards
One-shot workflow **ISPL Dashboard Style & KPIs** (`xk5S0HhZD9FjKWcC`, source
`scripts/ispl_dashboard_style_kpis.workflow.ts`) — applied on 2026-06-16:
- **Data labels** on every series of both charts.
- **₹ currency formatting** on the data cells (B:G) → axis, tooltips and labels show ₹.
- Live **"Today" KPI cells** in `I/J` (col J = `=LOOKUP(2,1/(col<>""),col)` → latest day's value).
- **3 scorecard charts** (`Today's Receipts` `699728460`, `Today's Payments` `89391805`,
  `Today's Net Cash Flow` `448051791`) reading those KPI cells.

> Because the KPI cells live in column J, the **daily refresh now clears only `A:G`**
> (not the whole sheet) so the KPI formulas and scorecards survive. Run the Style & KPIs
> workflow **once only** — re-running adds duplicate scorecards.

---

## Scheduling

The `/loop` skill expects a `9am` daily fire. **Note:** a Claude Code *web* session
cannot self-schedule a daily wake (no cron/wakeup primitive in that environment). Pick
one durable mechanism:

1. **n8n Schedule Trigger** ✅ **BUILT** — workflow **ISPL Bank Statement Loop**
   (`Cv3IBhUaGD7DpHk7`). Source committed at
   `scripts/ispl_bank_statement_loop.workflow.ts`.
   - Flow: `Daily 9AM Trigger` → `Find Today Statement Files` (Drive folder, modified today)
     → `Keep ICICI & DBS Only` (filter; Pegasus excluded) → `Loop Over Statement Files`
     → `Download` → `Extract Rows From XLSX` → `Parse Classify Filter` (Code: the same
     parsing/inter-bank/classification logic as `build_bank_tracker.py`) → `Append To
     Tracker` (Google Sheets upsert on **Reference No**).
   - Credentials: Google Drive `X6ONNTZzVhhKFi37`, Google Sheets `MzcFHNlXKDc9lIZ0`.

   Paired with **ISPL Bank Dashboard Refresh** (`QrtxpYLVuedOPU0e`) at 09:15 — see Dashboard
   section. (The dashboard workflow has been test-run successfully; it reads the data tab by
   name and rebuilds the Dashboard tab.)

   **Before relying on the main loop — two manual steps:**
   1. **Activate** both workflows in n8n (created inactive). Run the main loop once manually to
      confirm the `Extract from File` output shape (the data-tab reference is already fixed to
      use the tab **name**, verified working in the dashboard workflow).
   2. **Timezone:** `triggerAtHour` fires in the **n8n instance timezone**. If the instance runs
      UTC, set the instance/workflow TZ to `Asia/Kolkata` (or change the hour) so the loop fires
      at 9 AM IST and the dashboard at 9:15 AM IST.
2. **Claude Code scheduled session / trigger** configured in the web UI, re-running the
   `/loop` command each morning.
3. **Manual** — run the `/loop` command each morning from the terminal.

---

## Run Log

| Date (IST) | Status | Rows added | Notes |
|------------|--------|-----------|-------|
| 2026-06-16 | Processed (Drive fallback) | 124 (118 external + 6 inter-bank flagged) | Email had no attachment ("HDFC SITE NOT WORKING"); files taken from Drive folder. ICICI + DBS only; Pegasus skipped. Receipts ₹2,04,69,012.94, Payments ₹22,32,812.00 (excl. inter-bank). 6 inter-bank excluded: ICICI FUND120626B ₹1.5cr & FUND130626 ₹44,728 & INFT own-name ₹5,61,725.26; DBS Kotak own-name ₹8,51,328.86 & 2× DBS→SBI ₹3.5cr/₹50L. |
| 2026-06-30 | Monthly-reset config | — | Switched the loop + dashboard to **per-month tabs** so July starts afresh (see "Monthly reset" above). From 2026-07-01 data lands in tab `"Jul 2026"` and the Dashboard cumulative resets to ₹0. June to be cleared from the live sheet per instruction. Requires re-deploying both workflows in n8n. |
| 2026-07-02 | Fixes deployed | — | Four fixes after the first live month-rollover — see **"Fixes (2026-07-02)"** below. |
| 2026-07-10 | INFT client-receipt fix | — | ICICI `INF/INFT` credits are no longer blanket-excluded as inter-bank — see **"Fix (2026-07-10)"** below. 6 July rows (₹67,13,012 total: Snow White ×3, Elite Metaliks, Bengal Ultimate, Clinikally) need the one-time in-sheet correction listed in `docs/bank-tracker-inft-client-receipt-correction.md`. Requires re-deploying the loop workflow in n8n. |

### Fixes (2026-07-02)
1. **Month tab name is the FULL month** — `toFormat('LLLL yyyy')` → `"July 2026"`, `"August 2026"` (not the abbreviated `"Jul 2026"`; the live tab was created with the full name, so the abbreviation caused a "sheet not found").
2. **Bank detection by header cell, not account number.** A statement can cite *another* bank's account number inside a transfer narration (the HDFC file cites ICICI's `039951000005`, and ICICI cites HDFC's), so the old `flat.includes(<number>)` test misdetected and dropped whole files (HDFC → misread as ICICI → 0 rows). Now detected by the unique header cell, in order: ICICI `Tran. Id`/`S.N.` → KOTAK `Sl. No.`/`Dr / Cr` → HDFC `Transaction Date` → DBS. (ICICI/HDFC/KOTAK all have a `Transaction Date` column, hence the strict order.)
3. **`Move To Processed` runs AFTER the append** (flow: Download → Extract → Parse → Append → Move, `executeOnce`, errors tolerated). Previously the file was moved to the *Processed* folder *before* import, so a failed run relocated statements without ever saving their rows. Now a file only leaves the folder once its data is written; on failure it stays for the next run.
4. **Loan-reversal / DD-cancellation exclusion** in the Dashboard and both client-receipts workflows: rows whose narration contains `LOAN PAYMENT REVERSAL` or `DD CANCLN` are bank credits, not client money, and are excluded from receipts (they had inflated the headline by ~₹10 cr).

New companion workflow **ISPL Client Receipts (Monthly)** (`eMfGJ6cGzOt4VLaj`, source `scripts/ispl_client_receipts_monthly.workflow.ts`): daily 09:50, rebuilds the **Client Receipts** tab — receipts aggregated by client for the current month (same exclusions), ranked, with a TOTAL row.

### Fix (2026-07-10) — INFT credits are not always inter-bank
The ICICI parser hardcoded Party Name to `IMPRESSIONS SERVICES PVT LTD (own)` for every
`INF/INFT` (ICICI-to-ICICI internal transfer) row, so the inter-bank rule excluded **all**
INFT receipts — including genuine client payments sent from the client's own ICICI account.
In July 1–10 this wrongly excluded ₹67,13,012 of client receipts (Snow White Technologies ×3,
Elite Metaliks, Bengal Ultimate, Clinikally), overstating the month's deficit by the same
amount (₹12.13 cr → ₹11.46 cr corrected).

The parser now extracts the counterparty from the INFT narration segments
(`INF/INFT/<tranId>/<remark>/<party>[/NA]`, new `partyInft()` helper) and only excludes the
row when the party (or the TRFD/FUND rules) shows it is genuinely ISPL's own account.
One-time correction of the six already-written July rows: see
`docs/bank-tracker-inft-client-receipt-correction.md`.

### Review flags for 2026-06-16
- **63 ICICI "CMS/<id>/<9-digit>" debits** are tagged `CMS Settlement / Review Required` — the
  narration carries only numeric codes (no counterparty), so party/classification need a human
  pass. They are kept (not inter-bank) unless confirmed otherwise.
- The ICICI **INFT to "IMPRESSIONS SERVICES PVT LTD"** (₹5,61,725.26) was treated as an own-account
  internal transfer and excluded; confirm if it is actually an external receipt.

### Known limitations of this load
- The tracker was created as a **single-tab CSV import** (Daily Transactions only). The
  Monthly Summary / Run Log / Config tabs in the schema above still need to be added in-sheet,
  and true append+dedup on future runs needs a Google Sheets write tool or the n8n workflow.
