# ISPL Bank Statement Tracker — July 2026 reset (status & recovery)

**Tracker:** [ISPL Bank Statement Tracker](https://docs.google.com/spreadsheets/d/1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc/edit)
(Google Sheet, fed daily from the "DAILY BANK STATEMENT-FOR COLLECTION REPORT"
emails via the `DAILY BANK STATEMENTS` Drive folder; processed files move to
`DAILY BANK STATEMENTS/Processed`).

## State found on 3 Jul 2026

A July reset was run on **2 Jul 2026 (~12:58 UTC / 18:28 IST)** but it did not
complete cleanly:

| Tab | State |
|---|---|
| `ISPL Bank Statement Tracker` (main) | Rows 2–1337: 1,336 June rows **half-wiped** — Date, Value Date, Bank Account, Narration, Party Name, Mode, Reference No, Type and Balance cleared; Debit, Credit, Auto Tag, Inter-Bank Excluded?, Source Email Date, Processed On still present. Rows 1338–1385: 48 intact DBS rows appended after the wipe (36 dated 30 Jun, 12 dated 1–2 Jul). |
| `July 2026` | Clean — 135 rows covering 1–2 Jul across DBS / HDFC / ICICI / KOTAK. The 12 July DBS rows are **duplicated** here and in the main tab. |
| `Dashboard`, `Client Receipts`, `2026-07-01`, `2026-07-02`, `Client Lookup` | Created by the reset; static values (no formulas). |

June remnant totals (from the surviving columns): **658 debits = ₹36,31,80,522.51**
and **678 credits = ₹24,97,60,216.34** across source-email dates 16–30 Jun. The 36
intact DBS rows dated 30 Jun add debits ₹40,92,187.00 / credits ₹1,42,69,158.74.

## What was archived (this session)

Everything June-related still in the sheet was preserved to
[`docs/data/ISPL-Bank-Statement-Tracker-June-2026-Archive.xlsx`](data/ISPL-Bank-Statement-Tracker-June-2026-Archive.xlsx):

- **June Rows (remnant)** — the 1,336 half-wiped rows exactly as found.
- **DBS 30-Jun (full rows)** — the 36 intact June rows.
- **June Daily Summary** — debit/credit totals per source-email date.
- **Source Files (full detail)** — links to the 15 statement files still in the
  `Processed` Drive folder (batches of 24, 27, 29, 30 Jun), which hold full
  narration-level detail for those dates.

## Recovering full June detail (if needed)

The complete pre-wipe June data is in the sheet's revision history, which only a
human can restore: open the tracker → **File → Version history → See version
history** → pick any version **before 2 Jul 2026, 18:28 IST**. Copy the June rows
to a separate file, then return to the current version (or restore and redo the
reset per the checklist below).

## Finishing the July reset — manual checklist

1. *(Optional)* Recover full June detail via version history first (above).
2. In the **main tab**, delete rows **2–1337** (the half-wiped June remnants) and
   the **36 DBS rows dated 30-Jun-2026** below them (they are June transactions;
   they are preserved in the archive file).
3. Resolve the duplication: the 12 DBS rows dated 1–2 Jul exist in **both** the
   main tab and `July 2026`. Keep one source of truth — either the n8n workflow
   keeps appending to the main tab (then treat `July 2026` as a one-off snapshot),
   or repoint the workflow's Google Sheets append node to the `July 2026` tab and
   clear the main tab completely.
4. Move the leftover `KOTAK.xlsx` (2 Jul, still in `DAILY BANK STATEMENTS`) into
   `Processed` — its transactions are already in the tracker, and re-running the
   workflow on it would double-count them.
5. The 3 Jul statement batch (DBS/HDFC/ICICI/KOTAK, arrived 08:19 IST) had not
   been processed as of this check. If it hasn't appeared in the tracker by end of
   day, check the n8n workflow — the reset may have broken its sheet/tab binding.

## Monthly reset procedure going forward

At each month start: (1) duplicate the tracker (File → Make a copy) named
`ISPL Bank Statement Tracker – <Month> <Year> Archive` **before** touching rows;
(2) delete the finished month's rows from the append tab in one whole-row delete
(select rows → right-click → Delete rows — not a range clear, which is what left
half-wiped rows this time); (3) verify the next statement batch appends correctly.
