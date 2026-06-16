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
| *(first tab)* "ISPL Bank Statement Tracker" | main data (15 cols) — the data tab. **Referenced by NAME**, not gid (a CSV-imported sheet's first tab is not gid 0). |
| Dashboard | ✅ built — daily + cumulative figures (see below), rebuilt daily by the dashboard workflow |

> Originally-envisioned Monthly Summary / Run Log / Config tabs can be added later; the
> live figures the user asked for are delivered by the **Dashboard** tab.

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
**clears + rebuilds** the Dashboard tab from Daily Transactions (Schedule → Clear
Dashboard → Read Daily Transactions → Build Daily + Cumulative (Code) → Write Dashboard).
First run on 2026-06-16 populated it:

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
