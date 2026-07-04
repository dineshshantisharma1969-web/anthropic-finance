# SKILL PATCH — Rule M16: Excess-Salary Projection-Artifact Fix

> Paste into the `pf-salary-reconciliation` skill / fold into the pipeline that computes
> `EXCESS_SALARY` and `ACTION_NEEDED`. Verified on April-2026 (2026-07-04).

## Problem

The excess-salary detector projects each row to a full month
(`gross × FULL_MONTH / days`-style). For rows with **NORMALDAYS ≤ 2** (mid-month
joiners/leavers), the tiny divisor explodes the projection: employees paid ₹500–800
for 1 day were flagged with ₹4–7 **lakh** "excess". In April-2026 this inflated the
flagged total to ₹5.55 Cr, of which ₹3.6 Cr was mathematically impossible
(flagged excess exceeded total pay).

## Rule M16 (two parts)

**M16a — Cap:** `EXCESS_SALARY = min(EXCESS_SALARY, GROSS AMT)` on every row.
Real cash overpayment can never exceed what was actually paid. Preserve the raw
value in `EXCESS_SALARY_UNCAPPED`.

**M16b — Suppress:** if `ACTION_NEEDED = 'Y'` and `NORMALDAYS ≤ 2` and the reason
is the LOW-ATTENDANCE projection flag → set `ACTION_NEEDED = 'N'` and append
`[M16_ARTIFACT_LOW_DAYS]` to `ACTION_REASON`. These rows are projection artifacts,
not overpayments. Audit trail goes in a `RECON_FLAG_M16` column
(`M16a_CAPPED_AT_GROSS;M16b_SUPPRESSED_LOW_DAYS`).

**Invariant:** M16 touches ONLY `EXCESS_SALARY / ACTION_NEEDED / ACTION_REASON`
(+ the two new audit columns). PF, ESI, GROSS, NET, days and every golden-rule
column are untouched — verify `Σ REVISED_PF = ECR_PF` and `NET drift = 0`
after applying (April-26: PASS).

## April-2026 result (verified)

| Metric | Before | After M16 |
|---|--:|--:|
| Rows capped (M16a) | — | 575 |
| Flags suppressed (M16b) | — | 199 |
| Total EXCESS_SALARY | ₹5,55,36,280 | **₹1,93,64,573** |
| ACTION_NEEDED = Y rows | 4,974 | 4,775 |
| Flagged excess (Y rows) | ₹5,44,58,591 | **₹1,90,87,229** |
| Σ REVISED_PF = ECR_PF | ₹2,52,21,042 / gap 0 | unchanged ✅ |
| NET drift | 0 | 0 ✅ |

## How to apply to any month

```
python patch_excess_artifact_M16.py <Month_RECONCILED.xlsx> <Month_RECONCILED_M16.xlsx>
```
(script beside this file; needs `pip install openpyxl`). Or implement M16a/M16b
directly in the step that computes `EXCESS_SALARY` so future builds are born clean.
