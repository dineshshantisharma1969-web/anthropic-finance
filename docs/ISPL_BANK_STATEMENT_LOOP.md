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
| Scheduling mechanism | see "Scheduling" section | ⬜ decide |

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
| Daily Transactions | main data (15 cols) |
| Monthly Summary | auto-updated totals |
| Run Log | loop execution history (date, status, rows added, notes) |
| Config | bank names, account numbers, classification keywords |

---

## Scheduling

The `/loop` skill expects a `9am` daily fire. **Note:** a Claude Code *web* session
cannot self-schedule a daily wake (no cron/wakeup primitive in that environment). Pick
one durable mechanism:

1. **n8n Schedule Trigger** (recommended) — a `Schedule Trigger` (09:00 IST) →
   Gmail → parse → Sheets workflow, matching this spec. Consistent with the other
   ISPL automations in this repo.
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
