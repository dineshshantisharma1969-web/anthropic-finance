# One-time correction — July 2026 rows misclassified as inter-bank

> **✅ APPLIED 2026-07-10 (evening).** All 15 rows were updated in the live sheet via the
> one-off n8n workflow **ISPL One-off: July 2026 INFT + SBI Corrections** (`nAdoD8cpRDRuObsj`,
> execution 5997), matching on `Txn Key`. The LIVE loop workflow (`hqrLbu8oBQxIURU3`) was
> patched with both classifier fixes and republished (active version `b90c064b`). The
> Dashboard (`tqYOP2Rvgc9kI43F`, execution 5998) and Client Receipts (`eMfGJ6cGzOt4VLaj`,
> execution 5999) refreshes were run and verified: cumulative net July 1–10 now reads
> **−₹24.71 cr** (receipts ₹16.59 cr / payments ₹41.30 cr). This document is kept as the
> audit record; no further action needed.

**Sheet:** [ISPL Bank Statement Tracker](https://docs.google.com/spreadsheets/d/1P76gniXRPX01Hhaizga1xxd-TjBT2-jMfHM_KGRtpRc/edit) · **Tab:** `July 2026`

Two classifier defects (both fixed in `scripts/ispl_bank_statement_loop.workflow.ts` on
2026-07-10) left 15 rows in the sheet with the wrong `Inter-Bank Excluded?` flag. Rows
already written need the one-time edits below. Row numbers are as of 2026-07-10; if the
loop has appended since, match on **Reference No** (column G). The Dashboard and Client
Receipts tabs are rebuilt daily by the refresh workflows, so they pick up the corrections
on their next 09:45/09:50 run — no manual edit needed there.

## Correction 1 — INFT client receipts (6 rows, ₹67,13,012)

The ICICI parser hardcoded the party of every `INF/INFT` (ICICI-to-ICICI) credit as ISPL's
own account, excluding genuine client payments made from the client's own ICICI account.

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

## Correction 2 — payments to the SBI compliance account (9 rows, ₹13.25 cr)

The SBI account `31024290656` (SBIN0004449) is used **only for compliance payments**
(GST / TDS / PF / ESI), so sweeps into it are real outflows, not internal transfers.
Receipts coming back **from** SBI (₹17.88 cr in July 1–10) are WCDL/limit drawdowns —
funding — and correctly stay excluded.

For each row set: **Auto Tag** (col L) = `Compliance Payment (SBI)` ·
**Inter-Bank Excluded?** (col M) = `NO`.

| Sheet row | Date | From account | Reference No | Debit ₹ |
|-----------|------------|-----------|-----------|-------------:|
| 62 | 2026-07-01 | DBS | 0811OP6176672079 | 1,50,00,000 |
| 674 | 2026-07-06 | DBS | 0811OP6176967017 | 2,00,00,000 |
| 675 | 2026-07-06 | DBS | 0811OP6176966982 | 3,00,00,000 |
| 676 | 2026-07-06 | DBS | 0811OP6176966989 | 75,00,000 |
| 1144 | 2026-07-07 | DBS | 0811OP6177069413 | 1,00,00,000 |
| 1903 | 2026-07-07 | IDFC | IDFBR62026070703563603 | 1,00,00,000 |
| 1883 | 2026-07-08 | DBS | 0858OI6008875984 | 1,00,00,000 |
| 1884 | 2026-07-08 | DBS | 0858OI6008876856 | 1,40,00,000 |
| 1885 | 2026-07-08 | DBS | 0858OI6008876855 | 1,60,00,000 |
| | | | **Total** | **13,25,00,000** |

> **UPDATE 2026-07-10:** the IDFC row (`IDFBR62026070703563603`, ₹1 cr) was **confirmed by
> the user as a payment to a director** (Bikram Singh Chadha), not an SBI compliance sweep.
> It has been re-tagged `Director Payment` with Party Name "BIKRAM SINGH CHADHA (Director)"
> (execution 6001). It remains a real payment (`Inter-Bank Excluded? = NO`), so the deficit
> is unchanged at ₹24.71 cr; only the SBI-compliance bucket drops from ₹13.25 cr to ₹12.25 cr.
> The loop classifier now carries a `DIRECTOR_NAMES` guard so future director payments are
> tagged correctly and never counted as SBI compliance or inter-bank.

## Effect on July 1–10 headline numbers

| Metric | As displayed | After both corrections |
|--------|-------:|------:|
| Receipts MTD | ₹15.92 cr | ₹16.59 cr |
| Payments MTD | ₹28.05 cr | ₹41.30 cr |
| Cumulative deficit | ₹12.13 cr | **₹24.71 cr** |
| WCDL interest @7.9% p.a., Jul 1–10 | ₹1,17,066 | ₹2,40,136 |
| Interest run-rate at current deficit | ₹26,254/day | ₹53,478/day (~₹16 lakh/month) |

Funding of the corrected ₹24.71 cr deficit: **₹17.88 cr** WCDL/limit drawdowns from SBI
into the tracked accounts + **~₹6.8 cr** drawdown of balances/OD in the tracked accounts.

## Deployment

1. Re-deploy **ISPL Bank Statement Loop** (`Cv3IBhUaGD7DpHk7`) in n8n from
   `scripts/ispl_bank_statement_loop.workflow.ts` so future rows classify correctly.
2. Apply the 15 row edits above (n8n Google Sheets update matching on `Reference No`, or
   manually in the sheet).
3. Let the 09:45 Dashboard refresh / 09:50 Client Receipts run rebuild the summary tabs, or
   trigger them once manually.
