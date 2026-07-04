# SKILL PATCH — Rule M17: Monthly Recovery & ESI Worklist (summary sheet)

> Paste into the `pf-salary-reconciliation` SKILL.md. Runs AFTER Rule M16.
> Verified on April-2026 (2026-07-04).

## Purpose

After each month's reconciliation + M16, produce **one working Excel file** that the
payroll team can action directly — no filtering or analysis needed. The two
workstreams that always need human decisions are:

1. **Recovery review** — employees paid above their fixed rate (net of OT/attendance
   allowance), M16 cash-capped.
2. **ESI enrollment** — employees flagged ESI-exempt whose real full-month rate is
   ≤ ₹21,000 (must be enrolled; exposure = 4% of gross per month: EE 0.75% + ER 3.25%).

## Output: `<Mon>_WORKLIST_Recovery_ESI.xlsx` — three tabs

| Tab | Contents | Working columns (to be filled by team) |
|---|---|---|
| **SUMMARY** | Headline counts/amounts + by-client top-10 for both workstreams | — |
| **RECOVERY_REVIEW** | All overpaid-vs-rate rows, sorted biggest-first; **HIGH priority (> ₹10k) highlighted red and on top**. Shows fixed gross vs actual gross, OT and attendance allowance (so legit variable pay is visible), and `EXCESS_TO_REVIEW` (M16-capped) | `VERIFIED (Y/N)` · `DECISION (RECOVER/WAIVE/JUSTIFIED)` · `RECOVERY_MONTH` · `REMARKS` |
| **ESI_ENROLLMENT** | Eligible-but-exempt employees **grouped by client** with ESIC/UAN numbers and per-head EE 0.75% / ER 3.25% amounts | `IC_NO_ALLOTTED` · `ENROLLED_FROM (month)` · `REMARKS` |

## How to generate

```
python make_worklist_M17.py <Month_RECONCILED_M16.xlsx> <Mon>_WORKLIST_Recovery_ESI.xlsx
```
(script beside this file; needs `pip install openpyxl`). Input MUST be the
M16-patched file — M17 uses the cash-capped excess.

## Selection logic (for reimplementation in any pipeline)

- Universe: `ACTION_NEEDED = 'Y'` rows (post-M16).
- **RECOVERY_REVIEW** = reason contains `PAID ABOVE FIXED RATE` or `IMPLIED FULL-MONTH`.
  `EXCESS_TO_REVIEW = min(EXCESS_SALARY, GROSS AMT)`. `PRIORITY = HIGH` if > ₹10,000.
- **ESI_ENROLLMENT** = reason contains `ESI-EXEMPT`. Exposure/head/month =
  `GROSS AMT × 4%` (EE 0.75% + ER 3.25%).

## April-2026 result (verified)

| Workstream | Employees | Amount |
|---|--:|--:|
| Recovery — HIGH (> ₹10k each) | **133** | **₹16,22,437** |
| Recovery — remaining small rows | 2,644 | ₹74,48,065 |
| ESI enrollment needed | **1,940** | ₹15,38,471 / month exposure |

Working order: HIGH recovery rows first (5% of rows, ~18% of value, biggest tickets),
ESI enrollment in parallel (statutory clock runs monthly), small recovery rows batch-wise.
