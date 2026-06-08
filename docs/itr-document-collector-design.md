# Design: Automated ITR Document Collector & Summary

> **Status:** Design for review — nothing has been built in n8n yet.
> **Author:** Automated tax workflow task
> **Date:** 2026-06-08
> **Target filing:** AY 2026–27 (FY 2025–26). ITR due date for non-audit individuals: **31 Jul 2026.**

## 1. Goal & scope

Automatically **collect the source documents needed to file an Indian income-tax
return** as they arrive by email, file them neatly, track them against a
master checklist, and **notify** you per-document plus a periodic "what's still
missing" summary.

This is deliberately distinct from the existing **INCOMETAX NOTICE TRACKER** /
GST workflows, which track *notices/proceedings from the department*. This new
workflow tracks the *inputs you need to prepare the return* (Form 16, interest
certificates, capital-gains statements, 80C/80D proofs, etc.).

### In scope (chosen requirements)
- **Collect tax documents** — scan incoming Gmail, identify ITR-relevant
  documents, save attachments to Google Drive, label the email.
- **Summary & notifications** — Telegram alert per document + a weekly digest of
  collected vs. missing items.

### Trigger (chosen)
- **New email arrives** (Gmail Trigger, polling). Event-driven — runs whenever a
  matching email lands.

### Out of scope (explicitly not built)
- Computing tax liability or auto-filing the return.
- Reading Form 26AS / AIS directly from the income-tax portal (those are not
  emailed; they are downloaded after portal login — can be a later add-on).

## 2. The master ITR document checklist

The workflow recognises and tracks these document categories. Each maps to a
Drive sub-folder, a tracker row, and a set of email match rules.

| # | Document | Why it's needed | Typical sender / cue |
|---|----------|-----------------|----------------------|
| 1 | **Form 16** (Part A & B) | Salary + TDS by employer | Employer payroll / HR |
| 2 | **Form 16A** | TDS on non-salary (interest, professional) | Banks, payers |
| 3 | **Bank interest certificate** | Interest income (savings/FD) | Bank statements team |
| 4 | **Capital gains statement – equity/MF** | STCG/LTCG | Kotak Securities, CAMS, KFintech, Zerodha |
| 5 | **Dividend statement** | Dividend income | Brokers, registrars |
| 6 | **Home loan interest certificate** | Sec 24(b) deduction | Housing finance / bank |
| 7 | **80C proofs** | LIC, ELSS, PPF, tuition, principal | Insurers, AMCs, bank |
| 8 | **80D proof** | Health insurance premium | Health insurers |
| 9 | **80G donation receipts** | Donations | NGOs / trusts |
| 10 | **Rent receipts / HRA** | HRA exemption | Landlord / self |
| 11 | **Form 26AS / AIS / TIS** | Pre-filled TDS & income data | (portal — manual upload) |
| 12 | **Other / misc** | Anything tax-flagged but unmatched | — |

> The checklist is data, not code — it lives in a Google Sheet tab (`Checklist`)
> so you can add/remove rows without touching the workflow.

## 3. Architecture

```
                         ┌──────────────────────────────────────────┐
   New email  ──────────▶│ 1. Gmail Trigger (poll every 1–2 min)     │
                         └──────────────────────────────────────────┘
                                          │  (email + attachments)
                                          ▼
                         ┌──────────────────────────────────────────┐
                         │ 2. Pre-filter (IF/Code)                   │
                         │    cheap keyword/sender gate              │
                         └──────────────────────────────────────────┘
                            │ match                     │ no match
                            ▼                           ▼
            ┌────────────────────────────┐         ( stop — ignore )
            │ 3. AI Classifier+Extractor │
            │    (OpenAI / Anthropic)    │
            │    → {category, AY,        │
            │       issuer, amount,      │
            │       is_tax_doc}          │
            └────────────────────────────┘
                            │ is_tax_doc = true
                            ▼
            ┌────────────────────────────┐
            │ 4. Has attachment? (IF)    │
            └────────────────────────────┘
                 │ yes              │ no
                 ▼                  ▼
      ┌────────────────────┐   (skip Drive save,
      │ 5. Save to Drive   │    still log + notify)
      │  /ITR/AY2026-27/<cat>│
      └────────────────────┘
                 │
                 ▼
      ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
      │ 6. Label email     │──▶│ 7. Append to       │──▶│ 8. Telegram alert  │
      │  "ITR 2026-27"     │   │    tracker Sheet   │   │  per document      │
      └────────────────────┘   └────────────────────┘   └────────────────────┘


   ── Separate scheduled sub-workflow (weekly digest) ──
                         ┌──────────────────────────────────────────┐
   Mon 09:00 IST ──────▶│ A. Schedule Trigger                       │
                         └──────────────────────────────────────────┘
                                          ▼
                         ┌──────────────────────────────────────────┐
                         │ B. Read tracker + checklist (Sheets)      │
                         │ C. Diff → collected vs missing            │
                         │ D. Telegram digest ("5/12 collected …")   │
                         └──────────────────────────────────────────┘
```

## 4. Node-by-node design (collector workflow)

| Node | Type | Configuration |
|------|------|---------------|
| 1. Gmail Trigger | `n8n-nodes-base.gmailTrigger` | Event: *message received*. Poll every 1 min. **Download attachments = on.** Optionally filter `Q` to inbox only. |
| 2. Pre-filter | `n8n-nodes-base.if` (or `code`) | Cheap gate before spending an AI call. Pass if subject/from/snippet matches a keyword set (form 16, tds, interest certificate, capital gain, 80c, 80d, 80g, premium, donation, home loan, demat, AIS, 26AS, dividend, rent receipt). Known senders (e.g. Kotak Securities) auto-pass. |
| 3. AI Classify+Extract | `@n8n/n8n-nodes-langchain.openAi` *or* `anthropic` | Input = subject + from + body snippet + attachment filename(s). Output strict JSON (see §7). Use a cheap model; temperature 0. |
| 4. Has attachment? | `n8n-nodes-base.if` | Branch on whether the Gmail binary has ≥1 attachment. No-attachment emails still get logged + notified. |
| 5. Save to Drive | `n8n-nodes-base.googleDrive` | Upload each attachment to `/ITR/AY2026-27/<category>/`. Filename: `<category>_<issuer>_<received-date>_<originalName>`. |
| 6. Label email | `n8n-nodes-base.gmail` (add label) | Apply label **`ITR 2026-27`** (new). Keeps existing *"Income tax notices"* label reserved for notices. |
| 7. Append tracker | `n8n-nodes-base.googleSheets` (append) | One row per document into `Documents` tab (schema in §6). |
| 8. Telegram alert | `n8n-nodes-base.telegram` | Per-document message (format in §8). |

Recommended hardening (optional nodes): a **dedupe** check (Code or Sheets
lookup on Gmail `messageId`) before append, and a **Sticky Note** documenting
the match rules for future you.

## 5. Google Drive structure

```
ITR/
└── AY2026-27/
    ├── 01-Form16/
    ├── 02-Form16A/
    ├── 03-Bank-Interest/
    ├── 04-Capital-Gains/
    ├── 05-Dividends/
    ├── 06-Home-Loan-Interest/
    ├── 07-80C/
    ├── 08-80D/
    ├── 09-80G-Donations/
    ├── 10-HRA-Rent/
    ├── 11-26AS-AIS/
    └── 12-Misc/
```

## 6. Google Sheet: tracker schema

**Spreadsheet:** `ITR Document Tracker` (new). Two tabs.

`Documents` tab (append-only log, one row per received document):

| Column | Example |
|--------|---------|
| `received_at` | 2026-06-08 14:02 IST |
| `assessment_year` | AY2026-27 |
| `category` | 01-Form16 |
| `issuer` | ACME Corp |
| `amount` | 1450000 |
| `email_from` | hr@acme.com |
| `email_subject` | Form 16 for FY 2025-26 |
| `gmail_message_id` | 18f… (dedupe key) |
| `drive_link` | https://drive.google.com/… |
| `status` | Received |

`Checklist` tab (the master list from §2, editable). Columns: `category`,
`label`, `required` (Y/N), `expected_count`. The weekly digest diffs
`Documents` against this.

## 7. AI classifier contract

**System prompt (essence):** "You classify incoming emails for Indian income-tax
return preparation (AY 2026-27). Return only JSON."

**Output JSON:**
```json
{
  "is_tax_doc": true,
  "category": "01-Form16",
  "assessment_year": "AY2026-27",
  "issuer": "ACME Corp",
  "amount": 1450000,
  "confidence": 0.93,
  "reason": "Subject says 'Form 16 FY 2025-26', PDF attached"
}
```
- `category` must be one of the §2 codes or `12-Misc`.
- If `is_tax_doc` is false, the flow stops (no Drive/label/log).
- Low confidence (< 0.6) → route to `12-Misc` and flag in the Telegram alert so
  you can correct it manually.

## 8. Telegram notification formats

**Per-document alert:**
```
📄 ITR doc received — AY 2026-27
Type: Form 16 (salary TDS)
From: ACME Corp <hr@acme.com>
Amount: ₹14,50,000
Saved: Drive ▸ 01-Form16
Subject: Form 16 for FY 2025-26
```

**Weekly digest (Mon 09:00 IST):**
```
🗂️ ITR 2026-27 — document status (5/12)
✅ Collected: Form 16, Bank interest, 80C, 80D, Capital gains (Kotak)
⏳ Missing:   Form 16A, Home-loan interest, 80G, Dividends, HRA, 26AS/AIS, Form16(spouse?)
⏰ 53 days to the 31 Jul deadline.
```

## 9. Credentials to wire (from your n8n instance)

You have many of each type; the build step should confirm the exact ones. Likely picks:

| Purpose | Credential type | Candidate |
|---------|-----------------|-----------|
| Read mail + label | `gmailOAuth2` | one of *Gmail account …* (the mailbox that receives tax docs) |
| Save attachments | `googleDriveOAuth2Api` | *Google Drive account 4* (`G2zEKHaLjjQLWluh`) |
| Tracker sheet | `googleSheetsOAuth2Api` | a new sheet on any *Google Sheets account* |
| AI classify | `openAiApi` / `anthropicApi` | *open AI* (`DKHBJft11AwhANJu`) or *Anthropic account* (`GdaZxjTPFaY2AHce`) |
| Notify | `telegramApi` | *personal assistant* (`Poz89BTKUZKgvTAG`) — confirm chat ID |

> **Decision needed:** which Gmail mailbox and which Telegram bot/chat. (You have
> several Gmail accounts and bots like *personal assistant*, *dinub4u_bot*.)

## 10. Edge cases & decisions

- **Dedupe:** key on `gmail_message_id`; skip if already in `Documents`. Prevents
  double-logging when the Gmail trigger re-sees a thread.
- **Multiple attachments / multiple docs per email:** iterate attachments; one
  Drive file + one tracker row each, all linked to the same `gmail_message_id`.
- **Password-protected PDFs** (banks/brokers often send these): the AI can still
  classify from subject/filename; note in the alert that the file may be locked.
  Auto-unlock is out of scope.
- **Spouse / multiple filers:** if you file for more than one PAN, add a `filer`
  column and a label per person. *Decision needed.*
- **Privacy:** the AI step sees email subject/snippet/filenames (not necessarily
  full PDF contents). Keep it to a snippet to minimise data sent out; the
  Anthropic credential is available if you prefer it over OpenAI.

## 11. Open questions before build

1. Which **Gmail mailbox** receives your tax documents, and which **Telegram
   bot + chat** should get the alerts?
2. Are you filing for **one PAN or several** (self + spouse/family)?
3. OK to create a **new Gmail label `ITR 2026-27`**, a **new Drive folder tree**,
   and a **new tracker spreadsheet** — or reuse existing ones?
4. Prefer **OpenAI or Anthropic** for the classifier?
5. Want the **weekly digest** as a second (scheduled) workflow, or skip it and
   keep only per-document alerts?

---

### Next step
On your answers to §11, I'll build and validate the workflow(s) live in n8n
(SDK → validate → create), then add an implementation note to this repo like the
existing `food-log-meal-timing-fix.md`.
