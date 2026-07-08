# Telegram / n8n bot helpers — Maharashtra FY2024-25

These files fix the *"data for May-24 is not available in the provided dataset"* error.
That error is **not** a data problem — every month (Apr-24 … Mar-25) is in the repo. It happens
when the n8n workflow feeds the model a **fixed slice** of data (one file / one month) instead of
**fetching the file for the month asked**. These helpers make the workflow resolve the right month.

## Files

| File | Use |
|---|---|
| **`bot_MONTHLY_SUMMARY_FY2024-25.csv`** | **The summary-bot data source.** 13-row month-wise summary (all 12 months + total, incl. May-24). Import this into the Google Sheet the "Read Salary Summary" node reads. Fixes "May-24 not available" for summary/totals questions. |
| `bot_dataset_below15k_ecr0_ALLMONTHS.csv` | 889-row all-months below-₹15k / ECR-PF=0 detail (for gap queries, if you want that class too). |
| `manifest.json` | Month → raw-file URLs (corrected sheet, gap-full, gap-part) for all 12 months + year files. Load once; look up by month key. |
| `month_router.js` | Drop-in **n8n Code node**: parses the month from the Telegram text ("May", "May-24", "May 2024", "05/2024", "2024005") → canonical key `MAY-24` + the exact URL to fetch (for the fetch-per-month architecture). |

## Summary-bot quick fix (matches the current workflow)

The bot's flow is **Telegram → Read Salary Summary (Google Sheet) → Bundle Rows → AI Answerer → Send Reply**.
It answers from whatever is in that one Google Sheet. To make **every month** answerable:

1. Open the Google Sheet the **"Read Salary Summary"** node reads.
2. **File → Import → Upload** `bot_MONTHLY_SUMMARY_FY2024-25.csv` → **Replace current sheet**.
3. Done — no workflow change. The sheet now has all 12 months (incl. May-24), so summary/totals
   questions for any month work.

Columns: `MONTH, EMPLOYEES, MATCHED_IN_ECR, NOT_IN_ECR, ORIG_SALARY_PF, ECR_PF_FILED,
REVISED_PF_=_ECR_CAPPED, PF_GAP, ABOVE_1800_SURPLUS, PF_PARKED_OTHER_DED,
BELOW15K_ECR0_TOTAL, BELOW15K_ECR0_FULLATT_GAP`.

## Recommended n8n flow

```
Telegram Trigger
      │  (message text)
      ▼
Code node  ← paste month_router.js       →  outputs { monthKey, wants, fetchUrl, ... }
      │
      ▼
HTTP Request  (GET {{$json.fetchUrl}})    →  the month's CSV (≈1,700 rows)
      │
      ▼
(optional) Filter / Code  — apply the query (e.g. Basic<15000 & REVISED_PF=0)
      │
      ▼
LLM / Set node  — summarise the rows
      │
      ▼
Telegram Send
```

The key change: the **HTTP Request** must fetch `{{$json.fetchUrl}}` **per request**, so the model
only ever sees the requested month's rows — never a stale fixed dataset.

## Why the bot said "May-24 not available"

The LLM node was given a dataset that didn't contain May. Either it was pinned to a single file
(e.g. only March), or the month→file mapping was missing so it fell back to whatever was loaded.
`month_router.js` guarantees `May → MAY-24 → CORRECTED_MAY-24.csv`, which has **1,713 employees**.

## Column reference (corrected sheet)

Key: `EMP CODE` (or `NAME`). Query fields: `ORIG_BASIC(+DA)`, `ECR_PF (EE, filed)`, `REVISED_PF`,
`RULE_APPLIED`, `NORMALDAYS (W/DAYS)`, `M/DAYS (divisor)`, `NCP`, `BD_MONTHLY_PROJECTION`,
`PF_DIFF_PARKED_IN_OTHER_DED`. Full list in `manifest.json`.

> Note: URLs point at the current default branch (`claude/n8n-food-log-meal-timing-Ezdh1`).
> If the default branch is renamed (e.g. to `main`), update `RAW_BASE` in `month_router.js` and
> `raw_base`/`branch` in `manifest.json`.
