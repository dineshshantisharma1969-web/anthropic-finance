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
| **WAGE_CODE_50PCT** | Code on Wages 2019 test: `BASIC+DA < 50% of CTC`, worst ratio first, severity-banded (`<30%` structural rows highlighted red). Guards: negative-gross reversal rows excluded; `NOTE` column marks OT/arrears-heavy and ≤2-day rows so structural fails read clean. Shows shortfall-to-50% and target Basic+DA | `RESTRUCTURE (Y/N)` · `TARGET_BASIC_DA (=50% CTC)` · `REMARKS` |

## How to generate

```
python make_worklist_M17.py <Month_RECONCILED_M16.xlsx> <Mon>_WORKLIST_Recovery_ESI.xlsx
```
(script beside this file; needs `pip install openpyxl`). Input MUST be the
M16-patched file — M17 uses the cash-capped excess.

## Selection logic (for reimplementation in any pipeline)

- Universe: `ACTION_NEEDED = 'Y'` rows (post-M16).
- **RECOVERY_REVIEW** = reason contains `PAID ABOVE FIXED RATE` or `IMPLIED FULL-MONTH`,
  recomputed on the **M18 day-basis** (below). `PRIORITY = HIGH` if excess > ₹10,000.

### Rule M18 — day-basis + allowances excess (CRITICAL correction)

`FIXEDGROSS` is expressed at the `SITEDIVISIONDAYS` divisor — **when the divisor is 1
it is a PER-DAY rate** (e.g. ₹866, ₹985/day), else a monthly figure at divisor
26/27/28/30/31. Comparing a per-day rate directly against a month's gross wrongly
flags nearly every such employee as overpaid. Correct comparison:

```
RATE BASIS (M18c — the SITEDIVISIONDAYS column is unreliable on some rows;
per-day rates like ₹808 appear with divisor 30/31):
  div = 1               → PER-DAY
  FIXEDGROSS < ₹3,000   → PER-DAY (no monthly salary is < ₹3,000; daily
                          minimum wages run ₹300–1,500)
  ₹3,000 ≤ FG < ₹6,000  → ambiguous: pick the reading (per-day vs monthly/div)
                          whose expected total best explains the gross paid
  else                  → MONTHLY at the divisor

EXPECTED_BASE    = rate × NORMALDAYS            (PER-DAY basis)
                 = FIXEDGROSS / div × NORMALDAYS (MONTHLY basis)      (M18a)
EXPECTED_TOTAL   = EXPECTED_BASE + Σ max(0, OT, EXTRA OT, arrears,    (M18b)
                   ATTENDANCE ALW, PAID LEAVE, WEEKLY OFF,
                   NATIONAL/FESTIVAL/PAID HOLIDAY, TRAVELLING ALW)
                   — negatives are reconciliation adjustments, never subtract
EXCESS_TO_REVIEW = clamp(GROSS AMT − EXPECTED_TOTAL, 0, GROSS AMT)

CLEAR (no overpayment) when EXCESS < 1 OR EXPECTED_TOTAL is within
max(₹500, 2%) of GROSS AMT / REVISED_GROSS / REVISED_GROSS_NEW.
```

**NORMALDAYS (actual days worked) is always the multiplier.** The tab shows
`RATE_BASIS`, rate, NORMALDAYS, EXPECTED_BASE, ALLOWANCES, EXPECTED_TOTAL, GROSS
and REVISED_GROSS so every number is verifiable by eye. April-26 effect:
**644 rows cleared** (₹20.2L phantom excess removed — all 297 divisor-1 rows AND
58 per-day rates mislabeled with divisor 30/31, e.g. ₹808 × 25 days = ₹20,192 ≈
₹22,015 gross, previously flagged ₹21,342). Remaining genuine pool
**2,133 rows / ₹76.1L, HIGH 100 rows / ₹11.3L**.
- **ESI_ENROLLMENT** = reason contains `ESI-EXEMPT`. Exposure/head/month =
  `GROSS AMT × 4%` (EE 0.75% + ER 3.25%).

## April-2026 result (verified)

| Workstream | Employees | Amount |
|---|--:|--:|
| Recovery — HIGH (> ₹10k each, M18 basis) | **100** | **₹11,26,667** |
| Recovery — remaining small rows | 2,033 | ₹64,84,330 |
| Recovery rows cleared by M18 (297 div-1 + 58 mislabeled per-day + others) | 644 | (₹20.2L phantom excess removed) |
| ESI enrollment needed | **1,940** | ₹15,38,471 / month exposure |
| Wage Code 50% fails (1,019 structural + 31 noted; 234 negative-gross reversals excluded; 46 severe <30%) | **1,050** | ₹25,48,764 / month shortfall to 50% |

Wage-code concentration: Ministry of Railways, Blink Commerce (58% of its rows fail),
Bhagwati Products (87% fail), JLL, Zomato Hyperpure, Infosys. Fixing = restructure
salary components so Basic+DA ≥ 50% of CTC (raises PF/gratuity cost — price it first).

Working order: HIGH recovery rows first (5% of rows, ~18% of value, biggest tickets),
ESI enrollment in parallel (statutory clock runs monthly), small recovery rows batch-wise.
